# ===================================================================
# 0. 套件 & 全域函式（一定放最頂）
# ===================================================================
import streamlit as st  # ← 這裡已經有了
import subprocess, sys, os, datetime as dt, pandas as pd, io, json, re, tomli, tomli_w
from streamlit_calendar import calendar
import streamlit.components.v1 as components
import requests

token = "secret_ntn_j43799613399XOBBQtD54MQzAvMvU2CMzpZKwrLfg8M0Vx"
database_id = "2f910510e7fb80c4a67ff8735ea90cdf"

headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28"
}

response = requests.get(
    f"{{<https://api.notion.com/v1/databases/{database_id}>}}",
    headers=headers
)

print(f"狀態碼: {response.status_code}")
print(f"回應內容: {response.json()}")

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
# 3. TAB1 ─ 書桌（單字/片語/金句/文法，每小時自動輪換）
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
        
        v1_content = selected_data.get('v1_content', '')
        v1_rows = []
        if v1_content:
            try:
                lines = v1_content.strip().split('\n')
                if lines:
                    reader = csv.DictReader(lines)
                    v1_rows = list(reader)
            except:
                pass
        
        selected_verse = random.choice(v1_rows) if v1_rows else {}
        
        col_content, col_info = st.columns([0.65, 0.35])
        
        with col_content:
            ref = selected_verse.get('Ref.', 'Pro 17:7')
            english = selected_verse.get('English (ESV)', '')
            chinese = selected_verse.get('Chinese', '')
            
            st.info(f"**{ref}** / 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 🇹🇭 เหมาะสม | 🇨🇳 相稱")
            st.success(f"""
                🌟 **{ref}** {english}  
                🇨🇳 {chinese}
                """, icon="📖")
            
            st.divider()
            
            # ===== 單字提取（從 Syn/Ant）=====
            syn_ant = selected_verse.get('Syn/Ant', '')
            word_pair = syn_ant.split('/') if '/' in syn_ant else [syn_ant, '']
            
            word_1 = word_pair[0].strip() if len(word_pair) > 0 else ''
            match_1 = re.match(r'(.+?)\s*\((.+?)\)', word_1)
            if match_1:
                word_en = match_1.group(1).strip()
                word_cn = match_1.group(2).strip()
            else:
                word_en = word_1
                word_cn = ''
            
            word_2 = word_pair[1].strip() if len(word_pair) > 1 else ''
            match_2 = re.match(r'(.+?)\s*\((.+?)\)', word_2)
            if match_2:
                ant_en = match_2.group(1).strip()
                ant_cn = match_2.group(2).strip()
            else:
                ant_en = word_2
                ant_cn = ''
            
            st.markdown("### 📝 今日單字")
            col_word1, col_word2 = st.columns(2)
            with col_word1:
                st.markdown(f"**{word_en}**")
                st.caption(f"{word_cn}")
            with col_word2:
                if ant_en:
                    st.markdown(f"<span style='color:#dc3545;'>**{ant_en}**</span>", unsafe_allow_html=True)
                    st.caption(f"{ant_cn} (反義)")
            
            # ===== 片語/文法結構 =====
            grammar = selected_verse.get('Grammar', '')
            structure = ''
            if '2️⃣[' in grammar:
                structure_match = re.search(r'2️⃣\[(.+?)\]', grammar)
                if structure_match:
                    structure = structure_match.group(1)
            else:
                structure = grammar[:80]
            
            st.markdown("### 🔤 文法結構")
            st.markdown(f"`{structure}`")
        
        with col_info:
            st.markdown("### 📚 文法解析")
            analysis = ''
            if '1️⃣[' in grammar:
                analysis_match = re.search(r'1️⃣\[(.+?)\]', grammar)
                if analysis_match:
                    analysis = analysis_match.group(1)
            
            st.markdown(f"""
                <div style="background-color:#f8f9fa;border-radius:8px;padding:12px;border-left:5px solid #FF8C00;">
                    <p style="margin:2px 0;font-size:13px;font-weight:bold;color:#333;">{analysis[:100]}</p>
                    <hr style="margin:8px 0;">
                    <p style="margin:2px 0;font-size:11px;color:#666;">來源: {selected_ref}</p>
                    <p style="margin:2px 0;font-size:11px;color:#666;">下次更新: {((3600 - time_diff) / 60):.0f} 分鐘後</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # ===== 文法運用例句（從 3️⃣Ex. 提取，若無則用聖經經文）=====
        st.markdown("### ✍️ 文法運用例句")
        
        example_sentences = []
        if '3️⃣Ex.' in grammar:
            ex_part = grammar.split('3️⃣Ex.')[-1].strip()
            ex_sentences = re.split(r'[;；]', ex_part)
            for ex in ex_sentences[:2]:
                ex = ex.strip()
                if ex:
                    ex = re.sub(r'[\[\]]', '', ex)
                    example_sentences.append(ex)
        
        # 若無 Ex.，用聖經經文作為預設例句
        if len(example_sentences) < 2:
            example_sentences = [
                english,
                chinese
            ]
        
        cl1, cl2 = st.columns(2)
        with cl1:
            st.markdown(f"**Ex 1:** *{example_sentences[0][:120]}*")
        with cl2:
            if len(example_sentences) > 1:
                st.markdown(f"**Ex 2:** *{example_sentences[1][:120]}*")
            else:
                st.markdown(f"**Ex 2:** *{chinese}*")
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
        
        # ===== 片語題（3題）=====
        # 從 Grammar 提取結構
        phrase_pool = []
        for ref in weighted_pool[:5]:
            data = sentences[ref]
            v1_content = data.get('v1_content', '')
            if v1_content:
                try:
                    lines = v1_content.strip().split('\n')
                    if lines:
                        reader = csv.DictReader(lines)
                        for row in reader:
                            grammar = row.get('Grammar', '')
                            if '2️⃣[' in grammar:
                                match = re.search(r'2️⃣\[(.+?)\]', grammar)
                                if match:
                                    phrase_pool.append({
                                        'structure': match.group(1),
                                        'ref': row.get('Ref.', '')
                                    })
                except:
                    pass
        
        random.shuffle(phrase_pool)
        selected_phrases = phrase_pool[:3] if len(phrase_pool) >= 3 else phrase_pool
        
        for i, p in enumerate(selected_phrases, 10):
            st.markdown(f"**{i}.** 請用「{p['structure'][:50]}」造一個句子")
            st.text_area("", key=f"quiz_phrase_{i}", placeholder="Make a sentence...", label_visibility="collapsed", height=68)
            st.write("")
        
        st.divider()
        
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
                    
                    # 顯示片語答案
                    st.markdown("**片語參考：**")
                    for i, p in enumerate(selected_phrases, 10):
                        st.caption(f"{i}. {p['ref']}: {p['structure'][:50]}...")
                
                if st.button("🔄 換一批題目", use_container_width=True):
                    st.session_state.tab3_quiz_seed = random.randint(1, 1000)
                    st.session_state.tab3_show_answers = False
                    st.rerun()
            
# ===================================================================
# 6. TAB4 ─AI 控制台 + Notion Database 整合（修正版）
# ===================================================================
with tabs[3]:
    import os, json, datetime as dt, pandas as pd, urllib.parse, base64, re, csv
    from io import StringIO
    import streamlit.components.v1 as components

    # ---------- 1. Notion API 設定 ----------
    NOTION_TOKEN = ""
    try:
        NOTION_TOKEN = st.secrets["notion"]["token"]
    except:
        try:
            NOTION_TOKEN = st.secrets.get("notion", {}).get("token", "")
        except:
            pass
    
    DATABASE_ID = "2f910510e7fb80c4a67ff8735ea90cdf"
    
    # 顯示 Token 狀態（除錯用）
    with st.sidebar:
        st.write("=== Notion 除錯 ===")
        if NOTION_TOKEN:
            st.success(f"Token 長度: {len(NOTION_TOKEN)}")
            st.write(f"Token 前20: {NOTION_TOKEN[:20]}...")
        else:
            st.error("Token 未讀取")
            st.write(f"Secrets keys: {list(st.secrets.keys())}")
            try:
                st.write(f"notion 內容: {st.secrets.get('notion', {})}")
            except:
                pass

    # ---------- 2. 測試 API 連線（詳細版）----------
    if NOTION_TOKEN:
        import requests
        
        # 測試 1: 驗證 Token
        try:
            test_response = requests.get(
                "https://api.notion.com/v1/users/me",
                headers={
                    "Authorization": f"Bearer {NOTION_TOKEN}",
                    "Notion-Version": "2022-06-28"
                },
                timeout=10
            )
            
            with st.sidebar:
                st.write(f"Token 測試狀態碼: {test_response.status_code}")
                
                if test_response.status_code == 200:
                    user_name = test_response.json().get('name', 'Unknown')
                    st.success(f"✅ Token 有效: {user_name}")
                else:
                    st.error(f"❌ Token 無效: {test_response.text[:200]}")
                    
        except Exception as e:
            with st.sidebar:
                st.error(f"❌ Token 測試失敗: {str(e)}")
        
        # 測試 2: 驗證 Database
        try:
            db_response = requests.get(
                f"https://api.notion.com/v1/databases/{DATABASE_ID}",
                headers={
                    "Authorization": f"Bearer {NOTION_TOKEN}",
                    "Notion-Version": "2022-06-28"
                },
                timeout=10
            )
            
            with st.sidebar:
                st.write(f"Database 測試狀態碼: {db_response.status_code}")
                
                if db_response.status_code == 200:
                    db_title = db_response.json().get('title', [{}])[0].get('text', {}).get('content', 'Unknown')
                    st.success(f"✅ Database 可存取: {db_title}")
                elif db_response.status_code == 404:
                    st.error("❌ Database 不存在或 ID 錯誤")
                elif db_response.status_code == 403:
                    st.error("❌ 無權限存取 Database（Integration 未連結）")
                else:
                    st.error(f"❌ Database 錯誤: {db_response.text[:200]}")
                    
        except Exception as e:
            with st.sidebar:
                st.error(f"❌ Database 測試失敗: {str(e)}")

    # ---------- 3. Notion 函數 ----------
    def save_to_notion(data_dict):
        """儲存到 Notion"""
        if not NOTION_TOKEN:
            return False, "Token 未設定", None
        
        try:
            import requests
            
            url = "https://api.notion.com/v1/pages"
            headers = {
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            # 簡化內容，避免格式問題
            content_preview = data_dict.get('original', '')[:100]
            
            properties = {
                "Content": {
                    "title": [{"text": {"content": content_preview}}]
                },
                "Ref_No": {
                    "rich_text": [{"text": {"content": data_dict.get("ref", "N/A")}}]
                },
                "Type": {
                    "select": {"name": data_dict.get("type", "Scripture")}
                },
                "Source_Mode": {
                    "select": {"name": data_dict.get("mode", "Mode A")}
                },
                "Date_Added": {
                    "date": {"start": dt.datetime.now().isoformat()}
                }
            }
            
            # 選填欄位：Translation（如果內容太長會失敗，先不填）
            v1 = data_dict.get('v1_content', '')[:500]
            if v1:
                properties["Translation"] = {
                    "rich_text": [{"text": {"content": v1}}]
                }
            
            payload = {
                "parent": {"database_id": DATABASE_ID},
                "properties": properties
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                page_id = response.json().get("id")
                return True, "成功", page_id
            else:
                error_detail = response.json() if response.text else "無詳細錯誤"
                return False, f"API 錯誤 {response.status_code}: {error_detail}", None
                
        except Exception as e:
            return False, f"例外錯誤: {str(e)}", None

    # ---------- 4. 本地資料庫 ----------
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

    # ---------- 5. 初始化 session_state ----------
    if 'sentences' not in st.session_state:
        st.session_state.sentences = load_sentences()
    if 'is_prompt_generated' not in st.session_state:
        st.session_state.is_prompt_generated = False
    if 'main_input_value' not in st.session_state:
        st.session_state.main_input_value = ""
    if 'original_text' not in st.session_state:
        st.session_state.original_text = ""
    if 'content_mode' not in st.session_state:
        st.session_state.content_mode = ""
    if 'ref_number' not in st.session_state:
        st.session_state.ref_number = ""
    if 'current_entry' not in st.session_state:
        st.session_state.current_entry = {'v1': '', 'v2': '', 'other': ''}
    if 'saved_entries' not in st.session_state:
        st.session_state.saved_entries = []

    # ---------- 6. 偵測內容類型 ----------
    def detect_content_mode(text):
        text = text.strip()
        if not text:
            return "document"
        if text.startswith("{"):
            return "json"
        if re.search(r'[\u4e00-\u9fa5]', text):
            return "scripture"
        return "document"

    # ---------- 7. 產生 Prompt ----------
    def generate_full_prompt():
        raw_text = st.session_state.get("raw_input_temp", "").strip()
        if not raw_text:
            st.warning("請先貼上內容")
            return
        
        mode = detect_content_mode(raw_text)
        
        if mode == "scripture":
            full_prompt = f"""你是一位聖經專家。請分析以下經文，產出 V1 + V2 Excel 格式（Markdown 表格）。

待分析經文：{raw_text}"""
            st.session_state.content_mode = "A"
        else:
            full_prompt = f"""你是一位語言學教授。請分析以下文稿，產出 W + P + Grammar List Excel 格式（Markdown 表格）。

待分析文稿：{raw_text}"""
            st.session_state.content_mode = "B"

        st.session_state.original_text = raw_text
        st.session_state.main_input_value = full_prompt
        st.session_state.is_prompt_generated = True
        st.session_state.ref_number = f"REF_{dt.datetime.now().strftime('%m%d%H%M')}"
        st.session_state.current_entry = {'v1': '', 'v2': '', 'other': ''}
        st.session_state.saved_entries = []

    # ---------- 8. UI 介面 ----------
    st.header("📝 AI 分析工作流程")
    
    # 步驟 1
    with st.expander("步驟 1：輸入內容", expanded=not st.session_state.is_prompt_generated):
        st.text_area(
            "原始輸入",
            height=200,
            placeholder="貼上經文或文稿...",
            key="raw_input_temp"
        )
        
        if not st.session_state.is_prompt_generated:
            if st.button("⚡ 產生分析指令", type="primary"):
                generate_full_prompt()
                st.rerun()

    # 步驟 2
    if st.session_state.is_prompt_generated:
        with st.expander("步驟 2：複製到 AI"):
            st.text_area("Prompt", value=st.session_state.main_input_value, height=250, disabled=True)
            
            cols = st.columns(3)
            with cols[0]:
                encoded = urllib.parse.quote(st.session_state.main_input_value)
                st.link_button("💬 GPT", f"https://chat.openai.com/?q={encoded}")
            with cols[1]:
                st.link_button("🌙 Kimi", "https://kimi.com")
            with cols[2]:
                st.link_button("🔍 Gemini", "https://gemini.google.com")

        # 步驟 3
        with st.expander("步驟 3：貼上 AI 結果", expanded=True):
            sheet = st.selectbox("選擇工作表", ["V1 Sheet", "V2 Sheet", "其他"])
            content = st.text_area("內容", height=200)
            
            if st.button("➕ 暫存"):
                key_map = {"V1 Sheet": "v1", "V2 Sheet": "v2", "其他": "other"}
                key = key_map.get(sheet, "other")
                st.session_state.current_entry[key] = content
                if sheet not in st.session_state.saved_entries:
                    st.session_state.saved_entries.append(sheet)
                st.success(f"✅ {sheet} 已暫存")
                st.rerun()
            
            if st.session_state.saved_entries:
                st.write("已暫存：", " | ".join(st.session_state.saved_entries))

        # 步驟 4
        with st.expander("步驟 4：儲存", expanded=True):
            ref_input = st.text_input("Ref_No", value=st.session_state.ref_number)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 存本地"):
                    ref = ref_input or st.session_state.ref_number
                    data = {
                        "ref": ref,
                        "original": st.session_state.original_text,
                        "v1_content": st.session_state.current_entry['v1'],
                        "v2_content": st.session_state.current_entry['v2'],
                        "saved_sheets": st.session_state.saved_entries,
                        "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.session_state.sentences[ref] = data
                    save_sentences(st.session_state.sentences)
                    st.success(f"✅ 已存本地：{ref}")
            
            with col2:
                if NOTION_TOKEN:
                    if st.button("🚀 存 Notion", type="primary"):
                        data = {
                            "original": st.session_state.original_text,
                            "v1_content": st.session_state.current_entry['v1'],
                            "ref": ref_input or st.session_state.ref_number,
                            "type": "Scripture",
                            "mode": f"Mode {st.session_state.content_mode}"
                        }
                        success, msg, page_id = save_to_notion(data)
                        if success:
                            st.success(f"✅ 已存 Notion：{page_id[:8]}...")
                        else:
                            st.error(f"❌ 失敗：{msg}")
                else:
                    st.button("🚀 存 Notion", disabled=True)

    # 顯示統計
    st.divider()
    st.write(f"💾 本地資料：{len(st.session_state.sentences)} 筆")
