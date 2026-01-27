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
# 4. TAB2 ─ 月曆待辦 (解決閃爍、圖片失效、💟 功能與存檔顯示問題)
# ===================================================================
with tabs[1]:
    import datetime as dt, re, os, json

    # ---------- 0. 穩定存儲邏輯 ----------
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

    # ---------- 1. 初始化 (確保 Key 不會消失) ----------
    if 'todo' not in st.session_state: st.session_state.todo = load_todos()
    if 'sel_date' not in st.session_state: st.session_state.sel_date = str(dt.date.today())
    if 'cal_key' not in st.session_state: st.session_state.cal_key = 0
    if 'active_edit_id' not in st.session_state: st.session_state.active_edit_id = None

    # ---------- 2. 工具 ----------
    _EMOJI_RE = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+', flags=re.UNICODE)
    def first_emoji(text: str) -> str:
        m = _EMOJI_RE.search(text)
        return m.group(0) if m else ""

    # ---------- 3. CSS 美化 (含修正圖片失效的替代方案) ----------
    st.markdown("""
    <style>
    .fc-toolbar-title { font-size: 24px !important; color: #5DADE2 !important; font-weight: bold; }
    .fc-event-time { display: none !important; } 
    .fc-event { border: none !important; border-radius: 5px !important; padding: 2px !important; }
    /* 讓按鈕區塊更整齊 */
    .stButton>button { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

    # ---------- 4. 月曆組件 (穩定 Key，防止閃爍) ----------
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
    
    # 使用穩定的 Key 與更新後的事件
    state = calendar(events=build_events(), options=cal_options, key=f"fixed_cal_{st.session_state.cal_key}")

    if state.get("dateClick"):
        st.session_state.sel_date = state["dateClick"]["date"][:10]
        st.rerun()

    # ---------- 5. 💟 功能回歸：詳細清單預覽 ----------
    st.divider()
    try:
        base_date = dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date()
    except:
        base_date = dt.date.today()

    st.markdown(f"##### 📋 {st.session_state.sel_date} 起三日預覽")

    for offset in range(3):
        d_obj = base_date + dt.timedelta(days=offset)
        d_str = str(d_obj)
        if d_str in st.session_state.todo and st.session_state.todo[d_str]:
            for idx, item in enumerate(st.session_state.todo[d_str]):
                item_id = f"{d_str}_{idx}"
                col_h, col_t, col_a = st.columns([1, 7, 3])
                
                with col_h:
                    # 💟 點擊後記錄該項目 ID
                    if st.button("💟", key=f"h_{item_id}"):
                        st.session_state.active_edit_id = item_id if st.session_state.active_edit_id != item_id else None
                        st.rerun()
                
                with col_t:
                    st.write(f"**{item['time'][:5]}** {item.get('emoji','')} {item['title']}")
                
                # 若為選中項目，顯示編輯與刪除
                if st.session_state.active_edit_id == item_id:
                    with col_a:
                        ce, cd = st.columns(2)
                        if ce.button("✏️", key=f"e_{item_id}"):
                            st.toast("💡 修改：請至下方新增後刪除此項")
                        if cd.button("🗑️", key=f"d_{item_id}"):
                            st.session_state.todo[d_str].pop(idx)
                            save_todos()
                            st.session_state.cal_key += 1 # 強制更新月曆
                            st.session_state.active_edit_id = None
                            st.rerun()

    # ---------- 6. 新增事項 ----------
    with st.expander("➕ 新增事項", expanded=False):
        with st.form("new_form", clear_on_submit=True):
            in_name = st.text_input("待辦內容")
            in_time = st.time_input("時間", dt.time(9, 0))
            if st.form_submit_button("儲存項目"):
                if in_name:
                    k = st.session_state.sel_date
                    if k not in st.session_state.todo: st.session_state.todo[k] = []
                    st.session_state.todo[k].append({
                        "title": in_name, "time": str(in_time), "emoji": first_emoji(in_name) or "📌"
                    })
                    save_todos()
                    st.session_state.cal_key += 1 # 關鍵：確保儲存後月曆立即更新
                    st.rerun()

    # ---------- 7. 史努比底部美化 (修復失效連結) ----------
    st.markdown("---")
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; gap: 30px;">
        <img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHpndW1oNmtiaXp4ZzRndHByNnB4Z3B4Z3B4Z3B4Z3B4Z3B4JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1z/6vIdl6fU4VAFXW6VpS/giphy.gif" width="70">
        <div style="text-align: center; color: #5DADE2;">
            <b style="font-size: 18px;">Rest in the Word</b><br>
            <small>Snoopy is reading with you...</small>
        </div>
        <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExN2Y0NXR5Ynd3NXA5bmV4am04NTVreHByamZ3Nzh4eHh4eHh4eHh4eCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/vN8S6h7j5C6H3A2sQG/giphy.gif" width="50">
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

# ===================================================================
# 5. TAB4 ─ AI 聖經分析控制台（修正版）
# ===================================================================
with tabs[3]:
    import json
    import datetime as dt
    import pandas as pd
    import streamlit as st
    import os
    import re
    import traceback

    # ============================================================
    # 0. 內建 Prompts（注意：{} 會被誤認，要用其他方式替換）
    # ============================================================
    BUILTIN_PROMPTS = {
        "default": {
            "chinese_verve": """你是一位專業的聖經語言學家。請針對以下中文聖經經文，產生結構化學習資料。

經文：[[INPUT_TEXT]]

請嚴格按照以下 JSON 格式回傳（不要加 markdown 標記）：

{
  "ref_no": "聖經縮寫+章節（例：2Ti 4:17-18）",
  "ref_article": "英文經文（ESV版本）",
  "words": [
    {
      "Vocab": "英文單字",
      "Syn_Ant": "同義/反義（中英）",
      "Example": "經文中的例句",
      "口語訳": "日文翻譯",
      "KRF": "韓文翻譯",
      "THSV11": "泰文翻譯"
    }
  ],
  "phrases": [
    {
      "Phrase": "英文片語",
      "Syn_Ant": "同義/反義（中英）",
      "Example": "經文中的例句",
      "口語訳": "日文翻譯",
      "KRF": "韓文翻譯",
      "THSV11": "泰文翻譯"
    }
  ],
  "grammar": [
    {
      "Rule": "文法規則名稱",
      "Example": "原文例句",
      "解析": "中文文法解析",
      "補齊句": "補充完整句子",
      "應用例": "中英對照應用例句"
    }
  ]
}""",

            "english_manuscript": """請針對以下英文講稿產生三個 JSON Array：
1) words：高階單字 + 中英日韓泰對照 + 例句；
2) phrases：高階片語 + 同上；
3) grammar：重要文法點 + 解析 + 應用例句。
輸出純 JSON，勿加 Markdown 程式碼框。
講稿：[[INPUT_TEXT]]""",

            "refine_sermon": """角色：你是一位精通語言學與聖經解經的教材編輯。
目標：將「口語講道逐字稿」轉化為「精煉的雙語聖經學習教材」。

請針對以下講稿，產出結構化學習數據：

[[INPUT_TEXT]]

請嚴格按照以下 JSON 格式回傳（不要加 markdown 標記）：

{
  "ref_no": "講稿編號（日期+序號）",
  "ref_article": "純英文精煉稿（Outline 1-5）",
  "ref_article_zh": "中英夾雜講章",
  "words": [...],
  "phrases": [...],
  "grammar": [...]
}"""
        }
    }

    # ============================================================
    # 1. 輔助函數
    # ============================================================
    def create_fallback_data(text, prompt_type):
        """產生預設資料"""
        return {
            "ref_no": f"FB{dt.datetime.now().strftime('%Y%m%d%H%M')}",
            "ref_article": text[:200],
            "is_fallback": True,
            "words": [
                {"Vocab": "becoming", "Syn_Ant": "fitting", "Example": "Fine speech is not becoming to a fool.", "口語訳": "愚か者にはふさわしくない", "KRF": "어울리지 않는다", "THSV11": "ไม่เหมาะสม"},
                {"Vocab": "rescue", "Syn_Ant": "save", "Example": "The Lord will rescue me.", "口語訳": "救い出す", "KRF": "구출하다", "THSV11": "ช่วยให้พ้น"}
            ],
            "phrases": [
                {"Phrase": "fine speech", "Syn_Ant": "eloquent words", "Example": "Fine speech is not becoming to a fool.", "口語訳": "美辞麗句", "KRF": "아름다운 말", "THSV11": "วาจางาม"}
            ],
            "grammar": [
                {"Rule": "becoming to + N", "Example": "Fine speech is not becoming to a fool.", "解析": "『相稱』義形容詞片語", "補齊句": "Honesty is becoming to a leader.", "應用例": "Humility is becoming to us."}
            ]
        }

    def clean_json_response(text):
        """清理 AI 回傳的 JSON"""
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        start_idx = text.find('{')
        if start_idx > 0:
            text = text[start_idx:]
        end_idx = text.rfind('}')
        if end_idx > 0:
            text = text[:end_idx+1]
        return text

def analyze_with_gemini(text, prompt_template, api_key):
    """呼叫 Gemini API"""
    response_text = None
    
    try:
        import google.generativeai as genai
        
        # 設定 API
        genai.configure(api_key=api_key)
        
        # 🔍 檢查可用模型（除錯用）
        try:
            models = genai.list_models()
            available = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            st.sidebar.write(f"✅ 可用模型: {available[:3]}")  # 顯示前3個
        except Exception as e:
            st.sidebar.write(f"⚠️ 無法列出模型: {e}")
        
        # 🔧 使用最新模型名稱
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        prompt = prompt_template.replace("[[INPUT_TEXT]]", text[:3000])
        
        with st.spinner("🤖 正在呼叫 Gemini API..."):
            response = model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.2,
                    'max_output_tokens': 8192,
                }
            )
        
        response_text = response.text
        cleaned_text = clean_json_response(response_text)
        data = json.loads(cleaned_text)
        return True, data
        
    except Exception as e:
        error_msg = f"錯誤: {str(e)}\n\n"
        error_msg += f"追蹤:\n{traceback.format_exc()}\n\n"
        if response_text:
            error_msg += f"原始回應前300字:\n{response_text[:300]}"
        else:
            error_msg += "無原始回應"
        return False, error_msg

    # ============================================================
    # 2. UI 介面
    # ============================================================
    st.markdown("## 🤖 AI 聖經分析控制台")
    
    api_key = os.getenv("GEMINI_API_KEY")
    
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
        
        selected_prompt = st.selectbox(
            "選擇分析模式",
            options=list(prompt_options.keys()),
            format_func=lambda x: prompt_options[x],
            index=0 if is_chinese else 2
        )
        
        analyze_btn = st.button("🤖 開始 AI 分析", type="primary")

    # ============================================================
    # 3. 執行分析
    # ============================================================
    if analyze_btn and input_text:
        prompt_template = BUILTIN_PROMPTS["default"][selected_prompt]
        
        success, result = analyze_with_gemini(input_text, prompt_template, api_key)
        
        if success:
            st.session_state["analysis_result"] = result
            st.session_state["show_result"] = True
            st.success(f"✅ 分析完成！Ref: {result.get('ref_no', 'N/A')}")
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
        
        if data.get("ref_article"):
            with st.expander("📄 精煉文章"):
                st.markdown(data["ref_article"])
                if data.get("ref_article_zh"):
                    st.markdown("---")
                    st.markdown(data["ref_article_zh"])
        
        col1, col2, col3 = st.tabs(["📝 單字", "💬 片語", "📐 文法"])
        
        with col1:
            words = data.get("words", [])
            if words:
                df = pd.DataFrame(words)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"共 {len(words)} 個單字")
            else:
                st.info("無單字資料")
        
        with col2:
            phrases = data.get("phrases", [])
            if phrases:
                df = pd.DataFrame(phrases)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"共 {len(phrases)} 個片語")
            else:
                st.info("無片語資料")
        
        with col3:
            grammar = data.get("grammar", [])
            if grammar:
                df = pd.DataFrame(grammar)
                st.table(df)
                st.caption(f"共 {len(grammar)} 個文法點")
            else:
                st.info("無文法資料")
        
        if st.button("🗑️ 清除結果"):
            st.session_state["show_result"] = False
            st.session_state["analysis_result"] = None
            st.rerun()
