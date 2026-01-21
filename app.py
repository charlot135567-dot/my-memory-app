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
# TAB 2：📓 筆記（全面修正版）
# ===================================================================
with tabs[1]:
    # ---- 0. 初始化待辦為列表格式（支援多筆） ----
    if 'todo' not in st.session_state or not isinstance(st.session_state.todo, dict):
        st.session_state.todo = {}
    
    # 確保每個日期對應的是列表
    for date_key in st.session_state.todo:
        if not isinstance(st.session_state.todo[date_key], list):
            st.session_state.todo[date_key] = [st.session_state.todo[date_key]]

    # ---- 1. 事件建構：待辦靠左、筆記靠右 ----
    def build_events():
        ev = []
        # 筆記：顯示在右側
        for d, n in st.session_state.notes.items():
            emoji = n.get('emoji', '📝')
            ev.append({"title": f"{emoji} {n['title'][:6]}", "start": d, "classNames": ["note-right"]})
        # 待辦：顯示在左側（只顯示標題）
        for d, todos in st.session_state.todo.items():
            if isinstance(todos, list):
                for todo in todos:
                    emoji = todo.get('emoji', '🔔')
                    ev.append({"title": f"{emoji} {todo['title'][:8]}", "start": d, "classNames": ["todo-left"]})
            else:
                # 舊格式相容
                emoji = todos.get('emoji', '🔔')
                ev.append({"title": f"{emoji} {todos['title'][:8]}", "start": d, "classNames": ["todo-left"]})
        return ev

    # ---- 2. 日曆：可捲動、加大格子、無時間軸 ----
    if CALENDAR_OK:
        cal = calendar(
            events=build_events(),
            options={
                "initialView": "dayGridWeek",    # 改為dayGridWeek，格子更大
                "locale": "zh-tw",
                "firstDay": 1,
                "headerToolbar": {"start": "", "center": "title", "end": ""},
                "height": 500,                    # 固定高度→出現捲軸
                "dateClick": True,
                "allDaySlot": False,             # 移除時間欄
                "slotMinTime": "00:00:00",
                "slotMaxTime": "01:00:00",       # 最小化時間範圍
                "eventTimeFormat": False         # 不顯示時間
            },
            key="cal"
        )
        # 點擊日期 → 同步到下方表單
        if cal and cal.get("dateClick"):
            d = cal["dateClick"]["date"][:10]
            st.session_state.sel_date = d

    # ---- 3. 刪除重複編輯區，只保留下方統一區塊 ----
    # （已移除原上方編輯區）

    # ---- 4. 統一新增區（支援多筆待辦） ----
    with st.expander("📅 新增筆記 / 待辦", expanded=True):
        mode = st.radio("選擇模式", ["📝 新增筆記", "🔔 新增待辦"], horizontal=True)
        
        # 日期、Emoji、標題區塊
        col1, col2, col3 = st.columns([2, 1, 3])
        with col1:
            st.session_state.date_input = st.date_input(
                "📅 日期",
                dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date(),
                format="YYYY/MM/DD"
            )
        with col2:
            emoji = st.selectbox("🏷️ Emoji", ["📝", "🔔"] + st.session_state.custom_emojis)
        with col3:
            title = st.text_input("標題", placeholder="輸入標題...")
        
        # 內容區塊（僅筆記）
        content = None
        if mode == "📝 新增筆記":
            content = st.text_area("內容", placeholder="記錄靈修心得...")
        
        # 時間區塊（僅待辦）
        time_input = None
        if mode == "🔔 新增待辦":
            time_input = st.time_input("⏰ 時間", dt.time(9, 0))
        
        # 保存按鈕
        if st.button("💾 保存", use_container_width=True):
            date_key = str(st.session_state.date_input)
            if mode == "📝 新增筆記":
                if title:
                    st.session_state.notes[date_key] = {
                        "title": title,
                        "content": content,
                        "emoji": emoji
                    }
                    st.success(f"✅ 筆記已儲存至 {date_key}")
                    st.rerun()
                else:
                    st.error("請輸入標題")
            else:  # 待辦
                if title:
                    if date_key not in st.session_state.todo:
                        st.session_state.todo[date_key] = []
                    st.session_state.todo[date_key].append({
                        "title": title,
                        "time": str(time_input) if time_input else "00:00:00",
                        "emoji": emoji
                    })
                    st.success(f"✅ 待辦已新增至 {date_key}")
                    st.rerun()
                else:
                    st.error("請輸入待辦標題")

    # ---- 5. 顯示當日內容（支援多筆待辦+筆記編輯） ----
    st.divider()
    st.markdown(f"**📍 {st.session_state.sel_date} 的內容**")
    
    current_date = st.session_state.sel_date
    
    # 5-1 待辦事項（多筆+排序）
    if current_date in st.session_state.todo and st.session_state.todo[current_date]:
        st.markdown("#### 🔔 待辦事項")
        # 按時間排序
        sorted_todos = sorted(st.session_state.todo[current_date], key=lambda x: x.get('time', '00:00:00'))
        for i, todo in enumerate(sorted_todos):
            col_time, col_info, col_del = st.columns([1, 3, 1])
            with col_time:
                st.caption(todo.get('time', ''))
            with col_info:
                st.markdown(f"{todo.get('emoji', '🔔')} **{todo['title']}**")
            with col_del:
                if st.button("🗑️", key=f"del_todo_{current_date}_{i}"):
                    del st.session_state.todo[current_date][i]
                    if not st.session_state.todo[current_date]:
                        del st.session_state.todo[current_date]
                    st.rerun()
    
    # 5-2 筆記（可編輯）
    if current_date in st.session_state.notes:
        st.markdown("#### 📝 筆記")
        note = st.session_state.notes[current_date]
        col_title, col_edit, col_del = st.columns([4, 1, 1])
        with col_title:
            st.markdown(f"{note.get('emoji', '📝')} **{note['title']}**")
        with col_edit:
            if st.button("✏️ 編輯", key=f"edit_note_{current_date}"):
                st.session_state.edit_mode = True
                st.session_state.edit_title = note['title']
                st.session_state.edit_content = note['content']
                st.session_state.edit_emoji = note.get('emoji', '📝')
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"del_note_{current_date}"):
                del st.session_state.notes[current_date]
                st.rerun()
        
        # 顯示內容
        st.caption(note.get('content', ''))
    
    # 5-3 編輯筆記的 Modal（展開式）
    if st.session_state.get('edit_mode'):
        st.divider()
        st.markdown("#### ✏️ 編輯筆記")
        col1, col2 = st.columns([4, 1])
        with col1:
            edit_title = st.text_input("標題", value=st.session_state.edit_title, key="edit_title_input")
            edit_content = st.text_area("內容", value=st.session_state.edit_content, key="edit_content_input")
        with col2:
            edit_emoji = st.selectbox("Emoji", ["📝"] + st.session_state.custom_emojis, 
                                      index=["📝"] + st.session_state.custom_emojis.index(st.session_state.edit_emoji) 
                                      if st.session_state.edit_emoji in st.session_state.custom_emojis else 0,
                                      key="edit_emoji_input")
        
        col_save, col_cancel = st.columns([1, 4])
        with col_save:
            if st.button("💾 更新", key="update_note"):
                st.session_state.notes[current_date] = {
                    "title": edit_title,
                    "content": edit_content,
                    "emoji": edit_emoji
                }
                st.session_state.edit_mode = False
                st.rerun()
        with col_cancel:
            if st.button("取消編輯", key="cancel_edit"):
                st.session_state.edit_mode = False
                st.rerun()

    # 5-4 若當天無內容
    if current_date not in st.session_state.notes and current_date not in st.session_state.todo:
        st.info("當天尚無紀錄，請從上方新增")

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
