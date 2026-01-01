import streamlit as st
import pandas as pd
import random

# --- 1. 頁面配置 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide")

# --- 2. 史努比 × 瑪利歐 視覺注入 (奶油黃、黑粗框、字體大) ---
st.markdown("""
   <style>
    /* 換一個更有手繪感的字體 */
    @import url('fonts.googleapis.com');
    
    html, body, [class*="css"] {
        font-family: 'Architects Daughter', cursive;
        background-color: #FFFFFF; /* 改為純白，像漫畫紙 */
    }

    /* 讓邊框更像手繪線條（不規則感） */
    .stAlert, [data-testid="stSidebar"], .stDataFrame {
        border: 4px solid #000000 !important;
        border-radius: 2px !important; /* 減少圓角，改為硬邊框 */
        box-shadow: 8px 8px 0px #000000; /* 更厚重的陰影 */
    }
    </style>
    """, unsafe_allow_html=True)

# 在標題下方加入一張史努比插圖
st.sidebar.image("media.giphy.com", width=150)

# --- 3. 多分頁資料讀取邏輯 ---
# 這是您的 Google Sheets ID
SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ" 
GIDS = {
    "📖 經節": "1454083804",
    "🔤 單字": "1400979824",
    "🔗 片語": "1657258260"
}

def fetch_data(gid):
    # 使用您的專屬 ID 進行讀取
    url = f"docs.google.com{gid}"
    try:
        data = pd.read_csv(url)
        data.columns = [str(c).strip() for c in data.columns]
        return data.dropna(how='all', axis=0)
    except:
        return pd.DataFrame()

# --- 4. 側邊欄：進度管理與類別切換 ---
if 'exp' not in st.session_state: st.session_state.exp = 0

with st.sidebar:
    st.title("🐾 Snoopy's Desk")
    selected_tab = st.radio("🐾 選擇學習類別", list(GIDS.keys()))
    st.divider()
    # 瑪利歐過關遊戲進度
    st.subheader(f"🏆 史努比過關進度")
    lvl_progress = (st.session_state.exp % 5) / 5
    st.progress(lvl_progress)
    st.write(f"已收集骨頭: {st.session_state.exp % 5} / 5")
    if st.session_state.exp > 0 and st.session_state.exp % 5 == 0:
        st.balloons()
        st.success("🎉 過關了！史努比跳過屋頂了！")
    st.divider()
    search_query = st.text_input("🔍 搜尋關鍵字...")

# --- 5. 主介面顯示 ---
st.markdown(f'<h1 style="text-align:center;">🐶 {selected_tab} 智慧庫</h1>', unsafe_allow_html=True)
df = fetch_data(GIDS[selected_tab])

if not df.empty:
    # 搜尋過濾邏輯
    if search_query:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

    cmd = st.text_input(f"🐾 輸入 R 開始隨機複習 ({selected_tab}):").strip().upper()

    if cmd == "R":
        item = df.sample(1).iloc[0]
        st.divider()
        
        if "經節" in selected_tab:
            st.markdown(f"📍 **{item['Reference']}**")
            st.markdown(f'<div class="verse-text">{item["Chinese"]}</div>', unsafe_allow_html=True)
            if st.button("📖 顯示英文與多語答案"):
                st.success(f"**English:** {item['English']}")
                st.info(f"🔑 **Key:** {item['Key word']} | 📝 **Grammar:** {item['Grammar']}")
                cols = st.columns(3)
                cols[0].write(f"🇯🇵 {item['Japanese']}")
                cols[1].write(f"🇰🇷 {item['Korean']}")
                cols[2].write(f"🇹🇭 {item['Thai']}")
                st.session_state.exp += 1

        elif "單字" in selected_tab:
            st.subheader(f"❓ 這個單字什麼意思？ → **{item['Vocab']}**")
            st.caption(f"語言標註: {item['Language']}")
            if st.button("🔍 顯示定義與例句"):
                st.success(f"**定義:** {item['Definition']}")
                st.write(f"**同意語:** {item['Synonym']}")
                st.write(f"**例句:** {item['Example']}")
                st.caption(f"**例句翻譯:** {item['Example_CN']}")
                st.session_state.exp += 1

        elif "片語" in selected_tab:
            st.subheader(f"❓ 這個片語什麼意思？ → **{item['Phrase']}**")
            st.caption(f"語言標註: {item['Language']}")
            if st.button("🔍 顯示詳解"):
                st.success(f"**定義:** {item['Definition']}")
                st.write(f"**例句:** {item['Example']}")
                st.session_state.exp += 1

    # 庫存表格
    with st.expander("📚 查看所有庫存資料"):
        st.dataframe(df, use_container_width=True)
else:
    st.warning(f"目前 {selected_tab} 庫存為空，或 Google Sheets 尚未發布。")

# --- 6. AI 大量輸入介面 (Mass Import UI) ---
st.divider()
with st.expander("📥 大量輸入解析介面 (AI Mass Parser)"):
    st.write("請將文章或影片字幕貼在下面，系統將輔助您分類。")
    raw_text = st.text_area("在此輸入大量內容...", height=150)
    if st.button("🪄 執行結構化分析"):
        st.info("分析中... 請手動將結果貼回 Google Sheets 對應分頁。")
        # 此處為預覽邏輯
        st.code(f"Category: {selected_tab}\nContent: {raw_text[:50]}...")
