import streamlit as st
import pandas as pd
import requests
import re
import os
import base64

# --- 1. 頁面基礎配置 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide", page_icon="🐶")

# --- 2. 初始化 Session State ---
if 'final_df' not in st.session_state:
    st.session_state.final_df = pd.DataFrame(columns=["Reference", "English", "Chinese", "Key word", "Grammar", "Japanese", "Korean", "Thai"])

# --- 3. 核心工具類別 ---
class BibleAutomator:
    def __init__(self):
        self.api_base = "bible-api.com"
        self.lang_map = {"CN": "cuv", "EN": "web", "JA": "jpn", "KO": "kor", "TH": "tha"}

    def fetch_data(self, ref, lang_key):
        """正確抓取並處理多節經文"""
        trans = self.lang_map.get(lang_key, "web")
        try:
            clean_ref = ref.replace(" ", "+")
            url = f"{self.api_base}{clean_ref}?translation={trans}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                # 關鍵：如果 API 回傳多節，建立 {節號: 內容} 的對照表
                if 'verses' in data:
                    return {v['verse']: v['text'].strip() for v in data['verses']}
                # 單節處理
                v_num = data.get('verse', 0)
                return {v_num: data.get('text', '').strip()}
        except: pass
        return {}

    def extract_keywords(self, text):
        if not text: return ""
        words = re.findall(r'\b[A-Za-z]{6,}\b', text)
        return ", ".join(list(dict.fromkeys(words))[:2])

    def process_data(self, ref_input, manual_grammar_map=None):
        """全自動抓取並整合所有語言"""
        with st.spinner("⏳ 正在跨國抓取中、英、日、韓、泰經文..."):
            en_map = self.fetch_data(ref_input, "EN")
            cn_map = self.fetch_data(ref_input, "CN")
            ja_map = self.fetch_data(ref_input, "JA")
            ko_map = self.fetch_data(ref_input, "KO")
            th_map = self.fetch_data(ref_input, "TH")

        # 取得書卷名稱 (例如 Psalm 20)
        book_part = re.sub(r':\d+.*$', '', ref_input)
        
        rows = []
        # 遍歷每一節經文
        for v_num in sorted(en_map.keys()):
            ref_str = f"{book_part}:{v_num}"
            eng = en_map.get(v_num, "")
            
            # 整合文法：優先用手動貼上的，沒有則生成預設
            grammar = "AI 待分析..."
            if manual_grammar_map and v_num in manual_grammar_map:
                grammar = manual_grammar_map[v_num]
            
            rows.append({
                "Reference": ref_str,
                "English": eng,
                "Chinese": cn_map.get(v_num, "[未獲取]"),
                "Key word": self.extract_keywords(eng),
                "Grammar": grammar,
                "Japanese": ja_map.get(v_num, "[未獲取]"),
                "Korean": ko_map.get(v_num, "[未獲取]"),
                "Thai": th_map.get(v_num, "[未獲取]")
            })
        return pd.DataFrame(rows)

    def parse_manual_input(self, text):
        """解析手動貼上的筆記，提取 [節號] 與 [文法內容]"""
        # 尋找像是 1:1 或 19:4 這樣的標記
        parts = re.split(r'(\d+:\d+)', text)
        grammar_map = {}
        
        # 遍歷分割後的內容，配對節號與後方的文法說明
        for i in range(1, len(parts), 2):
            ref_tag = parts[i] # 像是 "19:4"
            content = parts[i+1] if (i+1) < len(parts) else ""
            try:
                v_num = int(ref_tag.split(':')[-1])
                grammar_map[v_num] = content.strip()
            except: continue
        return grammar_map

# --- 4. 資源與樣式 ---
@st.cache_data
def get_img_64(file):
    if os.path.exists(file):
        with open(file, "rb") as f:
            return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
    return ""

st.markdown(f"""
    <style>
    .stApp {{ background-color: #FFF9E3; }}
    .feature-box {{
        background: white; border-radius: 15px; padding: 20px;
        border: 2px solid #FFCDD2; box-shadow: 4px 4px 0px #FFCDD2;
        margin-bottom: 15px;
    }}
    .snoopy-container img {{
        width: 100%; border-radius: 15px; margin-bottom: 12px; border: 2.5px solid #FFCDD2;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. UI 佈局 ---
tab1, tab2, tab3 = st.tabs(["🏠 我的書桌", "🎯 翻譯挑戰", "🧪 自動工具"])

with tab1:
    col_main, col_snoopy = st.columns([2.5, 1])
    with col_main:
        st.markdown('<div class="feature-box"><h3>💡 今日金句</h3>傳道書 3:1<br>凡事都有定期，天下萬務都有定時。</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.markdown('<div class="feature-box">🔤 單字<br><b>Study</b><br>學習</div>', unsafe_allow_html=True)
        c2.markdown('<div class="feature-box">🔗 片語<br><b>Keep it up</b><br>繼續加油</div>', unsafe_allow_html=True)
        st.markdown('<div class="feature-box" style="background:#E3F2FD;">📝 文法重點<br>保持學習，每天進步！</div>', unsafe_allow_html=True)
    
    with col_snoopy:
        # 圖 1
        img1 = get_img_64("f364bd220887627.67cae1bd07457.jpg")
        if img1: st.markdown(f'<div class="snoopy-container"><img src="{img1}"></div>', unsafe_allow_html=True)
        # 圖 2
        img2 = get_img_64("183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg")
        if img2: st.markdown(f'<div class="snoopy-container"><img src="{img2}"></div>', unsafe_allow_html=True)

with tab3:
    st.subheader("🧪 聖經多語言自動分類器")
    mode = st.radio("功能選擇", ["全自動章節抓取 (支援範圍)", "手動貼上解析內容"], horizontal=True)
    
    if mode == "全自動章節抓取 (支援範圍)":
        ref_in = st.text_input("輸入章節 (例如: Psalm 20:1-9)", "Psalm 20:1-3")
        if st.button("🔍 開始全自動生成 Sheet"):
            st.session_state.final_df = auto_tool.process_range(ref_in)
            st.success(f"✅ 成功! 已拆分為 {len(st.session_state.final_df)} 筆數據")
    
    else:
        raw_input = st.text_area("在此貼上含文法的筆記文字...", height=200)
        if st.button("🚀 開始手動解析"):
            st.warning("手動解析正調用 API 補全中...")
            # 解析邏輯 (略，與自動抓取共享 API 邏輯)

    # 顯示結果，並應用 2026 width="stretch" 語法
    st.dataframe(st.session_state.final_df, width="stretch")
    
    if not st.session_state.final_df.empty:
        csv = st.session_state.final_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 匯出為 Verse/Words/Phrases 表格 (CSV)", csv, "Bible_Study_2026.csv")
