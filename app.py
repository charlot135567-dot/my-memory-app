import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Memory Logic 2025", page_icon="🛡️")

# --- 1. 資料庫串接 ---
SHEET_URL = "docs.google.com"

def load_data():
    try:
        csv_url = SHEET_URL.replace("/pubhtml", "/pub?output=csv")
        data = pd.read_csv(csv_url)
        data.columns = [str(c).strip() for c in data.columns]
        return data.dropna(how='all', axis=1)
    except Exception as e:
        st.error(f"資料讀取失敗: {e}")
        return pd.DataFrame()

df = load_data()

# --- 2. 核心介面 ---
st.title("🛡️ Memory Logic 2.0")

if 'English' not in df.columns or 'Chinese' not in df.columns:
    st.warning(f"⚠️ 標題不匹配！偵測到的欄位有: {list(df.columns)}")
else:
    # 側邊欄熱身
    st.sidebar.subheader("🔥 Daily Warm-up")
    warmup = df.sample(min(len(df), 3))
    for i, row in warmup.iterrows():
        st.sidebar.caption(f"{row['English']}")

    # 指令輸入
    cmd = st.text_input("輸入指令 (R: 複習):").strip().upper()

    if cmd == "R" and not df.empty:
        st.divider()
        # 隨機抽取一筆
        test_item = df.sample(1).iloc[0]
        st.subheader("🔄 隨機複習")
        st.write(f"**中文：** {test_item['Chinese']}")
        
        if st.button("查看答案"):
            st.success(f"**English:** {test_item['English']}")
            
            # --- 多國語言動態顯示區 ---
            col1, col2 = st.columns(2)
            with col1:
                if 'Japanese' in test_item and pd.notna(test_item['Japanese']):
                    st.warning(f"🇯🇵 **Japanese:**\n{test_item['Japanese']}")
            with col2:
                # 新增韓文顯示邏輯
                if 'Korean' in test_item and pd.notna(test_item['Korean']):
                    st.info(f"🇰🇷 **Korean:**\n{test_item['Korean']}")
            
            st.write(f"📌 **Note:** {test_item.get('Note', '')}")

    # 庫存顯示
    st.divider()
    st.subheader("📚 複習庫存清單")
    st.dataframe(df, use_container_width=True)
