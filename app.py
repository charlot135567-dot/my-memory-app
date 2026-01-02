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
        self.api_base = "https://bible-api.com/"
        # 2026 推薦版本：中(CUV)、英(WEB)、日(JPN)、韓(KOR)、泰(THA)
        self.lang_map = {"CN": "cuv", "EN": "web", "JA": "jpn", "KO": "kor", "TH": "tha"}

    def fetch_data(self, ref, lang_key):
        """抓取單節或多節經文資料庫"""
        trans = self.lang_map.get(lang_key, "web")
        try:
            # 確保使用半形引號與半形空格
            clean_ref = ref.replace(" ", "+")
            r = requests.get(f"{self.api_base}{clean_ref}?translation={trans}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                if 'verses' in data:
                    return {v['verse']: v['text'].strip() for v in data['verses']}
                return {data.get('verse', 0): data.get('text', '').strip()}
        except Exception as e:
            st.error(f"連線 {lang_key} 失敗: {e}")
        return {}

    def extract_keywords(self, text):
        """選取中高級單字 (6個字母以上)"""
        words = re.findall(r'\b[A-Za-z]{6,}\b', text)
        stop_words = {'through', 'between', 'against', 'everything'}
        filtered = [w for w in words if w.lower() not in stop_words]
        return ", ".join(list(dict.fromkeys(filtered))[:2])

    def process_range(self, ref_input):
        """核心功能：拆分 Psalm 20:1-9 為多行並補全語言"""
        with st.spinner("⏳ 正在跨國同步經文資料..."):
            cn_map = self.fetch_data(ref_input, "CN")
            en_map = self.fetch_data(ref_input, "EN")
            ja_map = self.fetch_data(ref_input, "JA")
            ko_map = self.fetch_data(ref_input, "KO")
            th_map = self.fetch_data(ref_input, "TH")

        base_ref = re.sub(r':\d+.*$', '', ref_input) # 取得 "Psalm 20"
        
        rows = []
        # 以英文版為基準進行拆分
        for v_num, eng_text in en_map.items():
            current_ref = f"{base_ref}:{v_num}"
            rows.append({
                "Reference": current_ref,
                "English": eng_text,
                "Chinese": cn_map.get(v_num, ""),
                "Key word": self.extract_keywords(eng_text),
                "Grammar": f"Analysis for {current_ref}:\n- Subject/Verb Analysis needed.",
                "Japanese": ja_map.get(v_num, "[未獲取]"),
                "Korean": ko_map.get(v_num, "[未獲取]"),
                "Thai": th_map.get(v_num, "[未獲取]")
            })
        return pd.DataFrame(rows)

auto_tool = BibleAutomator()

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
