import streamlit as st
import pandas as pd
import requests
import io
import re
import os
import random
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

# --- 3. 資料抓取函數 ---
@st.cache_data(ttl=300)
def fetch_data(gid):
    SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200: return pd.read_csv(io.StringIO(r.text)).fillna("")
    except: pass
    return pd.DataFrame()

# --- 4. CSS 樣式 (包含所有高度對齊與樣式) ---
st.markdown(f"""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [data-testid="stAppViewContainer"] {{ background-color: {THEME['bg']}; font-family: 'Comic Neue', cursive; }}
    .feature-box {{
        background-color: {THEME['box']} !important; border-radius: 18px !important; padding: 18px !important;
        border: 2.5px solid {THEME['accent']} !important; box-shadow: 4px 4px 0px {THEME['accent']} !important;
        margin-bottom: 12px !important; height: 150px !important; display: flex; flex-direction: column; justify-content: center;
    }}
    .grammar-box {{ height: 220px !important; justify-content: flex-start; }}
    .img-box {{ height: 150px !important; display: flex; justify-content: center; align-items: center; }}
    .img-box img {{ max-height: 100%; width: auto; border-radius: 15px; }}
    .img-box.grammar-img {{ height: 220px !important; }}
    .kw {{ color: {THEME['keyword']}; font-weight: bolder; font-size: 1.2em; background-color: #FFFF00; padding: 2px 4px; border-radius: 4px; }}
    .dict-btn {{ color: {THEME['sub']} !important; text-decoration: none !important; font-weight: bold; float: right; font-size: 11px; border: 1px solid {THEME['sub']}; padding: 1px 6px; border-radius: 4px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. 定義分頁標籤 (解決 NameError 的關鍵行！) ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 隨記挑戰", "🧪 自動分類工具"])

# --- TAB 1: 我的書桌 (排版已穩定) ---
with tab_home:
    v1 = st.session_state.verse_data
    w1 = st.session_state.word_data
    p1 = st.session_state.phrase_data

    # 第一排：單字 + 片語 + 史努比圖片 
    c1, c2, c3 = st.columns() 
    with c1:
        voc = w1.get("Vocab", "Study")
        st.markdown(f'<div class="feature-box"><a href="dictionary.cambridge.org{quote(str(voc))}" target="_blank" class="dict-btn">🔍 字典</a><small>🔤 單字</small><br><b style="font-size:24px;">{voc}</b><br><small>{w1.get("Definition","")}</small></div>', unsafe_allow_html=True)
    with c2:
        phr = p1.get("Phrase", "Keep it up")
        st.markdown(f'<div class="feature-box"><a href="www.google.com{quote(str(phr))}+meaning" target="_blank" class="dict-btn">🔗 參考</a><small>🔗 片語</small><br><b style="font-size:22px;">{phr}</b><br><small>{p1.get("Definition","")}</small></div>', unsafe_allow_html=True)
    with c3:
        top_img = "f364bd220887627.67cae1bd07457.jpg"
        if os.path.exists(top_img): st.markdown(f'<div class="img-box"> <img src="data:image/jpeg;base64,{base64.b64encode(open(top_img, "rb").read()).decode()}" alt="Snoopy 1" /> </div>', unsafe_allow_html=True)

    # 第二排：今日金句
    raw_ch = v1.get("Chinese", "")
    kw = str(v1.get("Keyword", ""))
    disp = raw_ch.replace(kw, f'<span class="kw">{kw}</span>') if kw and kw in raw_ch else raw_ch
    st.markdown(f'<div class="feature-box" style="min-height:140px; height: auto !important;"><h3 style="color:{THEME["sub"]}; margin-top:0; font-family: "Gloria Hallelujah", cursive;">💡 今日金句</h3><div style="font-size:26px; line-height:1.4; font-weight:bold;">“{disp}”</div><div style="color:gray; margin-top:10px; text-align:right;">— {v1.get("Reference","")}</div></div>', unsafe_allow_html=True)

    # 第三排：文法 (左側大框) + 史努比圖片 (右側)
    c4, c5 = st.columns()
    with c4:
        st.markdown(f'<div class="feature-box grammar-box" style="background-color:#E3F2FD !important;"><small>📝 關鍵文法</small><br><div style="font-size:15px; margin-top:8px;">{w1.get("Grammar", "保持學習，每天進步！")}</div></div>', unsafe_allow_html=True)
    with c5:
        bottom_img = "183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg"
        if os.path.exists(bottom_img): st.markdown(f'<div class="img-box grammar-img"> <img src="data:image/jpeg;base64,{base64.b64encode(open(bottom_img, "rb").read()).decode()}" alt="Snoopy 2" /> </div>', unsafe_allow_html=True)

# --- TAB 2: 隨記挑戰 ---
with tab_play:
    col_txt, col_img = st.columns()
    with col_txt:
        st.subheader("🎯 翻譯挑戰 (句子專屬)")
        current_challenge = st.session_state.quiz_data
        st.markdown(f"請翻譯以下句子：<br><b>{current_challenge.get('Text_CN', '')}</b>", unsafe_allow_html=True)
        ans = st.text_area("在此輸入翻譯好的句子...", height=150, key="play_input_sentence").strip()
        if st.button("提交答案"):
            if len(ans) > 5 and abs(len(ans) - len(current_challenge.get('Text_EN',''))) < 20:
                st.balloons()
                st.session_state.score += 20
                st.success("🎉 太棒了！答對了！(請點擊側邊欄刷新下一題)")
            else:
                st.session_state.lives -= 1
                st.error(f"❌ 答錯了！答案是: {current_challenge.get('Text_EN','')}")
    with col_img:
        target_img = "68254faebaafed9dafb41918f74c202e.jpg"
        if os.path.exists(target_img): st.image(target_img, caption="Cheers!", width=200)

# --- TAB 3: 自動分類工具 (輸入框已修正) ---
with tab_tool:
    st.markdown("### 🧪 AI 自動分類與匯出")
    input_text = st.text_area("在此貼上整篇文章、多個句子或經節...", height=200)
    
    def heuristic_classify(item):
        item = item.strip()
        if re.search(r'\b\d{1,3}:\d{1,3}\b', item): return "Verses"
        tokens = item.split()
        if len(tokens) <= 1: return "Words"
        if 2 <= len(tokens) <= 6: return "Phrases"
        return "Verses"

    if st.button("🚀 開始分析分類"):
        lines = re.split(r'\n+|(?<=[。！？\.\?\!;；])\s*', input_text)
        results = [{"內容": l.strip(), "建議分類": heuristic_classify(l)} for l in lines if l.strip()]
        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)

            # 匯出 Excel 功能 (括號已修正)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                pd.DataFrame(results).to_excel(writer, index=False)
                writer.close()
            
            st.download_button(
                label="⬇️ 下載為 Excel (.xlsx)", 
                data=output.getvalue(), 
                file_name="classified_items.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("分類完成！您可以下載檔案。")

# --- 側邊欄 ---
with st.sidebar:
    st.markdown("### 🐾 系統控制台")
    st.subheader(f"🏆 得分: {st.session_state.score}")
    st.subheader(f"❤️ 生命: {'❤️' * max(0, st.session_state.lives)}")
    if st.button("♻️ 刷新內容"):
        df_w = fetch_data("1400979824")
        df_v = fetch_data("1454083804")
        df_p = fetch_data("1657258260")
        source_df = pd.concat([df_v, df_p.rename(columns={'Phrase': 'Chinese', 'Definition': 'English'})], ignore_index=True)
        if not source_df.empty:
            new_quiz_item = source_df.sample(1).iloc
            st.session_state.quiz_data = {"Text_CN": new_quiz_item.get("Chinese", ""), "Text_EN": new_quiz_item.get("English", "") or new_quiz_item.get("Vocab", "") or new_quiz_item.get("Phrase", "")}
        if not df_w.empty: st.session_state.word_data = df_w.sample(1).iloc.to_dict()
        if not df_v.empty: st.session_state.verse_data = df_v.sample(1).iloc.to_dict()
        if not df_p.empty: st.session_state.phrase_data = df_p.sample(1).iloc.to_dict()
        st.rerun()
