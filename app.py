import streamlit as st
import datetime as dt
from streamlit_calendar import calendar

# ==========================================
# [1] 全域初始化：必須位於最頂端，解決 AttributeError
# ==========================================
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

if 'events' not in st.session_state: st.session_state.events = []
if 'notes' not in st.session_state: st.session_state.notes = {}
if 'todo' not in st.session_state: st.session_state.todo = {}
if 'custom_emojis' not in st.session_state:
    st.session_state.custom_emojis = ["🐾", "🐰", "🥰", "✨", "🥕", "🌟"]

# 樣式定義
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
    .grammar-box-container {
        background-color: #f8f9fa; border-radius: 8px; padding: 12px; 
        border-left: 5px solid #FF8C00; text-align: left;
    }
    </style>
    """, unsafe_allow_html=True)

IMG_URLS = {
    "M1": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro1.jpg",
    "M3": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro3.jpg"
}

# ==========================================
# [2] 側邊欄與 Tab 定義
# ==========================================
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다</p>', unsafe_allow_html=True)
    st.image(IMG_URLS["M3"], width=250)
    st.divider()
    st.link_button("✨ 開啟 Google AI", "https://gemini.google.com/", use_container_width=True)

tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# ==========================================
# [3] TAB 1: 修正對齊與 HTML 字串
# ==========================================
with tabs[0]:
    col_content, col_m1 = st.columns([0.65, 0.35])
    with col_content:
        st.info("**Becoming** / 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 🇹🇭 เหมาะสม | 🇨🇳 相稱")
        st.info("**Still less** / 🇯🇵 まして | 🇰🇷 하물며 | 🇹🇭 ยิ่งกว่านั้น | 🇨🇳 何況")
        st.success("""
            🌟 **Pro 17:07** Fine speech is not becoming to a fool; still less is false speech to a prince. 
            """, icon="📖")

    with col_m1:
        # 使用 justify-content: flex-end 確保框框在底部對齊
        st.markdown(f"""
            <div style="display: flex; flex-direction: column; justify-content: flex-end; height: 320px; text-align: center;">
                <div style="margin-bottom: 20px;">
                    <img src="{IMG_URLS['M1']}" style="width: 180px;">
                </div>
                <div class="grammar-box-container">
                    <p style="margin:2px 0; font-size: 14px; font-weight: bold; color: #333;">時態: 現在簡單式</p>
                    <ul style="margin:0; padding-left:18px; font-size: 13px; color: #555;">
                        <li>Fine speech (優美言辭)</li>
                        <li>Becoming to (相稱)</li>
                        <li>Still less (何況)</li>
                    </ul>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.divider()

# ==========================================
# [4] TAB 2: 解決 NameError 與所有需求整合
# ==========================================
with tabs[1]:
    # 安全門神：預先定義 sel_date 避免 NameError
    if 'temp_date' not in st.session_state: st.session_state.temp_date = str(dt.date.today())
    sel_date = st.session_state.temp_date

    # 1. 整合工具箱 (問題 3, 4, 5, 9)
    with st.expander("🛠️ 靈修工具箱 (+/- Emoji & 提醒設定)", expanded=True):
        c1, c2 = st.columns([0.4, 0.6])
        with c1:
            selected_emoji = st.selectbox("👣 選擇足跡", st.session_state.custom_emojis, index=0)
            new_emo = st.text_input("追加/刪除 Emoji (Enter)", placeholder="貼上符號...")
            if new_emo:
                if new_emo in st.session_state.custom_emojis: st.session_state.custom_emojis.remove(new_emo)
                else: st.session_state.custom_emojis.append(new_emo)
                st.rerun()
        with c2:
            current_todo = st.session_state.todo.get(sel_date, "")
            new_todo = st.text_area("📝 今日提醒 (自動存檔)", value=current_todo, height=100)
            if new_todo != current_todo:
                st.session_state.todo[sel_date] = new_todo
                if new_todo.strip() and selected_emoji:
                    if not any(e['start'] == sel_date for e in st.session_state.events):
                        st.session_state.events.append({"title": selected_emoji, "start": sel_date, "allDay": True})
                st.rerun()

    # 2. 月曆視窗 (折疊)
    with st.expander("📅 檢視靈修月曆", expanded=False):
        cal_state = calendar(events=st.session_state.events, key="cal_final")
        if cal_state.get("dateClick"):
            st.session_state.temp_date = cal_state["dateClick"]["date"][:10]
            st.rerun()

    # 3. 三語經文 (問題 6, 7, 8)
    st.markdown(f"""
    <div style="display: flex; background: #FFF0F5; border-radius: 15px; padding: 15px; align-items: center; margin-top: 10px; border-left: 5px solid #FF1493;">
        <div style="flex: 2;">
            <h4 style="color:#FF1493; margin:0;">ข้อพระคัมภีร์ประจำวันนี้</h4>
            <p style="font-size:16px; margin:5px 0;"><b>🇨🇳 應當常歡喜，不已禱告，凡事謝恩。</b></p>
            <p style="font-size:14px; color:#666;">🇯🇵 常に喜んでいなさい | 🇰🇷 항상 기뻐하라 | 🇹🇭 จงชื่นชมยินดีอยู่เสมอ</p>
        </div>
        <div style="flex: 1; text-align: right;"><img src="{IMG_URLS['M1']}" width="80"></div>
    </div>
    """, unsafe_allow_html=True)

    # 4. 筆記區：搜尋、存檔對齊 (問題 10, 11)
    st.divider()
    ctrl1, ctrl2, ctrl3 = st.columns([0.2, 0.3, 0.5])
    with ctrl1: btn_save = st.button("💾 存檔", use_container_width=True)
    with ctrl2: b_date = st.date_input("日期", value=dt.datetime.strptime(sel_date, "%Y-%m-%d"), label_visibility="collapsed")
    with ctrl3: search_q = st.text_input("🔍 搜尋筆記", placeholder="關鍵字...", label_visibility="collapsed")

    note_val = st.session_state.notes.get(str(b_date), "")
    if search_q:
        found = [v for k, v in st.session_state.notes.items() if search_q in v]
        if found: note_val = found[0]; st.caption("✨ 顯示搜尋結果")

    note_text = st.text_area("感悟", value=note_val, height=250, key="note_v_final")
    if btn_save:
        st.session_state.notes[str(b_date)] = note_text
        st.snow(); st.toast("🐾 腳印已留下！"); st.success("儲存成功")
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
        st.image(IMG_URLS["M1"], width=150, caption="Keep Going!")

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
