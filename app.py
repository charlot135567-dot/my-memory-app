import streamlit as st
import pandas as pd
import requests
import io
import re
import os
import base64
from urllib.parse import quote
from PIL import Image

# --- 1. 頁面配置與主題 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide", page_icon="🐶")

THEME = {
    "bg": "#FFF9E3", 
    "box": "#FFFFFF", 
    "accent": "#FFCDD2", 
    "text": "#4A4A4A", 
    "sub": "#F06292", 
    "keyword": "#E91E63"
}

# --- 2. 嘗試載入動畫套件 ---
try:
    from streamlit_lottie import st_lottie
    LOTTIE_AVAILABLE = True
except ImportError:
    LOTTIE_AVAILABLE = False

# --- 3. 輔助功能 ---
@st.cache_data(ttl=600)
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- 4. Google Sheet 抓取 ---
SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
GIDS = {"📖 經節": "1454083804", "🔤 單字": "1400979824", "🔗 片語": "1657258260"}

@st.cache_data(ttl=300)
def fetch_data(gid):
    # 確保網址包含 https:// 以及中間的 /d/ 路徑
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status() # 檢查請求是否成功
        return pd.read_csv(io.StringIO(r.text)).fillna("")
    except Exception as e:
        st.sidebar.error(f"資料載入失敗，請檢查網路或 Sheet ID")
        return pd.DataFrame()

# --- 5. CSS 注入 (修正字體與按鈕連結效果) ---
st.markdown(f"""
    <style>
    @import url('fonts.googleapis.com');
    
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {THEME['bg']};
        font-family: 'Comic Neue', cursive;
    }}
    
    .feature-box {{
        background-color: {THEME['box']} !important;
        border-radius: 18px !important;
        padding: 15px !important;
        border: 2.5px solid {THEME['accent']} !important;
        box-shadow: 4px 4px 0px {THEME['accent']} !important;
        margin-bottom: 10px !important;
        min-height: 110px;
    }}
    
    .kw {{ color: {THEME['keyword']}; font-weight: bolder; font-size: 1.1em; background-color: #FFFF00; padding: 2px 4px; border-radius: 4px; }}
    
    .dict-btn {{
        color: {THEME['sub']} !important;
        text-decoration: none !important;
        font-weight: bold;
        float: right;
        font-size: 11px;
        border: 1px solid {THEME['sub']};
        padding: 1px 6px;
        border-radius: 4px;
    }}
    
    .fixed-bottom-img {{
        position: fixed;
        bottom: 10px;
        right: 15px;
        width: 130px;
        z-index: 99;
        opacity: 0.85;
        pointer-events: none;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. 側邊欄邏輯 ---
with st.sidebar:
    st.markdown("### 🐾 系統控制台")
    if 'score' not in st.session_state: st.session_state.score = 0
    if 'lives' not in st.session_state: st.session_state.lives = 3
    
    st.subheader(f"🏆 得分: {st.session_state.score}")
    st.subheader(f"❤️ 生命: {'❤️' * max(0, st.session_state.lives)}")
    
    if st.button("♻️ 刷新內容"):
        st.cache_data.clear()
        st.rerun()

# --- 7. 資料準備 ---
df_v = fetch_data(GIDS["📖 經節"])
df_w = fetch_data(GIDS["🔤 單字"])
df_p = fetch_data(GIDS["🔗 片語"])

# 初始抽取，存入 session_state 避免點擊按鈕時單字跑掉
if 'quiz_data' not in st.session_state or st.sidebar.button("換一題"):
    if not df_w.empty:
        st.session_state.quiz_data = df_w.sample(1).iloc[0].to_dict()
    else:
        st.session_state.quiz_data = {"Vocab": "Study", "Definition": "學習", "Grammar": "Keep going!"}

# --- 8. 主分頁架構 ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 隨記挑戰", "🧪 自動分類工具"])

with tab_home:
    # 隨機抽取展示資料
    v1 = df_v.sample(1).iloc[0] if not df_v.empty else {}
    w1 = st.session_state.quiz_data # 與挑戰題保持同步或獨立皆可，此處採用同步
    p1 = df_p.sample(1).iloc[0] if not df_p.empty else {"Phrase": "Keep it up", "Definition": "加油"}

    # 頂部裝飾圖
    img_files = ["snoopy1.png", "snoopy2.png", "snoopy3.png"] # 確保這些檔案存在
    img_cols = st.columns(6)
    for idx, img_name in enumerate(img_files):
        if os.path.exists(img_name):
            img_cols[idx].image(img_name, width=80)

    st.markdown('<div style="margin-top: -10px;"></div>', unsafe_allow_html=True)
    
    # 單字、片語、文法卡片
    c1, c2, c3 = st.columns([1, 1.2, 1.8])
    with c1:
        vocab = str(w1.get("Vocab", "Study"))
        # 修正後的劍橋辭典連結
        d_url = f"dictionary.cambridge.org{quote(vocab)}"
        st.markdown(f'''<div class="feature-box">
            <a href="{d_url}" target="_blank" class="dict-btn">🔍 字典</a>
            <small>🔤 單字</small><br><b>{vocab}</b><br><small>{w1.get("Definition","")}</small>
        </div>''', unsafe_allow_html=True)
        
    with c2:
        phrase = str(p1.get("Phrase", "Keep it up"))
        p_url = f"www.google.com{quote(phrase + ' meaning')}"
        st.markdown(f'''<div class="feature-box">
            <a href="{p_url}" target="_blank" class="dict-btn">🔗 參考</a>
            <small>🔗 片語</small><br><b>{phrase}</b><br><small>{p1.get("Definition","")}</small>
        </div>''', unsafe_allow_html=True)
        
    with c3:
        gram = w1.get("Grammar", "保持學習，每天進步！")
        st.markdown(f'''<div class="feature-box" style="background-color:#E3F2FD !important;">
            <small>📝 關鍵文法</small><br><div style="font-size:14px; margin-top:5px;">{gram}</div>
        </div>''', unsafe_allow_html=True)

    # 今日金句 (修正後的關鍵字高亮邏輯)
    raw_ch = v1.get("Chinese", "載入中...")
    kw_str = str(v1.get("Keyword", "") or "")
    display_ch = raw_ch
    if kw_str:
        keywords = [k.strip() for k in kw_str.split(",") if k.strip()]
        for k in keywords:
            display_ch = re.sub(re.escape(k), f'<span class="kw">{k}</span>', display_ch, flags=re.IGNORECASE)
            
    st.markdown(f'''<div class="feature-box" style="min-height:140px;">
        <h3 style="color:{THEME["sub"]}; margin-top:0;">💡 今日金句</h3>
        <div style="font-size:26px; line-height:1.4; font-weight:bold;">“{display_ch}”</div>
        <div style="color:gray; margin-top:10px; text-align:right;">— {v1.get("Reference","")}</div>
    </div>''', unsafe_allow_html=True)

with tab_play:
    st.subheader("🎯 瞬時翻譯挑戰")
    
    # 載入 Lottie 動畫 (範例 URL：狗狗動畫)
    if LOTTIE_AVAILABLE:
        lottie_dog = load_lottieurl("assets10.lottiefiles.com")
        if lottie_dog:
            st_lottie(lottie_dog, height=150, key="play_anim")
    
    target_vocab = str(st.session_state.quiz_data.get("Vocab", "")).strip()
    target_def = st.session_state.quiz_data.get("Definition", "")
    
    st.write(f"題目： 請輸入「 **{target_def}** 」的英文單字")
    
    # 使用 Form 確保輸入流暢
    with st.form(key="quiz_form"):
        user_ans = st.text_input("輸入答案...", key="ans_input").strip()
        submit = st.form_submit_button("檢查答案")
        
        if submit:
            if user_ans.lower() == target_vocab.lower():
                st.balloons()
                st.success(f"太棒了！答案正是 {target_vocab}")
                st.session_state.score += 10
                # 答對後自動重抽
                if not df_w.empty:
                    st.session_state.quiz_data = df_w.sample(1).iloc[0].to_dict()
                st.write("正在準備下一題...")
                # 稍微延遲後刷新
                st.rerun()
            else:
                st.session_state.lives -= 1
                st.error(f"答錯囉！正確答案是: {target_vocab}")
                if st.session_state.lives <= 0:
                    st.warning("生命值歸零，再接再厲！")
                    st.session_state.lives = 3
                    st.session_state.score = 0

with tab_tool:
    st.info("🧪 自動分類工具已就緒，您可以開始建立新的標籤邏輯。")
    st.write("2026 版系統運行中 - 穩定度：高")

# --- 9. 固定裝飾圖 (Base64 確保穩定顯示) ---
# 若有 snoopy_bottom.png 則會顯示在右下角
if os.path.exists("snoopy_bottom.png"):
    with open("snoopy_bottom.png", "rb") as f:
        data = base64.b64encode(f.read()).decode()
        st.markdown(f'<img src="data:image/png;base64,{data}" class="fixed-bottom-img">', unsafe_allow_html=True)
