# ===================================================================
# 0. 套件 & 全域函式（一定放最頂）
# ===================================================================
import streamlit as st  
import os, datetime as dt, pandas as pd, io, json, re
import requests
import base64
import gspread
from google.oauth2.service_account import Credentials
from io import StringIO
import csv

# ---------- 頁面設定 ----------
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# ---------- 診斷：檢查 secrets ----------
if "gcp_service_account" not in st.secrets:
    st.error("❌ 找不到 gcp_service_account secrets！")
    st.info("""
    **請在 Streamlit Community Cloud 設定 Secrets：**
    
    1. 前往 https://share.streamlit.io/
    2. 點擊你的 app → ⚙️ Settings → Secrets
    3. 貼上 TOML 格式的 Google Sheets 憑證：
    
    ```toml
    [gcp_service_account]
    type = "service_account"
    project_id = "..."
    private_key_id = "..."
    private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
    client_email = "..."
    client_id = "..."
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    
    [sheets]
    spreadsheet_id = "你的試算表ID"
    ```
    """)
    # 停止執行，避免後續錯誤
    st.stop()

if "sheets" not in st.secrets or "spreadsheet_id" not in st.secrets["sheets"]:
    st.error("❌ 找不到 sheets.spreadsheet_id！")
    st.info("請在 secrets 中加入 `[sheets]` 區塊和 `spreadsheet_id`")
    st.stop()

# ---------- Google Sheets 連線（每次重新建立）----------
def get_google_sheets_client():
    """重新建立 Google Sheets 連線，回傳 (gc, sheet_id) 或 (None, None)"""
    try:
        if "gcp_service_account" not in st.secrets:
            return None, None
        if "sheets" not in st.secrets or "spreadsheet_id" not in st.secrets["sheets"]:
            return None, None
            
        gcp_sa = st.secrets["gcp_service_account"]
        sheet_id = st.secrets["sheets"]["spreadsheet_id"]
        
        creds = Credentials.from_service_account_info(
            gcp_sa,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        gc = gspread.authorize(creds)
        return gc, sheet_id
        
    except Exception as e:
        st.sidebar.error(f"Google Sheets 連線失敗: {e}")
        return None, None

# ---------- 資料庫設定 ----------
DATA_DIR = "data"
SENTENCES_FILE = os.path.join(DATA_DIR, "sentences.json")
TODO_FILE = os.path.join(DATA_DIR, "todos.json")
FAVORITE_FILE = os.path.join(DATA_DIR, "favorite_sentences.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ---------- 本地檔案操作（原子寫入 + 備份）----------
def load_sentences():
    """安全載入本地資料庫"""
    if not os.path.exists(SENTENCES_FILE):
        return {}
    
    try:
        with open(SENTENCES_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            data = json.loads(content)
            if not isinstance(data, dict):
                return {}
            return data
    except json.JSONDecodeError:
        backup_name = f"{SENTENCES_FILE}.backup_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            os.rename(SENTENCES_FILE, backup_name)
            st.warning(f"⚠️ 資料庫損毀，已備份為 {backup_name}")
        except:
            pass
        return {}
    except Exception as e:
        st.error(f"載入本地資料庫失敗：{e}")
        return {}

def save_sentences(data):
    """安全儲存本地資料庫（原子寫入）"""
    if not isinstance(data, dict):
        st.error("儲存失敗：資料必須是字典格式")
        return False
    
    try:
        temp_file = f"{SENTENCES_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        if os.path.exists(SENTENCES_FILE):
            backup_file = f"{SENTENCES_FILE}.backup_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                os.replace(SENTENCES_FILE, backup_file)
                backups = sorted([f for f in os.listdir(DATA_DIR) if f.startswith("sentences.json.backup_")])
                for old in backups[:-5]:
                    try:
                        os.remove(os.path.join(DATA_DIR, old))
                    except:
                        pass
            except:
                pass
        
        os.replace(temp_file, SENTENCES_FILE)
        return True
    except Exception as e:
        st.error(f"儲存本地資料庫失敗：{e}")
        return False

def load_todos():
    if os.path.exists(TODO_FILE):
        try:
            with open(TODO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_todos():
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.todo, f, ensure_ascii=False, indent=2)

def load_favorites():
    if os.path.exists(FAVORITE_FILE):
        try:
            with open(FAVORITE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_favorites():
    with open(FAVORITE_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.favorite_sentences, f, ensure_ascii=False, indent=2)

# ---------- 解析內容（支援 \t 分隔 + 欄位對齊）----------
def parse_content_to_rows(content, expected_cols=None):
    """解析 CSV 或 Markdown 表格為二維列表"""
    if not content:
        return []
    
    rows = []
    lines = content.strip().split('\n')
    
    if '|' in content:
        for line in lines:
            line = line.strip()
            if line.startswith('|') and '---' not in line and line.replace('|', '').strip():
                cells = [re.sub(r'\*\*(.*?)\*\*', r'\1', c.strip()) for c in line.split('|')[1:-1]]
                if any(cells):
                    rows.append(cells)
    else:
        reader = csv.reader(StringIO(content), delimiter='\t')
        for row in reader:
            if any(row):
                row = [re.sub(r'\*\*(.*?)\*\*', r'\1', c) for c in row]
                rows.append(row)
    
    if rows and any(k in str(rows[0]) for k in ['Ref', 'No', 'Word', 'Paragraph', 'English', 'Chinese', '口語訳']):
        rows = rows[1:]
    
    if expected_cols and rows:
        normalized = []
        for row in rows:
            if len(row) < expected_cols:
                row = row + [''] * (expected_cols - len(row))
            elif len(row) > expected_cols:
                row = row[:expected_cols]
            normalized.append(row)
        rows = normalized
    
    return rows

# ---------- Google Sheets 儲存函式（欄位對齊版）----------
def save_v1_sheet(ref, content, gc, sheet_id):
    """儲存到 V1_Sheet"""
    if not content or not content.strip() or not gc or not sheet_id:
        return True
    
    try:
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("V1_Sheet")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("V1_Sheet", rows=1000, cols=5)
            ws.append_row(["Ref.", "English (ESV)", "Chinese", "Syn/Ant", "Grammar"])
        
        rows = parse_content_to_rows(content, expected_cols=4)
        if rows:
            rows_with_ref = [[ref] + row for row in rows]
            ws.append_rows(rows_with_ref)
            st.sidebar.caption(f"  V1_Sheet：寫入 {len(rows_with_ref)} 行")
        return True
    except Exception as e:
        st.sidebar.error(f"  V1_Sheet 失敗：{e}")
        return False

def save_v2_sheet(ref, content, gc, sheet_id):
    """儲存到 V2_Sheet"""
    if not content or not content.strip() or not gc or not sheet_id:
        return True
    
    try:
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("V2_Sheet")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("V2_Sheet", rows=1000, cols=7)
            ws.append_row(["Ref.", "口語訳", "Grammar", "Note", "KRF", "Korean Syn/Ant", "THSV11"])
        
        rows = parse_content_to_rows(content, expected_cols=6)
        if rows:
            rows_with_ref = [[ref] + row for row in rows]
            ws.append_rows(rows_with_ref)
            st.sidebar.caption(f"  V2_Sheet：寫入 {len(rows_with_ref)} 行")
        return True
    except Exception as e:
        st.sidebar.error(f"  V2_Sheet 失敗：{e}")
        return False

def save_w_sheet(ref, content, gc, sheet_id):
    """儲存到 W_Sheet"""
    if not content or not content.strip() or not gc or not sheet_id:
        return True
    
    try:
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("W_Sheet")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("W_Sheet", rows=1000, cols=6)
            ws.append_row(["No", "Word/phrase", "Chinese", "Synonym+中文對照", "Antonym+中文對照", "全句聖經中英對照例句"])
        
        rows = parse_content_to_rows(content, expected_cols=5)
        if rows:
            rows_with_ref = [[ref] + row for row in rows]
            ws.append_rows(rows_with_ref)
            st.sidebar.caption(f"  W_Sheet：寫入 {len(rows_with_ref)} 行")
        return True
    except Exception as e:
        st.sidebar.error(f"  W_Sheet 失敗：{e}")
        return False

def save_p_sheet(ref, content, gc, sheet_id):
    """儲存到 P_Sheet"""
    if not content or not content.strip() or not gc or not sheet_id:
        return True
    
    try:
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("P_Sheet")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("P_Sheet", rows=1000, cols=3)
            ws.append_row(["Paragraph", "English Refinement", "中英夾雜講章"])
        
        rows = parse_content_to_rows(content, expected_cols=2)
        if rows:
            rows_with_ref = [[ref] + row for row in rows]
            ws.append_rows(rows_with_ref)
            st.sidebar.caption(f"  P_Sheet：寫入 {len(rows_with_ref)} 行")
        return True
    except Exception as e:
        st.sidebar.error(f"  P_Sheet 失敗：{e}")
        return False

def save_grammar_sheet(ref, content, gc, sheet_id):
    """儲存到 Grammar_List"""
    if not content or not content.strip() or not gc or not sheet_id:
        return True
    
    try:
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("Grammar_List")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("Grammar_List", rows=1000, cols=4)
            ws.append_row(["No", "Original Sentence(from text)", "Grammar Rule", "Analysis & Example (1️⃣2️⃣3️⃣4️⃣)"])
        
        rows = parse_content_to_rows(content, expected_cols=3)
        if rows:
            rows_with_ref = [[ref] + row for row in rows]
            ws.append_rows(rows_with_ref)
            st.sidebar.caption(f"  Grammar_List：寫入 {len(rows_with_ref)} 行")
        return True
    except Exception as e:
        st.sidebar.error(f"  Grammar_List 失敗：{e}")
        return False

def save_to_google_sheets(data_dict):
    """將資料分別存入對應的 5 個工作表"""
    gc, sheet_id = get_google_sheets_client()
    
    if not gc or not sheet_id:
        st.sidebar.error("❌ Google Sheets 未連線")
        return False, "Google Sheets 未連線"
    
    try:
        ref = data_dict.get('ref', 'N/A')
        mode = data_dict.get('mode', 'A')
        
        st.sidebar.info(f"📝 開始儲存：{ref}（模式 {mode}）")
        
        if mode == 'A':
            success_v1 = save_v1_sheet(ref, data_dict.get('v1_content', ''), gc, sheet_id)
            success_v2 = save_v2_sheet(ref, data_dict.get('v2_content', ''), gc, sheet_id)
            
            if success_v1 and success_v2:
                st.sidebar.success(f"✅ 模式A儲存完成：{ref}")
                return True, "Mode A saved"
            else:
                return False, f"V1={success_v1}, V2={success_v2}"
        else:
            success_w = save_w_sheet(ref, data_dict.get('w_sheet', ''), gc, sheet_id)
            success_p = save_p_sheet(ref, data_dict.get('p_sheet', ''), gc, sheet_id)
            success_g = save_grammar_sheet(ref, data_dict.get('grammar_list', ''), gc, sheet_id)
            
            if success_w and success_p and success_g:
                st.sidebar.success(f"✅ 模式B儲存完成：{ref}")
                return True, "Mode B saved"
            else:
                return False, f"W={success_w}, P={success_p}, G={success_g}"
            
    except Exception as e:
        st.sidebar.error(f"❌ 儲存失敗：{str(e)}")
        import traceback
        st.sidebar.code(traceback.format_exc())
        return False, str(e)

# ---------- 從 Google Sheets 載入（欄位對齊版）----------
def load_from_google_sheets():
    """從 5 個工作表載入所有資料"""
    gc, sheet_id = get_google_sheets_client()
    
    if not gc or not sheet_id:
        return {}
    
    all_data = {}
    try:
        sh = gc.open_by_key(sheet_id)
        
        # V1_Sheet
        try:
            ws = sh.worksheet("V1_Sheet")
            rows = ws.get_all_values()
            if len(rows) > 1:
                for row in rows[1:]:
                    if len(row) >= 5:
                        ref = row[0]
                        if ref not in all_data:
                            all_data[ref] = {
                                "ref": ref, "mode": "A", "type": "Scripture",
                                "v1_content": "", "v2_content": "",
                                "w_sheet": "", "p_sheet": "", "grammar_list": "", "other": "",
                                "date_added": ""
                            }
                        row_data = row[:5] if len(row) >= 5 else row + [''] * (5 - len(row))
                        all_data[ref]["v1_content"] += "\t".join(row_data) + "\n"
        except gspread.WorksheetNotFound:
            pass
        
        # V2_Sheet
        try:
            ws = sh.worksheet("V2_Sheet")
            rows = ws.get_all_values()
            if len(rows) > 1:
                for row in rows[1:]:
                    if len(row) >= 7:
                        ref = row[0]
                        if ref in all_data:
                            row_data = row[:7] if len(row) >= 7 else row + [''] * (7 - len(row))
                            all_data[ref]["v2_content"] += "\t".join(row_data) + "\n"
        except gspread.WorksheetNotFound:
            pass
        
        # W_Sheet
        try:
            ws = sh.worksheet("W_Sheet")
            rows = ws.get_all_values()
            if len(rows) > 1:
                for row in rows[1:]:
                    if len(row) >= 6:
                        ref = row[0]
                        if ref not in all_data:
                            all_data[ref] = {
                                "ref": ref, "mode": "B", "type": "Document",
                                "v1_content": "", "v2_content": "",
                                "w_sheet": "", "p_sheet": "", "grammar_list": "", "other": "",
                                "date_added": ""
                            }
                        row_data = row[:6] if len(row) >= 6 else row + [''] * (6 - len(row))
                        all_data[ref]["w_sheet"] += "\t".join(row_data) + "\n"
        except gspread.WorksheetNotFound:
            pass
        
        # P_Sheet
        try:
            ws = sh.worksheet("P_Sheet")
            rows = ws.get_all_values()
            if len(rows) > 1:
                for row in rows[1:]:
                    if len(row) >= 3:
                        ref = row[0]
                        if ref in all_data and all_data[ref]["mode"] == "B":
                            row_data = row[:3] if len(row) >= 3 else row + [''] * (3 - len(row))
                            all_data[ref]["p_sheet"] += "\t".join(row_data) + "\n"
        except gspread.WorksheetNotFound:
            pass
        
        # Grammar_List
        try:
            ws = sh.worksheet("Grammar_List")
            rows = ws.get_all_values()
            if len(rows) > 1:
                for row in rows[1:]:
                    if len(row) >= 4:
                        ref = row[0]
                        if ref in all_data and all_data[ref]["mode"] == "B":
                            row_data = row[:4] if len(row) >= 4 else row + [''] * (4 - len(row))
                            all_data[ref]["grammar_list"] += "\t".join(row_data) + "\n"
        except gspread.WorksheetNotFound:
            pass
        
        return all_data
        
    except Exception as e:
        st.sidebar.error(f"載入 Google Sheets 失敗: {e}")
        return {}

# ---------- 全域工具函式 ----------
def save_analysis_result(result, input_text):
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []
    st.session_state.analysis_history.append({
        "date": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "input_preview": input_text[:50] + "..." if len(input_text) > 50 else input_text,
        "result": result
    })
    if len(st.session_state.analysis_history) > 10:
        st.session_state.analysis_history.pop(0)

def to_excel(result: dict) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet, key in [("Words", "words"), ("Phrases", "phrases"), ("Grammar", "grammar")]:
            if key in result and result[key]:
                pd.DataFrame(result[key]).to_excel(writer, sheet_name=sheet, index=False)
        stats = pd.DataFrame({
            "項目": ["總字彙數", "總片語數", "文法點數", "分析日期"],
            "數值": [
                len(result.get("words", [])),
                len(result.get("phrases", [])),
                len(result.get("grammar", [])),
                dt.date.today().strftime("%Y-%m-%d")
            ]
        })
        stats.to_excel(writer, sheet_name="統計", index=False)
    buffer.seek(0)
    return buffer.getvalue()

# ---------- 初始化 Session State（優先從本地載入，再嘗試 Google Sheets）----------
if 'sentences' not in st.session_state:
    local_data = load_sentences()
    
    if local_data:
        st.session_state.sentences = local_data
    else:
        sheets_data = load_from_google_sheets()
        if sheets_data:
            st.session_state.sentences = sheets_data
            save_sentences(sheets_data)
        else:
            st.session_state.sentences = {}

if 'todo' not in st.session_state:
    st.session_state.todo = load_todos()
if 'favorite_sentences' not in st.session_state:
    st.session_state.favorite_sentences = load_favorites()
if 'sel_date' not in st.session_state:
    st.session_state.sel_date = str(dt.date.today())
if 'cal_key' not in st.session_state:
    st.session_state.cal_key = 0
if 'active_del_id' not in st.session_state:
    st.session_state.active_del_id = None
if 'active_fav_del' not in st.session_state:
    st.session_state.active_fav_del = None

# ===================================================================
# 1. 側邊欄（保留原 UI）
# ===================================================================
with st.sidebar:
    st.divider()
    
    # 資料檢查工具
    def parse_content_to_dict(content):
        """解析內容為字典列表（供資料檢查使用）"""
        if not content:
            return []
        try:
            from io import StringIO
            import csv
            reader = csv.DictReader(StringIO(content.strip()), delimiter='\t')
            return list(reader)
        except:
            return []
    
    if st.checkbox("🔍 開啟資料欄位檢查"):
        st.markdown("---")
        if 'sentences' in st.session_state and st.session_state.sentences:
            first_ref = list(st.session_state.sentences.keys())[0]
            data = st.session_state.sentences[first_ref]
            
            st.write(f"經節範例: {first_ref}")
            st.write(f"模式: {data.get('mode', 'Unknown')}")
            
            v1_test = parse_content_to_dict(data.get('v1_content', ''))
            if v1_test:
                st.info(f"V1 欄位偵測: {list(v1_test[0].keys())}")
            else:
                st.error("V1 內容解析失敗")
                
            v2_test = parse_content_to_dict(data.get('v2_content', ''))
            if v2_test:
                st.success(f"V2 欄位偵測: {list(v2_test[0].keys())}")
            else:
                st.warning("V2 內容為空")
                
            if data.get('w_sheet'):
                w_test = parse_content_to_dict(data.get('w_sheet', ''))
                if w_test:
                    st.info(f"W Sheet 欄位: {list(w_test[0].keys())}")
                    
            if data.get('grammar_list'):
                g_test = parse_content_to_dict(data.get('grammar_list', ''))
                if g_test:
                    st.info(f"Grammar 欄位: {list(g_test[0].keys())}")
        else:
            st.write("資料庫目前無資料")
    
    # 開發工具：重置 Google Sheets
    st.divider()
    st.markdown("### 🛠️ 開發工具")
    
    with st.expander("進階設定", expanded=False):
        if st.button("🚨 重置為 5 工作表格式", type="secondary", use_container_width=True):
            gc, sheet_id = get_google_sheets_client()
            if gc and sheet_id:
                try:
                    sh = gc.open_by_key(sheet_id)
                    
                    # 刪除舊的錯誤工作表
                    for old_name in ['Mode_A_Data', 'Mode_B_Data']:
                        try:
                            ws = sh.worksheet(old_name)
                            sh.del_worksheet(ws)
                            st.success(f"已刪除舊工作表：{old_name}")
                        except:
                            pass
                    
                    # 建立新的 5 個工作表
                    new_sheets = [
                        ("V1_Sheet", ["Ref.", "English (ESV)", "Chinese", "Syn/Ant", "Grammar"]),
                        ("V2_Sheet", ["Ref.", "口語訳", "Grammar", "Note", "KRF", "Korean Syn/Ant", "THSV11"]),
                        ("W_Sheet", ["No", "Word/phrase", "Chinese", "Synonym+中文對照", "Antonym+中文對照", "全句聖經中英對照例句"]),
                        ("P_Sheet", ["Paragraph", "English Refinement", "中英夾雜講章"]),
                        ("Grammar_List", ["No", "Original Sentence(from text)", "Grammar Rule", "Analysis & Example (1️⃣2️⃣3️⃣4️⃣)"])
                    ]
                    
                    for sheet_name, headers in new_sheets:
                        try:
                            try:
                                existing = sh.worksheet(sheet_name)
                                st.info(f"已存在：{sheet_name}")
                                continue
                            except gspread.WorksheetNotFound:
                                pass
                            
                            ws = sh.add_worksheet(sheet_name, rows=1000, cols=len(headers))
                            ws.append_row(headers)
                            st.success(f"✅ 已建立：{sheet_name}")
                        except Exception as e:
                            st.error(f"建立 {sheet_name} 失敗：{e}")
                    
                    st.balloons()
                    st.info("✅ 重置完成！請重新整理頁面")
                    
                except Exception as e:
                    st.error(f"重置失敗：{e}")
            else:
                st.error("Google Sheets 未連線")
        
        # 檢查 Google Sheets 連線狀態
        if st.button("🔎 檢查雲端工作表", use_container_width=True):
            gc, sheet_id = get_google_sheets_client()
            if gc and sheet_id:
                try:
                    sh = gc.open_by_key(sheet_id)
                    all_worksheets = sh.worksheets()
                    st.write(f"找到 {len(all_worksheets)} 個工作表：")
                    for ws in all_worksheets:
                        row_count = len(ws.get_all_values())
                        st.write(f"• **{ws.title}**：{row_count} 行")
                except Exception as e:
                    st.error(f"檢查失敗：{e}")
            else:
                st.error("Google Sheets 未連線")
            
    c1, c2 = st.columns(2)
    c1.link_button("✨ Google AI", "https://gemini.google.com")
    c2.link_button("🤖 Kimi K2", "https://kimi.moonshot.cn")
    c3, c4 = st.columns(2)
    c3.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb")
    c4.link_button("THSV11", "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")
    
    st.divider()
    st.markdown("### 💾 資料庫狀態")
    
    # 修正：動態檢查連線狀態
    gc, sheet_id = get_google_sheets_client()
    if gc and sheet_id:
        st.success("✅ Google Sheets 已連線")
        if st.button("🔄 強制同步到雲端", use_container_width=True):
            # 同步所有本地資料到 Google Sheets
            count = 0
            for ref, data in st.session_state.get('sentences', {}).items():
                success, _ = save_to_google_sheets(data)
                if success:
                    count += 1
            st.success(f"已同步 {count} 筆資料到 Google Sheets")
    else:
        st.error("❌ Google Sheets 未連線")
        st.caption("請在 secrets.toml 設定 gcp_service_account")
    
    local_count = len(st.session_state.get('sentences', {}))
    st.caption(f"本地快取：{local_count} 筆")
    
    st.divider()
    st.markdown("### 🖼️ 底部背景設定")
    
    bg_options = {
        "🐶 Snoopy": "Snoopy.jpg",
        "🐰 Mashimaro 1": "Mashimaro1.jpg",
        "🐰 Mashimaro 2": "Mashimaro2.jpg",
        "🐰 Mashimaro 3": "Mashimaro3.jpg",
        "🐰 Mashimaro 4": "Mashimaro4.jpg",
        "🐰 Mashimaro 5": "Mashimaro5.jpg",
        "🐰 Mashimaro 6": "Mashimaro6.jpg"
    }
    
    if 'selected_bg' not in st.session_state:
        st.session_state.selected_bg = list(bg_options.keys())[0]
    if 'bg_size' not in st.session_state:
        st.session_state.bg_size = 15
    if 'bg_bottom' not in st.session_state:
        st.session_state.bg_bottom = 30
    
    selected_bg = st.selectbox(
        "選擇角色", 
        list(bg_options.keys()), 
        index=list(bg_options.keys()).index(st.session_state.selected_bg),
        key="selected_bg"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        bg_size = st.slider("圖片大小", 5, 50, st.session_state.bg_size, format="%d%%", key="bg_size")
    with col2:
        bg_bottom = st.slider("底部間距", 0, 100, st.session_state.bg_bottom, format="%dpx", key="bg_bottom")

# 背景圖片套用（sidebar 外面）
selected_img_file = bg_options[st.session_state.selected_bg]
current_bg_size = st.session_state.bg_size
current_bg_bottom = st.session_state.bg_bottom

try:
    if os.path.exists(selected_img_file):
        with open(selected_img_file, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{img_b64}");
            background-size: {current_bg_size}% auto;
            background-position: center bottom {current_bg_bottom}px;
            background-attachment: fixed;
            background-repeat: no-repeat;
            z-index: 0;
        }}
        .main .block-container {{
            position: relative;
            z-index: 1;
            padding-bottom: {current_bg_bottom + 100}px;
        }}
        </style>
        """, unsafe_allow_html=True)
except:
    pass

# ===================================================================
# 2. 頁面配置 & Session 初值（只留全域會用到的）
# ===================================================================
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# 這些變數只有 TAB2 會用到，但為了避免後續 TAB 引用出錯，先給空值
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []

# CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
.cute-korean { font-family: 'Gamja Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
.small-font { font-size: 13px; color: #555555; margin-top: 5px !important; }
.grammar-box-container {
    background-color: #f8f9fa; border-radius: 8px; padding: 12px;
    border-left: 5px solid #FF8C00; text-align: left; margin-top: 0px;
}
.fc-daygrid-day-frame:hover {background-color: #FFF3CD !important; cursor: pointer; transform: scale(1.03); transition: .2s}
.fc-daygrid-day-frame:active {transform: scale(0.98); background-color: #FFE69C !important}
</style>
""", unsafe_allow_html=True)

# 圖片 & 現成 TAB
IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg",
    "M1": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro1.jpg",
    "M2": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro2.jpg",
    "M3": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro3.jpg",
    "M4": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro4.jpg"
}
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다</p>', unsafe_allow_html=True)
    st.image(IMG_URLS["M3"], width=250)
    st.divider()

tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# ===================================================================
# 3. TAB1 ─ 書桌 (簡化版，先確保不報錯)
# ===================================================================
with tabs[0]:
    st.info("🏠 TAB1 書桌功能 - 待資料庫穩定後加入完整功能")
    st.write(f"目前資料庫有 {len(st.session_state.get('sentences', {}))} 筆資料")

# ===================================================================
# 4. TAB2 ─ 月曆待辦 + 時段金句 + 收藏金句（簡化版）
# ===================================================================
with tabs[1]:
    st.info("📓 TAB2 筆記功能 - 待資料庫穩定後加入完整功能")

# ===================================================================
# 5. TAB3 ─ 挑戰（簡化版）
# ===================================================================
with tabs[2]:
    st.info("✍️ TAB3 挑戰功能 - 待資料庫穩定後加入完整功能")

# ===================================================================
# 6. TAB4 ─ AI 控制台 + 資料庫管理（保留完整 UI）
# ===================================================================
with tabs[3]:
    import streamlit.components.v1 as components

    # 背景圖片套用
    try:
        selected_img_file = bg_options.get(st.session_state.get('selected_bg', '🐶 Snoopy'), 'Snoopy.jpg')
        current_bg_size = st.session_state.get('bg_size', 15)
        current_bg_bottom = st.session_state.get('bg_bottom', 30)
        
        if os.path.exists(selected_img_file):
            with open(selected_img_file, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpeg;base64,{img_b64}");
                background-size: {current_bg_size}% auto;
                background-position: center bottom {current_bg_bottom}px;
                background-attachment: fixed;
                background-repeat: no-repeat;
                z-index: 0;
            }}
            .main .block-container {{
                position: relative;
                z-index: 1;
                padding-bottom: {current_bg_bottom + 100}px;
            }}
            </style>
            """, unsafe_allow_html=True)
    except:
        pass

    # Session State 初始化
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'is_prompt_generated' not in st.session_state:
        st.session_state.is_prompt_generated = False
    if 'main_input_value' not in st.session_state:
        st.session_state.main_input_value = ""
    if 'original_text' not in st.session_state:
        st.session_state.original_text = ""
    if 'content_mode' not in st.session_state:
        st.session_state.content_mode = ""
    if 'raw_input_value' not in st.session_state:
        st.session_state.raw_input_value = ""
    if 'ref_number' not in st.session_state:
        st.session_state.ref_number = ""
    if 'current_entry' not in st.session_state:
        st.session_state.current_entry = {
            'v1': '', 'v2': '', 'w_sheet': '', 
            'p_sheet': '', 'grammar_list': '', 'other': ''
        }
    if 'saved_entries' not in st.session_state:
        st.session_state.saved_entries = []
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'edit_ref' not in st.session_state:
        st.session_state.edit_ref = None

    # 智能偵測內容類型
    def detect_content_mode(text):
        text = text.strip()
        if not text:
            return "document"
        if text.startswith("{"):
            return "json"
        
        has_chinese = re.search(r'[\u4e00-\u9fa5]', text)
        return "scripture" if has_chinese else "document"

    # 產生完整指令
    def generate_full_prompt():
        raw_text = st.session_state.get("raw_input_temp", "").strip()
        if not raw_text:
            st.warning("請先貼上內容")
            return

        mode = detect_content_mode(raw_text)
        
        if mode in ["json", "scripture"]:
            full_prompt = f"""你是一位精通多國語言的聖經專家與語言學教授。請根據輸入內容選擇對應模式輸出。
            所有翻譯嚴格規定按聖經語言翻譯，不可私自亂翻譯

### 模式 A：【聖經經文分析時】＝》一定要產出V1 + V2 Excel格式（Markdown表格）

⚠️ 輸出格式要求：請使用 **Markdown 表格格式**（如下範例），方便我直接複製貼回 Excel：

【V1 Sheet 範例】
| Ref. | English (ESV) | Chinese | Syn/Ant | Grammar |
|------|---------------|---------|---------|---------|
| Pro 31:6 | Give strong drink... | 可以把濃酒... | strong drink (烈酒) / watered down wine (淡酒) | 1️⃣[分段解析+語法標籤]...<br>2️⃣[詞性辨析]...<br>3️⃣[修辭與結構或遞進邏輯]...<br>4️⃣[語意解釋]...<br>...|

【V2 Sheet 範例】
| Ref. | 口語訳 | Grammar | Note | KRF | Korean Syn/Ant | THSV11 |
|------|--------|---------|------|-----|---------|--------|

🔹 V1 Sheet 欄位要求：
1. Ref.：自動找尋經卷章節並用縮寫 (如: Pro, Rom, Gen).
2. English (ESV)：檢索對應的 ESV 英文經文.
3. Chinese：填入我提供的中文原文.
4. Syn/Ant："同義字與反義字"，取自ESV中的高級/中高級單字或片語（含中/英翻譯）
5. Grammar：嚴格遵守符號化格式＋嚴格提供詳細規範如下：
   例箴17:7Fine speech is not becoming to a fool; still less is false speech to a prince.
1️⃣[分段解析+語法標籤]： 1st clause：」Fine speech" is not becoming to a fool
                    2nd clause：still less is "false speech" to a prince
   語法標籤必須標註出Grammar labels (must be identified):
   主語 (Subject)、動詞 (Verb)、補語 (Complement) 或 修飾語。
* 主語 (Subject): Fine speech（Elegant words優美的言辭/Refined talk高雅的談吐）...等等
* 動詞 (Verb): is (Linking verb/Copula 系動詞)。
* 形容詞Adjective/Complement補語 (Complement): becoming(Adjective meaning「fitting相稱的」or「appropriate得體的」..等等
* 介系詞短語(Prepositional Phrase): to a fool。(Specifies the inappropriate recipient).
2️⃣詞性辨析Part-of-Speech Distinction： 若單字有歧義（例如 becoming 是動詞還是形容詞）...等等
If a word has potential ambiguity (for example, becoming can be a verb or an adjective), 
its part of speech and meaning in this sentence must be clearly identified...等等
* becoming
    * Possible forms:
        * Verb (to become)
        * Adjective (suitable, fitting)
    * In this sentence: adjective
    * Meaning here: appropriate, fitting, proper

3️⃣修辭與結構Rhetoric and Structure：Identify and explain specific grammatical phenomena, such as:如 倒裝 (Inversion)、省略 (Ellipsis)  或遞進邏輯 (Still less / A fortiori)。
4️⃣語意解釋：This grammatical structure strengthens the verse』s logic by contrasting inner character with outer speech.
  請以 **Markdown 表格格式**輸出（非 JSON）.
  
🔹 V2 Sheet 欄位要求：
1. Ref.：同 V1.
2. 口語訳：檢索對應的日本《口語訳聖經》(1955).
3. Grammar格式同 V1
4. Note：日文文法或語境的補充說明.
5. KRF：檢索對應的韓文《Korean Revised Version》.
6. Korean Syn/Ant：韓文高/ 中高級字（含日/韓/中翻譯）.
7. THSV11:輸出泰文"對應的重要片語key phrases"《Thai Holy Bible, Standard Version 2011》.

⚠️ 自動推斷書卷（若只有數字如31:6）：
• "可以把濃酒" → Pro
• "才德的婦人" → Prov • "太初有道" → John • "起初神創造" → Gen
• "虛心的人有福" → Matt • "愛是恆久忍耐" → 1Co

標準縮寫：Gen,Exo,Lev,Num,Deu,Jos,Jdg,Rut,1Sa,2Sa,1Ki,2Ki,1Ch,2Ch,Ezr,Neh,Est,Job,Psa,Pro,Ecc,Son,Isa,Jer,Lam,Eze,Dan,Hos,Joe,Amo,Oba,Jon,Mic,Nah,Hab,Zep,Hag,Zec,Mal,Mat,Mar,Luk,Joh,Act,Rom,1Co,2Co,Gal,Eph,Phi,Col,1Th,2Th,1Ti,2Ti,Tit,Phm,Heb,Jam,1Pe,2Pe,1Jo,2Jo,3Jo,Jud,Rev

請以 **Markdown 表格格式**輸出（非 JSON），方便我貼回 Excel.

待分析經文：{raw_text}"""
            st.session_state.content_mode = "A"
        else:
            full_prompt = f"""你是一位精通多國語言的聖經專家與語言學教授.

### 模式 B：【英文文稿分析時】＝》一定要產出W＋P Excel格式（Markdown表格）
一定要取足"高級/中高級單字15個＋片語15個"！！！！！！！！！
⚠️ 輸出格式要求：請使用 **Markdown 表格格式**：

 【W Sheet - 重點要求：取高級/中高級單字15個＋片語15個】
| No | Word/Phrase| Chinese | Synonym+中文對照 | Antonym＋中文對照 | 全句聖經中英對照例句 |
|----|-------------|-------|---------|---------|---------|---------------|
| 1 | steadfast 堅定不移的 | firm | wavering | 1Co 15:58 Therefore... |
⭐️No：請從文稿前5行找到經卷＋經節填入欄位

【P Sheet - 文稿段落】
| Paragraph | English Refinement | 中英夾雜講章 |
|-----------|-------------------|--------------|
| 1 | We need to be steadfast... | 我們需要 (**steadfast**) ... |

【Grammar List - 重點要求：6 句 × 每句4個解析】
| No | Original Sentence (from text) | Grammar Rule | Analysis & Example (1️⃣2️⃣3️⃣...5️⃣) |
|----|------------------------------|--------------|-----------------------------------|
| 1 | [文稿中的第1個精選句] | [文法規則名稱] | 1️⃣[分段解析+語法標籤]...<br>2️⃣[詞性辨析]...<br>3️⃣[修辭與結構或遞進邏輯]...<br>4️⃣[語意解釋]...<br>...|
🔹 Grammar List：從文稿中精選 6 個**最具教學價值**的句子
   嚴格遵守符號化格式＋嚴格提供中英對照詳細規範如下：
   例箴17:7Fine speech is not becoming to a fool; still less is false speech to a prince.
1️⃣[分段解析+語法標籤]： 1st clause：」Fine speech" is not becoming to a fool
                    2nd clause：still less is "false speech" to a prince
   語法標籤必須標註出Grammar labels (must be identified):
   主語 (Subject)、動詞 (Verb)、補語 (Complement) 或 修飾語。
* 主語 (Subject): Fine speech（Elegant words優美的言辭/Refined talk高雅的談吐）...等等
* 動詞 (Verb): is (Linking verb/Copula 系動詞)。
* 形容詞Adjective/Complement補語 (Complement): becoming(Adjective meaning「fitting相稱的」or「appropriate得體的」..等等
* 介系詞短語(Prepositional Phrase): to a fool。(Specifies the inappropriate recipient).
2️⃣詞性辨析Part-of-Speech Distinction： 若單字有歧義（例如 becoming 是動詞還是形容詞）...等等
If a word has potential ambiguity (for example, becoming can be a verb or an adjective), 
its part of speech and meaning in this sentence must be clearly identified...等等
* becoming
    * Possible forms:
        * Verb (to become)
        * Adjective (suitable, fitting)
    * In this sentence: adjective
    * Meaning here: appropriate, fitting, proper

3️⃣修辭與結構Rhetoric and Structure：Identify and explain specific grammatical phenomena, such as:如 倒裝 (Inversion)、省略 (Ellipsis)  或遞進邏輯 (Still less / A fortiori)。
4️⃣語意解釋：This grammatical structure strengthens the verse』s logic by contrasting inner character with outer speech.
  請以 **Markdown 表格格式**輸出（非 JSON）.

待分析文稿：{raw_text}"""
            st.session_state.content_mode = "B"

        st.session_state.original_text = raw_text
        st.session_state.main_input_value = full_prompt
        st.session_state.is_prompt_generated = True
        st.session_state.ref_number = f"REF_{dt.datetime.now().strftime('%m%d%H%M')}"
        st.session_state.current_entry = {
            'v1': '', 'v2': '', 'w_sheet': '', 
            'p_sheet': '', 'grammar_list': '', 'other': ''
        }
        st.session_state.saved_entries = []

    # ═══════════════════════════════════════════════════════════════
    # 快速功能區（空白資料建立器 + 編輯現有資料）
    # ═══════════════════════════════════════════════════════════════
    st.markdown("<h6>⚡ 快速功能</h6>", unsafe_allow_html=True)
    
    quick_cols = st.columns([1, 1, 2])
    
    with quick_cols[0]:
        with st.expander("➕ 建立空白資料", expanded=False):
            blank_mode = st.selectbox("選擇模式", ["Mode A (經文)", "Mode B (文稿)"], key="blank_mode")
            blank_ref = st.text_input("參考編號", value=f"BLANK_{dt.datetime.now().strftime('%m%d%H%M')}", key="blank_ref")
            
            if st.button("🆕 建立空白資料結構", use_container_width=True):
                if "Mode A" in blank_mode:
                    blank_structure = {
                        "ref": blank_ref,
                        "original": "[空白資料-待填入經文]",
                        "v1_content": "Ref.\tEnglish (ESV)\tChinese\tSyn/Ant\tGrammar\n",
                        "v2_content": "Ref.\t口語訳\tGrammar\tNote\tKRF\tKorean Syn/Ant\tTHSV11\n",
                        "w_sheet": "",
                        "p_sheet": "",
                        "grammar_list": "",
                        "other": "",
                        "saved_sheets": ["V1 Sheet", "V2 Sheet"],
                        "type": "Scripture",
                        "mode": "A",
                        "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "blank_template": True
                    }
                else:
                    blank_structure = {
                        "ref": blank_ref,
                        "original": "[空白資料-待填入文稿]",
                        "v1_content": "",
                        "v2_content": "",
                        "w_sheet": "No\tWord/Phrase\tChinese\tSynonym+中文對照\tAntonym+中文對照\t全句聖經中英對照例句\n",
                        "p_sheet": "Paragraph\tEnglish Refinement\t中英夾雜講章\n",
                        "grammar_list": "No\tOriginal Sentence\tGrammar Rule\tAnalysis & Example\n",
                        "other": "",
                        "saved_sheets": ["W Sheet", "P Sheet", "Grammar List"],
                        "type": "Document",
                        "mode": "B",
                        "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "blank_template": True
                    }
                
                st.session_state.sentences[blank_ref] = blank_structure
                save_sentences(st.session_state.sentences)
                
                st.session_state.edit_mode = True
                st.session_state.edit_ref = blank_ref
                st.session_state.current_entry = {
                    'v1': blank_structure['v1_content'],
                    'v2': blank_structure['v2_content'],
                    'w_sheet': blank_structure['w_sheet'],
                    'p_sheet': blank_structure['p_sheet'],
                    'grammar_list': blank_structure['grammar_list'],
                    'other': ''
                }
                st.session_state.saved_entries = blank_structure['saved_sheets']
                st.success(f"✅ 已建立空白資料：{blank_ref}")
                st.rerun()
    
    with quick_cols[1]:
        with st.expander("✏️ 編輯現有資料", expanded=False):
            if st.session_state.sentences:
                edit_select = st.selectbox(
                    "選擇要編輯的資料",
                    list(st.session_state.sentences.keys()),
                    format_func=lambda x: f"{x} ({st.session_state.sentences[x].get('type', 'Unknown')})",
                    key="edit_select"
                )
                
                if st.button("📝 載入編輯", use_container_width=True):
                    item = st.session_state.sentences[edit_select]
                    st.session_state.edit_mode = True
                    st.session_state.edit_ref = edit_select
                    st.session_state.current_entry = {
                        'v1': item.get('v1_content', ''),
                        'v2': item.get('v2_content', ''),
                        'w_sheet': item.get('w_sheet', ''),
                        'p_sheet': item.get('p_sheet', ''),
                        'grammar_list': item.get('grammar_list', ''),
                        'other': item.get('other', '')
                    }
                    st.session_state.saved_entries = item.get('saved_sheets', [])
                    st.rerun()
            else:
                st.info("尚無資料可編輯")
    
    with quick_cols[2]:
        if st.session_state.get('edit_mode') and st.session_state.get('edit_ref'):
            st.info(f"📝 目前正在編輯：**{st.session_state.edit_ref}**")
            if st.button("❌ 結束編輯模式", use_container_width=True):
                st.session_state.edit_mode = False
                st.session_state.edit_ref = None
                st.session_state.saved_entries = []
                st.session_state.current_entry = {
                    'v1': '', 'v2': '', 'w_sheet': '', 
                    'p_sheet': '', 'grammar_list': '', 'other': ''
                }
                st.rerun()
        else:
            st.caption("💡 使用左側按鈕快速建立或編輯資料")

    st.divider()

    # ═══════════════════════════════════════════════════════════════
    # 編輯模式介面
    # ═══════════════════════════════════════════════════════════════
    if st.session_state.get('edit_mode') and st.session_state.get('edit_ref'):
        st.markdown(f"<h6>✏️ 編輯模式：{st.session_state.edit_ref}</h6>", unsafe_allow_html=True)
        
        item = st.session_state.sentences.get(st.session_state.edit_ref, {})
        current_mode = item.get('mode', 'A')
        
        if current_mode == 'A':
            edit_tabs = st.tabs(["V1 Sheet", "V2 Sheet", "其他補充", "儲存"])
            
            with edit_tabs[0]:
                new_v1 = st.text_area(
                    "V1 Sheet 內容",
                    value=st.session_state.current_entry['v1'],
                    height=300,
                    key="edit_v1"
                )
                st.session_state.current_entry['v1'] = new_v1
            
            with edit_tabs[1]:
                new_v2 = st.text_area(
                    "V2 Sheet 內容",
                    value=st.session_state.current_entry['v2'],
                    height=300,
                    key="edit_v2"
                )
                st.session_state.current_entry['v2'] = new_v2
            
            with edit_tabs[2]:
                new_other = st.text_area(
                    "其他補充",
                    value=st.session_state.current_entry['other'],
                    height=200,
                    key="edit_other"
                )
                st.session_state.current_entry['other'] = new_other
            
            with edit_tabs[3]:
                st.write("確認修改後儲存：")
                save_cols = st.columns(2)
                
                with save_cols[0]:
                    if st.button("💾 存到本地", use_container_width=True, key="save_local_a"):
                        st.session_state.sentences[st.session_state.edit_ref].update({
                            'v1_content': st.session_state.current_entry['v1'],
                            'v2_content': st.session_state.current_entry['v2'],
                            'other': st.session_state.current_entry['other'],
                            'saved_sheets': ['V1 Sheet', 'V2 Sheet'] if st.session_state.current_entry['v1'] else [],
                            'date_added': dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        save_sentences(st.session_state.sentences)
                        st.success("✅ 已更新本地資料！")
                
                with save_cols[1]:
                    if st.button("💾 存到本地+雲端", use_container_width=True, key="save_both_a"):
                        st.session_state.sentences[st.session_state.edit_ref].update({
                            'v1_content': st.session_state.current_entry['v1'],
                            'v2_content': st.session_state.current_entry['v2'],
                            'other': st.session_state.current_entry['other'],
                            'saved_sheets': ['V1 Sheet', 'V2 Sheet'] if st.session_state.current_entry['v1'] else [],
                            'date_added': dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        save_sentences(st.session_state.sentences)
                        # 同步到 Google Sheets
                        success, msg = save_to_google_sheets(st.session_state.sentences[st.session_state.edit_ref])
                        if success:
                            st.success("✅ 已更新本地與 Google Sheets！")
                        else:
                            st.error(f"❌ Google Sheets 失敗：{msg}")
        
        else:  # Mode B
            edit_tabs = st.tabs(["W Sheet", "P Sheet", "Grammar List", "其他補充", "儲存"])
            
            with edit_tabs[0]:
                new_w = st.text_area(
                    "W Sheet 內容",
                    value=st.session_state.current_entry['w_sheet'],
                    height=300,
                    key="edit_w"
                )
                st.session_state.current_entry['w_sheet'] = new_w
            
            with edit_tabs[1]:
                new_p = st.text_area(
                    "P Sheet 內容",
                    value=st.session_state.current_entry['p_sheet'],
                    height=300,
                    key="edit_p"
                )
                st.session_state.current_entry['p_sheet'] = new_p
            
            with edit_tabs[2]:
                new_g = st.text_area(
                    "Grammar List 內容",
                    value=st.session_state.current_entry['grammar_list'],
                    height=300,
                    key="edit_g"
                )
                st.session_state.current_entry['grammar_list'] = new_g
            
            with edit_tabs[3]:
                new_other = st.text_area(
                    "其他補充",
                    value=st.session_state.current_entry['other'],
                    height=200,
                    key="edit_other_b"
                )
                st.session_state.current_entry['other'] = new_other
            
            with edit_tabs[4]:
                st.write("確認修改後儲存：")
                save_cols = st.columns(2)
                
                with save_cols[0]:
                    if st.button("💾 存到本地", use_container_width=True, key="save_local_b"):
                        st.session_state.sentences[st.session_state.edit_ref].update({
                            'w_sheet': st.session_state.current_entry['w_sheet'],
                            'p_sheet': st.session_state.current_entry['p_sheet'],
                            'grammar_list': st.session_state.current_entry['grammar_list'],
                            'other': st.session_state.current_entry['other'],
                            'saved_sheets': ['W Sheet', 'P Sheet', 'Grammar List'],
                            'date_added': dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        save_sentences(st.session_state.sentences)
                        st.success("✅ 已更新本地資料！")
                
                with save_cols[1]:
                    if st.button("💾 存到本地+雲端", use_container_width=True, key="save_both_b"):
                        st.session_state.sentences[st.session_state.edit_ref].update({
                            'w_sheet': st.session_state.current_entry['w_sheet'],
                            'p_sheet': st.session_state.current_entry['p_sheet'],
                            'grammar_list': st.session_state.current_entry['grammar_list'],
                            'other': st.session_state.current_entry['other'],
                            'saved_sheets': ['W Sheet', 'P Sheet', 'Grammar List'],
                            'date_added': dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        save_sentences(st.session_state.sentences)
                        success, msg = save_to_google_sheets(st.session_state.sentences[st.session_state.edit_ref])
                        if success:
                            st.success("✅ 已更新本地與 Google Sheets！")
                        else:
                            st.error(f"❌ Google Sheets 失敗：{msg}")
        
        st.divider()

    # ═══════════════════════════════════════════════════════════════
    # 主要功能區（保留原 UI）
    # ═══════════════════════════════════════════════════════════════
    st.markdown("<h6>📝 AI 分析工作流程</h6>", unsafe_allow_html=True)
    
    # STEP 1: 輸入區
    with st.expander("步驟 1：輸入經文或文稿", expanded=not st.session_state.is_prompt_generated):
        raw_input = st.text_area(
            "原始輸入",
            height=200,
            value=st.session_state.get('raw_input_value', ''),
            placeholder="請在此貼上內容：\n• 經文格式：31:6 可以把濃酒給將亡的人喝...\n• 文稿格式：直接貼上英文講稿",
            label_visibility="collapsed",
            key="raw_input_temp"
        )
        
        if not st.session_state.is_prompt_generated:
            if st.button("⚡ 產生完整分析指令", use_container_width=True, type="primary"):
                generate_full_prompt()
                st.rerun()

    # STEP 2: Prompt 產生後顯示
    if st.session_state.is_prompt_generated:
        with st.expander("步驟 2：複製 Prompt 到 AI", expanded=False):
            st.caption("複製以下內容，貼到 GPT/Kimi/Gemini 進行分析")
            
            components.html(
                f"""
                <textarea
                    readonly
                    onclick="this.select()"
                    style="
                        width:100%;
                        height:250px;
                        padding:12px;
                        font-size:14px;
                        line-height:1.5;
                        border-radius:8px;
                        border:1px solid #ccc;
                        box-sizing:border-box;
                        background-color:#f8f9fa;
                    "
                >{st.session_state.get('main_input_value','')}</textarea>
                """,
                height=280
            )
            
            cols = st.columns(2)
            with cols[0]:
                st.link_button("🌙 開啟 Kimi", "https://kimi.moonshot.cn", use_container_width=True)
            with cols[1]:
                st.link_button("🔍 開啟 Gemini", "https://gemini.google.com", use_container_width=True)

        # STEP 3: 多工作表收集區
        with st.expander("步驟 3：分批貼上 AI 分析結果", expanded=True):
            st.info("💡 可以分批貼上 V1、V2、W Sheet、P Sheet 等，貼好一個存一個，最後統一儲存")
            
            if st.session_state.content_mode == "A":
                sheet_options = ["V1 Sheet", "V2 Sheet", "其他補充"]
            else:
                sheet_options = ["W Sheet", "P Sheet", "Grammar List", "其他補充"]
            
            selected_sheet = st.selectbox("選擇要貼上的工作表", sheet_options)
            
            sheet_content = st.text_area(
                f"貼上 {selected_sheet} 內容",
                height=200,
                key=f"input_{selected_sheet.replace(' ', '_')}"
            )
            
            col_temp, col_view = st.columns([1, 3])
            with col_temp:
                if st.button("➕ 暫存此工作表", use_container_width=True):
                    key_map = {
                        "V1 Sheet": "v1",
                        "V2 Sheet": "v2", 
                        "W Sheet": "w_sheet",
                        "P Sheet": "p_sheet",
                        "Grammar List": "grammar_list",
                        "其他補充": "other"
                    }
                    key = key_map.get(selected_sheet, 'other')
                    st.session_state.current_entry[key] = sheet_content
                    if selected_sheet not in st.session_state.saved_entries:
                        st.session_state.saved_entries.append(selected_sheet)
                    st.success(f"✅ {selected_sheet} 已暫存！")
                    st.rerun()
            
            with col_view:
                if st.session_state.saved_entries:
                    st.write("📋 已暫存：", " | ".join([f"✅ {s}" for s in st.session_state.saved_entries]))
            
            if st.session_state.saved_entries:
                with st.expander("👁️ 預覽已暫存的內容"):
                    for sheet in st.session_state.saved_entries:
                        key_map = {
                            "V1 Sheet": "v1", "V2 Sheet": "v2",
                            "W Sheet": "w_sheet", "P Sheet": "p_sheet",
                            "Grammar List": "grammar_list", "其他補充": "other"
                        }
                        key = key_map.get(sheet, 'other')
                        content = st.session_state.current_entry.get(key, '')
                        if content:
                            st.write(f"**{sheet}：**")
                            st.code(content[:200] + "..." if len(content) > 200 else content)

        # STEP 4: 統一儲存區
        with st.expander("步驟 4：儲存到資料庫", expanded=True):
            st.caption("確認所有工作表都暫存後，填寫資訊並儲存")
            
            def get_default_ref():
                v1_content = st.session_state.current_entry.get('v1', '')
                if v1_content:
                    lines = v1_content.strip().split('\n')
                    for line in lines[1:]:
                        cols = line.split('\t')
                        if len(cols) > 0 and cols[0].strip():
                            return cols[0].strip()
                
                w_content = st.session_state.current_entry.get('w_sheet', '')
                if w_content:
                    lines = w_content.strip().split('\n')
                    for line in lines[1:]:
                        cols = line.split('\t')
                        if len(cols) > 0 and cols[0].strip():
                            return cols[0].strip()
                
                return f"REF_{dt.datetime.now().strftime('%m%d%H%M')}"
            
            st.markdown("**📁 檔名（可手動修改）**")
            ref_input = st.text_input(
                "Ref / 檔名", 
                value=get_default_ref(),
                key="ref_no_input"
            )
            
            type_select = st.selectbox(
                "類型",
                ["Scripture", "Document", "Vocabulary", "Grammar", "Sermon"],
                index=0 if st.session_state.content_mode == "A" else 1,
                key="type_select"
            )
            
            btn_cols = st.columns(2)
            
            with btn_cols[0]:
                if st.button("💾 僅存本地", use_container_width=True):
                    if not st.session_state.saved_entries:
                        st.error("請先至少暫存一個工作表！")
                    else:
                        try:
                            ref = ref_input
                            full_data = {
                                "ref": ref,
                                "original": st.session_state.original_text,
                                "prompt": st.session_state.main_input_value,
                                "v1_content": st.session_state.current_entry['v1'],
                                "v2_content": st.session_state.current_entry['v2'],
                                "w_sheet": st.session_state.current_entry['w_sheet'],
                                "p_sheet": st.session_state.current_entry['p_sheet'],
                                "grammar_list": st.session_state.current_entry['grammar_list'],
                                "other": st.session_state.current_entry['other'],
                                "saved_sheets": st.session_state.saved_entries,
                                "type": type_select,
                                "mode": st.session_state.content_mode,
                                "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                            st.session_state.sentences[ref] = full_data
                            save_sentences(st.session_state.sentences)
                            st.success(f"✅ 已存本地：{ref}")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ 儲存失敗：{str(e)}")
            
            with btn_cols[1]:
                gc, sheet_id = get_google_sheets_client()
                if gc and sheet_id:
                    if st.button("☁️ 存到雲端", use_container_width=True, type="primary"):
                        if not st.session_state.saved_entries:
                            st.error("請先至少暫存一個工作表！")
                        else:
                            try:
                                full_data = {
                                    "ref": ref_input,
                                    "original": st.session_state.original_text,
                                    "v1_content": st.session_state.current_entry['v1'],
                                    "v2_content": st.session_state.current_entry['v2'],
                                    "w_sheet": st.session_state.current_entry['w_sheet'],
                                    "p_sheet": st.session_state.current_entry['p_sheet'],
                                    "grammar_list": st.session_state.current_entry['grammar_list'],
                                    "other": st.session_state.current_entry['other'],
                                    "saved_sheets": st.session_state.saved_entries,
                                    "type": type_select,
                                    "mode": st.session_state.content_mode,
                                    "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                                }
                                success, msg = save_to_google_sheets(full_data)
                                if success:
                                    st.session_state.sentences[ref_input] = full_data
                                    save_sentences(st.session_state.sentences)
                                    st.success(f"✅ 已存 Google Sheets：{ref_input}")
                                    st.balloons()
                                else:
                                    st.error(f"❌ Google Sheets 失敗：{msg}")
                            except Exception as e:
                                st.error(f"❌ Google Sheets 失敗：{str(e)}")
                else:
                    st.button("☁️ 存到雲端", disabled=True, use_container_width=True)

            if st.button("🔄 新的分析", use_container_width=True):
                keys_to_clear = [
                    'is_prompt_generated', 'main_input_value', 'original_text',
                    'content_mode', 'raw_input_value', 'ref_number', 'raw_input_temp',
                    'current_entry', 'saved_entries', 'ref_no_input'
                ]
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    # 儲存狀態顯示區
    st.divider()
    status_cols = st.columns([1, 1, 2])
    
    with status_cols[0]:
        total_local = len(st.session_state.get('sentences', {}))
        st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>💾 本地資料庫</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 16px; font-weight: bold; margin: 0;'>{total_local} 筆</p>", unsafe_allow_html=True)
    
    with status_cols[1]:
        gc, sheet_id = get_google_sheets_client()
        if gc and sheet_id:
            st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>☁️ Google Sheets</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 16px; font-weight: bold; margin: 0; color: #28a745;'>✅ 已連線</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>☁️ Google Sheets</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 16px; font-weight: bold; margin: 0; color: #dc3545;'>❌ 未設定</p>", unsafe_allow_html=True)
    
    with status_cols[2]:
        if st.session_state.get('sentences'):
            recent = list(st.session_state.sentences.values())[-3:]
            st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>🕐 最近儲存：</p>", unsafe_allow_html=True)
            for item in reversed(recent):
                sheets = item.get('saved_sheets', ['未知'])
                st.caption(f"• {item.get('ref', 'N/A')} ({', '.join(sheets)})")

    # 已存資料瀏覽器
    with st.expander("📋 查看已儲存的資料", expanded=False):
        if not st.session_state.get('sentences'):
            st.info("資料庫是空的，請先儲存資料")
        else:
            ref_list = list(st.session_state.sentences.keys())
            selected_ref = st.selectbox(
                "選擇資料項目", 
                ref_list,
                format_func=lambda x: f"{x} - {st.session_state.sentences[x].get('date_added', '無日期')}"
            )
            
            if selected_ref:
                item = st.session_state.sentences[selected_ref]
                st.subheader(f"📄 {selected_ref}")
                
                cols = st.columns(3)
                with cols[0]:
                    st.write(f"**類型：** {item.get('type', 'N/A')}")
                with cols[1]:
                    st.write(f"**模式：** {item.get('mode', 'N/A')}")
                with cols[2]:
                    st.write(f"**日期：** {item.get('date_added', 'N/A')}")
                
                with st.expander("📝 原始輸入"):
                    st.text(item.get('original', '無'))
                
                saved_sheets = item.get('saved_sheets', [])
                if saved_sheets:
                    st.write(f"**已儲存工作表：** {', '.join(saved_sheets)}")
                    tabs_sheets = st.tabs(saved_sheets)
                    for i, sheet in enumerate(saved_sheets):
                        with tabs_sheets[i]:
                            key_map = {
                                "V1 Sheet": "v1_content", "V2 Sheet": "v2_content",
                                "W Sheet": "w_sheet", "P Sheet": "p_sheet",
                                "Grammar List": "grammar_list", "其他補充": "other"
                            }
                            content = item.get(key_map.get(sheet, 'other'), '')
                            if content:
                                st.text_area("內容", value=content, height=250, disabled=True)
                            else:
                                st.info("無內容")
                
                st.divider()
                btn_cols = st.columns([1, 1, 2])
                
                with btn_cols[0]:
                    if st.button("✏️ 載入編輯", key=f"edit_{selected_ref}"):
                        st.session_state.raw_input_value = item.get('original', '')
                        st.session_state.current_entry = {
                            'v1': item.get('v1_content', ''), 'v2': item.get('v2_content', ''),
                            'w_sheet': item.get('w_sheet', ''), 'p_sheet': item.get('p_sheet', ''),
                            'grammar_list': item.get('grammar_list', ''), 'other': item.get('other', '')
                        }
                        st.session_state.saved_entries = saved_sheets
                        st.session_state.ref_number = selected_ref
                        st.session_state.is_prompt_generated = True
                        st.session_state.original_text = item.get('original', '')
                        st.session_state.main_input_value = item.get('prompt', '')
                        st.session_state.content_mode = item.get('mode', 'A')
                        st.rerun()
                
                with btn_cols[1]:
                    if st.button("🗑️ 刪除", key=f"del_{selected_ref}"):
                        del st.session_state.sentences[selected_ref]
                        save_sentences(st.session_state.sentences)
                        st.rerun()

    # 簡易搜尋
    with st.expander("🔍 搜尋資料", expanded=False):
        search_kw = st.text_input("輸入關鍵字", placeholder="搜尋 Ref_No 或內容...")
        if search_kw:
            results = []
            for ref, item in st.session_state.sentences.items():
                if (search_kw.lower() in ref.lower() or 
                    search_kw.lower() in item.get('original', '').lower()):
                    results.append(f"• **{ref}** ({item.get('date_added', '')})")
            if results:
                st.write(f"找到 {len(results)} 筆：")
                for r in results:
                    st.markdown(r)
            else:
                st.info("無符合資料")

    # 底部統計
    st.divider()
    total_count = len(st.session_state.get('sentences', {}))
    st.caption(f"💾 資料庫：{total_count} 筆")
    if st.session_state.get('sentences', {}):
        json_str = json.dumps(st.session_state.sentences, ensure_ascii=False, indent=2)
        st.download_button(
            "⬇️ 備份 JSON",
            json_str,
            file_name=f"backup_{dt.datetime.now().strftime('%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )
