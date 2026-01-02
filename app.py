import streamlit as st
import pandas as pd
import requests
import io
import re
import os
import random
from datetime import datetime

# --- 1. 頁面配置與主題設定 ---
st.set_page_config(page_title="Memory Logic 2026 - Snoopy & Mario", layout="wide")

# 主題配色樣本 (可愛復古風)
THEMES = {
    "Snoopy Retro (奶油黃)": {"bg": "#FFF9E3", "box": "#FFFFFF", "accent": "#FFCDD2", "text": "#4A4A4A", "sub": "#F06292"},
    "Mario Classic (冒險紅)": {"bg": "#FFEBEE", "box": "#FFFFFF", "accent": "#E57373", "text": "#D32F2F", "sub": "#FF8A80"},
    "Woodstock (森林綠)": {"bg": "#F1F8E9", "box": "#FFFFFF", "accent": "#AED581", "text": "#33691E", "sub": "#689F38"}
}

# --- 2. 側邊欄控制台 ---
with st.sidebar:
    st.markdown("### 🐾 系統控制台")
    selected_theme = st.selectbox("選擇介面主題", list(THEMES.keys()))
    theme = THEMES[selected_theme]
    
    st.divider()
    # 遊戲狀態與學習進度
    if 'score' not in st.session_state: st.session_state.score = 0
    if 'lives' not in st.session_state: st.session_state.lives = 3
    if 'count' not in st.session_state: st.session_state.count = 0
    
    st.subheader(f"🏆 得分: {st.session_state.score}")
    st.subheader(f"❤️ 生命: {'❤️' * st.session_state.lives}")
    
    st.progress(min(st.session_state.count / 20.0, 1.0))
    st.caption(f"今日已處理項目: {st.session_state.count}")

    if st.button("♻️ 刷新內容並同步"):
        st.cache_data.clear()
        st.rerun()

# --- 3. CSS 注入 (含打字機與動畫) ---
st.markdown(f"""
    <style>
    @import url('fonts.googleapis.com');
    html, body, [data-testid="stAppViewContainer"] {{ background-color: {theme['bg']}; font-family: 'Comic Neue', cursive; }}
    
    .feature-box {{
        background-color: {theme['box']} !important;
        border-radius: 18px !important;
        padding: 20px !important;
        border: 3px solid {theme['accent']} !important;
        box-shadow: 6px 6px 0px {theme['accent']} !important;
        margin-bottom: 15px !important;
    }}
    
    .typing {{
        overflow: hidden; border-right: .15em solid orange; white-space: nowrap;
        animation: typing 3s steps(40, end), blink-caret .75s step-end infinite;
    }}
    @keyframes typing {{ from {{ width: 0 }} to {{ width: 100% }} }}
    @keyframes blink-caret {{ from, to {{ border-color: transparent }} 50% {{ border-color: orange; }} }}

    .mario-sprite {{ font-size: 50px; animation: bounce 0.5s infinite alternate; }}
    @keyframes bounce {{ from {{ transform: translateY(0); }} to {{ transform: translateY(-15px); }} }}
    
    .dict-btn {{ color: {theme['sub']}; text-decoration: none; font-weight: bold; float: right; border: 1px solid; padding: 2px 5px; border-radius: 5px; font-size: 12px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 資料庫與分類邏輯 (整合您之前的核心) ---
SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
GIDS = {"📖 經節": "1454083804", "🔤 單字": "1400979824", "🔗 片語": "1657258260"}

@st.cache_data(ttl=300)
def fetch_data(gid):
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=10)
        return pd.read_csv(io.StringIO(r.text)).fillna("")
    except: return pd.DataFrame()

def heuristic_classify(item):
    item = item.strip()
    if re.search(r'\b\d{1,3}:\d{1,3}\b', item): return "Verses"
    tokens = item.split()
    if len(tokens) <= 1: return "Words"
    if 2 <= len(tokens) <= 6: return "Phrases"
    return "Verses"

# --- 5. 主分頁架構 ---
tab_home, tab_play, tab_tool = st.tabs(["🏠 我的書桌", "🎯 闖關挑戰", "🧪 自動分類工具"])

# --- TAB 1: 我的書桌 (美化佈局) ---
with tab_home:
    df_v = fetch_data(GIDS["📖 經節"])
    df_w = fetch_data(GIDS["🔤 單字"])
    df_p = fetch_data(GIDS["🔗 片語"])

    v1 = df_v.sample(1).iloc[0] if not df_v.empty else {"Chinese": "請檢查連線", "Reference": ""}
    w1 = df_w.sample(1).iloc[0] if not df_w.empty else {"Vocab": "Study", "Definition": "學習"}
    p1 = df_p.sample(1).iloc[0] if not df_p.empty else {"Phrase": "Easy money", "Definition": "不義之財"}

    # 上方大框
    st.markdown(f'<div class="feature-box"><h3 style="color:{theme["sub"]};">💡 今日金句</h3><div class="typing" style="font-size:24px;">“{v1["Chinese"]}”</div><div style="color:gray; margin-top:10px;">— {v1["Reference"]}</div></div>', unsafe_allow_html=True)

    # 下方三欄：縮小單字片語，放大文法
    c1, c2, c3 = st.columns([1, 1.2, 1.8])
    with c1:
        st.markdown(f'<div class="feature-box"><a href="dictionary.cambridge.org{w1["Vocab"]}" target="_blank" class="dict-btn">DICT</a><b style="color:{theme["sub"]};">🔤 單字</b><br><span style="font-size:20px;">{w1["Vocab"]}</span><br><small>{w1["Definition"]}</small></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="feature-box"><b style="color:{theme["sub"]};">🔗 片語</b><br><span style="font-size:18px;">{p1["Phrase"]}</span><br><small>{p1["Definition"]}</small></div>', unsafe_allow_html=True)
    with c3:
        gram = w1.get("Grammar") or "保持學習，馬利歐就不會掉下去！"
        st.markdown(f'<div class="feature-box" style="background-color:#E3F2FD !important;"><b style="color:#0288D1;">📝 關鍵文法</b><br><p style="font-size:16px;">{gram}</p></div>', unsafe_allow_html=True)

# --- TAB 2: 闖關挑戰 (馬利歐遊戲) ---
with tab_play:
    st.markdown(f'<div style="text-align:center;"><span class="mario-sprite">🏃‍♂️</span> <span style="font-size:40px;">☁️</span> <span style="font-size:50px;">🐶</span></div>', unsafe_allow_html=True)
    
    if st.session_state.lives <= 0:
        st.error("💀 GAME OVER! 馬利歐需要休息...")
        if st.button("使用 1UP 蘑菇重生"):
            st.session_state.lives = 3
            st.rerun()
    else:
        st.subheader("⚡️ 瞬時翻譯挑戰 (中翻英)")
        q_item = w1 if random.random() > 0.5 else p1
        target = q_item.get("Vocab") or q_item.get("Phrase")
        meaning = q_item.get("Definition")
        
        st.write(f"題目： 「 **{meaning}** 」 的正確翻譯是？")
        ans = st.text_input("在此輸入答案... (注意大小寫)")
        
        if st.button("提交答案"):
            if ans.lower().strip() == target.lower().strip():
                st.balloons()
                st.session_state.score += 10
                st.session_state.count += 1
                st.success("✅ 正確！史努比幫你轉了一圈！")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.lives -= 1
                st.error(f"❌ 答錯了！生命值 -1。正確答案是: {target}")

# --- TAB 3: 自動分類工具 (整合功能) ---
with tab_tool:
    st.markdown("### 🧪 AI 自動分類與導出")
    input_text = st.text_area("在此貼上整篇文章、多個句子或經節...", height=200)
    
    if st.button("🚀 開始分析並分類"):
        lines = re.split(r'\n+|(?<=[。！？\.\?\!;；])\s*', input_text)
        results = []
        for l in lines:
            if l.strip():
                cat = heuristic_classify(l)
                results.append({"內容": l.strip(), "建議分類": cat})
        
        if results:
            res_df = pd.DataFrame(results)
            st.dataframe(res_df, use_container_width=True)
            
            # 下載 Excel 功能
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                res_df.to_excel(writer, index=False)
            st.download_button("⬇️ 匯出為 Excel", data=output.getvalue(), file_name="classified_items.xlsx")
            st.success("分類完成！您可以將內容複製到對應的 Google Sheet 欄位。")
