import streamlit as st
import pandas as pd
import requests
import io
import re
import random
from datetime import datetime

# --- 1. 頁面配置 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide")

# --- 2. 史努比柔和風格 CSS ---
st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Comic Neue', cursive;
        background-color: #FFF9E3; /* 淺奶油黃 */
    }
    
    .main-title {
        font-family: 'Gloria Hallelujah', cursive;
        color: #4A4A4A; text-align: center;
        font-size: 45px; font-weight: bold; padding: 10px;
    }

    /* 核心框框的樣式 */
    .feature-box {
        background-color: #FFFFFF;
        border-radius: 15px;
        padding: 20px;
        min-height: 200px;
        border: 2px solid #FFCDD2;
        box-shadow: 4px 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .box-title { color: #F06292; font-weight: bold; font-size: 18px; margin-bottom: 8px; border-bottom: 1px solid #FFEBEE; }
    .box-content { font-size: 19px; color: #333333; line-height: 1.4; font-weight: bold; }
    .box-ref { font-size: 14px; color: #888888; margin-top: 8px; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🐾 CHARLIE\'S MEMORY DESK</h1>', unsafe_allow_html=True)

# --- 3. 初始化設定 ---
SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
GIDS = {"📖 經節": "1454083804", "🔤 單字": "1400979824", "🔗 片語": "1657258260"}

@st.cache_data(ttl=600)
def fetch_data(gid):
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=10)
        return pd.read_csv(io.StringIO(r.text)).fillna("")
    except: return pd.DataFrame()

# --- 4. 功能分頁 ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌 (一目了然)", "🎯 隨機挑戰", "🧪 自動分類工具"])

# --- 分頁 1: 我的書桌 ---
with tab_home:
    df_v = fetch_data(GIDS["📖 經節"])
    df_w = fetch_data(GIDS["🔤 單字"])
    df_p = fetch_data(GIDS["🔗 片語"])

    # 準備隨機內容
    v_today = df_v.sample(1).iloc[0] if not df_v.empty else {"Chinese": "讀取中...", "Reference": "N/A"}
    v_review = df_v.sample(1).iloc[0] if not df_v.empty else {"Chinese": "讀取中...", "Reference": "N/A"}
    w_item = df_w.sample(1).iloc[0] if not df_w.empty else {"Vocab": "Loading...", "Definition": "N/A", "Grammar": "N/A"}
    p_item = df_p.sample(1).iloc[0] if not df_p.empty else {"Phrase": "Loading...", "Definition": "N/A", "Grammar": "N/A"}

    # 第一列：經節區
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="feature-box">
            <div class="box-title">💡 今日金句 (Daily Verse)</div>
            <div class="box-content">“{v_today.get('Chinese', 'N/A')}”</div>
            <div class="box-ref">— {v_today.get('Reference', 'N/A')}</div>
        </div>""", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""<div class="feature-box">
            <div class="box-title">🔄 複習經節 (Review Verse)</div>
            <div class="box-content">“{v_review.get('Chinese', 'N/A')}”</div>
            <div class="box-ref">— {v_review.get('Reference', 'N/A')}</div>
        </div>""", unsafe_allow_html=True)

    # 第二列：單字、片語、文法
    col3, col4, col5 = st.columns(3)
    with col3:
        st.markdown(f"""<div class="feature-box">
            <div class="box-title">🔤 今日單字 (Vocab)</div>
            <div class="box-content">{w_item.get('Vocab', 'N/A')}</div>
            <div class="box-ref">意義：{w_item.get('Definition', 'N/A')}</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""<div class="feature-box">
            <div class="box-title">🔗 今日片語 (Phrase)</div>
            <div class="box-content">{p_item.get('Phrase', 'N/A')}</div>
            <div class="box-ref">意義：{p_item.get('Definition', 'N/A')}</div>
        </div>""", unsafe_allow_html=True)
    
    with col5:
        # 從單字或片語中隨機抓取文法說明
        grammar_text = w_item.get('Grammar') or p_item.get('Grammar') or "今日無特定文法提醒"
        st.markdown(f"""<div class="feature-box" style="background-color: #E1F5FE; border-color: #81D4FA;">
            <div class="box-title" style="color: #0288D1;">📝 關鍵文法 (Grammar)</div>
            <div class="box-content" style="font-size: 17px;">{grammar_text}</div>
            <div class="box-ref">來自：{w_item.get('Vocab') or p_item.get('Phrase')}</div>
        </div>""", unsafe_allow_html=True)

    st.info("✨ 每次刷新頁面，史努比都會為您準備不同的學習組合！")

# --- 後續分頁保持功能 ---
with tab_play:
    st.subheader("🎯 隨機抽取與多語對照")
    # 此處可放入您之前的隨機抽題邏輯...

with tab_tool:
    st.subheader("🧪 自動分類與寫入工具")
    # 此處可放入您之前的分類寫入邏輯...
