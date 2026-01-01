import streamlit as st
import pandas as pd
import requests
import io
import os
import traceback

# Optional Google API imports done lazily when needed
# from google.oauth2.service_account import Credentials
# import gspread

# --- 0. 我是 GPT-5.2 ---
# 我是 GPT-5.2。

# --- 1. 頁面配置 ---
st.set_page_config(page_title="Memory Logic 2026", layout="wide")

# --- 2. CSS / 字體 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Comic+Neue&family=Gloria+Hallelujah&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Comic Neue', cursive;
        background-color: #FFD200;
    }

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
        padding: 20px;
    }

    [data-testid="stSidebar"] {
        background-color: #E22126 !important;
        border-right: 5px solid #000000 !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    .stAlert, .stDataFrame, div[data-testid="stExpander"] {
        border: 4px solid #000000 !important;
        border-radius: 0px !important;
        background-color: #FFFFFF !important;
        box-shadow: 10px 10px 0px #000000;
    }

    div.stButton > button:first-child {
        background-color: #00A2E8;
        color: #FFFFFF;
        border: 4px solid #000000;
        border-radius: 0px;
        font-size: 20px;
        box-shadow: 5px 5px 0px #000000;
        transition: 0.2s;
    }
    div.stButton > button:hover {
        background-color: #FFFFFF;
        color: #00A2E8;
        transform: translate(-2px, -2px);
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

# --- 3. Sheets 設定 ---
SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
GIDS = {
    "📖 經節": "1454083804",
    "🔤 單字": "1400979824",
    "🔗 片語": "1657258260"
}

# Optional: service account path or JSON from environment / st.secrets
# - On your deployment platform, set env var GSERVICE_ACCOUNT_FILE to path of JSON
# - Or put service account JSON as a string in st.secrets["gservice_account_json"]
GSERVICE_ACCOUNT_FILE = os.getenv("GSERVICE_ACCOUNT_FILE", None)

# --- 4. fetch_data with robust error handling and fallback ---
@st.cache_data(ttl=600)
def fetch_data(gid):
    """
    1) 嘗試透過 export?format=csv 取得
    2) 若失敗，嘗試 gviz/tq 出 csv
    3) 若仍失敗且有 Service Account，使用 Google Sheets API 讀取 worksheet by sheetId
    4) 捕捉並回傳 tuple: (df, diagnostics) 但為簡單使用這裡只回傳 df; diagnostics 用 st.session_state 顯示
    """
    diagnostics = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MemoryLogic/1.0)"}
    timeout = 15

    def try_requests(url):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
        except Exception as e:
            diagnostics.append(f"requests exception for {url}: {e}")
            return None, None
        diagnostics.append(f"HTTP {r.status_code} for {url}")
        if r.status_code == 200:
            # Quick check: if response looks like CSV, try parse
            content = r.content
            # for text decode
            try:
                text = content.decode("utf-8")
            except Exception:
                try:
                    text = content.decode("latin1")
                except Exception as e:
                    diagnostics.append(f"decode error: {e}")
                    return None, None
            # Heuristic: must contain newline and comma in first 500 chars
            head = text[:1000]
            if ("\n" in head) and ("," in head or "\t" in head):
                try:
                    df = pd.read_csv(io.StringIO(text))
                    df.columns = [str(c).strip() for c in df.columns]
                    return df, diagnostics
                except Exception as e:
                    diagnostics.append(f"pandas.parse error for {url}: {e}")
                    diagnostics.append("response snippet:\n" + head[:1000])
                    return None, diagnostics
            else:
                diagnostics.append("Response does not look like CSV (might be HTML login page). Snippet:\n" + head[:500])
                return None, diagnostics
        else:
            diagnostics.append(f"Non-200 response: {r.status_code}")
            return None, diagnostics

    # 1) export CSV URL
    url_export = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    df, diags = try_requests(url_export)
    if df is not None:
        st.session_state._last_diag = diags
        return df
    # collect diagnostics
    if diags:
        diagnostics.extend(diags)

    # 2) gviz fallback
    url_gviz = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={gid}"
    df, diags = try_requests(url_gviz)
    if df is not None:
        st.session_state._last_diag = diagnostics + (diags or [])
        return df
    if diags:
        diagnostics.extend(diags)

    # 3) Service Account fallback (if configured)
    # Look for JSON in env var path or in st.secrets
    sa_path = GSERVICE_ACCOUNT_FILE
    sa_json_dict = None
    # check st.secrets
    try:
        if "gservice_account_json" in st.secrets:
            sa_json_dict = st.secrets["gservice_account_json"]
    except Exception:
        # st.secrets may not exist / no access in local, ignore
        pass

    if sa_path or sa_json_dict:
        diagnostics.append("Attempting Google Sheets API via service account.")
        try:
            # Lazy import
            from google.oauth2.service_account import Credentials
            import gspread

            scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
            if sa_path:
                creds = Credentials.from_service_account_file(sa_path, scopes=scopes)
            else:
                # st.secrets contains JSON dict or JSON string
                if isinstance(sa_json_dict, str):
                    import json
                    info = json.loads(sa_json_dict)
                else:
                    info = sa_json_dict
                creds = Credentials.from_service_account_info(info, scopes=scopes)

            gc = gspread.authorize(creds)
            sh = gc.open_by_key(SHEET_ID)
            # find worksheet with matching sheetId
            target_ws = None
            for ws in sh.worksheets():
                props = ws._properties
                if str(props.get("sheetId")) == str(gid):
                    target_ws = ws
                    break
            if target_ws is None:
                diagnostics.append("Service account: cannot find worksheet with sheetId matching gid.")
            else:
                records = target_ws.get_all_records()
                df = pd.DataFrame(records)
                df.columns = [str(c).strip() for c in df.columns]
                st.session_state._last_diag = diagnostics
                return df
        except Exception as e:
            diagnostics.append("Service account read error: " + repr(e))
            diagnostics.append(traceback.format_exc())

    # if everything fails, store diagnostics and return empty
    st.session_state._last_diag = diagnostics
    return pd.DataFrame()

# --- 5. 初始化 session_state ---
if 'exp' not in st.session_state:
    st.session_state.exp = 0
if 'current_item' not in st.session_state:
    st.session_state.current_item = None
if 'revealed' not in st.session_state:
    st.session_state.revealed = False
# store last diagnostics (populated by fetch_data)
if '_last_diag' not in st.session_state:
    st.session_state._last_diag = []

# --- 6. 側邊欄與控制 ---
with st.sidebar:
    st.markdown("### 🐾 Snoopy's Desk")
    selected_tab = st.radio(
        "🐾 選擇類別",
        list(GIDS.keys()),
        on_change=lambda: st.session_state.update({"current_item": None, "revealed": False})
    )
    st.divider()
    progress = st.session_state.exp % 5
    st.subheader(f"🏆 進度: {progress} / 5")
    st.progress(progress / 5)
    if st.session_state.exp > 0 and progress == 0:
        st.balloons()
        st.success("過關了！史努比拿到骨頭了！")
    st.divider()
    search_query = st.text_input("🔍 搜尋關鍵字...")
    st.divider()
    st.markdown("#### Debug / 設定 (選用)")
    st.markdown("- 若需要使用 Google Service Account 存取私有試算表，請將 JSON 路徑設為環境變數 GSERVICE_ACCOUNT_FILE，或將 JSON 放入 Streamlit secrets key `gservice_account_json`。")

# --- 7. 主內容區 ---
st.markdown(f'<h2 style="color:black;">🐶 {selected_tab} 智慧庫</h2>', unsafe_allow_html=True)

# 取得資料
df = fetch_data(GIDS[selected_tab])

# 顯示診斷資訊（若有）
if st.session_state._last_diag:
    with st.expander("🔧 連線診斷資訊（debug）", expanded=False):
        for d in st.session_state._last_diag:
            st.text(d)

if df.empty:
    st.warning("資料庫讀取中或庫存為空。可能原因：\n"
               "- 試算表未對外開放（請設定為「任何擁有連結的人皆可檢視」）\n"
               "- 輸入的 SHEET_ID 或 gid 錯誤\n"
               "- 網路或 HTTP 錯誤（請查看診斷資訊）\n"
               "若需要存取私有試算表，請設定 Service Account（見側邊欄說明）。")
else:
    # 搜尋過濾
    if search_query:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

    # 抽題按鈕
    if st.button(f"🎲 隨機抽取一筆 {selected_tab}"):
        st.session_state.current_item = df.sample(1).iloc[0].to_dict()
        st.session_state.revealed = False

    # 顯示抽到的題目
    if st.session_state.current_item:
        item = st.session_state.current_item
        st.divider()

        if "經節" in selected_tab:
            st.markdown(f"📍 **{item.get('Reference', 'N/A')}**")
            st.markdown(f'<div class="verse-text">{item.get("Chinese", "N/A")}</div>', unsafe_allow_html=True)

            if not st.session_state.revealed:
                if st.button("📖 顯示翻譯與多語"):
                    st.session_state.revealed = True
                    st.session_state.exp += 1
                    st.experimental_rerun()
            else:
                st.success(f"**English:** {item.get('English', 'N/A')}")
                cols = st.columns(3)
                cols[0].write(f"🇯🇵 {item.get('Japanese', 'N/A')}")
                cols[1].write(f"🇰🇷 {item.get('Korean', 'N/A')}")
                cols[2].write(f"🇹🇭 {item.get('Thai', 'N/A')}")

        elif "單字" in selected_tab:
            st.subheader(f"❓ 單字： **{item.get('Vocab', 'N/A')}**")
            if not st.session_state.revealed:
                if st.button("🔍 顯示詳解"):
                    st.session_state.revealed = True
                    st.session_state.exp += 1
                    st.experimental_rerun()
            else:
                st.success(f"**定義:** {item.get('Definition', 'N/A')}")
                st.info(f"**例句:** {item.get('Example', 'N/A')}")

        elif "片語" in selected_tab:
            st.subheader(f"❓ 片語： **{item.get('Phrase', 'N/A')}**")
            if not st.session_state.revealed:
                if st.button("🔍 顯示詳解"):
                    st.session_state.revealed = True
                    st.session_state.exp += 1
                    st.experimental_rerun()
            else:
                st.success(f"**定義:** {item.get('Definition', 'N/A')}")
                st.info(f"**例句:** {item.get('Example', 'N/A')}")

    # 資料預覽
    with st.expander("📚 查看所有庫存表格"):
        st.dataframe(df, use_container_width=True)
