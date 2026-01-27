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
# 4. TAB2 ─ 月曆待辦 (精準修復：恢復日期選擇、修復 💟 功能、解決圖片閃爍)
# ===================================================================
with tabs[1]:
    import datetime as dt, re, os, json

    # ---------- 0. 穩定持久化邏輯 ----------
    TODO_FILE = "todos.json"

    def load_todos():
        if os.path.exists(TODO_FILE):
            try:
                with open(TODO_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {}

    def save_todos():
        with open(TODO_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.todo, f, ensure_ascii=False, indent=2)

    # ---------- 1. 初始化 (嚴格保留所有功能 Key) ----------
    if 'todo' not in st.session_state: st.session_state.todo = load_todos()
    if 'sel_date' not in st.session_state: st.session_state.sel_date = str(dt.date.today())
    if 'cal_key' not in st.session_state: st.session_state.cal_key = 0
    if 'active_edit_id' not in st.session_state: st.session_state.active_edit_id = None

    # ---------- 2. Emoji 工具 ----------
    _EMOJI_RE = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+', flags=re.UNICODE)
    def first_emoji(text: str) -> str:
        m = _EMOJI_RE.search(text)
        return m.group(0) if m else ""

    # ---------- 3. CSS 美化 (含隱藏時間與 Snoopy 風格) ----------
    st.markdown("""
    <style>
    .fc-toolbar-title { font-size: 24px !important; color: #5DADE2 !important; font-weight: bold; }
    .fc-event-time { display: none !important; } 
    .fc-event { border: none !important; border-radius: 5px !important; }
    .stButton>button { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

    # ---------- 4. 月曆組件 (格內僅顯示 Emoji + 標題) ----------
    def build_events():
        ev = []
        for d, items in st.session_state.todo.items():
            if isinstance(items, list):
                for t in items:
                    ev.append({
                        "title": f"{t.get('emoji','📌')}{t['title']}",
                        "start": f"{d}T{t.get('time','00:00:00')}",
                        "backgroundColor": "#FFE4E1", "borderColor": "#FFB6C1", "textColor": "#333"
                    })
        return ev

    st.subheader("📅 聖經學習生活月曆")
    
    cal_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
        "initialView": "dayGridMonth",
        "displayEventTime": False,
        "selectable": True,
        "height": 500
    }
    
    state = calendar(events=build_events(), options=cal_options, key=f"cal_v1_{st.session_state.cal_key}")

    if state.get("dateClick"):
        st.session_state.sel_date = state["dateClick"]["date"][:10]
        st.rerun()

    # ---------- 5. 💟 功能與三日清單預覽 (修復 strptime 崩潰) ----------
    st.divider()
    curr_date_str = st.session_state.sel_date
    try:
        # 防禦性檢查：確保是字串且格式正確
        base_date = dt.datetime.strptime(str(curr_date_str), "%Y-%m-%d").date()
    except:
        base_date = dt.date.today()
        st.session_state.sel_date = str(base_date)

    st.markdown(f"##### 📋 {st.session_state.sel_date} 起三日預覽")

    for offset in range(3):
        d_obj = base_date + dt.timedelta(days=offset)
        d_str = str(d_obj)
        if d_str in st.session_state.todo and st.session_state.todo[d_str]:
            for idx, item in enumerate(st.session_state.todo[d_str]):
                item_id = f"{d_str}_{idx}"
                col_h, col_t, col_a = st.columns([1, 7, 3])
                
                with col_h:
                    if st.button("💟", key=f"h_{item_id}"):
                        st.session_state.active_edit_id = item_id if st.session_state.active_edit_id != item_id else None
                        st.rerun()
                
                with col_t:
                    st.write(f"**{item['time'][:5]}** {item.get('emoji','')} {item['title']}")
                
                # 恢復 💟 點擊後的操作功能
                if st.session_state.active_edit_id == item_id:
                    with col_a:
                        ce, cd = st.columns(2)
                        if ce.button("✏️", key=f"e_{item_id}"):
                            st.toast("💡 修改：請在下方表單輸入新內容後刪除此舊項")
                        if cd.button("🗑️", key=f"d_{item_id}"):
                            st.session_state.todo[d_str].pop(idx)
                            save_todos()
                            st.session_state.cal_key += 1
                            st.session_state.active_edit_id = None
                            st.rerun()

    # ---------- 6. 新增事項 (恢復日期選擇器 st.date_input) ----------
    with st.expander("➕ 新增事項", expanded=True):
        with st.form("new_todo_form", clear_on_submit=True):
            col_d, col_tm = st.columns(2)
            with col_d:
                # 恢復日期選擇器，預設為選中日期
                in_date = st.date_input("日期", base_date)
            with col_tm:
                in_time = st.time_input("時間", dt.time(9, 0))
            
            in_name = st.text_input("待辦事項名稱 (可包含 Emoji)")
            
            if st.form_submit_button("💾 儲存事項"):
                if in_name:
                    k = str(in_date)
                    if k not in st.session_state.todo: st.session_state.todo[k] = []
                    st.session_state.todo[k].append({
                        "title": in_name, "time": str(in_time), "emoji": first_emoji(in_name) or "📌"
                    })
                    save_todos()
                    st.session_state.cal_key += 1 
                    st.rerun()

    # ---------- 7. 史努比底部美化 (修復失效圖片) ----------
    st.markdown("---")
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; gap: 30px;">
        <img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHpndW1oNmtiaXp4ZzRndHByNnB4Z3B4Z3B4Z3B4Z3B4Z3B4JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1z/6vIdl6fU4VAFXW6VpS/giphy.gif" width="75">
        <div style="text-align: center; color: #5DADE2; font-family: 'Comic Sans MS';">
            <b style="font-size: 18px;">Rest in the Word</b><br>
            <small>Woodstock is cheering for you!</small>
        </div>
        <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExN2Y0NXR5Ynd3NXA5bmV4am04NTVreHByamZ3Nzh4eHh4eHh4eHh4eCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/vN8S6h7j5C6H3A2sQG/giphy.gif" width="50">
    </div>
    """, unsafe_allow_html=True)
    
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

with tabs[3]:
    import json
    import pandas as pd
    import streamlit as st
    import os
    import re
    import google.generativeai as genai

    # --- 1. 工具函數 (不省略，確保清理與調用穩定) ---
    def clean_json_response(text):
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx >= 0 and end_idx >= 0:
            return text[start_idx:end_idx+1]
        return text

    def analyze_with_gemini(text, prompt_template, api_key):
        genai.configure(api_key=api_key)
        # 解決 404 的雙重模型路徑檢查
        candidate_models = ['gemini-1.5-flash', 'models/gemini-1.5-flash']
        last_error = ""
        for model_name in candidate_models:
            try:
                model = genai.GenerativeModel(model_name)
                full_prompt = prompt_template.replace("[[INPUT_TEXT]]", text[:4000])
                with st.spinner(f"🤖 AI 正在使用 {model_name} 分析中..."):
                    response = model.generate_content(full_prompt)
                    if response and response.text:
                        return True, json.loads(clean_json_response(response.text))
            except Exception as e:
                last_error = str(e)
                continue
        return False, f"API 錯誤: {last_error}"

    # --- 2. 初始化與 UI 標題 ---
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "show_result" not in st.session_state:
        st.session_state.show_result = False

    st.markdown("## 🤖 AI 聖經深度分析控制台")

    api_key_val = os.getenv("GEMINI_API_KEY") or (st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else "")

    if not api_key_val:
        st.error("❌ 找不到 API Key，請檢查設定。")
    else:
        # --- 3. 輸入區塊 (封裝邏輯) ---
        with st.expander("📝 寫作與分析輸入區", expanded=not st.session_state.show_result):
            input_text = st.text_area("貼上經文或英文講稿內容:", height=250, key="ai_input_main")
            
            # 模式選擇
            prompt_options = {
                "chinese_verve": "中文經文深度分析 (V1/V2)",
                "english_manuscript": "英文講稿詞彙分析 (Vocabulary/Phrases)",
                "refine_sermon": "英文講稿精煉 (Full Refinement)"
            }
            mode = st.selectbox("請選擇分析模式:", options=list(prompt_options.keys()), format_func=lambda x: prompt_options[x])
            
            # 按鈕與執行邏輯 (關鍵：在同一個縮排內)
            analyze_btn = st.button("🚀 開始 AI 深度分析", type="primary", use_container_width=True)

            if analyze_btn:
                if input_text:
                    success, result = analyze_with_gemini(input_text, BUILTIN_PROMPTS["default"][mode], api_key_val)
                    if success:
                        st.session_state.analysis_result = result
                        st.session_state.show_result = True
                        st.success("✅ 分析完成！")
                        st.rerun()
                    else:
                        st.error(result)
                else:
                    st.warning("⚠️ 請輸入內容。")

        # --- 4. 結果顯示區塊 (完整恢復) ---
        if st.session_state.show_result and st.session_state.analysis_result:
            data = st.session_state.analysis_result
            st.divider()
            
            # 顯示標題
            st.subheader(f"📋 分析報告: {data.get('ref_no', 'N/A')}")
            
            # 顯示文章內容 (中英)
            if "ref_article" in data:
                with st.container():
                    st.markdown("#### 📄 內容 / 精煉稿")
                    st.info(data["ref_article"])
                    if "ref_article_zh" in data:
                        st.markdown("---")
                        st.write(data["ref_article_zh"])

            # 顯示數據表格
            res_tabs = st.tabs(["📝 重點單字", "💬 重要片語", "📐 文法與重點"])
            
            with res_tabs[0]:
                if data.get("words"):
                    df_words = pd.DataFrame(data["words"])
                    st.dataframe(df_words, use_container_width=True, hide_index=True)
                else: st.info("無單字資料")

            with res_tabs[1]:
                if data.get("phrases"):
                    df_phrases = pd.DataFrame(data["phrases"])
                    st.dataframe(df_phrases, use_container_width=True, hide_index=True)
                else: st.info("無片語資料")

            with res_tabs[2]:
                if data.get("grammar"):
                    for item in data["grammar"]:
                        with st.expander(f"🔹 {item.get('point', '重點')}"):
                            st.write(f"**說明:** {item.get('explanation', '')}")
                            st.write(f"**範例:** {item.get('example', '')}")

            # 功能按鈕
            if st.button("🗑️ 清除分析結果"):
                st.session_state.analysis_result = None
                st.session_state.show_result = False
                st.rerun()
