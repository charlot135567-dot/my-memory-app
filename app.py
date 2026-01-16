import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# --- 1. 頁面基礎設定 ---
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# 自定義 CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
    .small-font { font-size: 13px; color: #555555; }
    
    /* 1) TAB1 文法欄位底部對齊經節 */
    .grammar-box {
        background-color: #f8f9fa; border-radius: 8px; padding: 15px;
        border-left: 5px solid #FF8C00; font-size: 14px; 
        height: 250px; /* 固定高度以確保與左側對齊 */
        display: flex; flex-direction: column; justify-content: space-between;
    }
    
    /* 縮緊所有元件間距 */
    .stVerticalBlock { gap: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 圖片路徑設定
IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg",
    "M1": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro1.jpg",
    "M3": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro3.jpg"
}

# --- 2. 側邊欄：控制台 (Mashimaro3) ---
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다<br><span style="font-size:12px;">(你是上帝寶貴的珍寶)</span></p>', unsafe_allow_html=True)
    # 控制台圖片換成 Mashimaro3
    st.image(IMG_URLS["M3"], use_container_width=True)
    st.divider()
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/", use_container_width=True)

# --- 3. 主要 UI 配置 ---
tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# --- TAB1: 書桌 (🏠) ---
with tabs[0]:
    col_content, col_m1 = st.columns([0.65, 0.35])
    
    with col_content:
        st.info("**Becoming** / 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 泰: เหมาะสม | 🇨🇳 相稱")
        st.info("**Still less** / 🇯🇵 まして | 🇰🇷 하물며 | 泰: ยิ่งกว่านั้น | 🇨🇳 何況")
        # 2) 補上日語經文
        st.success("""
        🌟 **Pro 17:07** Fine speech is not becoming to a fool; still less is false speech to a prince.  
        🇯🇵 すぐれた言葉は愚か者にはふさわしくない。偽りの言葉は君主にはなおさらふさわしくない。  
        🇨🇳 愚頑人說美言本不相稱，何況君王說謊話呢？
        """, icon="📖")

    with col_m1:
        # 主畫面右上層圖片換成 Mashimaro1
        st.image(IMG_URLS["M1"], use_container_width=True)
        # 1) 文法欄位底部與經節對齊
        st.markdown("""
        <div class="grammar-box">
            <div>
                <b>時態(Tense):</b> 現在簡單式表達恆常真理<br>
                <b>核心片語與詞彙:</b><br>
                • Fine speech (優美言辭)<br>
                • Becoming to (相稱/合宜)<br>
                • Still less (何況)<br>
                • False speech (虛假言辭)
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3) 恢復最下層的文法例句
    st.markdown("---")
    cg1, cg2 = st.columns(2)
    with cg1:
        st.markdown("**Ex 1:** Casual attire is not becoming to a CEO... <br><p class='small-font'>便服對執行長不相稱；更不用說不專業言語了。</p>", unsafe_allow_html=True)
    with cg2:
        st.markdown("**Ex 2:** Wealth is not becoming to a man without virtue... <br><p class='small-font'>財富對於無德之人不相稱；更不用說權力了。</p>", unsafe_allow_html=True)

# --- TAB2: 每日筆記 (📓) ---
with tabs[1]:
    top_l, top_r = st.columns([0.5, 0.5])
    
    with top_l:
        # 1 & 9) 日期篩選與待辦事項 (可在月曆選擇日期並填入待辦/時間/提醒)
        sel_date = st.date_input("選擇日期", value=datetime(2026, 1, 16), label_visibility="collapsed")
        st.write(f"📅 **{sel_date} 待辦與提醒設定**")
        
        c_todo, c_time = st.columns([0.7, 0.3])
        todo_item = c_todo.text_input("填入待辦事項", placeholder="輸入任務...", label_visibility="collapsed")
        remind_time = c_time.time_input("設定提醒", time(9, 0), label_visibility="collapsed")
        
        if st.button("🔔 設定提醒並加入清單"):
            st.toast(f"已設定 {remind_time} 提醒：{todo_item}")

    with top_r:
        # 7) 多語對照補上泰文
        st.write("**📖 Pro 17:07 多語對照**")
        st.write("<span style='font-size:13px;'><b>日:</b> すぐれた言葉は愚か者には...<br><b>韓:</b> 미련한 자에게 격에 맞지 않는 말이...<br><b>泰:</b> ริมฝีปากที่ประเสริฐไม่คู่ควรกับคนโง่...</span>", unsafe_allow_html=True)
        st.image(IMG_URLS["C"], width=150)

    st.divider()

    # 8) 筆記標題與存檔按鈕合併
    note_col, save_col = st.columns([0.7, 0.3])
    note_name = note_col.text_input("筆記標題", value="2026-01-16 靈修筆記", label_visibility="collapsed")
    if save_col.button(f"💾 存檔: {note_name[:10]}...", use_container_width=True):
        st.success(f"筆記 '{note_name}' 已成功存檔！")

    # 10) 筆記內容框優化
    st.text_area(label="筆記📝", value="", height=250, placeholder="筆記📝", label_visibility="visible")

# --- TAB3 & TAB4 (保留原有邏輯) ---
with tabs[2]:
    st.subheader("📝 翻譯挑戰")
    st.image(IMG_URLS["B"], width=200)
with tabs[3]:
    st.subheader("📂 資料庫存檔")
    input_content = st.text_area("📥 聖經經文 / 英文文稿輸入", height=150)
    if st.button("💾 正式存檔"):
        st.success("已存入雲端資料庫")

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

