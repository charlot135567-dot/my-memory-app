import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import datetime as dt  # 使用 dt 作為縮寫來呼叫 time

# ==========================================
# [區塊 1] 環境匯入與全域 CSS 樣式
# ==========================================
import streamlit as st
import pandas as pd
from datetime import datetime
import datetime as dt 

st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
    .small-font { font-size: 13px; color: #555555; }
    
    /* 修正文法框高度，確保與左側經節對齊 */
    .grammar-box {
        background-color: #f8f9fa; border-radius: 8px; padding: 15px;
        border-left: 5px solid #FF8C00; font-size: 14px; 
        height: 185px; 
        display: flex; flex-direction: column; justify-content: center;
    }
    .stVerticalBlock { gap: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg",
    "M1": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro1.jpg",
    "M3": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro3.jpg"
}

# ==========================================
# [區塊 2] 側邊欄 (Sidebar) 控制台
# ==========================================
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다</p>', unsafe_allow_html=True)
    # 1) 控制台 Mashimaro3 (大小保持 OK)
    st.image(IMG_URLS["M3"], width=100) 
    st.divider()
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/", use_container_width=True)

# ==========================================
# [區塊 3] TAB 1: 書桌主畫面 (修正 Mashimaro1 與例句)
# ==========================================
tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

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
        # 2) 右上 Mashimaro1 改為跟控制台一樣大小 (width=100)
        st.image(IMG_URLS["M1"], width=100) 
        st.markdown("""
        <div class="grammar-box">
            <b>時態:</b> 現在簡單式表達恆常真理<br>
            <b>核心片語:</b><br>
            • Fine speech (優美言辭)<br>
            • Becoming to (相稱/合宜)<br>
            • Still less (何況)
        </div>
        """, unsafe_allow_html=True)

    # 3) 最下層文法例句 (確保顯示在金句與圖片下方的空間)
    st.divider() 
    cg1, cg2 = st.columns(2)
    with cg1:
        st.markdown("**Ex 1:** Casual attire is not becoming to a CEO... <br><p class='small-font'>便服對執行長不相稱；更不用說不專業言語了。</p>", unsafe_allow_html=True)
    with cg2:
        st.markdown("**Ex 2:** Wealth is not becoming to a man without virtue... <br><p class='small-font'>財富對於無德之人不相稱；更不用說權力了。</p>", unsafe_allow_html=True)

# ==========================================
# [區塊 4] TAB 2: 筆記與折疊式待辦提醒 (新提案實作)
# ==========================================
with tabs[1]:
    # 討論點實作：折疊式月曆、待辦、提醒整合區
    with st.expander("📅 點擊展開：日期篩選、待辦事項與鬧鈴設定", expanded=False):
        c1, c2, c3 = st.columns([0.3, 0.4, 0.3])
        with c1:
            sel_date = st.date_input("選擇日期", value=datetime(2026, 1, 16))
        with c2:
            todo_val = st.text_input("填入待辦任務", placeholder="例如：查經第5章...")
        with c3:
            alarm_val = st.time_input("設定提醒", dt.time(9, 0))
        
        if st.button("➕ 儲存待辦並設定鬧鈴", use_container_width=True):
            st.success(f"已記錄！{sel_date} {alarm_val} 提醒：{todo_val}")

    st.divider()

    # 筆記區：標題與存檔鍵合併 (共用欄位)
    t2_left, t2_right = st.columns([0.7, 0.3])
    with t2_left:
        # 將筆記標題寫在框內
        note_title_input = st.text_input("筆記標題", value=f"{sel_date} 靈修筆記", label_visibility="collapsed")
    with t2_right:
        if st.button(f"💾 存檔：{note_title_input[:10]}...", use_container_width=True):
            st.toast("筆記已存檔成功！")

    # 多語對照 (含泰文)
    st.write("<p style='font-size:13px; color:gray;'><b>對照：</b> 🇯🇵 すぐれた言葉は... | 🇰🇷 미련한 자에게... | 🇹🇭 ริมฝีปากที่ประเสริฐ...</p>", unsafe_allow_html=True)
    
    # 筆記內容框 (清空內部，標題寫在框內)
    st.text_area("筆記📝", height=250, placeholder="", label_visibility="visible")

# ==========================================
# [區塊 5] TAB 3 & 4: 挑戰與資料庫
# ==========================================
with tabs[2]:
    st.subheader("📝 翻譯挑戰")
    st.image(IMG_URLS["B"], width=150)

with tabs[3]:
    st.subheader("🔗 資源連結")
    st.link_button("Google AI", "https://gemini.google.com/")
    if st.button("💾 資料存入雲端"):
        st.success("存檔完成")
