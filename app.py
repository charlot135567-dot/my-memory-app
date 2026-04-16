# ===================================================================
# 0. 套件（統一最頂）
# ===================================================================
import streamlit as st
import streamlit.components.v1 as components
from streamlit_calendar import calendar
import pandas as pd
import csv
from io import StringIO
import os
import json
import base64
import datetime
import requests
import random
import re
import io
from gtts import gTTS
import time
from google.api_core import exceptions

# Gemini API 匯入（含錯誤處理）
try:
    import google.generativeai as genai
except ImportError:
    genai = None
    st.warning("⚠️ google-generativeai 未安裝，AI 功能將無法使用")

# ==========================================
# 核心函數：處理 AI 解析與錯誤重試
# ==========================================
def run_bible_ai_analysis(current_verse):
    """執行聖經解析，自動處理 404 與 429 錯誤"""
    # 1. 取得資料
    verse_text = current_verse.get('english', '')
    chinese_text = current_verse.get('chinese', '')
    ref_text = current_verse.get('ref', '')

    # 2. API 設定
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 請在 secrets.toml 中設定 GEMINI_API_KEY")
        return

    try:
        genai.configure(api_key=api_key)

        # 3. 解決 404：動態找模型
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if "1.5-flash" in m), "models/gemini-1.5-flash")
        model = genai.GenerativeModel(target_model)

        prompt = f"請針對以下經文進行 JSON 語法解析：\n{ref_text}\n{verse_text}\n{chinese_text}"

        # 4. 解決 429：自動重試機制 (重試 5 次)
        response = None
        for i in range(5):
            try:
                response = model.generate_content(prompt)
                break 
            except exceptions.ResourceExhausted:
                wait_time = (2 ** i) + 1
                st.warning(f"⚠️ API 忙碌中，{wait_time} 秒後重試... ({i+1}/5)")
                time.sleep(wait_time)
            except Exception as e:
                raise e

        # 5. 安全解析 JSON
        raw_text = response.text
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            st.session_state.tab1_ai_result = json.loads(json_match.group(0))
            st.success("✅ AI 解析完成！")
        else:
            raise ValueError("格式錯誤")

    except Exception as e:
        # 加上這一行，讓我們看到底是哪裡錯了
        st.error(f"⚠️ 偵測到錯誤原因: {str(e)}") 
        
        # 降級處理
        st.session_state.tab1_ai_result = {
            "vocabulary": [{"word": "解析錯誤", "phonetic": "/error/", "meaning": "請稍後再試"}],
            "phrases": [{"phrase": "System Busy", "meaning": "API 暫時無法連線"}],
            "segments": [{"cn": chinese_text, "en": verse_text}]
        }

# 標準庫
import io

# --- Google Sheets 認證 ---
from google.oauth2.service_account import Credentials
import gspread

# ===================================================================
# 0.1 語音播放功能 (gTTS)
# ===================================================================
def text_to_speech(text, lang='en'):
    """將文字轉換為語音並返回 base64 編碼"""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_bytes = fp.read()
        b64 = base64.b64encode(audio_bytes).decode()
        return f'<audio controls autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mpeg"></audio>'
    except Exception as e:
        return f"<p>語音播放錯誤: {str(e)}</p>"

def play_audio_html(text, lang='en'):
    """生成音頻 HTML"""
    audio_html = text_to_speech(text, lang)
    st.markdown(audio_html, unsafe_allow_html=True)

# ===================================================================
# 0.2 AI 分析函式 (Gemini API) - 最終修正版
# ===================================================================
def analyze_scripture_with_ai(text, chinese, reference):
    """
    呼叫 Gemini API 進行經文解析，支援自動模型偵測與「強效」Secrets 讀取。
    """
    # 1. 檢查套件載入
    if genai is None:
        st.error("❌ Google Generative AI 套件未安裝")
        return None

    # 2. 強效讀取 API Key
    api_key = None
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        elif "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
            api_key = st.secrets["gemini"]["api_key"]
        elif "gemini_api_key" in st.secrets:
            api_key = st.secrets["gemini_api_key"]

        if not api_key:
            raise KeyError
    except Exception:
        st.error("❌ 讀取 API Key 失敗。")
        st.warning(f"目前 Secrets 包含: {list(st.secrets.keys())}")
        return None

    # 3. 配置與自動偵測可用模型
    try:
        genai.configure(api_key=api_key)
        
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception as list_e:
            st.error(f"無法取得模型清單: {list_e}")
            return None

        if not available_models:
            st.error("❌ 你的 API Key 目前沒有任何可用的生成模型。")
            return None

        target_model = None
        for m_name in available_models:
            if "gemini-1.5-flash" in m_name:
                target_model = m_name
                break
        
        if not target_model:
            target_model = available_models[0]
            st.warning(f"⚠️ 自動選用相容模型: {target_model}")

        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        # 4. 定義 Prompt
        prompt = f"""
        Act as a Bible linguist. Analyze this verse for flashcard learning.
        Verse: {text}
        Translation: {chinese}
        Ref: {reference}

        Return a JSON object ONLY with this exact structure:
        {{
          "vocabulary": [{{ "word": "word", "meaning": "意思", "phonetic": "/.../", "example": "sentence" }}],
          "phrases": [{{ "phrase": "phrase", "meaning": "意思", "example": "sentence" }}],
          "segments": [{{ "en": "Eng segment", "cn": "中文段句" }}],
          "full_verse": {{ "en": "{text}", "cn": "{chinese}", "ref": "{reference}" }},
          "podcast_script": [{{ "speaker": "Rachel", "text": "..." }}, {{ "speaker": "Mike", "text": "..." }}]
        }}
        Extract 2-3 words and 1-2 phrases.
        """

        # 5. 執行生成
        response = model.generate_content(prompt)

        if response and hasattr(response, 'text'):
            # A. 移除 Markdown 的 JSON 標籤
            clean_text = re.sub(r'```json|```', '', response.text).strip()

            try:
                # B. 嘗試標準解析
                return json.loads(clean_text, strict=False)
            except json.JSONDecodeError:
                # C. 二次修復
                st.warning("⚠️ 偵測到格式異常，正在進行二次修復...")
                fixed_text = "".join(ch for ch in clean_text if ord(ch) >= 32 or ch in "\n\r\t")
                try:
                    return json.loads(fixed_text, strict=False)
                except json.JSONDecodeError as e2:
                    st.error(f"⚠️ 無法修復 JSON 格式: {e2}")
                    return None
        else:
            st.error("AI 回傳內容為空")
            return None
            
    except Exception as e:
        st.error(f"⚠️ AI 運算過程出錯: {e}")
        return None
# ===================================================================
# 0.3 閃卡資料準備
# ===================================================================
def prepare_flashcards(analysis_data):
    """將分析資料轉換為閃卡格式"""
    flashcards = []
    
    for v in analysis_data.get('vocabulary', []):
        flashcards.append({
            'type': 'vocab',
            'front': f"**{v['meaning']}**",
            'back': f"### {v['word']}\n\n🔉 {v.get('phonetic', '')}\n\n**例句：**\n{v['example']}\n\n{v.get('example_cn', '')}",
            'audio': v['word'],
            'data': v
        })
    
    for p in analysis_data.get('phrases', []):
        flashcards.append({
            'type': 'phrase',
            'front': f"**{p['meaning']}**",
            'back': f"### {p['phrase']}\n\n**例句：**\n{p['example']}\n\n{p.get('example_cn', '')}",
            'audio': p['phrase'],
            'data': p
        })
    
    for i, s in enumerate(analysis_data.get('segments', [])):
        flashcards.append({
            'type': 'segment',
            'front': f"**段句 {i+1}**\n\n{s['cn']}",
            'back': f"{s['en']}",
            'audio': s['en'],
            'data': s
        })
    
    fv = analysis_data.get('full_verse', {})
    if fv:
        flashcards.append({
            'type': 'full',
            'front': f"**{fv.get('ref', '')}**\n\n{fv.get('cn', '')}",
            'back': f"{fv.get('en', '')}",
            'audio': fv.get('en', ''),
            'data': fv
        })
    
    return flashcards

# ===================================================================
# 0.4 閃卡導航函式
# ===================================================================
def next_card():
    """下一張閃卡"""
    if st.session_state.flashcards_data:
        st.session_state.flashcard_index = (st.session_state.flashcard_index + 1) % len(st.session_state.flashcards_data)
        st.session_state.flashcard_flipped = False

def prev_card():
    """上一張閃卡"""
    if st.session_state.flashcards_data:
        st.session_state.flashcard_index = (st.session_state.flashcard_index - 1) % len(st.session_state.flashcards_data)
        st.session_state.flashcard_flipped = False

def flip_card():
    """翻轉閃卡"""
    st.session_state.flashcard_flipped = not st.session_state.flashcard_flipped

# ===================================================================
# 0.5 資料儲存函數（統一使用 bible_data.json）
# ===================================================================
DATA_FILE = "bible_data.json"

def load_custom_verses():
    """載入自訂金句"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("custom_verses", [""] * 7)
        except:
            return [""] * 7
    return [""] * 7

def save_custom_verses(verses):
    """儲存自訂金句"""
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            pass
    data["custom_verses"] = verses
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_todos():
    """載入待辦事項"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("todos", {})
        except:
            return {}
    return {}

def save_todos():
    """儲存待辦事項"""
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            pass
    data["todos"] = st.session_state.todo
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_verse_by_reference(ref_input, sentences):
    """根據出處取得經文"""
    try:
        if ref_input in sentences:
            data = sentences[ref_input]
            content = data.get('v1_content', '')
            return extract_english(content), extract_chinese(content), ref_input
        
        ref_lower = ref_input.lower().replace(' ', '')
        for key in sentences.keys():
            if ref_lower in key.lower().replace(' ', ''):
                data = sentences[key]
                content = data.get('v1_content', '')
                return extract_english(content), extract_chinese(content), key
        
        return None, None, None
    except:
        return None, None, None

def extract_english(content):
    """從 Google Sheet 內容提取英文"""
    try:
        lines = content.strip().split('\n')
        if len(lines) < 2:
            return content
        headers = lines[0].split('\t')
        for i, h in enumerate(headers):
            if 'english' in h.lower() or 'esv' in h.lower():
                data_lines = [l for l in lines[1:] if l.strip()]
                if data_lines:
                    cells = data_lines[0].split('\t')
                    if i < len(cells):
                        return cells[i]
        return content
    except:
        return content

def extract_chinese(content):
    """從 Google Sheet 內容提取中文"""
    try:
        lines = content.strip().split('\n')
        if len(lines) < 2:
            return ""
        headers = lines[0].split('\t')
        for i, h in enumerate(headers):
            if 'chinese' in h.lower() or '中文' in h:
                data_lines = [l for l in lines[1:] if l.strip()]
                if data_lines:
                    cells = data_lines[0].split('\t')
                    if i < len(cells):
                        return cells[i]
        return ""
    except:
        return ""

def save_analysis_to_database(result):
    """儲存分析結果到資料庫"""
    try:
        data = {}
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        if 'ai_analysis' not in data:
            data['ai_analysis'] = []
        
        analysis_entry = {
            'reference': result.get('reference', ''),
            'timestamp': datetime.datetime.now().isoformat(),
            'words': result.get('words', []),
            'phrases': result.get('phrases', []),
            'flashcards': result.get('flashcards', []),
            'podcast_script': result.get('podcast_script', [])
        }
        
        data['ai_analysis'].append(analysis_entry)
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        st.error(f"儲存失敗: {e}")
        return False

def send_to_tab3(result):
    """傳送到 TAB3（挑戰測驗）"""
    if 'tab3_flashcards' not in st.session_state:
        st.session_state.tab3_flashcards = []
    
    for card in result.get('flashcards', []):
        st.session_state.tab3_flashcards.append({
            'front': card.get('front', ''),
            'back': card.get('back', ''),
            'reference': result.get('reference', '')
        })

def load_favorites():
    """載入收藏"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("favorites", [])
        except:
            return []
    return []

def save_favorites():
    """儲存收藏"""
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            pass
    data["favorites"] = st.session_state.favorite_sentences
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================================================================
# 頁面設定（必須是第一個 st. 指令！）
# ===================================================================
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# ===================================================================
# 診斷：檢查 secrets
# ===================================================================
if "gcp_service_account" not in st.secrets:
    st.error("❌ 找不到 gcp_service_account secrets！")
    st.info("""
    **請在 Streamlit Community Cloud 設定 Secrets：**
    
    1. 前往 https://share.streamlit.io/  
    2. 點擊你的 app → ⚙️ Settings → Secrets
    3. 貼上 TOML 格式的 Google Sheets 憑證
    
    [gcp_service_account]
    type = "service_account"
    ...
    """)
    st.stop()

if "sheets" not in st.secrets or "spreadsheet_id" not in st.secrets["sheets"]:
    st.error("❌ 找不到 sheets.spreadsheet_id！")
    st.stop()

# ===================================================================
# Google Sheets 連線
# ===================================================================
def get_google_sheets_client():
    """重新建立 Google Sheets 連線"""
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

# ===================================================================
# 資料庫設定
# ===================================================================
DATA_DIR = "data"
SENTENCES_FILE = os.path.join(DATA_DIR, "sentences.json")
TODO_FILE = os.path.join(DATA_DIR, "todos.json")
FAVORITE_FILE = os.path.join(DATA_DIR, "favorite_sentences.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ===================================================================
# 本地檔案操作
# ===================================================================
def load_sentences():
    """載入資料：優先從 Google Sheets，失敗時讀本地檔案"""
    google_data = load_sentences_from_google_sheets()
    
    if google_data:
        try:
            with open(SENTENCES_FILE, "w", encoding="utf-8") as f:
                json.dump(google_data, f, ensure_ascii=False, indent=2)
            st.sidebar.caption("💾 已同步更新本地快取")
        except Exception as e:
            st.sidebar.warning(f"本地快取更新失敗：{e}")
        
        return google_data
    
    st.sidebar.info("📁 從本地檔案載入...")
    
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
    """儲存本地快取"""
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

def load_todos_local():
    if os.path.exists(TODO_FILE):
        try:
            with open(TODO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_todos_local():
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.todo, f, ensure_ascii=False, indent=2)

def load_favorites_local():
    if os.path.exists(FAVORITE_FILE):
        try:
            with open(FAVORITE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_favorites_local():
    with open(FAVORITE_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.favorite_sentences, f, ensure_ascii=False, indent=2)

# ===================================================================
# 解析內容
# ===================================================================
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

# ===================================================================
# Google Sheets 儲存函式
# ===================================================================
def save_v1_sheet(ref, content, gc, sheet_id):
    """儲存到 V1_Sheet"""
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
    """儲存到 V2_Sheet"""
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
    """儲存到 W_Sheet"""
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
    """儲存到 P_Sheet"""
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
    """儲存到 Grammar_List"""
    if not content or not content.strip() or not gc or not sheet_id:
        return True
    
    try:
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("Grammar_List")
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet("Grammar_List", rows=1000, cols=5)
            ws.append_row(["檔名_批次", "No經卷範圍", "Original Sentence＋中文翻譯", "Grammar Rule", "Analysis & Example"])
        
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
    """將資料分別存入對應的 5 個工作表"""
    gc, sheet_id = get_google_sheets_client()
    
    if not gc or not sheet_id:
        st.sidebar.error("❌ Google Sheets 未連線")
        return False, "Google Sheets 未連線"
    
    try:
        ref = data_dict.get('ref', 'N/A')
        mode = data_dict.get('mode', 'A')
        
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
            st.sidebar.warning(f"⚠️ {ref} 已存在，跳過重複儲存")
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

def load_sentences_from_google_sheets():
    """從 Google Sheets 載入所有資料"""
    gc, sheet_id = get_google_sheets_client()
    
    if not gc or not sheet_id:
        st.sidebar.error("❌ 無法連線到 Google Sheets")
        return {}
    
    all_data = {}
    sh = gc.open_by_key(sheet_id)
    
    # V1_Sheet
    try:
        ws = sh.worksheet("V1_Sheet")
        rows = ws.get_all_values()
        st.sidebar.caption(f"📊 V1_Sheet：讀取 {len(rows)} 行")
        
        if len(rows) > 1:
            for row in rows[1:]:
                if len(row) >= 6:
                    group_ref = row[0].strip()
                    
                    if group_ref not in all_data:
                        all_data[group_ref] = {
                            "ref": group_ref,
                            "mode": "A",
                            "type": "Scripture",
                            "v1_content": "Ref.\tEnglish（ESV經文）\tChinese經文\tSyn/Ant\tGrammar\n",
                            "v2_content": "",
                            "w_sheet": "",
                            "p_sheet": "",
                            "grammar_list": "",
                            "other": "",
                            "saved_sheets": ["V1 Sheet"],
                            "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                    row_data = row[1:6] if len(row) >= 6 else row[1:] + [''] * (6 - len(row))
                    all_data[group_ref]["v1_content"] += "\t".join(row_data) + "\n"
    except gspread.WorksheetNotFound:
        st.sidebar.caption("ℹ️ V1_Sheet 不存在")
    except Exception as e:
        st.sidebar.error(f"V1_Sheet 讀取錯誤：{e}")
    
    # V2_Sheet
    try:
        ws = sh.worksheet("V2_Sheet")
        rows = ws.get_all_values()
        st.sidebar.caption(f"📊 V2_Sheet：讀取 {len(rows)} 行")
        
        if len(rows) > 1:
            for row in rows[1:]:
                if len(row) >= 8:
                    group_ref = row[0].strip()
                    
                    if group_ref in all_data:
                        row_data = row[1:8] if len(row) >= 8 else row[1:] + [''] * (8 - len(row))
                        all_data[group_ref]["v2_content"] += "\t".join(row_data) + "\n"
                        if "V2 Sheet" not in all_data[group_ref]["saved_sheets"]:
                            all_data[group_ref]["saved_sheets"].append("V2 Sheet")
    except gspread.WorksheetNotFound:
        st.sidebar.caption("ℹ️ V2_Sheet 不存在")
    except Exception as e:
        st.sidebar.error(f"V2_Sheet 讀取錯誤：{e}")
    
    # W_Sheet
    try:
        ws = sh.worksheet("W_Sheet")
        rows = ws.get_all_values()
        st.sidebar.caption(f"📊 W_Sheet：讀取 {len(rows)} 行")
        
        if len(rows) > 1:
            for row in rows[1:]:
                if len(row) >= 6:
                    group_ref = row[0].strip()
                    
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
                            "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                    row_data = row[1:6] if len(row) >= 6 else row[1:] + [''] * (6 - len(row))
                    all_data[group_ref]["w_sheet"] += "\t".join(row_data) + "\n"
    except gspread.WorksheetNotFound:
        st.sidebar.caption("ℹ️ W_Sheet 不存在")
    except Exception as e:
        st.sidebar.error(f"W_Sheet 讀取錯誤：{e}")
    
    # P_Sheet
    try:
        ws = sh.worksheet("P_Sheet")
        rows = ws.get_all_values()
        st.sidebar.caption(f"📊 P_Sheet：讀取 {len(rows)} 行")
        
        if len(rows) > 1:
            for row in rows[1:]:
                if len(row) >= 4:
                    group_ref = row[0].strip()
                    
                    if group_ref in all_data and all_data[group_ref]["mode"] == "B":
                        row_data = row[1:4] if len(row) >= 4 else row[1:] + [''] * (4 - len(row))
                        all_data[group_ref]["p_sheet"] += "\t".join(row_data) + "\n"
                        if "P Sheet" not in all_data[group_ref]["saved_sheets"]:
                            all_data[group_ref]["saved_sheets"].append("P Sheet")
    except gspread.WorksheetNotFound:
        st.sidebar.caption("ℹ️ P_Sheet 不存在")
    except Exception as e:
        st.sidebar.error(f"P_Sheet 讀取錯誤：{e}")
    
    # Grammar_List
    try:
        ws = sh.worksheet("Grammar_List")
        rows = ws.get_all_values()
        st.sidebar.caption(f"📊 Grammar_List：讀取 {len(rows)} 行")
        
        if len(rows) > 1:
            for row in rows[1:]:
                if len(row) >= 5:
                    group_ref = row[0].strip()
                    
                    if group_ref in all_data and all_data[group_ref]["mode"] == "B":
                        row_data = row[1:5] if len(row) >= 5 else row[1:] + [''] * (5 - len(row))
                        all_data[group_ref]["grammar_list"] += "\t".join(row_data) + "\n"
                        if "Grammar List" not in all_data[group_ref]["saved_sheets"]:
                            all_data[group_ref]["saved_sheets"].append("Grammar List")
    except gspread.WorksheetNotFound:
        st.sidebar.caption("ℹ️ Grammar_List 不存在")
    except Exception as e:
        st.sidebar.error(f"Grammar_List 讀取錯誤：{e}")
    
    st.sidebar.success(f"✅ 共載入 {len(all_data)} 筆資料")
    return all_data

# ===================================================================
# 全域工具函式
# ===================================================================
def save_analysis_result(result, input_text):
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []
    st.session_state.analysis_history.append({
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
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
                datetime.date.today().strftime("%Y-%m-%d")
            ]
        })
        stats.to_excel(writer, sheet_name="統計", index=False)
    buffer.seek(0)
    return buffer.getvalue()

# ===================================================================
# Session State 初始化
# ===================================================================
if 'todo' not in st.session_state:
    st.session_state.todo = load_todos()
if 'favorite_sentences' not in st.session_state:
    st.session_state.favorite_sentences = load_favorites()
if 'sel_date' not in st.session_state:
    st.session_state.sel_date = str(datetime.date.today())
if 'cal_key' not in st.session_state:
    st.session_state.cal_key = 0
if 'active_del_id' not in st.session_state:
    st.session_state.active_del_id = None
if 'active_fav_del' not in st.session_state:
    st.session_state.active_fav_del = None
if 'notes' not in st.session_state:
    st.session_state.notes = {}
if 'sentences' not in st.session_state:
    st.session_state.sentences = load_sentences()

# ===================================================================
# 1. 側邊欄（簡化版 + 書桌導航控制）
# ===================================================================
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

    # ===== 書桌導航控制（取代原有的4個連結）=====
    st.markdown("### 📚 書桌控制")
    
    # 字體選擇器
    font_option = st.selectbox(
        "字體樣式",
        ["系統預設", "圓體", "明體", "等寬"],
        index=0,
        key="font_selector"
    )
    
    # 頁碼顯示
    idx = st.session_state.get('tab1_idx', 0)
    st.markdown(f"<div style='text-align: center; padding: 4px 0; color: #666; font-size: 12px;'>"
               f"目前: 第 {idx + 1} 組</div>", unsafe_allow_html=True)
    
    # 導航按鈕
    col1, col2 = st.columns(2)
    with col1:
        st.button(
            "⬅️ 上頁", 
            use_container_width=True, 
            key="prev_btn_sidebar",
            on_click=lambda: setattr(st.session_state, 'tab1_idx', max(0, st.session_state.get('tab1_idx', 0) - 1))
        )
    with col2:
        st.button(
            "下頁 ➡️", 
            use_container_width=True, 
            key="next_btn_sidebar",
            on_click=lambda: setattr(st.session_state, 'tab1_idx', st.session_state.get('tab1_idx', 0) + 1)
        )
    
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

/* TAB1 極致壓縮間距 */
.tab1-font-system { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft JhengHei", "微軟正黑體", sans-serif; }
.tab1-font-rounded { font-family: "PingFang TC", "Hiragino Sans GB", "Microsoft YaHei", "文泉驛正黑", sans-serif; }
.tab1-font-serif { font-family: "Noto Serif CJK TC", "Source Han Serif TC", "Microsoft JhengHei", serif; }
.tab1-font-mono { font-family: "SF Mono", "Monaco", "Inconsolata", "Fira Code", monospace; }

.tab1-content {
    font-size: 14px;
    line-height: 1.0;
    color: #333;
    margin: 0 !important;
    padding: 0 !important;
}

/* 強制白色背景避免手機深色主題 */
.vocab-section {
    background-color: #ffffff !important;
    margin: 0 !important;
    padding: 4px !important;
    border-radius: 4px;
}
.phrase-section {
    background-color: #ffffff !important;
    margin: 0 !important;
    padding: 4px !important;
    border-radius: 4px;
}
.verse-section {
    background-color: #f8f9fa !important;
    margin: 0 !important;
    padding: 6px !important;
    border-radius: 6px;
    border-left: 3px solid #FF8C00;
}

/* 覆蓋Streamlit元素間距 */
div[data-testid="stMarkdownContainer"] > div {
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.0 !important;
}
</style>
""", unsafe_allow_html=True)

# 只定義一次 tabs
tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "🔮 AI解析", "📂 資料庫"])

# ===================================================================
# 3. TAB1 ─ 書桌（AI解析式交互版 - 優化版 v2）
# ===================================================================
with tabs[0]:
    # ========== 初始化 Session State ==========
    if "tab1_selected_ref" not in st.session_state:
        st.session_state.tab1_selected_ref = "來6:3"
    if "tab1_search" not in st.session_state:
        st.session_state.tab1_search = ""
    if "tab1_display_mode" not in st.session_state:
        st.session_state.tab1_display_mode = "en-th"
    if "tab1_ai_loading" not in st.session_state:
        st.session_state.tab1_ai_loading = False
    
    sentences = st.session_state.get('sentences', {})
    
    # ========== 多語言資料庫 ==========
    default_multilang_data = {
        "來6:3": {
            "ref": "Heb 6:3",
            "chinese": "神若許我們、我們必如此行。",
            "english": "And this we will do if God permits.",
            "japanese": "神が許して下さるなら、わたしたちはこのようにします。",
            "korean": "하나님이 허락하시면 우리가 이것을 하리라",
            "thai": "ถ้าพระเจ้าทรงอนุญาต เราก็จะได้เดินหน้าต่อไป",
            "grammar": {
                "english": {
                    "full": "And this we will do if God permits.",
                    "upper": {"title": "上半（When Clause）", "content": "when + God + desired + to show...", "breakdown": "當 + 神 + 想要 + 顯明..."},
                    "lower": {"title": "下半（Main Clause）", "content": "he + guaranteed + it + with an oath", "breakdown": "祂 + 保證 + 這事 + 用 + 起誓"},
                    "points": [
                        {"label": "A", "rule": "when-clause（時間副詞子句）", "pattern": "when + S + V 👉 當…時", "example": "when God speaks", "trans": "當神說話時"},
                        {"label": "B", "rule": "to show（不定詞表目的）", "pattern": "verb + to + V 👉 為了…", "example": "desired to show", "trans": "想要顯明"},
                        {"label": "C", "rule": "with an oath（方式介系詞）", "pattern": "with + N 👉 用…方式", "example": "with an oath", "trans": "用起誓"}
                    ]
                },
                "thai": {
                    "full": "ถ้าพระเจ้าทรงอนุญาต เราก็จะได้เดินหน้าต่อไป",
                    "upper": {"title": "上半句", "content": "ถ้า + พระเจ้า + ทรงอนุญาต", "breakdown": "if + God + permits"},
                    "lower": {"title": "下半句", "content": "เรา + ก็ + จะ + ได้ + เดินหน้า + ต่อไป", "breakdown": "we + then + will + be able to + move forward"},
                    "points": [
                        {"label": "A", "rule": "Clause + จึง + Result", "pattern": "👉 因此，所以", "example": "เหนื่อยมาก จึงไปนอน", "trans": "很累，所以去睡覺"},
                        {"label": "B", "rule": "N＋อัน＋描述詞", "pattern": "👉 which/that", "example": "พระประสงค์อันไม่เปลี่ยนแปลง", "trans": "不改變的旨意"},
                        {"label": "C", "rule": "ทรง（Royal Verb Marker）", "pattern": "พระเจ้า + ทรง + V", "example": "พระเจ้าทรงรัก", "trans": "神愛"}
                    ]
                },
                "japanese": {
                    "full": "神が許して下さるなら、わたしたちはこのようにします。",
                    "upper": {"title": "上半", "content": "約束の相続人たちに...望んで", "breakdown": "promise + heirs + to | desiring"},
                    "lower": {"title": "下半", "content": "誓いによって保証された", "breakdown": "oath + by + guaranteed"},
                    "points": [
                        {"label": "A", "rule": "N1のN2（名詞修飾）", "pattern": "", "example": "約束の相続人", "trans": "應許的繼承人"},
                        {"label": "B", "rule": "こと（名詞化）", "pattern": "V + こと", "example": "変わらないこと", "trans": "不改變這件事"},
                        {"label": "C", "rule": "N＋によって（方式）", "pattern": "", "example": "誓いによって", "trans": "藉著誓言"}
                    ]
                },
                "korean": {
                    "full": "하나님이 허락하시면 우리가 이것을 하리라",
                    "upper": {"title": "上半", "content": "약속의 상속자들에게...나타내시려고", "breakdown": "應許的 + 繼承人 + 對 | 為了顯明"},
                    "lower": {"title": "下半", "content": "맹세로 보증하셨느니라", "breakdown": "藉著 + 起誓 + 保證"},
                    "points": [
                        {"label": "A", "rule": "Verb+려고（目的）", "pattern": "", "example": "나타내시려고", "trans": "為了顯明"},
                        {"label": "B", "rule": "Verb+함（名詞化）", "pattern": "", "example": "변하지 아니함", "trans": "不改變這件事"},
                        {"label": "C", "rule": "N＋로（方式）", "pattern": "N + 로", "example": "맹세로", "trans": "用誓言"}
                    ]
                }
            }
        }
    }
    
    # 資料解析函數
    def parse_verse_data(data):
        multilang_data = {}
        for ref, content_data in data.items():
            v1_content = content_data.get('v1_content', '')
            v2_content = content_data.get('v2_content', '')
            v1_rows, v2_rows = [], []
            if v1_content:
                lines = v1_content.strip().split('\n')
                for line in lines[1:]:
                    if '\t' in line:
                        cols = line.split('\t')
                        if len(cols) >= 3:
                            v1_rows.append({'ref': cols[0], 'english': cols[1], 'chinese': cols[2]})
            if v2_content:
                lines = v2_content.strip().split('\n')
                for line in lines[1:]:
                    if '\t' in line:
                        cols = line.split('\t')
                        if len(cols) >= 7:
                            v2_rows.append({'ref': cols[0], 'japanese': cols[1], 'korean': cols[4], 'thai': cols[6]})
            for i, v1 in enumerate(v1_rows):
                v2 = v2_rows[i] if i < len(v2_rows) else {}
                key = v1.get('ref', ref)
                multilang_data[key] = {
                    'ref': key,
                    'chinese': v1.get('chinese', ''),
                    'english': v1.get('english', ''),
                    'japanese': v2.get('japanese', '') if v2 else '',
                    'korean': v2.get('korean', '') if v2 else '',
                    'thai': v2.get('thai', '') if v2 else '',
                    'grammar': default_multilang_data["來6:3"]['grammar']
                }
        return multilang_data
    
    multilang_db = parse_verse_data(sentences) if sentences else default_multilang_data
    if not multilang_db:
        multilang_db = default_multilang_data
    
    # 決定顯示經文
    if st.session_state.tab1_selected_ref in multilang_db:
        current = multilang_db[st.session_state.tab1_selected_ref]
    else:
        current = list(multilang_db.values())[0]
    
        # ========== 隱藏魔菇按鈕邊框 + 垂直置中對齊的 CSS ==========
    st.markdown("""
        <style>
        div[data-testid="stElementContainer"].st-key-mushroom_ai_btn {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            height: 100% !important;
        }
        div[data-testid="stElementContainer"].st-key-mushroom_ai_btn button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0px !important;
            font-size: 28px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # ========== 控制列：搜索框(縮小) + 魔菇 + 語言切換按鈕 ==========
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    # 欄位比例：1.2(搜索-縮小) | 0.5(魔菇) | 1(英泰) | 1(日韓)
    control_cols = st.columns([1.2, 0.5, 1, 1])
    
    with control_cols[0]:
        search_val = st.text_input(
            "",
            value=st.session_state.tab1_search,
            placeholder="例：來6:3",
            label_visibility="collapsed",
            key="verse_search_compact"
        )
        if search_val:
            st.session_state.tab1_search = search_val
            for key in multilang_db.keys():
                if search_val.lower() in key.lower():
                    st.session_state.tab1_selected_ref = key
                    st.rerun()
    
    with control_cols[1]:
        mushroom_clicked = st.button("🍄", key="mushroom_ai_btn", help="AI解析經文")
        if mushroom_clicked:
            st.session_state.tab1_ai_loading = True
            st.rerun()
    
    with control_cols[2]:
        btn_style_en_th = "primary" if st.session_state.tab1_display_mode == "en-th" else "secondary"
        if st.button("🇬🇧🇹🇭", use_container_width=True, type=btn_style_en_th):
            st.session_state.tab1_display_mode = "en-th"
            st.rerun()
    
    with control_cols[3]:
        btn_style_jp_kr = "primary" if st.session_state.tab1_display_mode == "jp-kr" else "secondary"
        if st.button("🇯🇵🇰🇷", use_container_width=True, type=btn_style_jp_kr):
            st.session_state.tab1_display_mode = "jp-kr"
            st.rerun()
    
    # ========== AI 解析處理（呼叫全域函數）==========
    if st.session_state.get('tab1_ai_loading', False):
        with st.spinner("🍄 魔菇AI正在解析經文..."):
            # 這裡會呼叫上面定義好的函數
            # 請確認 'current' 是你當前經文的變數名稱
            run_bible_ai_analysis(current)
    
        # 解析結束，關閉狀態並立即刷新畫面
        st.session_state.tab1_ai_loading = False
        st.rerun()
    
       # ========== AI 解析處理（動態即時解析版 - 修正後）==========
    if st.session_state.get('tab1_ai_loading', False):
        with st.spinner("🍄 魔菇AI正在動態解析「" + current['ref'] + "」..."):
            try:
                # 1. 取得 API Key (沿用 TAB4 的設定)
                api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("gemini", {}).get("api_key")
                genai.configure(api_key=api_key)
                
                # 2. 初始化模型 (動態選擇 flash 模型)
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                target_model_name = next((m for m in available_models if "flash" in m), available_models[0])
                model = genai.GenerativeModel(target_model_name)

                # 3. 針對 TAB1 設計的 Prompt
                tab1_prompt = f"""
                Analyze this Bible verse: "{current['ref']} {current['english']}" 
                and its Chinese version: "{current['chinese']}".
                Return a JSON object exactly with these keys: 
                'vocabulary' (list of {{word, phonetic, meaning}}), 
                'phrases' (list of {{phrase, meaning}}), 
                'segments' (list of {{en, cn}}).
                Language: Traditional Chinese explanations.
                """
                
                response = model.generate_content(tab1_prompt)
                response_text = response.text.strip()
                
                # 4. 提取 JSON (直接複製 TAB4 成功的邏輯)
                json_data = None
                
                # 方法 1: 嘗試從 markdown 代碼塊中提取
                json_match = re.search(r'```(?:json)?\s*\n?(\{.*?\})\s*\n?```', response_text, re.DOTALL)
                if json_match:
                    try:
                        json_data = json.loads(json_match.group(1))
                    except:
                        pass
                
                # 方法 2: 直接尋找 JSON 物件（從第一個 {{ 到最後一個 }}）
                if not json_data:
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}')
                    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                        try:
                            json_str = response_text[start_idx:end_idx+1]
                            json_data = json.loads(json_str)
                        except:
                            pass
                
                # 方法 3: 使用非貪婪正則匹配 (備援)
                if not json_data:
                    json_match = re.search(r'\{[\s\S]*?"segments"\s*:\s*\[[\s\S]*?\]\s*\}', response_text, re.DOTALL)
                    if json_match:
                        try:
                            json_data = json.loads(json_match.group(0))
                        except:
                            pass
                
                if json_data:
                    st.session_state.tab1_ai_result = json_data
                else:
                    st.error("❌ 無法從 AI 回應中提取 JSON 格式資料")
                    st.text(response_text)
                    
            except Exception as e:
                st.error(f"❌ AI 解析失敗: {str(e)}")
        
        # 解析結束，關閉狀態並立即刷新畫面
        st.session_state.tab1_ai_loading = False
        st.rerun()
    
    # ========== 經文標題 ==========
    ref_short = current['ref'].replace(" ", "")
    st.markdown(f"<h3 style='font-size: 22px; font-weight: bold; color: #333; margin: 10px 0;'>{ref_short}{current['chinese']}</h3>", unsafe_allow_html=True)
    
    # ========== 左右並排顯示雙語 ==========
    if st.session_state.tab1_display_mode == "en-th":
        col_left, col_right = st.columns(2)
        
        # 🇬🇧 英文（左）
        with col_left:
            eng = current['grammar']['english']
            st.markdown(f"<div style='font-size: 17px; margin-bottom: 12px;'>🇬🇧 {eng['full']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background: #f0f7ff; padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #4299e1;'><div style='font-weight: bold; color: #2b6cb0; font-size: 13px;'>{eng['upper']['title']}</div><div style='font-size: 13px;'>{eng['upper']['content']}</div><div style='font-size: 11px; color: #666;'>{eng['upper']['breakdown']}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background: #f0fff4; padding: 10px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #48bb78;'><div style='font-weight: bold; color: #276749; font-size: 13px;'>{eng['lower']['title']}</div><div style='font-size: 13px;'>{eng['lower']['content']}</div><div style='font-size: 11px; color: #666;'>{eng['lower']['breakdown']}</div></div>", unsafe_allow_html=True)
            st.markdown("<div style='font-weight: bold; font-size: 13px; margin: 8px 0;'>重點文法：</div>", unsafe_allow_html=True)
            for p in eng['points']:
                st.markdown(f"<div style='margin-bottom: 6px; padding: 6px; background: #fff; border-radius: 4px; border: 1px solid #e2e8f0; font-size: 12px;'><span style='color: #d69e2e; font-weight: bold;'>{p['label']})</span> {p['rule']}<br><span style='color: #666;'>{p['pattern']}</span><br>Ex: {p['example']} {p['trans']}</div>", unsafe_allow_html=True)
        
        # 🇹🇭 泰文（右）
        with col_right:
            th = current['grammar']['thai']
            st.markdown(f"<div style='font-size: 17px; margin-bottom: 12px;'>🇹🇭 {th['full']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background: #fffaf0; padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #ed8936;'><div style='font-weight: bold; color: #c05621; font-size: 13px;'>{th['upper']['title']}</div><div style='font-size: 13px;'>{th['upper']['content']}</div><div style='font-size: 11px; color: #666;'>{th['upper']['breakdown']}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background: #fffaf0; padding: 10px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #38a169;'><div style='font-weight: bold; color: #276749; font-size: 13px;'>{th['lower']['title']}</div><div style='font-size: 13px;'>{th['lower']['content']}</div><div style='font-size: 11px; color: #666;'>{th['lower']['breakdown']}</div></div>", unsafe_allow_html=True)
            st.markdown("<div style='font-weight: bold; font-size: 13px; margin: 8px 0;'>重要文法：</div>", unsafe_allow_html=True)
            for p in th['points']:
                st.markdown(f"<div style='margin-bottom: 6px; padding: 6px; background: #fff; border-radius: 4px; border: 1px solid #e2e8f0; font-size: 12px;'><span style='color: #d69e2e; font-weight: bold;'>{p['label']})</span> {p['rule']}<br><span style='color: #666;'>{p['pattern']}</span><br>Ex: {p['example']} 👉 {p['trans']}</div>", unsafe_allow_html=True)
    
    else:  # jp-kr 模式
        col_left, col_right = st.columns(2)
        
        # 🇯🇵 日文（左）
        with col_left:
            jp = current['grammar']['japanese']
            st.markdown(f"<div style='font-size: 17px; margin-bottom: 12px;'>🇯🇵 {jp['full']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background: #fef2f2; padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #e53e3e;'><div style='font-weight: bold; color: #c53030; font-size: 13px;'>{jp['upper']['title']}</div><div style='font-size: 13px;'>{jp['upper']['content']}</div><div style='font-size: 11px; color: #666;'>{jp['upper']['breakdown']}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background: #fef2f2; padding: 10px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #38a169;'><div style='font-weight: bold; color: #276749; font-size: 13px;'>{jp['lower']['title']}</div><div style='font-size: 13px;'>{jp['lower']['content']}</div><div style='font-size: 11px; color: #666;'>{jp['lower']['breakdown']}</div></div>", unsafe_allow_html=True)
            st.markdown("<div style='font-weight: bold; font-size: 13px; margin: 8px 0;'>文法解說：</div>", unsafe_allow_html=True)
            for p in jp['points']:
                pat = f"<br><span style='color: #666;'>{p['pattern']}</span>" if p['pattern'] else ""
                st.markdown(f"<div style='margin-bottom: 6px; padding: 6px; background: #fff; border-radius: 4px; border: 1px solid #e2e8f0; font-size: 12px;'><span style='color: #d69e2e; font-weight: bold;'>{p['label']})</span> {p['rule']}{pat}<br>Ex: {p['example']} {p['trans']}</div>", unsafe_allow_html=True)
        
        # 🇰🇷 韓文（右）
        with col_right:
            kr = current['grammar']['korean']
            st.markdown(f"<div style='font-size: 17px; margin-bottom: 12px;'>🇰🇷 {kr['full']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background: #f0fff4; padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #48bb78;'><div style='font-weight: bold; color: #276749; font-size: 13px;'>{kr['upper']['title']}</div><div style='font-size: 13px;'>{kr['upper']['content']}</div><div style='font-size: 11px; color: #666;'>{kr['upper']['breakdown']}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background: #f0fff4; padding: 10px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #ed8936;'><div style='font-weight: bold; color: #c05621; font-size: 13px;'>{kr['lower']['title']}</div><div style='font-size: 13px;'>{kr['lower']['content']}</div><div style='font-size: 11px; color: #666;'>{kr['lower']['breakdown']}</div></div>", unsafe_allow_html=True)
            st.markdown("<div style='font-weight: bold; font-size: 13px; margin: 8px 0;'>重要文法解說：</div>", unsafe_allow_html=True)
            for p in kr['points']:
                pat = f"<br><span style='color: #666;'>{p['pattern']}</span>" if p['pattern'] else ""
                st.markdown(f"<div style='margin-bottom: 6px; padding: 6px; background: #fff; border-radius: 4px; border: 1px solid #e2e8f0; font-size: 12px;'><span style='color: #d69e2e; font-weight: bold;'>{p['label']})</span> {p['rule']}{pat}<br>Ex: {p['example']} {p['trans']}</div>", unsafe_allow_html=True)

# ===================================================================
# 4. TAB2 ─ 月曆待辦 + 7句手動金句 + 我的收藏（無預設金句版）
# ===================================================================
with tabs[1]:
    # CSS - 修正月曆底部顯示問題
    st.markdown("""
        <style>
        div[data-testid="stVerticalBlock"] > div {padding: 0px !important; margin: 0px !important;}
        p {margin: 0px !important; padding: 0px !important; line-height: 1.2 !important;}
        .stButton button {padding: 0px 4px !important; min-height: 24px !important; font-size: 12px !important;}
        hr {margin: 2px 0 !important;}
        div[data-testid="stExpander"] {margin: 2px 0 !important;}
        /* 修正月曆顯示 - 不要裁切底部 */
        .fc {margin-bottom: 0 !important;}
        .fc-scroller {overflow: visible !important; height: auto !important;}
        .fc-view-harness {height: auto !important;}
        iframe {height: 500px !important; min-height: 450px !important;}
        /* 經文樣式 - 緊密排版 */
        .verse-line {display: block; margin: 2px 0 !important; padding: 0 !important; line-height: 1.4 !important;}
        .verse-ref {font-weight: bold; color: #333; font-size: 14px;}
        .verse-en {font-size: 13px; color: #666;}
        .verse-cn {font-size: 14px; color: #000; font-weight: 500;}
        </style>
    """, unsafe_allow_html=True)

    # Session State
    if "todo" not in st.session_state:
        st.session_state.todo = load_todos()
    if "favorite_sentences" not in st.session_state:
        st.session_state.favorite_sentences = load_favorites()
    if "custom_verses" not in st.session_state:
        st.session_state.custom_verses = load_custom_verses()
    if "sel_date" not in st.session_state:
        st.session_state.sel_date = str(datetime.date.today())
    if "cal_key" not in st.session_state:
        st.session_state.cal_key = 0
    if "verse_start_idx" not in st.session_state:
        st.session_state.verse_start_idx = 0

    # ---------- 月曆（點擊日期顯示當天待辦）----------
    def build_events():
        ev = []
        for d, items in st.session_state.todo.items():
            if isinstance(items, list):
                for idx, t in enumerate(items):
                    title = t.get("title", "")
                    display_title = title[:5] + "..." if len(title) > 5 else title
                    ev.append({
                        "id": f"{d}_{idx}",
                        "title": display_title,
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
            "height": "450px",  # 固定高度避免裁切
            "eventDisplay": "block",
            "dayMaxEvents": 3,
            "eventMinHeight": 20
        }

        state = calendar(
            events=build_events(), 
            options=cal_options, 
            key=f"cal_{st.session_state.cal_key}"
        )

        # 點擊日期 → 顯示當天待辦面板
        if state.get("dateClick"):
            clicked_date = state["dateClick"]["date"][:10]
            st.session_state.sel_date = clicked_date
            # 強制重新渲染面板
            st.session_state.cal_key += 1
            st.rerun()

    # ---------- 當天待辦事項面板（簡化穩定版）----------
    selected_date = st.session_state.sel_date
    
    # 使用 container 建立明確的視覺區塊
    todo_container = st.container()
    
    with todo_container:
        # 標題列
        header_col1, header_col2 = st.columns([6, 1])
        with header_col1:
            st.markdown(f'<p style="font-size:14px;font-weight:bold; margin:10px 0 5px 0;">'
                       f'📋 {selected_date} 待辦事項</p>', 
                       unsafe_allow_html=True)
        
        # 顯示當天所有待辦
        has_todos = (selected_date in st.session_state.todo and 
                    st.session_state.todo[selected_date])
        
        if has_todos:
            for idx, item in enumerate(st.session_state.todo[selected_date]):
                item_id = f"{selected_date}_{idx}"
                title = item.get("title", "") if isinstance(item, dict) else str(item)
                time_str = item.get('time', '')[:5] if isinstance(item, dict) and item.get('time') else ""
                
                # 每個待辦一行：收藏 | 刪除 | 內容
                c1, c2, c3 = st.columns([0.8, 0.8, 8])
                
                with c1:
                    if st.button("⭐", key=f"fav_{item_id}"):
                        fav_text = f"{selected_date} {time_str} {title}"
                        if fav_text not in st.session_state.favorite_sentences:
                            st.session_state.favorite_sentences.append(fav_text)
                            save_favorites()
                            st.toast("已加入收藏！")
                
                with c2:
                    # 刪除按鈕 - 直接刪除無確認
                    if st.button("🗑️", key=f"del_{item_id}"):
                        st.session_state.todo[selected_date].pop(idx)
                        if not st.session_state.todo[selected_date]:
                            del st.session_state.todo[selected_date]
                        save_todos()
                        st.session_state.cal_key += 1
                        st.rerun()
                
                with c3:
                    display_text = f"{time_str} {title}" if time_str else title
                    st.markdown(f'<p style="line-height:1.4;font-size:13px; margin:5px 0;">'
                               f'{display_text}</p>', 
                               unsafe_allow_html=True)
        else:
            st.caption(f"{selected_date} 無待辦事項")
        
        st.markdown('<hr style="margin:10px 0;">', unsafe_allow_html=True)

    # ---------- 長內容待辦事項（獨立顯示，超過5字）----------
    st.markdown('<p style="font-size:14px;font-weight:bold; margin:10px 0 5px 0;">'
               '📋 所有長內容待辦（5字以上）</p>', 
               unsafe_allow_html=True)

    long_todos_all = []
    for date_str, items in st.session_state.todo.items():
        if isinstance(items, list):
            for idx, item in enumerate(items):
                title = item.get("title", "") if isinstance(item, dict) else str(item)
                if len(title) > 5:
                    long_todos_all.append((date_str, idx, item, title))

    if long_todos_all:
        long_todos_all.sort(key=lambda x: x[0])
        for date_str, idx, item, title in long_todos_all[:10]:
            item_id = f"{date_str}_{idx}"
            time_str = item.get('time', '')[:5] if isinstance(item, dict) and item.get('time') else ""
            
            c1, c2, c3 = st.columns([0.8, 0.8, 8])
            
            with c1:
                if st.button("⭐", key=f"fav_long_{item_id}"):
                    fav_text = f"{date_str} {time_str} {title}"
                    if fav_text not in st.session_state.favorite_sentences:
                        st.session_state.favorite_sentences.append(fav_text)
                        save_favorites()
                        st.toast("已加入收藏！")
            
            with c2:
                if st.button("🗑️", key=f"del_long_{item_id}"):
                    st.session_state.todo[date_str].pop(idx)
                    if not st.session_state.todo[date_str]:
                        del st.session_state.todo[date_str]
                    save_todos()
                    st.session_state.cal_key += 1
                    st.rerun()
            
            with c3:
                display_text = f"{date_str} {time_str} {title}"
                st.markdown(f'<p style="line-height:1.4;font-size:13px; margin:5px 0;">'
                           f'{display_text}</p>', 
                           unsafe_allow_html=True)
    else:
        st.caption("無長內容待辦（5字以上才顯示）")

    # 新增待辦
    with st.expander("➕ 新增待辦", expanded=False):
        with st.form("todo_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                try:
                    default_date = datetime.datetime.strptime(selected_date, "%Y-%m-%d").date()
                except:
                    default_date = datetime.date.today()
                in_date = st.date_input("日期", default_date)
            with c2:
                in_time = st.time_input("時間", datetime.time(9, 0))
            in_title = st.text_input("待辦事項")

            if st.form_submit_button("💾 儲存"):
                if in_title:
                    k = str(in_date)
                    if k not in st.session_state.todo:
                        st.session_state.todo[k] = []
                    st.session_state.todo[k].append({"title": in_title, "time": str(in_time)})
                    save_todos()
                    st.session_state.cal_key += 1
                    st.session_state.sel_date = k
                    st.rerun()

    st.markdown('<hr style="margin:10px 0;">', unsafe_allow_html=True)

    # ---------- 8句 Google Sheet 經文（排版修正：經節與經文緊密連接）----------
    st.markdown('<p style="font-size:14px;font-weight:bold; margin:10px 0 5px 0;">'
               '📖 經文金句（Google Sheet）</p>', 
               unsafe_allow_html=True)

    sentences = st.session_state.get('sentences', {})
    sheet_verses = []

    for ref, data in sentences.items():
        v1_content = data.get('v1_content', '') or ''
        if not v1_content:
            continue
        try:
            lines = v1_content.strip().split('\n')
            if len(lines) < 2:
                continue
            headers = [h.strip() for h in lines[0].split('\t')]
            for line in lines[1:]:
                if not line.strip():
                    continue
                cells = [c.strip() for c in line.split('\t')]
                while len(cells) < len(headers):
                    cells.append('')
                row = {headers[i]: cells[i] for i in range(len(headers))}
                verse_ref = row.get('Ref.', row.get('Ref. 經文出處', ref))
                en = row.get('English（ESV經文）', row.get('English (ESV)', ''))
                cn = row.get('Chinese經文', row.get('Chinese', ''))
                if en and cn:
                    sheet_verses.append({'ref': verse_ref, 'en': en, 'cn': cn})
        except:
            pass

    sheet_verses = sheet_verses[:8]

    if len(sheet_verses) >= 2:
        if 'sheet_verse_idx' not in st.session_state:
            st.session_state.sheet_verse_idx = 0

        total_pairs = len(sheet_verses) // 2
        idx = st.session_state.sheet_verse_idx % total_pairs * 2

        v1, v2 = sheet_verses[idx], sheet_verses[idx+1] if idx+1 < len(sheet_verses) else None

        # ✅ 第一節：經節與經文緊密連接，無多餘換行
        col1, col2, col3 = st.columns([0.5, 6, 0.5])
        with col1:
            if st.button("《", key="sheet_prev"):
                st.session_state.sheet_verse_idx = (st.session_state.sheet_verse_idx - 1) % total_pairs
                st.rerun()
        with col2:
            # ✅ 修正：使用 <span> 讓所有內容緊密連接
            st.markdown(f"""
            <div style="border:1px solid #ddd; border-radius:8px; padding:10px; margin:4px 0;">
                <span class="verse-ref">📖 {v1['ref']}</span><br>
                <span class="verse-en">🇬🇧 {v1['en']}</span><br>
                <span class="verse-cn">🇨🇳 {v1['cn']}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⭐ 收藏", key=f"fav_s1_{idx}"):
                fav = f"{v1['ref']} {v1['en']}"
                if fav not in st.session_state.favorite_sentences:
                    st.session_state.favorite_sentences.append(fav)
                    save_favorites()
                    st.toast("已收藏！")
        with col3:
            if st.button("》", key="sheet_next"):
                st.session_state.sheet_verse_idx = (st.session_state.sheet_verse_idx + 1) % total_pairs
                st.rerun()

        # 第二節
        if v2:
            col1, col2, col3 = st.columns([0.5, 6, 0.5])
            with col1:
                st.empty()
            with col2:
                st.markdown(f"""
                <div style="border:1px solid #ddd; border-radius:8px; padding:10px; margin:4px 0;">
                    <span class="verse-ref">📖 {v2['ref']}</span><br>
                    <span class="verse-en">🇬🇧 {v2['en']}</span><br>
                    <span class="verse-cn">🇨🇳 {v2['cn']}</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button("⭐ 收藏", key=f"fav_s2_{idx}"):
                    fav = f"{v2['ref']} {v2['en']}"
                    if fav not in st.session_state.favorite_sentences:
                        st.session_state.favorite_sentences.append(fav)
                        save_favorites()
                        st.toast("已收藏！")
            with col3:
                st.empty()
    else:
        st.caption("經文資料不足2節")

    st.markdown('<hr style="margin:10px 0;">', unsafe_allow_html=True)

    # ---------- 7句自訂金句（同樣排版修正）----------
    st.markdown('<p style="font-size:14px;font-weight:bold; margin:10px 0 5px 0;">'
               '✏️ 我的自訂金句</p>', 
               unsafe_allow_html=True)

    custom_list = [(i, v) for i, v in enumerate(st.session_state.custom_verses) if v.strip()]

    if len(custom_list) >= 2:
        if 'custom_verse_idx' not in st.session_state:
            st.session_state.custom_verse_idx = 0

        total_pairs = (len(custom_list) + 1) // 2
        pair_idx = st.session_state.custom_verse_idx % total_pairs

        start = pair_idx * 2
        c1_data = custom_list[start]
        c2_data = custom_list[start + 1] if start + 1 < len(custom_list) else None

        col1, col2, col3 = st.columns([0.5, 6, 0.5])
        with col1:
            if st.button("《", key="custom_prev"):
                st.session_state.custom_verse_idx = (st.session_state.custom_verse_idx - 1) % total_pairs
                st.rerun()
        with col2:
            st.markdown(f"""
            <div style="border:1px solid #ddd; border-radius:8px; padding:10px; margin:4px 0; background:#f9f9f9;">
                <span style="font-weight:bold; color:#333; font-size:14px;">💎 金句 {c1_data[0]+1}</span><br>
                <span style="font-size:14px; color:#000; font-weight:500;">{c1_data[1]}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⭐ 收藏", key=f"fav_c1_{start}"):
                if c1_data[1] not in st.session_state.favorite_sentences:
                    st.session_state.favorite_sentences.append(c1_data[1])
                    save_favorites()
                    st.toast("已收藏！")
        with col3:
            if st.button("》", key="custom_next"):
                st.session_state.custom_verse_idx = (st.session_state.custom_verse_idx + 1) % total_pairs
                st.rerun()

        if c2_data:
            col1, col2, col3 = st.columns([0.5, 6, 0.5])
            with col1:
                st.empty()
            with col2:
                st.markdown(f"""
                <div style="border:1px solid #ddd; border-radius:8px; padding:10px; margin:4px 0; background:#f9f9f9;">
                    <span style="font-weight:bold; color:#333; font-size:14px;">💎 金句 {c2_data[0]+1}</span><br>
                    <span style="font-size:14px; color:#000; font-weight:500;">{c2_data[1]}</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button("⭐ 收藏", key=f"fav_c2_{start}"):
                    if c2_data[1] not in st.session_state.favorite_sentences:
                        st.session_state.favorite_sentences.append(c2_data[1])
                        save_favorites()
                        st.toast("已收藏！")
            with col3:
                st.empty()
    else:
        st.caption("請在下方新增至少2句自訂金句")

    # 編輯區
    with st.expander("✏️ 編輯7句金句", expanded=False):
        for i in range(7):
            st.text_input(f"金句 {i+1}", 
                         value=st.session_state.custom_verses[i], 
                         key=f"custom_{i}")
        if st.button("💾 儲存", key="save_custom"):
            updated = [st.session_state[f"custom_{i}"] for i in range(7)]
            st.session_state.custom_verses = updated
            save_custom_verses(updated)
            st.success("已儲存！")
            st.rerun()

    # ---------- 我的收藏（獨立區塊）----------
    st.markdown('<p style="font-size:14px;font-weight:bold; margin:10px 0 5px 0;">'
               '❤️ 我的收藏</p>', 
               unsafe_allow_html=True)

    if st.session_state.favorite_sentences:
        for i, fav in enumerate(st.session_state.favorite_sentences):
            c1, c2 = st.columns([8, 1.5])
            with c1:
                st.markdown(f'<p style="line-height:1.4;font-size:13px; margin:3px 0;">• {fav}</p>', 
                           unsafe_allow_html=True)
            with c2:
                if st.button("🗑️", key=f"del_fav_{i}"):
                    st.session_state.favorite_sentences.pop(i)
                    save_favorites()
                    st.rerun()
    else:
        st.caption("尚無收藏，點擊待辦事項的 ⭐ 加入")

# ===================================================================
# 5. TAB3 ─ 挑戰（輸入框改為單行）
# ===================================================================
with tabs[2]:

    if 'tab3_seed' not in st.session_state:
        st.session_state.tab3_seed = random.randint(1, 1000)

    sentences = st.session_state.get('sentences', {})

    if not sentences:
        st.warning("資料庫為空")
    else:
        sorted_refs = sorted(sentences.keys(), key=lambda x: sentences[x].get('date_added', ''), reverse=True)
        total = len(sorted_refs)

        new_refs = sorted_refs[:int(total*0.6)] if total >= 5 else sorted_refs
        mid_refs = sorted_refs[int(total*0.6):int(total*0.9)] if total >= 10 else []
        old_refs = sorted_refs[int(total*0.9):] if total >= 10 else []
        weighted_pool = (new_refs * 6) + (mid_refs * 3) + (old_refs * 1)
        if not weighted_pool:
            weighted_pool = sorted_refs

        random.seed(st.session_state.tab3_seed)

        all_verses = []
        for ref in weighted_pool[:15]:
            data = sentences[ref]
            v1 = data.get('v1_content', '')
            if v1:
                try:
                    lines = v1.strip().split('\n')
                    if lines:
                        reader = csv.DictReader(lines, delimiter='\t')
                        for row in reader:
                            all_verses.append({
                                'ref': row.get('Ref. 經文出處', row.get('Ref.', '')),
                                'en': row.get('English（ESV經文）', row.get('English (ESV)', '')),
                                'cn': row.get('Chinese經文', row.get('Chinese', ''))
                            })
                except:
                    pass

        if len(all_verses) < 6:
            st.warning("經文資料不足")
        else:
            selected = random.sample(all_verses, 6)
            zh_to_en = selected[:3]
            en_to_zh = selected[3:6]

            # ✅ 修正：改用 text_input（單行），高度自然縮小
            for i, q in enumerate(zh_to_en, 1):
                with st.expander(f"🇨🇳 {q['cn']}", expanded=False):
                    st.markdown(f"**🇬🇧 {q['en']}**")
                    st.caption(f"📖 {q['ref']}")
                
                # ✅ 改用單行輸入框
                user_answer = st.text_input(
                    "",
                    key=f"q_{i}_{st.session_state.tab3_seed}",
                    placeholder="請輸入英文翻譯...",
                    label_visibility="collapsed"
                )

                st.markdown("---")

            for i, q in enumerate(en_to_zh, 4):
                with st.expander(f"🇬🇧 {q['en']}", expanded=False):
                    st.markdown(f"**🇨🇳 {q['cn']}**")
                    st.caption(f"📖 {q['ref']}")
                
                # ✅ 改用單行輸入框
                user_answer = st.text_input(
                    "",
                    key=f"q_{i}_{st.session_state.tab3_seed}",
                    placeholder="請輸入中文翻譯...",
                    label_visibility="collapsed"
                )

                st.markdown("---")

            if st.button("🔄 換一批題目", use_container_width=True, type="primary"):
                st.session_state.tab3_seed = random.randint(1, 1000)
                st.rerun()
        
# ===================================================================
# TAB 4: AI 智慧學習 (純英對話與 UI 緊湊化優化)
# ===================================================================
with tabs[3]:
    # 1. & 2. 頂部輸入區 (高度對齊優化)
    c1, c2 = st.columns([1, 3])
    with c1:
        # 使用 CSS 調整按鈕高度與輸入欄一致
        st.markdown("""
            <style>
            div[data-testid="stButton"] > button {
                height: 36px !important;
                min-height: 36px !important;
                padding: 0px 16px !important;
            }
            </style>
        """, unsafe_allow_html=True)
        generate_all = st.button("✨ 生成內容", key="tab4_gen_btn", use_container_width=True)
    with c2:
        verse_input = st.text_input("輸入經文 (ESV/和合本)", key="tab4_input", placeholder="例如: Ephesians 1:3", label_visibility="collapsed")

    # 初始化狀態
    if "tab4_data" not in st.session_state: st.session_state.tab4_data = {"cards": [], "script": []}
    if "card_idx" not in st.session_state: st.session_state.card_idx = 0
    if "flipped" not in st.session_state: st.session_state.flipped = False

    # AI 生成邏輯
    if generate_all and verse_input:
        with st.spinner("AI 正在深度解析並編寫純英對話..."):
            try:
                api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("gemini", {}).get("api_key")
                genai.configure(api_key=api_key)
                
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                target_model_name = next((m for m in available_models if "flash" in m), available_models[0])
                model = genai.GenerativeModel(target_model_name)

                # 強化 Prompt：強調純英文、階梯記憶格式
                full_prompt = f"""
                Analyze "{verse_input}". Versions: English-ESV, Chinese-CUV (和合本).
                Return ONE JSON object with 'cards' and 'script'.
                
                [Flashcard Format - 必須依以下規則產生]
                每一句經文必須拆解為以下四個層級，依句子長度決定產生多少張卡：
                
                1. 單字卡 (WORD):
                   - 選擇 2-4 個重要單字
                   Front: "正面：[中文詞義]\\n例：[中文例句片段]"
                   Back: "反面：[Eng Word]\\n例：[Eng例句片段]"
                   
                2. 片語卡 (PHRASE):
                   - 選擇 2-3 個重要片語
                   Front: "正面：[Eng Phrase]\\n例：[Eng snippet]"
                   Back: "反面：[中文片語]\\n例：[中文snippet]"
                   
                3. 段句卡 (SEGMENT):
                   - 將經文分成 2-4 個語意段落
                   Front: "正面：[中文段落]"
                   Back: "反面：[Eng段落]"
                   
                4. 整句卡 (FULL):
                   - 1 張完整經文卡
                   Front: "正面：[中文全句]"
                   Back: "反面：[Eng全句]"
                
                [Podcast Rules - 100% 純英文對話]
                - 兩位主持人 Rachel (女性) 和 Mike (男性) 的對話
                - 對話必須 100% 使用英文，絕對不能出現中文
                - 內容：討論經文的意義、神學背景、實際應用
                - 語氣：輕鬆、教育性、像朋友聊天
                - 長度：約 600-800 字的詳細對話
                - 格式：每句話包含 "speaker" (Rachel/Mike) 和 "text" (純英文內容)
                
                JSON 格式:
                {{
                    "cards": [
                        {{"type": "WORD", "front": "...", "back": "..."}},
                        {{"type": "PHRASE", "front": "...", "back": "..."}},
                        {{"type": "SEGMENT", "front": "...", "back": "..."}},
                        {{"type": "FULL", "front": "...", "back": "..."}}
                    ],
                    "script": [
                        {{"speaker": "Rachel", "text": "..."}},
                        {{"speaker": "Mike", "text": "..."}}
                    ]
                }}
                """
                
                response = model.generate_content(full_prompt)
                response_text = response.text.strip()
                
                # 修正：多種方式嘗試提取 JSON
                json_data = None
                
                # 方法 1: 嘗試從 markdown 代碼塊中提取
                json_match = re.search(r'```(?:json)?\\s*\\n?(\\{.*?\\})\\s*\\n?```', response_text, re.DOTALL)
                if json_match:
                    try:
                        json_data = json.loads(json_match.group(1))
                    except:
                        pass
                
                # 方法 2: 直接尋找 JSON 物件（從第一個 { 到最後一個 }）
                if not json_data:
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}')
                    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                        try:
                            json_str = response_text[start_idx:end_idx+1]
                            json_data = json.loads(json_str)
                        except:
                            pass
                
                # 方法 3: 使用非貪婪正則匹配
                if not json_data:
                    json_match = re.search(r'\\{[\\s\\S]*?\"script\"\\s*:\\s*\\[[\\s\\S]*?\\]\\s*\\}', response_text, re.DOTALL)
                    if json_match:
                        try:
                            json_data = json.loads(json_match.group(0))
                        except:
                            pass
                
                if json_data:
                    st.session_state.tab4_data = json_data
                    st.session_state.card_idx = 0
                    st.session_state.flipped = False
                    st.rerun()
                else:
                    st.error("❌ 無法從 AI 回應中提取 JSON 格式資料")
                    st.text(response_text)

            except Exception as e:
                st.error(f"❌ 生成失敗: {str(e)}")

    # 3. 顯示區
    data = st.session_state.tab4_data
    if data.get("cards"):
        sub_tab1, sub_tab2 = st.tabs(["🗂️ 階梯式閃卡", "🎧 雙人對話"])
        
        with sub_tab1:
            cards = data["cards"]
            idx = st.session_state.card_idx
            card = cards[idx] if idx < len(cards) else cards[0]
            
            c_left, c_right = st.columns([2, 1])
            with c_left:
                st.caption(f"📍 {card.get('type', 'Learn')} | 📊 {idx + 1} / {len(cards)}")
                val = card.get("back", "") if st.session_state.flipped else card.get("front", "")
                st.markdown(f"""
                    <div style="height:180px; background:#fcfcfc; border:2px solid #333; border-radius:10px; 
                                display:flex; align-items:center; justify-content:center; text-align:center; padding:15px; 
                                font-size:18px; line-height:1.6; color:#1a1a1a; overflow-y:auto; white-space:pre-line;">
                        {str(val).replace(chr(10), '<br>')}
                    </div>
                """, unsafe_allow_html=True)

            with c_right:
                st.write("") 
                if st.button("⬅️ 上一頁", use_container_width=True):
                    st.session_state.card_idx = (idx - 1) % len(cards); st.session_state.flipped = False; st.rerun()
                if st.button("🔄 翻轉", use_container_width=True, type="primary"):
                    st.session_state.flipped = not st.session_state.flipped; st.rerun()
                if st.button("➡️ 下一頁", use_container_width=True):
                    st.session_state.card_idx = (idx + 1) % len(cards); st.session_state.flipped = False; st.rerun()
                if st.button("🔊 語音", use_container_width=True):
                    speech_text = str(val)
                    eng_only = re.sub(r'[\u4e00-\u9fa5]+', '', speech_text).replace('正面：', '').replace('反面：', '').replace('例：', '')
                    play_audio_html(eng_only)

        with sub_tab2:
            # CSS 注入：美化對話框、加大字體、縮減間距
            st.markdown("""
                <style>
                /* 整體對話容器 */
                [data-testid="stChatMessage"] { 
                    padding: 0.3rem 0.8rem !important; 
                    margin-bottom: -0.5rem !important; 
                }
                /* 對話內容字體加大 */
                [data-testid="stChatMessageContent"] p { 
                    font-size: 17px !important; 
                    line-height: 1.5 !important; 
                    margin-bottom: 0.3rem !important;
                }
                /* 對話氣泡美化 */
                [data-testid="stChatMessage"] > div {
                    border-radius: 12px !important;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
                }
                /* 減少對話之間的空白 */
                .stChatMessage {
                    margin-bottom: 0.2rem !important;
                }
                /* 發言者名稱樣式 */
                [data-testid="stChatMessage"] .stChatMessageAvatar + div strong {
                    font-size: 15px !important;
                    color: #2c3e50 !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            h1, h2 = st.columns([2, 1])
            h1.subheader("Podcast Mode")
            script_list = data.get("script", [])
            
            if h2.button("🔊 播放對話", use_container_width=True):
                full_audio = " ".join([f"{m.get('speaker')} says, {m.get('text')}" if isinstance(m, dict) else str(m) for m in script_list])
                play_audio_html(full_audio)
            
            for msg in script_list:
                speaker = msg.get("speaker", "Rachel") if isinstance(msg, dict) else "Podcast"
                text = msg.get("text", "") if isinstance(msg, dict) else str(msg)
                with st.chat_message(speaker):
                    st.write(f"**{speaker}**: {text}")

# ===================================================================
# 7. TAB5 ─ AI控制台-資料庫管理 (原 TAB4 功能)
# ===================================================================
with tabs[4]:
    # ═══════════════════════════════════════════════════════════════
    # 🔥 關鍵：確保資料已載入（只執行一次）
    # ═══════════════════════════════════════════════════════════════
    if 'sentences' not in st.session_state:
        with st.spinner("🔄 正在載入資料..."):
            st.session_state.sentences = load_sentences()
            st.success(f"✅ 已載入 {len(st.session_state.sentences)} 筆資料")

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
        
        # 特徵 1：經文格式（章:節 + 空格 + 中文開頭）
        scripture_pattern = r'\d+\s*[:：]\s*\d+\s+[\u4e00-\u9fa5]'
        scripture_matches = len(re.findall(scripture_pattern, text[:1000]))
        
        # 特徵 2：計算有效字符（排除時間戳雜訊）
        lines = text.split('\n')
        content_lines = []
        for line in lines:
            # 跳過純時間戳行（如 "0:08", "8 秒", "1 分鐘 4 秒"）
            if re.match(r'^\s*\d+[:：]\d+\s*$', line):
                continue
            if re.match(r'^\s*\d+\s*[秒分鐘小時]\s*$', line):
                continue
            content_lines.append(line)
        
        clean_text = '\n'.join(content_lines)
        
        chinese_count = len(re.findall(r'[\u4e00-\u9fa5]', clean_text))
        english_word_count = len(re.findall(r'\b[a-zA-Z]{2,}\b', clean_text))
        
        # 決策邏輯
        if scripture_matches >= 2:
            return "scripture"
        elif chinese_count > english_word_count * 3:
            return "scripture"
        else:
            return "document"

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
        st.session_state.ref_number = f"REF_{datetime.datetime.now().strftime('%m%d%H%M')}"
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
            blank_ref = st.text_input("參考編號", value=f"BLANK_{datetime.datetime.now().strftime('%m%d%H%M')}", key="blank_ref")
            
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
                        "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
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
                        "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
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
                            'date_added': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
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
                            'date_added': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
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
                            'date_added': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
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
                            'date_added': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
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
                
                return f"REF_{datetime.datetime.now().strftime('%m%d%H%M')}"
            
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
                                "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
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
                                    "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
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


