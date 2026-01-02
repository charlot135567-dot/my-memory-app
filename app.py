import streamlit as st
import pandas as pd
import requests
import io
import re
import random
import time
import json
from urllib.parse import quote

# --- 1. 頁面配置與主題設定 (僅保留奶油黃) ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide", page_icon="🐶")

THEME = {"bg": "#FFF9E3", "box": "#FFFFFF", "accent": "#FFCDD2", "text": "#4A4A4A", "sub": "#F06292", "keyword": "#E91E63"}

# --- Lottie 動畫加載函數 ---
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        return r.json()
    except requests.exceptions.RequestException:
        return None

# Lottie URLs for Mario and Snoopy (Example from Lottiefiles.com)
LOTTIE_MARIO = "assets9.lottiefiles.com"
LOTTIE_SNOOPY = "assets7.lottiefiles.com"

# --- 2. 側邊欄控制台 ---
with st.sidebar:
    st.markdown("### 🐾 系統控制台")
    st.markdown(f"**當前主題：Snoopy Retro (奶油黃)**")
    
    st.divider()
    if 'score' not in st.session_state: st.session_state.score = 0
    if 'lives' not in st.session_state: st.session_state.lives = 3
    if 'count' not in st.session_state: st.session_state.count = 0
    
    st.subheader(f"🏆 累計得分: {st.session_state.score}")
    st.subheader(f"❤️ 剩餘生命: {'❤️' * st.session_state.lives}")
    
    st.progress(min(st.session_state.count / 20.0, 1.0))
    st.caption(f"今日學習進度: {st.session_state.count}/20")

    if st.button("♻️ 刷新內容並同步"):
        st.cache_data.clear()
        st.rerun()

# --- 3. CSS 注入 (僅保留必要樣式) ---
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
        min-height: 120px; /* 確保小框框有基本高度 */
    }}
    
    .typing {{
        overflow: hidden; border-right: .15em solid orange; white-space: nowrap;
        animation: typing 3s steps(40, end), blink-caret .75s step-end infinite;
    }}
    @keyframes typing {{ from {{ width: 0 }} to {{ width: 100% }} }}
    @keyframes blink-caret {{ from, to {{ border-color: transparent }} 50% {{ border-color: orange; }} }}

    .dict-btn {{ color: {THEME['sub']}; text-decoration: none; font-weight: bold; float: right; font-size: 12px; }}
    .kw {{ color: {THEME['keyword']}; font-weight: bolder; font-size: 26px; }} /* 關鍵字樣式 */
    </style>
    """, unsafe_allow_html=True)

# --- 4. 資料庫抓取與分類邏輯 ---
SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
GIDS = {"📖 經節": "1454083804", "🔤 單字": "1400979824", "🔗 片語": "1657258260"}

@st.cache_data(ttl=300)
def fetch_data(gid):
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=10)
        return pd.read_csv(io.StringIO(r.text)).fillna("")
    except: return pd.DataFrame()

def heuristic_classify(item):
    item = item.strip()
    if re.search(r'\b\d{1,3}:\d{1,3}\b', item): return "Verses"
    tokens = item.split()
    if len(tokens) <= 1: return "Words"
    if 2 <= len(tokens) <= 6: return "Phrases"
    return "Verses"

# --- 5. 主分頁架構 ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 隨機挑戰", "🧪 自動分類工具"])

with tab_home:
    df_v = fetch_data(GIDS["📖 經節"])
    df_w = fetch_data(GIDS["🔤 單字"])
    df_p = fetch_data(GIDS["🔗 片語"])

    v1 = df_v.sample(1).iloc[0] if not df_v.empty else {"Chinese": "載入中...", "Reference": "", "Keyword": ""}
    w1 = df_w.sample(1).iloc[0] if not df_w.empty else {"Vocab": "Study", "Definition": "學習", "Grammar": ""}
    p1 = df_p.sample(1).iloc[0] if not df_p.empty else {"Phrase": "Keep it up", "Definition": "繼續加油", "Grammar": ""}

    # 5.1 顯示史努比圖片 (假設圖片已在 GitHub repo 根目錄)
    st.markdown('<div style="text-align:center;">', unsafe_allow_html=True)
    img_files = ["f364bd220887627.67cae1bd07457.jpg", "183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg", "68254faebaafed9dafb41918f74c202e.jpg"]
    for img_name in img_files:
        if os.path.exists(img_name):
            st.image(img_name, width=150)
    st.markdown('</div>', unsafe_allow_html=True)


    # 5.2 上方大框 (經節 + 關鍵字標色)
    chinese_text = v1["Chinese"]
    keyword = v1.get("Keyword", "").strip()
    if keyword and keyword in chinese_text:
        marked_text = chinese_text.replace(keyword, f'<span class="kw">{keyword}</span>')
    else:
        marked_text = chinese_text
        
    st.markdown(f'<div class="feature-box"><h3 style="color:{THEME["sub"]};">💡 今日金句</h3><div class="typing" style="font-size:24px;">“{marked_text}”</div><div style="color:gray; margin-top:10px;">— {v1["Reference"]}</div></div>', unsafe_allow_html=True)

    # 5.3 下方三欄 (字典連結, 片語/文法連結)
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        vocab = w1["Vocab"]
        dict_url = f"dictionary.cambridge.org{quote(vocab)}"
        st.markdown(f'<div class="feature-box"><a href="{dict_url}" target="_blank" class="dict-btn">🔍 字典</a><b style="color:{THEME["sub"]};">🔤 單字</b><br><span style="font-size:20px;">{vocab}</span><br><small>{w1["Definition"]}</small></div>', unsafe_allow_html=True)
    with c2:
        phrase = p1["Phrase"]
        grammar_search_url = f"www.google.com{quote(phrase + ' Grammar usage')}"
        st.markdown(f'<div class="feature-box"><a href="{grammar_search_url}" target="_blank" class="dict-btn">🔗 參考</a><b style="color:{THEME["sub"]};">🔗 片語</b><br><span style="font-size:18px;">{phrase}</span><br><small>{p1["Definition"]}</small></div>', unsafe_allow_html=True)
    with c3:
        gram = w1.get("Grammar") if pd.notna(w1.get("Grammar")) else "保持學習！"
        st.markdown(f'<div class="feature-box" style="background-color:#E3F2FD !important;"><b style="color:#0288D1;">📝 關鍵文法</b><br><p style="font-size:16px;">{gram}</p></div>', unsafe_allow_html=True)

# --- TAB 2: 闖關挑戰 (Lottie 動畫遊戲) ---
with tab_play:
    # 使用 Lottie 動畫代替文字圖示
    col_lottie1, col_lottie2, col_lottie3 = st.columns([1, 1, 1])
    with col_lottie1:
        if st.session_state.lives > 0:
            st_lottie(load_lottieurl(LOTTIE_MARIO), height=100, key="mario_run")
    with col_lottie3:
        st_lottie(load_lottieurl(LOTTIE_SNOOPY), height=100, key="snoopy_dance")

    if st.session_state.lives <= 0:
        st.error("💀 GAME OVER! 馬利歐需要休息...")
        if st.button("使用 1UP 蘑菇重生"):
            st.session_state.lives = 3
            st.rerun()
    else:
        st.subheader("⚡️ 瞬時翻譯挑戰 (中翻英)")
        q_item = w1 if random.random() > 0.5 else p1
        target = q_item.get("Vocab") or q_item.get("Phrase", "")
        st.write(f"題目： 「 **{q_item.get('Definition')}** 」 的正確翻譯是？")
        ans = st.text_input("在此輸入答案...", key="game_input")
        if st.button("提交答案"):
            if ans.lower().strip() == str(target).lower().strip():
                st.balloons()
                st.session_state.score += 10
                st.session_state.count += 1
                st.success("✅ 正確！")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.lives -= 1
                st.error(f"❌ 答錯了！生命值 -1。")

# --- TAB 3: 自動分類工具 ---
with tab_tool:
    st.markdown("### 🧪 AI 自動分類與導出")
    input_text = st.text_area("在此貼上文章...", height=200)
    if st.button("🚀 開始分析分類"):
        lines = re.split(r'\n+|(?<=[。！？\.\?\!;；])\s*', input_text)
        results = [{"內容": l.strip(), "建議分類": heuristic_classify(l)} for l in lines if l.strip()]
        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)
            # Add download button functionality here if needed
