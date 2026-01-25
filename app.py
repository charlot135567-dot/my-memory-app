# ===================================================================
# 0. 套件 & 全域函式（一定放最頂）
# ===================================================================
import streamlit as st
import subprocess, sys, os, pandas as pd, io, json
import random, math
from datetime import datetime, timezone, timedelta, date
# 現在就能用 date.today()
if 'sel_date' not in st.session_state:
    st.session_state.sel_date = str(date.today())
    
# ---- 29 段經文池（先放 3 段，記得補滿 29）----
VERSE_POOL = [
    {"ref": "2Ti 3:10-11", "en": "You, however, have followed my teaching...", "zh": "但你已經追隨了我的教導..."},
    {"ref": "2Ti 3:12", "en": "Indeed, all who desire to live a godly life...", "zh": "不但如此，凡立志..."},
    {"ref": "2Ti 3:29", "en": "Scripture is breathed out by God for our benefit.", "zh": "聖經是上帝所默示的..."}
    # ⭐ 把剩餘 26 段依同格式繼續補上
]

tz = timezone(timedelta(hours=8))          # 台灣時區
# 每 2 小時一段，一天 12 次
HOUR_IDX = (int(datetime.now(tz).strftime("%H")) // 2) % len(VERSE_POOL)
TODAY_VERSE = VERSE_POOL[HOUR_IDX]

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
# TAB2 ─ 金句集（5-5-4 群折疊，結構一致）
# ===================================================================
with tabs[1]:
    import datetime as dt

    today = dt.date.today()
    VERSES = [
    # ---- 14 句：5-5-4 群，結構一致 ----
    VERSES = [
        # 第 1 群（5 句）
        {"ref": "2Ti 3:10-11", "en": "You, however, have followed my teaching, my conduct, my aim in life, my faith, my patience, my love, my steadfastness, my persecutions and sufferings that happened to me at Antioch, at Iconium, and at Lystra—which persecutions I endured; yet from them all the Lord rescued me.",
         "zh": "但你已經追隨了我的教導、品行、志向、信心、寬容、愛心、忍耐，以及我在安提阿、以哥念、呂斯特拉所遭遇的逼迫和苦難；我所忍受的是何等的逼迫！但從這一切當中，主都把我救了出來。"},
        {"ref": "2Ti 3:12", "en": "Indeed, all who desire to live a godly life in Christ Jesus will be persecuted,",
         "zh": "不但如此，凡立志在基督耶穌裡敬虔度日的，也都要受逼迫。"},
        {"ref": "2Ti 3:13", "en": "while evil people and impostors will go on from bad to worse, deceiving and being deceived.",
         "zh": "但惡人和騙子必變本加厲，迷惑人也受迷惑。"},
        {"ref": "2Ti 3:14", "en": "But as for you, continue in what you have learned and have firmly believed, knowing from whom you learned it",
         "zh": "至於你，要持守你所學習的、所確信的，因為你知道是跟誰學的。"},
        {"ref": "2Ti 3:15", "en": "and how from childhood you have been acquainted with the sacred writings, which are able to make you wise for salvation through faith in Christ Jesus.",
         "zh": "並且你從小就明白聖經，這聖經能使你因信基督耶穌而有得救的智慧。"},
        # 第 2 群（5 句）
        {"ref": "2Ti 3:16", "en": "All Scripture is breathed out by God and profitable for teaching, for reproof, for correction, and for training in righteousness,",
         "zh": "聖經都是神所默示的，於教訓、督責、使人歸正、教導人學義都是有益的。"},
        {"ref": "2Ti 3:17", "en": "that the man of God may be complete, equipped for every good work.",
         "zh": "叫屬神的人得以完全，預備行各樣的善事。"},
        {"ref": "2Ti 3:10-11", "en": "High-Word: Conduct (品行) / Persecution (逼迫) / Steadfastness (堅忍)",
         "zh": "高階詞彙：品行、逼迫、堅忍 —— 你已追隨了我的教導與品行；我所忍受的逼迫，主都救我脫離。"},
        {"ref": "2Ti 3:12-13", "en": "High-Word: Godly (敬虔) / Impostors (騙子)",
         "zh": "高階詞彙：敬虔、騙子 —— 凡立志過敬虔生活的都要受逼迫；惡人與騙子變本加厲。"},
        {"ref": "2Ti 3:14-15", "en": "High-Word: Acquainted (熟悉) / Salvation (救恩)",
         "zh": "高階詞彙：熟悉、救恩 —— 從小熟悉聖經，使你因信基督而有得救智慧。"},
        # 第 3 群（4 句）
        {"ref": "2Ti 3:16-17", "en": "High-Word: Breathed out (默示) / Equipped (裝備)",
         "zh": "高階詞彙：默示、裝備 —— 聖經皆神所默示，使屬神之人得以完全，裝備行善。"},
        {"ref": "2Ti 3:16", "en": "High-Word: Profitable (有益) / Reproof (責備) / Righteousness (公義)",
         "zh": "高階詞彙：有益、責備、公義 —— 聖經於教訓、督責、使人歸正、教導人學義皆有益。"},
        {"ref": "2Ti 3:17", "en": "High-Word: Complete (完全) / Equipped (裝備)",
         "zh": "高階詞彙：完全、裝備 —— 使屬神的人得以完全，為各樣善事預備齊全。"},
        {"ref": "2Ti 3:10-17", "en": "High-Word: Vitality (生命力) / Aligned (對齊) / Infrastructure (基礎架構)",
         "zh": "高階詞彙：生命力、對齊、基礎架構 —— 話語帶來生命力，使人生與神對齊，信心為靈魂根基。"}
    ]

    # 只載一次，當永久庫    if "sentences" not in st.session_state:
        st.session_state.sentences = {str(today - dt.timedelta(days=i)): VERSES[i] for i in range(14)}

    # ---- 中文整句 + 英文 3 群折疊（句距已壓） ----
    group_size = [5, 5, 4]
    start = 0
    for g, size in enumerate(group_size, 1):
        with st.expander(f"📑 英文解答 第 {g} 組（點我看）"):
            for i in range(start, start + size):
                v = st.session_state.sentences[str(today - dt.timedelta(days=i))]
                st.markdown(f"**{v['ref']}**  \n{v['en']}")
                # 👇 只改這行：壓到半字高
                st.markdown('<div style="line-height:0.5;font-size:1px;">&nbsp;</div>',
                            unsafe_allow_html=True)
            start += size

    for i in range(14):
        d = str(today - dt.timedelta(days=i))
        v = st.session_state.sentences[d]
        st.markdown(f"**{d[-5:]}**｜{v['ref']}  \n{v['zh']}")
        # 👇 只改這行：壓到半字高
        st.markdown('<div style="line-height:0.5;font-size:1px;">&nbsp;</div>',
                    unsafe_allow_html=True)

    # 其餘原功能不動
    with st.expander("✨ 新增金句", expanded=True):
        new_sentence = st.text_input("中英並列", key="new_sentence")
        if st.button("儲存", type="primary"):
            if new_sentence:
                st.session_state.sentences[str(dt.date.today())] = new_sentence
                st.success("已儲存！")
            else:
                st.error("請輸入內容")

    if st.button("📋 匯出金句庫"):
        export = "\n".join([f"{k}  {v['ref']}  {v['en']}  {v['zh']}" for k, v in st.session_state.sentences.items()])
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
# TAB4 ─ AI 控制台（最終對齊版）
# ===================================================================
with tabs[3]:
    st.title("📚 多語聖經控制台")
    st.markdown("① 貼經文 → ② 一鍵分析 → ③ 直接檢視 → ④ 離線使用")

    # ① 貼經文
    with st.expander("① 貼經文（中文 or 英文講稿）", expanded=True):
        if st.button("🧪 快速測試（載入範例）"):
            st.session_state.input_text = "馬太福音 5:3 虚心的人有福了，因為天國是他們的。"
        input_text = st.text_area("經文/講稿", height=200, key="input_text")

        # 並排按鈕
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🤖 AI 分析", type="primary"):
                if not input_text:
                    st.error("請先貼經文")
                    st.stop()
                with st.spinner("AI 分析中，約 10 秒…"):
                    try:
                        with open("temp_input.txt", "w", encoding="utf-8") as f:
                            f.write(input_text.strip())
                        subprocess.run(
                            [sys.executable, "analyze_to_excel.py", "--file", "temp_input.txt"],
                            check=True, timeout=30
                        )
                        with open("temp_result.json", "r", encoding="utf-8") as f:
                            st.session_state["analysis"] = json.load(f)
                        save_analysis_result(st.session_state["analysis"], input_text)
                        st.success("分析完成！")
                    except Exception as e:
                        st.error(f"分析過程錯誤：{e}")

        with col2:
            if st.button("📊 顯示分析結果"):
                if "analysis" not in st.session_state:
                    st.error("請先按『AI 分析』")
                    st.stop()
                st.session_state["show_result"] = True

    # ② 結果呈現（與 expander 同層，滿寬）
    if st.session_state.get("show_result", False):
        data = st.session_state["analysis"]

        # Ref. 原文跳轉列
        st.session_state["ref_no"] = data.get("ref_no", "")
        st.session_state["ref_article"] = data.get("ref_article", "")
        st.markdown(f"**Ref. No.** `{st.session_state['ref_no']}`")
        c_jump, c_copy = st.columns(2)
        with c_jump:
            if st.button("📄 檢視原文"):
                st.session_state["show_article"] = True
        with c_copy:
            ref_no = st.session_state.get("ref_no", "")
            if ref_no:
                st.code(ref_no)          # 手動框選複製
            else:
                st.text("尚無 Ref.")

        if st.session_state.get("show_article", False):
            with st.expander("📘 中英精煉文章", expanded=True):
                st.markdown(st.session_state["ref_article"])

        # --- 表格（滿寬）---
        col_w, col_p, col_g = st.tabs(["單字", "片語", "文法"])
        with col_w:
            if data.get("words"):
                df = pd.DataFrame(data["words"])
                df.insert(0, "Ref.", data.get("ref_no", ""))
                st.dataframe(df, use_container_width=True)
            else:
                st.info("本次無單字分析")
        with col_p:
            if data.get("phrases"):
                df = pd.DataFrame(data["phrases"])
                df.insert(0, "Ref.", data.get("ref_no", ""))
                st.dataframe(df, use_container_width=True)
            else:
                st.info("本次無片語分析")
        with col_g:
            if data.get("grammar"):
                df = pd.DataFrame(data["grammar"])
                df.insert(0, "Ref.", data.get("ref_no", ""))
                st.table(df)
            else:
                st.info("本次無文法點")

    # ③ 其餘區塊保持原樣
    with st.expander("📋 輸入範例"):
        st.code("馬太福音 5:3 虚心的人有福了，因為天國是他們的。", language="text")
    if st.checkbox("顯示分析歷史（最近10筆）"):
        for item in st.session_state.get("analysis_history", []):
            st.caption(item["date"])
            st.code(item["input_preview"])
