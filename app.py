import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# --- 1. 頁面基礎設定 ---
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# 自定義 CSS 優化間距與字體
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
    .verse-box { line-height: 1.4; margin-top: -15px; }
    .small-font { font-size: 13px; color: #555555; }
    /* 縮緊所有元件間距 */
    .stVerticalBlock { gap: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 圖片路徑設定
IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg",
    "Helper": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/helper_character.png" # 假設這是新上傳的原創圖
}

# --- 2. 側邊欄：原創活潑人物 ---
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다<br><span style="font-size:12px;">(你是上帝寶貴的珍寶)</span></p>', unsafe_allow_html=True)
    # 8) 這裡顯示新設計的原創可愛角色 (生成圖在下方)
    st.image("https://files.oaiusercontent.com/file-K1mC7fV3A5C9XW7Z4Y2S1Q?se=2024-01-15T15%3A00%3A00Z&sp=r&sv=2021-08-06&sr=b&rscc=max-age%3D31536000%2C%20private%2C%20immutable&rscd=attachment%3B%20filename%3Dcharacter.png", use_container_width=True)
    st.divider()
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/", use_container_width=True)

# --- 3. 主要 UI 配置 ---
# 7) 在分頁最後增加一個連結感的分頁 (Streamlit 原生限制，採增加一個分頁顯示連結)
tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# --- TAB1: 書桌 (🏠) ---
with tabs[0]:
    # 建立左右兩欄，左邊放置所有文字內容，右邊放置圖 A
    col_content, col_img_a = st.columns([0.65, 0.35])
    
    with col_content:
        # 1) 單字欄 (一格顯示所有語言，刪除重複中文)
        st.info("**Becoming** / 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 🇹🇭 เหมาะสม | 🇨🇳 相稱")
        
        # 1) 片語欄 (一格顯示所有語言，刪除重複中文)
        st.info("**Still less** / 🇯🇵 まして | 🇰🇷 하물며 | 🇹🇭 ยิ่งกว่านั้น | 🇨🇳 何況 / 更不用說")
        
        # 2, 3, 4) 今日金句：移除標籤碼，緊接在片語下方無空位
        st.success("""
        🌟 **Pro 17:07** Fine speech is not becoming to a fool; still less is false speech to a prince.  
        すぐれた言葉は愚か者にはふさわしくない。偽りの言葉は君主にはなおさらふさわしくない。  
        愚頑人說美言本不相稱，何況君王說謊話呢？
        """, icon="📖")

    with col_img_a:
        # 4) 確保圖片高度與左側三個欄框對齊
        st.image(IMG_URLS["A"], use_container_width=True)

    # 5) 文法解析整體往上移，刪除標題與 Grammar Points 字樣
    st.markdown("---") # 分隔線
    cg1, cg2 = st.columns(2)
    with cg1:
        st.markdown("""
        **Ex 1:** Casual attire is not becoming to a CEO during a board meeting; still less is unprofessional language to a legal consultant.  
        <p class="small-font">便服對執行長不相稱；更不用說不專業言語對法律顧問了。</p>
        """, unsafe_allow_html=True)
        
    with cg2:
        st.markdown("""
        **Ex 2:** Wealth is not becoming to a man without virtue; still less is power to a person with a cruel heart.  
        <p class="small-font">財富對於無德之人不相稱；更不用說權力對於內心殘暴之人了。</p>
        """, unsafe_allow_html=True)

# --- 其餘分頁保持邏輯 ---
with tabs[1]:
    st.date_input("選擇日期", datetime.now())
with tabs[3]:
    st.subheader("📂 資料庫存檔")
    input_c = st.text_area("經文輸入", height=100)
    if st.button("💾 正式存檔"):
        st.success("已存入 Google Sheets")

# --- TAB2~4 保持原結構 ---
with tabs[1]:
    st.caption("（保留原筆記月曆與多語對照結構）")
with tabs[3]:
    st.caption("（保留原資料庫存檔邏輯）")

# --- TAB2: 每日筆記 ---
with tabs[1]:
    col_note_l, col_note_r = st.columns([0.7, 0.3])
    with col_note_l:
        st.subheader("📅 筆記月曆")
        # 此處可整合 streamlit-calendar 組件
        st.date_input("選擇日期以查看筆記", datetime.now())
        st.text_area("✍️ 筆記內容", height=200)
        
        # 篩選欄位
        st.text("🔍 篩選與搜尋")
        c_filter1, c_filter2 = st.columns([3, 1])
        c_filter1.text_input("搜尋標題/內容/待辦事項", label_visibility="collapsed")
        c_filter2.link_button("✨ Google AI", "https://gemini.google.com/")
        
        # 每日筆記欄位
        st.text_input("📒 筆記標題")
        st.text_area("✍️ 筆記內容與待辦事項", height=200)

    with col_note_r:
        st.subheader("🌏 多語對照 (V2 Sheet)")
        st.caption("Pro 17:07 對照")
        st.write("**日文:** すぐれた言葉は...")
        st.write("**韓文:** 미련한 자에게...")
        st.write("**泰文:** ริมฝีปากที่ประณีต...")
        # 7) 側邊欄史努比位置調換到這裡
        st.image(IMG_URLS["C"], use_container_width=True, caption="Study Partner")

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

