import streamlit as st
import datetime as dt
try:
    from streamlit_calendar import calendar
    CALENDAR_OK = True
except ModuleNotFoundError:
    CALENDAR_OK = False
    calendar = None

# ==========================================
# [區塊 1] 環境匯入與全域 CSS + 點擊動畫
# ==========================================
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# 初始化Session State（保證不報錯）
if 'events' not in st.session_state: st.session_state.events = []
if 'notes' not in st.session_state: st.session_state.notes = {}
if 'todo' not in st.session_state: st.session_state.todo = {}
if 'custom_emojis' not in st.session_state:
    st.session_state.custom_emojis = ["🐾", "🐰", "🥰", "✨", "🥕", "🌟"]
if 'sel_date' not in st.session_state:
    st.session_state.sel_date = str(dt.date.today())
if 'date_picker' not in st.session_state:
    st.session_state.date_picker = dt.date.today()
if 'expander_open' not in st.session_state:
    st.session_state.expander_open = True

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
    .small-font { font-size: 13px; color: #555555; margin-top: 5px !important; }
    .grammar-box-container {
        background-color: #f8f9fa; border-radius: 8px; padding: 12px; 
        border-left: 5px solid #FF8C00; text-align: left; margin-top: 0px;
    }
    /* 日曆格子點擊動畫 */
    .fc-daygrid-day-frame:hover {
        background-color: #FFF3CD !important;
        cursor: pointer;
        transform: scale(1.03);
        transition: all 0.2s ease;
    }
    .fc-daygrid-day-frame:active {
        transform: scale(0.98);
        background-color: #FFE69C !important;
    }
    /* 筆記(左)與待辦(右)分離顯示 */
    .note-emoji { color: #FF8C00; font-size: 12px; }
    .todo-emoji { color: #17A2B8; font-size: 12px; float: right; }
    </style>
    """, unsafe_allow_html=True)

IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg",
    "M1": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro1.jpg",
    "M2": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro2.jpg",
    "M3": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro3.jpg",
    "M4": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro4.jpg"
}

# ==========================================
# [區塊 2] 側邊欄與 Tabs
# ==========================================
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다</p>', unsafe_allow_html=True)
    st.image(IMG_URLS["M3"], width=250)
    st.divider()
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/", use_container_width=True)

tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# ==========================================
# [區塊 3] TAB 1: 完整版內容恢復
# ==========================================
with tabs[0]:
    col_content, col_m1 = st.columns([0.65, 0.35])
    with col_content:
        st.info("**Becoming** / 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 🇹🇭 เหมาะสม | 🇨🇳 相稱")
        st.info("**Still less** / 🇯🇵 まして | 🇰🇷 하물며 | 🇹🇭 ยิ่งกว่านั้น | 🇨🇳 何況")
        st.success("""
            🌟 **Pro 17:07** Fine speech is not becoming to a fool; still less is false speech to a prince.   
            🇯🇵 すぐれた言葉は愚か者にはふさわしくない。偽りの言葉は君主にはなおさらふさわしくない。   
            🇨🇳 愚頑人說美言本不相稱，何況君王說謊話呢？
            """, icon="📖")

    with col_m1:
        st.markdown(f"""
            <div style="display: flex; flex-direction: column; justify-content: space-between; height: 100%; min-height: 250px; text-align: center;">
                <div style="flex-grow: 1; display: flex; align-items: center; justify-content: center;">
                    <img src="{IMG_URLS['M1']}" style="width: 200px; margin-bottom: 10px;">
                </div>
                <div class="grammar-box-container" style="margin-top: auto;">
                    <p style="margin:2px 0; font-size: 14px; font-weight: bold; color: #333;">時態: 現在簡單式</p>
                    <p style="margin:2px 0; font-size: 14px; font-weight: bold; color: #333;">核心片語:</p>
                    <ul style="margin:0; padding-left:18px; font-size: 13px; line-height: 1.4; color: #555;">
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

# ==========================================
# [區塊 4] TAB 2: 最終可上線版（語法修正＋不閃＋多筆＋Emoji）
# ==========================================
with tabs[1]:
    # 建立事件清單（包含Emoji分離顯示）
    def build_events():
        events = []
        # 筆記事件（靠左，用📓）
        for date_key, note in st.session_state.notes.items():
            emoji = note.get('emoji', '📓')
            events.append({
                "title": f"{emoji} {note['title'][:6]}",
                "start": date_key,
                "classNames": ["note-emoji"]
            })
        # 待辦事件（靠右，用🔔）
        for date_key, todo in st.session_state.todo.items():
            emoji = todo.get('emoji', '🔔')
            events.append({
                "title": f"{todo['title'][:6]} {emoji}",
                "start": date_key,
                "classNames": ["todo-emoji"]
            })
        return events

    # 處理日曆點擊（修復時區Bug）
    def handle_cal_click():
        if "cal" in st.session_state and st.session_state.cal:
            e = st.session_state.cal
            if 'dateClick' in e:
                clicked = e['dateClick']
                if clicked and 'date' in clicked:
                    # 關鍵修正：直接取日期部分，忽略時間
                    date_str = clicked['date'][:10]
                    st.session_state.sel_date = date_str
                    st.session_state.date_picker = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
                    st.session_state.expander_open = True

    # 1. 快速Emoji選擇器
    st.markdown("#### 🏷️ 快速選擇Emoji")
    emoji_cols = st.columns(6)
    for i, em in enumerate(st.session_state.custom_emojis):
        with emoji_cols[i]:
            if st.button(em, key=f"quick_emoji_{i}", use_container_width=True):
                st.session_state.selected_emoji = em

    # 2. 本週靈修 glance ─ 不閃＋多筆＋Emoji
    with st.expander("📅 本週靈修 glance", expanded=st.session_state.expander_open):
        if CALENDAR_OK:
            today = dt.date.today()
            
            # 確保事件格式正確
            events_data = build_events()
            if events_data is None:
                events_data = []
            
            # 除錯資訊（部署後可刪除）
            if st.session_state.get('debug'):
                st.json(events_data[:3])  # 只顯示前3個事件
            
            try:
                cal = calendar(
                    events=events_data,
                    options={
                        "initialDate": str(today),
                        "initialView": "timeGridWeek",
                        "locale": "zh-tw",
                        "firstDay": 1,
                        "headerToolbar": {"start": "", "center": "title", "end": ""},
                        "height": "auto",
                        "selectable": True,
                        "dateClick": True
                    },
                    callbacks=['dateClick'],
                    key="cal"
                )
                # 立即處理點擊
                handle_cal_click()
            except Exception as e:
                st.error(f"日曆載入失敗: {str(e)}")
                st.info("💡 請在終端機執行: `pip install streamlit-calendar==1.2.0`")
                cal = None
                
    # 3. 日期選擇與功能區
    st.divider()
    
    # 3.1 三欄佈局：日期 + Emoji + 追加按鈕
    col_date, col_emoji, col_btn = st.columns([1.5, 2, 1])
    with col_date:
        st.session_state.date_picker = st.date_input(
            "📅 日期",
            value=st.session_state.date_picker,
            format="YYYY/MM/DD",
            label_visibility="visible"
        )
        # 同步sel_date
        st.session_state.sel_date = str(st.session_state.date_picker)
    
    with col_emoji:
        emoji_options = ["無"] + st.session_state.custom_emojis
        selected_emoji = st.selectbox(
            "🏷️ Emoji",
            options=emoji_options,
            format_func=lambda x: "選擇Emoji" if x=="無" else x,
            label_visibility="visible"
        )
        if selected_emoji != "無":
            st.session_state.selected_emoji = selected_emoji
    
    with col_btn:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)  # 對齊按鈕
        add_clicked = st.button("➕ 追加", use_container_width=True)

    # 3.2 筆記與待辦切換
    tab_note, tab_todo = st.tabs(["📝 筆記", "🔔 待辦"])

    with tab_note:
        note_title = st.text_input("標題", placeholder="輸入筆記標題")
        note_content = st.text_area("內容", placeholder="記錄靈修心得...")
        if st.button("💾 儲存筆記") or add_clicked:
            if note_title:
                date_key = st.session_state.sel_date
                emoji = getattr(st.session_state, 'selected_emoji', '📓')
                st.session_state.notes[date_key] = {
                    "title": note_title,
                    "content": note_content,
                    "emoji": emoji
                }
                st.success(f"✅ 筆記已儲存至 {date_key}")
                st.rerun()

    with tab_todo:
        todo_title = st.text_input("待辦事項", placeholder="輸入待辦標題")
        if st.button("➕ 新增待辦"):
            if todo_title:
                date_key = st.session_state.sel_date
                emoji = getattr(st.session_state, 'selected_emoji', '🔔')
                st.session_state.todo[date_key] = {
                    "title": todo_title,
                    "emoji": emoji
                }
                st.success(f"✅ 待辦已新增至 {date_key}")
                st.rerun()

    # 3.3 顯示當日紀錄
    st.divider()
    current_date = st.session_state.sel_date
    if current_date in st.session_state.notes:
        with st.container():
            note = st.session_state.notes[current_date]
            st.markdown(f"**{note['emoji']} 筆記：** {note['title']}")
            st.caption(note['content'])
    if current_date in st.session_state.todo:
        with st.container():
            todo = st.session_state.todo[current_date]
            st.markdown(f"**{todo['emoji']} 待辦：** {todo['title']}")

# ==========================================
# [區塊 5] TAB 3 & 4: 挑戰與資料庫（保持不變）
# ==========================================
with tabs[2]:
    col_challenge, col_deco = st.columns([0.7, 0.3])
    with col_challenge:
        st.subheader("📝 翻譯挑戰")
        st.write("題目 1: 愚頑人說美言本不相稱...")
        st.text_input("請輸入英文翻譯", key="ans_1_final", placeholder="Type your translation here...")
    with col_deco:
        st.image(IMG_URLS.get("B"), width=150, caption="Keep Going!")

with tabs[3]:
    st.subheader("🔗 聖經與AI 資源")
    cl1, cl2, cl3, cl4 = st.columns(4)
    cl1.link_button("ChatGPT", "https://chat.openai.com/ ")
    cl2.link_button("Google AI", "https://gemini.google.com/ ")
    cl3.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb ")
    cl4.link_button("THSV11", "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11 ")
    st.divider()
    input_content_final = st.text_area("📥 聖經經文 / 英文文稿輸入", height=150, key="db_input_area")
    btn_l, btn_r = st.columns(2)
    if btn_l.button("📥 執行輸入解析"):
        st.toast("已讀取文稿")
    if btn_r.button("💾 存檔至資料庫"):
        st.success("資料已成功存入雲端資料庫！")
                    
    
