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
# TAB 2：📓 靈修足跡月曆（1-4 完整覆蓋版）
# ===================================================================
with tabs[1]:

    # ---------- 1. session_state 保險 ----------
    if 'events'   not in st.session_state:  st.session_state.events   = []
    if 'notes'    not in st.session_state:  st.session_state.notes    = {}
    if 'todo'     not in st.session_state:  st.session_state.todo     = {}
    if 'sel_date' not in st.session_state:  st.session_state.sel_date = str(dt.date.today())
    if 'edit_mode'not in st.session_state:  st.session_state.edit_mode= False
    if 'cal_key'  not in st.session_state:  st.session_state.cal_key  = 0   # 強迫重繪計數器

    # ---------- 2. 圖片 & Emoji ----------
    REPO_RAW  = "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/"
    IMG_HEAD  = f"{REPO_RAW}Mashimaro1.jpg"
    EMOJI_LIST= ["🐾","🧸","🐶","🕌","🥐","💭","🍔","🍖","🍒","🍓","🥰","💖","🌸","💬","✨","🥕","🌟","🍀","🎀","🎉"]

    # ---------- 3. CSS（超大 Emoji + 去底 + 左右定位） ----------
    st.markdown("""
    <style>
    .fc-event-main {
        font-size: 28px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        height: 50px !important;
    }
    .fc-event {
        background-color: transparent !important;
        border: none !important;
    }
    .todo-left  { justify-content: flex-start !important; padding-left: 4px; }
    .note-right { justify-content: flex-end !important;  padding-right: 4px; }
    </style>
    """, unsafe_allow_html=True)

    # ---------- 4. 組建事件 + 月曆（含強迫重繪） ----------
    def build_events():
        ev=[]
        # 筆記 → 靠右
        for d,n in st.session_state.notes.items():
            ev.append({"title":f"{n.get('emoji','📝')} {n['title'][:6]}",
                       "start":d,"classNames":"note-right"})
        # 待辦 → 靠左（多筆）
        for d,todos in st.session_state.todo.items():
            if isinstance(todos,list):
                for t in todos:
                    ev.append({"title":f"{t.get('emoji','🔔')} {t['title'][:8]}",
                               "start":d,"classNames":"todo-left"})
            else:   # 舊格式相容
                ev.append({"title":f"{todos.get('emoji','🔔')} {todos['title'][:8]}",
                           "start":d,"classNames":"todo-left"})
        return ev

    st.subheader("📅 靈修足跡月曆")
    with st.expander("展開 / 摺疊月曆視窗", expanded=True):
        cal_opt = {
            "headerToolbar":{"left":"prev,next today","center":"title","right":""},
            "initialView":"dayGridMonth",
            "selectable":True,
            "height":500,
            "dateClick":True
        }
        # 關鍵：key 帶變數 → 資料異動就強迫重繪
        state = calendar(
            events=build_events(),
            options=cal_opt,
            key=f"emoji_calendar_{st.session_state.get('cal_key', 0)}"
        )
        if state.get("dateClick"):
            st.session_state.sel_date = state["dateClick"]["date"][:10]
        st.write(f"📍 目前選取日期：**{st.session_state.sel_date}**")

    # （以下 5. 新增 / 顯示 / 編輯區 保持你上一版不變，可直接沿用）

    # ---------- 5. 下方編輯 / 顯示區 ----------
    st.divider()
    st.markdown(f"**📍 {st.session_state.sel_date} 的內容**")

    # 5-1 新增區
    with st.expander("➕ 新增筆記 / 待辦", expanded=True):
        mode = st.radio("模式",["📝 新增筆記","🔔 新增待辦"],horizontal=True)
        c1,c2,c3=st.columns([2,1,3])
        with c1: d=st.date_input("日期",dt.datetime.strptime(st.session_state.sel_date,"%Y-%m-%d").date(),label_visibility="collapsed")
        with c2: emo=st.selectbox("Emoji",["📝","🔔"]+EMOJI_LIST,label_visibility="collapsed")
        with c3: ttl=st.text_input("標題",placeholder="輸入標題...",label_visibility="collapsed")
        if mode=="📝 新增筆記":
            cont=st.text_area("內容",placeholder="記錄靈修心得...")
            if st.button("💾 儲存筆記",use_container_width=True):
                if ttl:
                    st.session_state.notes[str(d)]={"title":ttl,"content":cont,"emoji":emo}
                    st.success("✅ 筆記已儲存"); st.rerun()
                else: st.error("請輸入標題")
        else:   # 待辦
            tm=st.time_input("⏰ 時間",dt.time(9,0))
            if st.button("💾 新增待辦",use_container_width=True):
                if ttl:
                    k=str(d)
                    if k not in st.session_state.todo: st.session_state.todo[k]=[]
                    st.session_state.todo[k].append({"title":ttl,"time":str(tm),"emoji":emo})
                    st.success("✅ 待辦已新增"); st.rerun()
                else: st.error("請輸入待辦標題")

    # 5-2 當日待辦（多筆 + 按時間排序）
    cur=st.session_state.sel_date
    if cur in st.session_state.todo and st.session_state.todo[cur]:
        st.markdown("#### 🔔 待辦事項")
        for t in sorted(st.session_state.todo[cur],key=lambda x:x.get('time','00:00:00')):
            c_tm,c_ttl,c_del=st.columns([1,4,1])
            with c_tm: st.caption(t.get('time',''))
            with c_ttl: st.markdown(f"{t.get('emoji','🔔')} **{t['title']}**")
            with c_del:
                if st.button("🗑️",key=f"del_todo_{cur}_{hash(t['title'])}"):
                    st.session_state.todo[cur].remove(t)
                    if not st.session_state.todo[cur]: del st.session_state.todo[cur]
                    st.rerun()

    # 5-3 當日筆記（可編輯 / 刪除）
    if cur in st.session_state.notes:
        st.markdown("#### 📝 筆記")
        n=st.session_state.notes[cur]
        c_ttl,c_ed,c_del=st.columns([5,1,1])
        with c_ttl: st.markdown(f"{n.get('emoji','📝')} **{n['title']}**")
        with c_ed:
            if st.button("✏️",key=f"edit_note_{cur}"):
                st.session_state.edit_mode=True
                st.session_state.edit_ttl=n['title']
                st.session_state.edit_cont=n.get('content','')
                st.session_state.edit_emo=n.get('emoji','📝')
                st.rerun()
        with c_del:
            if st.button("🗑️",key=f"del_note_{cur}"):
                del st.session_state.notes[cur]
                st.rerun()
        st.caption(n.get('content',''))

    # 5-4 編輯展開表單
    if st.session_state.get('edit_mode'):
        st.divider()
        st.markdown("#### ✏️ 編輯筆記")
        new_ttl=st.text_input("標題",value=st.session_state.edit_ttl,key="edit_ttl_inp")
        new_cont=st.text_area("內容",value=st.session_state.edit_cont,key="edit_cont_inp")
        new_emo=st.selectbox("Emoji",["📝"]+EMOJI_LIST,
                             index=EMOJI_LIST.index(st.session_state.edit_emo)+1
                                     if st.session_state.edit_emo in EMOJI_LIST else 0,
                             key="edit_emo_inp")
        c_save,c_cancel=st.columns([1,4])
        with c_save:
            if st.button("💾 更新",key="do_update"):
                st.session_state.notes[cur]={"title":new_ttl,"content":new_cont,"emoji":new_emo}
                st.session_state.edit_mode=False
                st.rerun()
        with c_cancel:
            if st.button("取消",key="cancel_edit"):
                st.session_state.edit_mode=False
                st.rerun()

    # 5-5 無資料提示
    if cur not in st.session_state.notes and cur not in st.session_state.todo:
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
