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
# 4. TAB2 ─ 月曆待辦（保持原邏輯 + 換行 + 刪除）
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
    for key in ('cal_key', 'sel_date', 'show_del', 'del_target'):
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

    # ---------- 3. 事件來源 ----------
    def build_events():
        ev = []
        for d, todos in st.session_state.todo.items():
            if not isinstance(todos, list): continue
            todos_sorted = sorted(todos, key=lambda x: x.get('time','00:00'))
            for t in todos_sorted:
                time_str = t.get('time','00:00:00')
                display_title = f"{t.get('emoji','🔔')} {t['title']}".strip()
                start_iso = f"{d}T{time_str}"
                ev.append({
                    "title": display_title,
                    "start": start_iso,
                    "allDay": False,
                    "backgroundColor": "#FFE4E1",
                    "borderColor": "#FFE4E1",
                    "textColor": "#333",
                    "extendedProps":{
                        "type":"todo",
                        "date": d,
                        "title": t['title'],
                        "time": time_str
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
    .fc-event-title {
        white-space: normal !important;  /* 換行 */
        font-size: 14px;
        line-height: 1.4;
    }
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
# 5. TAB4 ─ AI 控制台（零循環 + 永久存檔 + 輸入生效）
# ===================================================================
with tabs[3]:
    import os, json, datetime as dt, subprocess, sys
    import pandas as pd

    # ---------- 0. 資料庫持久化工具 ----------
    SENTENCES_FILE = "sentences.json"
    
    def load_sentences():
        if os.path.exists(SENTENCES_FILE):
            try:
                with open(SENTENCES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"讀取資料庫失敗：{e}")
        return {}
    
    def save_sentences():
        try:
            with open(SENTENCES_FILE, "w", encoding="utf-8") as f:
                json.dump(st.session_state.sentences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"存檔失敗：{e}")

    def save_analysis_result(data, input_text):
        if "analysis_history" not in st.session_state:
            st.session_state.analysis_history = []
        record = {
            "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ref_no": data.get("ref_no", ""),
            "input": input_text[:100] + "..." if len(input_text) > 100 else input_text,
            "data": data
        }
        st.session_state.analysis_history.append(record)

    # ---------- 1. 初值與自動讀檔 ----------
    if 'sentences' not in st.session_state:
        st.session_state.sentences = load_sentences()

    # 檢查環境
    API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("KIMI_API_KEY")
    has_prompts = os.path.exists("Prompts.toml")
    
    if not API_KEY:
        st.warning("⚠️ 尚未設定 GEMINI_API_KEY，將使用預設假資料。")
    if not has_prompts:
        st.warning("⚠️ 找不到 Prompts.toml，將使用預設假資料。")

    with st.expander("📚① 貼經文/講稿 → ② 一鍵分析 → ③ 直接檢視 → ④ 離線使用", expanded=True):
        input_text = st.text_area(
            "在此貼上經文或講稿（支援中文或英文）", 
            height=300, 
            key="input_text",
            placeholder="貼上聖經經文或講稿內容..."
        )

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
                st.empty()
        
        with col3:
            analyze_clicked = st.button("🤖 AI 分析", type="primary", key="ai_analyze_btn")
        
        with col4:
            st.write("")
            if search_type in ["Ref. 刪除", "關鍵字刪除"]:
                st.button("🗑️ 巨量刪除", type="primary", key="bulk_delete_btn")

        # 處理 AI 分析
        if analyze_clicked:
            if not input_text or not input_text.strip():
                st.error("請先貼上經文內容")
                st.stop()
            if search_type != "AI 分析":
                st.warning("請先選擇「AI 分析」操作")
                st.stop()
            
            with st.spinner("🔄 AI 分析中，請稍候…"):
                try:
                    # 寫入輸入檔
                    with open("temp_input.txt", "w", encoding="utf-8") as f:
                        f.write(input_text)
                    
                    # 執行分析腳本
                    result = subprocess.run(
                        [sys.executable, "analyze_to_excel.py", "--file", "temp_input.txt"],
                        capture_output=True,
                        text=True,
                        timeout=120  # 給多一點時間給 AI
                    )
                    
                    # 顯示腳本輸出（除錯用）
                    if result.stderr:
                        with st.expander("📝 分析過程記錄"):
                            st.text(result.stderr)
                    
                    if result.returncode != 0:
                        st.error(f"分析腳本執行失敗：{result.stderr}")
                        st.stop()
                    
                    # 讀取結果
                    if not os.path.exists("temp_result.json"):
                        st.error("找不到分析結果檔案")
                        st.stop()
                    
                    with open("temp_result.json", "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # 驗證結果
                    if not isinstance(data, dict):
                        st.error(f"結果格式錯誤：{type(data)}")
                        st.stop()
                    
                    if "ref_no" not in data:
                        st.error("結果缺少 ref_no 欄位")
                        st.json(data)
                        st.stop()
                    
                    # 儲存結果
                    save_analysis_result(data, input_text)
                    st.session_state["analysis"] = data
                    st.session_state["analysis_input"] = input_text
                    
                    # 存入資料庫
                    ref_no = data["ref_no"]
                    st.session_state.sentences[ref_no] = {
                        "ref": ref_no,
                        "en": data.get("ref_article", ""),
                        "zh": data.get("ref_article_zh", ""),
                        "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    save_sentences()
                    
                    st.success(f"✅ 分析完成！Ref: `{ref_no}`")
                    
                    # 顯示統計
                    w_count = len(data.get("words", []))
                    p_count = len(data.get("phrases", []))
                    g_count = len(data.get("grammar", []))
                    st.caption(f"📊 產出：{w_count} 單字 / {p_count} 片語 / {g_count} 文法點")
                    
                    # 檢查紀錄數
                    current_count = len(st.session_state.get("analysis_history", []))
                    if current_count >= 800:
                        st.warning("🔔 分析紀錄已達 800 筆，建議壓縮舊紀錄！")
                    
                    st.session_state["show_result"] = True
                    st.rerun()
                    
                except subprocess.TimeoutExpired:
                    st.error("⏱️ 分析超時，請稍後再試或縮短輸入內容")
                except Exception as e:
                    st.error(f"❌ 分析過程錯誤：{str(e)}")
                    import traceback
                    with st.expander("詳細錯誤資訊"):
                        st.code(traceback.format_exc())

        # 處理巨量刪除
        elif search_type in ["Ref. 刪除", "關鍵字刪除"]:
            if st.session_state.get("bulk_delete_btn"):
                if not query_box or not query_box.strip():
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
                    st.write(f"找到 **{len(hits)}** 筆符合項目")
                    selected = st.multiselect(
                        "勾選要刪除的項目", 
                        options=[d for d, _ in hits],
                        format_func=lambda x: f"{x}: {st.session_state.sentences[x].get('ref', '')[:50]}..."
                    )
                    if selected and st.button("⚠️ 確認刪除", type="secondary"):
                        for k in selected:
                            st.session_state.sentences.pop(k, None)
                        save_sentences()
                        st.success(f"已刪除 {len(selected)} 筆！")
                        st.rerun()
                else:
                    st.info("無符合條件的項目")

    # ---------- 2. 結果呈現 ----------
    if st.session_state.get("show_result", False) and "analysis" in st.session_state:
        data = st.session_state["analysis"]
        ref_no = data.get("ref_no", "尚無 Ref.")
        
        st.divider()
        st.markdown(f"### 📋 Ref. No. `{ref_no}`")
        
        c1, c2, c3 = st.columns([2, 2, 4])
        with c1:
            if st.button("📄 檢視原文", key="toggle_article"):
                st.session_state["show_article"] = not st.session_state.get("show_article", False)
                st.rerun()
        with c2:
            st.code(ref_no, language="text")
        with c3:
            if st.button("🔄 重新分析", key="reanalyze"):
                st.session_state["show_result"] = False
                st.rerun()
        
        # 顯示原文
        if st.session_state.get("show_article", False):
            with st.expander("📘 精煉文章", expanded=True):
                article = data.get("ref_article", "無資料")
                # 處理可能的 markdown
                st.markdown(article)
                
                if data.get("ref_article_zh"):
                    st.markdown("---")
                    st.markdown("**中文版本：**")
                    st.markdown(data["ref_article_zh"])

        # 三個分頁
        w_tab, p_tab, g_tab = st.tabs(["📝 單字", "💬 片語", "📐 文法"])
        
        def display_dataframe(tab, data_list, columns_mapping):
            with tab:
                if data_list and len(data_list) > 0:
                    df = pd.DataFrame(data_list)
                    # 確保必要欄位存在
                    for col in columns_mapping:
                        if col not in df.columns:
                            df[col] = ""
                    
                    # 重新排序欄位
                    display_cols = ["Ref."] + columns_mapping + (["🔍"] if "🔍" not in df.columns else [])
                    df.insert(0, "Ref.", ref_no)
                    if "🔍" not in df.columns:
                        df["🔍"] = "🔍"
                    
                    st.dataframe(
                        df[[c for c in display_cols if c in df.columns]], 
                        use_container_width=True,
                        hide_index=True
                    )
                    st.caption(f"共 {len(data_list)} 項")
                else:
                    st.info("本次無資料")
        
        # 單字欄位
        display_dataframe(
            w_tab, 
            data.get("words", []),
            ["Vocab", "Syn / Ant", "Example", "口語訳", "KRF", "THSV11"]
        )
        
        # 片語欄位
        display_dataframe(
            p_tab,
            data.get("phrases", []),
            ["Phrase", "Syn / Ant", "Example", "口語訳", "KRF", "THSV11"]
        )
        
        # 文法欄位
        with g_tab:
            grammar = data.get("grammar", [])
            if grammar and len(grammar) > 0:
                df = pd.DataFrame(grammar)
                df.insert(0, "Ref.", ref_no)
                if "🔍" not in df.columns:
                    df["🔍"] = "🔍"
                
                # 文法用 table 顯示較適合
                display_cols = ["Ref.", "Rule", "Example", "解析", "補齊句", "應用例", "🔍"]
                available_cols = [c for c in display_cols if c in df.columns]
                st.table(df[available_cols])
                st.caption(f"共 {len(grammar)} 個文法點")
            else:
                st.info("本次無文法點")
        
        # 除錯資訊
        with st.expander("🔧 原始 JSON 資料（除錯用）"):
            st.json(data)

    # ---------- 3. 容量管理 ----------
    with st.expander("⚙️ 容量管理"):
        col1, col2 = st.columns([3, 1])
        with col1:
            max_keep = st.number_input(
                "最多保留最近幾筆分析紀錄", 
                min_value=10, 
                max_value=2000, 
                value=800,
                step=50
            )
        with col2:
            st.write("")
            st.write("")
            if st.button("✂️ 壓縮"):
                hist = st.session_state.get("analysis_history", [])
                if len(hist) > max_keep:
                    st.session_state.analysis_history = hist[-max_keep:]
                    st.success(f"已壓縮至 {max_keep} 筆！")
                    st.rerun()
                else:
                    st.info("未達門檻")

    # ---------- 4. 匯出 ----------
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 匯出資料庫 (TSV)"):
            export = []
            for k, v in st.session_state.sentences.items():
                line = f"{k}\t{v.get('ref', '')}\t{v.get('en', '')[:100]}\t{v.get('zh', '')[:100]}"
                export.append(line)
            if export:
                st.code("\n".join(export), language="text")
                st.caption(f"共 {len(export)} 筆")
            else:
                st.info("資料庫為空")
    
    with col2:
        if st.button("🗑️ 清空當前顯示"):
            st.session_state["show_result"] = False
            st.session_state["analysis"] = None
            st.rerun()
