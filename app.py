import streamlit as st
import pandas as pd
import requests
import io
import re
import os
import random
import time
from urllib.parse import quote

# 嘗試載入動畫套件
try:
    from streamlit_lottie import st_lottie
    LOTTIE_AVAILABLE = True
except ImportError:
    LOTTIE_AVAILABLE = False

# --- 1. 頁面配置 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide", page_icon="🐶")

THEME = {"bg": "#FFF9E3", "box": "#FFFFFF", "accent": "#FFCDD2", "text": "#4A4A4A", "sub": "#F06292", "keyword": "#E91E63"}

# --- 2. Lottie 動畫加載 ---
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except: return None

LOTTIE_MARIO = "raw.githubusercontent.com"
LOTTIE_DOG = "assets10.lottiefiles.com"

# --- 3. 側邊欄 ---
with st.sidebar:
    st.markdown("### 🐾 系統控制台")
    if 'score' not in st.session_state: st.session_state.score = 0
    if 'lives' not in st.session_state: st.session_state.lives = 3
    st.subheader(f"🏆 得分: {st.session_state.score}")
    st.subheader(f"❤️ 生命: {'❤️' * st.session_state.lives}")
    if st.button("♻️ 刷新內容"):
        st.cache_data.clear()
        st.rerun()

# --- 4. CSS 樣式 ---
st.markdown(f"""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [data-testid="stAppViewContainer"] {{ background-color: {THEME['bg']}; font-family: 'Comic Neue', cursive; }}
    .feature-box {{
        background-color: {THEME['box']} !important;
        border-radius: 18px !important;
        padding: 15px !important;
        border: 2.5px solid {THEME['accent']} !important;
        box-shadow: 4px 4px 0px {THEME['accent']} !important;
        margin-bottom: 10px !important;
        min-height: 110px;
    }}
    .kw {{ color: {THEME['keyword']}; font-weight: bolder; font-size: 1.2em; background-color: #FFFF00; padding: 2px 4px; border-radius: 4px; }}
    .dict-btn {{ color: {THEME['sub']}; text-decoration: none; font-weight: bold; float: right; font-size: 11px; border: 1px solid; padding: 1px 4px; border-radius: 4px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. 資料抓取 ---
SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
GIDS = {"📖 經節": "1454083804", "🔤 單字": "1400979824", "🔗 片語": "1657258260"}

@st.cache_data(ttl=300)
def fetch_data(gid):
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=10)
        return pd.read_csv(io.StringIO(r.text)).fillna("")
    except: return pd.DataFrame()

# --- 6. 主頁面 ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 隨機挑戰", "🧪 自動分類工具"])

with tab_home:
    df_v = fetch_data(GIDS["📖 經節"])
    df_w = fetch_data(GIDS["🔤 單字"])
    df_p = fetch_data(GIDS["🔗 片語"])
    v1 = df_v.sample(1).iloc[0] if not df_v.empty else {}
    w1 = df_w.sample(1).iloc[0] if not df_w.empty else {"Vocab": "Study", "Definition": "學習"}
    p1 = df_p.sample(1).iloc[0] if not df_p.empty else {"Phrase": "Keep it up", "Definition": "加油"}

    # 6.1 頂部：史努比圖片並排縮小
    st.markdown('<div style="margin-top: -30px;"></div>', unsafe_allow_html=True)
    img_files = ["f364bd220887627.67cae1bd07457.jpg", "183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg", "68254faebaafed9dafb41918f74c202e.jpg"]
    img_cols = st.columns(6) # 使用更多欄位來縮小單張圖片
    for idx, img_name in enumerate(img_files):
        if os.path.exists(img_name):
            img_cols[idx].image(img_name, width=100)

    # 6.2 第一排：單字、片語、文法 (填補上方空白)
    st.markdown("---")
    c1, c2, c3 = st.columns([1, 1.2, 1.8])
    with c1:
        v_word = w1["Vocab"]
        d_url = f"dictionary.cambridge.org{quote(v_word)}"
        st.markdown(f'<div class="feature-box"><a href="{d_url}" target="_blank" class="dict-btn">🔍 字典</a><small>🔤 單字</small><br><b>{v_word}</b><br><small>{w1["Definition"]}</small></div>', unsafe_allow_html=True)
    with c2:
        phrase = p1["Phrase"]
        p_url = f"www.google.com{quote(phrase)}+meaning"
        st.markdown(f'<div class="feature-box"><a href="{p_url}" target="_blank" class="dict-btn">🔗 參考</a><small>🔗 片語</small><br><b>{phrase}</b><br><small>{p1["Definition"]}</small></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="feature-box" style="background-color:#E3F2FD !important;"><small>📝 關鍵文法</small><br><div style="font-size:14px; margin-top:5px;">{w1.get("Grammar", "保持學習！")}</div></div>', unsafe_allow_html=True)

    # 6.3 下方橫跨全寬：今日金句
    raw_ch = v1.get("Chinese", "載入中...")
    kw = str(v1.get("Keyword", ""))
    display_ch = raw_ch.replace(kw, f'<span class="kw">{kw}</span>') if kw and kw in raw_ch else raw_ch
    
    st.markdown(f'<div class="feature-box" style="min-height:150px;"><h3 style="color:{THEME["sub"]}; margin-top:0;">💡 今日金句</h3><div style="font-size:28px; line-height:1.4; font-weight:bold;">“{display_ch}”</div><div style="color:gray; margin-top:10px; text-align:right;">— {v1.get("Reference","")}</div></div>', unsafe_allow_html=True)

with tab_play:
    # 6.4 動態動畫
    m_data = load_lottieurl(LOTTIE_MARIO)
    s_data = load_lottieurl(LOTTIE_DOG)
    col_a, col_b = st.columns(2)
    with col_a:
        if LOTTIE_AVAILABLE and m_data: st_lottie(m_data, height=150, key="mario")
    with col_b:
        if LOTTIE_AVAILABLE and s_data: st_lottie(s_data, height=150, key="dog")
    
    if st.session_state.lives <= 0:
        st.error("💀 GAME OVER!")
        if st.button("重啟"):
            st.session_state.lives = 3
            st.rerun()
    else:
        st.subheader("⚡️ 瞬時翻譯挑戰")
        target = w1["Vocab"]
        st.write(f"題目： 「 **{w1['Definition']}** 」 的英文是？")
        ans = st.text_input("輸入答案...", key="play_in")
        if st.button("提交"):
            if ans.lower().strip() == target.lower().strip():
                st.balloons()
                st.session_state.score += 10
                st.rerun()
            else:
                st.session_state.lives -= 1
                st.error(f"生命值 -1。答案是: {target}")

with tab_tool:
    st.info("🧪 分類工具已就緒。")
