# ===================================================================
# 0. 套件 & 全域函式（一定放最頂）
# ===================================================================
import streamlit as st
import subprocess, sys, os, datetime as dt, pandas as pd, io, json, re, tomli, tomli_w
from streamlit_calendar import calendar

# ========== 除錯測試 ==========
st.sidebar.markdown("## 🔧 除錯資訊")

api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    st.sidebar.success("✅ GEMINI_API_KEY 已設定")
    st.sidebar.write(f"長度: {len(api_key)} 字元")
else:
    st.sidebar.error("❌ GEMINI_API_KEY 未設定")
    st.sidebar.info("請到 Settings → Secrets 設定")
    
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
    c1.link_button("✨ Google AI", "https://gemini.google.com/ ")
    c2.link_button("🤖 Kimi K2",   "https://kimi.moonshot.cn/ ")
    c3, c4 = st.columns(2)
    c3.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb ")
    c4.link_button("THSV11",    "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11 ")

# ===================================================================
# 2. 頁面配置 & Session 初值（只留全域會用到的）
# ===================================================================
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# 這些變數只有 TAB2 會用到，但為了避免後續 TAB 引用出錯，先給空值
if 'analysis_history' not in st.session_state: st.session_state.analysis_history = []

# ---------- CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap ');
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

tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# ===================================================================
# 3. TAB1 ─ 書桌（單純經文與例句，無月曆）
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
# 4. TAB2 ─ 月曆待辦（穩定最終版）
# ===================================================================
with tabs[1]:
    import datetime as dt, re, os, json
    from streamlit_calendar import calendar

    # ---------- 背景圖（僅 TAB2，淡化） ----------
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] + div [data-testid="stVerticalBlock"] {
        background-image: url("assets/68254faebaafed9dafb41918f74c202e.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }
    section[data-testid="stSidebar"] + div [data-testid="stVerticalBlock"]::before {
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(255,255,255,0.82);
        z-index: -1;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------- 0. 檔案持久化 ----------
    TODO_FILE = "todos.json"

    def load_todos():
        if os.path.exists(TODO_FILE):
            try:
                with open(TODO_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_todos():
        with open(TODO_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.todo, f, ensure_ascii=False, indent=2)

    # ---------- 1. 初始化 ----------
    if "todo" not in st.session_state:
        st.session_state.todo = load_todos()
    if "sel_date" not in st.session_state:
        st.session_state.sel_date = str(dt.date.today())
    if "cal_key" not in st.session_state:
        st.session_state.cal_key = 0
    if "active_del_id" not in st.session_state:
        st.session_state.active_del_id = None

    # ---------- 2. Emoji 工具 ----------
    _EMOJI_RE = re.compile(
        r'[\U0001F300-\U0001FAFF\U00002700-\U000027BF]+', flags=re.UNICODE
    )
    def first_emoji(text: str) -> str:
        m = _EMOJI_RE.search(text)
        return m.group(0) if m else ""

    # ---------- 3. 月曆事件（格子只顯示文字 + Emoji） ----------
    def build_events():
        ev = []
        for d, items in st.session_state.todo.items():
            if not isinstance(items, list):
                continue
            for t in items:
                ev.append({
                    "title": f"{t.get('emoji','')}{t['title']}",
                    "start": f"{d}T{t.get('time','00:00:00')}",
                    "backgroundColor": "#FFE4E1",
                    "borderColor": "#FFE4E1",
                    "textColor": "#333"
                })
        return ev

    # ---------- 4. 月曆（折疊欄） ----------
    with st.expander("📅 聖經學習生活月曆", expanded=True):
        cal_options = {
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": ""
            },
            "initialView": "dayGridMonth",
            "displayEventTime": False,
            "height": "auto"
        }

        state = calendar(
            events=build_events(),
            options=cal_options,
            key=f"calendar_{st.session_state.cal_key}"
        )

        if state.get("dateClick"):
            st.session_state.sel_date = state["dateClick"]["date"][:10]
            st.rerun()

    # ---------- 5. 下方三日清單（💟 → 🗑️） ----------
    st.markdown("##### 📋 待辦事項")

    try:
        base_date = dt.datetime.strptime(
            st.session_state.sel_date, "%Y-%m-%d"
        ).date()
    except:
        base_date = dt.date.today()

    for offset in range(3):
        d_obj = base_date + dt.timedelta(days=offset)
        d_str = str(d_obj)
        if d_str in st.session_state.todo:
            for idx, item in enumerate(st.session_state.todo[d_str]):
                item_id = f"{d_str}_{idx}"

                c1, c2, c3 = st.columns([1, 7, 2], vertical_alignment="top")

                with c1:
                    if st.button("💟", key=f"h_{item_id}"):
                        st.session_state.active_del_id = (
                            None if st.session_state.active_del_id == item_id else item_id
                        )
                        st.rerun()

                with c2:
                    st.write(
                        f"{d_obj.month}/{d_obj.day} "
                        f"{item['time'][:5]} "
                        f"{item.get('emoji','')}{item['title']}"
                    )

                with c3:
                    if st.session_state.active_del_id == item_id:
                        if st.button("🗑️", key=f"d_{item_id}"):
                            st.session_state.todo[d_str].pop(idx)
                            save_todos()
                            st.session_state.cal_key += 1
                            st.session_state.active_del_id = None
                            st.rerun()

    # ---------- 6. 新增待辦 ----------
    st.divider()
    with st.expander("➕ 新增待辦", expanded=True):
        with st.form("todo_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                in_date = st.date_input("日期", base_date)
            with col2:
                in_time = st.time_input("時間", dt.time(9, 0))

            in_title = st.text_input("待辦事項（可含 Emoji）")

            if st.form_submit_button("💾 儲存"):
                if in_title:
                    k = str(in_date)
                    if k not in st.session_state.todo:
                        st.session_state.todo[k] = []
                    st.session_state.todo[k].append({
                        "title": in_title,
                        "time": str(in_time),
                        "emoji": first_emoji(in_title)
                    })
                    save_todos()
                    st.session_state.cal_key += 1
                    st.rerun()

# ===================================================================
# 5. TAB3 ─ 挑戰（單純翻譯題，無月曆）
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
# 5. TAB4 ─ AI 控制台（共用欄位 + ChatGPT API / 任意 LLM UI）
# ===================================================================
with tabs[3]:
    import os, pandas as pd, io, json, datetime as dt
    import streamlit as st

    # ---------- 0. AI Prompt 定義 ----------
    PROMPT_BIBLE_MASTER = """
你是一位精通多國語言的聖經專家與語言學教授。請根據使用者輸入的內容類型，選擇對應的模式輸出。

---
### 模式 A：【聖經經文模式】
當使用者輸入為「中文聖經經文」時，請嚴格產出以下 V1 與 V2 表格數據，禁止產出講章。

🔹 V1 Sheet 要求：
1. Ref.：自動找尋經卷章節並用縮寫 (如: Pro, Rom, Gen)。
2. English (ESV)：檢索對應的 ESV 英文經文。
3. Chinese：填入我提供的中文原文。
4. Syn/Ant：挑選高級→中高級→中級→中級以下（無前者才列）字詞，含中/英翻譯。
5. Grammar：嚴格符號化格式 1️⃣2️⃣3️⃣Ex.

🔹 V2 Sheet 要求：
1. Ref.：同 V1。
2. 口語訳：日文《口語訳聖經》(1955)。
3. Grammar：解析日文文法（格式同 V1）。
4. Note：補充日文文法或語境。
5. KRF：韓文《Korean Revised Version》。
6. Syn/Ant：韓文高/中高級字（含日/韓/中翻譯）。
7. THSV11：泰文《THSV11》。

---
### 模式 B：【英文文稿模式】
當使用者輸入為「英文講道初稿」時：
1️⃣ 純英文段落 → 流暢＋文法正確，保留高級/中高級字詞，保持神學用詞精確。
2️⃣ 中英夾雜段落 → 中文敘述＋對應英文詞彙插入括號。
3️⃣ 排版 → 大綱標題與內容間空行。

🔹 第二步｜語言素材：
Vocabulary (20個) & Phrases (15個): 高級/中高級字詞＋片語，中英對照聖經例句。
Grammar List (6個): 原文+結構還原+邏輯解析+中英例句。
"""

    # ---------- 1. 雲端 JSON 持久化工具 ----------
    if 'sentences' not in st.session_state:
        st.session_state.sentences = {}

    def save_sentences():
        """JSON 儲存至 session_state"""
        st.session_state.sentences = st.session_state.sentences

    # ---------- 2. 共用輸入欄位 ----------
    st.markdown("📚① 貼經文/講稿 → ② 一鍵分析 → ③ 直接檢視 → ④ 離線使用")
    input_text = st.text_area("貼上經文或英文講稿", height=300, key="input_text")

    # ---------- 3. 操作方式選擇 ----------
    col1, col2 = st.columns([2,3])
    with col1:
        operation = st.selectbox("操作方式", ["ChatGPT API 生成", "任意 LLM UI 生成 Prompt"])
    with col2:
        st.write("說明：ChatGPT API 可一鍵生成 Excel/CSV；任意 LLM 需手動貼 Prompt 並貼回結果")

    # ---------- 4. 按鈕：生成或取得 Prompt ----------
    if operation == "任意 LLM UI 生成 Prompt":
        if st.button("🤖 生成 LLM Prompt"):
            if not input_text.strip():
                st.error("請先貼經文或講稿")
                st.stop()
            final_prompt = PROMPT_BIBLE_MASTER.replace("[[TEXT]]", input_text)
            st.success("✅ Prompt 已生成，可複製貼到任意 LLM UI")
            st.code(final_prompt, language="text")
            st.session_state["generated_prompt"] = final_prompt

    elif operation == "ChatGPT API 生成":
        if st.button("🤖 ChatGPT 生成 Excel/CSV"):
            if not input_text.strip():
                st.error("請先貼經文或講稿")
                st.stop()
            # 這裡放 ChatGPT API 呼叫邏輯 (假設你已有 API function)
            # result = call_chatgpt_api(input_text)
            result = {
                "ref_no": f"AI{dt.datetime.now().strftime('%Y%m%d%H%M')}",
                "words": [],
                "phrases": [],
                "grammar": [],
                "ref_article": "示例精煉文章",
                "ref_article_zh": "示例中文文章"
            }
            ref_no = result["ref_no"]
            st.session_state.sentences[ref_no] = {
                "ref": ref_no,
                "en": result.get("ref_article", ""),
                "zh": result.get("ref_article_zh", ""),
                "data": result,
                "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            save_sentences()
            st.success(f"✅ 已生成並存檔！Ref: {ref_no}")
            st.session_state["analysis"] = result
            st.session_state["show_result"] = True

    # ---------- 5. AI 回傳結果共用欄位 ----------
    st.divider()
    st.markdown("📥 步驟 ②：貼上任意 LLM UI 回傳的分析結果")
    ai_result = st.text_area("AI 回傳結果", height=250, key="ai_result")
    if st.button("💾 儲存 AI 結果"):
        if not ai_result.strip():
            st.error("請先貼上 AI 分析結果")
            st.stop()
        try:
            cleaned = ai_result.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            ref_no = data.get("ref_no", f"AI{dt.datetime.now().strftime('%Y%m%d%H%M')}")
            st.session_state.sentences[ref_no] = {
                "ref": ref_no,
                "en": data.get("ref_article",""),
                "zh": data.get("ref_article_zh",""),
                "data": data,
                "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            save_sentences()
            st.success(f"✅ AI 結果已存檔！Ref: {ref_no}")
            st.session_state["analysis"] = data
            st.session_state["show_result"] = True
        except json.JSONDecodeError:
            ref_no = f"TXT{dt.datetime.now().strftime('%Y%m%d%H%M')}"
            st.session_state.sentences[ref_no] = {
                "ref": ref_no,
                "raw_text": ai_result,
                "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            save_sentences()
            st.success(f"✅ 已存為純文字！Ref: {ref_no}")

    # ---------- 6. 結果呈現 ----------
    if st.session_state.get("show_result", False) and st.session_state.get("analysis"):
        data = st.session_state["analysis"]
        st.divider()
        st.markdown(f"## 📋 分析結果：{data.get('ref_no','N/A')}")
        if data.get("ref_article"):
            with st.expander("📄 檢視精煉文章", expanded=True):
                st.markdown(data["ref_article"])
        col_w, col_p, col_g = st.tabs(["單字","片語","文法"])
        with col_w:
            if data.get("words"):
                st.dataframe(pd.DataFrame(data["words"]), use_container_width=True)
            else:
                st.info("本次無單字分析")
        with col_p:
            if data.get("phrases"):
                st.dataframe(pd.DataFrame(data["phrases"]), use_container_width=True)
            else:
                st.info("本次無片語分析")
        with col_g:
            if data.get("grammar"):
                st.table(pd.DataFrame(data["grammar"]))
            else:
                st.info("本次無文法點")

    # ---------- 7. 匯出與容量管理 ----------
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 匯出含回溯欄位"):
            export = []
            for k,v in st.session_state.sentences.items():
                export.append(f"{k}\t{v.get('ref','')}\t{v.get('en','')}\t{v.get('raw_text','')[:100]}")
            st.code("\n".join(export), language="text")
    with col2:
        max_keep = st.number_input("最多保留最近幾筆分析紀錄", min_value=10, max_value=1000, value=50)
        if st.button("✂️ 壓縮舊紀錄"):
            hist = list(st.session_state.sentences.items())
            if len(hist) > max_keep:
                st.session_state.sentences = dict(hist[-max_keep:])
                st.success(f"已壓縮至最近 {max_keep} 筆！")
            else:
                st.info("未達壓縮門檻")


