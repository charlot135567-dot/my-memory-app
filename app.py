import streamlit as st
import pandas as pd
import requests
import re
import os
import base64

# --- 1. 頁面配置 (2026 最新標準) ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide", page_icon="🐶")

# --- 2. 初始化 Session State ---
if 'final_df' not in st.session_state:
    st.session_state.final_df = pd.DataFrame(columns=["Reference", "English", "Chinese", "Key word", "Grammar", "Japanese", "Korean", "Thai"])

# --- 3. 核心工具類別 ---
class BibleAutomator:
    def __init__(self):
        self.api_base = "bible-api.com"
        # 推薦版本：中(CUV)、英(WEB)、日(JPN)、韓(KOR)、泰(THA)
        self.lang_map = {"CN": "cuv", "EN": "web", "JA": "jpn", "KO": "kor", "TH": "tha"}

    def fetch_data(self, ref, lang_key):
        """正確處理多節經文的 API 抓取"""
        trans = self.lang_map.get(lang_key, "web")
        try:
            # 必須處理網址空格
            clean_ref = ref.replace(" ", "+")
            url = f"{self.api_base}{clean_ref}?translation={trans}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if 'verses' in data:
                    return {v['verse']: v['text'].strip() for v in data['verses']}
                return {data.get('verse', 0): data.get('text', '').strip()}
        except: pass
        return {}

    def extract_keywords(self, text):
        if not text: return ""
        words = re.findall(r'\b[A-Za-z]{6,}\b', text)
        return ", ".join(list(dict.fromkeys(words))[:2])

    def process_range(self, ref_input, manual_grammar_map=None):
        """核心邏輯：整合所有語言並拆分章節"""
        with st.spinner("⏳ 正在全球同步中、英、日、韓、泰經文..."):
            en_map = self.fetch_data(ref_input, "EN")
            cn_map = self.fetch_data(ref_input, "CN")
            ja_map = self.fetch_data(ref_input, "JA")
            ko_map = self.fetch_data(ref_input, "KO")
            th_map = self.fetch_data(ref_input, "TH")

        # 取得書卷名 (例如 Psalm 20)
        book_part = re.sub(r':\d+.*$', '', ref_input)
        rows = []
        # 以英文版節號為基準進行拆分
        for v_num in sorted(en_map.keys()):
            ref_str = f"{book_part}:{v_num}"
            eng = en_map.get(v_num, "")
            
            # 文法優先使用手動貼上的，否則放預設
            grammar = "AI 待分析"
            if manual_grammar_map and v_num in manual_grammar_map:
                grammar = manual_grammar_map[v_num]
            
            rows.append({
                "Reference": ref_str,
                "English": eng,
                "Chinese": cn_map.get(v_num, ""),
                "Key word": self.extract_keywords(eng),
                "Grammar": grammar,
                "Japanese": ja_map.get(v_num, "[未獲取]"),
                "Korean": ko_map.get(v_num, "[未獲取]"),
                "Thai": th_map.get(v_num, "[未獲取]")
            })
        return pd.DataFrame(rows)

    def parse_manual_input(self, text):
        """解析手動筆記中的節號 (如 19:4)"""
        parts = re.split(r'(\d+:\d+)', text)
        grammar_map = {}
        for i in range(1, len(parts), 2):
            ref_tag = parts[i]
            content = parts[i+1] if (i+1) < len(parts) else ""
            try:
                v_num = int(ref_tag.split(':')[-1])
                grammar_map[v_num] = content.strip()
            except: continue
        return grammar_map

# --- 4. 實例化工具 (解決 NameError) ---
auto_tool = BibleAutomator()

# --- 5. 樣式與資源 ---
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
    /* 高度對齊：左側文法框設為與右側兩圖等高 */
    .grammar-box {{ min-height: 310px; background-color: #F0F7FF !important; }}
    .snoopy-container img {{
        width: 100%; border-radius: 15px; margin-bottom: 12px; border: 2.5px solid #FFCDD2;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. UI 主介面 ---
tab1, tab2, tab3 = st.tabs(["🏠 我的書桌", "🎯 翻譯挑戰", "🧪 自動工具"])

with tab1:
    col_l, col_r = st.columns([2.5, 1])
    with col_l:
        st.markdown('<div class="feature-box"><h3>💡 今日金句</h3>傳道書 3:1<br>凡事都有定期，天下萬務都有定時。</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.markdown('<div class="feature-box">🔤 單字<br><b>Study</b><br>學習</div>', unsafe_allow_html=True)
        c2.markdown('<div class="feature-box">🔗 片語<br><b>Keep it up</b><br>繼續加油</div>', unsafe_allow_html=True)
        st.markdown('<div class="feature-box grammar-box">📝 文法重點說明<br>此框已透過 CSS min-height 確保與右側圖片高度對齊。</div>', unsafe_allow_html=True)
    with col_r:
        img1 = get_img_64("f364bd220887627.67cae1bd07457.jpg")
        if img1: st.markdown(f'<div class="snoopy-container"><img src="{img1}"></div>', unsafe_allow_html=True)
        img2 = get_img_64("183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg")
        if img2: st.markdown(f'<div class="snoopy-container"><img src="{img2}"></div>', unsafe_allow_html=True)

with tab2:
    st.subheader("🎯 翻譯挑戰")
    st.info("請翻譯：凡事都有定期，天下萬務都有定時。")
    st.text_area("輸入翻譯內容...", key="challenge_input")
    if st.button("查看參考答案"): 
        st.balloons()
        st.success("To everything there is a season, and a time to every purpose under the heaven.")

with tab3:
    st.subheader("🧪 聖經多語言自動分類器")
    mode = st.radio("模式", ["全自動章節抓取 (支援範圍)", "手動貼上解析內容"], horizontal=True)
    
    if mode == "全自動章節抓取 (支援範圍)":
        ref_in = st.text_input("輸入範圍 (例: Psalm 20:1-5)", "Psalm 20:1-3")
        if st.button("🔍 開始生成表格"):
            st.session_state.final_df = auto_tool.process_range(ref_in)
            st.success("✅ 抓取完成！")
    
    else:
        ref_scope = st.text_input("輸入經卷座標範圍 (例: Psalm 19:1-2)")
        manual_text = st.text_area("貼上文法筆記 (需含節號, 如 19:1 主詞...)")
        if st.button("🚀 執行手動解析"):
            g_map = auto_tool.parse_manual_input(manual_text)
            st.session_state.final_df = auto_tool.process_range(ref_scope, manual_grammar_map=g_map)
            st.success("✅ 手動筆記已合併！")

    st.dataframe(st.session_state.final_df, width="stretch")
    if not st.session_state.final_df.empty:
        csv = st.session_state.final_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 匯出 CSV 表格", csv, "Bible_Study_2026.csv")
