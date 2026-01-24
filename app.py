# ===================================================================
# 0. 套件與全域設定（保留你原封不動的區塊 1~5）
# ===================================================================
import streamlit as st
import datetime as dt
try:
    from streamlit_calendar import calendar
    CALENDAR_OK = True
except ModuleNotFoundError:
    CALENDAR_OK = False
    calendar = None

st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# ---------- Session 初始 ----------
if 'events'   not in st.session_state: st.session_state.events   = []
if 'notes'    not in st.session_state: st.session_state.notes    = {}
if 'todo'     not in st.session_state: st.session_state.todo     = {}
if 'custom_emojis' not in st.session_state: st.session_state.custom_emojis = ["🐾", "🐰", "🥰", "✨", "🥕", "🌟"]
if 'sel_date' not in st.session_state: st.session_state.sel_date = str(dt.date.today())
if 'modal'    not in st.session_state: st.session_state.modal    = None   # 新增：控制彈窗

# ---------- 你原有的 CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap ');
.cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
.small-font { font-size: 13px; color: #555555; margin-top: 5px !important; }
.grammar-box-container {
    background-color: #f8f9fa; border-radius: 8px; padding: 12px; 
    border-left: 5px solid #FF8C00; text-align: left; margin-top: 0px;
}
/* 日曆格子點擊回饋 */
.fc-daygrid-day-frame:hover {background-color: #FFF3CD !important; cursor: pointer; transform: scale(1.03); transition: .2s}
.fc-daygrid-day-frame:active {transform: scale(0.98); background-color: #FFE69C !important}
</style>
""", unsafe_allow_html=True)

# ---------- IMG & Sidebar（原樣） ----------
IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg ",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg ",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg ",
    "M1": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro1.jpg ",
    "M2": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro2.jpg ",
    "M3": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro3.jpg ",
    "M4": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro4.jpg "
}
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다</p>', unsafe_allow_html=True)
    st.image(IMG_URLS["M3"], width=250)
    st.divider()
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/ ", use_container_width=True)

tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# ===================================================================
# 精簡版：只留 TAB1、TAB3、TAB4（零日曆、零錯誤）
# ===================================================================
import streamlit as st
import datetime as dt

st.set_page_config(layout="wide", page_title="Language Learning App")

# ---------- 簡單 Session ----------
if 'sel_date' not in st.session_state: st.session_state.sel_date = str(dt.date.today())

# ---------- 左側 Sidebar：控制台連結（手機乾淨） ----------
with st.sidebar:
    st.markdown("### 🔗 控制台")
    st.link_button("ESV Bible", "https://www.bible.com/zh-TW/bible/59/GEN.1.ESV")
    st.link_button("THSV11", "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")
    st.divider()
    st.caption("AI 分析請在『主畫面 → TAB4』操作")

# ---------- TAB1：語言書桌（你原樣保留） ----------
tabs = st.tabs(["🏠 書桌", "✍️ 挑戰", "📊 控制台"])

with tabs[0]:
    st.subheader("📖 每日靈修英語")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**Becoming** / 相稱")
        st.success("Pro 17:07 Fine speech is not becoming to a fool; still less is false speech to a prince.")
    with col2:
        st.markdown("**核心片語：**")
        st.markdown("- Fine speech (優美言辭)")
        st.markdown("- Becoming to (相稱)")
        st.markdown("- Still less (何況)")

# ===================================================================
# TAB 2：14 天滑動金句庫（純按鈕，零日曆）
# ===================================================================
with tabs[1]:

    import datetime as dt

    # ---------- 參數 ----------
    DAYS_KEEP = 14  # 只留 14 天
    today = dt.date.today()

    # ---------- Session 初始化 ----------
    if "sentences" not in st.session_state:
        # 預設 14 天空陣列，避免 KeyError
        st.session_state.sentences = {str(today - dt.timedelta(days=i)): "" for i in range(DAYS_KEEP)}

    # ---------- 每日推進：刪最舊 → 留最新 ----------
    dates_keep = [today - dt.timedelta(days=i) for i in range(DAYS_KEEP)]
    # 只保留最近 14 天的 key
    for d in list(st.session_state.sentences.keys()):
        if dt.datetime.strptime(d, "%Y-%m-%d").date() not in dates_keep:
            del st.session_state.sentences[d]

    # ---------- 摺疊：新增今日金句 ----------
    with st.expander("✨ 新增今日金句", expanded=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            new_sentence = st.text_input("金句（中英並列）", key="new_sentence")
        with col2:
            st.write("")
            if st.button("儲存", type="primary"):
                if new_sentence:
                    st.session_state.sentences[str(today)] = new_sentence
                    st.success("已儲存！")
                else:
                    st.error("請輸入金句")

    # ---------- 14 天條列（最新在上） ----------
    st.subheader("📅 最近 14 天金句")
    for d in sorted(dates_keep, reverse=True):
        date_str = str(d)
        sentence = st.session_state.sentences.get(date_str, "")
        col_emoji, col_txt = st.columns([1, 9])
        with col_emoji:
            st.caption(f"{d.strftime('%m/%d')}")
        with col_txt:
            if sentence:
                st.info(sentence)
            else:
                st.caption("（尚無金句）")

    # ---------- 一鍵匯出（可複製） ----------
    if st.button("📋 匯出 14 天金句"):
        export = "\n".join([f"{d.strftime('%m/%d')}  {st.session_sentences.get(str(d), '')}" for d in sorted(dates_keep, reverse=True)])
        st.code(export, language="text")

# ---------- TAB3：語言挑戰 ----------
with tabs[1]:
    st.subheader("✍️ 語言挑戰")
    st.write("題目 1: 愚頑人說美言本不相稱...")
    ans = st.text_input("請輸入英文翻譯", key="ans_1", placeholder="Type your translation here...")
    if st.button("提交", key="submit_ans"):
        st.success("已收到！繼續加油～")

# ---------- TAB4：AI 控制台（只有貼經文 + 下載） ----------
with tabs[2]:
    st.title("📊 AI 多語分析控制台")
    st.markdown("① 貼經文 → ② AI 分析 → ③ 下載 Excel → ④ 離線使用")

    with st.expander("① 貼經文（中文 or 英文講稿）", expanded=True):
        input_text = st.text_area("經文/講稿", height=200, key="input_text")
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("🤖 AI 分析", type="primary"):
                if not input_text:
                    st.error("請先貼經文")
                    st.stop()
                with st.spinner("AI 分析中，約 10 秒…"):
                    try:
                        result = run_analysis(input_text)
                        st.session_state["analysis"] = result
                        st.success("分析完成！")
                    except Exception as e:
                        st.error(f"分析失敗：{e}")
        with c2:
            if st.button("📥 下載 Excel"):
                if "analysis" not in st.session_state:
                    st.error("請先按『AI 分析』")
                    st.stop()
                excel_bytes = to_excel(st.session_state["analysis"])
                st.download_button(
                    label="📊 下載 Excel",
                    data=excel_bytes,
                    file_name=f"{dt.date.today()}-analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    with st.expander("② 貼上 Excel → 存進資料庫", expanded=True):
        paste_text = st.text_area("把 Excel 內容全選複製→貼上", height=300, key="paste_text")
        if st.button("💾 儲存至資料庫"):
            if not paste_text:
                st.error("請先貼上 Excel 內容")
                st.stop()
            save_to_db(paste_text)
            st.success("已離線儲存！")

# ---------- 背後函式：你零維護 ----------
def run_analysis(text: str) -> dict:
    """呼叫外部 analyze_to_excel.py → 回傳結構化 dict"""
    with open("temp_input.txt", "w", encoding="utf-8") as f:
        f.write(text)
    subprocess.run([sys.executable, "analyze_to_excel.py", "--file", "temp_input.txt"], check=True)
    with open("temp_result.json", "r", encoding="utf-8") as f:
        return json.load(f)


def to_excel(result: dict) -> bytes:
    df_words = pd.DataFrame(result["words"])
    df_phrases = pd.DataFrame(result["phrases"])
    df_grammar = pd.DataFrame(result["grammar"])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_words.to_excel(writer, sheet_name='Words', index=False)
        df_phrases.to_excel(writer, sheet_name='Phrases', index=False)
        df_grammar.to_excel(writer, sheet_name='Grammar', index=False)
    buffer.seek(0)
    return buffer.getvalue()
