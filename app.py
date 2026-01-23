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

if 'cal_key'  not in st.session_state: st.session_state.cal_key = 0
# ---------- 全域常數 ----------
EMOJI_LIST = ["🐾","🧸","🐶","🕌","🥐","💭","🍔","🍖","🍒","🍓","🥰","💖","🌸","💬","✨","🥕","🌟","🍀","🎀","🎉"]

# ===================================================================
# TAB 2：純 Streamlit 雙週格（100% 可動）- 捲動+Emoji點刪+>10字+靠右
# ===================================================================
with tabs[1]:

    import re, datetime as dt
    _EMOJI_RE = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+",flags=re.UNICODE)
    def first_emoji(text: str) -> str:
        m = _EMOJI_RE.search(text)
        return m.group(0) if m else ""
    def remove_emoji(text: str) -> str:
        return _EMOJI_RE.sub("", text).strip()

    if "start_week" not in st.session_state:
        today = dt.date.today()
        st.session_state.start_week = today - dt.timedelta(days=today.weekday())

    start = st.session_state.start_week
    dates = [start + dt.timedelta(days=i) for i in range(14)]  # 本週+下週

    # ---- 手機原生捲動：兩週格 + 上下週按鈕 ----
    with st.expander("📅 雙週靈修足跡（捲動換週，點 Emoji 刪除）", expanded=True):
        st.markdown("""
        <style>
        .stExpander .stBlock{overflow-y:auto!important;max-height:45vh!important;}
        </style>
        """, unsafe_allow_html=True)

        # 上下週按鈕
        c_prev, c_next = st.columns(2)
        with c_prev:
            if st.button("⬆ 上一週", key="prev_w"):
                st.session_state.start_week -= dt.timedelta(days=7)
                st.rerun()
        with c_next:
            if st.button("⬇ 下一週", key="next_w"):
                st.session_state.start_week += dt.timedelta(days=7)
                st.rerun()

        # 逐日格子（一行一天）
        for i, d in enumerate(dates):
            wd = d.strftime("%a")
            col_emoji, col_txt = st.columns([1, 9])
            # === 關鍵：純按鈕就能觸發 ===
            with col_emoji:
                # 待辦 Emoji（單顆按鈕 → 直接觸發刪除）
                if str(d) in st.session_state.todo:
                    for idx, t in enumerate(st.session_state.todo[str(d)]):
                        if st.button(f"{t.get('emoji','🔔')}", key=f"td_{d}_{idx}"):
                            st.session_state.del_target = {"date": str(d), "index": idx, "title": t['title']}
                            st.session_state.show_del = True
                # 筆記 Emoji（單顆按鈕 → 帶出當天筆記）
                if str(d) in st.session_state.notes:
                    n = st.session_state.notes[str(d)]
                    if st.button(f"{n.get('emoji','📝')}", key=f"nt_{d}"):
                        st.session_state.sel_date = str(d)
            with col_txt:
                st.caption(f"{wd} {d.day}")
                # 待辦標題（>10 字才列）
                if str(d) in st.session_state.todo:
                    for t in st.session_state.todo[str(d)]:
                        if len(t['title']) > 10:
                            st.caption(f"🔔 {t.get('time','')}　{t['title'][:20]}")
                # 筆記標題
                if str(d) in st.session_state.notes:
                    st.caption(f"📝 {st.session_state.notes[str(d)]['title'][:15]}")

    # ---- 單 Emoji 點刪確認 ----
    if st.session_state.get("show_del"):
        t = st.session_state.del_target
        st.warning(f"🗑️ 確定刪除待辦「{t['title']}」？")
        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button("確認", type="primary", key="del_ok"):
                d, idx = t["date"], t["index"]
                del st.session_state.todo[d][idx]
                if not st.session_state.todo[d]: del st.session_state.todo[d]
                st.session_state.cal_key += 1
                st.session_state.show_del = False
                st.rerun()
        with c2:
            if st.button("取消", key="del_no"):
                st.session_state.show_del = False
                st.rerun()

    # ---- 5-1 新增區（同前版） ----
    st.divider()
    with st.expander("➕ 新增筆記 / 待辦", expanded=True):
        mode = st.radio("模式", ["📝 新增筆記", "🔔 新增待辦"], horizontal=True, key="mode_radio_1")
        ph_emo = "📝" if mode == "📝 新增筆記" else "🔔"
        if mode == "📝 新增筆記":
            c1, c2 = st.columns([2, 8])
            with c1: d = st.date_input("日期", dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date(), label_visibility="collapsed")
            with c2: ttl = st.text_input("標題", placeholder=f"{ph_emo} 可直接輸入 Emoji＋標題", label_visibility="collapsed")
            cont = st.text_area("內容", placeholder="記錄靈修心得...")
        else:
            c1, c2, c3 = st.columns([2, 2, 6])
            with c1: d = st.date_input("日期", dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date(), label_visibility="collapsed")
            with c2: tm = st.time_input("⏰ 時間", dt.time(9, 0), label_visibility="collapsed")
            with c3: ttl = st.text_input("標題", placeholder=f"{ph_emo} 可直接輸入 Emoji＋待辦", label_visibility="collapsed")

        if st.button("💾 儲存", use_container_width=True):
            if not ttl:
                st.error("請輸入標題")
                st.stop()
            emo_found = first_emoji(ttl) or ph_emo
            ttl_clean = remove_emoji(ttl)
            if mode == "📝 新增筆記":
                st.session_state.notes[str(d)] = {"title": ttl_clean, "content": cont, "emoji": emo_found}
            else:
                k = str(d)
                if k not in st.session_state.todo: st.session_state.todo[k] = []
                st.session_state.todo[k].append({"title": ttl_clean, "time": str(tm), "emoji": emo_found})
            st.session_state.cal_key += 1
            st.rerun()

    # ---- 5-2 待辦列表（只列 >10 字） ----
    start = st.session_state.start_week
    dates_show = [start + dt.timedelta(days=i) for i in range(14)]
    has_long = False
    for d in dates_show:
        ds = str(d)
        if ds in st.session_state.todo and st.session_state.todo[ds]:
            for t in sorted(st.session_state.todo[ds], key=lambda x: x.get('time', '00:00:00')):
                if len(t['title']) > 10:
                    has_long = True
                    st.caption(f"🔔 {d.strftime('%m/%d')} {t.get('time', '')}　{t['title']}")
    if has_long:
        st.markdown("---")

    # ---- 5-3 點格帶出當天筆記（編/刪靠最右） ----
    cur = st.session_state.sel_date
    if cur in st.session_state.notes:
        n = st.session_state.notes[cur]
        st.caption(f"📝 {dt.datetime.strptime(cur, '%Y-%m-%d').strftime('%m/%d')}　**{n['title']}**")
        if n.get('content'):
            st.caption(f"　{n['content']}")
        # 按鈕緊貼最右
        c_ed, c_del = st.columns([1, 1])
        with c_ed:
            if st.button("✏️", key=f"edit_note_{cur}"):
                st.session_state.edit_mode = True
                st.session_state.edit_ttl = n['title']
                st.session_state.edit_cont = n.get('content', '')
                st.session_state.edit_emo = n.get('emoji', '📝')
                st.rerun()
        with c_del:
            if st.button("🗑️", key=f"del_note_{cur}"):
                del st.session_state.notes[cur]
                st.session_state.cal_key += 1
                st.rerun()

    # ---- 5-4 編輯表單（同前版） ----
    if st.session_state.get('edit_mode'):
        st.divider()
        st.markdown("#### ✏️ 編輯筆記")
        new_ttl = st.text_input("標題", value=st.session_state.edit_ttl, key="edit_ttl_inp")
        new_cont = st.text_area("內容", value=st.session_state.edit_cont, key="edit_cont_inp")
        new_emo = st.selectbox("Emoji", EMOJI_LIST, index=EMOJI_LIST.index(st.session_state.edit_emo) if st.session_state.edit_emo in EMOJI_LIST else 0, key="edit_emo_inp")
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

    # ---- 5-5 無資料提示 ----
    if not has_long and cur not in st.session_state.notes:
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
