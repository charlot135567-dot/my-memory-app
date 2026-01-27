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
# 4. TAB2 ─ 月曆待辦（折衷版）
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
    for key in ('cal_key','sel_date','show_del','del_target'):
        if key not in st.session_state:
            st.session_state[key] = 0 if key=='cal_key' else False if key=='show_del' else {}
    if 'todo' not in st.session_state:
        st.session_state.todo = load_todos()

    # 建立未來60天空清單
    today = dt.date.today()
    for i in range(60):
        d = str(today + dt.timedelta(days=i))
        if d not in st.session_state.todo:
            st.session_state.todo[d] = []

    # ---------- 2. Emoji 工具 ----------
    _EMOJI_RE = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+', flags=re.UNICODE)
    def first_emoji(text: str) -> str:
        m = _EMOJI_RE.search(text)
        return m.group(0) if m else ""
    def remove_emoji(text: str) -> str:
        return _EMOJI_RE.sub("", text).strip()

# ---------- 3. 事件來源（只顯示短標題） ----------
def build_events():
    ev = []
    for d, todos in st.session_state.todo.items():
        if not isinstance(todos, list): 
            continue
        
        todos_sorted = sorted(todos, key=lambda x: x.get('time','00:00'))
        
        for t in todos_sorted:
            time_str = t.get('time','00:00:00')

            # ⭐ 月曆只顯示短文字（避免格子爆掉）
            short_title = f"{t.get('emoji','🔔')} {t['title']}"
            if len(short_title) > 20:
                short_title = short_title[:20] + "…"

            start_iso = f"{d}T{time_str}"

            ev.append({
                "title": short_title,   # ← 只給短標題
                "start": start_iso,
                "allDay": False,
                "backgroundColor": "#FFE4E1", 
                "borderColor": "#FFE4E1", 
                "textColor": "#333",

                # 保留完整資料給下方列表用（不動結構）
                "extendedProps": {
                    "type": "todo", 
                    "date": d, 
                    "title": t['title'],
                    "time": time_str,
                    "emoji": t.get("emoji","🔔")
                }
            })
    return ev

    # ---------- 4. CSS 美化（只改文字換行） ----------
    st.markdown("""
    <style>
    .fc-toolbar-title { font-size: 26px; font-weight: 700; color: #3b82f6; letter-spacing: 1px; }
    .fc-day-sat .fc-daygrid-day-number,
    .fc-day-sun .fc-daygrid-day-number { color: #dc2626 !important; font-weight: 600; }
    .fc-event { cursor: pointer; border: none; }
    .fc-event-title { white-space: normal !important; font-size:14px; line-height:1.4; }
    </style>
    """, unsafe_allow_html=True)

    # ---------- 5. 月曆 ----------
    st.subheader("📅 月曆待辦")
    with st.expander("展開 / 折疊月曆視窗", expanded=True):
        calendar_events = build_events()
        calendar_options = {
            "headerToolbar":{"left":"prev,next today","center":"title","right":""},
            "initialView":"dayGridMonth",
            "height":"auto",
            "dateClick": True,
            "eventClick": True,
            "eventDisplay":"block",
            "eventTimeFormat":{"hour":"2-digit","minute":"2-digit","meridiem":False,"hour12":False}
        }
        state = calendar(events=calendar_events, options=calendar_options, key=f"emoji_cal_{st.session_state.cal_key}")

        # 點擊事件 → 彈窗刪除
        if state.get("eventClick"):
            ext = state["eventClick"]["event"]["extendedProps"]
            if ext.get("type")=="todo":
                st.session_state.del_target = ext
                st.session_state.show_del = True
                st.rerun()

        # 點擊日期 → 選擇日期
        if state.get("dateClick"):
            new_date = state["dateClick"]["date"][:10]
            if st.session_state.sel_date != new_date:
                st.session_state.sel_date = new_date
                st.rerun()

    # ---------- 6. 刪除對話框 ----------
    if st.session_state.get("show_del"):
        t = st.session_state.del_target
        st.warning(f"🗑️ 確定刪除待辦「{t.get('title','')}」？")
        c1,c2 = st.columns([1,1])
        with c1:
            if st.button("確認刪除", key="confirm_del"):
                d = t.get("date")
                title_to_del = t.get("title")
                time_to_del = t.get("time")
                if d in st.session_state.todo:
                    st.session_state.todo[d] = [
                        item for item in st.session_state.todo[d]
                        if not (item['title']==title_to_del and item.get('time')==time_to_del)
                    ]
                    if not st.session_state.todo[d]: del st.session_state.todo[d]
                save_todos()
                st.session_state.show_del = False
                st.session_state.cal_key += 1
                st.success("✅ 已刪除！")
                st.rerun()
        with c2:
            if st.button("取消", key="cancel_del"):
                st.session_state.show_del = False
                st.rerun()

    # ---------- 7. 下方列表 ----------
    try:
        base_date = dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date()
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
            sorted_items = sorted(st.session_state.todo[ds], key=lambda x:x.get('time','00:00'))
            for t in sorted_items:
                time_display = t.get('time','00:00')[:5]
                st.write(f"**{date_display} {time_display}** {t.get('emoji','🔔')}{t['title']}")
    if not has_items:
        st.caption("此期間尚無待辦事項")

    # ---------- 8. 新增待辦 ----------
    st.divider()
    with st.expander("➕ 新增待辦", expanded=True):
        ph_emo = "🔔"
        with st.form("todo_form"):
            try:
                default_date = dt.datetime.strptime(st.session_state.sel_date,"%Y-%m-%d").date()
            except:
                default_date = dt.date.today()
            c1,c2,c3 = st.columns([2,2,6])
            with c1: d_input = st.date_input("日期", default_date, label_visibility="collapsed", key="todo_date")
            with c2: tm_input = st.time_input("⏰ 時間", dt.time(9,0), label_visibility="collapsed", key="todo_time")
            with c3: ttl_input = st.text_input("標題", placeholder=f"{ph_emo} Emoji＋待辦", label_visibility="collapsed", key="todo_ttl")
            submitted = st.form_submit_button("💾 儲存", use_container_width=True)
            if submitted:
                if not ttl_input:
                    st.error("請輸入標題")
                else:
                    emo_found = first_emoji(ttl_input) or ph_emo
                    ttl_clean = remove_emoji(ttl_input)
                    k = str(d_input)
                    if k not in st.session_state.todo: st.session_state.todo[k] = []
                    st.session_state.todo[k].append({
                        "title": ttl_clean, "time": str(tm_input), "emoji": emo_found
                    })
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
# 5. TAB4 ─ AI 聖經分析控制台（完整版）
# ===================================================================
with tabs[3]:
    import os, json, datetime as dt, subprocess, sys, re
    import pandas as pd
    import streamlit as st

    # ============================================================
    # 0. 設定與初始化
    # ============================================================
    SENTENCES_FILE = "sentences.json"
    PROMPTS_FILE = "prompts_tab4.json"  # 內建 prompts，避免檔案遺失問題
    
    # 內建 AI Prompts（避免 Prompts.toml 找不到的問題）
    BUILTIN_PROMPTS = {
        "chinese_verse": """你是一位專業的聖經語言學家。請針對以下中文聖經經文，產生結構化學習資料。

經文：{text}

請嚴格按照以下 JSON 格式回傳（不要加 markdown 標記）：

{{
  "ref_no": "聖經縮寫+章節（例：2Ti 4:17-18）",
  "ref_article": "英文經文（ESV版本）",
  "ref_article_zh": "輸入的中文經文",
  
  "v1_data": {{
    "Ref": "聖經縮寫章節",
    "English": "ESV英文經文",
    "Chinese": "中文經文",
    "Syn_Ant": "高級單字/片語的同義反義（中英對照）",
    "Grammar": "文法分析（含補齊句、應用例句）"
  }},
  
  "v2_data": {{
    "Ref": "聖經縮寫章節",
    "口語訳": "日文經文（口語體）",
    "Grammar": "日文文法解析",
    "Note": "文法補充說明",
    "KRF": "韓文經文",
    "Syn_Ant_KR": "韓文高級字彙同義反義",
    "THSV11": "泰文重要片語"
  }},
  
  "words": [
    {{
      "Vocab": "英文單字",
      "Syn_Ant": "同義/反義",
      "Example": "經文中的例句",
      "口語訳": "日文翻譯",
      "KRF": "韓文翻譯", 
      "THSV11": "泰文翻譯"
    }}
  ],
  
  "phrases": [
    {{
      "Phrase": "英文片語",
      "Syn_Ant": "同義/反義",
      "Example": "經文中的例句",
      "口語訳": "日文翻譯",
      "KRF": "韓文翻譯",
      "THSV11": "泰文翻譯"
    }}
  ],
  
  "grammar": [
    {{
      "Rule": "文法規則名稱",
      "Example": "原文例句",
      "解析": "中文文法解析",
      "補齊句": "補充完整句子",
      "應用例": "中英對照應用例句"
    }}
  ]
}}""",

        "english_manuscript": """角色：你是一位精通語言學與聖經解經的教材編輯。
目標：將「口語講道逐字稿」轉化為「精煉的雙語聖經學習教材」。

請針對以下講稿，產出結構化學習數據：

{text}

請嚴格按照以下 JSON 格式回傳（不要加 markdown 標記）：

{{
  "ref_no": "講稿編號（日期+序號，例：2025012701）",
  "ref_article": "純英文精煉稿（Outline 1-5，去除口氣詞，高級詞彙加粗並附中文解釋）",
  "ref_article_zh": "中英夾雜講章（與英文版同步，英文詞彙嵌入括號對照）",
  
  "words": [
    {{
      "Vocab": "高級/中高級單字",
      "Syn_Ant": "同義/反義（中英）",
      "Example": "講稿中的例句",
      "口語訳": "日文翻譯",
      "KRF": "韓文翻譯",
      "THSV11": "泰文翻譯"
    }}
  ],
  
  "phrases": [
    {{
      "Phrase": "高級/中高級片語", 
      "Syn_Ant": "同義/反義（中英）",
      "Example": "講稿中的例句",
      "口語訳": "日文翻譯",
      "KRF": "韓文翻譯",
      "THSV11": "泰文翻譯"
    }}
  ],
  
  "grammar": [
    {{
      "Rule": "文法規則名稱",
      "Example": "原稿範例",
      "解析": "中文文法解析",
      "補齊句": "補齊後的完整句",
      "應用例": "中英對照應用例句"
    }}
  ]
}}

格式要求：
1. 純英文精煉稿與中英夾雜講章要**交錯呈現**（一段英文配一段中英）
2. 禁止使用 HTML 標籤，只用 Markdown 加粗
3. 段落間要有空行
4. 翻譯必須對照聖經原文，禁止自行亂翻"""
    }

    def load_sentences():
        """載入資料庫"""
        if os.path.exists(SENTENCES_FILE):
            try:
                with open(SENTENCES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_sentences():
        """儲存資料庫"""
        try:
            with open(SENTENCES_FILE, "w", encoding="utf-8") as f:
                json.dump(st.session_state.sentences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"存檔失敗：{e}")

    def save_analysis_result(data, input_text, analysis_type):
        """儲存分析歷史"""
        if "analysis_history" not in st.session_state:
            st.session_state.analysis_history = []
        
        record = {
            "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "type": analysis_type,  # "chinese_verse" 或 "english_manuscript"
            "ref_no": data.get("ref_no", ""),
            "input": input_text[:150] + "..." if len(input_text) > 150 else input_text,
            "data": data
        }
        st.session_state.analysis_history.append(record)

    # ============================================================
    # 1. 初始化 Session State
    # ============================================================
    if 'sentences' not in st.session_state:
        st.session_state.sentences = load_sentences()
    if 'show_result' not in st.session_state:
        st.session_state.show_result = False
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None

    # ============================================================
    # 2. AI 分析函數
    # ============================================================
    def detect_language(text):
        """偵測輸入語言"""
        chinese_chars = sum(1 for c in text[:200] if '\u4e00' <= c <= '\u9fff')
        return "chinese" if chinese_chars > 10 else "english"

    def call_gemini_api(prompt, api_key):
        """呼叫 Gemini API"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            response = model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.2,
                    'max_output_tokens': 8192,
                }
            )
            
            # 清理回應
            text = response.text
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            return text.strip()
            
        except Exception as e:
            st.error(f"Gemini API 錯誤：{e}")
            return None

    def analyze_with_ai(text, analysis_type, api_key):
        """執行 AI 分析"""
        prompt_template = BUILTIN_PROMPTS.get(analysis_type, BUILTIN_PROMPTS["english_manuscript"])
        prompt = prompt_template.format(text=text[:4000])  # 限制長度
        
        response_text = call_gemini_api(prompt, api_key)
        
        if not response_text:
            return None
        
        try:
            data = json.loads(response_text)
            
            # 確保必要欄位存在
            required_fields = ["ref_no", "ref_article", "words", "phrases", "grammar"]
            for field in required_fields:
                if field not in data:
                    if field in ["words", "phrases", "grammar"]:
                        data[field] = []
                    else:
                        data[field] = ""
            
            # 加入時間戳
            data["analyzed_at"] = dt.datetime.now().isoformat()
            data["input_type"] = analysis_type
            
            return data
            
        except json.JSONDecodeError as e:
            st.error(f"JSON 解析錯誤：{e}")
            with st.expander("查看原始回應"):
                st.code(response_text[:1000])
            return None

    def create_fallback_data(text, analysis_type):
        """AI 失敗時的回退資料"""
        ref_no = f"FB{dt.datetime.now().strftime('%Y%m%d%H%M')}"
        
        is_chinese = analysis_type == "chinese_verse"
        
        return {
            "ref_no": ref_no,
            "ref_article": text[:300] + "..." if len(text) > 300 else text,
            "ref_article_zh": "（⚠️ AI 分析失敗，顯示預設資料）" if is_chinese else "",
            "input_type": analysis_type,
            "analyzed_at": dt.datetime.now().isoformat(),
            "words": [
                {"Vocab": "becoming", "Syn_Ant": "fitting / unbecoming", "Example": "Fine speech is not becoming to a fool.", "口語訳": "愚か者にはふさわしくない", "KRF": "어울리지 않는다", "THSV11": "ไม่เหมาะสม"},
                {"Vocab": "rescue", "Syn_Ant": "save / abandon", "Example": "The Lord will rescue me.", "口語訳": "救い出す", "KRF": "구출하다", "THSV11": "ช่วยให้พ้น"},
            ],
            "phrases": [
                {"Phrase": "fine speech", "Syn_Ant": "eloquent words", "Example": "Fine speech is not becoming to a fool.", "口語訳": "美辞麗句", "KRF": "아름다운 말", "THSV11": "วาจางาม"},
            ],
            "grammar": [
                {"Rule": "becoming to + N", "Example": "Fine speech is not becoming to a fool.", "解析": "『相稱』義形容詞片語", "補齊句": "Honesty is becoming to a leader.", "應用例": "Humility is becoming to us."},
            ],
            "is_fallback": True
        }

    # ============================================================
    # 3. UI 介面
    # ============================================================
    
    # 檢查 API Key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("KIMI_API_KEY")
    
    st.markdown("## 🤖 AI 聖經分析控制台")
    
    if not api_key:
        st.warning("⚠️ 尚未設定 GEMINI_API_KEY，請在 Streamlit Secrets 設定後重新啟動")
    
    # 主操作區
    with st.expander("📚 分析設定", expanded=True):
        
        # 輸入區
        input_text = st.text_area(
            "貼上經文或講稿（支援中文經文或英文講稿）",
            height=250,
            key="tab4_input",
            placeholder="貼上中文聖經經文或英文講道逐字稿..."
        )
        
        # 自動偵測語言
        detected_lang = detect_language(input_text) if input_text else "unknown"
        
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            analysis_mode = st.radio(
                "分析模式",
                ["自動偵測", "中文經文分析 (V1/V2)", "英文講稿分析 (Words/Phrases)"],
                index=0 if not input_text else (1 if detected_lang == "chinese" else 2)
            )
        
        with col2:
            if input_text:
                st.info(f"偵測到：{'中文' if detected_lang == 'chinese' else '英文'}")
                st.caption(f"字數：{len(input_text)}")
        
        with col3:
            st.write("")
            st.write("")
            analyze_btn = st.button("🤖 開始 AI 分析", type="primary", use_container_width=True)
    
    # 資料庫操作區
    with st.expander("🗄️ 資料庫管理", expanded=False):
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            search_ref = st.text_input("搜尋 Ref.", placeholder="例：2Ti 4:17")
        with col2:
            search_kw = st.text_input("關鍵字搜尋")
        with col3:
            st.write("")
            st.write("")
            if st.button("🔍 搜尋", use_container_width=True):
                # 搜尋邏輯
                results = []
                for k, v in st.session_state.sentences.items():
                    match = False
                    if search_ref and search_ref.lower() in k.lower():
                        match = True
                    if search_kw and search_kw.lower() in str(v).lower():
                        match = True
                    if match:
                        results.append((k, v))
                
                if results:
                    st.session_state["search_results"] = results
                    st.success(f"找到 {len(results)} 筆")
                else:
                    st.info("無符合項目")
        
        # 顯示搜尋結果
        if "search_results" in st.session_state:
            for k, v in st.session_state["search_results"]:
                with st.container():
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{k}**")
                        st.caption(v.get("en", "")[:100] + "...")
                    with c2:
                        if st.button("🗑️ 刪除", key=f"del_{k}"):
                            st.session_state.sentences.pop(k, None)
                            save_sentences()
                            st.rerun()
                    st.divider()
    
    # ============================================================
    # 4. 執行分析
    # ============================================================
    if analyze_btn and input_text:
        # 決定分析類型
        if analysis_mode == "自動偵測":
            analysis_type = "chinese_verse" if detected_lang == "chinese" else "english_manuscript"
        elif "中文" in analysis_mode:
            analysis_type = "chinese_verse"
        else:
            analysis_type = "english_manuscript"
        
        with st.spinner(f"🤖 AI 分析中（{ '中文經文' if analysis_type == 'chinese_verse' else '英文講稿' }）..."):
            
            if api_key:
                result = analyze_with_ai(input_text, analysis_type, api_key)
            else:
                result = None
            
            # 如果 AI 失敗，使用回退資料
            if result is None:
                result = create_fallback_data(input_text, analysis_type)
                st.warning("⚠️ 使用預設資料（請檢查 API Key）")
            
            # 儲存結果
            st.session_state.current_analysis = result
            save_analysis_result(result, input_text, analysis_type)
            
            # 存入資料庫
            ref_no = result["ref_no"]
            st.session_state.sentences[ref_no] = {
                "ref": ref_no,
                "type": analysis_type,
                "en": result.get("ref_article", ""),
                "zh": result.get("ref_article_zh", ""),
                "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "data": result
            }
            save_sentences()
            
            st.session_state.show_result = True
            st.success(f"✅ 分析完成！Ref: `{ref_no}`")
            st.rerun()
    
    # ============================================================
    # 5. 顯示分析結果
    # ============================================================
    if st.session_state.show_result and st.session_state.current_analysis:
        data = st.session_state.current_analysis
        
        st.divider()
        st.markdown(f"## 📋 分析結果：{data['ref_no']}")
        
        if data.get("is_fallback"):
            st.warning("⚠️ 此為預設資料，非 AI 分析結果")
        
        # 操作按鈕
        c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.5, 1.5])
        with c1:
            if st.button("📄 切換原文顯示"):
                st.session_state["show_article"] = not st.session_state.get("show_article", False)
                st.rerun()
        with c2:
            st.code(data['ref_no'])
        with c3:
            if st.button("💾 匯出 JSON"):
                st.download_button(
                    label="下載 JSON",
                    data=json.dumps(data, ensure_ascii=False, indent=2),
                    file_name=f"{data['ref_no']}.json",
                    mime="application/json"
                )
        with c4:
            if st.button("🗑️ 清除結果"):
                st.session_state.show_result = False
                st.session_state.current_analysis = None
                st.rerun()
        
        # 顯示精煉文章
        if st.session_state.get("show_article", False):
            with st.expander("📘 精煉文章", expanded=True):
                tabs = st.tabs(["英文版", "中英對照"] if data.get("ref_article_zh") else ["文章"])
                
                with tabs[0]:
                    st.markdown(data.get("ref_article", "無資料"))
                
                if len(tabs) > 1 and data.get("ref_article_zh"):
                    with tabs[1]:
                        st.markdown(data["ref_article_zh"])
        
        # 資料表格（依分析類型顯示不同欄位）
        if data.get("input_type") == "chinese_verse":
            # 中文經文：顯示 V1/V2 格式
            v1_tab, v2_tab, words_tab, phrases_tab, grammar_tab = st.tabs([
                "📊 V1 (英中對照)", "📊 V2 (日韓泰)", "📝 單字", "💬 片語", "📐 文法"
            ])
            
            with v1_tab:
                if "v1_data" in data:
                    v1 = data["v1_data"]
                    df = pd.DataFrame([v1])
                    st.dataframe(df, use_container_width=True)
                else:
                    # 從 words/phrases/grammar 組合 V1 顯示
                    st.info("V1 資料格式")
            
            with v2_tab:
                if "v2_data" in data:
                    v2 = data["v2_data"]
                    df = pd.DataFrame([v2])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("V2 資料格式")
        else:
            # 英文講稿：直接顯示 Words/Phrases/Grammar
            words_tab, phrases_tab, grammar_tab = st.tabs(["📝 Words 單字", "💬 Phrases 片語", "📐 Grammar 文法"])
        
        # 單字表
        with words_tab:
            words = data.get("words", [])
            if words:
                df = pd.DataFrame(words)
                # 確保欄位順序
                cols = ["Vocab", "Syn_Ant", "Example", "口語訳", "KRF", "THSV11"]
                display_cols = [c for c in cols if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
                st.caption(f"共 {len(words)} 個單字")
            else:
                st.info("無單字資料")
        
        # 片語表
        with phrases_tab:
            phrases = data.get("phrases", [])
            if phrases:
                df = pd.DataFrame(phrases)
                cols = ["Phrase", "Syn_Ant", "Example", "口語訳", "KRF", "THSV11"]
                display_cols = [c for c in cols if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
                st.caption(f"共 {len(phrases)} 個片語")
            else:
                st.info("無片語資料")
        
        # 文法表
        with grammar_tab:
            grammar = data.get("grammar", [])
            if grammar:
                df = pd.DataFrame(grammar)
                # 文法用 table 顯示較清楚
                st.table(df)
                st.caption(f"共 {len(grammar)} 個文法點")
            else:
                st.info("無文法資料")
        
        # 原始資料（除錯用）
        with st.expander("🔧 原始 JSON 資料"):
            st.json(data)
    
    # ============================================================
    # 6. 匯出與管理
    # ============================================================
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.expander("📊 統計資訊"):
            total = len(st.session_state.sentences)
            st.metric("資料庫筆數", total)
            
            types = {}
            for v in st.session_state.sentences.values():
                t = v.get("type", "unknown")
                types[t] = types.get(t, 0) + 1
            
            for t, c in types.items():
                st.caption(f"{t}: {c} 筆")
    
    with col2:
        with st.expander("📋 匯出資料"):
            if st.button("匯出全部 (TSV)"):
                lines = ["Ref\tType\tEnglish\tChinese\tDate"]
                for k, v in st.session_state.sentences.items():
                    line = f"{k}\t{v.get('type','')}\t{v.get('en','')[:50]}\t{v.get('zh','')[:50]}\t{v.get('date_added','')}"
                    lines.append(line)
                st.code("\n".join(lines), language="text")
            
            if st.button("匯出 JSON"):
                st.code(json.dumps(st.session_state.sentences, ensure_ascii=False, indent=2)[:2000] + "...")
    
    with col3:
        with st.expander("⚠️ 危險操作"):
            if st.button("🗑️ 清空資料庫", type="secondary"):
                confirm = st.checkbox("確認刪除全部資料？")
                if confirm:
                    st.session_state.sentences = {}
                    save_sentences()
                    st.success("已清空資料庫")
                    st.rerun()
