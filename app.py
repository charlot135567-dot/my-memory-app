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

    # 1. 靈修工具箱 🧰
    with st.expander("🛠️ 靈修工具箱 (提醒與 Emoji 管理)", expanded=True):
        row1_col1, row1_col2, row1_col3 = st.columns([0.3, 0.25, 0.45])

        with row1_col1:
            st.markdown("#### 今日提醒 🔔")

        with row1_col2:
            # 手機友善：直接用 radio 就能點
            selected_emoji = st.radio(
                "🐾 足跡",
                st.session_state.custom_emojis,
                horizontal=True,
                label_visibility="collapsed"
            )

        with row1_col3:
            emoji_mode = st.selectbox(
                "",
                ["🐾 使用 Emoji", "🚫 不使用 Emoji"],
                label_visibility="collapsed"
            )

        # 待辦事項
        current_todo = st.session_state.todo.get(st.session_state.sel_date, "")
        new_todo = st.text_area(
            "📋 待辦事項清單 (自動存檔)",
            value=current_todo,
            height=120
        )

        if new_todo != current_todo:
            st.session_state.todo[st.session_state.sel_date] = new_todo

            # --- Emoji 事件：先清後補 ---
            # 1. 刪掉當日所有「純 Emoji」事件
            st.session_state.events = [
                e for e in st.session_state.events
                if not (e["start"] == st.session_state.sel_date and e["title"] in st.session_state.custom_emojis)
            ]
            # 2. 若有內容且開啟 Emoji，就補上
            if new_todo.strip() and emoji_mode == "🐾 使用 Emoji":
                st.session_state.events.append({
                    "title": selected_emoji,
                    "start": st.session_state.sel_date,
                    "allDay": True
                })
            st.rerun()
            
      # 2. 月曆（可切週/月，手機友善）
    with st.expander("📅 檢視靈修月曆", expanded=False):
        if CALENDAR_OK:
            state = calendar(
                events=st.session_state.events,
                options={
                    "initialView": "dayGridMonth",
                    "headerToolbar": {
                        "left": "prev,next today",
                        "center": "title",
                        "right": "dayGridMonth,timeGridWeek"
                    },
                    "selectable": True,
                },
                key="bible_cal_final"
            )
            if state.get("dateClick"):
                clicked_date = state["dateClick"]["date"][:10]
                if clicked_date != st.session_state.sel_date:
                    st.session_state.sel_date = clicked_date
                    st.rerun()
        else:
            st.info("月曆元件尚未安裝，請稍後再試。")

    # 3. 經文區
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

    # 4. 筆記區
    st.divider()
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([0.2, 0.3, 0.5])

    with ctrl_col1:
        btn_save = st.button("💾 存檔", key="save_note_final")

    with ctrl_col2:
        default_date = dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d")
        b_date = st.date_input(
            "日期",
            value=default_date,
            label_visibility="collapsed",
            key="date_picker_final",
            on_change=lambda: setattr(st.session_state, "sel_date", str(st.session_state.date_picker_final))
        )

    with ctrl_col3:
        search_q = st.text_input(
            "🔍 搜尋",
            placeholder="關鍵字...",
            label_visibility="collapsed",
            key="search_final"
        )

    note_val = st.session_state.notes.get(str(b_date), "")
    note_text = st.text_area(
        "",
        value=note_val,
        height=250,
        placeholder="寫下心得與感悟...",
        key="note_area_final"
    )

    if btn_save:
        st.session_state.notes[str(b_date)] = note_text
        st.toast("🐾 腳印已留下！")

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
