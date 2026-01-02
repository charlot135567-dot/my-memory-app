import streamlit as st
import pandas as pd
import requests
import io
import re
import os  # 補上缺失的模組
import random
import time
from urllib.parse import quote

# 嘗試載入動畫套件，若環境未安裝則忽略
try:
    from streamlit_lottie import st_lottie
    LOTTIE_AVAILABLE = True
except ImportError:
    LOTTIE_AVAILABLE = False

# --- 1. 頁面配置 (奶油黃風格) ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide", page_icon="🐶")

THEME = {"bg": "#FFF9E3", "box": "#FFFFFF", "accent": "#FFCDD2", "text": "#4A4A4A", "sub": "#F06292", "keyword": "#E91E63"}

# --- 2. Lottie 動畫加載 ---
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# 動畫網址
LOTTIE_MARIO = "assets9.lottiefiles.com"
LOTTIE_SNOOPY = "assets7.lottiefiles.com"

# --- 3. 側邊欄 ---
with st.sidebar:
    st.markdown("### 🐾 系統控制台")
    if 'score' not in st.session_state: st.session_state.score = 0
    if 'lives' not in st.session_state: st.session_state.lives = 3
    if 'count' not in st.session_state: st.session_state.count = 0
    
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
        padding: 20px !important;
        border: 3px solid {THEME['accent']} !important;
        box-shadow: 6px 6px 0px {THEME['accent']} !important;
        margin-bottom: 15px !important;
    }}
    .kw {{ color: {THEME['keyword']}; font-weight: bolder; font-size: 1.2em; }}
    .dict-btn {{ color: {THEME['sub']}; text-decoration: none; font-weight: bold; float: right; font-size: 12px; border: 1px solid; padding: 2px 5px; border-radius: 5px; }}
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

    # 6.1 靜態圖片展示
    img_files = ["f364bd220887627.67cae1bd07457.jpg", "183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg", "68254faebaafed9dafb41918f74c202e.jpg"]
    cols = st.columns(len(img_files))
    for i, img_name in enumerate(img_files):
        if os.path.exists(img_name):
            cols[i].image(img_name, use_container_width=True)

    # 6.2 金句大框 (關鍵字標色)
    raw_ch = v1.get("Chinese", "載入中...")
    kw = v1.get("Keyword", "")
    display_ch = raw_ch.replace(kw, f'<span class="kw">{kw}</span>') if kw and kw in raw_ch else raw_ch
    
    st.markdown(f'<div class="feature-box"><h3 style="color:{THEME["sub"]};">💡 今日金句</h3><div style="font-size:24px;">“{display_ch}”</div><div style="color:gray;">— {v1.get("Reference","")}</div></div>', unsafe_allow_html=True)

    # 6.3 下方三欄
    c1, c2, c3 = st.columns([1, 1, 1.5])
    with c1:
        v_word = w1["Vocab"]
        d_url = f"dictionary.cambridge.org{quote(v_word)}"
        st.markdown(f'<div class="feature-box"><a href="{d_url}" target="_blank" class="dict-btn">🔍 字典</a><b>🔤 單字</b><br><h3>{v_word}</h3>{w1["Definition"]}</div>', unsafe_allow_html=True)
    with c2:
        p_word = p1["Phrase"]
        p_url = f"www.google.com{quote(p_word)}+meaning"
        st.markdown(f'<div class="feature-box"><a href="{p_url}" target="_blank" class="dict-btn">🔗 參考</a><b>🔗 片語</b><br><h4>{p_word}</h4>{p1["Definition"]}</div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="feature-box" style="background-color:#E3F2FD !important;"><b>📝 關鍵文法</b><br>{w1.get("Grammar", "保持學習！")}</div>', unsafe_allow_html=True)

with tab_play:
    # 6.4 動態 Lottie 動畫
    if LOTTIE_AVAILABLE:
        la, lb = st.columns(2)
        with la: st_lottie(load_lottieurl(LOTTIE_MARIO), height=150, key="m")
        with lb: st_lottie(load_lottieurl(LOTTIE_SNOOPY), height=150, key="s")
    
    if st.session_state.lives <= 0:
        st.error("💀 GAME OVER!")
        if st.button("重啟馬利歐"):
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
                st.error(f"答錯了！答案是: {target}")

with tab_tool:
    st.markdown("### 🧪 自動分類工具")
    txt = st.text_area("貼上文字...")
    if st.button("開始分類"):
        st.write("分類功能運作中...")
