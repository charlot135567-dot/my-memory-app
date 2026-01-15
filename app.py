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
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 22px; color: #FF8C00; text-align: center; }
    .small-font { font-size: 12px; color: #666666; line-height: 1.2; }
    .verse-font { font-size: 14px; font-weight: 500; }
    /* 移除 subheader 多餘間距 */
    .stMarkdown h3 { margin-bottom: -10px; }
    </style>
    """, unsafe_allow_html=True)

IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg"
}

# --- 2. 側邊欄 ---
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다<br><span style="font-size:14px;">(你是上帝寶貴的珍寶)</span></p>', unsafe_allow_html=True)
    _, col_img, _ = st.columns([0.3, 0.4, 0.3])
    with col_img:
        st.image(IMG_URLS["C"])
    st.divider()
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/", use_container_width=True)

# --- 3. 主要 UI 配置 ---
# 7) 在分頁最後增加一個連結感的分頁 (Streamlit 原生限制，採增加一個分頁顯示連結)
tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫", "🤖 Google AI"])

with tabs[4]:
    st.info("點擊下方按鈕開啟 AI 輔助解析")
    st.link_button("前往 Gemini AI", "https://gemini.google.com/")

# --- TAB1: 書桌 ---
with tabs[0]:
    # 4, 5) 達成 1:1:1 比例：單字欄 : 片語欄 : 史努比A
    c_word, c_phrase, c_snoopy_a = st.columns([1, 1, 1])
    
    with c_word:
        st.info("""
        **Becoming** 🇯🇵 ふさわしい | 🇨🇳 相稱  
        🇰🇷 어울리는 | 🇹🇭 เหมาะสม
        """)
    
    with c_phrase:
        st.info("""
        **Still less** 🇯🇵 まして | 🇨🇳 何況 / 更不用說  
        🇰🇷 하물며 | 🇹🇭 ยิ่งกว่านั้น
        """)
        
    with c_snoopy_a:
        st.image(IMG_URLS["A"], use_container_width=True)

    # 中層：今日金句 (左側對照 + 右側史努比B)
    col_verse, col_snoopy_b = st.columns([2, 1])
    
    with col_verse:
        # 6) 今日金句：中英日對照，不跳行
        st.success(f"""
        <div class="verse-font">
        🌟 **Pro 17:07** Fine speech is not becoming to a fool; still less is false speech to a prince. <br>
        <span class="small-font">
        **[中]** 愚頑人說美言本不相稱，何況君王說謊話呢？ <br>
        **[日]** すぐれた言葉は愚か者にはふさわしくない。偽りの言葉は君主にはなおさらふさわしくない。
        </span>
        </div>
        """, icon="📖")

    with col_snoopy_b:
        # 5) 史努比 B 比例與上方 A 一致
        st.image(IMG_URLS["B"], use_container_width=True)

    # 8) 下層文法解析：刪除標題，給予兩句例句空間
    st.divider()
    cg1, cg2 = st.columns(2)
    with cg1:
        st.markdown("""
        <p class="small-font">
        1. <b>現在簡單式</b>：表達恆常真理。<br>
        2. <b>Fine speech</b>(優美言辭)、<b>Becoming to</b>(相稱)、<b>Still less</b>(何況)。
        </p>
        <b>Example 1:</b><br>
        <span style="font-size:13px;">Casual attire is not becoming to a CEO during a board meeting; still less is unprofessional language to a legal consultant.</span>
        <p class="small-font">便服對執行長不相稱；更不用說不專業言語對法律顧問了。</p>
        """, unsafe_allow_html=True)
        
    with cg2:
        st.markdown("""
        <b>Example 2:</b><br>
        <span style="font-size:13px;">Wealth is not becoming to a man without virtue; still less is power to a person with a cruel heart.</span>
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
