# ===================================================================
# 0. 套件 & 全域函式（一定放最頂）
# ===================================================================
import streamlit as st  

# ✅ 修正：set_page_config 必須是第一個 Streamlit 指令
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

import subprocess, sys, os, datetime as dt, pandas as pd, io, json, re, tomli, tomli_w
from streamlit_calendar import calendar
import streamlit.components.v1 as components
import requests
import base64
import csv
import random
import urllib.parse
from io import StringIO
import gspread
from google.oauth2.service_account import Credentials

# 在文件最開始初始化所有 session state 變量
def init_session_state():
    defaults = {
        "is_prompt_generated": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

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

# ===================================================================
# ✅ 修正：資料庫設定 - 統一使用 data 目錄，並加入 Google Sheets 備援
# ===================================================================
DATA_DIR = "data"
SENTENCES_FILE = os.path.join(DATA_DIR, "sentences.json")
TODO_FILE = os.path.join(DATA_DIR, "todos.json")
FAVORITE_FILE = os.path.join(DATA_DIR, "favorite_sentences.json")

# 確保資料目錄存在
os.makedirs(DATA_DIR, exist_ok=True)

# ---------- Google Sheets 設定 ----------
def init_google_sheets():
    """初始化 Google Sheets 連線"""
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
        st.sidebar.error(f"Google Sheets 初始化失敗: {e}")
        return None, None

# 全域初始化
GC, SHEET_ID = init_google_sheets()

def get_or_create_worksheet(sheet_name, rows=1000, cols=20):
    """取得或建立工作表"""
    if not GC or not SHEET_ID:
        return None
    try:
        sh = GC.open_by_key(SHEET_ID)
        try:
            return sh.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            return sh.add_worksheet(title=sheet_name, rows=rows, cols=cols)
    except Exception as e:
        st.error(f"工作表操作失敗: {e}")
        return None

def save_to_google_sheets(data_dict):
    """儲存資料到 Google Sheets（主要儲存）"""
    if not GC or not SHEET_ID:
        return False, "Google Sheets 未連線"
    
    try:
        mode = data_dict.get('mode', 'A')
        sheet_name = f"Mode_{mode}_Data"
        worksheet = get_or_create_worksheet(sheet_name)
        
        if not worksheet:
            return False, "無法取得工作表"
        
        # 準備資料列
        ref = data_dict.get('ref', 'N/A')
        row_data = [
            ref,
            data_dict.get('type', 'Unknown'),
            data_dict.get('original', '')[:200],
            data_dict.get('v1_content', '')[:2000] if data_dict.get('v1_content') else "",
            data_dict.get('v2_content', '')[:2000] if data_dict.get('v2_content') else "",
            data_dict.get('w_sheet', '')[:2000] if data_dict.get('w_sheet') else "",
            data_dict.get('p_sheet', '')[:2000] if data_dict.get('p_sheet') else "",
            data_dict.get('grammar_list', '')[:2000] if data_dict.get('grammar_list') else "",
            dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            json.dumps(data_dict.get('saved_sheets', []))
        ]
        
        # 檢查是否已存在（更新 vs 新增）
        try:
            cell = worksheet.find(ref)
            if cell:
                worksheet.update(f"A{cell.row}:J{cell.row}", [row_data])
                return True, "updated"
        except:
            pass
        
        # 新增行
        worksheet.append_row(row_data)
        return True, "created"
        
    except Exception as e:
        return False, str(e)

def load_from_google_sheets():
    """從 Google Sheets 載入所有資料"""
    if not GC or not SHEET_ID:
        return {}
    
    all_data = {}
    try:
        sh = GC.open_by_key(SHEET_ID)
        
        for mode in ['A', 'B']:
            sheet_name = f"Mode_{mode}_Data"
            try:
                worksheet = sh.worksheet(sheet_name)
                rows = worksheet.get_all_values()
                
                if len(rows) > 1:
                    headers = rows[0]
                    for row in rows[1:]:
                        if len(row) >= 10:
                            ref = row[0]
                            all_data[ref] = {
                                "ref": ref,
                                "type": row[1],
                                "original": row[2],
                                "v1_content": row[3] if len(row) > 3 else "",
                                "v2_content": row[4] if len(row) > 4 else "",
                                "w_sheet": row[5] if len(row) > 5 else "",
                                "p_sheet": row[6] if len(row) > 6 else "",
                                "grammar_list": row[7] if len(row) > 7 else "",
                                "date_added": row[8] if len(row) > 8 else "",
                                "saved_sheets": json.loads(row[9]) if len(row) > 9 and row[9] else [],
                                "mode": mode,
                                "source": "google_sheets"
                            }
            except gspread.WorksheetNotFound:
                continue
                
        return all_data
    except Exception as e:
        st.sidebar.error(f"載入 Google Sheets 失敗: {e}")
        return {}

def sync_local_to_sheets():
    """同步本地資料到 Google Sheets"""
    if not GC or not SHEET_ID:
        return False
    
    try:
        local_data = load_sentences()
        success_count = 0
        for ref, data in local_data.items():
            success, _ = save_to_google_sheets(data)
            if success:
                success_count += 1
        return success_count
    except Exception as e:
        st.error(f"同步失敗: {e}")
        return 0

# ---------- 本地 JSON 檔案操作（作為快取/備援）----------
def load_sentences():
    """安全載入本地資料庫"""
    if os.path.exists(SENTENCES_FILE):
        try:
            with open(SENTENCES_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError as e:
            backup_name = f"{SENTENCES_FILE}.backup_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                os.rename(SENTENCES_FILE, backup_name)
                st.warning(f"⚠️ 本地資料庫損毀，已備份為 {backup_name}")
            except:
                pass
            return {}
        except Exception as e:
            st.error(f"載入本地資料庫失敗：{e}")
            return {}
    return {}

def save_sentences(data):
    """安全儲存本地資料庫（原子寫入）"""
    try:
        temp_file = f"{SENTENCES_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        if os.path.exists(SENTENCES_FILE):
            os.replace(temp_file, SENTENCES_FILE)
        else:
            os.rename(temp_file, SENTENCES_FILE)
            
        # 自動同步到 Google Sheets
        if GC and SHEET_ID:
            try:
                save_to_google_sheets(data)
            except:
                pass
                
    except Exception as e:
        st.error(f"儲存本地資料庫失敗：{e}")

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

# ✅ 修正：初始化 Session State（優先從 Google Sheets 載入）
if 'sentences' not in st.session_state:
    sheets_data = load_from_google_sheets()
    if sheets_data:
        st.session_state.sentences = sheets_data
        save_sentences(sheets_data)
    else:
        st.session_state.sentences = load_sentences()

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
# 1. 側邊欄
# ===================================================================
with st.sidebar:
    st.divider()
    c1, c2 = st.columns(2)
    c1.link_button("✨ Google AI", "https://gemini.google.com")
    c2.link_button("🤖 Kimi K2", "https://kimi.moonshot.cn")
    c3, c4 = st.columns(2)
    c3.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb")
    c4.link_button("THSV11", "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")
    
    st.divider()
    st.markdown("### 💾 資料庫狀態")
    
    if GC and SHEET_ID:
        st.success("✅ Google Sheets 已連線")
        if st.button("🔄 強制同步到雲端", use_container_width=True):
            count = sync_local_to_sheets()
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

# 背景 CSS
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
# 2. 頁面配置 & Session 初值
# ===================================================================
if 'analysis_history' not in st.session_state: 
    st.session_state.analysis_history = []

# ---------- CSS ----------
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

# ---------- 圖片 & 現成 TAB ----------
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
# 3. TAB1 ─ 書桌 (輪流顯示版 - 支援CSV和Markdown雙格式)
# ===================================================================
with tabs[0]:
    import csv, random, re, datetime as dt
    from io import StringIO

    # 確保資料已載入
    if 'sentences' not in st.session_state:
        st.session_state.sentences = load_sentences()
    
    sentences = st.session_state.sentences

    # --- Session State 初始化（確保每次都有值）---
    if "tab1_vocab_index" not in st.session_state:
        st.session_state.tab1_vocab_index = 0
    if "tab1_phrase_index" not in st.session_state:
        st.session_state.tab1_phrase_index = 15
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
        st.session_state.tab1_phrase_index += 4
        st.session_state.tab1_grammar_index += 1
        st.session_state.tab1_verse_index += 1
        st.rerun()
    
    if not sentences:
        st.warning("資料庫為空，請先在 TAB4 載入資料")
    else:
        def parse_csv(content):
            """解析CSV格式"""
            if not content or not content.strip(): 
                return []
            try:
                if '|' in content and '\n' in content and content.strip().startswith('|'):
                    return []
                reader = csv.DictReader(StringIO(content.strip()))
                rows = list(reader)
                return [row for row in rows if any(v.strip() for v in row.values())]
            except Exception as e:
                st.write(f"CSV解析錯誤: {e}")
                return []

        def parse_markdown_table(content):
            """解析Markdown表格格式"""
            if not content or not content.strip():
                return []
            
            lines = content.strip().split('\n')
            rows = []
            
            table_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith('|'):
                    table_lines.append(line)
            
            if len(table_lines) < 2:
                return []
            
            header_line = table_lines[0]
            headers = [h.strip() for h in header_line.split('|')[1:-1]]
            
            data_lines = table_lines[2:]
            
            for line in data_lines:
                if not line.strip() or line.strip().replace('|', '').strip() == '':
                    continue
                    
                cells = [c.strip() for c in line.split('|')[1:-1]]
                
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

        # 收集所有模式A資料和模式B資料
        all_mode_a = []
        all_mode_b = []
        all_grammar_sources = []
        
        for ref, data in sentences.items():
            v1_content = data.get('v1_content', '')
            v2_content = data.get('v2_content', '')
            w_content = data.get('w_sheet', '')
            g_content = data.get('grammar_list', '')
            
            v1_rows = parse_csv(v1_content) or parse_markdown_table(v1_content)
            v2_rows = parse_csv(v2_content) or parse_markdown_table(v2_content)
            w_rows = parse_csv(w_content) or parse_markdown_table(w_content)
            g_rows = parse_csv(g_content) or parse_markdown_table(g_content)
            
            if v1_rows:
                all_mode_a.append({
                    'ref': ref,
                    'v1': v1_rows,
                    'v2': v2_rows,
                    'v1_count': len(v1_rows)
                })
                for i, row in enumerate(v1_rows):
                    all_grammar_sources.append({
                        'type': 'A',
                        'ref': ref,
                        'row': row,
                        'v2_row': v2_rows[i] if i < len(v2_rows) else {},
                        'index': i,
                        'total_in_file': len(v1_rows)
                    })
            
            if w_rows and len(w_rows) > 0:
                all_mode_b.append({
                    'ref': ref,
                    'w': w_rows,
                    'w_count': len(w_rows)
                })
            
            if g_rows:
                for i, row in enumerate(g_rows):
                    all_grammar_sources.append({
                        'type': 'B',
                        'ref': ref,
                        'row': row,
                        'v2_row': {},
                        'index': i,
                        'total_in_file': len(g_rows)
                    })
        
        # 1) 單字：V1 Syn/Ant + V2 Syn/Ant + THSV11
        vocab_display = []
        current_vocab_ref = "N/A"
        
        if all_mode_a:
            total_vocab_items = sum(f['v1_count'] for f in all_mode_a)
            if total_vocab_items > 0:
                vocab_counter = st.session_state.tab1_vocab_index % total_vocab_items
                cumulative = 0
                vocab_file = None
                row_idx = 0
                for f in all_mode_a:
                    if cumulative + f['v1_count'] > vocab_counter:
                        vocab_file = f
                        row_idx = vocab_counter - cumulative
                        break
                    cumulative += f['v1_count']
                
                if vocab_file and row_idx < len(vocab_file['v1']):
                    v1_row = vocab_file['v1'][row_idx]
                    v2_row = vocab_file['v2'][row_idx] if row_idx < len(vocab_file['v2']) else {}
                    
                    current_vocab_ref = v1_row.get('Ref.', vocab_file['ref'])
                    if not current_vocab_ref or current_vocab_ref == vocab_file['ref']:
                        # 嘗試從其他欄位取得
                        current_vocab_ref = v1_row.get('Ref', v1_row.get('ref', vocab_file['ref']))
                    
                    # V1 Syn/Ant - 解析同義詞和反義詞
                    v1_syn_ant = v1_row.get('Syn/Ant', v1_row.get('Syn/Ant.', ''))
                    v1_syn_list = []
                    v1_ant_list = []
                    
                    if v1_syn_ant and v1_syn_ant.strip():
                        v1_syn_ant_str = str(v1_syn_ant)
                        # 嘗試多種格式解析
                        if 'Syn:' in v1_syn_ant_str or 'Ant:' in v1_syn_ant_str:
                            syn_match = re.search(r'Syn:\s*([^/;]+)', v1_syn_ant_str, re.IGNORECASE)
                            ant_match = re.search(r'Ant:\s*([^/;]+)', v1_syn_ant_str, re.IGNORECASE)
                            if syn_match:
                                v1_syn_list = [s.strip() for s in syn_match.group(1).split(',') if s.strip()]
                            if ant_match:
                                v1_ant_list = [a.strip() for a in ant_match.group(1).split(',') if a.strip()]
                        else:
                            # 嘗試用 / 或 | 分隔
                            parts = re.split(r'[/|]', v1_syn_ant_str)
                            if len(parts) >= 2:
                                v1_syn_list = [p.strip() for p in parts[0].split(',') if p.strip()]
                                v1_ant_list = [p.strip() for p in parts[1].split(',') if p.strip()]
                            else:
                                # 如果只有一個部分，可能是同義詞
                                v1_syn_list = [v1_syn_ant_str.strip()]
                    
                    # V2 Syn/Ant (韓文) + THSV11 (泰文)
                    v2_syn_ant = v2_row.get('Syn/Ant', v2_row.get('Syn/Ant.', '')) if v2_row else ''
                    v2_th = v2_row.get('THSV11', v2_row.get('THSV11 (Key Phrases)', '')) if v2_row else ''
                    
                    vocab_items = []
                    if v1_syn_list:
                        vocab_items.append(f"<span style='color:#2E8B57;'>✨{', '.join(v1_syn_list)}</span>")
                    if v1_ant_list:
                        vocab_items.append(f"<span style='color:#CD5C5C;'>❄️{', '.join(v1_ant_list)}</span>")
                    if v2_syn_ant and str(v2_syn_ant).strip():
                        vocab_items.append(f"<span style='color:#4682B4;'>🇰🇷 {v2_syn_ant}</span>")
                    if v2_th and str(v2_th).strip():
                        vocab_items.append(f"<span style='color:#9932CC;'>🇹🇭 {v2_th}</span>")
                    
                    vocab_display = vocab_items
        
        # 2) 片語：只從模式B的W Sheet輪流（第16個開始，索引15）
        w_phrases = []
        current_phrase_ref = "N/A"
        
        all_available_phrases = []
        
        for mb in all_mode_b:
            w_rows = mb.get('w', [])
            w_count = len(w_rows)
            
            if w_count > 15:
                for idx in range(15, w_count):
                    all_available_phrases.append({
                        'data': w_rows[idx],
                        'ref': mb['ref'],
                        'original_idx': idx + 1
                    })
        
        if len(all_available_phrases) > 0:
            total_available = len(all_available_phrases)
            start_idx = st.session_state.tab1_phrase_index % total_available
            
            for i in range(4):
                idx = (start_idx + i) % total_available
                item = all_available_phrases[idx]
                w_phrases.append(item['data'])
                if i == 0:
                    current_phrase_ref = f"{item['ref']} #{item['original_idx']}"
        
        # 3) 金句：從模式A的V1 Sheet輪流（與單字錯開6句）
        verse_lines = []
        current_verse_ref = "N/A"
        
        if all_mode_a:
            total_verse_items = sum(f['v1_count'] for f in all_mode_a)
            if total_verse_items > 0:
                # 金句索引 = 當前索引 + 6，與單字錯開
                verse_counter = (st.session_state.tab1_verse_index + 6) % total_verse_items
                cumulative = 0
                verse_file = None
                row_idx = 0
                
                for f in all_mode_a:
                    if cumulative + f['v1_count'] > verse_counter:
                        verse_file = f
                        row_idx = verse_counter - cumulative
                        break
                    cumulative += f['v1_count']
                
                if verse_file and row_idx < len(verse_file['v1']):
                    v1_verse = verse_file['v1'][row_idx]
                    v2_verse = verse_file['v2'][row_idx] if row_idx < len(verse_file['v2']) else {}
                    
                    current_verse_ref = v1_verse.get('Ref.', v1_verse.get('Ref', verse_file['ref']))
                    
                    # 建議改寫抓取方式，增加相容性
                    en_text = v1_verse.get('English (ESV)', v1_verse.get('English', v1_verse.get('ESV', '')))
                    cn_text = v1_verse.get('Chinese', v1_verse.get('Chinese (CUV)', v1_verse.get('CUV', '')))
                    # 嘗試抓取不同可能的標籤名稱
                    jp_text = ''
                    if v2_verse:
                        jp_text = v2_verse.get('口語訳 (1955)', v2_verse.get('口語訳', v2_verse.get('Japanese', '')))
                    kr_text = v2_verse.get('KRF', v2_verse.get('Korean', '')) if v2_verse else ''
                    th_text = ''
                    if v2_verse:
                        th_text = v2_verse.get('THSV11 (Key Phrases)', v2_verse.get('THSV11', v2_verse.get('Thai', '')))

                    # 填充邏輯
                    verse_lines = []
                    if en_text and str(en_text).strip(): 
                        verse_lines.append(f"🇬🇧 **{current_verse_ref}** {en_text}")
                    if jp_text and str(jp_text).strip(): 
                        verse_lines.append(f"🇯🇵 {jp_text}")
                    if kr_text and str(kr_text).strip(): 
                        verse_lines.append(f"🇰🇷 {kr_text}")
                    if th_text and str(th_text).strip(): 
                        verse_lines.append(f"🇹🇭 {th_text}")
                    if cn_text and str(cn_text).strip(): 
                        verse_lines.append(f"🇨🇳 {cn_text}")              
                    
        # 4) 文法：從兩處來，加入V2口語訳+Grammar+Note
        grammar_html = "等待資料中..."
        current_grammar_ref = "N/A"
        
        if all_grammar_sources:
            g_idx = st.session_state.tab1_grammar_index % len(all_grammar_sources)
            g_source = all_grammar_sources[g_idx]
            g_row = g_source['row']
            v2_row = g_source.get('v2_row', {})
            current_grammar_ref = f"{g_source['ref']}-{g_source['index']+1}"
            
            all_grammar = []
            
            if g_source['type'] == 'A':
                g_ref = g_row.get('Ref.', '')
                g_en = g_row.get('English (ESV)', '')
                g_cn = g_row.get('Chinese', '')
                g_syn = g_row.get('Syn/Ant', '')
                g_grammar = g_row.get('Grammar', '')
                
                if g_ref and g_en:
                    all_grammar.append(f"<b>{g_ref}</b>{g_en}")
                elif g_en:
                    all_grammar.append(g_en)
                
                if g_cn:
                    all_grammar.append(g_cn)
                
                if g_syn:
                    syn_ant_html = ""
                    syn_text = ""
                    ant_text = ""
                    
                    if 'Syn:' in g_syn or 'Ant:' in g_syn:
                        syn_match = re.search(r'Syn:\s*([^/;]+?)(?=\s*Ant:|$)', g_syn)
                        ant_match = re.search(r'Ant:\s*([^/;]+)', g_syn)
                        if syn_match:
                            syn_text = syn_match.group(1).strip()
                        if ant_match:
                            ant_text = ant_match.group(1).strip()
                    else:
                        parts = re.split(r'[/|]', g_syn)
                        if len(parts) >= 2:
                            syn_text = parts[0].strip()
                            ant_text = parts[1].strip()
                        else:
                            syn_text = g_syn.strip()
                    
                    if syn_text:
                        syn_ant_html += f'<span style="color:#2E8B57;">✨Syn:{syn_text}</span>'
                    if ant_text:
                        if syn_text:
                            syn_ant_html += ' '
                        syn_ant_html += f'<span style="color:#CD5C5C;">❄️Ant:{ant_text}</span>'
                    
                    if syn_ant_html:
                        all_grammar.append(syn_ant_html)
                
                if g_grammar:
                    text = str(g_grammar)
                    text = re.sub(r'\\?\*\s+', '• ', text)
                    text = text.replace('1️⃣[', '1️⃣[')
                    text = text.replace('2️⃣[', '<br>2️⃣[')
                    text = text.replace('3️⃣[', '<br>3️⃣[')
                    text = text.replace('4️⃣[', '<br>4️⃣[')
                    text = text.replace('\n', '<br>')
                    all_grammar.append(text)
                
                v2_jp = v2_row.get('口語訳', '') if v2_row else ''
                v2_grammar = v2_row.get('Grammar', '') if v2_row else ''
                v2_note = v2_row.get('Note', '') if v2_row else ''
                
                if v2_jp:
                    v2_parts = ["<br>"]
                    v2_ref = v2_row.get('Ref.', g_ref) if v2_row else g_ref
                    v2_parts.append(f"<b>{v2_ref}</b>{v2_jp}")
                    
                    if v2_grammar:
                        v2_parts.append(f'<span style="color:#4682B4;">文法：</span>{v2_grammar}')
                    if v2_note:
                        v2_parts.append(f'<span style="color:#D2691E;">備註：</span>{v2_note}')
                    
                    all_grammar.append("<br>".join(v2_parts))
                    
            else:
                orig = (g_row.get('Original Sentence (from text)', '') or 
                        g_row.get('Original Sentence', ''))
                rule = g_row.get('Grammar Rule', '')
                analysis = (g_row.get('Analysis & Example (1️⃣2️⃣3️⃣4️⃣)', '') or
                           g_row.get('Analysis & Example', '') or
                           g_row.get('Analysis', ''))
                
                html_parts = []
                
                if orig:
                    html_parts.append(
                        f'<div style="margin-bottom:2px; color:#FFD700; font-size:15px; font-weight:bold;">'
                        f'{orig}</div>'
                    )
                
                if analysis:
                    af = str(analysis).strip()
                    
                    if rule:
                        af = af.replace('1️⃣', f'📌 {rule}<br>1️⃣', 1)
                    
                    af = af.replace(
                        '1️⃣**[分段解析+語法標籤]**：',
                        '<div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">1️⃣[分段解析+語法標籤]：</span>'
                    )
                    af = af.replace(
                        '2️⃣**[詞性辨析]**：',
                        '</div><div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">2️⃣[詞性辨析]：</span>'
                    )
                    af = af.replace(
                        '3️⃣**[修辭與結構]**：',
                        '</div><div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">3️⃣[修辭與結構]：</span>'
                    )
                    af = af.replace(
                        '4️⃣**[語意解釋]**：',
                        '</div><div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">4️⃣[語意解釋]：</span>'
                    )
                    
                    af = af.replace(
                        '1️⃣[分段解析+語法標籤]：',
                        '<div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">1️⃣[分段解析+語法標籤]：</span>'
                    )
                    af = af.replace(
                        '2️⃣[詞性辨析]：',
                        '</div><div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">2️⃣[詞性辨析]：</span>'
                    )
                    af = af.replace(
                        '3️⃣[修辭與結構]：',
                        '</div><div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">3️⃣[修辭與結構]：</span>'
                    )
                    af = af.replace(
                        '4️⃣[語意解釋]：',
                        '</div><div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">4️⃣[語意解釋]：</span>'
                    )
                    
                    af = af + '</div>'
                    
                    html_parts.append(af)
                
                all_grammar = html_parts
                
            if all_grammar:
                grammar_html = "<br>".join(all_grammar)        
                
        # 渲染畫面
        col_left, col_right = st.columns([0.67, 0.33])
        
        with col_left:
            if vocab_display:
                st.markdown(
                    "<div style='margin-bottom:4px; line-height:1.6;'>" + 
                    " ; ".join(vocab_display) + 
                    "</div>", 
                    unsafe_allow_html=True
                )
            else:
                st.caption("無單字資料（請確認有模式A資料）")
            
            st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

            if w_phrases:
                for i, row in enumerate(w_phrases):
                    p = (row.get('Word/Phrase', '') or 
                         row.get('Word/phrase', '') or 
                         row.get('words/phrases', '') or 
                         row.get('Word', '') or
                         row.get('No', ''))
                    
                    c = (row.get('Chinese', '') or 
                         row.get('Chinese Meaning', '') or
                         row.get('Meaning', ''))
                    
                    s = (row.get('Synonym+中文對照', '') or 
                         row.get('Synonym', '') or 
                         row.get('Syn', ''))
                    
                    a = (row.get('Antonym+中文對照', '') or 
                         row.get('Antonym', '') or 
                         row.get('Ant', ''))
                    
                    bible_ex = (row.get('全句聖經中英對照例句', '') or 
                               row.get('Bible Example', '') or 
                               row.get('Example', '') or
                               row.get('全句聖經中英對照例句 ', ''))
                    
                    if p and p != str(i+16):
                        parts = [f"🔤 **{p}**"]
                        if c: 
                            parts.append(f"<span style='color:#666;'>{c}</span>")
                        if s or a:
                            sa_parts = []
                            if s: 
                                sa_parts.append(f"<span style='color:#2E8B57;'>✨{s}</span>")
                            if a: 
                                sa_parts.append(f"<span style='color:#CD5C5C;'>❄️{a}</span>")
                            parts.append("<span style='font-size:0.9em;'>" + " | ".join(sa_parts) + "</span>")
                        
                        st.markdown(
                            "<div style='margin-bottom:2px;'>" + " ".join(parts) + "</div>", 
                            unsafe_allow_html=True
                        )
                        
                        if bible_ex:
                            match = re.match(r'([^(]+)(\([^)]+\))?$', bible_ex)
                            if match:
                                eng_part = match.group(1).strip()
                                cn_part = match.group(2) if match.group(2) else ""
                                bible_html = f"<span style='font-size:1.15em; font-weight:500;'>{eng_part}</span> <span style='font-size:0.9em; color:#666;'>{cn_part}</span>"
                            else:
                                bible_html = f"<span style='font-size:1.15em;'>{bible_ex}</span>"
                            
                            st.markdown(
                                f"<div style='margin-bottom:4px; margin-left:20px;'>📖 {bible_html}</div>", 
                                unsafe_allow_html=True
                            )
                        
                        if i < len(w_phrases) - 1:
                            st.markdown("<div style='margin:4px 0;'></div>", unsafe_allow_html=True)
            else:
                st.caption(f"無片語資料（模式B={len(all_mode_b)}個）")
                if all_mode_b:
                    for mb in all_mode_b:
                        st.caption(f"  - {mb['ref']}: {mb['w_count']}筆")

            st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

            if verse_lines:
                st.markdown(f"<div style='margin-bottom:4px;'>{verse_lines[0]}</div>", unsafe_allow_html=True)
                for v in verse_lines[1:]:
                    st.markdown(f"<div style='margin-bottom:2px;'>{v}</div>", unsafe_allow_html=True)
            else:
                st.caption("📖 無金句資料（請確認有模式A資料）")

        with col_right:
            st.markdown(f"""
                <div style="background-color:#1E1E1E; color:#FFFFFF; padding:10px; border-radius:8px; 
                            border-left:4px solid #FF8C00; font-size:13px; line-height:1.5; 
                            min-height:100%; display:flex; flex-direction:column;">
                    {grammar_html}
                </div>
                """, unsafe_allow_html=True)
            
            minutes_left = max(0, (3600 - time_diff) / 60)
            st.caption(f"單字:{current_vocab_ref} | 片語:{current_phrase_ref} | 金句:{current_verse_ref}")
            st.caption(f"文法:{current_grammar_ref} | {minutes_left:.0f}分後更新")
            st.caption(f"資料統計: A={len(all_mode_a)}個, B={len(all_mode_b)}個, 文法源={len(all_grammar_sources)}個")

# ===================================================================
# 4. TAB2 ─ 月曆待辦 + 時段金句 + 收藏金句（修正版）
# ===================================================================
with tabs[1]:
    import datetime as dt, re, os, json
    from streamlit_calendar import calendar
    from io import StringIO
    import csv

    # 確保資料已載入
    if 'sentences' not in st.session_state:
        st.session_state.sentences = load_sentences()
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

    # 全局CSS：壓縮所有間距
    st.markdown("""
        <style>
        div[data-testid="stVerticalBlock"] > div {padding: 0px !important; margin: 0px !important;}
        div[data-testid="stVerticalBlock"] > div > div {padding: 0px !important; margin: 0px !important;}
        p {margin: 0px !important; padding: 0px !important; line-height: 1.2 !important;}
        .stMarkdown {margin: 0px !important; padding: 0px !important;}
        .stButton button {padding: 0px 4px !important; min-height: 24px !important; font-size: 12px !important; margin: 0px !important;}
        hr {margin: 2px 0 !important; padding: 0 !important;}
        div[data-testid="stExpander"] {margin: 2px 0 !important;}
        div[data-testid="stExpander"] > div {padding: 0px 8px !important;}
        div[data-testid="column"] {padding: 0px 2px !important;}
        </style>
    """, unsafe_allow_html=True)

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

    # ---------- 3. 待辦清單 ----------
    st.markdown('<p style="margin:0;padding:0;font-size:14px;font-weight:bold;">📋 待辦事項</p>', unsafe_allow_html=True)

    try:
        selected_date = dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date()
    except:
        selected_date = dt.date.today()

    d_str = str(selected_date)
    has_todo = False
    
    if d_str in st.session_state.todo and st.session_state.todo[d_str]:
        has_todo = True
        
        for idx, item in enumerate(st.session_state.todo[d_str]):
            item_id = f"{d_str}_{idx}"
            title = item.get("title", "") if isinstance(item, dict) else str(item)
            time_str = item.get('time', '')[:5] if isinstance(item, dict) and item.get('time') else ""

            c1, c2, c3 = st.columns([0.3, 8, 1.2])
            
            with c1:
                if st.button("💟", key=f"h_{item_id}"):
                    st.session_state.active_del_id = None if st.session_state.active_del_id == item_id else item_id
                    st.rerun()

            with c2:
                st.markdown(f'<p style="margin:0;padding:0;line-height:1.2;font-size:13px;">{time_str} {title}</p>', unsafe_allow_html=True)

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
            st.markdown('<div style="height:1px;"></div>', unsafe_allow_html=True)
    
    if not has_todo:
        st.caption(f"{selected_date.month}/{selected_date.day} 尚無待辦事項")
        
    # ---------- 4. 新增待辦 ----------
    with st.expander("➕ 新增待辦", expanded=False):
        with st.form("todo_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                in_date = st.date_input("日期", selected_date)
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
    
    # ---------- 5. 時段金句 ----------
    st.markdown('<p style="margin:0;padding:0;font-size:14px;font-weight:bold;">📖 今日時段金句</p>', unsafe_allow_html=True)
    
    sentences = st.session_state.sentences
    all_verses = []
    
    for ref, data in sentences.items():
        v1_content = data.get('v1_content', '')
        v2_content = data.get('v2_content', '')
        if v1_content and v1_content.strip():
            try:
                def parse_to_list(content):
                    content = content.strip()
                    if not content: return []
                    if content.startswith('|'):
                        lines = [l.strip() for l in content.split('\n') if l.strip()]
                        if len(lines) < 3: return []
                        headers = [h.strip() for h in lines[0].split('|') if h.strip()]
                        data_rows = []
                        for l in lines[2:]:
                            cols = [c.strip() for c in l.split('|') if c.strip()]
                            if len(cols) == len(headers):
                                data_rows.append(dict(zip(headers, cols)))
                        return data_rows
                    else:
                        reader = csv.DictReader(StringIO(content))
                        return list(reader)

                v1_rows = parse_to_list(v1_content)
                v2_rows = parse_to_list(v2_content) if v2_content else []
                
                for i, row in enumerate(v1_rows):
                    v2_row = v2_rows[i] if i < len(v2_rows) else {}
                    verse_ref = row.get('Ref.', row.get('Ref', ref))
                    en = row.get('English (ESV)', row.get('English', row.get('ESV', '')))
                    cn = row.get('Chinese', row.get('Chinese (CUV)', row.get('CUV', '')))
                    jp = v2_row.get('口語訳 (1955)', v2_row.get('口語訳', '')) if v2_row else ''
                    kr = v2_row.get('KRF', '') if v2_row else ''
                    th = v2_row.get('THSV11 (Key Phrases)', v2_row.get('THSV11', '')) if v2_row else ''
                    
                    # 只加入有內容的經文
                    if (en and str(en).strip()) or (cn and str(cn).strip()):
                        all_verses.append({
                            'ref': verse_ref,
                            'en': en if en else '',
                            'jp': jp if jp else '',
                            'kr': kr if kr else '',
                            'th': th if th else '',
                            'cn': cn if cn else ''
                        })
            except Exception as e:
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
            v = all_verses[idx]
            
            line1_parts = []
            if v['en']: 
                line1_parts.append(f"🇬🇧 <b>{v['ref']}</b> {v['en']}")
            if v['jp']: 
                line1_parts.append(f"🇯🇵 {v['jp']}")
            if v['kr']: 
                line1_parts.append(f"🇰🇷 {v['kr']}")
            if v['th']: 
                line1_parts.append(f"🇹🇭 {v['th']}")
            
            line2 = f"🇨🇳 <span style='color:#999;'>{v['cn']}</span>" if v['cn'] else ""
            
            if line1_parts:
                st.markdown(f'<p style="margin:0;padding:0;font-size:12px;line-height:1.1;"><b>{i+1}.</b> {" ".join(line1_parts)}</p>', unsafe_allow_html=True)
            if line2:
                st.markdown(f'<p style="margin:0;padding:0;font-size:12px;line-height:1.1;margin-left:14px;">{line2}</p>', unsafe_allow_html=True)
            
            if i < 5:
                st.markdown('<hr style="margin:1px 0;border:none;border-top:1px solid #eee;">', unsafe_allow_html=True)
    else:
        st.caption("尚無金句資料")

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
# 5. TAB3 ─ 挑戰（簡化版：直接給題目，最後給答案）
# ===================================================================
with tabs[2]:
    # 確保資料已載入
    if 'sentences' not in st.session_state:
        st.session_state.sentences = load_sentences()
    
    sentences = st.session_state.sentences

    # 隱藏 Streamlit 元件預設的過大間距
    st.markdown("""
        <style>
            [data-testid="stVerticalBlock"] > div {
                gap: 0rem;
            }
            .stTextInput {
                margin-top: -15px !important;
                margin-bottom: 0px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    if 'tab3_quiz_seed' not in st.session_state:
        st.session_state.tab3_quiz_seed = random.randint(1, 1000)
        st.session_state.tab3_show_answers = False
    
    if not sentences:
        st.warning("資料庫為空，請先在 TAB4 儲存資料")
    else:
        # 排序資料
        sorted_refs = sorted(sentences.keys(), 
                           key=lambda x: sentences[x].get('date_added', ''), 
                           reverse=True)
        total = len(sorted_refs)
        
        new_refs = sorted_refs[:int(total*0.6)] if total >= 5 else sorted_refs
        mid_refs = sorted_refs[int(total*0.6):int(total*0.9)] if total >= 10 else []
        old_refs = sorted_refs[int(total*0.9):] if total >= 10 else []
        
        weighted_pool = (new_refs * 6) + (mid_refs * 3) + (old_refs * 1)
        if not weighted_pool:
            weighted_pool = sorted_refs
        
        random.seed(st.session_state.tab3_quiz_seed)
        
        # 雙相容解析函數
        def parse_v1_content(content):
            content = content.strip()
            if not content: return []
            if content.startswith('|'):
                lines = [l.strip() for l in content.split('\n') if l.strip()]
                if len(lines) < 3: return []
                headers = [h.strip() for h in lines[0].split('|') if h.strip()]
                data_rows = []
                for l in lines[2:]:
                    cols = [c.strip() for c in l.split('|') if c.strip()]
                    if len(cols) == len(headers):
                        data_rows.append(dict(zip(headers, cols)))
                return data_rows
            else:
                return list(csv.DictReader(StringIO(content)))

        # 收集經文
        all_verses = []
        for ref in weighted_pool[:20]:  # 增加取樣數量
            data = sentences[ref]
            v1_content = data.get('v1_content', '')
            if v1_content and v1_content.strip():
                try:
                    rows = parse_v1_content(v1_content)
                    for row in rows:
                        # 確保有內容才加入
                        chinese = row.get('Chinese', row.get('Chinese (CUV)', row.get('CUV', '')))
                        english = row.get('English (ESV)', row.get('English', row.get('ESV', '')))
                        
                        if (chinese and str(chinese).strip()) or (english and str(english).strip()):
                            all_verses.append({
                                'ref': row.get('Ref.', row.get('Ref', ref)),
                                'english': english if english else '',
                                'chinese': chinese if chinese else '',
                                'syn_ant': row.get('Syn/Ant', row.get('Syn/Ant.', ''))
                            })
                except Exception as e:
                    pass
        
        # 確保有足夠的題目
        if len(all_verses) < 6:
            st.warning(f"資料庫中只有 {len(all_verses)} 筆可用資料，需要至少 6 筆才能生成挑戰題")
            st.stop()
        
        random.shuffle(all_verses)
        # 確保至少有3個中翻英和3個英翻中
        zh_to_en_candidates = [v for v in all_verses if v['chinese'] and str(v['chinese']).strip()]
        en_to_zh_candidates = [v for v in all_verses if v['english'] and str(v['english']).strip()]
        
        if len(zh_to_en_candidates) < 3 or len(en_to_zh_candidates) < 3:
            st.warning("可用資料不足，請確保資料包含中英文內容")
            st.stop()
        
        zh_to_en = zh_to_en_candidates[:3]
        en_to_zh = en_to_zh_candidates[:3]
        
        st.subheader("📝 翻譯挑戰")
        
        # 題目 1-3：中翻英
        for i, q in enumerate(zh_to_en, 1):
            st.markdown(f'<p style="margin: 0px; font-size: 14px; font-weight: bold;">{i}. {q["chinese"][:60]}</p>', unsafe_allow_html=True)
            st.text_input("", key=f"quiz_zh_en_{i}", placeholder="請翻譯成英文...", label_visibility="collapsed")
            st.markdown('<div style="margin-bottom: 2px;"></div>', unsafe_allow_html=True)
        
        # 題目 4-6：英翻中
        for i, q in enumerate(en_to_zh, 4):
            st.markdown(f'<p style="margin: 0px; font-size: 14px; font-weight: bold;">{i}. {q["english"][:100]}</p>', unsafe_allow_html=True)
            st.text_input("", key=f"quiz_en_zh_{i}", placeholder="請翻譯成中文...", label_visibility="collapsed")
            st.markdown('<div style="margin-bottom: 2px;"></div>', unsafe_allow_html=True)
        
        # 單字題
        word_pool = []
        for v in all_verses:
            syn_ant = v.get('syn_ant', '')
            if '/' in syn_ant:
                for p in syn_ant.split('/'):
                    match = re.match(r'(.+?)\s*\((.+?)\)', p.strip())
                    if match:
                        word_pool.append({'en': match.group(1).strip(), 'cn': match.group(2).strip()})
        
        random.shuffle(word_pool)
        selected_words = word_pool[:3] if len(word_pool) >= 3 else word_pool
        
        for i, w in enumerate(selected_words, 7):
            st.markdown(f'<p style="margin: 0px; font-size: 14px; font-weight: bold;">{i}. {w["cn"]}（請寫出英文）</p>', unsafe_allow_html=True)
            st.text_input("", key=f"quiz_word_{i}", placeholder="English word...", label_visibility="collapsed")
            st.markdown('<div style="margin-bottom: 2px;"></div>', unsafe_allow_html=True)
        
        # 翻看答案
        st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
        col_btn, col_answer = st.columns([1, 3])
        with col_btn:
            if st.button("👁️ 翻看正確答案", use_container_width=True, type="primary"):
                st.session_state.tab3_show_answers = True
                st.rerun()
        
        with col_answer:
            if st.session_state.tab3_show_answers:
                with st.expander("📖 正確答案", expanded=True):
                    st.markdown("**中翻英：**")
                    for i, q in enumerate(zh_to_en, 1):
                        st.caption(f"{i}. {q['english']}")
                    st.markdown("**英翻中：**")
                    for i, q in enumerate(en_to_zh, 4):
                        st.caption(f"{i}. {q['chinese']}")
                    st.markdown("**單字：**")
                    for i, w in enumerate(selected_words, 7):
                        st.caption(f"{i}. {w['en']}")
                             
                if st.button("🔄 換一批題目", use_container_width=True):
                    st.session_state.tab3_quiz_seed = random.randint(1, 1000)
                    st.session_state.tab3_show_answers = False
                    st.rerun()

# ===================================================================
# 6. TAB4 ─ AI 控制台（已移除 Notion，改用 Google Sheets）
# ===================================================================
with tabs[3]:
    # 確保資料已載入
    if 'sentences' not in st.session_state:
        sheets_data = load_from_google_sheets()
        st.session_state.sentences = sheets_data if sheets_data else load_sentences()
    
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

    # 1. 智能偵測內容類型
    def detect_content_mode(text):
        text = text.strip()
        if not text:
            return "document"
        if text.startswith("{"):
            return "json"
        
        has_chinese = re.search(r'[\u4e00-\u9fa5]', text)
        return "scripture" if has_chinese else "document"

    # 2. 產生完整指令
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
| Ref. | 口語訳 | Grammar | Note | KRF | Syn/Ant | THSV11 |
|------|--------|---------|------|-----|---------|--------|

🔹 V1 Sheet 欄位要求：
1. Ref.：自動找尋經卷章節並用縮寫 (如: Pro, Rom, Gen).
2. English (ESV)：檢索對應的 ESV 英文經文.
3. Chinese：填入我提供的中文原文.
4. Syn/Ant："同義字與反義字"，取自ESV中的高級/中高級單字或片語（含中/英翻譯）
5. Grammar：嚴格遵守符號化格式＋嚴格提供詳細規範...

🔹 V2 Sheet 欄位要求：
1. Ref.：同 V1.
2. 口語訳：檢索對應的日本《口語訳聖經》(1955).
3. Grammar格式同 V1
4. Note：日文文法或語境的補充說明.
5. KRF：檢索對應的韓文《Korean Revised Version》.
6. Syn/Ant：韓文高/ 中高級字（含日/韓/中翻譯）.
7. THSV11:輸出泰文"對應的重要片語key phrases"《Thai Holy Bible, Standard Version 2011》.

請以 **Markdown 表格格式**輸出（非 JSON）.

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

【P Sheet - 文稿段落】
| Paragraph | English Refinement | 中英夾雜講章 |
|-----------|-------------------|--------------|
| 1 | We need to be steadfast... | 我們需要 (**steadfast**) ... |

【Grammar List - 重點要求：6 句 × 每句4個解析】
| No | Original Sentence (from text) | Grammar Rule | Analysis & Example (1️⃣2️⃣3️⃣...5️⃣) |
|----|------------------------------|--------------|-----------------------------------|
| 1 | [文稿中的第1個精選句] | [文法規則名稱] | 1️⃣[分段解析+語法標籤]...<br>2️⃣[詞性辨析]...<br>3️⃣[修辭與結構或遞進邏輯]...<br>4️⃣[語意解釋]...<br>...|

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

    # 快速功能區
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
                        "v2_content": "Ref.\t口語訳\tGrammar\tNote\tKRF\tSyn/Ant\tTHSV11\n",
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
                
                if GC and SHEET_ID:
                    save_to_google_sheets(blank_structure)
                
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

    # 編輯模式介面
    if st.session_state.get('edit_mode') and st.session_state.get('edit_ref'):
        st.markdown(f"<h6>✏️ 編輯模式：{st.session_state.edit_ref}</h6>", unsafe_allow_html=True)
        
        item = st.session_state.sentences.get(st.session_state.edit_ref, {})
        current_mode = item.get('mode', 'A')
        
        if current_mode == 'A':
            edit_tabs = st.tabs(["V1 Sheet", "V2 Sheet", "其他補充", "儲存"])
            
            with edit_tabs[0]:
                new_v1 = st.text_area("V1 Sheet 內容", value=st.session_state.current_entry['v1'], height=300, key="edit_v1")
                st.session_state.current_entry['v1'] = new_v1
            
            with edit_tabs[1]:
                new_v2 = st.text_area("V2 Sheet 內容", value=st.session_state.current_entry['v2'], height=300, key="edit_v2")
                st.session_state.current_entry['v2'] = new_v2
            
            with edit_tabs[2]:
                new_other = st.text_area("其他補充", value=st.session_state.current_entry['other'], height=200, key="edit_other")
                st.session_state.current_entry['other'] = new_other
            
            with edit_tabs[3]:
                st.write("確認修改後儲存：")
                if st.button("💾 儲存變更", use_container_width=True, type="primary"):
                    updated_data = {
                        'v1_content': st.session_state.current_entry['v1'],
                        'v2_content': st.session_state.current_entry['v2'],
                        'other': st.session_state.current_entry['other'],
                        'saved_sheets': ['V1 Sheet', 'V2 Sheet'] if st.session_state.current_entry['v1'] else [],
                        'date_added': dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.session_state.sentences[st.session_state.edit_ref].update(updated_data)
                    save_sentences(st.session_state.sentences)
                    
                    if GC and SHEET_ID:
                        full_data = st.session_state.sentences[st.session_state.edit_ref]
                        save_to_google_sheets(full_data)
                    
                    st.success("✅ 已儲存並同步到雲端！")
        else:
            edit_tabs = st.tabs(["W Sheet", "P Sheet", "Grammar List", "其他補充", "儲存"])
            
            with edit_tabs[0]:
                new_w = st.text_area("W Sheet 內容", value=st.session_state.current_entry['w_sheet'], height=300, key="edit_w")
                st.session_state.current_entry['w_sheet'] = new_w
            
            with edit_tabs[1]:
                new_p = st.text_area("P Sheet 內容", value=st.session_state.current_entry['p_sheet'], height=300, key="edit_p")
                st.session_state.current_entry['p_sheet'] = new_p
            
            with edit_tabs[2]:
                new_g = st.text_area("Grammar List 內容", value=st.session_state.current_entry['grammar_list'], height=300, key="edit_g")
                st.session_state.current_entry['grammar_list'] = new_g
            
            with edit_tabs[3]:
                new_other = st.text_area("其他補充", value=st.session_state.current_entry['other'], height=200, key="edit_other_b")
                st.session_state.current_entry['other'] = new_other
            
            with edit_tabs[4]:
                st.write("確認修改後儲存：")
                if st.button("💾 儲存變更", use_container_width=True, type="primary"):
                    updated_data = {
                        'w_sheet': st.session_state.current_entry['w_sheet'],
                        'p_sheet': st.session_state.current_entry['p_sheet'],
                        'grammar_list': st.session_state.current_entry['grammar_list'],
                        'other': st.session_state.current_entry['other'],
                        'saved_sheets': ['W Sheet', 'P Sheet', 'Grammar List'],
                        'date_added': dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.session_state.sentences[st.session_state.edit_ref].update(updated_data)
                    save_sentences(st.session_state.sentences)
                    
                    if GC and SHEET_ID:
                        full_data = st.session_state.sentences[st.session_state.edit_ref]
                        save_to_google_sheets(full_data)
                    
                    st.success("✅ 已儲存並同步到雲端！")
        
        st.divider()

    # 主要功能區
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
            
            cols = st.columns(3)
            with cols[0]:
                encoded = urllib.parse.quote(st.session_state.get('main_input_value', ''))
                st.link_button("💬 開啟 GPT", f"https://chat.openai.com/?q={encoded}", use_container_width=True)
            with cols[1]:
                st.link_button("🌙 開啟 Kimi", "https://kimi.com", use_container_width=True)
            with cols[2]:
                st.link_button("🔍 開啟 Gemini", "https://gemini.google.com", use_container_width=True)

        # STEP 3: 多工作表收集區
        with st.expander("步驟 3：分批貼上 AI 分析結果", expanded=True):
            st.info("💡 可以分批貼上 V1、V2、W Sheet、P Sheet 等，貼好一個存一個")
            
            if st.session_state.content_mode == "A":
                sheet_options = ["V1 Sheet", "V2 Sheet", "其他補充"]
            else:
                sheet_options = ["W Sheet", "P Sheet", "Grammar List", "其他補充"]
            
            selected_sheet = st.selectbox("選擇要貼上的工作表", sheet_options)
            
            sheet_content = st.text_area(f"貼上 {selected_sheet} 內容", height=200, key=f"input_{selected_sheet.replace(' ', '_')}")
            
            col_temp, col_view = st.columns([1, 3])
            with col_temp:
                if st.button("➕ 暫存此工作表", use_container_width=True):
                    key_map = {
                        "V1 Sheet": "v1", "V2 Sheet": "v2",
                        "W Sheet": "w_sheet", "P Sheet": "p_sheet",
                        "Grammar List": "grammar_list", "其他補充": "other"
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
            ref_input = st.text_input("Ref / 檔名", value=get_default_ref(), key="ref_no_input")
            
            type_select = st.selectbox("類型", ["Scripture", "Document", "Vocabulary", "Grammar", "Sermon"],
                                       index=0 if st.session_state.content_mode == "A" else 1, key="type_select")
            
            btn_cols = st.columns([1, 1])
            
            with btn_cols[0]:
                if st.button("💾 儲存到雲端", use_container_width=True, type="primary"):
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
                            
                            if GC and SHEET_ID:
                                success, msg = save_to_google_sheets(full_data)
                                if success:
                                    st.success(f"✅ 已同步到 Google Sheets！({msg})")
                                else:
                                    st.warning(f"⚠️ Google Sheets 同步失敗：{msg}，但已儲存到本地")
                            else:
                                st.warning("⚠️ Google Sheets 未連線，僅儲存到本地")
                            
                            st.balloons()
                            
                        except Exception as e:
                            st.error(f"❌ 儲存失敗：{str(e)}")
            
            with btn_cols[1]:
                if st.button("🔄 新的分析", use_container_width=True):
                    keys_to_clear = ['is_prompt_generated', 'main_input_value', 'original_text',
                                   'content_mode', 'raw_input_value', 'ref_number', 'raw_input_temp',
                                   'current_entry', 'saved_entries', 'ref_no_input']
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

    # 儲存狀態顯示區
    st.divider()
    status_cols = st.columns([1, 1, 2])
    
    with status_cols[0]:
        total_local = len(st.session_state.get('sentences', {}))
        st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>💾 本地快取</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 16px; font-weight: bold; margin: 0;'>{total_local} 筆</p>", unsafe_allow_html=True)
    
    with status_cols[1]:
        if GC and SHEET_ID:
            st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>☁️ Google Sheets</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 16px; font-weight: bold; margin: 0; color: #28a745;'>✅ 已連線</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>☁️ Google Sheets</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 16px; font-weight: bold; margin: 0; color: #dc3545;'>❌ 未連線</p>", unsafe_allow_html=True)
    
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
            selected_ref = st.selectbox("選擇資料項目", ref_list,
                                        format_func=lambda x: f"{x} - {st.session_state.sentences[x].get('date_added', '無日期')}")
            
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
                            key_map = {"V1 Sheet": "v1_content", "V2 Sheet": "v2_content",
                                      "W Sheet": "w_sheet", "P Sheet": "p_sheet",
                                      "Grammar List": "grammar_list", "其他補充": "other"}
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
    st.caption(f"💾 資料庫：{total_count} 筆 | 儲存位置：本地 + Google Sheets")
    if st.session_state.get('sentences', {}):
        json_str = json.dumps(st.session_state.sentences, ensure_ascii=False, indent=2)
        st.download_button("⬇️ 備份 JSON", json_str,
                          file_name=f"backup_{dt.datetime.now().strftime('%m%d_%H%M')}.json",
                          mime="application/json", use_container_width=True)
