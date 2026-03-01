# ===================================================================
# 基礎架構版本 - 僅 TAB4 功能（修正版）
# 目標：穩定的 Google Sheets 連線 + 資料持久化
# ===================================================================
import streamlit as st
import os
import json
import datetime as dt
import re
import gspread
from google.oauth2.service_account import Credentials
from io import StringIO
import csv

# ---------- 頁面設定（必須在第一個 st 命令）----------
st.set_page_config(layout="wide", page_title="Bible Study DB - Base")

# ---------- 資料庫設定 ----------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
SENTENCES_FILE = os.path.join(DATA_DIR, "sentences.json")

# ---------- Google Sheets 連線（修正回傳值）----------
def get_google_sheets_client():
    """重新建立 Google Sheets 連線，回傳 (gc, sheet_id) 或 (None, None)"""
    try:
        if "gcp_service_account" not in st.secrets:
            st.sidebar.error("❌ 找不到 gcp_service_account")
            return None, None
        
        if "sheets" not in st.secrets or "spreadsheet_id" not in st.secrets["sheets"]:
            st.sidebar.error("❌ 找不到 spreadsheet_id")
            return None, None
            
        gcp_sa = st.secrets["gcp_service_account"]
        sheet_id = st.secrets["sheets"]["spreadsheet_id"]
        
        creds = Credentials.from_service_account_info(
            gcp_sa,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        gc = gspread.authorize(creds)
        return gc, sheet_id  # 永遠回傳兩個值
        
    except Exception as e:
        st.sidebar.error(f"連線失敗: {e}")
        return None, None  # 永遠回傳兩個值

# ---------- 本地檔案操作 ----------
def load_sentences():
    """安全載入本地資料庫"""
    if not os.path.exists(SENTENCES_FILE):
        return {}
    
    try:
        with open(SENTENCES_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        backup_name = f"{SENTENCES_FILE}.backup_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            os.rename(SENTENCES_FILE, backup_name)
            st.sidebar.warning(f"⚠️ 資料庫損毀，已備份")
        except:
            pass
        return {}
    except Exception as e:
        st.sidebar.error(f"載入失敗: {e}")
        return {}

def save_sentences(data):
    """原子寫入 + 自動備份"""
    if not isinstance(data, dict):
        return False
    
    try:
        temp_file = f"{SENTENCES_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 備份舊檔
        if os.path.exists(SENTENCES_FILE):
            backup_file = f"{SENTENCES_FILE}.backup_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                os.replace(SENTENCES_FILE, backup_file)
                # 清理舊備份
                backups = sorted([f for f in os.listdir(DATA_DIR) if f.startswith("sentences.json.backup_")])
                for old in backups[:-5]:
                    os.remove(os.path.join(DATA_DIR, old))
            except:
                pass
        
        os.replace(temp_file, SENTENCES_FILE)
        return True
        
    except Exception as e:
        st.sidebar.error(f"儲存失敗: {e}")
        return False

# ---------- 解析內容 ----------
def parse_content_to_rows(content, expected_cols=None):
    """解析 CSV 或 Markdown 表格"""
    if not content or not content.strip():
        return []
    
    rows = []
    lines = content.strip().split('\n')
    
    # Markdown 表格
    if '|' in content:
        for line in lines:
            line = line.strip()
            if line.startswith('|') and '---' not in line and line.replace('|', '').strip():
                cells = [re.sub(r'\*\*(.*?)\*\*', r'\1', c.strip()) 
                        for c in line.split('|')[1:-1]]
                if any(cells):
                    rows.append(cells)
    else:
        # CSV with \t delimiter
        reader = csv.reader(StringIO(content), delimiter='\t')
        for row in reader:
            if any(row):
                row = [re.sub(r'\*\*(.*?)\*\*', r'\1', c) for c in row]
                rows.append(row)
    
    # 跳過標題列
    if rows and any(k in str(rows[0]) for k in ['Ref', 'No', 'Word', 'Paragraph', 'English', 'Chinese']):
        rows = rows[1:]
    
    # 欄位數對齊
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

# ---------- Google Sheets 操作 ----------
def save_to_gsheet(gc, sheet_id, ref, mode, data_dict):
    """儲存資料到對應工作表"""
    if not gc or not sheet_id:
        return False, "未連線"
    
    try:
        sh = gc.open_by_key(sheet_id)
        
        if mode == 'A':
            # V1_Sheet
            try:
                ws = sh.worksheet("V1_Sheet")
            except:
                ws = sh.add_worksheet("V1_Sheet", rows=1000, cols=6)
                ws.append_row(["Ref", "English", "Chinese", "Syn/Ant", "Grammar", "Note"])
            
            rows = parse_content_to_rows(data_dict.get('v1', ''), 5)
            if rows:
                ws.append_rows([[ref] + r for r in rows])
            
            # V2_Sheet
            try:
                ws = sh.worksheet("V2_Sheet")
            except:
                ws = sh.add_worksheet("V2_Sheet", rows=1000, cols=7)
                ws.append_row(["Ref", "Japanese", "Grammar", "Note", "Korean", "Korean_SA", "Thai"])
            
            rows = parse_content_to_rows(data_dict.get('v2', ''), 6)
            if rows:
                ws.append_rows([[ref] + r for r in rows])
                
        else:  # Mode B
            # W_Sheet
            try:
                ws = sh.worksheet("W_Sheet")
            except:
                ws = sh.add_worksheet("W_Sheet", rows=1000, cols=6)
                ws.append_row(["Ref", "No", "Word", "Chinese", "Synonym", "Antonym"])
            
            rows = parse_content_to_rows(data_dict.get('w', ''), 5)
            if rows:
                ws.append_rows([[ref] + r for r in rows])
            
            # P_Sheet
            try:
                ws = sh.worksheet("P_Sheet")
            except:
                ws = sh.add_worksheet("P_Sheet", rows=1000, cols=3)
                ws.append_row(["Ref", "English", "Chinese"])
            
            rows = parse_content_to_rows(data_dict.get('p', ''), 2)
            if rows:
                ws.append_rows([[ref] + r for r in rows])
            
            # Grammar_List
            try:
                ws = sh.worksheet("Grammar_List")
            except:
                ws = sh.add_worksheet("Grammar_List", rows=1000, cols=4)
                ws.append_row(["Ref", "Sentence", "Rule", "Analysis"])
            
            rows = parse_content_to_rows(data_dict.get('g', ''), 3)
            if rows:
                ws.append_rows([[ref] + r for r in rows])
        
        return True, "儲存成功"
        
    except Exception as e:
        return False, str(e)

def load_from_gsheet(gc, sheet_id):
    """從 Google Sheets 載入所有資料"""
    if not gc or not sheet_id:
        return {}
    
    all_data = {}
    try:
        sh = gc.open_by_key(sheet_id)
        
        # V1_Sheet
        try:
            ws = sh.worksheet("V1_Sheet")
            rows = ws.get_all_values()
            for row in rows[1:]:
                if len(row) >= 6:
                    ref = row[0]
                    if ref not in all_data:
                        all_data[ref] = {"ref": ref, "mode": "A", "v1": "", "v2": "", "w": "", "p": "", "g": ""}
                    all_data[ref]["v1"] += "\t".join(row[:6]) + "\n"
        except:
            pass
        
        # V2_Sheet
        try:
            ws = sh.worksheet("V2_Sheet")
            rows = ws.get_all_values()
            for row in rows[1:]:
                if len(row) >= 7:
                    ref = row[0]
                    if ref in all_data:
                        all_data[ref]["v2"] += "\t".join(row[:7]) + "\n"
        except:
            pass
        
        # W_Sheet
        try:
            ws = sh.worksheet("W_Sheet")
            rows = ws.get_all_values()
            for row in rows[1:]:
                if len(row) >= 6:
                    ref = row[0]
                    if ref not in all_data:
                        all_data[ref] = {"ref": ref, "mode": "B", "v1": "", "v2": "", "w": "", "p": "", "g": ""}
                    all_data[ref]["w"] += "\t".join(row[:6]) + "\n"
        except:
            pass
        
        # P_Sheet
        try:
            ws = sh.worksheet("P_Sheet")
            rows = ws.get_all_values()
            for row in rows[1:]:
                if len(row) >= 3:
                    ref = row[0]
                    if ref in all_data:
                        all_data[ref]["p"] += "\t".join(row[:3]) + "\n"
        except:
            pass
        
        # Grammar_List
        try:
            ws = sh.worksheet("Grammar_List")
            rows = ws.get_all_values()
            for row in rows[1:]:
                if len(row) >= 4:
                    ref = row[0]
                    if ref in all_data:
                        all_data[ref]["g"] += "\t".join(row[:4]) + "\n"
        except:
            pass
        
        return all_data
        
    except Exception as e:
        st.sidebar.error(f"載入失敗: {e}")
        return {}

# ---------- 初始化 Session State ----------
if 'sentences' not in st.session_state:
    # 先嘗試本地載入
    local_data = load_sentences()
    
    if local_data:
        st.session_state.sentences = local_data
        st.sidebar.success(f"✅ 本地載入 {len(local_data)} 筆")
    else:
        # 嘗試 Google Sheets
        gc, sheet_id = get_google_sheets_client()
        if gc and sheet_id:
            sheets_data = load_from_gsheet(gc, sheet_id)
            if sheets_data:
                st.session_state.sentences = sheets_data
                save_sentences(sheets_data)
                st.sidebar.success(f"✅ 雲端載入 {len(sheets_data)} 筆")
            else:
                st.session_state.sentences = {}
                st.sidebar.info("ℹ️ 資料庫空白")
        else:
            st.session_state.sentences = {}
            st.sidebar.warning("⚠️ 未連線 Google Sheets")

if 'edit_ref' not in st.session_state:
    st.session_state.edit_ref = None

# ---------- 側邊欄 ----------
with st.sidebar:
    st.title("💾 資料庫控制台")
    
    # 檢查連線（每次重新取得）
    gc, sheet_id = get_google_sheets_client()
    
    if gc and sheet_id:
        st.success("✅ Google Sheets 已連線")
        try:
            sh = gc.open_by_key(sheet_id)
            sheets = sh.worksheets()
            st.caption(f"工作表: {len(sheets)}個")
            for ws in sheets:
                st.caption(f"• {ws.title}")
        except Exception as e:
            st.caption(f"無法讀取工作表: {e}")
    else:
        st.error("❌ Google Sheets 未連線")
        st.caption("請設定 secrets.toml")
    
    st.divider()
    st.caption(f"本地資料: {len(st.session_state.get('sentences', {}))}筆")
    
    # 手動同步
    if st.button("🔄 強制從雲端同步", use_container_width=True):
        gc, sheet_id = get_google_sheets_client()
        if gc and sheet_id:
            with st.spinner("同步中..."):
                sheets_data = load_from_gsheet(gc, sheet_id)
                if sheets_data:
                    st.session_state.sentences = sheets_data
                    save_sentences(sheets_data)
                    st.success(f"同步完成: {len(sheets_data)}筆")
                    st.rerun()
                else:
                    st.error("雲端無資料")

# ---------- 主介面 ----------
st.title("📚 聖經學習資料庫 - 基礎版")

# 取得連線（主介面使用）
gc, sheet_id = get_google_sheets_client()

# 新增資料區
with st.expander("➕ 新增資料", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        ref_input = st.text_input("參考編號 (如: Pro 31:6)", key="new_ref")
        mode = st.selectbox("模式", ["A (經文)", "B (文稿)"])
    with col2:
        st.caption("💡 模式A: V1+V2 Sheet")
        st.caption("💡 模式B: W+P+Grammar Sheet")
    
    if mode.startswith("A"):
        v1_content = st.text_area("V1 Sheet 內容 (用 \\t 分隔欄位)", 
                                   height=150, 
                                   placeholder="Ref\tEnglish\tChinese\tSyn/Ant\tGrammar",
                                   key="v1")
        v2_content = st.text_area("V2 Sheet 內容", 
                                   height=150,
                                   placeholder="Ref\tJapanese\tGrammar\tNote\tKorean\tKorean_SA\tThai", 
                                   key="v2")
    else:
        w_content = st.text_area("W Sheet 內容", 
                                  height=100,
                                  placeholder="Ref\tNo\tWord\tChinese\tSynonym\tAntonym", 
                                  key="w")
        p_content = st.text_area("P Sheet 內容", 
                                  height=100,
                                  placeholder="Ref\tEnglish\tChinese", 
                                  key="p")
        g_content = st.text_area("Grammar List 內容", 
                                  height=100,
                                  placeholder="Ref\tSentence\tRule\tAnalysis", 
                                  key="g")
    
    col_save1, col_save2 = st.columns(2)
    with col_save1:
        if st.button("💾 僅存本地", use_container_width=True):
            data = {
                "ref": ref_input,
                "mode": "A" if mode.startswith("A") else "B",
                "date": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            if mode.startswith("A"):
                data.update({"v1": v1_content, "v2": v2_content, "w": "", "p": "", "g": ""})
            else:
                data.update({"v1": "", "v2": "", "w": w_content, "p": p_content, "g": g_content})
            
            st.session_state.sentences[ref_input] = data
            save_sentences(st.session_state.sentences)
            st.success("✅ 已存本地")
    
    with col_save2:
        if gc and sheet_id:
            if st.button("☁️ 存到雲端", use_container_width=True, type="primary"):
                data = {
                    "ref": ref_input,
                    "mode": "A" if mode.startswith("A") else "B",
                    "date": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                if mode.startswith("A"):
                    data.update({"v1": v1_content, "v2": v2_content, "w": "", "p": "", "g": ""})
                else:
                    data.update({"v1": "", "v2": "", "w": w_content, "p": p_content, "g": g_content})
                
                success, msg = save_to_gsheet(gc, sheet_id, ref_input, data["mode"], data)
                if success:
                    st.session_state.sentences[ref_input] = data
                    save_sentences(st.session_state.sentences)
                    st.success("✅ 已存雲端+本地")
                else:
                    st.error(f"❌ {msg}")
        else:
            st.button("☁️ 存到雲端", disabled=True, use_container_width=True)
            st.caption("請先設定 Google Sheets")

# 資料列表
st.divider()
st.subheader(f"📋 已儲存資料 ({len(st.session_state.get('sentences', {}))}筆)")

if st.session_state.get('sentences'):
    for ref, item in list(st.session_state.sentences.items()):
        with st.expander(f"{ref} [{item.get('mode', '?')}]", expanded=False):
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.write(f"**日期:** {item.get('date', 'N/A')}")
                st.write(f"**模式:** {item.get('mode', 'N/A')}")
                
                has_content = []
                if item.get('v1'): has_content.append(f"V1 ({len(item['v1'])}字)")
                if item.get('v2'): has_content.append(f"V2 ({len(item['v2'])}字)")
                if item.get('w'): has_content.append(f"W ({len(item['w'])}字)")
                if item.get('p'): has_content.append(f"P ({len(item['p'])}字)")
                if item.get('g'): has_content.append(f"G ({len(item['g'])}字)")
                st.write(f"**內容:** {', '.join(has_content) if has_content else '無'}")
            
            with cols[1]:
                if st.button("✏️ 編輯", key=f"edit_{ref}", use_container_width=True):
                    st.session_state.edit_ref = ref
            
            with cols[2]:
                if st.button("🗑️ 刪除", key=f"del_{ref}", use_container_width=True):
                    del st.session_state.sentences[ref]
                    save_sentences(st.session_state.sentences)
                    st.rerun()
            
            # 顯示內容
            tabs_content = st.tabs(["V1", "V2", "W", "P", "G"])
            with tabs_content[0]:
                st.text(item.get('v1', '[無]'))
            with tabs_content[1]:
                st.text(item.get('v2', '[無]'))
            with tabs_content[2]:
                st.text(item.get('w', '[無]'))
            with tabs_content[3]:
                st.text(item.get('p', '[無]'))
            with tabs_content[4]:
                st.text(item.get('g', '[無]'))

# 編輯模式
if st.session_state.get('edit_ref') and st.session_state.edit_ref in st.session_state.sentences:
    st.divider()
    st.subheader(f"✏️ 編輯: {st.session_state.edit_ref}")
    item = st.session_state.sentences[st.session_state.edit_ref]
    
    if item.get('mode') == 'A':
        new_v1 = st.text_area("V1", value=item.get('v1', ''), height=150, key="edit_v1")
        new_v2 = st.text_area("V2", value=item.get('v2', ''), height=150, key="edit_v2")
        
        if st.button("💾 更新", key="update_a"):
            item['v1'] = new_v1
            item['v2'] = new_v2
            item['date'] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
            save_sentences(st.session_state.sentences)
            
            # 同步到 Google Sheets
            gc, sheet_id = get_google_sheets_client()
            if gc and sheet_id:
                save_to_gsheet(gc, sheet_id, st.session_state.edit_ref, 'A', item)
            
            st.session_state.edit_ref = None
            st.rerun()
    else:
        new_w = st.text_area("W", value=item.get('w', ''), height=100, key="edit_w")
        new_p = st.text_area("P", value=item.get('p', ''), height=100, key="edit_p")
        new_g = st.text_area("G", value=item.get('g', ''), height=100, key="edit_g")
        
        if st.button("💾 更新", key="update_b"):
            item['w'] = new_w
            item['p'] = new_p
            item['g'] = new_g
            item['date'] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
            save_sentences(st.session_state.sentences)
            
            gc, sheet_id = get_google_sheets_client()
            if gc and sheet_id:
                save_to_gsheet(gc, sheet_id, st.session_state.edit_ref, 'B', item)
            
            st.session_state.edit_ref = None
            st.rerun()
    
    if st.button("❌ 取消編輯"):
        st.session_state.edit_ref = None
        st.rerun()

# 底部工具
st.divider()
col_tool1, col_tool2 = st.columns(2)
with col_tool1:
    if st.session_state.get('sentences'):
        json_str = json.dumps(st.session_state.sentences, ensure_ascii=False, indent=2)
        st.download_button("⬇️ 下載 JSON", json_str, 
                          file_name=f"backup_{dt.datetime.now().strftime('%m%d_%H%M')}.json",
                          mime="application/json", use_container_width=True)

with col_tool2:
    if st.checkbox("🛠️ 開發者模式"):
        gc, sheet_id = get_google_sheets_client()
        if gc and sheet_id:
            if st.button("🚨 重建工作表", use_container_width=True):
                try:
                    sh = gc.open_by_key(sheet_id)
                    for name in ["V1_Sheet", "V2_Sheet", "W_Sheet", "P_Sheet", "Grammar_List"]:
                        try:
                            ws = sh.worksheet(name)
                            sh.del_worksheet(ws)
                        except:
                            pass
                    
                    sh.add_worksheet("V1_Sheet", rows=1000, cols=6).append_row(["Ref", "English", "Chinese", "Syn/Ant", "Grammar", "Note"])
                    sh.add_worksheet("V2_Sheet", rows=1000, cols=7).append_row(["Ref", "Japanese", "Grammar", "Note", "Korean", "Korean_SA", "Thai"])
                    sh.add_worksheet("W_Sheet", rows=1000, cols=6).append_row(["Ref", "No", "Word", "Chinese", "Synonym", "Antonym"])
                    sh.add_worksheet("P_Sheet", rows=1000, cols=3).append_row(["Ref", "English", "Chinese"])
                    sh.add_worksheet("Grammar_List", rows=1000, cols=4).append_row(["Ref", "Sentence", "Rule", "Analysis"])
                    
                    st.success("✅ 重建完成")
                    st.rerun()
                except Exception as e:
                    st.error(f"重建失敗: {e}")

# 狀態顯示
st.caption(f"💾 本地: {len(st.session_state.get('sentences', {}))}筆 | 時間: {dt.datetime.now().strftime('%H:%M:%S')}")
