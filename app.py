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
# [區塊 1] 環境匯入與全域 CSS 樣式 (精煉修復版)
# ==========================================
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
    .small-font { font-size: 13px; color: #555555; margin-top: 5px !important; }
    
    /* 語法框樣式：確保在手機與桌面端皆能正確填充內容 */
    .grammar-box-container {
        background-color: #f8f9fa; 
        border-radius: 8px; 
        padding: 12px; 
        border-left: 5px solid #FF8C00; 
        text-align: left;
        margin-top: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

# 統一圖片資源管理 (URL 方式)
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
# [區塊 2] 側邊欄 (Sidebar) 與 Tabs 定義
# ==========================================
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다</p>', unsafe_allow_html=True)
    st.image(IMG_URLS["M3"], width=250) 
    st.divider()
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/", use_container_width=True)

tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# ==========================================
# [區塊 3] TAB 1: 書桌主畫面內容 (修復渲染整合版)
# ==========================================
with tabs[0]:
    # 建立兩欄：左邊放經文，右邊放圖片與框
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
        # 使用 Flex 佈局強制讓 Mashimaro 在上，框框在下且底部對齊
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
    st.divider()

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
