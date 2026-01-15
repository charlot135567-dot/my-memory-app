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
