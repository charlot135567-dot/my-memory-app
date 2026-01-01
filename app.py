import streamlit as st
import pandas as pd
import random

# --- 1. 頁面配置 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide")

# --- 2. 查理布朗彩色視覺注入 ---
st.markdown("""
    <style>
    @import url('fonts.googleapis.com');

    /* 全局背景：查理布朗亮黃 */
    html, body, [class*="css"] {
        font-family: 'Comic Neue', cursive;
        background-color: #FFD200; 
    }

    /* 頂部標題：鋸齒波浪文字 */
    .main-title {
        font-family: 'Gloria Hallelujah', cursive;
        color: #000000;
        text-align: center;
        background: repeating-linear-gradient(
            45deg,
            #FFD200,
            #FFD200 10px,
            #000000 10px,
            #000000 20px
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 50px;
        font-weight: bold;
    }

    /* 側邊欄：狗屋紅 */
    [data-testid="stSidebar"] {
        background-color: #E22126 !important;
        border-right: 5px solid #000000 !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* 對話框：硬邊框 + 漫畫陰影 */
    .stAlert, .stDataFrame, .stExpander, div[data-testid="stExpander"] {
        border: 4px solid #000000 !important;
        border-radius: 0px !important;
        background-color: #FFFFFF !important;
        box-shadow: 10px 10px 0px #000000;
    }

    /* 按鈕：亮藍色 */
    div.stButton > button:first-child {
        background-color: #00A2E8; 
        color: #FFFFFF;
        border: 4px solid #000000;
        border-radius: 0px;
        font-size: 20px;
        box-shadow: 5px 5px 0px #000000;
    }
    div.stButton > button:hover {
        background-color: #FFFFFF;
        color: #00A2E8;
    }

    .verse-text {
        font-size: 28px;
        font-weight: bold;
        color: #000000;
        background-color: #FFFFFF;
        border-left: 10px solid #000000;
        padding: 15px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title">GOOD GRIEF! MEMORY LOGIC</h1>', unsafe_allow_html=True)

# --- 3. 多分頁資料讀取邏輯 ---
SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ" 
GIDS = {
    "📖 經節": "1454083804",
    "🔤 單字": "1400979824",
    "🔗 片語": "1657258260"
}

def fetch_data(gid):
    # 【最終正確版網址】請直接複製這一行
    url = f"docs.google.com{SHEET_ID}/export?format=csv&gid={gid}"
    try:
        data = pd.read_csv(url)
        data.columns = [str(c).strip() for c in data.columns]
        return data.dropna(how='all', axis=0)
    except Exception as e:
        return pd.DataFrame()

# --- 4. 側邊欄控制 ---
if 'exp' not in st.session_state: st.session_state.exp = 0

with st.sidebar:
    st.markdown("### 🐾 Snoopy's Desk")
    selected_tab = st.radio("🐾 選擇類別", list(GIDS.keys()))
    st.divider()
    st.subheader(f"🏆 進度: {st.session_state.exp % 5} / 5")
    st.progress((st.session_state.exp % 5) / 5)
    if st.session_state.exp > 0 and st.session_state.exp % 5 == 0:
        st.balloons()
        st.success("過關了！史努比拿到骨頭了！")
    st.divider()
    search_query = st.text_input("🔍 搜尋關鍵字...")

# --- 5. 主內容區 ---
st.markdown(f'<h2 style="color:black;">🐶 {selected_tab} 智慧庫</h2>', unsafe_allow_html=True)
df = fetch_data(GIDS[selected_tab])

if not df.empty:
    if search_query:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

    cmd = st.text_input(f"🐾 輸入 R 開始複習 ({selected_tab}):").strip().upper()

    if cmd == "R":
        item = df.sample(1).iloc[0]
        st.divider()
        
        if "經節" in selected_tab:
            st.markdown(f"📍 **{item['Reference']}**")
            st.markdown(f'<div class="verse-text">{item["Chinese"]}</div>', unsafe_allow_html=True)
            if st.button("📖 顯示翻譯與多語"):
                st.success(f"**English:** {item['English']}")
                cols = st.columns(3)
                cols[0].write(f"🇯🇵 {item['Japanese']}")
                cols[1].write(f"🇰🇷 {item['Korean']}")
                cols[2].write(f"🇹🇭 {item['Thai']}")
                st.session_state.exp += 1

        elif "單字" in selected_tab:
            st.subheader(f"❓ 這個單字什麼意思？ → **{item['Vocab']}**")
            if st.button("🔍 顯示詳解"):
                st.success(f"**定義:** {item['Definition']}")
                st.write(f"**例句:** {item['Example']}")
                st.session_state.exp += 1

        elif "片語" in selected_tab:
            st.subheader(f"❓ 這個片語什麼意思？ → **{item['Phrase']}**")
            if st.button("🔍 顯示詳解"):
                st.success(f"**定義:** {item['Definition']}")
                st.write(f"**例句:** {item['Example']}")
                st.session_state.exp += 1

    with st.expander("📚 查看所有庫存"):
        st.dataframe(df, use_container_width=True)
else:
    st.warning("目前資料庫為空，請在 Sheets 填入資料並確認已『發布到網路』。")
