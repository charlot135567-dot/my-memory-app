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
    st.image(IMG_URLS["C"], caption="Snoopy Helper", use_column_width=True)
    st.title("控制面板")
    # 移除資料來源設定與 JSON 相關程式

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
            st.info("**單字 (Vocab)**\n\nBecoming / 相稱")  # 來源：W/P Sheet
        with c2:
            st.info("**片語 (Phrase)**\n\nStill less / 何況")  # 來源：W/P Sheet

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
                - Casual attire is not becoming to a CEO during a board meeting; still less is unprofessional language to a legal consultant.
                - 休閒服裝在董事會議中對 CEO 並不相稱；更不用說對法律顧問使用不專業的語言了。
            """, unsafe_allow_html=True)

    with col_right:
        # 右半部：史努比照片
        st.image(IMG_URLS["A"], use_column_width=True)
        st.image(IMG_URLS["B"], use_column_width=True)
