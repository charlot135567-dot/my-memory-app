import streamlit as st
import pandas as pd
import requests
import re
import os
import base64
import io

# --- 1. 頁面基礎配置 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide", page_icon="🐶")

# --- 2. 初始化 Session State ---
def init_session():
    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = {"Text_CN": "凡事都有定期，天下萬務都有定時。", "Text_EN": "To everything there is a season."}
    if 'verse_data' not in st.session_state:
        st.session_state.verse_data = {"Chinese": "凡事都有定期，天下萬務都有定時。", "Reference": "傳道書 3:1", "Keyword": "定時"}
    if 'word_data' not in st.session_state:
        st.session_state.word_data = {"Vocab": "Study", "Definition": "學習", "Grammar": "保持學習，每天進步！"}
    if 'phrase_data' not in st.session_state:
        st.session_state.phrase_data = {"Phrase": "Keep it up", "Definition": "繼續加油"}
    if 'final_df' not in st.session_state:
        st.session_state.final_df = pd.DataFrame(columns=["Reference", "English", "Chinese", "Key word", "Grammar", "Japanese", "Korean", "Thai"])
    if 'score' not in st.session_state: st.session_state.score = 0

init_session()

THEME = {"bg": "#FFF9E3", "box": "#FFFFFF", "accent": "#FFCDD2", "text": "#4A4A4A", "sub": "#F06292", "keyword": "#E91E63"}

# --- 3. 核心工具類別 ---
class BibleAutomator:
    def __init__(self):
        # 這是正確的寫法
        self.api_base = "https://bible-api.com/" 
        self.analysis_keywords = ['Subject', 'Verb', '補全後', '例句', '譯為', '指代', '語氣', '省略', '主謂', 'Agreement']
        self.lang_map = {"CN": "cuv", "EN": "web", "JA": "jpn", "KO": "kor", "TH": "tha"}
        
    def fetch_real_bible(self, ref, lang_key):
        """抓取真實聖經版本 (2026 推薦版本)"""
        trans = self.lang_map.get(lang_key, "web")
        try:
            ref_clean = ref.replace(" ", "+")
            r = requests.get(f"{self.api_base}{ref_clean}?translation={trans}", timeout=7)
            if r.status_code == 200:
                return r.json().get('text', '').strip()
        except: pass
        return f"[無法獲取 {lang_key} 版本]"

    def extract_keywords(self, text):
        """選取 6 字母以上中高級單字"""
        if not text: return ""
        stop_words = {'through', 'between', 'against', 'before', 'because', 'everything', 'handiwork'}
        words = re.findall(r'\b[A-Za-z]{6,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        return ", ".join(list(dict.fromkeys(keywords))[:2])

    def parse_manual(self, raw_text):
        """將手動筆記拆解並自動分類至欄位"""
        book_match = re.search(r'([\u4e00-\u9fa5]+)(\d+)(篇|章)?', raw_text)
        book_name = book_match.group(1) if book_match else ""
        
        # 依照座標分割塊
        blocks = re.split(r'\n(?=\d{1,3}:\d{1,3})', raw_text)
        final_list = []
        
        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if not lines: continue
            
            ref_match = re.match(r'^(\d+:\d+)', lines[0])
            if not ref_match: continue
            
            ref_val = f"{book_name}{ref_match.group(1)}"
            entry = {"Reference": ref_val, "Chinese": "", "English": "", "Key word": "", "Grammar": ""}
            
            grammar_lines = []
            english_accumulator = []
            
            for line in lines:
                # 1. 識別中文
                if re.search(r'[\u4e00-\u9fa5]', line) and not any(k in line for k in self.analysis_keywords) and not entry["Chinese"]:
                    entry["Chinese"] = re.sub(r'^\d+:\d+\s*', '', line)
                # 2. 識別英文 (改進版：支援跨行)
                elif re.match(r'^[A-Za-z0-9\s.,;!\?\'\"()\-\:]+$', line) and not any(k in line for k in self.analysis_keywords):
                    cleaned_eng = re.sub(r'^\d+:\d+\s*|^\d+\s*', '', line)
                    if cleaned_eng: english_accumulator.append(cleaned_eng)
                # 3. 識別文法說明
                else:
                    grammar_lines.append(line)
            
            entry["English"] = " ".join(english_accumulator)
            entry["Grammar"] = "\n".join(grammar_lines)
            entry["Key word"] = self.extract_keywords(entry["English"])
            
            # 自動抓取多國語言
            with st.spinner(f"正在同步 {ref_val} 多國譯本..."):
                entry["Japanese"] = self.fetch_real_bible(ref_val, "JA")
                entry["Korean"] = self.fetch_real_bible(ref_val, "KO")
                entry["Thai"] = self.fetch_real_bible(ref_val, "TH")
            
            final_list.append(entry)
        return pd.DataFrame(final_list)

# --- 4. 圖片與樣式處理 ---
@st.cache_data(ttl=600)
def get_img_base64(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        except: return None
    return None

st.markdown(f"""
    <style>
    .stApp {{ background-color: {THEME['bg']}; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
    .feature-box {{
        background: {THEME['box']}; border-radius: 15px; padding: 20px;
        border: 2px solid {THEME['accent']}; box-shadow: 4px 4px 0px {THEME['accent']};
        margin-bottom: 15px;
        color: {THEME['text']};
    }}
    .img-container img {{ border-radius: 12px; width: 100%; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. UI 標籤頁 ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 隨記挑戰", "🧪 自動分類工具"])

with tab_home:
    v1, w1, p1 = st.session_state.verse_data, st.session_state.word_data, st.session_state.phrase_data
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.markdown(f'<div class="feature-box"><h3>💡 今日金句</h3><p style="font-size:20px; font-weight:500;">{v1["Chinese"]}</p><div style="text-align:right; font-style:italic;">— {v1["Reference"]}</div></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="feature-box"><small>🔤 單字</small><br><b style="font-size:22px; color:{THEME["keyword"]};">{w1["Vocab"]}</b><br>{w1["Definition"]}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="feature-box"><small>🔗 片語</small><br><b style="font-size:22px; color:{THEME["sub"]};">{p1["Phrase"]}</b><br>{p1["Definition"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="feature-box" style="background-color:#F0F7FF;"><small>📝 文法點撥</small><br>{w1["Grammar"]}</div>', unsafe_allow_html=True)
    
    with col_side:
        img_b64 = get_img_base64("f364bd220887627.67cae1bd07457.jpg")
        if img_b64: st.markdown(f'<div class="img-container"><img src="{img_b64}"></div>', unsafe_allow_html=True)

with tab_play:
    st.subheader("🎯 翻譯練習")
    curr = st.session_state.quiz_data
    col_q, col_img = st.columns([2, 1])
    with col_q:
        st.info(f"請嘗試翻譯這句話：\n\n**{curr['Text_CN']}**")
        if st.button("✨ 顯示正確答案"):
            st.success(f"參考答案：{curr['Text_EN']}")
            st.balloons()
    with col_img:
        img_play = get_img_base64("68254faebaafed9dafb41918f74c202e.jpg")
        if img_play: st.markdown(f'<div class="img-container"><img src="{img_play}"></div>', unsafe_allow_html=True)

with tab_tool:
    st.markdown("### 🧪 聖經學習分類器 (2026 版)")
    mode = st.radio("模式選擇", ["手動解析大量筆記", "指定章節全自動抓取"], horizontal=True)
    auto = BibleAutomator()
    
    if mode == "手動解析大量筆記":
        raw_text = st.text_area("請在此貼上您的筆記 (包含座標、經文與解析)：", height=300, 
                               placeholder="例：詩篇19篇\n19:1 諸天述說...\n19:1 The heavens...\nGrammar: Subject is...")
        if st.button("🚀 執行分類匯出"):
            if raw_text:
                st.session_state.final_df = auto.parse_manual(raw_text)
                st.success(f"成功解析 {len(st.session_state.final_df)} 節經文！")
                st.dataframe(st.session_state.final_df, use_container_width=True)
    
    else:
        ref_input = st.text_input("輸入要檢索的章節 (例如: Psalms 19:1-4)", "Psalms 19:1")
        if st.button("🔍 AI 全自動檢索"):
            with st.spinner("正在連線全球聖經資料庫..."):
                res = {
                    "Reference": ref_input,
                    "English": auto.fetch_real_bible(ref_input, "EN"),
                    "Chinese": auto.fetch_real_bible(ref_input, "CN"),
                    "Japanese": auto.fetch_real_bible(ref_input, "JA"),
                    "Korean": auto.fetch_real_bible(ref_input, "KO"),
                    "Thai": auto.fetch_real_bible(ref_input, "TH")
                }
                res["Key word"] = auto.extract_keywords(res["English"])
                res["Grammar"] = "AI 自動抓取建議：請參考上下文進行文法對仗分析。"
                st.session_state.final_df = pd.DataFrame([res])
                st.dataframe(st.session_state.final_df, use_container_width=True)

    if not st.session_state.final_df.empty:
        csv_data = st.session_state.final_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 匯出為 Verse/Words/Phrases 表格 (CSV)", csv_data, "Bible_Study_Data.csv", "text/csv")
