#===================================================================
# 0. 套件 & 全域函式（一定放最頂）
# ===================================================================
import streamlit as st
import subprocess, sys, os, datetime as dt, pandas as pd, io, json, re, tomli, tomli_w
# 確保有裝 streamlit-calendar
from streamlit_calendar import calendar

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
# 4. TAB2 ─ 靈修足跡月曆（格式與顯示優化版）
# ===================================================================
with tabs[1]:
    import datetime as dt, re, os, json

    # ---------- 0. 檔案持久化工具 ----------
    TODO_FILE = "todos.json"
    
    def load_todos():
        """網頁載入時從檔案讀取待辦"""
        if os.path.exists(TODO_FILE):
            try:
                with open(TODO_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_todos():
        """每次改動立刻存檔（自動清理 60 天前舊資料）"""
        cutoff = str(dt.date.today() - dt.timedelta(days=60))
        keys_to_remove = [k for k in st.session_state.todo.keys() if k < cutoff]
        for k in keys_to_remove:
            del st.session_state.todo[k]
        
        with open(TODO_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.todo, f, ensure_ascii=False, indent=2)

    # ---------- 1. 初值與自動讀檔 ----------
    for key in ('cal_key', 'sel_date', 'show_del', 'del_target'):
        if key not in st.session_state:
            if key == 'cal_key': st.session_state[key] = 0
            elif key == 'sel_date': st.session_state[key] = str(dt.date.today())
            elif key == 'show_del': st.session_state[key] = False
            elif key == 'del_target': st.session_state[key] = {}
    
    if 'todo' not in st.session_state:
        st.session_state.todo = load_todos()
    
    # 預先建立未來 60 天的空清單
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

    # ---------- 3. 事件來源（修正時間顯示） ----------
    def build_events():
        ev = []
        for d, todos in st.session_state.todo.items():
            if not isinstance(todos, list): continue
            
            # 依時間排序
            todos_sorted = sorted(todos, key=lambda x: x.get('time', '00:00'))
            
            for idx, t in enumerate(todos_sorted):
                time_str = t.get('time', '00:00:00')
                
                # [修改點 1] 標題不再包含時間字串，只保留 Emoji + 標題
                # 時間將由月曆系統自動顯示在最前面
                display_title = f"{t.get('emoji','🔔')} {t['title']}".strip()
                
                # 組合 ISO 時間格式
                start_iso = f"{d}T{time_str}"
                
                ev.append({
                    "title": display_title,
                    "start": start_iso,
                    "allDay": False,
                    "backgroundColor": "#FFE4E1", 
                    "borderColor": "#FFE4E1", 
                    "textColor": "#333",
                    "extendedProps": {
                        "type": "todo", 
                        "date": d, 
                        "title": t['title'],
                        "time": time_str
                    }
                })
        return ev

   # ---------- 4. 美化 CSS（讓格子自動長高 + 換行） ----------
st.markdown(f"""
<style>
.fc-toolbar-title {{ font-size: 26px; font-weight: 700; color: #3b82f6; letter-spacing: 1px; }}
.fc-day-sat .fc-daygrid-day-number,
.fc-day-sun .fc-daygrid-day-number {{ color: #dc2626 !important; font-weight: 600; }}
.fc-event {{ cursor: pointer; border: none; }} 

/* 允許文字換行 + 自動撐高格子 */
.fc-event-title {{
    white-space: normal !important; /* 允許換行 */
    overflow: visible !important;   /* 顯示完整內容 */
    font-size: 14px;
    line-height: 1.4;
}}
.fc-daygrid-event {{
    white-space: normal !important;
    align-items: flex-start !important;
}}
.fc-daygrid-day-frame {{
    height: auto !important;
}}
.fc-daygrid-day-events {{
    height: auto !important;
    max-height: none !important;
    overflow: visible !important;
}}
</style>
""", unsafe_allow_html=True)

# ---------- 5. 月曆本體 ----------
calendar_events = build_events()

calendar_options = {
    "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
    "initialView": "dayGridMonth",
    "height": "auto", # 月曆自動撐高
    "dateClick": True,
    "eventClick": True,
    "eventDisplay": "block",
    "eventTimeFormat": {
        "hour": "2-digit",
        "minute": "2-digit",
        "meridiem": False,
        "hour12": False
    }
}

state = calendar(
    events=calendar_events,
    options=calendar_options,
    key=f"emoji_cal_{st.session_state.cal_key}"
)

# ---------- 6. 點擊事件處理（彈窗刪除） ----------
if state.get("eventClick"):
    ext = state["eventClick"]["event"]["extendedProps"]
    if ext.get("type") == "todo":
        # 設置刪除目標並打開刪除彈窗
        st.session_state.del_target = ext
        st.session_state.show_del = True
        st.rerun()

# ---------- 7. 刪除對話框 ----------
if st.session_state.get("show_del"):
    t = st.session_state.del_target
    st.warning(f"🗑️ 確定刪除待辦「{t.get('title','')}」？")
    c1, c2 = st.columns([1, 1])
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

    # ---------- 8. 待辦列表（格式優化） ----------
    # [修改點 3] 依照您的需求調整下方顯示格式：1/27 10:30 📕標題
    try:
        base_date = dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date()
    except:
        base_date = dt.date.today()

    st.markdown("##### 📋 詳細列表")
    has_items = False
    
    # 顯示選取日期及未來 2 天
    for i in range(3):
        dd = base_date + dt.timedelta(days=i)
        ds = str(dd)
        
        if ds in st.session_state.todo and st.session_state.todo[ds]:
            has_items = True
            # 格式化日期：1/27
            date_display = f"{dd.month}/{dd.day}"
            
            # 排序
            sorted_items = sorted(st.session_state.todo[ds], key=lambda x: x.get('time', '00:00'))
            
            for t in sorted_items:
                # 格式化時間：只取 HH:MM (例如 10:30)
                time_raw = t.get('time', '00:00:00')
                time_display = time_raw[:5] 
                
                # 組合字串
                full_text = f"**{date_display} {time_display}** {t.get('emoji', '🔔')}{t['title']}"
                st.write(full_text)
                
    if not has_items:
        st.caption("此期間尚無待辦事項")
    
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
# 5. TAB4 ─ AI 控制台（零循環 + 永久存檔 + 輸入生效）
# ===================================================================
with tabs[3]:
    import os, subprocess, sys, pandas as pd, io, json

    # ---------- 0. 資料庫持久化工具 ----------
    SENTENCES_FILE = "sentences.json"
    
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
        """存檔資料庫"""
        with open(SENTENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.sentences, f, ensure_ascii=False, indent=2)

    # ---------- 1. 初值與自動讀檔 ----------
    if 'sentences' not in st.session_state:
        st.session_state.sentences = load_sentences()

    API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("KIMI_API_KEY")
    if not API_KEY:
        st.warning("⚠️ 尚未設定 GEMINI_API_KEY 或 KIMI_API_KEY，請至 Streamlit-Secrets 加入金鑰後重新啟動。")
        st.stop()

    with st.expander("📚① 貼經文/講稿 → ② 一鍵分析 → ③ 直接檢視 → ④ 離線使用", expanded=True):
        input_text = st.text_area("", height=300, key="input_text")

        # -------------- 布局：操作 + 輸入框 + AI 分析鍵（獨立） + 巨量刪除靠右 --------------
        col1, col2, col3, col4 = st.columns([2.5, 3.5, 2, 2])
        
        with col1:
            search_type = st.selectbox("操作", ["AI 分析", "Ref. 刪除", "關鍵字刪除"])
        
        with col2:
            query_box = None
            if search_type == "Ref. 刪除":
                query_box = st.text_input("輸入 Ref.（例：2Ti 3:10）", key="ref_del")
            elif search_type == "關鍵字刪除":
                query_box = st.text_input("輸入關鍵字", key="kw_del")
            else:
                st.empty()  # 保持高度一致
        
        with col3:
            # AI 分析鍵：獨立運作
            if st.button("🤖 AI 分析", type="primary", key="ai_analyze_btn"):
                if not input_text:
                    st.error("請先貼經文")
                    st.stop()
                if search_type != "AI 分析":
                    st.warning("請先選擇「AI 分析」操作")
                    st.stop()
                with st.spinner("AI 分析中，約 10 秒…"):
                    try:
                        subprocess.run([sys.executable, "analyze_to_excel.py", "--file", "temp_input.txt"],
                                       check=True, timeout=30)
                        with open("temp_result.json", "r", encoding="utf-8") as f:
                            data = json.load(f)
                        save_analysis_result(data, input_text)
                        st.session_state["analysis"] = data
                        
                        # 自動存入資料庫（sentences）
                        ref_no = data.get("ref_no", "")
                        st.session_state.sentences[ref_no] = {
                            "ref": ref_no,
                            "en": data.get("ref_article", ""),
                            "zh": "",
                            "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        save_sentences()  # 存檔
                        
                        st.success("分析完成！已存入資料庫")
                        current_count = len(st.session_state.get("analysis_history", []))
                        if current_count >= 800:
                            st.warning("🔔 分析紀錄已達 800 筆，建議使用「壓縮舊紀錄」功能，避免瀏覽器卡頓！")
                        if st.checkbox("分析完自動展開", value=True):
                            st.session_state["show_result"] = True
                    except Exception as e:
                        st.error(f"分析過程錯誤：{e}")
        
        with col4:
            st.write("")  # 對齊留白
            # 巨量刪除鍵：靠右對齊
            if search_type in ["Ref. 刪除", "關鍵字刪除"]:
                if st.button("🗑️ 巨量刪除", type="primary", key="bulk_delete_btn"):
                    if query_box is None or not query_box.strip():
                        st.error("請先輸入刪除條件")
                        st.stop()
                    hits = []
                    for d, v in st.session_state.sentences.items():
                        txt = f"{v.get('ref', '')} {v.get('en', '')} {v.get('zh', '')}".lower()
                        if search_type == "Ref. 刪除" and query_box.lower() in v.get('ref', '').lower():
                            hits.append((d, v))
                        elif search_type == "關鍵字刪除" and query_box.lower() in txt:
                            hits.append((d, v))
                    if hits:
                        st.write(f"共 {len(hits)} 筆（含聖經經節）")
                        selected_keys = st.multiselect("勾選要刪除的項目", [d for d, _ in hits])
                        if st.button("確認刪除", type="secondary"):
                            for k in selected_keys:
                                st.session_state.sentences.pop(k, None)
                            save_sentences()  # 刪除後存檔
                            st.success(f"已刪除 {len(selected_keys)} 筆！")
                    else:
                        st.info("無符合條件")

    # ---------- 2. 結果呈現 ----------
    if st.session_state.get("show_result", False):
        data = st.session_state["analysis"]
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
                st.code(ref_no)
            else:
                st.text("尚無 Ref.")

        if st.session_state.get("show_article", False):
            with st.expander("📘 中英精煉文章", expanded=True):
                st.markdown(st.session_state["ref_article"])

        col_w, col_p, col_g = st.tabs(["單字", "片語", "文法"])
        with col_w:
            if data.get("words"):
                df = pd.DataFrame(data["words"])
                df.insert(0, "Ref.", data.get("ref_no", ""))
                df["🔍"] = "🔍"
                st.dataframe(df, use_container_width=True)
            else:
                st.info("本次無單字分析")
        with col_p:
            if data.get("phrases"):
                df = pd.DataFrame(data["phrases"])
                df.insert(0, "Ref.", data.get("ref_no", ""))
                df["🔍"] = "🔍"
                st.dataframe(df, use_container_width=True)
            else:
                st.info("本次無片語分析")
        with col_g:
            if data.get("grammar"):
                df = pd.DataFrame(data["grammar"])
                df.insert(0, "Ref.", data.get("ref_no", ""))
                df["🔍"] = "🔍"
                st.table(df)
            else:
                st.info("本次無文法點")

    # ---------- 3. 容量管理 ----------
    with st.expander("⚙️ 容量管理", expanded=True):
        max_keep = st.number_input("最多保留最近幾筆分析紀錄", min_value=10, max_value=1000, value=50)
        if st.button("✂️ 壓縮舊紀錄"):
            hist = st.session_state.get("analysis_history", [])
            if len(hist) > max_keep:
                st.session_state.analysis_history = hist[-max_keep:]
                st.success(f"已壓縮至最近 {max_keep} 筆！")
            else:
                st.info("未達壓縮門檻")

    # ---------- 4. 匯出 ----------
    if st.button("📋 匯出含回溯欄位"):
        export = []
        for k, v in st.session_state.sentences.items():
            export.append(f"{k}\t{v.get('ref', '')}\t{v.get('en', '')}\t{v.get('zh', '')}")
        st.code("\n".join(export), language="text")
