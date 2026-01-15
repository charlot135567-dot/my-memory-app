import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# --- 1. 頁面基礎設定 ---
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# 自定義 CSS：可愛風韓文字體與小字效果
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    .cute-korean {
        font-family: 'Gamja+Flower', cursive;
        font-size: 24px;
        color: #FF8C00;
        text-align: center;
    }
    .small-font {
        font-size: 13px;
        color: #666666;
    }
    </style>
    """, unsafe_allow_html=True)

# 史努比照片網址
IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg"
}

# --- 2. 側邊欄：功能選單 ---
with st.sidebar:
    # 7) 韓文鼓勵經節與縮小史努比
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다<br>(你是上帝寶貴的珍寶)</p>', unsafe_allow_html=True)
    
    # 按比例縮成一半大小 (使用 columns 技巧居中並限縮寬度)
    _, col_img, _ = st.columns([0.25, 0.5, 0.25])
    with col_img:
        st.image(IMG_URLS["C"])

# --- 3. 主要 TAB UI 配置 ---
tabs = st.tabs(["🏠 書桌", "📓 每日筆記", "✍️ 翻譯挑戰", "📂 資料庫"])

# --- TAB1: 書桌 (🏠) ---
with tabs[0]:
    # 定義左右比例
    col_left, col_right = st.columns([0.6, 0.4])
    
    with col_left:
        # 2, 3, 4, 5, 6) 整合後的單字與片語區 (直接填入翻譯，刪除多餘選擇與標籤)
        st.subheader("📚 核心單字與片語對照")
        st.info("""
        **Becoming / 相稱** 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 🇹🇭 เหมาะสม | 🇨🇳 相稱  
        
        **Still less / 何況** 🇯🇵 まして | 🇰🇷 하물며 | 🇹🇭 ยิ่งกว่านั้น | 🇨🇳 何況 / 更不用說
        """)

        # [中層] 今日金句 (金句與上層同寬)
        st.divider()
        st.subheader("🌟 今日金句")
        st.success("**Pro 17:07**\n\nFine speech is not becoming to a fool; still less is false speech to a prince.")

    with col_right:
        # 1) 右側史努比圖：按比例與左側 [上層+中層] 同高度
        # 使用 container 保持緊湊
        with st.container():
            st.image(IMG_URLS["A"], use_container_width=True)
            st.image(IMG_URLS["B"], use_container_width=True)

    # 1) 最下層位置：全給文法解析使用
    st.divider()
    st.subheader("📝 深入文法解析")
    # 8) 詳細文法內容與縮小翻譯
    c_gram1, c_gram2 = st.columns(2)
    with c_gram1:
        st.markdown("""
        #### Grammar Points:
        1. **時態 (Tense)**: 現在簡單式  
           <p class="small-font">用於表達恆常真理、格言或普遍現象。</p>
        2. **核心詞彙解析**:
           * **Fine speech**: 優美言辭/雄辯 <p class="small-font">(指高雅或有說服力的談吐)</p>
           * **Becoming to**: 相稱/合宜 <p class="small-font">(形容詞用法，後接對象)</p>
           * **Still less**: 何況/更不用說 <p class="small-font">(用於否定句後的遞進比較)</p>
           * **False speech**: 虛假言辭/謊言 <p class="small-font">(與 Fine speech 形成對比)</p>
        """, unsafe_allow_html=True)
    
    with c_gram2:
        st.markdown("""
        #### 實戰例句 (Example):
        > *Casual attire is not becoming to a CEO during a board meeting; still less is unprofessional language to a legal consultant.* **中文翻譯:** <p class="small-font">董事會議中，便服對執行長而言並不相稱；<br>更不用說不專業的言語對於法律顧問了。</p>
        """, unsafe_allow_html=True)

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

# --- TAB3: 翻譯挑戰 ---
with tabs[2]:
    # 1) 篩選範圍與 AI 連結
    c_t1, c_t2 = st.columns([3, 1])
    c_t1.selectbox("翻譯題篩選範圍", ["最新一週", "最新一月", "最新一季"])
    c_t2.link_button("✨ Google AI", "https://gemini.google.com/")
    
    # 2-3) 題目與作答
    st.subheader("📝 翻譯挑戰 (V1 Sheet)")
    for i in range(1, 4):
        st.write(f"題目 {i}: 愚頑人說美言本不相稱...")
        st.text_input(f"請輸入英文翻譯 ({i})", key=f"ans_{i}")

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
