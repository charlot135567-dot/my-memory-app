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
# 6. TAB4 ─ AI 控制台（單一輸入框 + 外部 AI 連結 + Excel 式管理）
# ===================================================================
with tabs[3]:
    import os, json, datetime as dt, pandas as pd, urllib.parse
    
    SENTENCES_FILE = "sentences.json"
    
    # ---------- 資料庫持久化 ----------
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
    
    # 初始化
    if 'sentences' not in st.session_state:
        st.session_state.sentences = load_sentences()
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_for_delete' not in st.session_state:
        st.session_state.selected_for_delete = []

    # ---------- 上方功能列（AI 連結 + 儲存）----------
    st.markdown("### 🤖 AI 分析連結")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    
    # 取得當前輸入內容生成 Prompt
    current_input = st.session_state.get("main_input", "")
    
    # 預設分析指令 Prompt
    ai_prompt = f"""請分析以下聖經經文，以 JSON 格式回傳（不要 markdown 格式）：
{{
  "ref_no": "經文編號（如：2Ti 3:10）",
  "ref_article": "完整英文經文",
  "zh_translation": "中文翻譯",
  "words": [
    {{"word": "單字", "meaning": "中文解釋", "level": "難度等級"}}
  ],
  "phrases": [
    {{"phrase": "片語", "meaning": "中文解釋", "usage": "例句"}}
  ],
  "grammar": [
    {{"grammar_point": "文法點", "explanation": "詳細說明"}}
  ]
}}

待分析經文：
{current_input}"""
    
    encoded_prompt = urllib.parse.quote(ai_prompt)
    
    with c1:
        st.link_button("💬 ChatGPT 🔗", f"https://chat.openai.com/?q={encoded_prompt}", 
                       use_container_width=True, help="開啟 ChatGPT 並自動帶入分析指令")
    with c2:
        # Kimi 網頁版連結（使用 query 參數）
        st.link_button("🌙 Kimi K2 🔗", f"https://kimi.com/?q={encoded_prompt}", 
                       use_container_width=True, help="開啟 Kimi 並自動帶入分析指令")
    with c3:
        # Google Gemini 連結
        st.link_button("🔍 Google 🔗", f"https://gemini.google.com/app?q={encoded_prompt}", 
                       use_container_width=True, help="開啟 Gemini 並自動帶入分析指令")
    with c4:
        # 儲存鍵：支援 JSON 格式 AI 結果或純文字
        if st.button("💾 儲存", type="primary", use_container_width=True):
            if not current_input.strip():
                st.error("⚠️ 請先輸入內容")
            else:
                try:
                    # 嘗試解析為 JSON（AI 分析結果）
                    data = json.loads(current_input)
                    ref = data.get("ref_no") or data.get("ref") or f"REF_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
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
                    st.success(f"✅ 已儲存：{ref}")
                    
                    # 清空輸入框並重新載入
                    st.session_state["main_input"] = ""
                    st.session_state["search_results"] = []
                    st.rerun()
                    
                except json.JSONDecodeError:
                    # 視為純文字筆記儲存
                    ref = f"NOTE_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
                    st.success(f"✅ 已儲存為文字筆記：{ref}")
                    st.session_state["main_input"] = ""
                    st.rerun()

    # ---------- 核心：單一多功能輸入框 ----------
    st.markdown("### 📝 多功能輸入區")
    input_text = st.text_area(
        "",
        height=350,
        key="main_input",
        placeholder="""📋 使用說明：
1. 貼上經文 → 點上方 AI 連結進行分析 → 複製 AI 結果 → 回貼至此 → 按儲存
2. 輸入 Ref. 或關鍵字 → 點下方「搜尋」查詢資料庫
3. 管理資料：搜尋後勾選項目 → 點「刪除」移除""",
        label_visibility="collapsed"
    )

    # ---------- 下方操作列（搜尋 + 刪除）----------
    st.markdown("### 🔍 資料檢索與管理")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔍 搜尋資料庫", use_container_width=True, type="primary"):
            if not input_text.strip():
                st.warning("請先在上方輸入框輸入搜尋條件（Ref. 編號或關鍵字）")
                st.session_state.search_results = []
            else:
                keyword = input_text.lower()
                results = []
                
                for k, v in st.session_state.sentences.items():
                    # 搜尋範圍：Ref、英文、中文、日期
                    searchable = f"{v.get('ref','')} {v.get('en','')} {v.get('zh','')} {v.get('date_added','')}".lower()
                    
                    if keyword in searchable or keyword in k.lower():
                        results.append({
                            "key": k,
                            "勾選": False,  # 用於刪除勾選
                            "Ref.": v.get("ref", k),
                            "內容預覽": (v.get("en", "")[:80] + "...") if len(v.get("en","")) > 80 else v.get("en", ""),
                            "中文": (v.get("zh", "")[:40] + "...") if len(v.get("zh","")) > 40 else v.get("zh", ""),
                            "日期": v.get("date_added", "")
                        })
                
                st.session_state.search_results = results
                if not results:
                    st.info("📭 找不到符合條件的資料")

    with col2:
        if st.button("🗑️ 刪除勾選項目", use_container_width=True, type="secondary"):
            if not st.session_state.get("selected_rows"):
                st.warning("請先在下方表格勾選要刪除的項目")
            else:
                deleted_count = 0
                for key in st.session_state.selected_rows:
                    if key in st.session_state.sentences:
                        del st.session_state.sentences[key]
                        deleted_count += 1
                
                if deleted_count > 0:
                    save_sentences(st.session_state.sentences)
                    st.success(f"✅ 已成功刪除 {deleted_count} 筆資料")
                    st.session_state.selected_rows = []
                    # 重新執行搜尋以更新列表
                    st.rerun()
                else:
                    st.error("刪除失敗")

    # ---------- 搜尋結果顯示區（Excel 式表格 + 勾選）----------
    if st.session_state.search_results:
        st.markdown(f"#### 📊 搜尋結果（共 {len(st.session_state.search_results)} 筆）")
        
        # 使用 Data Editor 實現勾選功能
        df = pd.DataFrame(st.session_state.search_results)
        
        edited_df = st.data_editor(
            df,
            column_config={
                "勾選": st.column_config.CheckboxColumn(
                    "選擇",
                    help="勾選後按上方「刪除勾選項目」",
                    default=False,
                    width="small"
                ),
                "key": None,  # 隱藏 key 欄位（內部使用）
                "Ref.": st.column_config.TextColumn("經文編號", width="medium"),
                "內容預覽": st.column_config.TextColumn("英文內容預覽", width="large"),
                "中文": st.column_config.TextColumn("中文", width="medium"),
                "日期": st.column_config.TextColumn("儲存日期", width="small")
            },
            hide_index=True,
            use_container_width=True,
            height=min(400, len(df) * 35 + 40),  # 動態高度
            key="result_editor"
        )
        
        # 更新選取狀態
        selected = edited_df[edited_df["勾選"] == True]["key"].tolist()
        st.session_state.selected_rows = selected
        
        if selected:
            st.caption(f"已選取 {len(selected)} 筆資料待刪除")
        
        # 詳細內容展開（僅顯示前 3 筆避免畫面過長，點擊可展開全部）
        st.markdown("#### 📖 詳細內容檢視")
        for i, row in enumerate(st.session_state.search_results[:5]):
            full_data = st.session_state.sentences.get(row["key"], {})
            
            with st.expander(f"📌 {row['Ref.']} | {row['日期']}"):
                col_content, col_analysis = st.columns([2, 1])
                
                with col_content:
                    st.markdown("**📝 英文內容：**")
                    st.text(full_data.get("en", "無"))
                    st.markdown("**🈺 中文：**")
                    st.text(full_data.get("zh", "無"))
                
                with col_analysis:
                    if full_data.get("words"):
                        st.markdown("**📚 單字重點：**")
                        for w in full_data["words"][:3]:
                            st.caption(f"• {w.get('word','')}：{w.get('meaning','')}")
                    
                    if full_data.get("phrases"):
                        st.markdown("**🔗 片語：**")
                        for p in full_data["phrases"][:2]:
                            st.caption(f"• {p.get('phrase','')}：{p.get('meaning','')}")
                    
                    if full_data.get("grammar"):
                        st.markdown("**⚙️ 文法點：**")
                        for g in full_data["grammar"][:2]:
                            st.caption(f"• {g.get('grammar_point','')}")

    # ---------- 底部統計與匯出 ----------
    st.divider()
    stat_col1, stat_col2, stat_col3 = st.columns([2, 2, 2])
    
    with stat_col1:
        st.caption(f"📦 資料庫總數：{len(st.session_state.sentences)} 筆")
    
    with stat_col2:
        # 一鍵匯出 JSON
        if st.session_state.sentences:
            json_str = json.dumps(st.session_state.sentences, ensure_ascii=False, indent=2)
            st.download_button(
                "⬇️ 匯出 JSON 備份",
                data=json_str,
                file_name=f"sentences_backup_{dt.datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    with stat_col3:
        # 清空資料庫（危險操作，需確認）
        if st.button("⚠️ 清空全部資料", type="secondary", use_container_width=True):
            st.session_state.show_confirm_clear = True
    
    if st.session_state.get("show_confirm_clear"):
        st.error("⚠️ 確定要刪除所有資料嗎？此動作無法復原！")
        conf_col1, conf_col2 = st.columns([1, 1])
        with conf_col1:
            if st.button("✅ 確認清空", type="primary"):
                st.session_state.sentences = {}
                save_sentences({})
                st.session_state.search_results = []
                st.session_state.show_confirm_clear = False
                st.success("資料庫已清空")
                st.rerun()
        with conf_col2:
            if st.button("❌ 取消"):
                st.session_state.show_confirm_clear = False
                st.rerun()
