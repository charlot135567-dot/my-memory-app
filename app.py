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
import toml

# ---------- 頁面設定（必須在第一個 st. 指令前）----------
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
    
    [gemini]
    api_key = "你的 Gemini API Key"
    ```
    """)
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

# ---------- 本地檔案操作（簡化版，無備份）----------
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
        return {}
    except Exception as e:
        st.error(f"載入本地資料庫失敗：{e}")
        return {}

def save_sentences(data):
    """簡化版：儲存本地快取（無備份）"""
    if not isinstance(data, dict):
        st.error("儲存失敗：資料必須是字典格式")
        return False
    
    try:
        with open(SENTENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
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
    """儲存到 V1_Sheet，第一欄為原始檔名，第二欄起為資料"""
    if not content or not content.strip() or not gc or not sheet_id:
        return True
    
    try:
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("V1_Sheet")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("V1_Sheet", rows=1000, cols=6)
            ws.append_row(["檔名_批次", "Ref. 經文出處", "English（ESV經文）", "Chinese經文", "Syn/Ant", "Grammar"])
        
        rows = parse_content_to_rows(content, expected_cols=5)
        if rows:
            rows_with_group = [[ref] + row for row in rows]
            ws.append_rows(rows_with_group)
            st.sidebar.caption(f"  V1_Sheet：寫入 {len(rows_with_group)} 行")
        return True
    except Exception as e:
        st.sidebar.error(f"  V1_Sheet 失敗：{e}")
        return False

def save_v2_sheet(ref, content, gc, sheet_id):
    """儲存到 V2_Sheet，第一欄為原始檔名，第二欄起為資料"""
    if not content or not content.strip() or not gc or not sheet_id:
        return True
    
    try:
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("V2_Sheet")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("V2_Sheet", rows=1000, cols=8)
            ws.append_row(["檔名_批次", "Ref.經文出處", "口語訳", "Grammar", "Note", "KRF", "Korean Syn/Ant", "THSV11 泰文重要片語"])
        
        rows = parse_content_to_rows(content, expected_cols=7)
        if rows:
            rows_with_group = [[ref] + row for row in rows]
            ws.append_rows(rows_with_group)
            st.sidebar.caption(f"  V2_Sheet：寫入 {len(rows_with_group)} 行")
        return True
    except Exception as e:
        st.sidebar.error(f"  V2_Sheet 失敗：{e}")
        return False

def save_w_sheet(ref, content, gc, sheet_id):
    """儲存到 W_Sheet，第一欄為原始檔名"""
    if not content or not content.strip() or not gc or not sheet_id:
        return True
    
    try:
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("W_Sheet")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("W_Sheet", rows=1000, cols=6)
            ws.append_row(["檔名_批次", "No經卷範圍", "Word/Phrase+Chinese", "Synonym+中文對照", "Antonym+中文對照", "全句聖經中英對照例句"])
        
        rows = parse_content_to_rows(content, expected_cols=5)
        if rows:
            rows_with_group = [[ref] + row for row in rows]
            ws.append_rows(rows_with_group)
            st.sidebar.caption(f"  W_Sheet：寫入 {len(rows_with_group)} 行")
        return True
    except Exception as e:
        st.sidebar.error(f"  W_Sheet 失敗：{e}")
        return False

def save_p_sheet(ref, content, gc, sheet_id):
    """儲存到 P_Sheet，第一欄為原始檔名"""
    if not content or not content.strip() or not gc or not sheet_id:
        return True
    
    try:
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("P_Sheet")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("P_Sheet", rows=1000, cols=4)
            ws.append_row(["檔名_批次", "Paragraph", "English Refinement", "中英夾雜講章"])
        
        rows = parse_content_to_rows(content, expected_cols=3)
        if rows:
            rows_with_group = [[ref] + row for row in rows]
            ws.append_rows(rows_with_group)
            st.sidebar.caption(f"  P_Sheet：寫入 {len(rows_with_group)} 行")
        return True
    except Exception as e:
        st.sidebar.error(f"  P_Sheet 失敗：{e}")
        return False

def save_grammar_sheet(ref, content, gc, sheet_id):
    """儲存到 Grammar_List，第一欄為原始檔名"""
    if not content or not content.strip() or not gc or not sheet_id:
        return True
    
    try:
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("Grammar_List")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("Grammar_List", rows=1000, cols=5)
            ws.append_row(["檔名_批次", "No經卷範圍", "Original Sentence＋中文翻譯", "Grammar Rule", "Analysis & Example (1️⃣2️⃣3️⃣4️⃣)"])
        
        rows = parse_content_to_rows(content, expected_cols=4)
        if rows:
            rows_with_group = [[ref] + row for row in rows]
            ws.append_rows(rows_with_group)
            st.sidebar.caption(f"  Grammar_List：寫入 {len(rows_with_group)} 行")
        return True
    except Exception as e:
        st.sidebar.error(f"  Grammar_List 失敗：{e}")
        return False

def save_to_google_sheets(data_dict):
    """將資料分別存入對應的 5 個工作表，避免重複上傳"""
    gc, sheet_id = get_google_sheets_client()
    
    if not gc or not sheet_id:
        st.sidebar.error("❌ Google Sheets 未連線")
        return False, "Google Sheets 未連線"
    
    try:
        ref = data_dict.get('ref', 'N/A')
        mode = data_dict.get('mode', 'A')
        
        # 檢查是否已存在相同的 ref
        sh = gc.open_by_key(sheet_id)
        existing_refs = set()
        
        check_sheet = "V1_Sheet" if mode == 'A' else "W_Sheet"
        try:
            ws = sh.worksheet(check_sheet)
            all_values = ws.get_all_values()
            for row in all_values[1:]:
                if row and len(row) > 0:
                    existing_refs.add(row[0].strip())
        except gspread.WorksheetNotFound:
            pass
        
        if ref in existing_refs:
            st.sidebar.warning(f"⚠️ {ref} 已存在於 Google Sheets，跳過重複儲存")
            return False, f"重複資料：{ref} 已存在"
        
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
        
        # V1_Sheet - 按檔名分組
        try:
            ws = sh.worksheet("V1_Sheet")
            rows = ws.get_all_values()
            if len(rows) > 1:
                for row in rows[1:]:
                    if len(row) >= 6:
                        group_ref = row[0]
                        verse_ref = row[1]
                        
                        if group_ref not in all_data:
                            all_data[group_ref] = {
                                "ref": group_ref,
                                "mode": "A",
                                "type": "Scripture",
                                "v1_content": "Ref. 經文出處\tEnglish（ESV經文）\tChinese經文\tSyn/Ant\tGrammar\n",
                                "v2_content": "",
                                "w_sheet": "", "p_sheet": "", "grammar_list": "", "other": "",
                                "saved_sheets": ["V1 Sheet"],
                                "date_added": ""
                            }
                        row_data = row[1:6] if len(row) >= 6 else row[1:] + [''] * (6 - len(row))
                        all_data[group_ref]["v1_content"] += "\t".join(row_data) + "\n"
        except gspread.WorksheetNotFound:
            pass
        
        # V2_Sheet - 按檔名分組
        try:
            ws = sh.worksheet("V2_Sheet")
            rows = ws.get_all_values()
            if len(rows) > 1:
                for row in rows[1:]:
                    if len(row) >= 8:
                        group_ref = row[0]
                        
                        if group_ref in all_data:
                            row_data = row[1:8] if len(row) >= 8 else row[1:] + [''] * (8 - len(row))
                            all_data[group_ref]["v2_content"] += "\t".join(row_data) + "\n"
                            if "V2 Sheet" not in all_data[group_ref]["saved_sheets"]:
                                all_data[group_ref]["saved_sheets"].append("V2 Sheet")
        except gspread.WorksheetNotFound:
            pass
            
        # W_Sheet - 按檔名分組
        try:
            ws = sh.worksheet("W_Sheet")
            rows = ws.get_all_values()
            # 🔥 這裡保留你的 Debug 訊息
            st.write(f"W_Sheet 總行數: {len(rows)}") 
            
            if len(rows) > 1:
                # 🔥 這裡也可以 Debug 第一行資料
                st.write(f"W_Sheet 第一行內容: {rows[1]}") 
                
                for row in rows[1:]:
                    if len(row) >= 6:
                        group_ref = row[0]
                        
                        if group_ref not in all_data:
                            all_data[group_ref] = {
                                "ref": group_ref,
                                "mode": "B",
                                "type": "Document",
                                "v1_content": "",
                                "v2_content": "",
                                "w_sheet": "No經卷範圍\tWord/Phrase+Chinese\tSynonym+中文對照\tAntonym+中文對照\t全句聖經中英對照例句\n",
                                "p_sheet": "",
                                "grammar_list": "No經卷範圍\tOriginal Sentence＋中文翻譯\tGrammar Rule\tAnalysis & Example\n",
                                "other": "",
                                "saved_sheets": ["W Sheet"],
                                "date_added": ""
                            }
                        row_data = row[1:6] if len(row) >= 6 else row[1:] + [''] * (6 - len(row))
                        all_data[group_ref]["w_sheet"] += "\t".join(row_data) + "\n"
                    else:
                        # 🔥 捕捉欄位不足的行，這就是為什麼 UI 沒顯示的原因！
                        st.warning(f"跳過欄位不足的行: {len(row)} 欄, 內容: {row[:3]}...")
        except gspread.WorksheetNotFound:
            pass
        
        except gspread.WorksheetNotFound:
            pass
        
        # P_Sheet - 按檔名分組
        try:
            ws = sh.worksheet("P_Sheet")
            rows = ws.get_all_values()
            if len(rows) > 1:
                for row in rows[1:]:
                    if len(row) >= 4:
                        group_ref = row[0]
                        
                        if group_ref in all_data and all_data[group_ref]["mode"] == "B":
                            row_data = row[1:4] if len(row) >= 4 else row[1:] + [''] * (4 - len(row))
                            all_data[group_ref]["p_sheet"] += "\t".join(row_data) + "\n"
                            if "P Sheet" not in all_data[group_ref]["saved_sheets"]:
                                all_data[group_ref]["saved_sheets"].append("P Sheet")
        except gspread.WorksheetNotFound:
            pass
        
        # Grammar_List - 按檔名分組
        try:
            ws = sh.worksheet("Grammar_List")
            rows = ws.get_all_values()
            if len(rows) > 1:
                for row in rows[1:]:
                    if len(row) >= 5:
                        group_ref = row[0]
                        
                        if group_ref in all_data and all_data[group_ref]["mode"] == "B":
                            row_data = row[1:5] if len(row) >= 5 else row[1:] + [''] * (5 - len(row))
                            all_data[group_ref]["grammar_list"] += "\t".join(row_data) + "\n"
                            if "Grammar List" not in all_data[group_ref]["saved_sheets"]:
                                all_data[group_ref]["saved_sheets"].append("Grammar List")
        except gspread.WorksheetNotFound:
            pass
            
    except Exception as e:
        st.error(f"載入 Google Sheets 時發生錯誤: {str(e)}")
        return {}
    
    return all_data

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

# ← 加入這行
if 'notes' not in st.session_state:
    st.session_state.notes = {}

# ===================================================================
# 1. 側邊欄（簡化版）
# ===================================================================

import datetime
import requests
import json

# 圖片 URL
IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg",
    "M1": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro1.jpg",
    "M2": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro2.jpg",
    "M3": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro3.jpg",
    "M4": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro4.jpg",
    "M5": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro5.jpg",
    "M6": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro6.jpg"
}

# ---------- 側邊欄開始 ----------
with st.sidebar:
    # ===== 每日韓文鼓勵話（輪播）+ Mashimaro（最頂部）=====
    
    quotes = [
        "당신은 하나님의 소중한 보물입니다 💎",
        "오늘도 당신을 사랑하십니다 ❤️",
        "당신은 특별한 존재입니다 ⭐",
        "하나님의 은혜가 함께하길 🙏",
        "당신의 미소가 세상을 밝힙니다 😊",
        "오늘도 힘내세요! 💪",
        "당신은 축복받은 사람입니다 🌈",
        "평안이 당신과 함께하길 ✨",
        "사랑은 언제나 승리합니다 💕",
        "당신의 꿈을 응원합니다 🌟",
    ]
    today_index = datetime.date.today().weekday() % len(quotes)
    korean_text = quotes[today_index]
    
    # 顯示韓文
    st.markdown(f'<p class="cute-korean">{korean_text}</p>', unsafe_allow_html=True)
    
    st.image(IMG_URLS["M3"], width=250)
    st.divider()

    # ===== 快速連結 =====
    c1, c2 = st.columns(2)
    c1.link_button("✨ Google AI", "https://gemini.google.com")
    c2.link_button("🤖 Kimi K2", "https://kimi.moonshot.cn")
    c3, c4 = st.columns(2)
    c3.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb")
    c4.link_button("THSV11", "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")
    
    st.divider()
    
    # ===== 底部背景設定 =====
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
    
    st.divider()
    
    # ===== 檢查雲端工作表（最底部）=====
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

tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# ===================================================================
# 3. TAB1 ─ 書桌 (修正版 - 正確的資料來源邏輯)
# ===================================================================
with tabs[0]:
    import csv, random, re, datetime as dt
    from io import StringIO

    # --- Session State 初始化 ---
    if "tab1_vocab_index" not in st.session_state:
        st.session_state.tab1_vocab_index = 0
    if "tab1_phrase_index" not in st.session_state:
        st.session_state.tab1_phrase_index = 0
    if "tab1_grammar_index" not in st.session_state:
        st.session_state.tab1_grammar_index = 0
    if "tab1_verse_index" not in st.session_state:
        st.session_state.tab1_verse_index = 0
    if "tab1_last_update" not in st.session_state:
        st.session_state.tab1_last_update = dt.datetime.now()

    # 檢查是否需要更新（超過1小時）
    current_time = dt.datetime.now()
    time_diff = (current_time - st.session_state.tab1_last_update).total_seconds()
    
    if time_diff > 3600:
        st.session_state.tab1_last_update = current_time
        st.session_state.tab1_vocab_index += 1
        st.session_state.tab1_phrase_index += 1
        st.session_state.tab1_grammar_index += 1
        st.session_state.tab1_verse_index += 1
        st.rerun()
    
    sentences = st.session_state.get('sentences', {})
    
    if not sentences:
        st.warning("資料庫為空，請先在 TAB4 載入資料")
    else:
        def parse_csv(content):
            """解析CSV格式或Tab分隔格式"""
            if not content or not content.strip(): 
                return []
            try:
                # 處理Tab分隔格式
                if '\t' in content:
                    lines = content.strip().split('\n')
                    if len(lines) >= 1:
                        headers = [h.strip() for h in lines[0].split('\t')]
                        rows = []
                        for line in lines[1:]:
                            if not line.strip():
                                continue
                            cells = [c.strip() for c in line.split('\t')]
                            while len(cells) < len(headers):
                                cells.append('')
                            row_dict = {}
                            for i, header in enumerate(headers):
                                cell_value = cells[i] if i < len(cells) else ''
                                cell_value = re.sub(r'\*\*(.*?)\*\*', r'\1', cell_value)
                                row_dict[header] = cell_value
                            if any(v.strip() for v in row_dict.values()):
                                rows.append(row_dict)
                        return rows
                return []
            except Exception as e:
                return []

        # ============================================================
        # 資料收集與正確來源映射
        # ============================================================
        
        all_vocab_items = []      # 單字：從 V1 + V2 來
        all_phrase_items = []     # 片語：從 W_Sheet 來
        all_verse_items = []      # 金句：從 V1 + V2 來
        all_grammar_items = []    # 文法：從 V1 Grammar + Grammar_List 來
        
        for ref, data in sentences.items():
            v1_content = data.get('v1_content', '')
            v2_content = data.get('v2_content', '')
            w_content = data.get('w_sheet', '')
            g_content = data.get('grammar_list', '')
            
            v1_rows = parse_csv(v1_content)
            v2_rows = parse_csv(v2_content)
            w_rows = parse_csv(w_content)
            g_rows = parse_csv(g_content)
            
            mode = data.get('mode', 'A')
            
            # ========== 模式 A 處理 ==========
            if mode == 'A' and v1_rows:
                for i, v1_row in enumerate(v1_rows):
                    v2_row = v2_rows[i] if i < len(v2_rows) else {}
                    verse_ref = v1_row.get('Ref. 經文出處', ref)
                    
                    # --- 單字資料（從 V1 Syn/Ant + V2 多語言）---
                    syn_ant_text = v1_row.get('Syn/Ant', '')
                    # 解析 Syn/Ant，格式可能是 "Syn:xxx / Ant:xxx" 或 "xxx / xxx"
                    syn_list = []
                    ant_list = []
                    
                    if syn_ant_text:
                        if '/' in syn_ant_text:
                            parts = syn_ant_text.split('/')
                            syn_part = parts[0].strip()
                            ant_part = parts[1].strip() if len(parts) > 1 else ""
                            
                            # 移除 "Syn:" 或 "Ant:" 前綴
                            syn_part = re.sub(r'^[Ss]yn:?\s*', '', syn_part)
                            ant_part = re.sub(r'^[Aa]nt:?\s*', '', ant_part)
                            
                            if syn_part:
                                syn_list.append(syn_part)
                            if ant_part:
                                ant_list.append(ant_part)
                        else:
                            syn_list.append(syn_ant_text.strip())
                    
                    # --- 單字與多語言資料收集 ---
                    vocab_item = {
                        'ref': verse_ref,
                        'syn': syn_list,
                        'ant': ant_list,
                        'jp': v2_row.get('口語訳', ''),
                        'kr': v2_row.get('Korean Syn/Ant', ''),
                        'th': v2_row.get('THSV11 泰文重要片語', '')
                    }
                    
                    # 判斷是否存入 all_vocab_items
                    if syn_list or ant_list or vocab_item['jp'] or vocab_item['kr'] or vocab_item['th']:
                        all_vocab_items.append(vocab_item)
                    
                    # --- 金句資料（V1 English/Chinese + V2 多語言）---
                    verse_item = {
                        'ref': verse_ref,
                        'en': v1_row.get('English（ESV經文）', ''),
                        'cn': v1_row.get('Chinese經文', ''),
                        'jp': v2_row.get('口語訳', ''),
                        'kr': v2_row.get('Korean Syn/Ant', ''),
                        'th': v2_row.get('THSV11 泰文重要片語', '')
                    }
                    if verse_item['en'] or verse_item['cn']:
                        all_verse_items.append(verse_item)
                    
                    # --- 文法資料（從 V1 Grammar 欄位）---
                    grammar_text = v1_row.get('Grammar', '')
                    if grammar_text:
                        all_grammar_items.append({
                            'type': 'A',
                            'ref': verse_ref,
                            'en': verse_item['en'],
                            'cn': verse_item['cn'],
                            'grammar': grammar_text,
                            'syn': syn_list,
                            'ant': ant_list,
                            'jp': v2_row.get('口語訳', ''),
                            'kr': v2_row.get('Korean Syn/Ant', ''),
                            'th': v2_row.get('THSV11 泰文重要片語', ''),
                            'note': v2_row.get('Note', '')
                        })
            
            # ========== 模式 B 處理 ==========
            if mode == 'B':
                # --- 片語資料（從 W_Sheet）---
                for w_row in w_rows:
                    word_phrase = w_row.get('Word/Phrase+Chinese', '')
                    if word_phrase:  # 只取有資料的
                        phrase_item = {
                            'ref': ref,
                            'word_phrase': word_phrase,
                            'syn': w_row.get('Synonym+中文對照', ''),
                            'ant': w_row.get('Antonym+中文對照', ''),
                            'example': w_row.get('全句聖經中英對照例句', '')
                        }
                        all_phrase_items.append(phrase_item)
                
                # --- 文法資料（從 Grammar_List）---
                for g_row in g_rows:
                    orig_sent = g_row.get('Original Sentence＋中文翻譯', '')
                    grammar_rule = g_row.get('Grammar Rule', '')
                    analysis = g_row.get('Analysis & Example (1️⃣2️⃣3️⃣4️⃣)', '')
                    
                    if orig_sent or grammar_rule or analysis:
                        all_grammar_items.append({
                            'type': 'B',
                            'ref': ref,
                            'orig_sent': orig_sent,
                            'grammar_rule': grammar_rule,
                            'analysis': analysis
                        })

        # ============================================================
        # 1) 單字顯示（輪轉邏輯）
        # ============================================================
        vocab_display = []
        current_vocab_ref = "N/A"
        
        if all_vocab_items:
            vocab_idx = st.session_state.tab1_vocab_index % len(all_vocab_items)
            vocab_item = all_vocab_items[vocab_idx]
            current_vocab_ref = vocab_item['ref']
            
            display_parts = []
            
            # Syn（綠色）
            if vocab_item['syn']:
                syn_text = ' | '.join(vocab_item['syn'])
                display_parts.append(f"<span style='color:#2E8B57;'>✨{syn_text}</span>")
            
            # Ant（紅色）
            if vocab_item['ant']:
                ant_text = ' | '.join(vocab_item['ant'])
                display_parts.append(f"<span style='color:#CD5C5C;'>❄️{ant_text}</span>")
            
            # 多語言（V2 Sheet）
            if vocab_item.get('jp'):
                display_parts.append(f"<span style='color:#FF8C00;'>🇯🇵 {vocab_item['jp']}</span>")
            if vocab_item.get('kr'):
                display_parts.append(f"<span style='color:#4682B4;'>🇰🇷 {vocab_item['kr']}</span>")
            if vocab_item.get('th'):
                display_parts.append(f"<span style='color:#9932CC;'>🇹🇭 {vocab_item['th']}</span>")
            
            vocab_display = display_parts

        # ============================================================
        # 2) 片語顯示（一次顯示4個，輪轉邏輯）
        # ============================================================
        w_phrases = []
        current_phrase_ref = "N/A"
        
        if all_phrase_items:
            start_idx = st.session_state.tab1_phrase_index % len(all_phrase_items)
            
            for i in range(min(4, len(all_phrase_items))):
                idx = (start_idx + i) % len(all_phrase_items)
                w_phrases.append(all_phrase_items[idx])
                if i == 0:
                    current_phrase_ref = all_phrase_items[idx]['ref']

        # ============================================================
        # 3) 金句顯示（輪轉邏輯）
        # ============================================================
        verse_lines = []
        current_verse_ref = "N/A"
        
        if all_verse_items:
            verse_idx = st.session_state.tab1_verse_index % len(all_verse_items)
            verse_item = all_verse_items[verse_idx]
            current_verse_ref = verse_item['ref']
            
            if verse_item['ref'] and verse_item['en']:
                verse_lines.append(f"<b>{verse_item['ref']}</b> {verse_item['en']}")
            if verse_item['cn']:
                verse_lines.append(f"<span style='color:#666;'>{verse_item['cn']}</span>")
            
            # 多語言（V2 Sheet）
            other_langs = []
            if verse_item.get('jp'):
                other_langs.append(f"🇯🇵 {verse_item['jp']}")
            if verse_item.get('kr'):
                other_langs.append(f"🇰🇷 {verse_item['kr']}")
            if verse_item.get('th'):
                other_langs.append(f"🇹🇭 {verse_item['th']}")
            
            if other_langs:
                verse_lines.append("<div style='font-size:0.85em; color:#888;'>" + " | ".join(other_langs) + "</div>")

        # ============================================================
        # 4) 文法解析顯示（輪轉邏輯）
        # ============================================================
        grammar_html = "等待資料中..."
        current_grammar_ref = "N/A"
        
        if all_grammar_items:
            grammar_idx = st.session_state.tab1_grammar_index % len(all_grammar_items)
            g_item = all_grammar_items[grammar_idx]
            current_grammar_ref = g_item['ref']
            
            html_parts = []
            
            if g_item['type'] == 'A':
                # 模式 A 文法：從 V1 Sheet
                ref = g_item['ref']
                en = g_item['en']
                cn = g_item['cn']
                grammar = g_item['grammar']
                syn = g_item['syn']
                ant = g_item['ant']
                jp = g_item['jp']
                note = g_item['note']
                
                # 經文（黃色字體，Ref 緊貼英文）
                if ref and en:
                    html_parts.append(
                        f'<div style="color:#FFD700; font-size:15px; font-weight:bold;">'
                        f'<b>{ref}</b>{en}</div>'
                    )
                elif en:
                    html_parts.append(
                        f'<div style="color:#FFD700; font-size:15px; font-weight:bold;">{en}</div>'
                    )
                
                if cn:
                    html_parts.append(f"<span style='color:#AAAAAA;'>{cn}</span>")
                
                # Syn/Ant
                syn_ant_parts = []
                if syn:
                    syn_text = ' | '.join(syn)
                    syn_ant_parts.append(f'<span style="color:#2E8B57;">✨Syn:{syn_text}</span>')
                if ant:
                    ant_text = ' | '.join(ant)
                    syn_ant_parts.append(f'<span style="color:#CD5C5C;">❄️Ant:{ant_text}</span>')
                
                if syn_ant_parts:
                    html_parts.append(" ".join(syn_ant_parts))
                
                # Grammar 內容（處理 1️⃣2️⃣3️⃣4️⃣ 格式）
                if grammar:
                    text = str(grammar)
                    # 確保 1️⃣2️⃣3️⃣4️⃣ 換行顯示
                    text = text.replace('1️⃣', '<br>1️⃣')
                    text = text.replace('2️⃣', '<br>2️⃣')
                    text = text.replace('3️⃣', '<br>3️⃣')
                    text = text.replace('4️⃣', '<br>4️⃣')
                    html_parts.append(text)
                
                # V2 多語言資料
                v2_parts = []
                if jp:
                    v2_parts.append(f"<br><span style='color:#FF8C00;'>🇯🇵 {jp}</span>")
                if g_item.get('kr'):
                    v2_parts.append(f"<span style='color:#4682B4;'>🇰🇷 {g_item['kr']}</span>")
                if g_item.get('th'):
                    v2_parts.append(f"<span style='color:#9932CC;'>🇹🇭 {g_item['th']}</span>")
                if note:
                    v2_parts.append(f'<span style="color:#D2691E;">備註：</span>{note}')
                
                if v2_parts:
                    html_parts.append("<br>".join(v2_parts))
                    
            else:
                # 模式 B 文法：從 Grammar_List
                orig = g_item.get('orig_sent', '')
                analysis = g_item.get('analysis', '')
                
                if orig:
                    # 嘗試分離經卷和句子
                    match = re.match(r'^([A-Za-z0-9\s:]+?)([A-Z][a-z].*)$', orig.strip())
                    if match:
                        ref_part = match.group(1).strip()
                        text_part = match.group(2).strip()
                        html_parts.append(
                            f'<div style="color:#FFD700; font-size:15px; font-weight:bold;">'
                            f'<b>{ref_part}</b>{text_part}</div>'
                        )
                    else:
                        html_parts.append(
                            f'<div style="color:#FFD700; font-size:15px; font-weight:bold;">{orig}</div>'
                        )
                
                if analysis:
                    af = str(analysis).strip()
                    # 處理 1️⃣2️⃣3️⃣4️⃣ 格式，加上顏色
                    af = af.replace('1️⃣', '<br><span style="color:#2E8B57; font-weight:bold;">1️⃣')
                    af = af.replace('2️⃣', '</span><br><span style="color:#2E8B57; font-weight:bold;">2️⃣')
                    af = af.replace('3️⃣', '</span><br><span style="color:#2E8B57; font-weight:bold;">3️⃣')
                    af = af.replace('4️⃣', '</span><br><span style="color:#2E8B57; font-weight:bold;">4️⃣')
                    af = af + '</span>'
                    html_parts.append(af)
            
            if html_parts:
                grammar_html = "<br>".join(html_parts)

        # ============================================================
        # 渲染畫面
        # ============================================================
        col_left, col_right = st.columns([0.67, 0.33])
        
        with col_left:
            # 單字區塊
            if vocab_display:
                st.markdown(
                    "<div style='margin-bottom:4px; line-height:1.6;'>" + 
                    " ; ".join(vocab_display) + 
                    "</div>", 
                    unsafe_allow_html=True
                )
            else:
                st.caption("無單字資料")
            
            st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

            # 片語區塊（修正：正確顯示 W_Sheet 欄位）
            if w_phrases:
                for i, row in enumerate(w_phrases):
                    word_phrase = row.get('word_phrase', '')
                    syn = row.get('syn', '')
                    ant = row.get('ant', '')
                    example = row.get('example', '')
                    
                    if word_phrase:
                        parts = [f"🔤 **{word_phrase}**"]
                        if syn: 
                            parts.append(f"<span style='color:#2E8B57;'>✨{syn}</span>")
                        if ant: 
                            parts.append(f"<span style='color:#CD5C5C;'>❄️{ant}</span>")
                        
                        st.markdown(
                            "<div style='margin-bottom:2px;'>" + " | ".join(parts) + "</div>", 
                            unsafe_allow_html=True
                        )
                        
                        if example:
                            st.markdown(
                                f"<div style='margin-bottom:4px; margin-left:20px; font-size:0.9em;'>📖 {example}</div>", 
                                unsafe_allow_html=True
                            )
                        
                        if i < len(w_phrases) - 1:
                            st.markdown("<div style='margin:4px 0;'></div>", unsafe_allow_html=True)
            else:
                st.caption("無片語資料")

            st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

            # 金句區塊
            if verse_lines:
                for v in verse_lines:
                    st.markdown(f"<div style='margin-bottom:4px;'>{v}</div>", unsafe_allow_html=True)
            else:
                st.caption("📖 無金句資料")

        with col_right:
            # 文法區塊
            st.markdown(f"""
                <div style="background-color:#1E1E1E; color:#FFFFFF; padding:10px; border-radius:8px; 
                            border-left:4px solid #FF8C00; font-size:13px; line-height:1.5;">
                    {grammar_html}
                </div>
                """, unsafe_allow_html=True)
            
            minutes_left = max(0, (3600 - time_diff) / 60)
            st.caption(f"單字:{current_vocab_ref} | 片語:{current_phrase_ref} | 金句:{current_verse_ref}")
            st.caption(f"文法:{current_grammar_ref} | {minutes_left:.0f}分後更新")
            st.caption(f"資料統計: 單字={len(all_vocab_items)}, 片語={len(all_phrase_items)}, 金句={len(all_verse_items)}, 文法={len(all_grammar_items)}")

# ===================================================================
# 4. TAB2 ─ 月曆待辦 + 時段金句 + 收藏金句（修正版）
# ===================================================================
with tabs[1]:
    import datetime as dt, re, os, json
    from streamlit_calendar import calendar
    from io import StringIO
    import csv

    # 全局CSS：壓縮所有間距
    st.markdown("""
        <style>
        /* 壓縮所有元素間距 */
        div[data-testid="stVerticalBlock"] > div {padding: 0px !important; margin: 0px !important;}
        div[data-testid="stVerticalBlock"] > div > div {padding: 0px !important; margin: 0px !important;}
        p {margin: 0px !important; padding: 0px !important; line-height: 1.2 !important;}
        .stMarkdown {margin: 0px !important; padding: 0px !important;}
        /* 壓縮按鈕 */
        .stButton button {padding: 0px 4px !important; min-height: 24px !important; font-size: 12px !important; margin: 0px !important;}
        /* 壓縮分隔線 */
        hr {margin: 2px 0 !important; padding: 0 !important;}
        /* 壓縮expander */
        div[data-testid="stExpander"] {margin: 2px 0 !important;}
        div[data-testid="stExpander"] > div {padding: 0px 8px !important;}
        /* 壓縮columns間距 */
        div[data-testid="column"] {padding: 0px 2px !important;}
        </style>
    """, unsafe_allow_html=True)

    # ---------- 0. 檔案設定 ----------
    DATA_DIR = "data"
    os.makedirs(DATA_DIR, exist_ok=True)
    TODO_FILE = os.path.join(DATA_DIR, "todos.json")
    FAVORITE_FILE = os.path.join(DATA_DIR, "favorite_sentences.json")

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

    # ---------- 1. Session State ----------
    if "todo" not in st.session_state:
        st.session_state.todo = load_todos()
    if "favorite_sentences" not in st.session_state:
        st.session_state.favorite_sentences = load_favorites()
    if "sel_date" not in st.session_state:
        st.session_state.sel_date = str(dt.date.today())
    if "cal_key" not in st.session_state:
        st.session_state.cal_key = 0
    if "active_del_id" not in st.session_state:
        st.session_state.active_del_id = None
    if "active_fav_del" not in st.session_state:
        st.session_state.active_fav_del = None

    # ---------- 2. 月曆 ----------
    def build_events():
        ev = []
        for d, items in st.session_state.todo.items():
            if isinstance(items, list):
                for t in items:
                    ev.append({
                        "title": t.get("title", ""),
                        "start": f"{d}T{t.get('time','00:00:00')}",
                        "backgroundColor": "#FFE4E1",
                        "borderColor": "#FFE4E1",
                        "textColor": "#333"
                    })
        return ev

    with st.expander("📅 聖經學習生活月曆", expanded=True):
        cal_options = {
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
            "initialView": "dayGridMonth",
            "displayEventTime": False,
            "height": "auto"
        }
        state = calendar(events=build_events(), options=cal_options, key=f"cal_{st.session_state.cal_key}")
        if state.get("dateClick"):
            st.session_state.sel_date = state["dateClick"]["date"][:10]
            st.rerun()

    # ---------- 3. 三日清單（修正：顯示選中日期的前後一天）----------
    st.markdown('<p style="margin:0;padding:0;font-size:14px;font-weight:bold;">📋 待辦事項</p>', unsafe_allow_html=True)

    try:
        base_date = dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date()
    except:
        base_date = dt.date.today()

    # 顯示選中日期及其前後各一天（共3天）
    dates_to_show = [base_date - dt.timedelta(days=1), base_date, base_date + dt.timedelta(days=1)]
    
    has_todo = False
    for d_obj in dates_to_show:
        d_str = str(d_obj)
        
        if d_str in st.session_state.todo and st.session_state.todo[d_str]:
            has_todo = True
            
            for idx, item in enumerate(st.session_state.todo[d_str]):
                item_id = f"{d_str}_{idx}"
                title = item.get("title", "") if isinstance(item, dict) else str(item)
                time_str = item.get('time', '')[:5] if isinstance(item, dict) and item.get('time') else ""

                # 極緊湊布局
                c1, c2, c3 = st.columns([0.3, 8, 1.2])
                
                with c1:
                    if st.button("💟", key=f"h_{item_id}"):
                        st.session_state.active_del_id = None if st.session_state.active_del_id == item_id else item_id
                        st.rerun()

                with c2:
                    # 使用html壓縮行距
                    st.markdown(f'<p style="margin:0;padding:0;line-height:1.2;font-size:13px;">{d_obj.month}/{d_obj.day} {time_str} {title}</p>', unsafe_allow_html=True)

                with c3:
                    if st.session_state.active_del_id == item_id:
                        if st.button("🗑️", key=f"d_{item_id}"):
                            st.session_state.todo[d_str].pop(idx)
                            if not st.session_state.todo[d_str]:
                                del st.session_state.todo[d_str]
                            save_todos()
                            st.session_state.cal_key += 1
                            st.session_state.active_del_id = None
                            st.rerun()
                # 每個項目後極小間距
                st.markdown('<div style="height:1px;"></div>', unsafe_allow_html=True)
    
    if not has_todo:
        st.caption("尚無待辦事項")

    # ---------- 4. 新增待辦 ----------
    with st.expander("➕ 新增待辦", expanded=False):
        with st.form("todo_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                in_date = st.date_input("日期", base_date)
            with c2:
                in_time = st.time_input("時間", dt.time(9, 0))
            in_title = st.text_input("待辦事項（可含 Emoji）")
            
            if st.form_submit_button("💾 儲存"):
                if in_title:
                    k = str(in_date)
                    if k not in st.session_state.todo:
                        st.session_state.todo[k] = []
                    st.session_state.todo[k].append({"title": in_title, "time": str(in_time)})
                    save_todos()
                    st.session_state.cal_key += 1
                    st.rerun()

    st.markdown('<hr style="margin:4px 0;">', unsafe_allow_html=True)
    
    # ---------- 5. 時段金句 ----------
    st.markdown('<p style="margin:0;padding:0;font-size:14px;font-weight:bold;">📖 今日時段金句</p>', unsafe_allow_html=True)
    
    sentences = st.session_state.get('sentences', {})
    all_verses = []
    
    for ref, data in sentences.items():
        v1_content = data.get('v1_content', '')
        v2_content = data.get('v2_content', '')
        if v1_content:
            try:
                v1_rows = list(csv.DictReader(StringIO(v1_content.strip())))
                v2_rows = list(csv.DictReader(StringIO(v2_content.strip()))) if v2_content else []
                
                for i, row in enumerate(v1_rows):
                    v2_row = v2_rows[i] if i < len(v2_rows) else {}
                    verse_ref = row.get('Ref.', ref)
                    en = row.get('English (ESV)', '')
                    cn = row.get('Chinese', '')
                    jp = v2_row.get('口語訳 (1955)', '') if isinstance(v2_row, dict) else ''
                    kr = v2_row.get('KRF', '') if isinstance(v2_row, dict) else ''
                    th = v2_row.get('THSV11 (Key Phrases)', '') if isinstance(v2_row, dict) else ''
                    
                    verse_text = f"🇬🇧 {verse_ref} {en}"
                    if jp:
                        verse_text += f"<br>🇯🇵 {jp}"
                    if kr:
                        verse_text += f"<br>🇰🇷 {kr}"
                    if th:
                        verse_text += f"<br>🇹🇭 {th}"
                    if cn:
                        verse_text += f"<br>🇨🇳 {cn}"
                    
                    all_verses.append(verse_text)
            except:
                pass

    hour = dt.datetime.now().hour
    
    if 7 <= hour < 11:
        period_name, period_idx = "早晨 7-11", 0
    elif 11 <= hour < 15:
        period_name, period_idx = "午間 11-15", 1
    elif 15 <= hour < 19:
        period_name, period_idx = "下午 15-19", 2
    elif 19 <= hour < 23:
        period_name, period_idx = "晚間 19-23", 3
    else:
        period_name, period_idx = "深夜", -1

    st.markdown(f'<p style="margin:0;padding:0;font-size:11px;color:#FF8C00;">⏰ {period_name}</p>', unsafe_allow_html=True)

    if all_verses and period_idx >= 0:
        total = len(all_verses)
        start = (period_idx * 6) % total
        
        for i in range(6):
            idx = (start + i) % total
            st.markdown(f'<p style="margin:2px 0;padding:0;font-size:12px;line-height:1.3;"><b>{i+1}.</b> {all_verses[idx]}</p>', unsafe_allow_html=True)
            if i < 5:
                st.markdown('<hr style="margin:2px 0;border:none;border-top:1px solid #eee;">', unsafe_allow_html=True)
    else:
        st.caption("尚無金句資料")

    st.markdown('<hr style="margin:4px 0;">', unsafe_allow_html=True)

    # ---------- 6. 收藏金句 ----------
    st.markdown('<p style="margin:0;padding:0;font-size:14px;font-weight:bold;">🔽 收藏金句</p>', unsafe_allow_html=True)

    for idx, fav in enumerate(st.session_state.favorite_sentences[:8]):
        fav_id = f"fav_{idx}"
        c1, c2, c3 = st.columns([0.3, 8.5, 1.2])
        
        with c1:
            if st.button("💝", key=f"favh_{fav_id}"):
                st.session_state.active_fav_del = None if st.session_state.active_fav_del == fav_id else fav_id
                st.rerun()
        
        with c2:
            st.markdown(f'<p style="margin:0;padding:0;font-size:12px;line-height:1.2;">{fav}</p>', unsafe_allow_html=True)
        
        with c3:
            if st.session_state.active_fav_del == fav_id:
                if st.button("🗑️", key=f"favd_{fav_id}"):
                    st.session_state.favorite_sentences.pop(idx)
                    save_favorites()
                    st.session_state.active_fav_del = None
                    st.rerun()
        st.markdown('<div style="height:1px;"></div>', unsafe_allow_html=True)

    if len(st.session_state.favorite_sentences) < 8:
        with st.form("add_fav", clear_on_submit=True):
            new_fav = st.text_area("新增收藏", height=50)
            if st.form_submit_button("➕ 加入"):
                if new_fav:
                    st.session_state.favorite_sentences.append(new_fav)
                    save_favorites()
                    st.rerun()

    st.caption(f"收藏: {len(st.session_state.favorite_sentences)}/8")

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
            full_prompt = f"""你是一位精通多國語言的聖經專家與語言學教授。請嚴格根據輸入內容選擇對應模式及對應欄位輸出。
            所有翻譯嚴格規定按聖經語言翻譯，不可私自亂翻譯

### 模式 A：【聖經經文分析時】＝》一定要產出V1 + V2 Excel格式（Markdown表格）
⚠️ 輸出格式要求：「輸出時，請確保 Grammar 欄位內的所有 1️⃣2️⃣3️⃣... 分段內容不使用物理換行，
   改以空格或符號分隔，並確保每列經文嚴格佔據 **Markdown 表格格式**（如下範例）表格的一行。」
【V1 Sheet 範例】
| Ref. | English（ESV經文) | Chinese經文 | Syn/Ant | Grammar |
|------|---------------|---------|---------|---------|
| Pro 31:6 | Give strong drink... | 可以把濃酒... | strong drink (烈酒) / watered down wine (淡酒) | 1️⃣[分段解析+語法標籤]...<br>2️⃣[詞性辨析]...<br>3️⃣[修辭與結構或遞進邏輯]...<br>4️⃣[語意解釋]...<br>...|

【V2 Sheet 範例】
| Ref. | 口語訳 | Grammar | Note | KRF | Korean Syn/Ant | THSV11泰文重要片語 |
|------|--------|---------|------|-----|---------|--------|

🔹 V1 Sheet 欄位要求：
1. Ref.：自動找尋經卷章節並用縮寫 (如: Pro, Rom, Gen).
2. English (ESV)：檢索對應的 ESV 英文經文.
3. Chinese：提供的中文原文.
4. Syn/Ant："同義與反義字"，取自ESV英文經文中的高級/中高級單字或片語（含中/英翻譯）
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
1. Ref.：同 V1 Ref.欄位同資料.
2. 口語訳：檢索對應的日本《口語訳聖經》(1955).
3. Grammar：同V1模式
4. Note：日文文法或語境的補充說明.
5. KRF：檢索對應的韓文《Korean Revised Version》.
6. Korean Syn/Ant：韓文高/ 中高級字（含日/韓/中翻譯）.
7. THSV11泰文重要片語:輸出泰文"對應的重要片語key phrases"《版本用：Thai Holy Bible, Standard Version 2011》.

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
一定要取足"高級/中高級單字15個＋片語15個共30個在同一Excel Sheet裡"！！！！！！！！！
⚠️ 輸出格式要求：「輸出時，請確保 Grammar 欄位內的所有 1️⃣2️⃣3️⃣... 分段內容不使用物理換行，
   改以空格或符號分隔，並確保每列經文嚴格佔據 **Markdown 表格格式**（如下範例）表格的一行。」
 【W Sheet - 重點要求：取高級/中高級單字15個＋片語15個】
⭐️No：請從文稿前5行找到經卷＋經節填入欄位
| No經卷範圍 | Word/Phrase＋Chinese | Synonym+中文對照 | Antonym＋中文對照 | 全句聖經中英對照例句 |
|----|-------------|-------|---------|---------|---------|---------------|
| 1 | steadfast 堅定不移的 | firm | wavering | 1Co 15:58 Therefore... |

【P Sheet - 文稿段落】
| Paragraph | English Refinement | 中英夾雜講章 |
|-----------|-------------------|--------------|
| 1 | We need to be steadfast... | 我們需要 (**steadfast**) ... |

【Grammar List - 重點要求：6 句 × 每句4個解析】
⭐️No：請從文稿前5行找到經卷＋經節填入欄位
| No經卷範圍 | Original Sentence＋中文翻譯 | Grammar Rule＋Analysis & Example (1️⃣2️⃣3️⃣...5️⃣) |
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
                        "v1_content": "Ref. 經文出處\tEnglish（ESV經文）\tChinese經文\tSyn/Ant\tGrammar\n",
                        "v2_content": "Ref.經文出處\t口語訳\tGrammar\tNote\tKRF\tKorean Syn/Ant\tTHSV11 泰文重要片語\n",
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
                        "w_sheet": "No\tWord/Phrase＋Chinese\tSynonym+中文對照\tAntonym+中文對照\t全句聖經中英對照例句\n",
                        "p_sheet": "Paragraph\tEnglish Refinement\t中英夾雜講章\n",
                        "grammar_list": "No\tOriginal Sentence＋中文翻譯\tGrammar Rule＋Analysis\n",
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
            # 使用動態索引來記住當前選中的 tab
            if 'edit_tab_index' not in st.session_state:
                st.session_state.edit_tab_index = 0
            
            edit_tabs = st.tabs(["V1 Sheet", "V2 Sheet", "其他補充", "儲存"])
            
            with edit_tabs[0]:
                # 直接顯示已暫存的內容，無需額外點擊
                new_v1 = st.text_area(
                    "V1 Sheet 內容",
                    value=st.session_state.current_entry.get('v1', ''),
                    height=300,
                    key="edit_v1"
                )
                st.session_state.current_entry['v1'] = new_v1
            
            with edit_tabs[1]:
                new_v2 = st.text_area(
                    "V2 Sheet 內容",
                    value=st.session_state.current_entry.get('v2', ''),
                    height=300,
                    key="edit_v2"
                )
                st.session_state.current_entry['v2'] = new_v2
            
            with edit_tabs[2]:
                new_other = st.text_area(
                    "其他補充",
                    value=st.session_state.current_entry.get('other', ''),
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

        # STEP 3: 多工作表收集區（改為 Tab 介面）
        with st.expander("步驟 3：分批貼上 AI 分析結果", expanded=True):
            
            if st.session_state.content_mode == "A":
                sheet_tabs = st.tabs(["V1 Sheet", "V2 Sheet", "其他補充"])
                
                with sheet_tabs[0]:
                    v1_content = st.text_area(
                        "貼上 V1 Sheet 內容（Markdown 表格格式）",
                        value=st.session_state.current_entry.get('v1', ''),
                        height=300,
                        key="input_v1_tab"
                    )
                    st.session_state.current_entry['v1'] = v1_content
                    if v1_content and "V1 Sheet" not in st.session_state.saved_entries:
                        st.session_state.saved_entries.append("V1 Sheet")
                        st.caption("✅ V1 Sheet 已自動暫存")
                
                with sheet_tabs[1]:
                    v2_content = st.text_area(
                        "貼上 V2 Sheet 內容（Markdown 表格格式）",
                        value=st.session_state.current_entry.get('v2', ''),
                        height=300,
                        key="input_v2_tab"
                    )
                    st.session_state.current_entry['v2'] = v2_content
                    if v2_content and "V2 Sheet" not in st.session_state.saved_entries:
                        st.session_state.saved_entries.append("V2 Sheet")
                        st.caption("✅ V2 Sheet 已自動暫存")
                
                with sheet_tabs[2]:
                    other_content = st.text_area(
                        "其他補充",
                        value=st.session_state.current_entry.get('other', ''),
                        height=200,
                        key="input_other_tab"
                    )
                    st.session_state.current_entry['other'] = other_content
                    if other_content and "其他補充" not in st.session_state.saved_entries:
                        st.session_state.saved_entries.append("其他補充")
                        st.caption("✅ 其他補充 已自動暫存")
            
            else:  # Mode B
                sheet_tabs = st.tabs(["W Sheet", "P Sheet", "Grammar List", "其他補充"])
                
                with sheet_tabs[0]:
                    w_content = st.text_area(
                        "貼上 W Sheet 內容（Markdown 表格格式）",
                        value=st.session_state.current_entry.get('w_sheet', ''),
                        height=300,
                        key="input_w_tab"
                    )
                    st.session_state.current_entry['w_sheet'] = w_content
                    if w_content and "W Sheet" not in st.session_state.saved_entries:
                        st.session_state.saved_entries.append("W Sheet")
                        st.caption("✅ W Sheet 已自動暫存")
                
                with sheet_tabs[1]:
                    p_content = st.text_area(
                        "貼上 P Sheet 內容（Markdown 表格格式）",
                        value=st.session_state.current_entry.get('p_sheet', ''),
                        height=300,
                        key="input_p_tab"
                    )
                    st.session_state.current_entry['p_sheet'] = p_content
                    if p_content and "P Sheet" not in st.session_state.saved_entries:
                        st.session_state.saved_entries.append("P Sheet")
                        st.caption("✅ P Sheet 已自動暫存")
                
                with sheet_tabs[2]:
                    g_content = st.text_area(
                        "貼上 Grammar List 內容（Markdown 表格格式）",
                        value=st.session_state.current_entry.get('grammar_list', ''),
                        height=300,
                        key="input_g_tab"
                    )
                    st.session_state.current_entry['grammar_list'] = g_content
                    if g_content and "Grammar List" not in st.session_state.saved_entries:
                        st.session_state.saved_entries.append("Grammar List")
                        st.caption("✅ Grammar List 已自動暫存")
                
                with sheet_tabs[3]:
                    other_content = st.text_area(
                        "其他補充",
                        value=st.session_state.current_entry.get('other', ''),
                        height=200,
                        key="input_other_b_tab"
                    )
                    st.session_state.current_entry['other'] = other_content
                    if other_content and "其他補充" not in st.session_state.saved_entries:
                        st.session_state.saved_entries.append("其他補充")
                        st.caption("✅ 其他補充 已自動暫存")
            
            # 顯示暫存狀態
            if st.session_state.saved_entries:
                st.write("📋 已暫存工作表：", " | ".join([f"✅ {s}" for s in st.session_state.saved_entries]))

        # STEP 4: 統一儲存區
        with st.expander("步驟 4：儲存到資料庫", expanded=True):
            st.caption("確認所有工作表都暫存後，填寫資訊並儲存")
            
            if 'uploaded_to_sheets' not in st.session_state:
                st.session_state.uploaded_to_sheets = False
            
            if st.session_state.uploaded_to_sheets:
                st.success("✅ 此資料已上傳至 Google Sheets")
                st.info("請點擊下方「🔄 新的分析」開始下一筆資料")
                
                if st.button("🔄 新的分析", key="new_analysis_main", use_container_width=True):
                    keys_to_clear = [
                        'is_prompt_generated', 'main_input_value', 'original_text',
                        'content_mode', 'raw_input_value', 'ref_number', 'raw_input_temp',
                        'current_entry', 'saved_entries', 'ref_no_input', 'uploaded_to_sheets'
                    ]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            
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
                                    st.session_state.uploaded_to_sheets = True  # 🔥 鎖定重複上傳
                                    st.success(f"✅ 已存 Google Sheets：{ref_input}")
                                    st.balloons()
                                    st.rerun()  # 🔥 重新整理顯示鎖定狀態
                                else:
                                    st.error(f"❌ Google Sheets 失敗：{msg}")
                            except Exception as e:
                                st.error(f"❌ Google Sheets 失敗：{str(e)}")
                else:
                    st.button("☁️ 存到雲端", disabled=True, use_container_width=True)

            if st.button("🔄 新的分析", key="new_analysis_secondary", use_container_width=True):
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

