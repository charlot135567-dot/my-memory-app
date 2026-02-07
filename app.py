# ===================================================================
# 0. 套件 & 全域函式（一定放最頂）
# ===================================================================
import streamlit as st
import subprocess, sys, os, datetime as dt, pandas as pd, io, json, re, tomli, tomli_w
from streamlit_calendar import calendar
import streamlit.components.v1 as components

# 在文件最開始初始化所有 session state 變量
def init_session_state():
    defaults = {
        "is_prompt_generated": False,
        # 其他變量...
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
# 1. 側邊欄（一次 4 連結，無重複）
# ===================================================================
with st.sidebar:
    st.divider()
    c1, c2 = st.columns(2)
    c1.link_button("✨ Google AI", "https://gemini.google.com/")
    c2.link_button("🤖 Kimi K2",   "https://kimi.moonshot.cn/")
    c3, c4 = st.columns(2)
    c3.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb")
    c4.link_button("THSV11",    "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")
    
    # ✅ 加在這裡（仍在 with st.sidebar: 內部）
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

# ✅ 注意這裡已經不在 with st.sidebar: 裡面了！
# 背景 CSS 要放在這裡（sidebar 外面，但在 tabs 前面）
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
if 'analysis_history' not in st.session_state: st.session_state.analysis_history = []

# ---------- CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap ');
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
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg ",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg ",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg ",
    "M1": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro1.jpg ",
    "M2": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro2.jpg ",
    "M3": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro3.jpg ",
    "M4": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro4.jpg "
}
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다</p>', unsafe_allow_html=True)
    st.image(IMG_URLS["M3"], width=250)
    st.divider()

tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# ===================================================================
# 3. TAB1 ─ 書桌（單純經文與例句，無月曆）
# ===================================================================
with tabs[0]:
    col_content, col_m1 = st.columns([0.65, 0.35])

    with col_content:
        st.info("**Becoming** / 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 🇹🇭 เหมาะสม | 🇨🇳 相稱")
        st.success("""
            🌟 **Pro 17:07** Fine speech is not becoming to a fool; still less is false speech to a prince.   
            🇯🇵 すぐれた言葉は愚か者にはふさわしくない。偽りの言葉は君主にはなおさらふさわしくない。   
            🇨🇳 愚頑人說美言本不相稱，何況君王說謊話呢？
            """, icon="📖")
    with col_m1:
        st.markdown(f"""
            <div style="display:flex;flex-direction:column;justify-content:space-between;height:100%;min-height:250px;text-align:center;">
                <div style="flex-grow:1;display:flex;align-items:center;justify-content:center;">
                    <img src="{IMG_URLS['M1']}" style="width:200px;margin-bottom:10px;">
                </div>
                <div class="grammar-box-container" style="margin-top:auto;">
                    <p style="margin:2px 0;font-size:14px;font-weight:bold;color:#333;">時態: 現在簡單式</p>
                    <p style="margin:2px 0;font-size:14px;font-weight:bold;color:#333;">核心片語:</p>
                    <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.4;color:#555;">
                        <li>Fine speech (優美言辭)</li>
                        <li>Becoming to (相稱)</li>
                        <li>Still less (何況)</li>
                        <li>False speech (虛假言辭)</li>
                    </ul>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### ✍️ 文法運用例句")
    cl1, cl2 = st.columns(2)
    with cl1:
        st.markdown("**Ex 1:** *Casual attire is not becoming to a CEO; still less is unprofessional language.* <p class='small-font'>便服對執行長不相稱；更不用說不專業的言語了。</p>", unsafe_allow_html=True)
    with cl2:
        st.markdown("**Ex 2:** *Wealth is not becoming to a man without virtue; still less is power.* <p class='small-font'>財富對於無德之人不相稱；更不用說權力了。</p>", unsafe_allow_html=True)

# ===================================================================
# 4. TAB2 ─ 月曆待辦（Emoji 清洗版，避免重複顯示）
# ===================================================================
with tabs[1]:
    import datetime as dt, re, os, json
    from streamlit_calendar import calendar

    # ---------- 0. 檔案持久化 ----------
    DATA_DIR = "data"
    os.makedirs(DATA_DIR, exist_ok=True)
    TODO_FILE = os.path.join(DATA_DIR, "todos.json")

    def load_todos():
        if os.path.exists(TODO_FILE):
            try:
                with open(TODO_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("載入待辦失敗:", e)
        return {}

    def save_todos():
        try:
            with open(TODO_FILE, "w", encoding="utf-8") as f:
                json.dump(st.session_state.todo, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("儲存待辦失敗:", e)

    # ---------- 1. 初始化 ----------
    if "todo" not in st.session_state:
        st.session_state.todo = load_todos()
    if "sel_date" not in st.session_state:
        st.session_state.sel_date = str(dt.date.today())
    if "cal_key" not in st.session_state:
        st.session_state.cal_key = 0
    if "active_del_id" not in st.session_state:
        st.session_state.active_del_id = None

    # ---------- 2. Emoji 清洗工具（核心修正） ----------
    _EMOJI_RE = re.compile(
        r'[\U0001F300-\U0001FAFF\U00002700-\U000027BF]+',
        flags=re.UNICODE
    )

    def get_clean_title(text: str) -> tuple:
        """
        從標題中：
        1. 擷取第一個 Emoji
        2. 移除所有 Emoji，保留純文字
        """
        found = _EMOJI_RE.search(text)
        emoji = found.group(0)[0] if found else ""
        clean_text = _EMOJI_RE.sub('', text).strip()
        return emoji, clean_text

    # ---------- 3. 月曆事件 ----------
    def build_events():
        ev = []
        for d, items in st.session_state.todo.items():
            if not isinstance(items, list):
                continue
            for t in items:
                emo, pure_title = get_clean_title(t.get("title", ""))
                ev.append({
                    "title": f"{emo} {pure_title}".strip(),
                    "start": f"{d}T{t.get('time','00:00:00')}",
                    "backgroundColor": "#FFE4E1",
                    "borderColor": "#FFE4E1",
                    "textColor": "#333"
                })
        return ev

    # ---------- 4. 月曆 ----------
    with st.expander("📅 聖經學習生活月曆", expanded=True):
        cal_options = {
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": ""
            },
            "initialView": "dayGridMonth",
            "displayEventTime": False,
            "height": "auto"
        }

        state = calendar(
            events=build_events(),
            options=cal_options,
            key=f"calendar_{st.session_state.cal_key}"
        )

        if state.get("dateClick"):
            st.session_state.sel_date = state["dateClick"]["date"][:10]
            st.rerun()

    # ---------- 5. 下方三日清單 ----------
    st.markdown("##### 📋 待辦事項")

    try:
        base_date = dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date()
    except:
        base_date = dt.date.today()

    for offset in range(3):
        d_obj = base_date + dt.timedelta(days=offset)
        d_str = str(d_obj)
        if d_str in st.session_state.todo:
            for idx, item in enumerate(st.session_state.todo[d_str]):
                item_id = f"{d_str}_{idx}"
                emo, pure_title = get_clean_title(item.get("title", ""))

                c1, c2, c3 = st.columns([0.25, 7.75, 2], vertical_alignment="top")

                with c1:
                    if st.button("💟", key=f"h_{item_id}"):
                        st.session_state.active_del_id = (
                            None if st.session_state.active_del_id == item_id else item_id
                        )
                        st.rerun()

                with c2:
                    st.write(
                        f"{d_obj.month}/{d_obj.day} "
                        f"{item['time'][:5]} "
                        f"{emo} {pure_title}".strip()
                    )

                with c3:
                    if st.session_state.active_del_id == item_id:
                        if st.button("🗑️", key=f"d_{item_id}"):
                            st.session_state.todo[d_str].pop(idx)
                            save_todos()
                            st.session_state.cal_key += 1
                            st.session_state.active_del_id = None
                            st.rerun()

    # ---------- 6. 新增待辦 ----------
    st.divider()
    with st.expander("➕ 新增待辦", expanded=True):
        with st.form("todo_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                in_date = st.date_input("日期", base_date)
            with col2:
                in_time = st.time_input("時間", dt.time(9, 0))

            in_title = st.text_input("待辦事項（可含 Emoji）")

            if st.form_submit_button("💾 儲存"):
                if in_title:
                    k = str(in_date)
                    if k not in st.session_state.todo:
                        st.session_state.todo[k] = []
                    st.session_state.todo[k].append({
                        "title": in_title,
                        "time": str(in_time)
                    })
                    save_todos()
                    st.session_state.cal_key += 1
                    st.rerun()

# ===================================================================
# 5. TAB3 ─ 挑戰（單純翻譯題，無月曆）
# ===================================================================
with tabs[2]:
    col_challenge, col_deco = st.columns([0.7, 0.3])
    with col_challenge:
        st.subheader("📝 翻譯挑戰")
        st.write("題目 1: 愚頑人說美言本不相稱...")
        st.text_input("請輸入英文翻譯", key="ans_1_final", placeholder="Type your translation here...")
    with col_deco:
        st.image(IMG_URLS.get("B"), width=150, caption="Keep Going!")
        
# ===================================================================
# 6. TAB4 ─AI 控制台 + Notion Database 整合（支援多工作表）
# ===================================================================
with tabs[3]:
    import os, json, datetime as dt, pandas as pd, urllib.parse, base64, re, csv, requests
    from io import StringIO
    import streamlit.components.v1 as components

    # ---------- 新增：Notion API 設定與載入函數 ----------
    NOTION_TOKEN = st.secrets.get("notion", {}).get("token", "")
    DATABASE_ID = "2f910510e7fb80c4a67ff8735ea90cdf"

    # ---------- 輔助工具：安全獲取 Notion 文字 ----------
    def get_notion_text(prop_dict):
        """防止 Index out of range"""
        rt = prop_dict.get("rich_text", [])
        if rt and len(rt) > 0:
            return rt[0].get("text", {}).get("content", "")
        return ""

    # 顯示連線狀態（在 Sidebar）
    with st.sidebar:
        if NOTION_TOKEN:
            st.success("☁️ Notion 已連線")
        else:
            st.warning("⚠️ Notion 未設定（Reboot 後資料會消失）")

    def load_from_notion():
        """啟動時從 Notion 載入所有資料"""
        if not NOTION_TOKEN:
            return {}

        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        all_data = {}
        has_more = True
        start_cursor = None

        try:
            with st.spinner("☁️ 正在從 Notion 載入資料..."):
                while has_more:
                    payload = {"page_size": 100}
                    if start_cursor:
                        payload["start_cursor"] = start_cursor

                    response = requests.post(url, headers=headers, json=payload)
                    data = response.json()

                    for page in data.get("results", []):
                        props = page.get("properties", {})

                        ref = get_notion_text(props.get("Ref_No", {})) or "unknown"
                        translation = get_notion_text(props.get("Translation", {}))

                        v1_content = ""
                        v2_content = ""
                        if "【V1 Sheet】" in translation:
                            parts = translation.split("【V2 Sheet】")
                            v1_content = parts[0].split("【V1 Sheet】")[-1].strip() if len(parts) > 0 else ""
                            v2_content = parts[1].split("【其他工作表】")[0].strip() if len(parts) > 1 else ""

                        title_list = props.get("Content", {}).get("title", [])
                        original = title_list[0].get("text", {}).get("content", "") if title_list else ""

                        all_data[ref] = {
                            "ref": ref,
                            "original": original,
                            "v1_content": v1_content,
                            "v2_content": v2_content,
                            "ai_result": translation,
                            "type": props.get("Type", {}).get("select", {}).get("name", "Scripture"),
                            "mode": props.get("Source_Mode", {}).get("select", {}).get("name", "Mode A"),
                            "date_added": props.get("Date_Added", {}).get("date", {}).get("start", "") if props.get("Date_Added", {}).get("date") else "",
                            "notion_page_id": page.get("id"),
                            "notion_synced": True,
                            "saved_sheets": ["V1", "V2"] if v1_content or v2_content else ["從Notion載入"]
                        }

                    has_more = data.get("has_more", False)
                    start_cursor = data.get("next_cursor")

                if all_data:
                    st.sidebar.success(f"✅ 已載入 {len(all_data)} 筆")
                return all_data
        except Exception as e:
            st.sidebar.error(f"❌ 載入失敗：{e}")
            return {}

    def save_to_notion(data_dict):
        """儲存到 Notion，成功後回傳 page_id"""
        if not NOTION_TOKEN:
            return False, "未設定 Notion Token", None

        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        full_content = f"""【V1 Sheet】
{data_dict.get('v1_content', '無')}

【V2 Sheet】
{data_dict.get('v2_content', '無')}

【其他補充】
{data_dict.get('other_sheets', '無')}
"""

        properties = {
            "Content": {"title": [{"text": {"content": data_dict.get('original', '')[:100]}}]},
            "Translation": {"rich_text": [{"text": {"content": full_content[:2000]}}]},
            "Ref_No": {"rich_text": [{"text": {"content": data_dict.get("ref", "N/A")}}]},
            "Source_Mode": {"select": {"name": data_dict.get("mode", "Mode A")}},
            "Type": {"select": {"name": data_dict.get("type", "Scripture")}},
            "Date_Added": {"date": {"start": dt.datetime.now().isoformat()}}
        }

        try:
            response = requests.post(url, headers=headers, json={
                "parent": {"database_id": DATABASE_ID},
                "properties": properties
            })
            if response.status_code == 200:
                page_id = response.json().get("id")
                return True, "成功", page_id
            else:
                return False, f"Notion API Error: {response.text}", None
        except Exception as e:
            return False, str(e), None

    # ---------- 資料庫持久化 ----------
    SENTENCES_FILE = "sentences.json"

    def load_sentences():
        if os.path.exists(SENTENCES_FILE):
            try:
                with open(SENTENCES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_sentences(data):
        with open(SENTENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ---------- 初始化所有 session_state ----------
    if 'sentences' not in st.session_state:
        st.session_state.sentences = load_sentences()
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

    # 1. 智能偵測內容類型
    def detect_content_mode(text):
        text = text.strip()
        if not text:
            return "document"
        if text.startswith("{"):
            return "json"
        
        has_chinese = re.search(r'[\u4e00-\u9fa5]', text)
        return "scripture" if has_chinese else "document"

    # 2. 產生完整指令（修正：獨立函數，不再包在 save_to_notion 內）
    def generate_full_prompt():
        raw_text = st.session_state.get("raw_input_temp", "").strip()
        if not raw_text:
            st.warning("請先貼上內容")
            return
        
        mode = detect_content_mode(raw_text)
        
        if mode in ["json", "scripture"]:
            full_prompt = f"""你是一位精通多國語言的聖經專家與語言學教授。請根據輸入內容選擇對應模式輸出。

### 模式 A：【聖經經文分析時】＝》一定要產出V1 + V2 Excel格式（Markdown表格）

⚠️ 輸出格式要求：請使用 **Markdown 表格格式**（如下範例），方便我直接複製貼回 Excel：

【V1 Sheet 範例】
| Ref. | English (ESV) | Chinese | Syn/Ant | Grammar |
|------|---------------|---------|---------|---------|
| Pro 31:6 | Give strong drink... | 可以把濃酒... | strong drink (烈酒) / watered down wine (淡酒) | 1️⃣[祈使句解析] 2️⃣[Give strong drink to him who is perishing] 3️⃣Ex. [Go and make disciples...] |

【V2 Sheet 範例】
| Ref. | 口語訳 | Grammar | Note | KRF | Syn/Ant | THSV11 |
|------|--------|---------|------|-----|---------|--------|

🔹 V1 Sheet 欄位要求：
1. Ref.：自動找尋經卷章節並用縮寫 (如: Pro, Rom, Gen).
2. English (ESV)：檢索對應的 ESV 英文經文.
3. Chinese：填入我提供的中文原文.
4. Syn/Ant：ESV 中的中高級單字或片語（含中/英翻譯），低於中級不列出.
5. Grammar：嚴格遵守符號化格式：1️⃣[文法邏輯解析] 2️⃣[補齊後的完整應用句] 3️⃣Ex. [中英對照聖經應用例句]

🔹 V2 Sheet 欄位要求：
1. Ref.：同 V1.
2. 口語訳：檢索對應的日本《口語訳聖經》(1955).
3. Grammar：解析日文文法（格式同 V1，使用 1️⃣2️⃣3️⃣Ex.）.
4. Note：日文文法或語境的補充說明.
5. KRF：檢索對應的韓文《Korean Revised Version》.
6. Syn/Ant：韓文高/ 中高級字（含日/韓/中翻譯）.
7. THSV11:輸出泰文對應的重要片語《Thai Holy Bible, Standard Version 2011》.

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

⚠️ 輸出格式要求：請使用 **Markdown 表格格式**：

 【W Sheet - 重點要求：取高級/中高級單字15個/片語15個】
| No | Word/Phrase | Level | Chinese | Synonym | Antonym | Bible Example |
|----|-------------|-------|---------|---------|---------|---------------|
| 1 | steadfast | 高級 | 堅定不移的 | firm | wavering | 1Co 15:58 Therefore... |

【P Sheet - 文稿段落】
| Paragraph | English Refinement | 中英夾雜講章 |
|-----------|-------------------|--------------|
| 1 | We need to be steadfast... | 我們需要 (**steadfast**) ... |

【Grammar List - 重點要求：6 句 × 每句 3-6 解析】
| No | Original Sentence (from text) | Grammar Rule | Analysis & Example (1️⃣2️⃣3️⃣...6️⃣) |
|----|------------------------------|--------------|-----------------------------------|
| 1 | [文稿中的第1個精選句] | [文法規則名稱] | 1️⃣[句構辨識]...<br>2️⃣[結構還原]...<br>3️⃣[語義分析]...<br>4️⃣[聖經例句]... |

🔹 Grammar List 詳細規範：
1. **選句標準**：從文稿中精選 6 個**最具教學價值**的句子
2. **解析深度**：每句必須提供 **3-6 個文法解析點**

請以 **Markdown 表格格式**輸出（非 JSON）.

待分析文稿：{raw_text}"""
            st.session_state.content_mode = "B"

        st.session_state.original_text = raw_text
        st.session_state.main_input_value = full_prompt
        st.session_state.is_prompt_generated = True
        st.session_state.ref_number = f"REF_{dt.datetime.now().strftime('%m%d%H%M')}"
        # 重置工作表暫存
        st.session_state.current_entry = {
            'v1': '', 'v2': '', 'w_sheet': '', 
            'p_sheet': '', 'grammar_list': '', 'other': ''
        }
        st.session_state.saved_entries = []

    # ---------- 📝 主要功能區 ----------
    st.header("📝 AI 分析工作流程")
    
    # === STEP 1: 輸入區 ===
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

    # === STEP 2: Prompt 產生後顯示 ===
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

        # === STEP 3: 多工作表收集區 ===
        with st.expander("步驟 3：分批貼上 AI 分析結果", expanded=True):
            st.info("💡 可以分批貼上 V1、V2、W Sheet、P Sheet 等，貼好一個存一個，最後統一儲存")
            
            # 根據模式顯示對應的工作表選項
            if st.session_state.content_mode == "A":
                sheet_options = ["V1 Sheet", "V2 Sheet", "其他補充"]
            else:
                sheet_options = ["W Sheet", "P Sheet", "Grammar List", "其他補充"]
            
            selected_sheet = st.selectbox("選擇要貼上的工作表", sheet_options)
            
            # 輸入區
            sheet_content = st.text_area(
                f"貼上 {selected_sheet} 內容",
                height=200,
                key=f"input_{selected_sheet.replace(' ', '_')}"
            )
            
            # 暫存按鈕
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
                # 顯示已暫存的工作表
                if st.session_state.saved_entries:
                    st.write("📋 已暫存：", " | ".join([f"✅ {s}" for s in st.session_state.saved_entries]))
            
            # 預覽已暫存的內容
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

                # === STEP 4: 統一儲存區（字體縮小版）===
        with st.expander("步驟 4：儲存到資料庫", expanded=True):
            st.caption("確認所有工作表都暫存後，填寫資訊並儲存")
            
            # 儲存設定
            save_cols = st.columns([2, 1, 1])
            with save_cols[0]:
                ref_input = st.text_input(
                    "參考編號 (Ref_No)", 
                    value=st.session_state.get('ref_number', ''),
                    key="ref_no_input"
                )
            with save_cols[1]:
                type_select = st.selectbox(
                    "類型",
                    ["Scripture", "Document", "Vocabulary", "Grammar", "Sermon"],
                    index=0 if st.session_state.content_mode == "A" else 1,
                    key="type_select"
                )
            
            # --- Google Sheet 設定（新增）---
            sheet_connected = False
            try:
                import gspread
                from google.oauth2.service_account import Credentials
                GCP_SA = st.secrets.get("gcp_service_account", {})
                SHEET_ID = st.secrets.get("sheets", {}).get("spreadsheet_id", "")
                if GCP_SA and SHEET_ID:
                    sheet_connected = True
            except:
                pass
            
            # 儲存按鈕列（4個並列：本地、Notion、Google Sheet、全部）
            btn_cols = st.columns(4)
            
            with btn_cols[0]:
                # 存到本地
                if st.button("💾 本地", use_container_width=True):
                    if not st.session_state.saved_entries:
                        st.error("請先至少暫存一個工作表！")
                    else:
                        try:
                            ref = ref_input or st.session_state.ref_number
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
                # 存到 Notion
                if NOTION_TOKEN:
                    if st.button("🚀 Notion", use_container_width=True, type="primary"):
                        if not st.session_state.saved_entries:
                            st.error("請先至少暫存一個工作表！")
                        else:
                            data_to_save = {
                                "original": st.session_state.original_text,
                                "prompt": st.session_state.main_input_value,
                                "v1_content": st.session_state.current_entry['v1'],
                                "v2_content": st.session_state.current_entry['v2'],
                                "other_sheets": str(st.session_state.current_entry),
                                "ref": ref_input or st.session_state.ref_number,
                                "mode": f"Mode {st.session_state.content_mode}",
                                "type": type_select
                            }
                            success, msg, page_id = save_to_notion(data_to_save)
                            if success:
                                full_data = {
                                    "ref": ref_input or st.session_state.ref_number,
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
                                    "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "notion_synced": True,
                                    "notion_page_id": page_id
                                }
                                st.session_state.sentences[ref_input or st.session_state.ref_number] = full_data
                                save_sentences(st.session_state.sentences)
                                st.success(f"✅ 已同步 Notion！")
                                st.balloons()
                            else:
                                st.error(f"❌ 同步失敗：{msg}")
                else:
                    st.button("🚀 Notion", disabled=True, use_container_width=True)
            
            with btn_cols[2]:
                # 存到 Google Sheet（新增）
                if sheet_connected:
                    if st.button("📊 Google", use_container_width=True, type="primary"):
                        if not st.session_state.saved_entries:
                            st.error("請先至少暫存一個工作表！")
                        else:
                            try:
                                # 認證
                                creds = Credentials.from_service_account_info(
                                    GCP_SA,
                                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                                )
                                gc = gspread.authorize(creds)
                                sh = gc.open_by_key(SHEET_ID)
                                
                                # 取得或建立工作表
                                sheet_name = st.session_state.content_mode
                                try:
                                    worksheet = sh.worksheet(sheet_name)
                                except:
                                    worksheet = sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
                                
                                # 準備資料
                                ref = ref_input or st.session_state.ref_number
                                row_data = [
                                    ref,
                                    type_select,
                                    st.session_state.original_text[:100],
                                    st.session_state.current_entry['v1'][:500] if st.session_state.current_entry['v1'] else "",
                                    st.session_state.current_entry['v2'][:500] if st.session_state.current_entry['v2'] else "",
                                    st.session_state.current_entry['w_sheet'][:500] if st.session_state.current_entry['w_sheet'] else "",
                                    st.session_state.current_entry['p_sheet'][:500] if st.session_state.current_entry['p_sheet'] else "",
                                    dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    ", ".join(st.session_state.saved_entries)
                                ]
                                
                                # 寫入
                                worksheet.append_row(row_data)
                                
                                # 標記已同步
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
                                    "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "google_sheet_synced": True
                                }
                                st.session_state.sentences[ref] = full_data
                                save_sentences(st.session_state.sentences)
                                
                                st.success(f"✅ 已存 Google Sheet：{sheet_name}")
                                st.balloons()
                                
                            except Exception as e:
                                st.error(f"❌ Google Sheet 失敗：{str(e)}")
                else:
                    st.button("📊 Google", disabled=True, use_container_width=True)
                    if not GCP_SA:
                        st.caption("未設定憑證")
                    elif not SHEET_ID:
                        st.caption("未設定 Sheet ID")
            
            with btn_cols[3]:
                # 一鍵存全部（本地+Notion+Google）
                if st.button("💾🚀📊 全部", use_container_width=True):
                    if not st.session_state.saved_entries:
                        st.error("請先至少暫存一個工作表！")
                    else:
                        ref = ref_input or st.session_state.ref_number
                        success_list = []
                        
                        # 1. 存本地
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
                        success_list.append("本地")
                        
                        # 2. 存 Notion
                        if NOTION_TOKEN:
                            notion_data = {
                                "original": st.session_state.original_text,
                                "prompt": st.session_state.main_input_value,
                                "v1_content": st.session_state.current_entry['v1'],
                                "v2_content": st.session_state.current_entry['v2'],
                                "other_sheets": str(st.session_state.current_entry),
                                "ref": ref,
                                "mode": f"Mode {st.session_state.content_mode}",
                                "type": type_select
                            }
                            success_notion, msg, page_id = save_to_notion(notion_data)
                            if success_notion:
                                full_data['notion_synced'] = True
                                full_data['notion_page_id'] = page_id
                                success_list.append("Notion")
                        
                        # 3. 存 Google Sheet
                        if sheet_connected:
                            try:
                                creds = Credentials.from_service_account_info(
                                    GCP_SA,
                                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                                )
                                gc = gspread.authorize(creds)
                                sh = gc.open_by_key(SHEET_ID)
                                sheet_name = st.session_state.content_mode
                                try:
                                    worksheet = sh.worksheet(sheet_name)
                                except:
                                    worksheet = sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
                                
                                row_data = [
                                    ref, type_select,
                                    st.session_state.original_text[:100],
                                    st.session_state.current_entry['v1'][:500],
                                    st.session_state.current_entry['v2'][:500],
                                    st.session_state.current_entry['w_sheet'][:500],
                                    st.session_state.current_entry['p_sheet'][:500],
                                    dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    ", ".join(st.session_state.saved_entries)
                                ]
                                worksheet.append_row(row_data)
                                full_data['google_sheet_synced'] = True
                                success_list.append("Google Sheet")
                            except:
                                pass
                        
                        # 更新本地資料
                        st.session_state.sentences[ref] = full_data
                        save_sentences(st.session_state.sentences)
                        
                        st.success(f"✅ 已同步：{' + '.join(success_list)}")
                        st.balloons()

            # 清除按鈕（縮小字體）
            st.divider()
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
    # ---------- 📊 儲存狀態顯示區（字體縮小版）----------
    st.divider()
    status_cols = st.columns([1, 1, 1, 2])
    
    with status_cols[0]:
        total_local = len(st.session_state.get('sentences', {}))
        # 使用較小的標題
        st.markdown(f"<small>💾 本地資料庫</small>", unsafe_allow_html=True)
        st.markdown(f"<h4>{total_local} 筆</h4>", unsafe_allow_html=True)
    
    with status_cols[1]:
        if NOTION_TOKEN:
            st.markdown(f"<small>☁️ Notion</small>", unsafe_allow_html=True)
            st.markdown(f"<h4>✅ 已連線</h4>", unsafe_allow_html=True)
        else:
            st.markdown(f"<small>☁️ Notion</small>", unsafe_allow_html=True)
            st.markdown(f"<h4>❌ 未設定</h4>", unsafe_allow_html=True)
    
    with status_cols[2]:
        # 檢查 Google Sheet 連線狀態
        sheet_connected = False
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            GCP_SA = st.secrets.get("gcp_service_account", {})
            SHEET_ID = st.secrets.get("sheets", {}).get("spreadsheet_id", "")
            if GCP_SA and SHEET_ID:
                sheet_connected = True
        except:
            pass
        
        if sheet_connected:
            st.markdown(f"<small>📊 Google</small>", unsafe_allow_html=True)
            st.markdown(f"<h4>✅ 已連線</h4>", unsafe_allow_html=True)
        else:
            st.markdown(f"<small>📊 Google</small>", unsafe_allow_html=True)
            st.markdown(f"<h4>❌ 未設定</h4>", unsafe_allow_html=True)
    
    with status_cols[3]:
        # 顯示最近儲存的資料
        if st.session_state.get('sentences'):
            recent = list(st.session_state.sentences.values())[-3:]
            st.markdown(f"<small>🕐 最近儲存：</small>", unsafe_allow_html=True)
            for item in reversed(recent):
                sheets = item.get('saved_sheets', ['未知'])
                st.caption(f"• {item.get('ref', 'N/A')} ({', '.join(sheets)})")

    # ---------- 📋 已存資料瀏覽器 ----------
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
                
                # 原始內容
                with st.expander("📝 原始輸入"):
                    st.text(item.get('original', '無'))
                
                # 工作表分頁
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
                
                # 操作按鈕
                st.divider()
                btn_cols = st.columns([1, 1, 1, 2])
                
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
                
                with btn_cols[2]:
                    notion_synced = item.get('notion_synced', False)
                    if NOTION_TOKEN and not notion_synced:
                        if st.button("🚀 同步Notion", key=f"sync_{selected_ref}"):
                            data = {
                                "original": item['original'], "prompt": item['prompt'],
                                "v1_content": item.get('v1_content', ''),
                                "v2_content": item.get('v2_content', ''),
                                "ref": selected_ref, "mode": f"Mode {item.get('mode', 'A')}",
                                "type": item.get('type', 'Scripture')
                            }
                            success, msg, page_id = save_to_notion(data)
                            if success:
                                st.session_state.sentences[selected_ref]['notion_synced'] = True
                                st.session_state.sentences[selected_ref]['notion_page_id'] = page_id
                                save_sentences(st.session_state.sentences)
                                st.success(f"✅ 已同步!")
                                st.rerun()
                    elif notion_synced:
                        st.caption("✅ 已同步")

    # ---------- 🔍 簡易搜尋 ----------
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

    # ---------- 底部統計（移除重複的備份下載） ----------
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
