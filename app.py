# ===================================================================
# 0. 套件 & 全域函式（一定放最頂）
# ===================================================================
import streamlit as st
import subprocess, sys, os, datetime as dt, pandas as pd, io, json

# ---------- 全域工具函式 ----------
def save_analysis_result(result, input_text):
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []
    st.session_state.analysis_history.append({
        "date": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "input_preview": input_text[:50] + "..." if len(input_text) > 50 else input_text,
        "result": result
    })
    if len(st.session_state.analysis_history) > 10:
        st.session_state.analysis_history.pop(0)

def to_excel(result: dict) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet, key in [("Words", "words"), ("Phrases", "phrases"), ("Grammar", "grammar")]:
            if key in result and result[key]:
                pd.DataFrame(result[key]).to_excel(writer, sheet_name=sheet, index=False)
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
# 1. 側邊欄（一次 4 連結，無重複）
# ===================================================================
with st.sidebar:
    st.divider()
    c1, c2 = st.columns(2)
    c1.link_button("✨ Google AI", "https://gemini.google.com/")
    c2.link_button("🤖 Kimi K2",   "https://kimi.moonshot.cn/")
    c3, c4 = st.columns(2)
    c3.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb")
    c4.link_button("THSV11",    "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")

# ===================================================================
# 2. 頁面配置 & Session 初值
# ===================================================================
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

if 'events'   not in st.session_state: st.session_state.events   = []
if 'notes'    not in st.session_state: st.session_state.notes    = {}
if 'todo'     not in st.session_state: st.session_state.todo     = {}
if 'custom_emojis' not in st.session_state: st.session_state.custom_emojis = ["🐾", "🐰", "🥰", "✨", "🥕", "🌟"]
if 'sel_date' not in st.session_state: st.session_state.sel_date = str(dt.date.today())
if 'modal'    not in st.session_state: st.session_state.modal    = None
if 'analysis_history' not in st.session_state: st.session_state.analysis_history = []

# ---------- CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
.cute-korean { font-family: 'Gamja Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
.small-font { font-size: 13px; color: #555555; margin-top: 5px !important; }
.grammar-box-container {
    background-color: #f8f9fa; border-radius: 8px; padding: 12px; 
    border-left: 5px solid #FF8C00; text-align: left; margin-top: 0px;
}
.fc-daygrid-day-frame:hover {background-color: #FFF3CD !important; cursor: pointer; transform: scale(1.03); transition: .2s}
.fc-daygrid-day-frame:active {transform: scale(0.98); background-color: #FFE69C !important}
</style>
""", unsafe_allow_html=True)

# ---------- 圖片 & 現成 TAB ----------
IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg",
    "M1": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro1.jpg",
    "M2": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro2.jpg",
    "M3": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro3.jpg",
    "M4": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro4.jpg"
}
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다</p>', unsafe_allow_html=True)
    st.image(IMG_URLS["M3"], width=250)
    st.divider()

tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# ===================================================================
# 3. TAB1 ─ 書桌（原內容，未動）
# ===================================================================
with tabs[0]:
    col_content, col_m1 = st.columns([0.65, 0.35])
    with col_content:
        st.info("**Becoming** / 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 🇹🇭 เหมาะสม | 🇨🇳 相稱")
        st.success("""
            🌟 **Pro 17:07** Fine speech is not becoming to a fool; still less is false speech to a prince.   
            🇯🇵 すぐれた言葉は愚か者にはふさわしくない。偽りの言葉は君主にはなおさらふさわしくない。   
            🇨🇳 愚頑人說美言本不相稱，何況君王說謊話呢？
            """, icon="📖")
    with col_m1:
        st.markdown(f"""
            <div style="display:flex;flex-direction:column;justify-content:space-between;height:100%;min-height:250px;text-align:center;">
                <div style="flex-grow:1;display:flex;align-items:center;justify-content:center;">
                    <img src="{IMG_URLS['M1']}" style="width:200px;margin-bottom:10px;">
                </div>
                <div class="grammar-box-container" style="margin-top:auto;">
                    <p style="margin:2px 0;font-size:14px;font-weight:bold;color:#333;">時態: 現在簡單式</p>
                    <p style="margin:2px 0;font-size:14px;font-weight:bold;color:#333;">核心片語:</p>
                    <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.4;color:#555;">
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

# ===================================================================
# 4. TAB2 ─ 14 天滑動金句庫（原碼，未動）
# ===================================================================
with tabs[1]:
    import datetime as dt
    DAYS_KEEP = 14
    today = dt.date.today()
    if "sentences" not in st.session_state:
        st.session_state.sentences = {str(today - dt.timedelta(days=i)): "" for i in range(DAYS_KEEP)}
    dates_keep = [today - dt.timedelta(days=i) for i in range(DAYS_KEEP)]
    for d in list(st.session_state.sentences.keys()):
        if dt.datetime.strptime(d, "%Y-%m-%d").date() not in dates_keep:
            del st.session_state.sentences[d]
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
    if st.button("📋 匯出 14 天金句"):
        export = "\n".join([f"{d.strftime('%m/%d')}  {st.session_state.sentences.get(str(d), '')}" for d in sorted(dates_keep, reverse=True)])
        st.code(export, language="text")

# ===================================================================
# 5. TAB3 ─ 挑戰（原碼，未動）
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
# 6. TAB4 ─ AI 控制台（不產 Excel，直接呈現）
# ===================================================================
with tabs[3]:
    st.title("📚 多語聖經控制台")
    st.markdown("① 貼經文 → ② 一鍵分析 → ③ 直接檢視 → ④ 離線使用")

# ---------- ① 貼經文 expander ----------
with st.expander("① 貼經文（中文 or 英文講稿）", expanded=True):
    if st.button("🧪 快速測試（載入範例）"):
        st.session_state.input_text = "馬太福音 5:3 虛心的人有福了，因為天國是他們的。"
    input_text = st.text_area("經文/講稿", height=200, key="input_text")

    # AI 分析按鈕（在 expander 內）
    if st.button("🤖 AI 分析", type="primary"):
        ...  # 原分析邏輯不變

# ② 顯示分析結果（拉出 expander，同層）
if st.button("📊 顯示分析結果"):
    if "analysis" not in st.session_state:
        st.error("請先按『AI 分析』")
        st.stop()
    data = st.session_state["analysis"]

    # Ref. 原文跳轉列
    st.session_state["ref_no"] = data.get("ref_no", "")
    st.session_state["ref_article"] = data.get("ref_article", "")
    st.markdown(f"**Ref. No.** `{st.session_state['ref_no']}`")
    col_jump, col_copy = st.columns(2)
    with col_jump:
        if st.button("📄 檢視原文"):
            st.session_state["show_article"] = True
    with col_copy:
        st.copy_button("複製 Ref.", st.session_state["ref_no"])

    if st.session_state.get("show_article", False):
        with st.expander("📘 中英精煉文章", expanded=True):
            st.markdown(st.session_state["ref_article"])

    # 表格呈現（滿寬）
    col_w, col_p, col_g = st.tabs(["單字", "片語", "文法"])
    with col_w:
        if data.get("words"):
            df = pd.DataFrame(data["words"])
            df.insert(0, "Ref.", data["ref_no"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("本次無單字分析")
    with col_p:
        if data.get("phrases"):
            df = pd.DataFrame(data["phrases"])
            df.insert(0, "Ref.", data["ref_no"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("本次無片語分析")
    with col_g:
        if data.get("grammar"):
            df = pd.DataFrame(data["grammar"])
            df.insert(0, "Ref.", data["ref_no"])
            st.table(df)
        else:
            st.info("本次無文法點")

# ③ 其餘區塊保持原樣
with st.expander("📋 輸入範例"):
    st.code("馬太福音 5:3 虛心的人有福了，因為天國是他們的。", language="text")
if st.checkbox("顯示分析歷史（最近10筆）"):
    for item in st.session_state.get("analysis_history", []):
        st.caption(item["date"])
        st.code(item["input_preview"])
