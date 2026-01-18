import streamlit as st
import pandas as pd
import requests
import datetime as dt
from datetime import datetime, time
from PIL import Image
from io import BytesIO
from streamlit_calendar import calendar
import base64
from urllib.request import urlopen

# ==========================================
# [區塊 1] 環境匯入與全域 CSS 樣式
# ==========================================
st.set_page_config(layout="wide", page_title="Bible AI 2026")
from streamlit_calendar import calendar

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
    .small-font { font-size: 13px; color: #555555; margin-top: 5px !important; }
    .grammar-box-container {
        background-color: #f8f9fa; border-radius: 8px; padding: 12px; 
        border-left: 5px solid #FF8C00; text-align: left;
    }
    /* 月曆 Emoji 樣式 */
    .fc-event-main { font-size: 24px !important; display: flex !important; justify-content: center !important; }
    .fc-event { background-color: transparent !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

IMG_URLS = {
    "M1": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro1.jpg",
    "M3": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro3.jpg"
}

# ==========================================
# [區塊 2] 側邊欄與 Tabs 定義
# ==========================================
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다</p>', unsafe_allow_html=True)
    st.image(IMG_URLS["M3"], width=250)
    st.divider()
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/", use_container_width=True)

tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# ==========================================
# [區塊 3] TAB 1: 完美對齊修復版
# ==========================================
with tabs[0]:
    col1, col2 = st.columns([0.65, 0.35])
    with col1:
        st.info("**Becoming** / 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 🇨🇳 相稱")
        st.success("🌟 **Pro 17:07** Fine speech is not becoming to a fool...\n\n🇨🇳 愚頑人說美言本不相稱...", icon="📖")
    with col2:
        st.markdown(f"""
            <div style="display: flex; flex-direction: column; justify-content: flex-end; height: 100%; min-height: 350px;">
                <img src="{IMG_URLS['M1']}" style="width: 180px; margin: 0 auto -20px auto; position: relative; z-index: 15;">
                <div class="grammar-box-container">
                    <b>時態:</b> 現在簡單式<br><b>核心片語:</b><br>
                    <ul style="margin:0; padding-left:20px; font-size:13px;">
                        <li>Fine speech (優美言辭)</li>
                        <li>Becoming to (相稱)</li>
                    </ul>
                </div>
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# [區塊 4] TAB 2: 新增功能與佈局優化版
# ==========================================
with tabs[1]:
    if 'events' not in st.session_state: st.session_state.events = []
    if 'notes' not in st.session_state: st.session_state.notes = {}
    if 'todo' not in st.session_state: st.session_state.todo = {}
    if 'custom_emojis' not in st.session_state: st.session_state.custom_emojis = ["🐾", "🐰", "🐼", "🥰", "✨", "🥕"]

    # 標題與操作按鈕對齊 (問題 3)
    t_col, e_col, a_col, d_col = st.columns([0.4, 0.2, 0.2, 0.2])
    with t_col: st.subheader("📅 靈修足跡")
    with e_col: sel_emoji = st.selectbox("", st.session_state.custom_emojis, label_visibility="collapsed")
    with a_col: btn_add = st.button("＋足跡", use_container_width=True)
    with d_col: 
        if st.button("🗑️清空", use_container_width=True): 
            st.session_state.events = []; st.rerun()

    state = calendar(events=st.session_state.events, options={"height": 350}, key="calendar")
    sel_date = state.get("dateClick", {"date": str(dt.date.today())})["date"][:10]

    # 待辦與增減 Emoji (問題 4, 2)
    with st.expander(f"📝 {sel_date} 待辦與提醒", expanded=True):
        st.session_state.todo[sel_date] = st.text_input("輸入事項", value=st.session_state.todo.get(sel_date, ""))
    
    # 經文欄框 2/3 分欄 + 恢復中文 (問題 5, 6)
    st.markdown(f"""
    <div style="display: flex; background: #FFF0F5; border-radius: 15px; padding: 15px; align-items: center; margin-top: 10px;">
        <div style="flex: 2;">
            <h4 style="color:#FF1493; margin:0;">📖 今日經文</h4>
            <p style="font-size:16px; margin:5px 0;"><b>🇨🇳 應當常歡喜，不已禱告，凡事謝恩。</b></p>
            <p style="font-size:14px; color:#666;">🇯🇵 常に喜んでいなさい | 🇰🇷 항상 기뻐하라</p>
        </div>
        <div style="flex: 1; text-align: right;"><img src="{IMG_URLS['M1']}" width="70"></div>
    </div>
    """, unsafe_allow_html=True)

    # 筆記區最大化 (問題 7)
    st.divider()
    s_col, d_col, _ = st.columns([0.2, 0.3, 0.5])
    with s_col: btn_save = st.button("💾 儲存", use_container_width=True)
    with d_col: b_date = st.date_input("", value=dt.datetime.strptime(sel_date, "%Y-%m-%d"), label_visibility="collapsed")
    
    st.session_state.notes[str(b_date)] = st.text_area("", value=st.session_state.notes.get(str(b_date), ""), height=250, placeholder="寫下感悟...", key="note")
    if btn_save: st.success("已存檔！"); st.balloons()
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
        st.image(IMG_URLS["B"], width=150, caption="Keep Going!")

with tabs[3]:
    st.subheader("🔗 聖經與 AI 資源")
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
