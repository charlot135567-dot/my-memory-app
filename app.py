import streamlit as st
import pandas as pd
import requests
import io
import re
import os
import time
import base64
from urllib.parse import quote

# --- 1. 頁面基礎配置 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide", page_icon="🐶")

# --- 2. 初始化 Session State ---
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = {"Text_CN": "凡事都有定期，天下萬務都有定時。", "Text_EN": "To everything there is a season."}
if 'verse_data' not in st.session_state:
    st.session_state.verse_data = {"Chinese": "凡事都有定期，天下萬務都有定時。", "Reference": "傳道書 3:1", "Keyword": "定時"}
if 'word_data' not in st.session_state:
    st.session_state.word_data = {"Vocab": "Study", "Definition": "學習", "Grammar": "保持學習，每天進步！"}
if 'phrase_data' not in st.session_state:
    st.session_state.phrase_data = {"Phrase": "Keep it up", "Definition": "繼續加油"}
if 'score' not in st.session_state: st.session_state.score = 0
if 'lives' not in st.session_state: st.session_state.lives = 3

THEME = {"bg": "#FFF9E3", "box": "#FFFFFF", "accent": "#FFCDD2", "text": "#4A4A4A", "sub": "#F06292", "keyword": "#E91E63"}

# --- 3. 核心工具類別 ---
class BibleAutomator:
    def __init__(self):
        self.api_base = "bible-api.com"
        self.analysis_keywords = ['Subject', 'Verb', '補全後', '例句', '譯為', '指代', '語氣', '省略', '主謂']
        # 2026 支援版本代碼
        self.lang_map = {"CN": "cuv", "EN": "web", "JA": "jpn", "KO": "kor", "TH": "tha"}

    def fetch_real_bible(self, ref, lang_key):
        """真實透過 API 抓取各國版本經文"""
        trans = self.lang_map.get(lang_key, "web")
        try:
            r = requests.get(f"{self.api_base}{ref}?translation={trans}", timeout=10)
            if r.status_code == 200:
                return r.json().get('text', '').strip()
        except: pass
        return f"[無法獲取 {lang_key} 版本]"

    def parse_manual(self, raw_text):
        """解析手動貼上的複雜解析文字"""
        book_match = re.search(r'([\u4e00-\u9fa5]+)(\d+)篇', raw_text)
        book_name = book_match.group(1) if book_match else ""
        blocks = re.split(r'\n(?=\d{1,3}:\d{1,3})', raw_text)
        
        final_list = []
        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if not lines: continue
            ref_match = re.match(r'^(\d+:\d+)', lines[0])
            if not ref_match: continue
            
            ref_val = f"{book_name}{ref_match.group(1)}"
            entry = {
                "Reference": ref_val, "English": "", "Chinese": "", "Key word": "",
                "Grammar": "", "Japanese": self.fetch_real_bible(ref_val, "JA"),
                "Korean": self.fetch_real_bible(ref_val, "KO"), "Thai": self.fetch_real_bible(ref_val, "TH")
            }
            grammar_lines = []
            for line in lines:
                if any(k in line for k in self.analysis_keywords): grammar_lines.append(line)
                elif re.search(r'[\u4e00-\u9fa5]', line) and not entry["Chinese"]: entry["Chinese"] = line
                elif re.match(r'^[A-Za-z\d\s\p{P}]+$', line) and not entry["English"]:
                    entry["English"] = re.sub(r'^\d+\s', '', line)
            
            entry["Grammar"] = "\n".join(grammar_lines)
            # 關鍵字：選取長度 > 5 的單字模擬中高級程度
            words = list(set([w.strip(',.') for w in entry["English"].split() if len(w) > 5]))
            entry["Key word"] = ", ".join(words[:3])
            final_list.append(entry)
        return pd.DataFrame(final_list)

@st.cache_data(ttl=300)
def fetch_data(gid):
    SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200: return pd.read_csv(io.StringIO(r.text)).fillna("")
    except: pass
    return pd.DataFrame()

def get_img_as_base64(file):
    if os.path.exists(file):
        with open(file, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f"data:image/jpeg;base64,{data}"
    return None

# --- 4. CSS 樣式 ---
st.markdown(f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{ background-color: {THEME['bg']}; font-family: 'Comic Neue', cursive; }}
    .feature-box {{
        background-color: {THEME['box']} !important; border-radius: 18px !important; padding: 18px !important;
        border: 2.5px solid {THEME['accent']} !important; box-shadow: 4px 4px 0px {THEME['accent']} !important;
        margin-bottom: 12px !important; display: flex; flex-direction: column; justify-content: center;
    }}
    .kw {{ color: {THEME['keyword']}; font-weight: bolder; background-color: #FFFF00; padding: 2px 4px; border-radius: 4px; }}
    .img-box img {{ border-radius: 15px; max-width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. 定義標籤頁 (解決 NameError) ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 隨記挑戰", "🧪 自動分類工具"])

# --- TAB 1: 我的書桌 (史努比圖 1 & 2) ---
with tab_home:
    v1, w1, p1 = st.session_state.verse_data, st.session_state.word_data, st.session_state.phrase_data
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="feature-box"><small>🔤 單字</small><br><b style="font-size:24px;">{w1.get("Vocab","")}</b><br>{w1.get("Definition","")}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="feature-box"><small>🔗 片語</small><br><b style="font-size:22px;">{p1.get("Phrase","")}</b><br>{p1.get("Definition","")}</div>', unsafe_allow_html=True)
    with c3:
        b64 = get_img_as_base64("f364bd220887627.67cae1bd07457.jpg")
        if b64: st.markdown(f'<div class="img-box" style="height:150px; text-align:center;"><img src="{b64}" style="height:100%;"></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="feature-box"><h3>💡 今日金句</h3><div style="font-size:22px;">{v1.get("Chinese","")}</div><div style="text-align:right;">— {v1.get("Reference","")}</div></div>', unsafe_allow_html=True)
    
    c4, c5 = st.columns([2, 1])
    with c4:
        st.markdown(f'<div class="feature-box" style="background-color:#E3F2FD !important; min-height:180px;"><small>📝 文法</small><br>{w1.get("Grammar","")}</div>', unsafe_allow_html=True)
    with c5:
        b64_2 = get_img_as_base64("183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg")
        if b64_2: st.markdown(f'<div class="img-box" style="height:180px; text-align:center;"><img src="{b64_2}" style="height:100%;"></div>', unsafe_allow_html=True)

# --- TAB 2: 隨記挑戰 (史努比圖 3) ---
with tab_play:
    col_txt, col_img = st.columns([2, 1])
    with col_txt:
        st.subheader("🎯 翻譯挑戰")
        curr = st.session_state.quiz_data
        st.info(f"請翻譯：{curr.get('Text_CN','')}")
        ans = st.text_area("在此輸入英文...", height=100)
        if st.button("提交答案"):
            st.balloons()
            st.success(f"參考答案: {curr.get('Text_EN','')}")
            st.session_state.score += 20
    with col_img:
        t_img = "68254faebaafed9dafb41918f74c202e.jpg"
        if os.path.exists(t_img): st.image(t_img, caption="Cheers!")

# --- TAB 3: 自動分類工具 (AI & 手動解析) ---
with tab_tool:
    st.markdown("### 🧪 萬用聖經資料 AI 解析器 (2026 版)")
    mode = st.radio("模式選擇", ["手動貼上大量筆記", "AI 指定章節抓取"], horizontal=True)
    auto = BibleAutomator()
    
    if mode == "手動貼上大量筆記":
        raw_input = st.text_area("貼上含解析的文字：", height=250, placeholder="詩篇19篇\n19:1... (Subject:...)")
        if st.button("🚀 執行解析匯出"):
            if raw_input:
                res_df = auto.parse_manual(raw_input)
                st.data_editor(res_df, use_container_width=True)
                csv = res_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載 Excel (CSV)", csv, "bible_parsed.csv", "text/csv")
    else:
        cmd = st.text_input("輸入英文書卷章節 (例: Psalms 19:1-5)：")
        if st.button("🔍 AI 自動檢索"):
            if cmd:
                with st.spinner("抓取多國官方經文中..."):
                    results = {
                        "Reference": cmd,
                        "Chinese": auto.fetch_real_bible(cmd, "CN"),
                        "English": auto.fetch_real_bible(cmd, "EN"),
                        "Japanese": auto.fetch_real_bible(cmd, "JA"),
                        "Korean": auto.fetch_real_bible(cmd, "KO"),
                        "Thai": auto.fetch_real_bible(cmd, "TH"),
                        "Key word": "檢索中...", "Grammar": "待分析"
                    }
                    st.data_editor(pd.DataFrame([results]), use_container_width=True)
            else: st.warning("請輸入章節")

# --- 側邊欄 ---
with st.sidebar:
    st.title("🐾 控制台")
    st.metric("得分", st.session_state.score)
    st.metric("生命", "❤️" * st.session_state.lives)
    if st.button("♻️ 刷新內容"):
        df_w = fetch_data("1400979824")
        if not df_w.empty: st.session_state.word_data = df_w.sample(1).iloc[0].to_dict()
        st.rerun()
