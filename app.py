import streamlit as st
import pandas as pd
import requests
import io
import re
import os
import base64

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
    if 'score' not in st.session_state: st.session_state.score = 0

init_session()

THEME = {"bg": "#FFF9E3", "box": "#FFFFFF", "accent": "#FFCDD2", "text": "#4A4A4A", "sub": "#F06292", "keyword": "#E91E63"}

# --- 3. 核心工具類別 ---
class BibleAutomator:
    def __init__(self):
        # 修正：API 必須包含協議
        self.api_base = "bible-api.com"
        self.analysis_keywords = ['Subject', 'Verb', '補全後', '例句', '譯為', '指代', '語氣', '省略', '主謂']
        self.lang_map = {"CN": "cuv", "EN": "web", "JA": "jpn", "KO": "kor", "TH": "tha"}

    def fetch_real_bible(self, ref, lang_key):
        """透過 API 獲取經文資料"""
        trans = self.lang_map.get(lang_key, "web")
        try:
            # 清理經文參考格式（空格轉為 +）
            ref_encoded = ref.replace(" ", "+")
            r = requests.get(f"{self.api_base}{ref_encoded}?translation={trans}", timeout=7)
            if r.status_code == 200:
                return r.json().get('text', '').strip()
        except:
            pass
        return f"[無法獲取 {lang_key} 版本]"

    def parse_manual(self, raw_text):
        """解析手動筆記（已修正 Python re 不支援 \p{P} 的問題）"""
        book_match = re.search(r'([\u4e00-\u9fa5]+)(\d+)(篇|章)?', raw_text)
        book_name = book_match.group(1) if book_match else ""
        
        # 以換行且後方接座標 (如 19:1) 作為分割點
        blocks = re.split(r'\n(?=\d{1,3}:\d{1,3})', raw_text)
        
        final_list = []
        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if not lines: continue
            
            # 第一行通常是座標
            ref_match = re.match(r'^(\d+:\d+)', lines[0])
            if not ref_match: continue
            
            ref_val = f"{book_name}{ref_match.group(1)}"
            entry = {
                "Reference": ref_val, "Chinese": "", "English": "", 
                "Key word": "", "Grammar": ""
            }
            
            grammar_lines = []
            for line in lines:
                # 排除座標行
                if re.match(r'^\d+:\d+$', line): continue
                
                # 判定文法行
                if any(k in line for k in self.analysis_keywords):
                    grammar_lines.append(line)
                # 判定中文行
                elif re.search(r'[\u4e00-\u9fa5]', line) and not entry["Chinese"]:
                    entry["Chinese"] = line
                # 判定英文行 (修正後的 Regex，不使用 \p)
                elif re.match(r'^[A-Za-z0-9\s.,;!\?\'\"()\-\:]+$', line) and not entry["English"]:
                    entry["English"] = re.sub(r'^\d+:\d+\s*', '', line)
            
            entry["Grammar"] = "\n".join(grammar_lines)
            # 提取長單字作為關鍵字
            words = [w.strip('.,!?;') for w in entry["English"].split() if len(w) > 5]
            entry["Key word"] = ", ".join(list(dict.fromkeys(words))[:3])
            final_list.append(entry)
            
        return pd.DataFrame(final_list)

# --- 4. 效能優化元件 ---
@st.cache_data(ttl=600)
def get_img_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
    return None

# --- 5. CSS 樣式 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {THEME['bg']}; }}
    .feature-box {{
        background: {THEME['box']}; border-radius: 15px; padding: 20px;
        border: 2px solid {THEME['accent']}; box-shadow: 4px 4px 0px {THEME['accent']};
        margin-bottom: 15px;
    }}
    .img-container img {{ border-radius: 12px; width: 100%; object-fit: cover; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. UI 佈局 ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 隨記挑戰", "🧪 自動化工具"])

with tab_home:
    v1, w1, p1 = st.session_state.verse_data, st.session_state.word_data, st.session_state.phrase_data
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.markdown(f'<div class="feature-box"><h3>💡 今日金句</h3><p style="font-size:20px;">{v1["Chinese"]}</p><div style="text-align:right;">— {v1["Reference"]}</div></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="feature-box"><small>🔤 單字</small><br><b>{w1["Vocab"]}</b><br>{w1["Definition"]}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="feature-box"><small>🔗 片語</small><br><b>{p1["Phrase"]}</b><br>{p1["Definition"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="feature-box" style="background:#E3F2FD;"><small>📝 文法筆記</small><br>{w1["Grammar"]}</div>', unsafe_allow_html=True)

    with col_side:
        img_data = get_img_base64("f364bd220887627.67cae1bd07457.jpg")
        if img_data: st.markdown(f'<div class="img-container"><img src="{img_data}"></div>', unsafe_allow_html=True)

with tab_play:
    st.subheader("🎯 翻譯挑戰")
    curr = st.session_state.quiz_data
    st.info(f"請翻譯：{curr['Text_CN']}")
    user_input = st.text_input("輸入英文...")
    if st.button("提交答案"):
        if user_input.lower().strip() == curr['Text_EN'].lower().strip():
            st.success("太棒了！完全正確")
            st.balloons()
        else:
            st.warning(f"再試一次？參考答案：{curr['Text_EN']}")

with tab_tool:
    st.markdown("### 🧪 聖經資料解析工具 (2026)")
    mode = st.radio("模式選擇", ["手動解析筆記", "API 聯網抓取"], horizontal=True)
    auto = BibleAutomator()
    
    if mode == "手動解析筆記":
        raw_text = st.text_area("貼上含座標的經文解析：", height=200, placeholder="詩篇19篇\n19:1 The heavens...\nSubject: The heavens")
        if st.button("🚀 開始解析"):
            if raw_text:
                df = auto.parse_manual(raw_text)
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 匯出 Excel (CSV)", df.to_csv(index=False).encode('utf-8-sig'), "bible_notes.csv")
    
    else:
        ref_input = st.text_input("輸入經文座標 (例如: Psalms 19:1)")
        if st.button("🔍 聯網抓取"):
            with st.spinner("連線中..."):
                res = {
                    "中文": auto.fetch_real_bible(ref_input, "CN"),
                    "英文": auto.fetch_real_bible(ref_input, "EN"),
                    "日文": auto.fetch_real_bible(ref_input, "JA")
                }
                st.json(res)
