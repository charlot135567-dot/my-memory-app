import streamlit as st
import pandas as pd
import requests
import re
import os
import base64
import random

# --- 1. 頁面配置 (2026 最新標準) ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide", page_icon="🐶")

# --- 2. 初始化 Session State (確保功能不消失的核心) ---
if 'final_df' not in st.session_state:
    st.session_state.final_df = pd.DataFrame(columns=["Reference", "English", "Chinese", "Key word", "Grammar", "Japanese", "Korean", "Thai"])

# 初始化 5 題挑戰題目 (260103 新增需求)
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = [
        {"q": "凡事都有定期，天下萬務都有定時。", "a": "To everything there is a season, and a time to every purpose under the heaven.", "lang": "English (WEB)"},
        {"q": "神愛世人，甚至將他的獨生子賜給他們。", "a": "For God so loved the world, that he gave his only begotten Son.", "lang": "English (WEB)"},
        {"q": "起初，神創造天地。", "a": "はじめに、神は天と地を創造された。", "lang": "Japanese (JPN)"},
        {"q": "耶和華是我的牧者，我必不至缺乏。", "a": "여호와는 나의 목자시니 내게 부족함이 없으리로다.", "lang": "Korean (KOR)"},
        {"q": "你要專心仰賴耶和華。", "a": "จงวางใจในพระยาห์เวห์ด้วยสุดใจของเจ้า", "lang": "Thai (THA)"}
    ]

# --- 3. 核心工具類別 ---
class BibleAutomator:
    def __init__(self):
        self.api_base = "bible-api.com"
        self.lang_map = {"CN": "cuv", "EN": "web", "JA": "jpn", "KO": "kor", "TH": "tha"}

    @st.cache_data(ttl=3600)
    def fetch_data(_self, ref, lang_key):
        trans = _self.lang_map.get(lang_key, "web")
        try:
            clean_ref = ref.replace(" ", "+")
            r = requests.get(f"{_self.api_base}{clean_ref}?translation={trans}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                return {v['verse']: v['text'].strip() for v in data.get('verses', [])} if 'verses' in data else {data.get('verse', 0): data.get('text', '').strip()}
        except: pass
        return {}

    def extract_keywords(self, text):
        if not text: return ""
        words = re.findall(r'\b[A-Za-z]{6,}\b', text)
        return ", ".join(list(dict.fromkeys(words))[:2])

    def process_range(self, ref_input, manual_grammar_map=None):
        en_map = self.fetch_data(ref_input, "EN")
        cn_map = self.fetch_data(ref_input, "CN")
        ja_map = self.fetch_data(ref_input, "JA")
        ko_map = self.fetch_data(ref_input, "KO")
        th_map = self.fetch_data(ref_input, "TH")
        book_part = re.sub(r':\d+.*$', '', ref_input)
        rows = []
        for v_num in sorted(en_map.keys()):
            rows.append({
                "Reference": f"{book_part}:{v_num}", "English": en_map.get(v_num, ""),
                "Chinese": cn_map.get(v_num, ""), "Key word": self.extract_keywords(en_map.get(v_num, "")),
                "Grammar": manual_grammar_map.get(v_num, "AI 待分析") if manual_grammar_map else "AI 待分析",
                "Japanese": ja_map.get(v_num, "-"), "Korean": ko_map.get(v_num, "-"), "Thai": th_map.get(v_num, "-")
            })
        return pd.DataFrame(rows)

auto_tool = BibleAutomator()

# --- 4. 資源定義 (解決圖片不見的問題) ---
@st.cache_data
def get_img_64(file):
    # 如果本地有圖讀本地，沒圖顯示 Placeholder 確保 UI 不跑版
    if os.path.exists(file):
        with open(file, "rb") as f:
            return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
    return "via.placeholder.com"

st.markdown("""
    <style>
    .stApp { background-color: #FFFDF5; }
    .feature-box { background: white; border-radius: 12px; padding: 18px; border: 1px solid #E0E0E0; margin-bottom: 15px; }
    .grammar-box { min-height: 310px; background-color: #F8FBFF !important; border-left: 5px solid #64B5F6 !important; }
    .snoopy-container img { width: 100%; border-radius: 10px; margin-bottom: 10px; border: 1px solid #DDD; }
    </style>
""", unsafe_allow_html=True)

# --- 5. UI 呈現 ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 翻譯挑戰", "🧪 自動工具"])

with tab_home:
    col_l, col_r = st.columns([2.5, 1])
    with col_l:
        st.markdown('<div class="feature-box"><h3>💡 今日金句</h3>傳道書 3:1<br>凡事都有定期，天下萬務都有定時。</div>', unsafe_allow_html=True)
        st.markdown('<div class="feature-box grammar-box">📝 <b>文法重點說明</b><br>此框高度與右側史努比圖案齊平。</div>', unsafe_allow_html=True)
    with col_r:
        # 確保兩張史努比圖顯示
        for img_name in ["f364bd220887627.67cae1bd07457.jpg", "183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg"]:
            img_data = get_img_64(img_name)
            st.markdown(f'<div class="snoopy-container"><img src="{img_data}"></div>', unsafe_allow_html=True)

with tab_play:
    st.subheader("🎯 多國語言翻譯挑戰 (5 題版)")
    for i, item in enumerate(st.session_state.quiz_data):
        with st.expander(f"第 {i+1} 題：{item['q'][:10]}...", expanded=(i==0)):
            st.write(f"**題目：** {item['q']}")
            st.write(f"**目標語言：** {item['lang']}")
            ans = st.text_input(f"在此輸入翻譯...", key=f"ans_{i}")
            if st.button(f"檢查第 {i+1} 題答案"):
                if ans:
                    st.info(f"💡 參考答案：{item['a']}")
                    st.balloons()
                else:
                    st.warning("請先輸入答案喔！")

with tab_tool:
    st.subheader("🧪 聖經自動工具")
    ref_in = st.text_input("輸入範圍", "Psalm 20:1-3")
    if st.button("🔍 開始生成"):
        st.session_state.final_df = auto_tool.process_range(ref_in)
    st.dataframe(st.session_state.final_df, width="stretch")
