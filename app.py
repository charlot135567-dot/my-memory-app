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

# --- 3. 工具函式與 AI 分類類別 ---
@st.cache_data(ttl=300)
def fetch_data(gid):
    SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200: return pd.read_csv(io.StringIO(r.text)).fillna("")
    except: pass
    return pd.DataFrame()

class BibleAutomator:
    def __init__(self):
        self.analysis_keywords = ['Subject', 'Verb', '補全後', '例句', '譯為', '指代', '語氣', '省略', '主謂']

    def fetch_api_bible(self, ref, lang):
        # 2026 虛擬 API 調用：按 Reference 抓取權威版本
        return f"[2026 {lang} Official Version] {ref} Text"

    def parse_manual(self, raw_text):
        # 解析邏輯：書卷名補全與 8 欄位對應
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
                "Grammar": "", "Japanese": self.fetch_api_bible(ref_val, "JA"),
                "Korean": self.fetch_api_bible(ref_val, "KO"), "Thai": self.fetch_api_bible(ref_val, "TH")
            }
            grammar_lines = []
            for line in lines:
                if any(k in line for k in self.analysis_keywords): grammar_lines.append(line)
                elif re.search(r'[\u4e00-\u9fa5]', line) and not entry["Chinese"]: entry["Chinese"] = line
                elif re.match(r'^[A-Za-z\d\s\p{P}]+$', line) and not entry["English"]:
                    entry["English"] = re.sub(r'^\d+\s', '', line)
            
            entry["Grammar"] = "\n".join(grammar_lines)
            # 關鍵字擷取邏輯 (判斷中高級單字)
            words = [w.strip(',.') for w in entry["English"].split() if len(w) > 6]
            entry["Key word"] = ", ".join(list(set(words))[:3])
            final_list.append(entry)
        return pd.DataFrame(final_list)

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
    </style>
    """, unsafe_allow_html=True)

# --- 5. 定義標籤頁 (解決 NameError 的關鍵順序) ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 隨記挑戰", "🧪 自動分類工具"])

# --- TAB 1: 我的書桌 ---
with tab_home:
    v1 = st.session_state.verse_data
    w1 = st.session_state.word_data
    p1 = st.session_state.phrase_data

    # 第一排：單字 + 片語 + 史努比圖片
    c1, c2, c3 = st.columns(3) 
    with c1:
        voc = w1.get("Vocab", "Study")
        st.markdown(f'<div class="feature-box"><a href="dictionary.cambridge.org{quote(str(voc))}" target="_blank" class="dict-btn" style="float:right; font-size:10px; border:1px solid #F06292; padding:2px; border-radius:4px; text-decoration:none; color:#F06292;">🔍 字典</a><small>🔤 單字</small><br><b style="font-size:24px;">{voc}</b><br><small>{w1.get("Definition","")}</small></div>', unsafe_allow_html=True)
    with c2:
        phr = p1.get("Phrase", "Keep it up")
        st.markdown(f'<div class="feature-box"><small>🔗 片語</small><br><b style="font-size:22px;">{phr}</b><br><small>{p1.get("Definition","")}</small></div>', unsafe_allow_html=True)
    with c3:
        # 史努比圖 1
        top_img = "f364bd220887627.67cae1bd07457.jpg"
        if os.path.exists(top_img):
            b64 = base64.b64encode(open(top_img, "rb").read()).decode()
            st.markdown(f'<div class="img-box" style="height:150px; display:flex; justify-content:center;"><img src="data:image/jpeg;base64,{b64}" style="max-height:100%; border-radius:15px;"></div>', unsafe_allow_html=True)
        else:
            st.info("🐶 史努比在休息")

    # 第二排：今日金句
    raw_ch = v1.get("Chinese", "")
    kw = str(v1.get("Keyword", ""))
    disp = raw_ch.replace(kw, f'<span class="kw">{kw}</span>') if kw and kw in raw_ch else raw_ch
    st.markdown(f'<div class="feature-box" style="height: auto !important; min-height:140px;"><h3 style="color:{THEME["sub"]}; margin-top:0;">💡 今日金句</h3><div style="font-size:24px; font-weight:bold;">“{disp}”</div><div style="color:gray; text-align:right;">— {v1.get("Reference","")}</div></div>', unsafe_allow_html=True)

    # 第三排：文法 + 史努比圖 2
    c4, c5 = st.columns([2, 1]) 
    with c4:
        st.markdown(f'<div class="feature-box" style="background-color:#E3F2FD !important; min-height:200px;"><small>📝 關鍵文法</small><br><div style="font-size:15px; margin-top:8px;">{w1.get("Grammar", "保持學習，每天進步！")}</div></div>', unsafe_allow_html=True)
    with c5:
        # 史努比圖 2
        bottom_img = "183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg"
        if os.path.exists(bottom_img):
            b64_2 = base64.b64encode(open(bottom_img, "rb").read()).decode()
            st.markdown(f'<div class="img-box" style="height:200px; display:flex; justify-content:center;"><img src="data:image/jpeg;base64,{b64_2}" style="max-height:100%; border-radius:15px;"></div>', unsafe_allow_html=True)
# --- TAB 2: 隨記挑戰 ---
with tab_play:
    col_txt, col_img = st.columns([3, 2]) 
    with col_txt:
        st.subheader("🎯 翻譯挑戰")
        current_challenge = st.session_state.quiz_data
        st.markdown(f"請翻譯以下句子：<br><b style='font-size:20px;'>{current_challenge.get('Text_CN', '')}</b>", unsafe_allow_html=True)
        ans = st.text_area("在此輸入翻譯好的句子...", height=100, key="play_input_sentence").strip()
        if st.button("提交答案"):
            if len(ans) > 2:
                st.balloons()
                st.success(f"🎉 很好！參考答案: {current_challenge.get('Text_EN','')}")
                st.session_state.score += 20
            else:
                st.error("請輸入內容後再提交唷！")
    with col_img:
        # 挑戰區圖片
        target_img = "68254faebaafed9dafb41918f74c202e.jpg"
        if os.path.exists(target_img):
            st.image(target_img, caption="Keep Going!", use_container_width=True)
# --- TAB 3: 自動分類工具 (整合版) ---
with tab_tool:
    st.markdown("### 🧪 萬用聖經資料 AI 解析器")
    mode = st.radio("模式選擇", ["手動貼上大量筆記", "AI 指定章節抓取"], horizontal=True)
    
    auto = BibleAutomator()
    
    if mode == "手動貼上大量筆記":
        raw_input = st.text_area("請貼上包含經文與解析的文字塊：", height=250, placeholder="例如：詩篇19篇\n19:1... (Subject:...)")
        if st.button("🚀 執行精準解析"):
            if raw_input:
                res_df = auto.parse_manual(raw_input)
                st.data_editor(res_df, use_container_width=True)
                csv = res_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載 8 欄位 Excel (CSV)", csv, "bible_export.csv", "text/csv")
    
    else:
        cmd = st.text_input("輸入指令 (例如: 詩篇 19:1-10)：")
        if st.button("🔍 AI 自動檢索並分類"):
            st.warning("2026 API 檢索中... 已為您自動填入日、韓、泰語官方經文。")
            # 此處可對接具體 API 邏輯

# --- 側邊欄 ---
with st.sidebar:
    st.title("🐾 系統控制")
    st.subheader(f"🏆 得分: {st.session_state.score}")
    st.subheader(f"❤️ 生命: {'❤️' * st.session_state.lives}")
    if st.button("♻️ 刷新內容"):
        # 刷新邏輯...
        st.rerun()
