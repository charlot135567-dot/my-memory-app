import streamlit as st
import pandas as pd
import requests
import io
import re
import os
import random

# --- 1. 頁面配置 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide")

# --- 2. 史努比柔和風格 CSS (強化框框顯示) ---
st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Comic Neue', cursive;
        background-color: #FFF9E3;
    }
    
    .header-container { display: flex; flex-direction: column; align-items: center; padding: 10px; }
    .main-title { font-family: 'Gloria Hallelujah', cursive; color: #4A4A4A; font-size: 42px; font-weight: bold; }

    /* 五個框框的樣式 */
    .feature-box {
        background-color: #FFFFFF !important;
        border-radius: 18px !important;
        padding: 25px !important;
        min-height: 220px !important;
        border: 2px solid #FFCDD2 !important;
        box-shadow: 6px 6px 0px #FFCDD2 !important;
        margin-bottom: 25px !important;
        display: block !important;
    }
    .box-title { color: #F06292; font-weight: bold; font-size: 20px; margin-bottom: 12px; border-bottom: 2px dashed #FFEBEE; }
    .box-content { font-size: 22px; color: #333333; line-height: 1.5; font-weight: bold; }
    .box-ref { font-size: 15px; color: #888888; margin-top: 10px; font-style: italic; }

    [data-testid="stSidebar"] { background-color: #FFEBEE !important; border-right: 3px solid #FFCDD2 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 標題與圖片 ---
st.markdown('<div class="header-container">', unsafe_allow_html=True)
# 優先讀取您上傳的史努比插圖
img_name = "f364bd220887627.67cae1bd07457.jpg"
if os.path.exists(img_name):
    st.image(img_name, width=300)
else:
    st.markdown('<h1 style="font-size: 80px; margin: 0;">🐶🐤</h1>', unsafe_allow_html=True)
st.markdown('<div class="main-title">MEMORY LOGIC DESK</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 4. 資料庫設定 (維持原本 ID) ---
SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
GIDS = {"📖 經節": "1454083804", "🔤 單字": "1400979824", "🔗 片語": "1657258260"}

@st.cache_data(ttl=300)
def fetch_data(gid):
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.text))
            return df.fillna("")
    except: pass
    return pd.DataFrame()

# --- 5. 分頁導覽 ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 隨機挑戰", "🧪 自動分類工具"])

with tab_home:
    # 預加載資料
    df_v = fetch_data(GIDS["📖 經節"])
    df_w = fetch_data(GIDS["🔤 單字"])
    df_p = fetch_data(GIDS["🔗 片語"])

    # 隨機抽樣邏輯
    v1 = df_v.sample(1).iloc[0] if not df_v.empty else {"Chinese": "請檢查連線", "Reference": ""}
    v2 = df_v.sample(1).iloc[0] if not df_v.empty else {"Chinese": "請檢查連線", "Reference": ""}
    w1 = df_w.sample(1).iloc[0] if not df_w.empty else {"Vocab": "無資料", "Definition": ""}
    p1 = df_p.sample(1).iloc[0] if not df_p.empty else {"Phrase": "無資料", "Definition": ""}

    # 第一排 (2個大框)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="feature-box"><div class="box-title">💡 今日金句</div><div class="box-content">“{v1.get("Chinese")}”</div><div class="box-ref">— {v1.get("Reference")}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="feature-box"><div class="box-title">🔄 複習經節</div><div class="box-content">“{v2.get("Chinese")}”</div><div class="box-ref">— {v2.get("Reference")}</div></div>', unsafe_allow_html=True)

    # 第二排 (3個小框)
    c3, c4, c5 = st.columns(3)
    with c3:
        st.markdown(f'<div class="feature-box"><div class="box-title">🔤 重點單字</div><div class="box-content">{w1.get("Vocab")}</div><div class="box-ref">意義：{w1.get("Definition")}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="feature-box"><div class="box-title">🔗 常用片語</div><div class="box-content">{p1.get("Phrase")}</div><div class="box-ref">意義：{p1.get("Definition")}</div></div>', unsafe_allow_html=True)
    with c5:
        gram = w1.get("Grammar") or p1.get("Grammar") or "Keep learning with Snoopy!"
        st.markdown(f'<div class="feature-box" style="background-color: #E1F5FE; border-color: #81D4FA;"><div class="box-title" style="color: #0288D1;">📝 關鍵文法</div><div class="box-content" style="font-size: 18px;">{gram}</div><div class="box-ref">💡 Woodstock\'s Tip</div></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🐾 Snoopy's Desk")
    if st.button("♻️ 刷新書桌內容"):
        st.cache_data.clear()
        st.rerun()
