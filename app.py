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
        # 修正：必須包含 https:// 且包含末端 /
        self.api_base = "https://bible-api.com/"
        # 推薦版本：中(CUV)、英(WEB)、日(JPN)、韓(KOR)、泰(THA)
        self.lang_map = {"CN": "cuv", "EN": "web", "JA": "jpn", "KO": "kor", "TH": "tha"}

    def fetch_data(self, ref, lang_key):
        """正確處理 API 抓取與 URL 編碼"""
        trans = self.lang_map.get(lang_key, "web")
        try:
            # 必須處理網址空格以防止 No connection adapters 錯誤
            clean_ref = ref.replace(" ", "+")
            url = f"{self.api_base}{clean_ref}?translation={trans}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                # --- 關鍵修正處：處理多節 (verses) 列表 ---
                if 'verses' in data:
                    # 這會把 1-9 節拆開，存成 {1: "經文", 2: "經文"...}
                    return {v['verse']: v['text'].strip() for v in data['verses']}
                # 若只有單節
                return {data.get('verse', 0): data.get('text', '').strip()}
        except: pass
        return {}

    def extract_keywords(self, text):
        if not text: return ""
        # 選取中高級單字 (6個字母以上)
        words = re.findall(r'\b[A-Za-z]{6,}\b', text)
        stop = {'through', 'between', 'against', 'everything'}
        filtered = [w for w in words if w.lower() not in stop]
        return ", ".join(list(dict.fromkeys(filtered))[:2])

    def process_range(self, ref_input, manual_grammar_map=None):
        # 1. 同步抓取所有語言的「對照表」
        en_map = self.fetch_data(ref_input, "EN")
        cn_map = self.fetch_data(ref_input, "CN")
        ja_map = self.fetch_data(ref_input, "JA")
        ko_map = self.fetch_data(ref_input, "KO")
        th_map = self.fetch_data(ref_input, "TH")

        book_part = re.sub(r':\d+.*$', '', ref_input) # 取得書卷名如 Psalm 20
        rows = []

        # --- 關鍵修正處：使用 for 循環讓每一節都變成獨立的一行 ---
        for v_num in sorted(en_map.keys()):
            rows.append({
                "Reference": f"{book_part}:{v_num}",
                "English": en_map.get(v_num, ""),
                "Chinese": cn_map.get(v_num, ""),
                "Key word": self.extract_keywords(en_map.get(v_num, "")),
                "Grammar": manual_grammar_map.get(v_num, "AI 待分析") if manual_grammar_map else "AI 待分析",
                "Japanese": ja_map.get(v_num, "[未獲取]"),
                "Korean": ko_map.get(v_num, "[未獲取]"),
                "Thai": th_map.get(v_num, "[未獲取]")
            })
        
        # 最終回傳一個多行的 DataFrame，匯出時就不會擠在一起
        return pd.DataFrame(rows)

    def parse_manual_input(self, text):
        """解析手動筆記中的節號 (如 19:4) 對應文法"""
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

# --- 4. 實例化工具 (確保 NameError 消失) ---
auto_tool = BibleAutomator()

# --- 5. 資源處理與對齊樣式 ---
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
    /* --- 修正處：純粹的 CSS 定義 --- */
    .grammar-box {{ 
        min-height: 315px; 
        background-color: #F0F7FF !important; 
    }}
    /* -------------------------- */
    .snoopy-container img {{
        width: 100%; border-radius: 15px; margin-bottom: 12px; border: 2.5px solid #FFCDD2;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. UI 佈局 ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 翻譯挑戰", "🧪 自動工具"])

# --- TAB 1: 我的書桌 ---
with tab_home:
    # 1. 注入 CSS 樣式 (確保高度對齊生效)
    st.markdown("""
        <style>
        .grammar-box { 
            min-height: 310px; 
            background-color: #F0F7FF !important; 
        }
        .snoopy-container img { 
            width: 100%; 
            border-radius: 15px; 
            margin-bottom: 12px; 
            border: 2px solid #FFCDD2; 
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. 開始佈局 (左側 2.5, 右側 1)
    col_l, col_r = st.columns([2.5, 1])
    
    with col_l:
        # A. 今日金句
        st.markdown('<div class="feature-box"><h3>💡 今日金句</h3>傳道書 3:1<br>凡事都有定期，天下萬務都有定時。</div>', unsafe_allow_html=True)
        
        # B. 單字與片語並排 (使用內層 columns)
        c1, c2 = st.columns(2)
        c1.markdown('<div class="feature-box">🔤 單字<br><b>Study</b><br>學習</div>', unsafe_allow_html=True)
        c2.markdown('<div class="feature-box">🔗 片語<br><b>Keep it up</b><br>繼續加油</div>', unsafe_allow_html=True)
        
        # C. 文法框 (套用 grammar-box 以對齊右側圖片高度)
        st.markdown('<div class="feature-box grammar-box">📝 文法重點說明<br>此框高度已透過 CSS 自動對齊右側兩張史努比圖片。</div>', unsafe_allow_html=True)

    with col_r:
        # D. 右側史努比圖片 (垂直排列於容器內)
        img1 = get_img_64("f364bd220887627.67cae1bd07457.jpg")
        if img1: 
            st.markdown(f'<div class="snoopy-container"><img src="{img1}"></div>', unsafe_allow_html=True)
        
        img2 = get_img_64("183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg")
        if img2: 
            st.markdown(f'<div class="snoopy-container"><img src="{img2}"></div>', unsafe_allow_html=True)

# --- TAB 2: 翻譯挑戰 ---
with tab_play:
    st.subheader("🎯 翻譯挑戰")
    st.info("請翻譯：凡事都有定期，天下萬務都有定時。")
    st.text_area("在此輸入翻譯內容...", key="input_play")
    if st.button("查看參考答案"): 
        st.balloons()
        st.success("To everything there is a season, and a time to every purpose under the heaven.")

# --- TAB 3: 自動工具 ---
with tab_tool:
    st.subheader("🧪 聖經多語言自動分類器")
    mode = st.radio("模式", ["全自動章節抓取 (支援範圍)", "手動貼上解析內容"], horizontal=True)
    
    if mode == "全自動章節抓取 (支援範圍)":
        ref_in = st.text_input("輸入範圍 (例: Psalm 20:1-9)", "Psalm 20:1-3")
        if st.button("🔍 開始生成表格"):
            st.session_state.final_df = auto_tool.process_range(ref_in)
            st.success("✅ 成功同步多國經文！")
    
    else:
        ref_scope = st.text_input("輸入對應章節範圍 (例: Psalm 19:1-2)")
        manual_text = st.text_area("貼上文法筆記 (需含節號, 如 19:1 主詞...)")
        if st.button("🚀 執行手動解析整合"):
            g_map = auto_tool.parse_manual_input(manual_text)
            st.session_state.final_df = auto_tool.process_range(ref_scope, manual_grammar_map=g_map)
            st.success("✅ 手動筆記已合併！")

    # 使用 2026 推薦語法 width="stretch"
    st.dataframe(st.session_state.final_df, width="stretch")
    
    if not st.session_state.final_df.empty:
        csv_data = st.session_state.final_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 匯出 CSV 表格", csv_data, "Bible_Study_2026.csv")
