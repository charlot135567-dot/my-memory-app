import streamlit as st
import random
import time
# --- 1. 頁面配置 (2026 極簡可愛風設定) ---
st.set_page_config(
    page_title="Memory Bible 2026",
    layout="wide",
    page_icon="📖"
)
# --- 2. 注入 CSS：極簡明亮可愛風 (2026 UI 趨勢) ---
st.markdown("""
    <style>
    /* 主背景與字體 */
    .stApp { background-color: #FDFDFD; }
    /* 自定義卡片風格 (用於經文、筆記、待辦) */
    .custom-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 25px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-left: 8px solid #FFD1DC; /* 粉嫩邊框 */
    }  
    /* 可愛風按鈕 */
    .stButton>button {
        border-radius: 50px !important;
        border: none !important;
        background-color: #FFD1DC !important;
        color: #555 !important;
        font-weight: bold !important;
        padding: 0.5rem 2rem !important;
        transition: 0.3s !important;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        background-color: #FFB7C5 !important;
    }
    /* 輸入框美化 */
    .stTextArea textarea, .stTextInput input {
        border-radius: 20px !important;
        border: 2px solid #F0F2F6 !important;
    }
    </style>
    """, unsafe_allow_html=True)
# --- 3. 初始化 Session State ---
if 'my_notes' not in st.session_state:
    st.session_state.my_notes = []
if 'todo_list' not in st.session_state:
    st.session_state.todo_list = []
if 'current_bible' not in st.session_state:
    # 預設 5 國語言經文資料 JSON 結構
    st.session_state.current_bible = {
        "ref": "Psalm 23:1",
        "translations": {
            "CN": "耶和華是我的牧者，我必不致缺乏。",
            "EN": "The Lord is my shepherd; I shall not want.",
            "KO": "여호와는 나의 목자시니 내게 부족함이 없으리로다.",
            "JA": "主は私の羊飼い。私は、何も欠けることがありません。",
            "TH": "พระยาห์เวห์ทรงเลี้ยงดูข้าพเจ้าดั่งเลี้ยงแกะ ข้าพเจ้าจะไม่ขัดสน"
        }
    }
# --- 4. 功能函數 ---
def get_new_verse():
    # 模擬 2026 定時更新經文 (這部分可依需求擴充 JSON 資料庫)
    verses = [
        {"ref": "John 3:16", "translations": {"CN": "神愛世人...", "EN": "For God so loved...", "KO": "하나님이 세상을...", "JA": "神は、実に...", "TH": "เพราะว่าพระเจ้าทรงรักโลก..."}},
        {"ref": "Matthew 5:3", "translations": {"CN": "虛心的人有福了...", "EN": "Blessed are the poor...", "KO": "심령이 가난한 자는...", "JA": "心の貧しい者は...", "TH": "คนที่ยากจนด้านจิตวิญญาณ..."}}
    ]
    st.session_state.current_bible = random.choice(verses)
# --- 5. APP 介面佈局 ---
st.title("📖 Memory Bible 2026")
st.write("在 2026 年，每天給予自己一點屬靈的可愛能量 ✨")
# --- 區塊 A: 5 國語言聖經顯示 ---
st.markdown("### 🕊️ 每日應許")
with st.container():
    bible = st.session_state.current_bible
    content = f"""
    <div class="custom-card">
        <h4 style='color: #AEC6CF;'>{bible['ref']}</h4>
        <p><b>🇨🇳 中文：</b>{bible['translations']['CN']}</p>
        <p><b>🇺🇸 English：</b>{bible['translations']['EN']}</p>
        <p><b>🇰🇷 한국어：</b>{bible['translations']['KO']}</p>
        <p><b>🇯🇵 日本語：</b>{bible['translations']['JA']}</p>
        <p><b>🇹🇭 ไทย：</b>{bible['translations']['TH']}</p>
    </div>
    """
    st.markdown(content, unsafe_allow_html=True)
    if st.button("換一則應許"):
        get_new_verse()
st.divider()
# --- 區塊 B: 筆記與待辦 (分欄設計) ---
col1, col2 = st.columns(2)
with col1:
    st.markdown("### 📓 靈修筆記")
    note_text = st.text_area("寫下感動...", height=150, placeholder="今天上帝對我說了什麼？")
    if st.button("收藏筆記"):
        if note_text:
            st.session_state.my_notes.append(note_text)
            st.toast("已存入可愛小本本！ 💖")
    # 顯示歷史筆記
    for n in reversed(st.session_state.my_notes[-3:]): # 顯示最後三則
        st.info(n)
with col2:
    st.markdown("### ✅ 今日待辦")
    with st.form("todo_form", clear_on_submit=True):
        new_todo = st.text_input("新增任務", placeholder="例如：讀經 15 分鐘")
        submitted = st.form_submit_button("添加")
        if submitted and new_todo:
            st.session_state.todo_list.append(new_todo)
    # 顯示待辦清單
    for i, task in enumerate(st.session_state.todo_list):
        st.markdown(f"<div style='padding:5px; border-bottom:1px solid #eee;'>📍 {task}</div>", unsafe_allow_html=True)
# 頁尾
st.caption(f"© 2026 Memory Bible App | 當前時間: {time.strftime('%Y-%m-%d %H:%M')}")
