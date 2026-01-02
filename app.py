import streamlit as st
import pandas as pd
import requests
import io
import re
import os
import base64
import random
import time
from urllib.parse import quote

# --- 1. 頁面基礎配置 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide", page_icon="🐶")

# --- 2. 初始化 Session State ---
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = {"Vocab": "Study", "Definition": "學習", "Grammar": "保持學習，每天進步！"}
if 'verse_data' not in st.session_state:
    st.session_state.verse_data = {"Chinese": "凡事都有定期，天下萬務都有定時。", "Reference": "傳道書 3:1", "Keyword": "定時"}
if 'phrase_data' not in st.session_state:
    st.session_state.phrase_data = {"Phrase": "Keep it up", "Definition": "加油"}
if 'score' not in st.session_state: st.session_state.score = 0
if 'lives' not in st.session_state: st.session_state.lives = 3

THEME = {"bg": "#FFF9E3", "box": "#FFFFFF", "accent": "#FFCDD2", "text": "#4A4A4A", "sub": "#F06292", "keyword": "#E91E63"}

# --- 3. 資料抓取函數 ---
@st.cache_data(ttl=300)
def fetch_data(gid):
    SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return pd.read_csv(io.StringIO(r.text)).fillna("")
    except: pass
    return pd.DataFrame()

# --- 4. CSS 樣式 ---
st.markdown(f"""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [data-testid="stAppViewContainer"] {{ background-color: {THEME['bg']}; font-family: 'Comic Neue', cursive; }}
    .feature-box {{
        background-color: {THEME['box']} !important;
        border-radius: 18px !important;
        padding: 18px !important;
        border: 2.5px solid {THEME['accent']} !important;
        box-shadow: 4px 4px 0px {THEME['accent']} !important;
        margin-bottom: 12px !important;
    }}
    .kw {{ color: {THEME['keyword']}; font-weight: bolder; font-size: 1.2em; background-color: #FFFF00; padding: 2px 4px; border-radius: 4px; }}
    .dict-btn {{ color: {THEME['sub']} !important; text-decoration: none !important; font-weight: bold; float: right; font-size: 11px; border: 1px solid {THEME['sub']}; padding: 1px 6px; border-radius: 4px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. 主內容渲染 ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 隨記挑戰", "🧪 自動分類工具"])

# --- TAB 1: 我的書桌 ---
with tab_home:
    v1 = st.session_state.verse_data
    w1 = st.session_state.quiz_data
    p1 = st.session_state.phrase_data

    # 第一排：單字 (1) + 片語 (1) + 史努比圖片 (1)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        voc = w1.get("Vocab", "Study")
        st.markdown(f'<div class="feature-box"><a href="dictionary.cambridge.org{quote(str(voc))}" target="_blank" class="dict-btn">🔍 字典</a><small>🔤 單字</small><br><b>{voc}</b><br><small>{w1.get("Definition","")}</small></div>', unsafe_allow_html=True)
    with c2:
        phr = p1.get("Phrase", "Keep it up")
        st.markdown(f'<div class="feature-box"><a href="www.google.com{quote(str(phr))}+meaning" target="_blank" class="dict-btn">🔗 參考</a><small>🔗 片語</small><br><b>{phr}</b><br><small>{p1.get("Definition","")}</small></div>', unsafe_allow_html=True)
    with c3:
        # 放第一張圖在右上角
        top_img = "f364bd220887627.67cae1bd07457.jpg"
        if os.path.exists(top_img):
            st.image(top_img, width=120)

    # 第二排：今日金句 (中間大框)
    raw_ch = v1.get("Chinese", "")
    kw = str(v1.get("Keyword", ""))
    disp = raw_ch.replace(kw, f'<span class="kw">{kw}</span>') if kw and kw in raw_ch else raw_ch
    st.markdown(f'<div class="feature-box" style="min-height:140px;"><h3 style="color:{THEME["sub"]}; margin-top:0; font-family: "Gloria Hallelujah", cursive;">💡 今日金句</h3><div style="font-size:26px; line-height:1.4; font-weight:bold;">“{disp}”</div><div style="color:gray; margin-top:10px; text-align:right;">— {v1.get("Reference","")}</div></div>', unsafe_allow_html=True)

    # 第三排：文法 (左側大框) + 史努比圖片 (右側)
    c4, c5 = st.columns([2, 1])
    with c4:
        st.markdown(f'<div class="feature-box" style="background-color:#E3F2FD !important; height: 100%;"><small>📝 關鍵文法</small><br><div style="font-size:15px; margin-top:8px;">{w1.get("Grammar", "保持學習，每天進步！")}</div></div>', unsafe_allow_html=True)
    with c5:
        bottom_img = "183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg"
        if os.path.exists(bottom_img):
            st.image(bottom_img, width=150)

# --- TAB 2: 隨記挑戰 ---
with tab_play:
    col_txt, col_img = st.columns([2, 1])
    with col_txt:
        st.subheader("🎯 瞬時翻譯挑戰")
        st.write(f"題目： 請輸入「 **{st.session_state.quiz_data.get('Definition')}** 」的英文單字")
        ans = st.text_input("在此輸入答案...", key="play_input").strip()
        if st.button("提交答案"):
            if ans.lower() == str(st.session_state.quiz_data.get("Vocab")).lower():
                st.balloons()
                st.session_state.score += 10
                st.success("🎉 太棒了！答對了！(請點擊側邊欄刷新下一題)")
            else:
                st.session_state.lives -= 1
                st.error(f"❌ 答錯了！正確答案是: {st.session_state.quiz_data.get('Vocab')}")
    
    with col_img:
        target_img = "68254faebaafed9dafb41918f74c202e.jpg"
        if os.path.exists(target_img):
            st.image(target_img, caption="Cheers!", width=200)

# --- TAB 3: 自動分類工具 ---
with tab_tool:
    st.info("🧪 自動分類工具已就緒。")

# --- 側邊欄 ---
with st.sidebar:
    st.markdown("### 🐾 系統控制台")
    st.subheader(f"🏆 得分: {st.session_state.score}")
    st.subheader(f"❤️ 生命: {'❤️' * max(0, st.session_state.lives)}")
    if st.button("♻️ 刷新內容"):
        df_w = fetch_data("1400979824")
        df_v = fetch_data("1454083804")
        df_p = fetch_data("1657258260")
        if not df_w.empty: st.session_state.quiz_data = df_w.sample(1).iloc[0].to_dict()
        if not df_v.empty: st.session_state.verse_data = df_v.sample(1).iloc[0].to_dict()
        if not df_p.empty: st.session_state.phrase_data = df_p.sample(1).iloc[0].to_dict()
        st.rerun()
