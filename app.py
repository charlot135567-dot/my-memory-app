import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# --- 1. 頁面基礎設定 ---
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# 史努比照片網址
IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg"
}

# --- 2. 側邊欄：功能選單 ---
with st.sidebar:
    st.image(IMG_URLS["C"], caption="Snoopy Helper", use_column_width=True, width=150, height=100)
    st.markdown("<h3 style='color: pink;'>힘내세요! 당신은 할 수 있어요!</h3>", unsafe_allow_html=True)

# --- 3. 主要 TAB UI 配置 ---
tabs = st.tabs(["🏠 書桌", "📓 每日筆記", "✍️ 翻譯挑戰", "📂 資料庫"])

# --- TAB1: 書桌 (🏠 + 待辦事項) ---
with tabs[0]:
    col_left, col_right = st.columns([0.6, 0.4])
    
    with col_left:
        # [上層] 單字與片語
        st.subheader("📚 核心單字與片語")
        c1, c2 = st.columns(2)
        with c1:
            st.info("**單字 (Vocab)**\n\nBecoming / 相稱\n\n日文: すぐれた言葉\n韓文: 미련한 자에게\n泰文: คำพูดที่ดี")
        with c2:
            st.info("**片語 (Phrase)**\n\nStill less / 何況\n\n日文: まして\n韓文: 더욱이\n泰文: ยิ่งไปกว่านั้น")

        # [中層] 今日金句
        st.divider()
        st.subheader("🌟 今日金句 (V1 Sheet)")
        st.success("**Pro 17:07**\n\nFine speech is not becoming to a fool; still less is false speech to a prince.")

        # [下層] 經文文法解析
        with st.expander("📝 文法解析 (V1 Sheet)", expanded=True):
            st.markdown("""
            - **時態**: 現在簡單式表達恆常真理。
            - **核心詞彙**: Becoming to (形容詞片語)。
            - **句型**: 倒裝句 (Still less is...)。
            - **例句**:
              - **英文**: Casual attire is not becoming to a CEO during a board meeting; still less is unprofessional language to a legal consultant.
              - **中文**: 在董事會議中，隨便的服裝不適合 CEO；更不用說對法律顧問使用不專業的語言了。
            """)

    with col_right:
         # 右半部：史努比照片
           st.image(IMG_URLS["A"], caption="Snoopy Helper", width=150, height=100)
           st.image(IMG_URLS["B"], caption="Snoopy Helper", width=150, height=100)

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
