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
# 4. TAB2 ─ 月曆待辦（穩定最終版，史奴比移除 & Reboot 資料持久化）
# ===================================================================
with tabs[1]:
    import datetime as dt, re, os, json
    import streamlit as st
    from streamlit_calendar import calendar

    # ---------- 0. 檔案持久化 (Persistence) ----------
    DATA_DIR = "data"
    os.makedirs(DATA_DIR, exist_ok=True)
    TODO_FILE = os.path.join(DATA_DIR, "todos.json")

    def load_todos():
        if os.path.exists(TODO_FILE):
            try:
                with open(TODO_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"載入失敗: {e}")
        return {}

    def save_todos():
        try:
            with open(TODO_FILE, "w", encoding="utf-8") as f:
                json.dump(st.session_state.todo, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"儲存失敗: {e}")

    # ---------- 1. 初始化 (Initialization) ----------
    if "todo" not in st.session_state:
        st.session_state.todo = load_todos()
    if "sel_date" not in st.session_state:
        st.session_state.sel_date = str(dt.date.today())
    if "cal_key" not in st.session_state:
        st.session_state.cal_key = 0

    # ---------- 2. Emoji 工具 (Emoji Utils) ----------
    _EMOJI_RE = re.compile(r'[\U0001F300-\U0001FAFF\U00002700-\U000027BF]+', flags=re.UNICODE)
    
    def get_clean_title(text: str) -> tuple:
        """回傳 (單個Emoji, 無Emoji的標題)"""
        found = _EMOJI_RE.search(text)
        emoji = found.group(0)[0] if found else "" # 只取第一個字元
        clean_text = _EMOJI_RE.sub('', text).strip() # 移除所有 Emoji
        return emoji, clean_text

    # ---------- 3. 月曆事件 (Calendar Events) ----------
    def build_events():
        ev = []
        for d, items in st.session_state.todo.items():
            for t in items:
                # 重新解析，確保格子內不重複
                emo, pure_title = get_clean_title(t['title'])
                ev.append({
                    "title": f"{emo} {pure_title}",
                    "start": f"{d}T{t.get('time','00:00:00')}",
                    "backgroundColor": "#FFE4E1",
                    "borderColor": "#FFE4E1",
                    "textColor": "#333"
                })
        return ev

    # ---------- 4. 月曆組件 ----------
    with st.expander("📅 聖經學習生活月曆", expanded=True):
        cal_options = {
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
            "initialView": "dayGridMonth",
            "height": "auto"
        }
        state = calendar(events=build_events(), options=cal_options, key=f"cal_{st.session_state.cal_key}")
        if state.get("dateClick"):
            st.session_state.sel_date = state["dateClick"]["date"][:10]
            st.rerun()

    # ---------- 5. 待辦清單 (CRUD Operations) ----------
    st.markdown(f"##### 📋 {st.session_state.sel_date} 起三日清單")
    base_date = dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date()

    for offset in range(3):
        curr_d = str(base_date + dt.timedelta(days=offset))
        if curr_d in st.session_state.todo:
            # 倒序刪除才不會影響 index
            for idx, item in enumerate(st.session_state.todo[curr_d]):
                emo, txt = get_clean_title(item['title'])
                c1, c2, c3 = st.columns([1, 8, 1])
                c1.write("📍")
                c2.write(f"**{item['time'][:5]}** {emo} {txt}")
                if c3.button("🗑️", key=f"del_{curr_d}_{idx}"):
                    st.session_state.todo[curr_d].pop(idx)
                    save_todos() # 立即存檔
                    st.session_state.cal_key += 1
                    st.rerun()

    # ---------- 6. 新增 (Create) ----------
    with st.form("add_todo"):
        col1, col2 = st.columns(2)
        in_date = col1.date_input("日期", base_date)
        in_time = col2.time_input("時間", dt.time(9, 0))
        in_title = st.text_input("事項內容 (可輸入 Emoji)")
        if st.form_submit_button("💾 儲存並同步"):
            if in_title:
                d_key = str(in_date)
                if d_key not in st.session_state.todo:
                    st.session_state.todo[d_key] = []
                st.session_state.todo[d_key].append({"title": in_title, "time": str(in_time)})
                save_todos() # 立即存檔
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
# 6. TAB4 ─ AI 控制台（Snoopy置中版 + 功能修復）
# ===================================================================
with tabs[3]:
    import os, json, datetime as dt, pandas as pd, urllib.parse, base64

    # ---------- 🎨 Snoopy 背景（簡化版，不影響內容）----------
    try:
        with open("Snoopy.jpg", "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{img_b64}");
            background-size: 15% auto;
            background-position: center bottom 30px;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }}
        </style>
        """, unsafe_allow_html=True)
    except:
        pass  # 沒圖片也沒關係，繼續執行

    # ---------- 資料庫持久化 ----------
    SENTENCES_FILE = "sentences.json"

    def load_sentences():
        if os.path.exists(SENTENCES_FILE):
            try:
                with open(SENTENCES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_sentences(data):
        with open(SENTENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # 初始化 session_state
    if 'sentences' not in st.session_state:
        st.session_state.sentences = load_sentences()
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []

    # ---------- 📝 折疊欄 1：輸入與分析 ----------
    with st.expander("📝 經文輸入與AI分析", expanded=True):
        c1, c2, c3, c4 = st.columns(4)

        current_input = st.session_state.get("main_input", "")
        ai_prompt = f"""分析經文回傳JSON：{{"ref_no":"編號","ref_article":"英文","zh_translation":"中文","words":[],"phrases":[],"grammar":[]}}。經文：{current_input}"""
        encoded_prompt = urllib.parse.quote(ai_prompt)

        with c1:
            st.link_button("💬 GPT", f"https://chat.openai.com/?q={encoded_prompt}", use_container_width=True)
        with c2:
            st.link_button("🌙 K2", f"https://kimi.com/?q={encoded_prompt}", use_container_width=True)
        with c3:
            st.link_button("🔍 G", f"https://gemini.google.com/app?q={encoded_prompt}", use_container_width=True)
        with c4:
            if st.button("💾 存", type="primary", use_container_width=True):
                if not current_input.strip():
                    st.error("請輸入內容")
                else:
                    try:
                        data = json.loads(current_input)
                        ref = data.get("ref_no") or data.get("ref") or f"R_{dt.datetime.now().strftime('%m%d%H%M')}"
                        st.session_state.sentences[ref] = {
                            "ref": ref,
                            "en": data.get("ref_article", data.get("en", "")),
                            "zh": data.get("zh_translation", data.get("zh", "")),
                            "words": data.get("words", []),
                            "phrases": data.get("phrases", []),
                            "grammar": data.get("grammar", []),
                            "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        save_sentences(st.session_state.sentences)
                        st.success(f"✅ 已存：{ref}")
                        st.session_state["main_input"] = ""
                        st.rerun()
                    except:
                        ref = f"N_{dt.datetime.now().strftime('%m%d%H%M')}"
                        st.session_state.sentences[ref] = {
                            "ref": ref,
                            "en": current_input,
                            "zh": "",
                            "words": [],
                            "phrases": [],
                            "grammar": [],
                            "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        save_sentences(st.session_state.sentences)
                        st.success(f"✅ 已存筆記：{ref}")
                        st.session_state["main_input"] = ""
                        st.rerun()

        # ---------- 輸入框 ----------
        st.text_area(
            "",
            height=260,
            key="main_input",
            placeholder="📝 貼經文→點下方AI連結（系統會自動帶上這段文字）",
            label_visibility="collapsed"
        )

        # ---------- AI 連結區 ----------
        current_input = st.session_state.get("main_input", "")
        if current_input.strip():
            ai_prompt = f"""請分析以下聖經經文，以 JSON 格式回傳：
{{
  "ref_no": "經文編號",
  "ref_article": "完整英文經文", 
  "zh_translation": "中文翻譯",
  "words": [],
  "phrases": [],
  "grammar": []
}}
待分析經文：
{current_input}"""
            encoded = urllib.parse.quote(ai_prompt)

            st.caption(f"✅ 系統已讀取輸入（{len(current_input)} 字），點擊下方按鈕將自動傳給 AI：")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.link_button("💬 GPT", f"https://chat.openai.com/?q={encoded}", use_container_width=True, type="secondary")
            with c2:
                st.link_button("🌙 K2", f"https://kimi.com/?q={encoded}", use_container_width=True, type="secondary")
            with c3:
                st.link_button("🔍 G", f"https://gemini.google.com/app?q={encoded}", use_container_width=True, type="secondary")
            with c4:
                # 你原本 save_data 未定義，這裡先註解提示
                # st.button("💾 存", type="primary", use_container_width=True, on_click=save_data)
                pass
        else:
            st.warning("⚠️ 請先在上方輸入框貼上經文，AI 連結才會出現")
            st.write("（系統需要記錄輸入內容後，才能生成帶資料的連結）")

    # ---------- 🔍 折疊欄 2：資料管理 ----------
    with st.expander("🔍 資料搜尋與管理", expanded=False):
        search_col, btn_col = st.columns([3, 1])
        with search_col:
            query = st.text_input("搜尋 Ref. 或關鍵字", key="search_box", placeholder="例：2Ti 3:10 或 love")
        with btn_col:
            if st.button("搜尋", type="primary", use_container_width=True):
                if not query:
                    st.warning("請輸入搜尋條件")
                else:
                    kw = query.lower()
                    st.session_state.search_results = [
                        {"key": k, "選": False, "Ref.": v.get("ref", k),
                         "內容": (v.get("en", "")[:50] + "...") if len(v.get("en", "")) > 50 else v.get("en", ""),
                         "日期": v.get("date_added", "")[:10]}
                        for k, v in st.session_state.sentences.items()
                        if kw in f"{v.get('ref','')} {v.get('en','')} {v.get('zh','')}".lower()
                    ]
                    if not st.session_state.search_results:
                        st.info("找不到符合資料")

        if st.session_state.search_results:
            st.write(f"共 {len(st.session_state.search_results)} 筆")
            if st.checkbox("☑️ 全選"):
                for r in st.session_state.search_results:
                    r["選"] = True
            if st.button("🗑️ 刪除勾選項目"):
                selected = [r["key"] for r in st.session_state.search_results if r.get("選")]
                if selected:
                    for k in selected:
                        st.session_state.sentences.pop(k, None)
                    save_sentences(st.session_state.sentences)
                    st.success(f"✅ 已刪除 {len(selected)} 筆")
                    st.session_state.search_results = []
                    st.rerun()
                else:
                    st.warning("請先勾選要刪除的項目")
            df = pd.DataFrame(st.session_state.search_results)
            edited = st.data_editor(
                df,
                column_config={
                    "選": st.column_config.CheckboxColumn("選", width="small"),
                    "key": None,
                    "Ref.": st.column_config.TextColumn("Ref.", width="small"),
                    "內容": st.column_config.TextColumn("內容預覽", width="large"),
                    "日期": st.column_config.TextColumn("日期", width="small")
                },
                hide_index=True,
                use_container_width=True,
                height=min(350, len(df) * 35 + 40)
            )
            for i, row in edited.iterrows():
                st.session_state.search_results[i]["選"] = row["選"]

    # ---------- 底部統計 ----------
    st.divider()
    st.caption(f"💾 資料庫：{len(st.session_state.sentences)} 筆")
    if st.session_state.sentences:
        json_str = json.dumps(st.session_state.sentences, ensure_ascii=False, indent=2)
        st.download_button(
            "⬇️ 備份 JSON",
            json_str,
            file_name=f"backup_{dt.datetime.now().strftime('%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )

