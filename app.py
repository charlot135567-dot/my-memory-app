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
        """抓取單節或多節經文"""
        trans = self.lang_map.get(lang_key, "web")
        try:
            r = requests.get(f"{self.api_base}{ref}?translation={trans}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                # 如果是多節，API 會回傳一個 list 在 'verses'
                if 'verses' in data:
                    return {v['verse']: v['text'].strip() for v in data['verses']}
                return {data.get('verse', 0): data.get('text', '').strip()}
        except: pass
        return {}

    def parse_and_fetch_all(self, ref_input):
        """處理如 Psalm 20:1-9 並抓取所有語言"""
        # 抓取各國版本
        with st.spinner(f"正在同步多國語言資料..."):
            cn_map = self.fetch_data(ref_input, "CN")
            en_map = self.fetch_data(ref_input, "EN")
            ja_map = self.fetch_data(ref_input, "JA")
            ko_map = self.fetch_data(ref_input, "KO")
            th_map = self.fetch_data(ref_input, "TH")
        
        # 取得書卷名 (例如 Psalms 20)
        base_ref = re.sub(r':\d+.*$', '', ref_input)
        
        rows = []
        for v_num in en_map.keys():
            ref_str = f"{base_ref}:{v_num}"
            eng_text = en_map.get(v_num, "")
            rows.append({
                "Reference": ref_str,
                "English": eng_text,
                "Chinese": cn_map.get(v_num, "[未獲取]"),
                "Key word": ", ".join(re.findall(r'\b[A-Za-z]{6,}\b', eng_text)[:2]),
                "Grammar": f"Analysis for {ref_str}:\nSubject: ...\nVerb: ...",
                "Japanese": ja_map.get(v_num, "[未獲取]"),
                "Korean": ko_map.get(v_num, "[未獲取]"),
                "Thai": th_map.get(v_num, "[未獲取]")
            })
        return pd.DataFrame(rows)

auto_tool = BibleAutomator()

# --- 4. CSS 與 圖片處理 ---
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
    .snoopy-img {{ width: 100%; border-radius: 15px; margin-bottom: 10px; border: 2px solid #FFCDD2; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. UI 佈局 ---
t1, t2, t3 = st.tabs(["🏠 我的書桌", "🎯 挑戰", "🧪 自動工具"])

with t1:
    col_left, col_right = st.columns([2.5, 1])
    with col_left:
        st.markdown('<div class="feature-box"><h3>💡 今日金句</h3>傳道書 3:1<br>凡事都有定期，天下萬務都有定時。</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.markdown('<div class="feature-box">🔤 單字<br><b>Study</b><br>學習</div>', unsafe_allow_html=True)
        c2.markdown('<div class="feature-box">🔗 片語<br><b>Keep it up</b><br>繼續加油</div>', unsafe_allow_html=True)
    
    with col_right:
        # 史努比圖 1
        img1 = get_img_64("f364bd220887627.67cae1bd07457.jpg")
        if img1: st.markdown(f'<img src="{img1}" class="snoopy-img">', unsafe_allow_html=True)
        # 史努比圖 2
        img2 = get_img_64("183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg")
        if img2: st.markdown(f'<img src="{img2}" class="snoopy-img">', unsafe_allow_html=True)

with t3:
    st.subheader("🧪 聖經資料自動分類器")
    mode = st.radio("模式", ["手動解析筆記", "指定章節全自動抓取 (支援範圍)"], horizontal=True)
    
    if mode == "指定章節全自動抓取 (支援範圍)":
        ref_in = st.text_input("輸入章節 (例: Psalm 20:1-5)", "Psalm 20:1-3")
        if st.button("🔍 開始全自動分類"):
            st.session_state.final_df = auto_tool.parse_and_fetch_all(ref_in)
            st.success(f"已成功拆分並抓取 {len(st.session_state.final_df)} 節經文")
    
    else:
        # 手動解析邏輯
        raw_text = st.text_area("貼上筆記內容", height=200)
        if st.button("🚀 執行解析"):
            # 這裡簡化演示解析一節，實務上可串接 fetch_data
            st.warning("手動解析建議配合 API 自動補全功能使用")

    st.dataframe(st.session_state.final_df, use_container_width=True)
    
    if not st.session_state.final_df.empty:
        csv = st.session_state.final_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 匯出 Verse/Words/Phrases 表格", csv, "Bible_Export.csv")
