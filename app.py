# ===================================================================
# 0. 套件與全域設定（保留你原封不動的區塊 1~5）
# ===================================================================
import streamlit as st
import datetime as dt
try:
    from streamlit_calendar import calendar
    CALENDAR_OK = True
except ModuleNotFoundError:
    CALENDAR_OK = False
    calendar = None

st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# ---------- Session 初始 ----------
if 'events' not in st.session_state: st.session_state.events = []
if 'notes' not in st.session_state: st.session_state.notes = {}
if 'todo' not in st.session_state: st.session_state.todo = {}
if 'custom_emojis' not in st.session_state: st.session_state.custom_emojis = ["🐾", "🐰", "🥰", "✨", "🥕", "🌟"]
if 'sel_date' not in st.session_state: st.session_state.sel_date = str(dt.date.today())
if 'modal' not in st.session_state: st.session_state.modal = None   # 新增：控制彈窗

# ---------- 你原有的 CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
.cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
.small-font { font-size: 13px; color: #555555; margin-top: 5px !important; }
.grammar-box-container {
    background-color: #f8f9fa; border-radius: 8px; padding: 12px; 
    border-left: 5px solid #FF8C00; text-align: left; margin-top: 0px;
}
/* 日曆格子點擊回饋 */
.fc-daygrid-day-frame:hover {background-color: #FFF3CD !important; cursor: pointer; transform: scale(1.03); transition: .2s}
.fc-daygrid-day-frame:active {transform: scale(0.98); background-color: #FFE69C !important}
</style>
""", unsafe_allow_html=True)

# ---------- IMG & Sidebar（原樣） ----------
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
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/", use_container_width=True)

tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# ===================================================================
# 1. TAB 1：書桌（你原來的內容，完全沒動）
# ===================================================================
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

# ===================================================================
# TAB 2：📓 筆記（一週捲動 + 大格子 + 多筆待辦 + 當日筆記即點即現）
# ===================================================================
with tabs[1]:
    # ---- 0. 手動開關（保險） ----
    if 'expander' not in st.session_state:
        st.session_state.expander = True
    c_top, _ = st.columns([1, 4])
    with c_top:
        if st.button("📅 開啟編輯區", key='open_editor'):
            st.session_state.expander = not st.session_state.expander

    # ---- 1. 事件建構（照你原邏輯） ----
    def build_events():
        ev = []
        for d, n in st.session_state.notes.items():
            ev.append({"title": f"{n.get('emoji','📝')} {n['title'][:8]}", "start": d})
        for d, t in st.session_state.todo.items():
            ev.append({"title": f"{t['title'][:8]} {t.get('emoji','🔔')}", "start": d})
        return ev

    # ---- 2. 一週視圖 + 固定高度捲動 ----
    if CALENDAR_OK:
        cal = calendar(
            events=build_events(),
            options={
                "initialView": "timeGridWeek",   # 一週視圖
                "locale": "zh-tw",
                "firstDay": 1,
                "headerToolbar": {"start": "", "center": "title", "end": ""},
                "height": 400,                   # 固定高度 → 出現捲軸
                "dateClick": True
            },
            key="cal"
        )
        # 點格子 → 記錄日期 → 下方即時刷新
        if cal and cal.get("dateClick"):
            d = cal["dateClick"]["date"][:10]
            st.session_state.sel_date = d
            st.session_state.expander = True

    # ---- 3. 統一折疊區（保證出現） ----
    with st.expander("📅 新增筆記 / 待辦", expanded=st.session_state.expander):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📝 新增筆記", use_container_width=True):
                st.session_state.modal = 'note'; st.rerun()
        with c2:
            if st.button("🔔 新增待辦", use_container_width=True):
                st.session_state.modal = 'todo'; st.rerun()

        # 3-1 筆記 Modal
        if st.session_state.modal == 'note':
            d1, d2, d3 = st.columns([2, 2, 1])
            with d1:
                new_date = st.date_input("日期", dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date(), label_visibility="collapsed")
            with d2:
                emoji = st.selectbox("Emoji", ["📝"] + st.session_state.custom_emojis, label_visibility="collapsed")
            with d3:
                if st.button("💾 保存", key="save_note"):
                    k = str(new_date)
                    st.session_state.notes[k] = {"title": st.session_state.get('note_title', ''), "content": st.session_state.get('note_content', ''), "emoji": emoji}
                    st.session_state.modal = None; st.rerun()
            st.text_input("標題", placeholder="筆記標題", key="note_title")
            st.text_area("內容", placeholder="記錄靈修心得...", key="note_content")
            if st.button("取消", key="cancel_note"): st.session_state.modal = None; st.rerun()

        # 3-2 待辦 Modal
        if st.session_state.modal == 'todo':
            d1, d2, d3 = st.columns([2, 2, 1])
            with d1:
                new_date = st.date_input("日期", dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date(), label_visibility="collapsed")
                new_time = st.time_input("時間", dt.time(9, 0), label_visibility="collapsed")
            with d2:
                emoji = st.selectbox("Emoji", ["🔔"] + st.session_state.custom_emojis, label_visibility="collapsed")
            with d3:
                if st.button("💾 保存", key="save_todo"):
                    k = str(new_date)
                    st.session_state.todo[k] = {"title": st.session_state.get('todo_title', ''), "time": str(new_time), "emoji": emoji}
                    st.session_state.modal = None; st.rerun()
            st.text_input("待辦事項", placeholder="輸入待辦標題", key="todo_title")
            if st.button("取消", key="cancel_todo"): st.session_state.modal = None; st.rerun()

    # ---- 4. 日曆下方：多筆待辦（依時間）+ 當日所有筆記 ----
    st.divider()
    st.markdown(f"**📍 {st.session_state.sel_date} 的內容**")

    # 4-1 待辦：同一日可能有多筆 → 先轉時間再排序
    todo_list = [
        (t['time'], t.get('emoji', '🔔'), t['title'])
        for d, t in st.session_state.todo.items()
        if d == st.session_state.sel_date
    ]
    for tm, em, tit in sorted(todo_list):
        st.markdown(f"🔔 **{em} {tit}** ・`{tm}`")

    # 4-2 筆記：當日全部列出
    for d, n in st.session_state.notes.items():
        if d == st.session_state.sel_date:
            with st.container():
                st.markdown(f"📝 **{n.get('emoji', '📝')} {n['title']}**")
                st.caption(n.get('content', ''))
                
# ===================================================================
# 3. TAB 3 & 4：挑戰 / 資料庫（你原來的內容，完全沒動）
# ===================================================================
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
