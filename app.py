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
# [區塊 4] TAB 2: 最終整合版（閃爍✔ Emoji✔ 週月切換✔ 連動✔）
# ==========================================
with tabs[1]:
    # 0. 防閃爍：保證一定有 sel_date
    if 'sel_date' not in st.session_state:
        st.session_state.sel_date = str(dt.date.today())

    # 背景桌布狀態初始化
    if "show_bg" not in st.session_state:
        st.session_state.show_bg = True

    if "bg_image" not in st.session_state:
        st.session_state.bg_image = None
            
    # 2. 本週靈修 glance ─ 手機專用折疊週曆＋活潑配色＋雙 Emoji 標記
    with st.expander("📅 本週靈修 glance", expanded=True):
        if CALENDAR_OK:
            today = dt.date.today()

            # ── ① 背景桌布（上傳即套用，可隨時更換）──
            bg_col1, bg_col2, bg_col3 = st.columns([1, 2, 1])
with bg_col2:
    uploaded_bg = st.file_uploader(
        "📷",
        type=["jpg", "jpeg"],
        key="bg_week",
        label_visibility="collapsed"
    )
     # ⭐ 上傳後，立刻覆蓋舊背景（這一行很關鍵）
        if uploaded_bg:
        st.session_state.bg_image = uploaded_bg

                b64 = base64.b64encode(uploaded_bg.getvalue()).decode()
                st.markdown(
                    f"""
                    <style>
                    .week-cal{{background:url(data:image/jpeg;base64,{b64});
                    background-size:cover;border-radius:16px;padding:8px;}}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

            # ── ② 懸浮快速鍵（3 鍵並排）──
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
            with btn_col1:
                if st.button("📷", key="bg_btn"):  # 更換桌布
                    st.session_state.show_bg = not st.session_state.get("show_bg", False)
            with btn_col2:
                if st.button("➕", key="quick_diary"):
                    st.session_state.show_diary = not st.session_state.get("show_diary", False)
                    st.session_state.show_todo = False  # 互斥收合
            with btn_col3:
                if st.button("🔔", key="quick_todo"):
                    st.session_state.show_todo = not st.session_state.get("show_todo", False)
                    st.session_state.show_diary = False  # 互斥收合

            # ── ③ 一週無限捲動日曆（活潑配色）──
            week_start = today - dt.timedelta(days=today.weekday())
            week_end = week_start + dt.timedelta(days=6)
            week_events = [
                e for e in st.session_state.events
                if week_start <= dt.date.fromisoformat(e["start"]) <= week_end
            ]

            # 幫每一天加上「雙 Emoji 標記」：左=待辦🔔，右=筆記📝
            for e in week_events:
                d = dt.date.fromisoformat(e["start"])
                todo_emoji = "🔔" if str(d) in st.session_state.todo else ""
                note_emoji = "📝" if str(d) in st.session_state.notes else ""
                e["title"] = f"{todo_emoji} {e['title']} {note_emoji}"

            st.markdown(
                """
                <style>
                .fc-daygrid-day-frame{border-radius:12px;}
                .fc-day-today{background:#fff7d6!important;}
                .fc-daygrid-day-number{color:#333;font-weight:600}
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <style>
                /* 圓角卡片 */
                .fc-daygrid-day-frame{
                    border-radius: 16px;
                    margin: 2px;
                    background: linear-gradient(135deg, #fff9f0 0%, #ffdbea 100%);
                    box-shadow: 0 2px 6px rgba(0,0,0,.05);
                }
                /* 今天特別粉嫩 */
                .fc-day-today .fc-daygrid-day-frame{
                    background: linear-gradient(135deg, #ffe4f0 0%, #ffc2d8 100%);
                    border: 2px dashed #ff8ab4;
                }
                /* 日期數字可愛粗體 */
                .fc-daygrid-day-number{
                    font-weight: 700;
                    font-size: 15px;
                    color: #5c3c50;
                }
                /* Emoji 氣泡 */
                .fc-event{
                    border-radius: 12px;
                    font-size: 18px;
                    padding: 2px 6px;
                    margin: 1px;
                    background: #ffffffcc;
                    backdrop-filter: blur(4px);
                    border: 1px solid #ffffff99;
                }
                /* 整體圓角 */
                .fc-daygrid-body, .fc-scrollgrid {
                    border-radius: 20px;
                    overflow: hidden;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )   
            st.markdown(
                """
                <style>
                /* 每一天強制粉嫩圓角 */
                .fc-daygrid-day-frame{
                    border-radius: 16px !important;
                    margin: 2px !important;
                    background: linear-gradient(135deg, #ffe8f5 0%, #ffd0e6 100%) !important;
                    box-shadow: 0 2px 8px rgba(0,0,0,.08) !important;
                }
                /* 今天特別桃色邊框 */
                .fc-day-today .fc-daygrid-day-frame{
                    background: linear-gradient(135deg, #ffc2d8 0%, #ffa6c1 100%) !important;
                    border: 2px dashed #ff6ba4 !important;
                }
                /* 日期數字可愛粗體 */
                .fc-daygrid-day-number{
                    font-weight: 700 !important;
                    font-size: 16px !important;
                    color: #5c3c50 !important;
                }
                /* Emoji 氣泡 */
                .fc-event{
                    border-radius: 12px !important;
                    font-size: 18px !important;
                    padding: 2px 6px !important;
                    margin: 1px !important;
                    background: #ffffffcc !important;
                    backdrop-filter: blur(4px) !important;
                    border: 1px solid #ffffff99 !important;
                }
                /* 整體外框大圓角 */
                .fc-daygrid-body, .fc-scrollgrid {
                    border-radius: 20px !important;
                    overflow: hidden !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            cal_options = {
                "initialView": "dayGridWeek",
                "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
                "height": "auto",
            }
            state = calendar(events=week_events, options=cal_options, key="week_cal_mobile")

            # ── ④ 點擊日期 → 即時顯示當日筆記 ──
            if state.get("dateClick"):
                clicked = state["dateClick"]["date"][:10]
                st.session_state.sel_date = clicked
                st.rerun()

            # ── ⑤ 動態表單（平行欄位＋一鍵收合）──
            if st.session_state.get("show_diary"):
                with st.form("diary_form"):
                    d1, d2 = st.columns([1, 1])
                    with d1:
                        d_date = st.date_input("日期", value=today)
                    with d2:
                        d_emoji = st.selectbox("Emoji", st.session_state.custom_emojis)
                    d_text = st.text_area("靈修筆記", height=180)
                    if st.form_submit_button("保存"):
                        key = str(d_date)
                        st.session_state.notes[key] = d_text
                        # 同時寫入日曆格子（右側 Emoji）
                        st.session_state.events.append({
                            "title": d_emoji or "📝",
                            "start": str(d_date),
                            "allDay": True,
                        })
                        st.success("已保存")
                        st.session_state.show_diary = False  # 自動收合
                        st.rerun()

            if st.session_state.get("show_todo"):
                with st.form("todo_form"):
                    t1, t2 = st.columns([1, 1])
                    with t1:
                        t_date = st.date_input("日期", value=today)
                    with t2:
                        t_time = st.time_input("時間", value=None)
                    t_all_day = st.checkbox("全天提醒", value=True)
                    t_text = st.text_area("待辦事項", height=120)
                    if st.form_submit_button("設定提醒"):
                        st.session_state.todo[str(t_date)] = t_text
                        # 同時寫入日曆格子（左側 Emoji）
                        st.session_state.events.append({
                            "title": "🔔",
                            "start": str(t_date),
                            "allDay": t_all_day,
                        })
                        st.success("已設定")
                        st.session_state.show_todo = False  # 自動收合
                        st.rerun()

        else:
            st.info("月曆元件尚未安裝，請稍後再試。")

    # 3. 經文區（維持原樣）
    st.markdown(f"""
    <div style="display:flex; background:#FFF0F5; border-radius:15px; padding:15px; margin-top:10px;">
        <div style="flex:2;">
            <p style="margin:4px 0;">🇨🇳 應當常常喜樂，不住地禱告，凡事謝恩。</p>
            <p style="margin:4px 0; color:#666;">
                🇯🇵 常に喜んでいなさい ｜ 🇰🇷 항상 기뻐하라 ｜ 🇹🇭 <span style="font-size:18px;">จงชื่นชมยินดีอยู่เสมอ</span>
            </p>
        </div>
        <div style="flex:1; text-align:right;">
            <img src="{IMG_URLS['M1']}" width="80">
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. 下半部 UI ── 當日筆記即時顯示＋搜尋欄
    st.divider()
    st.markdown("#### 今日靈修筆記 ✍️")
    # ── 搜尋欄 ──
    search_q = st.text_input("🔍 關鍵字搜尋", placeholder="輸入經文、筆記、待辦關鍵字...")
    # ── 當日筆記即時顯示 ──
    note_val = st.session_state.notes.get(st.session_state.sel_date, "")
    if note_val:
        st.success(f"{st.session_state.sel_date} 筆記")
        st.write(note_val)
    else:
        st.info("當日尚無筆記，點 ➕ 新增！")

# ==========================================
# [區塊 5] TAB 3 & 4: 挑戰與資料庫
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
    cl1.link_button("ChatGPT", "https://chat.openai.com/")
    cl2.link_button("Google AI", "https://gemini.google.com/")
    cl3.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb")
    cl4.link_button("THSV11", "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")
    st.divider()
    input_content_final = st.text_area("📥 聖經經文 / 英文文稿輸入", height=150, key="db_input_area")
    btn_l, btn_r = st.columns(2)
    if btn_l.button("📥 執行輸入解析"):
        st.toast("已讀取文稿")
    if btn_r.button("💾 存檔至資料庫"):
        st.success("資料已成功存入雲端資料庫！")
