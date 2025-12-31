python
import streamlit as st
import pandas as pd
import random

# 頁面基本設定
st.set_page_config(page_title="Memory Logic 2025", page_icon="🛡️")

# --- 1. 資料庫串接 ---
# 請在此處貼上你從 Google Sheets "發布到網路" 取得的網址
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0iqV8nIk_JibUbCPzf8-9SaTP3EexTgF9vce8n-HgKN3QkCDkksMVbZhDmRZY9gushTthKwSPA56A/pubhtml"

def load_data():
    try:
        # 將網址格式轉換為 CSV 下載格式
        csv_url = SHEET_URL.replace("/pubhtml", "/pub?output=csv")
        data = pd.read_csv(csv_url)
        # 清除空格
        data.columns = [c.strip() for c in data.columns]
        return data
    except Exception as e:
        st.error(f"資料讀取失敗，請檢查發布網址。錯誤訊息: {e}")
        return pd.DataFrame()

df = load_data()

# --- 2. 核心邏輯處理 ---
st.title("🛡️ Memory Logic 2.0")

# 熱身提醒 (隨機取 3 筆)
if not df.empty:
    st.sidebar.subheader("🔥 Daily Warm-up")
    warmup = df.sample(min(len(df), 3))
    for i, row in warmup.iterrows():
        st.sidebar.caption(f"{row['English']}")

# 指令輸入
cmd = st.text_input("輸入指令 (R: 複習, G: 校對,清單請向下捲動):").strip().upper()

if cmd == "R":
    st.divider()
    test_item = df.sample(1).iloc[0]
    st.subheader("🔄 隨機複習")
    st.write(f"**中文：** {test_item['Chinese']}")
    if st.button("查看答案"):
        st.success(f"**English:** {test_item['English']}")
        st.info(f"**Note:** {test_item['Note']}")

# --- 3. 庫存顯示 ---
st.divider()
st.subheader("📚 複習庫存清單")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.warning("目前庫存為空，請在 Google Sheets 填入資料並發布。")
