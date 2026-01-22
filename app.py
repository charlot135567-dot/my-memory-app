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
# TAB 2：📅 靈修足跡月曆（Emoji 強制出現 + 刪除多餘日期列）
# ===================================================================
with tabs[1]:

    # ---------- 1-3 初始化、CSS、Emoji 清單（同上，不變） ----------
    if 'events'   not in st.session_state:  st.session_state.events   = []
    if 'notes'    not in st.session_state:  st.session_state.notes    = {}
    if 'todo'     not in st.session_state:  st.session_state.todo     = {}
    if 'sel_date' not in st.session_state:  st.session_state.sel_date = str(dt.date.today())
    if 'cal_key'  not in st.session_state:  st.session_state.cal_key  = 0   # 強迫重繪計數器

    REPO_RAW   = "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/"
    EMOJI_LIST = ["🐾","🧸","🐶","🕌","🥐","💭","🍔","🍖","🍒","🍓","🥰","💖","🌸","💬","✨","🥕","🌟","🍀","🎀","🎉"]

    st.markdown("""
    <style>
    .fc-event-main { font-size:28px !important; display:flex !important; justify-content:center !important; align-items:center !important; height:50px !important; }
    .fc-event { background-color:transparent !important; border:none !important; }
    .todo-left  { justify-content:flex-start !important; padding-left:4px; }
    .note-right { justify-content:flex-end  !important; padding-right:4px; }
    </style>
    """, unsafe_allow_html=True)

    # ---------- 4. 組建事件 + 月曆（Emoji 強制出現） ----------
    def build_events():
        ev=[]
        for d,n in st.session_state.notes.items():
            ev.append({"title":f"{n.get('emoji','📝')} {n['title'][:6]}","start":d,"classNames":"note-right"})
        for d,todos in st.session_state.todo.items():
            if isinstance(todos,list):
                for t in todos:
                    ev.append({"title":f"{t.get('emoji','🔔')} {t['title'][:8]}","start":d,"classNames":"todo-left"})
            else:
                ev.append({"title":f"{todos.get('emoji','🔔')} {todos['title'][:8]}","start":d,"classNames":"todo-left"})
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
        state = calendar(events=build_events(), options=cal_opt,
                         key=f"emoji_calendar_{st.session_state.cal_key}")
        if state.get("dateClick"):
            st.session_state.sel_date = state["dateClick"]["date"][:10]
        # ❌ 刪除：不再顯示「目前選取日期」這行

    # ---------- 5. 下方顯示區（今明後天 + 奶油/粉底 + 對齊垃圾桶） ----------
    st.divider()
    from datetime import timedelta

    base  = dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date()
    days3 = [base + timedelta(days=i) for i in range(0, 3)]   # 今天・明天・後天

    # 5-1 待辦（3 日 + 粉底 + 垃圾桶對齊）
    st.markdown("#### 🔔 待辦事項（今明後）")
    has_todo = False
    for dd in days3:
        ds = str(dd)
        if ds not in st.session_state.todo: continue
        has_todo = True
        for t in sorted(st.session_state.todo[ds], key=lambda x: x.get('time', '00:00:00')):
            with st.container():
                col_d, col_ico, col_ttl, col_del = st.columns([1, 1, 5, 1])
                with col_d: st.caption(f"{dd.month}/{dd.day}")
                with col_ico:
                    st.markdown(f"<span style='background-color:#FFE4E1;border-radius:4px;'>{t.get('emoji','🔔')}</span>", unsafe_allow_html=True)
                with col_ttl: st.markdown(f"**{t['title']}**")
                with col_del:
                    # 只讓「當天」出現垃圾桶
                    if ds == st.session_state.sel_date:
                        if st.button("🗑️", key=f"del_todo_{ds}_{hash(t['title'])}"):
                            st.session_state.todo[ds].remove(t)
                            if not st.session_state.todo[ds]: del st.session_state.todo[ds]
                            st.session_state.cal_key += 1; st.rerun()
                    else: st.empty()   # 其他天留空，保持直線
    if not has_todo: st.info("今明後尚無待辦")

    # 5-2 筆記（3 日 + 奶油底 + 編輯+垃圾桶並排）
    st.markdown("#### 📝 筆記（今明後）")
    has_note = False
    for dd in days3:
        ds = str(dd)
        if ds not in st.session_state.notes: continue
        has_note = True
        n = st.session_state.notes[ds]
        with st.container():
            col_ico, col_ttl, col_act = st.columns([1, 5, 2])
            with col_ico:
                st.markdown(f"<span style='background-color:#FFF8DC;border-radius:4px;'>{n.get('emoji','📝')}</span>", unsafe_allow_html=True)
            with col_ttl: st.markdown(f"**{n['title']}** ‑ {dd.month}/{dd.day}")
            with col_act:
                c_ed, c_del = st.columns(2)
                with c_ed:
                    if ds == st.session_state.sel_date:   # 只當天可編輯
                        if st.button("✏️", key=f"ed_note_{ds}"):
                            st.session_state.edit_mode = True
                            st.session_state.edit_ttl   = n['title']
                            st.session_state.edit_cont  = n.get('content', '')
                            st.session_state.edit_emo   = n.get('emoji', '📝')
                            st.rerun()
                    else: st.empty()
                with c_del:
                    if ds == st.session_state.sel_date:   # 只當天可刪除
                        if st.button("🗑️", key=f"del_note_{ds}"):
                            del st.session_state.notes[ds]
                            st.session_state.cal_key += 1; st.rerun()
                    else: st.empty()
        st.caption(n.get('content', ''))

    if not has_note: st.info("今明後尚無筆記")

    # 5-3 編輯展開表單（與你上一版相同）
    if st.session_state.get('edit_mode'):
        st.divider()
        st.markdown("#### ✏️ 編輯筆記")
        new_ttl = st.text_input("標題", value=st.session_state.edit_ttl, key="edit_ttl_inp")
        new_cont = st.text_area("內容", value=st.session_state.edit_cont, key="edit_cont_inp")
        new_emo = st.selectbox("Emoji", ["📝"] + EMOJI_LIST,
                               index=EMOJI_LIST.index(st.session_state.edit_emo) + 1
                               if st.session_state.edit_emo in EMOJI_LIST else 0,
                               key="edit_emo_inp")
        c_save, c_cancel = st.columns([1, 4])
        with c_save:
            if st.button("💾 更新", key="do_update"):
                st.session_state.notes[cur] = {"title": new_ttl, "content": new_cont, "emoji": new_emo}
                st.session_state.edit_mode = False
                st.session_state.cal_key += 1
                st.rerun()
        with c_cancel:
            if st.button("取消", key="cancel_edit"):
                st.session_state.edit_mode = False
                st.rerun()
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
