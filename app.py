# ===================================================================
# 0. 套件與全域設定（保留你原封不動的區塊 1~5）
# ===================================================================
import streamlit as st
import datetime as dt
import json   # run_analysis 裡的 json.load 需要
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

# ---------- 背後函式：強化版 ----------
def run_analysis(text: str) -> dict:
    try:
        with open("temp_input.txt", "w", encoding="utf-8") as f:
            f.write(text.strip())
        result = subprocess.run(
            [sys.executable, "analyze_to_excel.py", "--file", "temp_input.txt"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        with open("temp_result.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        for tmp in ["temp_input.txt", "temp_result.json"]:
            if os.path.exists(tmp):
                os.remove(tmp)
        return data
    except subprocess.TimeoutExpired:
        st.error("分析超時（30秒），請檢查輸入內容")
        raise
    except FileNotFoundError:
        st.error("找不到 analyze_to_excel.py 腳本")
        raise
    except Exception as e:
        st.error(f"分析過程錯誤：{str(e)}")
        raise

def to_excel(result: dict) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        for sheet, key in [("Words", "words"), ("Phrases", "phrases"), ("Grammar", "grammar")]:
            if key in result and result[key]:
                pd.DataFrame(result[key]).to_excel(writer, sheet_name=sheet, index=False)
        # 統計頁
        stats = pd.DataFrame({
            "項目": ["總字彙數", "總片語數", "文法點數", "分析日期"],
            "數值": [
                len(result.get("words", [])),
                len(result.get("phrases", [])),
                len(result.get("grammar", [])),
                dt.date.today().strftime("%Y-%m-%d")
            ]
        })
        stats.to_excel(writer, sheet_name="統計", index=False)
    buffer.seek(0)
    return buffer.getvalue()
# ===================================================================
# 1. TAB 1：書桌（你原來的內容，完全沒動）
# ===================================================================
with tabs[0]:
    col_content, col_m1 = st.columns([0.65, 0.35])
    with col_content:
        st.info("**Becoming** / 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 🇹🇭 เหมาะสม | 🇨🇳 相稱")
        st.info("**Still less** / 🇯🇵 まして | 🇰🇷 하물며 | 🇹🇭 ยิ่งกว่านั้น | 🇨🇳 何況")
        st.success("""
            🌟 **Pro 17:07** Fine speech is not becoming to a fool; still less is false speech to a prince.   
            🇯🇵 すぐれた言葉は愚か者にはふさわしくない。偽りの言葉は君主にはなおさらふさわしくない。   
            🇨🇳 愚頑人說美言本不相稱，何況君王說謊話呢？
            """, icon="📖")
    with col_m1:
        st.markdown(f"""
            <div style="display: flex; flex-direction: column; justify-content: space-between; height: 100%; min-height: 250px; text-align: center;">
                <div style="flex-grow: 1; display: flex; align-items: center; justify-content: center;">
                    <img src="{IMG_URLS['M1']}" style="width: 200px; margin-bottom: 10px;">
                </div>
                <div class="grammar-box-container" style="margin-top: auto;">
                    <p style="margin:2px 0; font-size: 14px; font-weight: bold; color: #333;">時態: 現在簡單式</p>
                    <p style="margin:2px 0; font-size: 14px; font-weight: bold; color: #333;">核心片語:</p>
                    <ul style="margin:0; padding-left:18px; font-size: 13px; line-height: 1.4; color: #555;">
                        <li>Fine speech (優美言辭)</li>
                        <li>Becoming to (相稱)</li>
                        <li>Still less (何況)</li>
                        <li>False speech (虛假言辭)</li>
                    </ul>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### ✍️ 文法運用例句")
    cl1, cl2 = st.columns(2)
    with cl1:
        st.markdown("**Ex 1:** *Casual attire is not becoming to a CEO; still less is unprofessional language.* <p class='small-font'>便服對執行長不相稱；更不用說不專業的言語了。</p>", unsafe_allow_html=True)
    with cl2:
        st.markdown("**Ex 2:** *Wealth is not becoming to a man without virtue; still less is power.* <p class='small-font'>財富對於無德之人不相稱；更不用說權力了。</p>", unsafe_allow_html=True)

if 'cal_key'  not in st.session_state: st.session_state.cal_key = 0
# ---------- 全域常數 ----------
EMOJI_LIST = ["🐾","🧸","🐶","🕌","🥐","💭","🍔","🍖","🍒","🍓","🥰","💖","🌸","💬","✨","🥕","🌟","🍀","🎀","🎉"]

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

# ===================================================================
# 3. TAB 3 & 4：挑戰 / 資料庫（你原來的內容，完全沒動）
# ===================================================================
with tabs[2]:
    col_challenge, col_deco = st.columns([0.7, 0.3])
    with col_challenge:
        st.subheader("📝 翻譯挑戰")
        st.write("題目 1: 愚頑人說美言本不相稱...")
        st.text_input("請輸入英文翻譯", key="ans_1_final", placeholder="Type your translation here...")
    with col_deco:
        st.image(IMG_URLS.get("B"), width=150, caption="Keep Going!")

# ===================================================================
# TAB4：AI 控制台（完整替換版）
# ===================================================================
with tabs[3]:
    import json   # 別忘了補這一行
    import subprocess, sys, os, datetime as dt, pandas as pd, io

    st.title("📚 多語聖經控制台")
    st.markdown("① 貼經文 → ② 一鍵分析 → ③ 下載 Excel → ④ 離線使用")

    # ---------- ① 貼經文 ----------
    with st.expander("① 貼經文（中文 or 英文講稿）", expanded=True):
        # 快速測試按鈕
        if st.button("🧪 快速測試（載入範例）"):
            st.session_state.input_text = "馬太福音 5:3 虛心的人有福了，因為天國是他們的。"

        input_text = st.text_area("經文/講稿", height=200, key="input_text")

        # 進階設定
        with st.expander("⚙️ 進階設定"):
            c_opt1, c_opt2 = st.columns(2)
            with c_opt1:
                st.selectbox("分析深度", ["標準", "詳細", "簡易"], key="analysis_depth")
            with c_opt2:
                st.selectbox("輸出語言", ["中英日韓泰", "中英", "中日"], key="output_langs")

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
                        save_analysis_result(result, input_text)  # 存歷史
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

    # ---------- ② 輸入範例提示 ----------
    with st.expander("📋 輸入範例"):
        st.markdown("**中文經文範例：**")
        st.code("馬太福音 5:3 虛心的人有福了，因為天國是他們的。", language="text")
        st.markdown("**英文講稿範例：**")
        st.code("Today we will explore the meaning of true wisdom...", language="text")

    # ---------- ③ 分析歷史 ----------
    if st.checkbox("顯示分析歷史（最近10筆）"):
        for item in st.session_state.get("analysis_history", []):
            st.caption(item["date"])
            st.code(item["input_preview"])

    # ---------- ④ 控制台連結（僅兩顆） ----------
    st.markdown("---")
    st.subheader("🔗 聖經連結控制台")
    cl3, cl4 = st.columns(2)
    with cl3:
        st.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb")
    with cl4:
        st.link_button("THSV11", "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")

# ---------- Session 初始化（最上方） ----------
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []

def save_analysis_result(result, input_text):
    # 存一筆
    st.session_state.analysis_history.append({
        "date": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "input_preview": input_text[:50] + "..." if len(input_text) > 50 else input_text,
        "result": result
    })
    # 只留最近 10 筆
    if len(st.session_state.analysis_history) > 10:
        st.session_state.analysis_history.pop(0)
