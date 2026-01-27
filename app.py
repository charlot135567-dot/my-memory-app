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
# 4. TAB2 ─ 月曆待辦（最終折衷穩定版）
# ===================================================================
with tabs[1]:
    import datetime as dt, re, os, json

    # ---------- 0. 檔案持久化工具 ----------
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
        cutoff = str(dt.date.today() - dt.timedelta(days=60))
        keys_to_remove = [k for k in st.session_state.todo.keys() if k < cutoff]
        for k in keys_to_remove:
            del st.session_state.todo[k]
        with open(TODO_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.todo, f, ensure_ascii=False, indent=2)

    # ---------- 1. 初值與自動讀檔 ----------
    for key in ("cal_key", "sel_date", "edit_target"):
        if key not in st.session_state:
            st.session_state[key] = None if key == "edit_target" else 0

    if not st.session_state.sel_date:
        st.session_state.sel_date = str(dt.date.today())

    if "todo" not in st.session_state:
        st.session_state.todo = load_todos()

    # 預先建立未來 60 天空清單
    today = dt.date.today()
    for i in range(60):
        d = str(today + dt.timedelta(days=i))
        if d not in st.session_state.todo:
            st.session_state.todo[d] = []

    # ---------- 2. Emoji 工具 ----------
    _EMOJI_RE = re.compile(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
        r"\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
        r"\U00002702-\U000027B0\U000024C2-\U0001F251]+",
        flags=re.UNICODE,
    )

    def first_emoji(text: str) -> str:
        m = _EMOJI_RE.search(text)
        return m.group(0) if m else ""

    def remove_emoji(text: str) -> str:
        return _EMOJI_RE.sub("", text).strip()

    # ---------- 3. 月曆事件來源（只顯示短標題，不互動） ----------
    def build_events():
        ev = []
        for d, todos in st.session_state.todo.items():
            if not isinstance(todos, list):
                continue

            todos_sorted = sorted(todos, key=lambda x: x.get("time", "00:00"))
            for t in todos_sorted:
                short_title = f"{t.get('emoji','🔔')} {t['title']}"
                if len(short_title) > 18:
                    short_title = short_title[:18] + "…"

                ev.append(
                    {
                        "title": short_title,
                        "start": f"{d}T{t.get('time','00:00')}",
                        "allDay": False,
                        "backgroundColor": "#FFE4E1",
                        "borderColor": "#FFE4E1",
                        "textColor": "#333",
                    }
                )
        return ev

    # ---------- 4. CSS（僅基本美化，不碰高度/互動） ----------
    st.markdown(
        """
    <style>
    .fc-toolbar-title { font-size: 26px; font-weight: 700; color: #3b82f6; }
    .fc-day-sat .fc-daygrid-day-number,
    .fc-day-sun .fc-daygrid-day-number { color: #dc2626 !important; font-weight: 600; }
    .fc-event { border: none; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # ---------- 5. 月曆本體（純顯示） ----------
    st.subheader("📅 月曆待辦")
    with st.expander("展開 / 折疊月曆視窗", expanded=True):
        calendar(
            events=build_events(),
            options={
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": "",
                },
                "initialView": "dayGridMonth",
                "height": "auto",
                "eventDisplay": "block",
                "eventTimeFormat": {
                    "hour": "2-digit",
                    "minute": "2-digit",
                    "hour12": False,
                },
            },
            key=f"emoji_cal_{st.session_state.cal_key}",
        )

    # ---------- 6. 下方列表（唯一操作入口） ----------
    try:
        base_date = dt.datetime.strptime(
            st.session_state.sel_date, "%Y-%m-%d"
        ).date()
    except:
        base_date = dt.date.today()

    st.markdown("##### 📋 詳細列表")
    has_items = False

    for i in range(3):
        dd = base_date + dt.timedelta(days=i)
        ds = str(dd)

        if ds in st.session_state.todo and st.session_state.todo[ds]:
            has_items = True
            date_display = f"{dd.month}/{dd.day}"
            sorted_items = sorted(
                st.session_state.todo[ds], key=lambda x: x.get("time", "00:00")
            )

            for idx, t in enumerate(sorted_items):
                row_key = f"{ds}_{idx}"
                time_display = t.get("time", "00:00")[:5]

                c0, c1 = st.columns([1, 11])
                with c0:
                    toggle = st.button("💟", key=f"opt_{row_key}")
                with c1:
                    st.write(
                        f"**{date_display} {time_display}** "
                        f"{t.get('emoji','🔔')}{t['title']}"
                    )

                if toggle:
                    op1, op2, _ = st.columns([2, 2, 8])

                    # 編輯
                    with op1:
                        if st.button("📑 編輯", key=f"edit_{row_key}"):
                            st.session_state.edit_target = {
                                "date": ds,
                                "title": t["title"],
                                "time": t.get("time", "00:00"),
                                "emoji": t.get("emoji", "🔔"),
                            }
                            st.rerun()

                    # 刪除
                    with op2:
                        if st.button("🗑️ 刪除", key=f"del_{row_key}"):
                            st.session_state.todo[ds] = [
                                item
                                for item in st.session_state.todo[ds]
                                if not (
                                    item["title"] == t["title"]
                                    and item.get("time") == t.get("time")
                                )
                            ]
                            if not st.session_state.todo[ds]:
                                del st.session_state.todo[ds]
                            save_todos()
                            st.session_state.cal_key += 1
                            st.rerun()

    if not has_items:
        st.caption("此期間尚無待辦事項")

    # ---------- 7. 編輯區 ----------
    if st.session_state.edit_target:
        et = st.session_state.edit_target
        st.markdown("---")
        st.markdown("#### ✏️ 編輯待辦")

        new_emoji = st.text_input("Emoji", et["emoji"], max_chars=2)
        new_title = st.text_input("標題", et["title"])
        new_time = st.time_input(
            "時間", dt.datetime.strptime(et["time"], "%H:%M").time()
        )

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("💾 儲存修改"):
                for item in st.session_state.todo.get(et["date"], []):
                    if (
                        item["title"] == et["title"]
                        and item.get("time") == et["time"]
                    ):
                        item["title"] = new_title
                        item["emoji"] = new_emoji
                        item["time"] = new_time.strftime("%H:%M")
                        break
                save_todos()
                st.session_state.edit_target = None
                st.session_state.cal_key += 1
                st.rerun()

        with c2:
            if st.button("取消"):
                st.session_state.edit_target = None
                st.rerun()

    # ---------- 8. 新增待辦 ----------
    st.divider()
    with st.expander("➕ 新增待辦", expanded=True):
        with st.form("todo_form"):
            try:
                default_date = dt.datetime.strptime(
                    st.session_state.sel_date, "%Y-%m-%d"
                ).date()
            except:
                default_date = dt.date.today()

            c1, c2, c3 = st.columns([2, 2, 6])
            with c1:
                d_input = st.date_input("日期", default_date, label_visibility="collapsed")
            with c2:
                tm_input = st.time_input(
                    "時間", dt.time(9, 0), label_visibility="collapsed"
                )
            with c3:
                ttl_input = st.text_input(
                    "標題", placeholder="🔔 Emoji＋待辦", label_visibility="collapsed"
                )

            if st.form_submit_button("💾 儲存", use_container_width=True):
                if not ttl_input:
                    st.error("請輸入標題")
                else:
                    emo = first_emoji(ttl_input) or "🔔"
                    title = remove_emoji(ttl_input)
                    k = str(d_input)
                    st.session_state.todo.setdefault(k, []).append(
                        {
                            "title": title,
                            "time": tm_input.strftime("%H:%M"),
                            "emoji": emo,
                        }
                    )
                    save_todos()
                    st.session_state.cal_key += 1
                    st.success("✅ 已儲存！")
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
# 5. TAB4 ─ AI 聖經分析控制台（路徑修正版）
# ===================================================================
with tabs[3]:
    import json
    import datetime as dt
    import pandas as pd
    import streamlit as st
    import os
    import sys

    # ============================================================
    # 0. 輔助函數（先定義）
    # ============================================================
    def create_fallback_data(text, prompt_type):
        """產生預設資料"""
        return {
            "ref_no": f"FB{dt.datetime.now().strftime('%Y%m%d%H%M')}",
            "ref_article": text[:200],
            "is_fallback": True,
            "words": [{"Vocab": "becoming", "Example": "Fine speech is not becoming to a fool.", "口語訳": "愚か者にはふさわしくない"}],
            "phrases": [{"Phrase": "fine speech", "Example": "Fine speech is not becoming to a fool."}],
            "grammar": [{"Rule": "becoming to + N", "解析": "相稱義形容詞片語"}]
        }

    def find_prompts_file():
        """尋找 Prompts.toml（嘗試多個路徑）"""
        possible_paths = [
            "Prompts.toml",  # 目前目錄
            "./Prompts.toml",
            "../Prompts.toml",
            "/mount/src/Prompts.toml",  # Streamlit Cloud 常見路徑
            "/app/Prompts.toml",
        ]
        
        # 也嘗試從腳本位置找
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            possible_paths.insert(0, os.path.join(script_dir, "Prompts.toml"))
        except:
            pass
        
        for path in possible_paths:
            if os.path.exists(path):
                st.sidebar.success(f"✅ 找到 Prompts.toml: {path}")
                return path
        
        # 找不到，列出目前目錄內容
        st.sidebar.error("❌ 找不到 Prompts.toml")
        try:
            st.sidebar.write("目前目錄內容:")
            st.sidebar.code(str(os.listdir('.')))
        except Exception as e:
            st.sidebar.write(f"無法列出目錄: {e}")
        
        return None

    def load_prompts_from_toml():
        """載入 Prompts.toml"""
        file_path = find_prompts_file()
        if not file_path:
            return None
            
        try:
            import tomllib
            with open(file_path, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            st.sidebar.error(f"❌ 讀取 Prompts.toml 失敗: {e}")
            return None

    def analyze_with_gemini(text, prompt_template, api_key):
        """呼叫 Gemini API，回傳 (成功與否, 結果或錯誤訊息)"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = prompt_template.format(text=text[:3000])
            
            with st.spinner("🤖 正在呼叫 Gemini API..."):
                response = model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.2,
                        'max_output_tokens': 8192,
                    }
                )
            
            result_text = response.text
            result_text = result_text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(result_text)
            return True, data
            
        except Exception as e:
            return False, str(e)

    # ============================================================
    # 1. 載入 Prompts
    # ============================================================
    PROMPTS = load_prompts_from_toml()

    # ============================================================
    # 2. UI 介面
    # ============================================================
    st.markdown("## 🤖 AI 聖經分析控制台")
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not PROMPTS:
        st.error("❌ 無法載入 Prompts.toml")
        st.info("請確認 Prompts.toml 在專案根目錄，或改用內建 Prompts")
        
        # 提供內建備援
        if st.button("使用內建 Prompts 繼續"):
            PROMPTS = {
                "default": {
                    "chinese_verve": """請分析以下中文經文，產生 JSON 格式：
{text}
輸出格式：{"ref_no": "...", "words": [...], "phrases": [...], "grammar": [...]}""",
                    "english_manuscript": """請分析以下英文講稿，產生 JSON 格式：
{text}
輸出格式：{"ref_no": "...", "words": [...], "phrases": [...], "grammar": [...]}""",
                    "refine_sermon": """請精煉以下講稿，產生 JSON 格式：
{text}
輸出格式：{"ref_no": "...", "ref_article": "...", "words": [...], "phrases": [...], "grammar": [...]}"""
                }
            }
            st.rerun()
        st.stop()
    
    if not api_key:
        st.error("❌ 未設定 GEMINI_API_KEY")
        st.stop()
    
    # 輸入區
    with st.expander("📚 輸入經文或講稿", expanded=True):
        input_text = st.text_area(
            "貼上內容",
            height=250,
            key="tab4_input",
            placeholder="貼上中文聖經經文或英文講稿..."
        )
        
        chinese_chars = sum(1 for c in input_text[:200] if '\u4e00' <= c <= '\u9fff')
        is_chinese = chinese_chars > 10
        
        if input_text:
            st.info(f"偵測到：{'中文' if is_chinese else '英文'}（{len(input_text)} 字）")
        
        prompt_options = {
            "chinese_verve": "中文經文分析 (V1/V2)",
            "english_manuscript": "英文講稿分析 (Words/Phrases)",
            "refine_sermon": "英文講稿精煉 (完整版)"
        }
        
        available_prompts = [p for p in prompt_options.keys() 
                           if p in PROMPTS.get("default", {})]
        
        if not available_prompts:
            st.error("Prompts.toml 中沒有可用的 Prompt")
            st.stop()
        
        selected_prompt = st.selectbox(
            "選擇分析模式",
            options=available_prompts,
            format_func=lambda x: prompt_options[x],
            index=0 if is_chinese and "chinese_verve" in available_prompts else 0
        )
        
        analyze_btn = st.button("🤖 開始 AI 分析", type="primary")

    # ============================================================
    # 3. 執行分析
    # ============================================================
    if analyze_btn and input_text:
        prompt_template = PROMPTS.get("default", {}).get(selected_prompt, "")
        
        if not prompt_template:
            st.error(f"❌ 找不到 Prompt: {selected_prompt}")
            st.stop()
        
        success, result = analyze_with_gemini(input_text, prompt_template, api_key)
        
        if success:
            st.session_state["analysis_result"] = result
            st.session_state["show_result"] = True
            st.success(f"✅ 分析完成！")
            st.rerun()
        else:
            st.error("❌ AI 分析失敗")
            st.code(result)
            
            if st.button("使用預設資料繼續"):
                fallback = create_fallback_data(input_text, selected_prompt)
                st.session_state["analysis_result"] = fallback
                st.session_state["show_result"] = True
                st.rerun()

    # ============================================================
    # 4. 顯示結果
    # ============================================================
    if st.session_state.get("show_result", False):
        data = st.session_state.get("analysis_result", {})
        
        st.divider()
        st.markdown(f"## 📋 分析結果")
        
        if data.get("is_fallback"):
            st.warning("⚠️ 此為預設資料")
        
        st.markdown(f"**Ref. No.:** `{data.get('ref_no', 'N/A')}`")
        
        col1, col2, col3 = st.tabs(["📝 單字", "💬 片語", "📐 文法"])
        
        with col1:
            words = data.get("words", [])
            if words:
                st.dataframe(pd.DataFrame(words), use_container_width=True)
            else:
                st.info("無單字資料")
        
        with col2:
            phrases = data.get("phrases", [])
            if phrases:
                st.dataframe(pd.DataFrame(phrases), use_container_width=True)
            else:
                st.info("無片語資料")
        
        with col3:
            grammar = data.get("grammar", [])
            if grammar:
                st.table(pd.DataFrame(grammar))
            else:
                st.info("無文法資料")
