import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# --- 1. 頁面基礎設定 (已取代舊有設定) ---
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# 整合原有的 CSS 與新需求 (角色繪圖、佈局優化)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    
    /* 原有的字體樣式 */
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
    .small-font { font-size: 13px; color: #555555; }
    .stVerticalBlock { gap: 0.4rem !important; }

    /* 原創角色繪製 (史努比/賤兔風格) - 用於 TAB1 與側邊欄 */
    .char-container { display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 5px; }
    .cute-char {
        width: 38px; height: 30px; background: white; border: 2px solid #333;
        border-radius: 50% 50% 45% 45%; position: relative;
    }
    .cute-char::before, .cute-char::after { /* 賤兔長耳朵感 */
        content: ''; position: absolute; width: 10px; height: 20px; 
        background: #333; border-radius: 50%; top: 5px;
    }
    .cute-char::before { left: -8px; transform: rotate(-15deg); }
    .cute-char::after { right: -8px; transform: rotate(15deg); }
    .eye { position: absolute; width: 3px; height: 3px; background: #333; border-radius: 50%; top: 14px; }
    .eye.left { left: 11px; } .eye.right { right: 11px; }
    .nose { position: absolute; width: 5px; height: 3px; background: #333; border-radius: 50%; top: 17px; left: 16.5px; }

    /* Grammar 專屬欄框 */
    .grammar-box {
        background-color: #f8f9fa; border-radius: 8px; padding: 10px;
        border-left: 5px solid #FF8C00; font-size: 13.5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 圖片路徑 (保留您的原始連結)
IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg"
}

# 初始化資料存檔邏輯
if 'todo_list' not in st.session_state:
    st.session_state.todo_list = []

# --- 2. 側邊欄 ---
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다<br><span style="font-size:12px;">(你是上帝寶貴的珍寶)</span></p>', unsafe_allow_html=True)
    # 顯示原創角色 (側邊欄版)
    st.markdown('<div class="char-container"><div class="cute-char"><div class="eye left"></div><div class="eye right"></div><div class="nose"></div></div></div>', unsafe_allow_html=True)
    st.divider()
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/", use_container_width=True)

# --- 3. 主要分頁 ---
tabs = st.tabs(["🏠 書桌", "📓 每日筆記", "✍️ 挑戰", "📂 資料庫"])

# --- TAB1: 書桌 ---
with tabs[0]:
    col_l, col_r = st.columns([0.65, 0.35])
    with col_l:
        st.info("**Becoming** / 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 🇹🇭 เหมาะสม | 🇨🇳 相稱")
        st.info("**Still less** / 🇯🇵 まして | 🇰🇷 하물며 | 🇹🇭 ยิ่งกว่านั้น | 🇨🇳 何況")
        st.success("📖 **Pro 17:07** Fine speech is not becoming to a fool; still less is false speech to a prince. \n\n 愚頑人說美言本不相稱，何況君王說謊話呢？")
    
    with col_r:
        # 13) 角色縮小並工整對齊左方欄位
        st.markdown('<div class="char-container"><div class="cute-char"><div class="eye left"></div><div class="eye right"></div><div class="nose"></div></div></div>', unsafe_allow_html=True)
        # 3) 騰出的空間顯示 Grammar
        st.markdown("""
        <div class="grammar-box">
            <b>時態 (Tense):</b> 現在簡單式 (恆常真理)<br>
            <b>核心片語:</b><br>
            • Fine speech (優美言辭)<br>
            • Becoming to (相稱/合宜)<br>
            • Still less (何況/更不用說)
        </div>
        """, unsafe_allow_html=True)

# --- TAB2: 每日筆記 (整合待辦與搜尋) ---
with tabs[1]:
    # 10) 上半部 UI 欄位對稱設計
    top_l, top_r = st.columns([0.5, 0.5])
    
    with top_l:
        # 2) 縮小日期篩選
        sel_date = st.date_input("日期", value=datetime(2026, 1, 16), label_visibility="collapsed")
        # 8) 待辦事項清單
        st.write("**📝 今日及以後的待辦清單**")
        # 模擬顯示，實際可從 session_state 讀取
        st.checkbox("完成提摩太前書查經", value=True)
        st.checkbox("更新 AI 教材生成指令", value=False)
        with st.expander("更多待辦事項..."):
            st.write("• 預習下週主日經文")

    with top_r:
        # 9) 經文全句顯現
        st.write("**Pro 17:07 多語對照**")
        st.write("🇯🇵 すぐれた言葉は愚か者にはふさわしくない...")
        st.write("🇰🇷 미련한 자에게 격에 맞지 않는 말이...")
        # 6) 角色寬度高度縮減 1/3
        st.markdown('<div style="transform: scale(0.65); opacity: 0.7;"><div class="char-container"><div class="cute-char"><div class="eye left"></div><div class="eye right"></div><div class="nose"></div></div></div></div>', unsafe_allow_html=True)

    st.divider()
    
    # 11 & 12) 筆記功能
    nb_title_col, nb_save_col = st.columns([0.8, 0.2])
    with nb_title_col:
        st.text_input("筆記標題 (關鍵字搜尋用)", key="note_title")
    with nb_save_col:
        st.write(" ") # 調整按鈕對齊
        st.button("💾 Save Note", use_container_width=True)
    
    st.text_area("待辦事項與筆記內容", height=200, placeholder="在此填寫待辦、提醒或詳細筆記...")

# --- TAB3: 翻譯挑戰 ---
with tabs[2]:
    # 建立左右比例，左邊作答，右邊放縮小的史努比 B
    col_challenge, col_deco = st.columns([0.7, 0.3])
    
    with col_challenge:
        st.subheader("📝 翻譯挑戰")
        # 示範題目
        st.write("題目 1: 愚頑人說美言本不相稱...")
        st.text_input("請輸入英文翻譯", key="ans_1", placeholder="Type your translation here...")
    
    with col_deco:
        # 7) 史努比 B 縮小並移至此 (使用 width 控制大小)
        st.image(IMG_URLS["B"], width=200, caption="Keep Going!")

# --- TAB4: 資料庫 (輸入與連結) ---
with tabs[3]:
    # 1) 外部連結區
    st.subheader("🔗 聖經與 AI 資源")
    cl1, cl2, cl3, cl4 = st.columns(4)
    cl1.link_button("ChatGPT", "https://chat.openai.com/")
    cl2.link_button("Google AI", "https://gemini.google.com/")
    cl3.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb")
    cl4.link_button("THSV11", "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")

    st.divider()
    
    # 2) 輸入資料欄位與按鍵
    input_content = st.text_area("📥 聖經經文 / 英文文稿輸入", height=150, help="輸入中文經文(V 卷章節)或英文文稿")
    
    btn_l, btn_r = st.columns(2)
    if btn_l.button("📥 輸入 - 經文/文稿"):
        st.toast("已讀取文稿，請搭配 AI 指令解析。")
    if btn_r.button("💾 存檔 - AI 解析完資料"):
        # 這裡放置寫入 Google Sheets 的邏輯
        st.success("資料已成功存入雲端資料庫！")

    st.info("💡 提示：請將 AI 產出的表格內容貼入下方對應欄位後按存檔。")

