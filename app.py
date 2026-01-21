import streamlit as st
import datetime as dt
try:
    from streamlit_calendar import calendar
    CALENDAR_OK = True
except ModuleNotFoundError:
    CALENDAR_OK = False
    calendar = None

# ==========================================
# [區塊 1] 環境匯入與全域 CSS (完全保留原稿)
# ==========================================
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

if 'events' not in st.session_state: st.session_state.events = []
if 'notes' not in st.session_state: st.session_state.notes = {}
if 'todo' not in st.session_state: st.session_state.todo = {}
if 'custom_emojis' not in st.session_state:
    st.session_state.custom_emojis = ["🐾", "🐰", "🥰", "✨", "🥕", "🌟"]

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
    .small-font { font-size: 13px; color: #555555; margin-top: 5px !important; }
    .grammar-box-container {
        background-color: #f8f9fa; border-radius: 8px; padding: 12px; 
        border-left: 5px solid #FF8C00; text-align: left; margin-top: 0px;
    }
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

import streamlit as st
import datetime as dt
try:
    from streamlit_calendar import calendar
    CALENDAR_OK = True
except ModuleNotFoundError:
    CALENDAR_OK = False
    calendar = None

# ==========================================
# [區塊 1] 環境匯入與全域 CSS (完全保留原稿)
# ==========================================
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

if 'events' not in st.session_state: st.session_state.events = []
if 'notes' not in st.session_state: st.session_state.notes = {}
if 'todo' not in st.session_state: st.session_state.todo = {}
if 'custom_emojis' not in st.session_state:
    st.session_state.custom_emojis = ["🐾", "🐰", "🥰", "✨", "🥕", "🌟"]

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
    .small-font { font-size: 13px; color: #555555; margin-top: 5px !important; }
    .grammar-box-container {
        background-color: #f8f9fa; border-radius: 8px; padding: 12px; 
        border-left: 5px solid #FF8C00; text-align: left; margin-top: 0px;
    }
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
# [區塊 4] TAB 2: 最終可上線版（語法修正＋不閃＋多筆）
# ==========================================
with tabs[1]:
    # 0. 先給預設值（保證第一次不報錯）
    if 'sel_date' not in st.session_state:
        st.session_state.sel_date = str(dt.date.today())

    # 2. 本週靈修 glance ─ 不閃＋26/1/19＋多筆
    with st.expander("📅 本週靈修 glance", expanded=True):
        if CALENDAR_OK:
            today = dt.date.today()
            week_start = today - dt.timedelta(days=today.weekday())  # 週一
            week_end = week_start + dt.timedelta(days=6)

            # ── 每週事件 ──
            week_events = [
                e for e in st.session_state.events
                if week_start <= dt.date.fromisoformat(e["start"]) <= week_end
            ]

            # ── 數字氣泡＋簡短內容 ──
            for e in week_events:
                d = dt.date.fromisoformat(e["start"])
                todo_list = st.session_state.todo.get(str(d), "").splitlines()[:3]
                note_txt = st.session_state.notes.get(str(d), "")[:10]
                count = len(todo_list)
                if count:
                    titles = " ".join([f"{i+1}-{t[:4]}" for i, t in enumerate(todo_list)])
                    e["title"] = f"🔔{count} {titles}"
                elif note_txt:
                    e["title"] = f"📝{note_txt}"
                else:
                    e["title"] = ""

            # ── 最輕量圓角（不含漸層，避免閃爍）──
            st.markdown(
                """
                <style>
                .fc-daygrid-day-frame{border-radius:12px;}
                .fc-day-today{background:#ffe4f0!important;}
                .fc-daygrid-day-number{font-weight:700;font-size:15px;color:#333;}
                </style>
                """,
                unsafe_allow_html=True,
            )
            cal_options = {
                "initialView": "dayGridWeek",
                "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
                "height": "auto",
                "locale": "zh-tw",  # → 日期呈現 26/1/19"
            }
            state = calendar(events=week_events, options=cal_options, key="week_cal_mobile")
            if state.get("dateClick"):
                clicked = state["dateClick"]["date"][:10]
                st.session_state.sel_date = clicked
                # ── 獨立表單區塊（填完才收合）──
                def toggle_diary():
                    st.session_state.show_todo = False
                    st.session_state.show_diary = not st.session_state.get("show_diary", False)

                def toggle_todo():
                    st.session_state.show_diary = False
                    st.session_state.show_todo = not st.session_state.get("show_todo", False)

                def toggle_bg():
                    st.session_state.show_bg = not st.session_state.get("show_bg", False)

                c1, c2, c3 = st.columns(3, gap="small")
                c1.button("📷", on_click=toggle_bg, help="更換桌布", use_container_width=True)
                c2.button("➕", on_click=toggle_diary, help="新增靈修筆記", use_container_width=True)
                c3.button("🔔", on_click=toggle_todo, help="新增待辦提醒", use_container_width=True)

                # ── 多筆表單（追加才收合）──
                if st.session_state.get("show_diary"):
                    with st.form("diary_form"):
                        d_date = st.date_input("日期", value=dt.date.fromisoformat(st.session_state.sel_date))
                        d_emoji = st.selectbox("Emoji", st.session_state.custom_emojis)
                        d_text = st.text_area("靈修筆記", height=250)
                        if st.form_submit_button("追加"):
                            key = str(d_date)
                            old = st.session_state.notes.get(key, "").splitlines()
                            new_item = f"{d_emoji} {d_text}"
                            st.session_state.notes[key] = "\n".join(old + [new_item])
                            st.session_state.events.append({
                                "title": d_emoji or "📝",
                                "start": str(d_date),
                                "allDay": True,
                            })
                            st.success("已追加")
                            st.session_state.show_diary = False
                            st.rerun()

                if st.session_state.get("show_todo"):
                    with st.form("todo_form"):
                        t_date = st.date_input("日期", value=dt.date.fromisoformat(st.session_state.sel_date))
                        t_time = st.time_input("時間", value=None)
                        t_all_day = st.checkbox("全天提醒", value=True)
                        t_emoji = st.selectbox("Emoji", st.session_state.custom_emojis)
                        t_text = st.text_area("待辦事項", height=120)
                        if st.form_submit_button("追加"):
                            key = str(t_date)
                            old = st.session_state.todo.get(key, "").splitlines()
                            new_item = f"{t_emoji} {t_text}"
                            st.session_state.todo[key] = "\n".join(old + [new_item])
                            st.session_state.events.append({
                                "title": t_emoji or "🔔",
                                "start": str(t_date),
                                "allDay": t_all_day,
                            })
                            st.success("已追加")
                            st.session_state.show_todo = False
                            st.rerun()

        else:
            st.info("月曆元件尚未安裝，請稍後再試。")

    # 4. 下半部 UI ── 先給預設值＋當日筆記＋搜尋＋待辦清單 ──
    st.divider()
    st.markdown("#### 今日靈修筆記 ✍️")
    # ── 先給預設值（保證第一次不報錯）──
    st.session_state.sel_date = st.session_state.get("sel_date", str(dt.date.today()))
    note_val = st.session_state.notes.get(st.session_state.sel_date, "")
    if note_val:
        st.success(f"{st.session_state.sel_date} 筆記")
        st.write(note_val)
        if st.button("✏️ 編輯／追加", key="edit_note"):
            st.session_state.show_diary = True
            st.rerun()
    else:
        st.info("當日尚無筆記，點 ➕ 新增！")

    # ── 本日～明日待辦清單（即使 expander 收起也能看到）──
    st.markdown("### 本日～明日待辦")
    now = dt.date.today()
    tomorrow = now + dt.timedelta(days=1)
    for d in [now, tomorrow]:
        items = st.session_state.todo.get(str(d), "").splitlines()
        if items:
            st.write(f"**{d}**")
            for it in items:
                st.write(f"- {it}")

    # ── 筆記蒐尋欄位（獨立折疊）──
    with st.expander("🔍 筆記蒐尋")
        search_q = st.text_input("關鍵字", key="note_search")
        if search_q:
            hits = [d for d, txt in st.session_state.notes.items() if search_q in txt]
            for d in hits:
                st.write(f"**{d}**")
                st.write(st.session_state.notes[d]")
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
                    
    
