import streamlit as st
import pandas as pd
import requests
import io
import re
import json
import os
from datetime import datetime

# --- 1. 頁面配置 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide")

# --- 2. 柔和配色 CSS (淺黃、淺紅、日韓字體) ---
st.markdown("""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Comic Neue', 'Noto Sans JP', 'Noto Sans KR', cursive;
        background-color: #FFF9E3;
    }
    .main-title {
        font-family: 'Gloria Hallelujah', cursive;
        color: #4A4A4A; text-align: center; font-size: 45px; font-weight: bold; padding: 20px;
    }
    .stat-card {
        background-color: #FFFFFF; border: 2px solid #FFCDD2; border-radius: 15px;
        padding: 15px; text-align: center; box-shadow: 5px 5px 0px #FFCDD2;
    }
    .verse-display {
        font-size: 28px; line-height: 1.6; font-weight: bold; color: #333333;
        background-color: #FFFFFF; border-left: 12px solid #FFD54F;
        padding: 25px; margin: 20px 0; border-radius: 10px; box-shadow: 6px 6px 0px #FFF9C4;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title">✨ GOOD GRIEF! MEMORY LOGIC</h1>', unsafe_allow_html=True)

# --- 3. 設定區 ---
SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
GIDS = {"📖 經節": "1454083804", "🔤 單字": "1400979824", "🔗 片語": "1657258260"}

if 'exp' not in st.session_state: st.session_state.exp = 0
if 'current_item' not in st.session_state: st.session_state.current_item = None
if 'revealed' not in st.session_state: st.session_state.revealed = False

# --- 4. 資料抓取函式 (備援機制) ---
@st.cache_data(ttl=600)
def fetch_data(gid):
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return pd.read_csv(io.StringIO(r.text)).fillna("")
    except: pass
    return pd.DataFrame()

# --- 5. 分頁導覽 ---
tab_play, tab_tool = st.tabs(["🎮 記憶與多語對照", "🧪 自動分類工具"])

# --- 分頁 1: 記憶挑戰模式 ---
with tab_play:
    col_l, col_r = st.columns([1, 2])
    
    with col_l:
        st.markdown(f'<div class="stat-card"><h3>🏆 累積 EXP</h3><h1>{st.session_state.exp}</h1></div>', unsafe_allow_html=True)
        category = st.radio("選擇類別", list(GIDS.keys()), horizontal=True)
        if st.button("🎲 抽取題目"):
            df = fetch_data(GIDS[category])
            if not df.empty:
                st.session_state.current_item = df.sample(1).iloc[0].to_dict()
                st.session_state.revealed = False

    with col_r:
        if st.session_state.current_item:
            item = st.session_state.current_item
            st.markdown(f'<div class="verse-display">{item.get("Chinese") or item.get("Vocab")}</div>', unsafe_allow_html=True)
            
            if not st.session_state.revealed:
                if st.button("👁️ 顯示多國譯本對照 (日韓標準譯本)"):
                    st.session_state.revealed = True
                    st.session_state.exp += 1
                    st.rerun()
            else:
                st.success(f"🇺🇸 **English:** {item.get('English', 'N/A')}")
                if category == "📖 經節":
                    st.info(f"🇯🇵 **日本語 (聖書 新共同譯):** {item.get('Japanese', '尚未錄入標準譯本')}")
                    st.warning(f"🇰🇷 **한국어 (개역개정):** {item.get('Korean', '尚未錄入標準譯本')}")
                else:
                    st.info(f"💡 **定義/例句:** {item.get('Definition', 'N/A')}")
                
                if st.button("✅ 記住了"):
                    st.session_state.current_item = None
                    st.rerun()

# --- 分頁 2: 自動分類工具 ---
with tab_tool:
    st.subheader("🧪 批次文字自動分類")
    input_text = st.text_area("請在此貼上聖經經文或單字文章：", height=200)
    
    if input_text:
        # 分類邏輯：有冒號或長句視為經節，短的視為單字/片語
        lines = [p.strip() for p in re.split(r'[。\.\n]+', input_text) if p.strip()]
        processed = []
        for l in lines:
            cat = "Verses" if ":" in l or len(l) > 15 else "Words"
            processed.append({"內容": l, "類型預測": cat})
        
        df_edit = st.data_editor(pd.DataFrame(processed), num_rows="dynamic")
        
        if st.button("📦 產生 Excel 下載"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_edit.to_excel(writer, index=False)
            st.download_button("⬇️ 下載檔案", output.getvalue(), f"memory_{datetime.now().strftime('%m%d')}.xlsx")

st.sidebar.caption("2026 Memory Logic v2.0 - 已啟用日韓標準譯本支援")
