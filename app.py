# ===================================================================
# 0. 套件 & 全域函式（一定放最頂）
# ===================================================================
import streamlit as st  
import subprocess, sys, os, datetime as dt, pandas as pd, io, json, re, tomli, tomli_w
from streamlit_calendar import calendar
import streamlit.components.v1 as components
import requests

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

# ---------- 背景圖片套用（補上這段！）----------
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
    pass  # 背景圖失敗時靜默處理

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
# 3. TAB1 ─ 書桌（修正版：只抓2筆文法，內容有序編排）
# ===================================================================
with tabs[0]:
    import csv
    from io import StringIO
    import random
    import re
    
    # 初始化輪換時間
    if 'tab1_last_update' not in st.session_state:
        st.session_state.tab1_last_update = dt.datetime.now()
        st.session_state.tab1_random_seed = random.randint(1, 1000)
    
    # 檢查是否需要更新（超過1小時）
    time_diff = (dt.datetime.now() - st.session_state.tab1_last_update).total_seconds()
    if time_diff > 3600:
        st.session_state.tab1_last_update = dt.datetime.now()
        st.session_state.tab1_random_seed = random.randint(1, 1000)
        st.rerun()
    
    sentences = st.session_state.get('sentences', {})
    
    if not sentences:
        st.warning("資料庫為空，請先在 TAB4 儲存資料")
    else:
        random.seed(st.session_state.tab1_random_seed)
        selected_ref = random.choice(list(sentences.keys()))
        selected_data = sentences[selected_ref]
        
        # 取得資料
        v1_content = selected_data.get('v1_content', '')
        w_sheet = selected_data.get('w_sheet', '')
        grammar_list = selected_data.get('grammar_list', [])
        
        v1_rows = []
        w_rows = []
        
        # 解析 V1 CSV
        if v1_content:
            try:
                lines = v1_content.strip().split('\n')
                if lines:
                    reader = csv.DictReader(lines)
                    v1_rows = list(reader)
            except:
                pass
        
        # 解析 W sheet CSV
        if w_sheet:
            try:
                lines = w_sheet.strip().split('\n')
                if lines:
                    reader = csv.DictReader(lines)
                    w_rows = list(reader)
            except:
                pass
        
        selected_verse = random.choice(v1_rows) if v1_rows else {}
        
        # 版面配置：左側 (2/3) + 右側 (1/3)
        col_left, col_right = st.columns([0.67, 0.33])
        
        with col_left:
            # ===== 左上：多語言單字（來自 V1 的 Syn/Ant）=====
            syn_ant = selected_verse.get('Syn/Ant', '')
            st.markdown("### 🌍")
            
            if syn_ant:
                # 先嘗試用 | 分割
                if '|' in syn_ant:
                    entries = [e.strip() for e in syn_ant.split('|') if e.strip()]
                else:
                    entries = [e.strip() for e in re.split(r'(?=🇯🇵|🇰🇷|🇹🇭|🇨🇳)', syn_ant) if e.strip()]
                
                for entry in entries:
                    entry = entry.lstrip('•').strip()
                    
                    if entry.startswith('🇯🇵'):
                        st.markdown(f"🇯🇵 **{entry[2:].strip()}**")
                    elif entry.startswith('🇰🇷'):
                        st.markdown(f"🇰🇷 **{entry[2:].strip()}**")
                    elif entry.startswith('🇹🇭'):
                        st.markdown(f"🇹🇭 **{entry[2:].strip()}**")
                    elif entry.startswith('🇨🇳'):
                        st.markdown(f"🇨🇳 **{entry[2:].strip()}**")
                    else:
                        # 根據內容判斷語言
                        if any(c in entry for c in ['ふさわ', '言い', '覆い']):
                            st.markdown(f"🇯🇵 **{entry}**")
                        elif any(c in entry for c in ['화합', '이간', '어울']):
                            st.markdown(f"🇰🇷 **{entry}**")
                        elif any(c in entry for c in ['ให้อภัย', 'บั่นทอน', 'เหมาะ']):
                            st.markdown(f"🇹🇭 **{entry}**")
                        else:
                            st.markdown(f"🇬🇧 **{entry}**")
            else:
                st.info("無單字資料")
            
            st.divider()
            
            # ===== 左中：片語（來自 W sheet）=====
            st.markdown("### 🔤")
            
            phrases = []
            
            # 從 W sheet 讀取
            if w_rows:
                for row in w_rows[:4]:
                    wp = row.get('word/phrases', '')
                    if wp and wp.strip():
                        phrases.append(wp.strip())
            
            # 備援：從 V1 Grammar 提取
            if not phrases:
                grammar = selected_verse.get('Grammar', '')
                if '2️⃣[' in grammar:
                    matches = re.findall(r'2️⃣\[(.+?)\]', grammar)
                    for m in matches[:4]:
                        clean_phrase = re.sub(r'\s*\([^)]*詞[^)]*\)', '', m)
                        phrases.append(clean_phrase)
            
            if phrases:
                for i, phrase in enumerate(phrases[:4]):
                    parts = phrase.split('/')
                    if len(parts) >= 2:
                        col1, col2 = st.columns([0.6, 0.4])
                        with col1:
                            st.markdown(f"**{parts[0].strip()}**")
                        with c2:
                            st.caption(f"↔ {'/'.join(parts[1:]).strip()}")
                    else:
                        st.markdown(f"**{phrase}**")
                    if i < 3:
                        st.markdown("---")
            else:
                st.info("無片語資料")
            
            st.divider()
            
            # ===== 左下：經文（英日韓中）=====
            st.markdown("### 📖🌟")
            
            ref = selected_verse.get('Ref.', '')
            en = selected_verse.get('English (ESV)', '')
            cn = selected_verse.get('Chinese', '')
            jp = selected_verse.get('Japanese', '')
            kr = selected_verse.get('Korean', '')
            
            if en:
                st.markdown(f"🇬🇧 **{ref}**  \n>{en}")
            if jp:
                st.markdown(f"🇯🇵 **{ref}**  \n>{jp}")
            if kr:
                st.markdown(f"🇰🇷 **{ref}**  \n>{kr}")
            if cn:
                st.markdown(f"🇨🇳 **{ref}**  \n>{cn}")
        
        with col_right:
            # ===== 右側：文法解析（只抓2筆，有序編排）=====
            st.markdown("### 📚")
            
            # 收集文法資料（最多2筆）
            grammar_items = []
            
            # 來源 1：V1 的 Grammar 欄位（只取2筆）
            if v1_rows:
                for row in v1_rows[:2]:
                    grammar_text = row.get('Grammar', '')
                    if grammar_text and grammar_text.strip():
                        grammar_items.append(grammar_text.strip())
            
            # 來源 2：grammar_list（如果 V1 沒有）
            if not grammar_items and grammar_list:
                if isinstance(grammar_list, list):
                    for item in grammar_list[:2]:
                        if isinstance(item, dict):
                            item_text = '\n'.join(str(v) for v in item.values() if v)
                            grammar_items.append(item_text)
                        else:
                            grammar_items.append(str(item))
            
            # 顯示文法內容（有序編排）
            with st.container():
                st.markdown(
                    "<div style='background:#f8f9fa;padding:12px;border-radius:8px;border-left:4px solid #FF8C00;'>",
                    unsafe_allow_html=True
                )
                
                if grammar_items:
                    for idx, grammar_text in enumerate(grammar_items):
                        # 1️⃣ 分段解析
                        if '1️⃣[' in grammar_text:
                            match = re.search(r'1️⃣\[(.+?)\]', grammar_text, re.DOTALL)
                            if match:
                                st.markdown("📌 **分段解析**")
                                for line in match.group(1).strip().split('\n'):
                                    if line.strip():
                                        st.markdown(f"&nbsp;&nbsp;{line.strip()}")
                        
                        # 2️⃣ 詞性辨析
                        if '2️⃣[' in grammar_text:
                            match = re.search(r'2️⃣\[(.+?)\]', grammar_text, re.DOTALL)
                            if match:
                                st.markdown("🔤 **詞性辨析**")
                                for line in match.group(1).strip().split('\n'):
                                    if line.strip():
                                        st.markdown(f"&nbsp;&nbsp;{line.strip()}")
                        
                        # 3️⃣ 修辭與結構
                        if '3️⃣[' in grammar_text:
                            match = re.search(r'3️⃣\[(.+?)\]', grammar_text, re.DOTALL)
                            if match:
                                st.markdown("📖 **修辭與結構**")
                                for line in match.group(1).strip().split('\n'):
                                    if line.strip():
                                        st.markdown(f"&nbsp;&nbsp;{line.strip()}")
                        
                        # 4️⃣ 語意解釋
                        if '4️⃣[' in grammar_text:
                            match = re.search(r'4️⃣\[(.+?)\]', grammar_text, re.DOTALL)
                            if match:
                                st.markdown("💡 **語意解釋**")
                                for line in match.group(1).strip().split('\n'):
                                    if line.strip():
                                        st.markdown(f"&nbsp;&nbsp;{line.strip()}")
                        
                        # 如果沒有標記，直接顯示
                        if not any(x in grammar_text for x in ['1️⃣[', '2️⃣[', '3️⃣[', '4️⃣[']):
                            st.markdown(grammar_text)
                        
                        # 2筆之間加分隔線
                        if idx < len(grammar_items) - 1:
                            st.markdown("---")
                else:
                    st.info("無文法資料")
                
                minutes_left = max(0, (3600 - time_diff) / 60)
                st.markdown(
                    f"<small>來源: {selected_ref}｜{minutes_left:.0f}分後更新</small>",
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)
                
# ===================================================================
# 4. TAB2 ─ 月曆待辦 + 14天滑動金句（合併版）
# ===================================================================
with tabs[1]:
    import datetime as dt, re, os, json
    from streamlit_calendar import calendar

    # ==========================================
    # 上半部：月曆待辦（原有功能完整保留）
    # ==========================================
    
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

    # ---------- 2. Emoji 清洗工具 ----------
    _EMOJI_RE = re.compile(
        r'[\U0001F300-\U0001FAFF\U00002700-\U000027BF]+',
        flags=re.UNICODE
    )

    def get_clean_title(text: str) -> tuple:
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

    # ==========================================
    # 下半部：14天滑動金句（檔案持久化 + 美觀互動）
    # ==========================================
    st.divider()
    st.markdown("### ✨ 14天滑動金句")
    
    # 檔案持久化設定
    SENTENCES_FILE = os.path.join(DATA_DIR, "daily_sentences.json")
    
    def load_daily_sentences():
        """從檔案載入金句"""
        if os.path.exists(SENTENCES_FILE):
            try:
                with open(SENTENCES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("載入金句失敗:", e)
        return {}
    
    def save_daily_sentences():
        """儲存金句到檔案"""
        try:
            with open(SENTENCES_FILE, "w", encoding="utf-8") as f:
                json.dump(st.session_state.daily_sentences_tab2, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("儲存金句失敗:", e)
            st.error(f"儲存失敗: {e}")
    
    # 參數
    DAYS_KEEP = 14
    today = dt.date.today()
    
    # Session 初始化
    if "daily_sentences_tab2" not in st.session_state:
        # 先從檔案載入
        loaded = load_daily_sentences()
        
        # 如果是空的，放入預設5句金句
        if not loaded:
            loaded = {}
            default_sentences = [
                "遮掩人過的，尋求人愛；屢次挑錯的，離間密友。 箴言 17:9\nWhoever covers an offense seeks love, but he who repeats a matter separates close friends. (Proverbs 17:9 ESV)",
                "因為耶和華是你所倚靠的；他必保守你的腳不陷入網羅。(箴言 3:26)\nfor the LORD will be your confidence and will keep your foot from being caught. (Proverbs 3:26 ESV)",
                "箴言 17:27 寡少言語的，有知識；性情溫良的，有聰明。\nWhoever restrains his words has knowledge, and he who has a cool spirit is a man of understanding. (Proverbs 17:27 ESV)",
                "箴言 17:28 愚昧人若靜默不言也可算為智慧，閉口不說也可算為聰明\nEven a fool who keeps silent is considered wise; when he closes his lips, he is deemed intelligent. (Proverbs 17:28 ESV)",
                "詩 50:23 凡以感謝獻上為祭的便是榮耀我；那按正路而行的，我必使他得着我的救恩。\nWhoever offers praise glorifies Me; And to him who orders his conduct aright I will show the salvation of God. (Psalms 50:23 NKJV)"
            ]
            for i, sentence in enumerate(default_sentences):
                date_key = str(today - dt.timedelta(days=i))
                loaded[date_key] = sentence
        
        st.session_state.daily_sentences_tab2 = loaded
    
    # 初始化刪除狀態
    if "active_sentence_del" not in st.session_state:
        st.session_state.active_sentence_del = None
    
    # 每日清理：只保留最近14天
    dates_keep = [today - dt.timedelta(days=i) for i in range(DAYS_KEEP)]
    
    # 刪除超過14天的舊資料
    for d in list(st.session_state.daily_sentences_tab2.keys()):
        try:
            if dt.datetime.strptime(d, "%Y-%m-%d").date() not in dates_keep:
                del st.session_state.daily_sentences_tab2[d]
        except:
            pass
    
    # 清理後立即存檔
    save_daily_sentences()

    # 摺疊：新增/更新金句（可選任意日期）
    with st.expander("✏️ 新增或更新金句"):
        col1, col2, col3 = st.columns([2, 5, 1])
        with col1:
            selected_date = st.date_input("選擇日期", today, key="sentence_date_tab2")
        with col2:
            new_sentence = st.text_input("金句（中英並列）", key="new_sentence_tab2")
        with col3:
            st.write("")
            st.write("")
            if st.button("儲存", type="primary", key="save_sentence_tab2"):
                if new_sentence:
                    date_key = str(selected_date)
                    st.session_state.daily_sentences_tab2[date_key] = new_sentence
                    save_daily_sentences()
                    st.success(f"已儲存到 {selected_date}！")
                    st.rerun()
                else:
                    st.error("請輸入金句")

    # 14天條列（最新在上）
    st.markdown("##### 📖 最近14天金句列表")
    
    for d in sorted(dates_keep, reverse=True):
        date_str = str(d)
        sentence = st.session_state.daily_sentences_tab2.get(date_str, "")
        
        # 產生唯一 ID
        item_id = f"sent_{date_str}"
        
        # 三欄布局：日期、內容、操作
        c1, c2, c3 = st.columns([1, 8, 1.5], vertical_alignment="top")
        
        with c1:
            # 標記今天
            if d == today:
                st.markdown(f"**{d.strftime('%m/%d')}** 🌟")
            else:
                st.caption(f"{d.strftime('%m/%d')}")
        
        with c2:
            if sentence:
                # 顯示金句內容
                st.info(sentence)
            else:
                # 無金句時顯示提示
                st.caption("（尚無金句）")
        
        with c3:
            # 只有有金句的才顯示 💝 和垃圾桶
            if sentence:
                # 💝 點擊切換刪除模式
                if st.button("💝", key=f"heart_{item_id}"):
                    if st.session_state.active_sentence_del == item_id:
                        st.session_state.active_sentence_del = None
                    else:
                        st.session_state.active_sentence_del = item_id
                    st.rerun()
                
                # 垃圾桶（條件顯示）
                if st.session_state.active_sentence_del == item_id:
                    if st.button("🗑️", key=f"del_{item_id}"):
                        del st.session_state.daily_sentences_tab2[date_str]
                        save_daily_sentences()
                        st.session_state.active_sentence_del = None
                        st.rerun()
            else:
                # 無金句時顯示佔位符
                st.caption("—")

    # 統計與匯出
    st.divider()
    total_sentences = len([s for s in st.session_state.daily_sentences_tab2.values() if s])
    st.caption(f"已儲存 {total_sentences} / 14 天金句")
    
    col_export, col_clear = st.columns([1, 1])
    with col_export:
        if st.button("📋 匯出全部金句", key="export_tab2"):
            export_lines = []
            for d in sorted(dates_keep, reverse=True):
                date_str = str(d)
                sent = st.session_state.daily_sentences_tab2.get(date_str, "")
                if sent:
                    export_lines.append(f"{d.strftime('%m/%d')}  {sent}")
            
            if export_lines:
                export = "\n\n".join(export_lines)
                st.code(export, language="text")
            else:
                st.info("尚無金句可匯出")
    
    with col_clear:
        if st.button("🧹 清空全部", key="clear_all_tab2"):
            st.session_state.daily_sentences_tab2 = {}
            save_daily_sentences()
            st.success("已清空！")
            st.rerun()
                    
# ===================================================================
# 5. TAB3 ─ 挑戰（簡化版：直接給題目，最後給答案）
# ===================================================================
with tabs[2]:
    import csv
    from io import StringIO
    import random
    
    if 'tab3_quiz_seed' not in st.session_state:
        st.session_state.tab3_quiz_seed = random.randint(1, 1000)
        st.session_state.tab3_show_answers = False
    
    sentences = st.session_state.get('sentences', {})
    
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
        
        # 收集所有經文資料
        all_verses = []
        for ref in weighted_pool[:10]:  # 取前10筆資料
            data = sentences[ref]
            v1_content = data.get('v1_content', '')
            if v1_content:
                try:
                    lines = v1_content.strip().split('\n')
                    if lines:
                        reader = csv.DictReader(lines)
                        for row in reader:
                            all_verses.append({
                                'ref': row.get('Ref.', ''),
                                'english': row.get('English (ESV)', ''),
                                'chinese': row.get('Chinese', '')
                            })
                except:
                    pass
        
        # 隨機選6題（3題中翻英，3題英翻中）
        random.shuffle(all_verses)
        selected = all_verses[:6] if len(all_verses) >= 6 else all_verses
        
        # 分配題目
        zh_to_en = selected[:3]  # 中翻英
        en_to_zh = selected[3:6] if len(selected) > 3 else []  # 英翻中
        
        st.subheader("📝 翻譯挑戰")
        
        # ===== 題目 1-3：中翻英 =====
        for i, q in enumerate(zh_to_en, 1):
            st.markdown(f"**{i}.** {q['chinese'][:60]}")
            st.text_input("", key=f"quiz_zh_en_{i}", placeholder="請翻譯成英文...", label_visibility="collapsed")
            st.write("")
        
        # ===== 題目 4-6：英翻中 =====
        for i, q in enumerate(en_to_zh, 4):
            st.markdown(f"**{i}.** {q['english'][:100]}")
            st.text_input("", key=f"quiz_en_zh_{i}", placeholder="請翻譯成中文...", label_visibility="collapsed")
            st.write("")
        
        # ===== 單字題（3題）=====
        # 從 Syn/Ant 提取單字
        word_pool = []
        for ref in weighted_pool[:5]:
            data = sentences[ref]
            v1_content = data.get('v1_content', '')
            if v1_content:
                try:
                    lines = v1_content.strip().split('\n')
                    if lines:
                        reader = csv.DictReader(lines)
                        for row in reader:
                            syn_ant = row.get('Syn/Ant', '')
                            if '/' in syn_ant:
                                parts = syn_ant.split('/')
                                for p in parts:
                                    match = re.match(r'(.+?)\s*\((.+?)\)', p.strip())
                                    if match:
                                        word_pool.append({
                                            'en': match.group(1).strip(),
                                            'cn': match.group(2).strip()
                                        })
                except:
                    pass
        
        random.shuffle(word_pool)
        selected_words = word_pool[:3] if len(word_pool) >= 3 else word_pool
        
        for i, w in enumerate(selected_words, 7):
            st.markdown(f"**{i}.** {w['cn']}（請寫出英文）")
            st.text_input("", key=f"quiz_word_{i}", placeholder="English word...", label_visibility="collapsed")
            st.write("")
        
        # ===== 翻看答案按 =====
        col_btn, col_answer = st.columns([1, 3])
        with col_btn:
            if st.button("👁️ 翻看正確答案", use_container_width=True, type="primary"):
                st.session_state.tab3_show_answers = True
                st.rerun()
        
        with col_answer:
            if st.session_state.tab3_show_answers:
                with st.expander("📖 正確答案", expanded=True):
                    # 顯示中翻英答案
                    st.markdown("**中翻英：**")
                    for i, q in enumerate(zh_to_en, 1):
                        st.caption(f"{i}. {q['english'][:100]}")
                    
                    # 顯示英翻中答案
                    st.markdown("**英翻中：**")
                    for i, q in enumerate(en_to_zh, 4):
                        st.caption(f"{i}. {q['chinese'][:60]}")
                    
                    # 顯示單字答案
                    st.markdown("**單字：**")
                    for i, w in enumerate(selected_words, 7):
                        st.caption(f"{i}. {w['en']}")
                             
                if st.button("🔄 換一批題目", use_container_width=True):
                    st.session_state.tab3_quiz_seed = random.randint(1, 1000)
                    st.session_state.tab3_show_answers = False
                    st.rerun()
            
# ===================================================================
# 6. TAB4 ─AI 控制台 + Notion Database 整合（支援多工作表）
# ===================================================================
with tabs[3]:
    import os, json, datetime as dt, pandas as pd, urllib.parse, base64, re, csv, requests
    from io import StringIO
    import streamlit.components.v1 as components

    # ═══════════════════════════════════════════════════════════════
    # 🔒 NOTION 設定集中管理區（更新時請勿修改此區塊結構）
    # ═══════════════════════════════════════════════════════════════
    # 讀取 secrets.toml 的 [notion] 區段
    NOTION_TOKEN = ""
    DATABASE_ID = ""
    
    try:
        if "notion" in st.secrets:
            notion_cfg = st.secrets["notion"]
            NOTION_TOKEN = notion_cfg.get("token", "")
            # 優先從 secrets 讀取 database_id，沒有則使用預設值
            DATABASE_ID = notion_cfg.get("database_id", "2f910510e7fb80c4a67ff8735ea90cdf")
            
            # 驗證
            if NOTION_TOKEN and DATABASE_ID:
                st.sidebar.success(f"✅ Notion 設定載入成功")
            else:
                st.sidebar.warning(f"⚠️ Notion 設定不完整: Token={'有' if NOTION_TOKEN else '無'}, ID={'有' if DATABASE_ID else '無'}")
        else:
            st.sidebar.error("❌ secrets.toml 缺少 [notion] 區段")
            # 使用預設值讓程式能繼續執行（雖然會失敗）
            DATABASE_ID = "2f910510e7fb80c4a67ff8735ea90cdf"
    except Exception as e:
        st.sidebar.error(f"❌ 讀取 Notion 設定失敗: {e}")
        DATABASE_ID = "2f910510e7fb80c4a67ff8735ea90cdf"
    
    # 常數定義（避免魔法字串）
    NOTION_API_VERSION = "2022-06-28"
    NOTION_BASE_URL = "https://api.notion.com/v1"
    
    # ═══════════════════════════════════════════════════════════════
    # ---------- 背景圖片套用 ----------
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

    # ---------- Google Sheet 連線檢查 ----------
    sheet_connected = False
    GCP_SA = None
    SHEET_ID = None
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        GCP_SA = st.secrets.get("gcp_service_account", {})
        SHEET_ID = st.secrets.get("sheets", {}).get("spreadsheet_id", "")
        if GCP_SA and SHEET_ID:
            sheet_connected = True
    except:
        pass

    # ---------- 輔助函式 ----------
    def get_notion_text(prop_dict):
        """安全取得 Notion rich_text 內容"""
        rt = prop_dict.get("rich_text", [])
        if rt and len(rt) > 0:
            return rt[0].get("text", {}).get("content", "")
        return ""

    # ---------- Notion 核心函式 ----------
    def load_from_notion():
        """從 Notion 資料庫載入所有資料"""
        # 使用頂層定義的 NOTION_TOKEN 和 DATABASE_ID
        if not NOTION_TOKEN:
            st.sidebar.error("❌ NOTION_TOKEN 未設定，無法載入")
            return {}
        
        if not DATABASE_ID:
            st.sidebar.error("❌ DATABASE_ID 未設定")
            return {}
        
        # ✅ 修正：確保 URL 沒有空格
        url = f"{NOTION_BASE_URL}/databases/{DATABASE_ID}/query"
        
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_API_VERSION,
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
                    
                    if response.status_code != 200:
                        st.sidebar.error(f"🚫 Notion API 錯誤 ({response.status_code})")
                        try:
                            st.sidebar.json(response.json())
                        except:
                            st.sidebar.code(response.text[:300])
                        return {}

                    data = response.json()

                    for page in data.get("results", []):
                        props = page.get("properties", {})
                        ref = get_notion_text(props.get("Ref_No", {})) or "unknown"
                        translation = get_notion_text(props.get("Translation", {}))

                        v1_content = ""
                        v2_content = ""
                        if translation and "【V1 Sheet】" in translation:
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
                            "saved_sheets": ["V1", "V2"] if v1_content or v2_content else ["載入成功"]
                        }

                    has_more = data.get("has_more", False)
                    start_cursor = data.get("next_cursor")

            if all_data:
                st.sidebar.success(f"✅ 已從 Notion 載入 {len(all_data)} 筆資料")
            return all_data

        except Exception as e:
            st.sidebar.error(f"❌ 載入失敗：{e}")
            return {}

    def save_to_notion(data_dict):
        """儲存資料到 Notion"""
        if not NOTION_TOKEN:
            return False, "NOTION_TOKEN 未設定", None

        # ✅ 修正：確保 URL 沒有空格
        url = f"{NOTION_BASE_URL}/pages"
        
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_API_VERSION
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
                return False, f"API Error: {response.text}", None
        except Exception as e:
            return False, str(e), None

    # ---------- 本地資料庫 ----------
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

    # ---------- Session State 初始化 ----------
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

    # 顯示連線狀態（Sidebar）
    with st.sidebar:
        st.divider()
        st.subheader("☁️ 連線狀態")
        if NOTION_TOKEN:
            st.success("✅ Notion Token 已設定")
        else:
            st.error("❌ Notion Token 未設定")
        
        if sheet_connected:
            st.success("✅ Google Sheet 已連線")
        else:
            st.error("❌ Google Sheet 未連線")

    # ... 其餘程式碼（generate_full_prompt, UI 等）保持不變 ...

    def load_from_notion():
        # --- 強制診斷區 ---
        st.sidebar.divider()
        st.sidebar.subheader("🔧 Notion 連線診斷")
        
        if "notion" not in st.secrets:
            st.sidebar.warning("⚠️ 偵測不到 [notion] 區塊")
            st.sidebar.write(f"可用的 secrets keys: {list(st.secrets.keys())}")
            return {}
        
        token = st.secrets["notion"].get("token")
        db_id = st.secrets["notion"].get("database_id")
        
        st.sidebar.write(f"Token 存在: {bool(token)}")
        st.sidebar.write(f"Database ID 存在: {bool(db_id)}")
        
        if not token or not db_id:
            st.sidebar.error(f"🚫 憑證缺失: Token={'有' if token else '無'}, ID={'有' if db_id else '無'}")
            return {}
        
        st.sidebar.success("✅ 憑證檢查通過")
        # ----------------

        # ✅ 修正：移除 URL 中的空格（這是關鍵！）
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        st.sidebar.write(f"URL: {url[:50]}...")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        all_data = {}
        has_more = True
        start_cursor = None
        
        try:
            with st.spinner("☁️ 正在連線 Notion..."):
                while has_more:
                    payload = {"page_size": 100}
                    if start_cursor:
                        payload["start_cursor"] = start_cursor
                        
                    response = requests.post(url, headers=headers, json=payload)
                    
                    if response.status_code != 200:
                        st.sidebar.error(f"❌ Notion 拒絕連線 ({response.status_code})")
                        try:
                            error_detail = response.json()
                            st.sidebar.json(error_detail)
                        except:
                            st.sidebar.code(response.text[:300])
                        return {}

                    data = response.json()
                    
                    for page in data.get("results", []):
                        props = page.get("properties", {})
                        ref = get_notion_text(props.get("Ref_No", {})) or "unknown"
                        translation = get_notion_text(props.get("Translation", {}))

                        v1_content = ""
                        v2_content = ""
                        if translation and "【V1 Sheet】" in translation:
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
                            "saved_sheets": ["V1", "V2"] if v1_content or v2_content else ["載入成功"]
                        }

                    has_more = data.get("has_more", False)
                    start_cursor = data.get("next_cursor")

            st.sidebar.success(f"✅ 已連線：載入 {len(all_data)} 筆")
            return all_data
            
        except Exception as e:
            st.sidebar.error(f"❌ 執行異常: {e}")
            import traceback
            st.sidebar.code(traceback.format_exc())
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
5. Grammar：嚴格遵守符號化格式＋嚴格提供詳細規範如下：
   例箴17:7Fine speech is not becoming to a fool; still less is false speech to a prince.
1️⃣[分段解析+語法標籤]： 1st clause：”Fine speech" is not becoming to a fool
                    2nd clause：still less is "false speech" to a prince
   語法標籤必須標註出Grammar labels (must be identified):
   主語 (Subject)、動詞 (Verb)、補語 (Complement) 或 修飾語。
* 主語 (Subject): Fine speech（Elegant words優美的言辭/Refined talk高雅的談吐）。
* 動詞 (Verb): is (Linking verb/Copula 系動詞)。
* 形容詞Adjective/Complement補語 (Complement): becoming(Adjective meaning「fitting相稱的」or「appropriate得體的」。
* 介系詞短語(Prepositional Phrase): to a fool。(Specifies the inappropriate recipient).
   說明此不合宜的對象是「愚頑人」。
2️⃣詞性辨析Part-of-Speech Distinction： 若單字有歧義（例如 becoming 是動詞還是形容詞），
If a word has potential ambiguity (for example, becoming can be a verb or an adjective), 
請特別說明其在句中的詞性與意義。
its part of speech and meaning in this sentence must be clearly identified.
* becoming
    * Possible forms:
        * Verb (to become)
        * Adjective (suitable, fitting)
    * In this sentence: adjective
    * Meaning here: appropriate, fitting, proper

3️⃣修辭與結構Rhetoric and Structure： 識別並解釋特定的文法現象Identify and explain specific grammatical phenomena, such as:如 倒裝 (Inversion)、省略 (Ellipsis)  或遞進邏輯 (Still less / A fortiori)。
4️⃣語意解釋：This grammatical structure strengthens the verse’s logic by contrasting inner character with outer speech.
  請以 **Markdown 表格格式**輸出（非 JSON）.
  
🔹 V2 Sheet 欄位要求：
1. Ref.：同 V1.
2. 口語訳：檢索對應的日本《口語訳聖經》(1955).
3. Grammar格式同 V1
4. Note：日文文法或語境的補充說明.
5. KRF：檢索對應的韓文《Korean Revised Version》.
6. Syn/Ant：韓文高/ 中高級字（含日/韓/中翻譯）.
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

⚠️ 輸出格式要求：請使用 **Markdown 表格格式**：

 【W Sheet - 重點要求：取高級/中高級單字15個/片語15個】
| No | Word/Phrase| Chinese | Synonym | Antonym | Bible Example（Full sentence) |
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
🔹 Grammar List 詳細規範：
1. **選句標準**：從文稿中精選 6 個**最具教學價值**的句子
2. **解析深度**：每句必須提供以下解析內容
   例箴17:7Fine speech is not becoming to a fool; still less is false speech to a prince.
1️⃣[分段解析+語法標籤]： 1st clause：”Fine speech" is not becoming to a fool
                    2nd clause：still less is "false speech" to a prince
   語法標籤必須標註出Grammar labels (must be identified):
   主語 (Subject)、動詞 (Verb)、補語 (Complement) 或 修飾語。
* 主語 (Subject): Fine speech（Elegant words優美的言辭/Refined talk高雅的談吐）。
* 動詞 (Verb): is (Linking verb/Copula 系動詞)。
* 形容詞Adjective/Complement補語 (Complement): becoming(Adjective meaning「fitting相稱的」or「appropriate得體的」。
* 介系詞短語(Prepositional Phrase): to a fool。(Specifies the inappropriate recipient).
   說明此不合宜的對象是「愚頑人」。
2️⃣詞性辨析Part-of-Speech Distinction： 若單字有歧義（例如 becoming 是動詞還是形容詞），
If a word has potential ambiguity (for example, becoming can be a verb or an adjective), 
請特別說明其在句中的詞性與意義。
its part of speech and meaning in this sentence must be clearly identified.
* becoming
    * Possible forms:
        * Verb (to become)
        * Adjective (suitable, fitting)
    * In this sentence: adjective
    * Meaning here: appropriate, fitting, proper

3️⃣修辭與結構Rhetoric and Structure： 識別並解釋特定的文法現象Identify and explain specific grammatical phenomena, 
   such as:如 倒裝 (Inversion)、省略 (Ellipsis)  或遞進邏輯 (Still less / A fortiori)。
4️⃣語意解釋： This grammatical structure strengthens the verse’s logic by contrasting inner character with outer speech.
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

    # ---------- 📝 主要功能區（標題縮小為 h6）----------
    st.markdown("<h6>📝 AI 分析工作流程</h6>", unsafe_allow_html=True)
    
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


        # === STEP 4: 統一儲存區（修正縮排：在 if 區塊內）===
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
                # 存到 Google Sheet（使用外面定義的 sheet_connected）
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

            # 清除按鈕
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

    # ---------- 📊 儲存狀態顯示區（字體縮小版，在 if 區塊外面）----------
    st.divider()
    status_cols = st.columns([1, 1, 1, 2])
    
    with status_cols[0]:
        total_local = len(st.session_state.get('sentences', {}))
        st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>💾 本地資料庫</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 16px; font-weight: bold; margin: 0;'>{total_local} 筆</p>", unsafe_allow_html=True)
    
    with status_cols[1]:
        if NOTION_TOKEN:
            st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>☁️ Notion</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 16px; font-weight: bold; margin: 0; color: #28a745;'>✅ 已連線</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>☁️ Notion</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 16px; font-weight: bold; margin: 0; color: #dc3545;'>❌ 未設定</p>", unsafe_allow_html=True)
    
    with status_cols[2]:
        if sheet_connected:
            st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>📊 Google</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 16px; font-weight: bold; margin: 0; color: #28a745;'>✅ 已連線</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>📊 Google</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 16px; font-weight: bold; margin: 0; color: #dc3545;'>❌ 未設定</p>", unsafe_allow_html=True)
    
    with status_cols[3]:
        # 顯示最近儲存的資料
        if st.session_state.get('sentences'):
            recent = list(st.session_state.sentences.values())[-3:]
            st.markdown(f"<p style='font-size: 12px; margin: 0; color: #666;'>🕐 最近儲存：</p>", unsafe_allow_html=True)
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

    # ---------- 底部統計（移除重複的備份下載）----------
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

