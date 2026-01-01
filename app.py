🚀 史努比書桌旗艦版 app.py
請將 GitHub 上的內容全選刪除，改貼入這份：
python
import streamlit as st
import pandas as pd
import requests
import io
import re
import random
import os
from datetime import datetime

# --- 1. 頁面配置 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide")

# --- 2. 柔和史努比風格 CSS ---
st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Comic Neue', cursive;
        background-color: #FFF9E3; /* 柔和淺黃背景 */
    }
    
    /* 標題與圖片區 */
    .header-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 10px;
    }
    .main-title {
        font-family: 'Gloria Hallelujah', cursive;
        color: #4A4A4A;
        font-size: 42px;
        font-weight: bold;
        margin-top: 15px;
    }

    /* 五個框框的樣式 */
    .feature-box {
        background-color: #FFFFFF;
        border-radius: 18px;
        padding: 22px;
        min-height: 200px;
        border: 2px solid #FFCDD2;
        box-shadow: 6px 6px 0px #FFCDD2;
        margin-bottom: 20px;
    }
    .box-title { color: #F06292; font-weight: bold; font-size: 19px; margin-bottom: 10px; border-bottom: 2px dashed #FFEBEE; }
    .box-content { font-size: 20px; color: #333333; line-height: 1.5; font-weight: bold; }
    .box-ref { font-size: 14px; color: #888888; margin-top: 10px; font-style: italic; }

    /* 側邊欄風格 */
    [data-testid="stSidebar"] {
        background-color: #FFEBEE !important;
        border-right: 3px solid #FFCDD2 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 主視覺圖片 (使用您提供的圖片) ---
st.markdown('<div class="header-container">', unsafe_allow_html=True)
img_name = "f364bd220887627.67cae1bd07457.jpg"

if os.path.exists(img_name):
    st.image(img_name, width=280) # 顯示您的史努比圖片
else:
    # 備用方案：若圖片尚未同步，使用 Emoji
    st.markdown('<h1 style="font-size: 80px; margin: 0;">🐶🐤</h1>', unsafe_allow_html=True)

st.markdown('<div class="main-title">MEMORY LOGIC DESK</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 4. 初始化設定與資料讀取 ---
SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
GIDS = {"📖 經節": "1454083804", "🔤 單字": "1400979824", "🔗 片語": "1657258260"}

@st.cache_data(ttl=600)
def fetch_data(gid):
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=10)
        return pd.read_csv(io.StringIO(r.text)).fillna("")
    except: return pd.DataFrame()

# --- 5. 分頁導覽 ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌 (一目了然)", "🎯 隨機對照挑戰", "🧪 自動分類工具"])

with tab_home:
    df_v = fetch_data(GIDS["📖 經節"])
    df_w = fetch_data(GIDS["🔤 單字"])
    df_p = fetch_data(GIDS["🔗 片語"])

    # 隨機抽取內容
    v_today = df_v.sample(1).iloc if not df_v.empty else {}
    v_review = df_v.sample(1).iloc if not df_v.empty else {}
    w_item = df_w.sample(1).iloc if not df_w.empty else {}
    p_item = df_p.sample(1).iloc if not df_p.empty else {}

    # 第一排：兩個大框 (經節)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="feature-box"><div class="box-title">💡 今日金句 (Daily Verse)</div><div class="box-content">“{v_today.get("Chinese", "讀取中...")}”</div><div class="box-ref">— {v_today.get("Reference", "N/A")}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="feature-box"><div class="box-title">🔄 複習經節 (Review Verse)</div><div class="box-content">“{v_review.get("Chinese", "讀取中...")}”</div><div class="box-ref">— {v_review.get("Reference", "N/A")}</div></div>', unsafe_allow_html=True)

    # 第二排：三個小框 (單字、片語、文法)
    col3, col4, col5 = st.columns(3)
    with col3:
        st.markdown(f'<div class="feature-box"><div class="box-title">🔤 重點單字</div><div class="box-content">{w_item.get("Vocab", "...")}</div><div class="box-ref">意義：{w_item.get("Definition", "N/A")}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="feature-box"><div class="box-title">🔗 常用片語</div><div class="box-content">{p_item.get("Phrase", "...")}</div><div class="box-ref">意義：{p_item.get("Definition", "N/A")}</div></div>', unsafe_allow_html=True)
    with col5:
        grammar = w_item.get('Grammar') or p_item.get('Grammar') or "Keep learning, Snoopy is watching you!"
        st.markdown(f'<div class="feature-box" style="background-color: #E1F5FE; border-color: #81D4FA;"><div class="box-title" style="color: #0288D1;">📝 關鍵文法</div><div class="box-content" style="font-size: 17px;">{grammar}</div><div class="box-ref">💡 Woodstock\'s Tip</div></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🐾 Snoopy's Desk")
    st.info("“Learn from yesterday, live for today, look to tomorrow.”")
    if st.button("♻️ 刷新書桌內容"):
        st.cache_data.clear()
        st.rerun()
