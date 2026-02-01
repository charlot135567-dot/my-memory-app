# ===================================================================
# 0. 套件 & 全域函式（一定放最頂）
# ===================================================================
import streamlit as st
import subprocess, sys, os, datetime as dt, pandas as pd, io, json, re, tomli, tomli_w
from streamlit_calendar import calendar
import streamlit.components.v1 as components

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
    c1.link_button("✨ Google AI", "https://gemini.google.com/")
    c2.link_button("🤖 Kimi K2",   "https://kimi.moonshot.cn/")
    c3, c4 = st.columns(2)
    c3.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb")
    c4.link_button("THSV11",    "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")
    
    # ✅ 加在這裡（仍在 with st.sidebar: 內部）
    st.divider()
    st.markdown("### 🖼️ 底部背景設定")
    
    bg_options = {
        "🐶 Snoopy": "Snoopy.jpg",
        "🐰 Mashimaro 1": "Mashimaro1.jpg",
        "🐰 Mashimaro 2": "Mashimaro2.jpg",
        "🐰 Mashimaro 3": "Mashimaro3.jpg",
        "🐰 Mashimaro 4": "Mashimaro4.jpg",
        "🐰 Mashimaro 5": "Mashimaro5.jpg",
        "🐰 Mashimaro 6": "Mashimaro6.jpg"
    }
    
    if 'selected_bg' not in st.session_state:
        st.session_state.selected_bg = list(bg_options.keys())[0]
    if 'bg_size' not in st.session_state:
        st.session_state.bg_size = 15
    if 'bg_bottom' not in st.session_state:
        st.session_state.bg_bottom = 30
    
    selected_bg = st.selectbox(
        "選擇角色", 
        list(bg_options.keys()), 
        index=list(bg_options.keys()).index(st.session_state.selected_bg),
        key="selected_bg"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        bg_size = st.slider("圖片大小", 5, 50, st.session_state.bg_size, format="%d%%", key="bg_size")
    with col2:
        bg_bottom = st.slider("底部間距", 0, 100, st.session_state.bg_bottom, format="%dpx", key="bg_bottom")

# ✅ 注意這裡已經不在 with st.sidebar: 裡面了！
# 背景 CSS 要放在這裡（sidebar 外面，但在 tabs 前面）
selected_img_file = bg_options[st.session_state.selected_bg]
current_bg_size = st.session_state.bg_size
current_bg_bottom = st.session_state.bg_bottom

try:
    if os.path.exists(selected_img_file):
        with open(selected_img_file, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{img_b64}");
            background-size: {current_bg_size}% auto;
            background-position: center bottom {current_bg_bottom}px;
            background-attachment: fixed;
            background-repeat: no-repeat;
            z-index: 0;
        }}
        .main .block-container {{
            position: relative;
            z-index: 1;
            padding-bottom: {current_bg_bottom + 100}px;
        }}
        </style>
        """, unsafe_allow_html=True)
except:
    pass

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
# 4. TAB2 ─ 月曆待辦（Emoji 清洗版，避免重複顯示）
# ===================================================================
with tabs[1]:
    import datetime as dt, re, os, json
    from streamlit_calendar import calendar

    # ---------- 0. 檔案持久化 ----------
    DATA_DIR = "data"
    os.makedirs(DATA_DIR, exist_ok=True)
    TODO_FILE = os.path.join(DATA_DIR, "todos.json")

    def load_todos():
        if os.path.exists(TODO_FILE):
            try:
                with open(TODO_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("載入待辦失敗:", e)
        return {}

    def save_todos():
        try:
            with open(TODO_FILE, "w", encoding="utf-8") as f:
                json.dump(st.session_state.todo, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("儲存待辦失敗:", e)

    # ---------- 1. 初始化 ----------
    if "todo" not in st.session_state:
        st.session_state.todo = load_todos()
    if "sel_date" not in st.session_state:
        st.session_state.sel_date = str(dt.date.today())
    if "cal_key" not in st.session_state:
        st.session_state.cal_key = 0
    if "active_del_id" not in st.session_state:
        st.session_state.active_del_id = None

    # ---------- 2. Emoji 清洗工具（核心修正） ----------
    _EMOJI_RE = re.compile(
        r'[\U0001F300-\U0001FAFF\U00002700-\U000027BF]+',
        flags=re.UNICODE
    )

    def get_clean_title(text: str) -> tuple:
        """
        從標題中：
        1. 擷取第一個 Emoji
        2. 移除所有 Emoji，保留純文字
        """
        found = _EMOJI_RE.search(text)
        emoji = found.group(0)[0] if found else ""
        clean_text = _EMOJI_RE.sub('', text).strip()
        return emoji, clean_text

    # ---------- 3. 月曆事件 ----------
    def build_events():
        ev = []
        for d, items in st.session_state.todo.items():
            if not isinstance(items, list):
                continue
            for t in items:
                emo, pure_title = get_clean_title(t.get("title", ""))
                ev.append({
                    "title": f"{emo} {pure_title}".strip(),
                    "start": f"{d}T{t.get('time','00:00:00')}",
                    "backgroundColor": "#FFE4E1",
                    "borderColor": "#FFE4E1",
                    "textColor": "#333"
                })
        return ev

    # ---------- 4. 月曆 ----------
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

    # ---------- 5. 下方三日清單 ----------
    st.markdown("##### 📋 待辦事項")

    try:
        base_date = dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date()
    except:
        base_date = dt.date.today()

    for offset in range(3):
        d_obj = base_date + dt.timedelta(days=offset)
        d_str = str(d_obj)
        if d_str in st.session_state.todo:
            for idx, item in enumerate(st.session_state.todo[d_str]):
                item_id = f"{d_str}_{idx}"
                emo, pure_title = get_clean_title(item.get("title", ""))

                c1, c2, c3 = st.columns([0.25, 7.75, 2], vertical_alignment="top")

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
                        f"{emo} {pure_title}".strip()
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
                        "time": str(in_time)
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
# 6. TAB4 ─ AI 控制台 Sidebar 背景圖挑選 + K2/Google prompt + 完整版 AI prompts
# ===================================================================
with tabs[3]:
    import os, json, datetime as dt, pandas as pd, urllib.parse, base64, re, csv
    from io import StringIO
    import streamlit as st
    import streamlit.components.v1 as components

    # ---------- 背景圖片（使用 Sidebar 選擇的圖片） ----------
    try:
        if 'selected_img_file' in globals() and os.path.exists(selected_img_file):
            with open(selected_img_file, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpeg;base64,{img_b64}");
                background-size: {current_bg_size if 'current_bg_size' in globals() else 15}% auto;
                background-position: center bottom {current_bg_bottom if 'current_bg_bottom' in globals() else 30}px;
                background-attachment: fixed;
                background-repeat: no-repeat;
                z-index: 0;
            }}
            .main .block-container {{
                position: relative;
                z-index: 1;
                padding-bottom: {(current_bg_bottom if 'current_bg_bottom' in globals() else 30) + 100}px;
            }}
            </style>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"背景圖載入失敗：{e}")

    # ---------- 資料庫持久化 ----------
    SENTENCES_FILE = "sentences.json"

    def load_sentences():
        """讀取本地 JSON 資料庫"""
        if os.path.exists(SENTENCES_FILE):
            try:
                with open(SENTENCES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                st.warning(f"讀取 JSON 失敗：{e}")
        return {}

    def save_sentences(data):
        """保存 JSON 資料庫"""
        with open(SENTENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # 初始化 session_state
    if 'sentences' not in st.session_state:
        st.session_state.sentences = load_sentences()
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'is_prompt_generated' not in st.session_state:
        st.session_state.is_prompt_generated = False
    if 'main_input_value' not in st.session_state:
        st.session_state.main_input_value = ""
    if 'original_text' not in st.session_state:
        st.session_state.original_text = ""

    # ---------- 智能偵測內容類型（整合版） ----------
    def detect_content_mode(text: str) -> str:
        """
        偵測使用者貼入內容的類型：
        - JSON 格式
        - 聖經經文（含中文或章節數字）
        - 一般文稿
        """
        text = text.strip()
        if not text:
            return "document"
        
        # 1. 偵測是否為 JSON
        if text.startswith("{"):
            return "json"
        
        # 2. 偵測中文字元
        has_chinese = re.search(r'[\u4e00-\u9fa5]', text)
        if has_chinese:
            # 只要包含中文，就判定為模式 A (經文模式)
            return "scripture"
        
        # 3. 若無中文，純英文則判定為模式 B (文稿模式)
        return "document"

    # ---------- Callback 函數：產生完整指令 ----------
    def generate_full_prompt():
        raw_text = st.session_state.get("raw_input_temp", "").strip()
        if not raw_text:
            st.warning("請先貼上內容")
            return
        
        mode = detect_content_mode(raw_text)
        
        if mode in ["json", "scripture"]:
            # 模式 A：聖經經文分析
            full_prompt = f"""你是一位精通多國語言的聖經專家與語言學教授。請根據輸入內容選擇對應模式輸出。

### 模式 A：【聖經經文分析時】＝》一定要產出 V1 + V2 Excel 格式（Markdown 表格）

⚠️ 輸出格式要求：請使用 **Markdown 表格格式**，方便直接複製貼回 Excel：

【V1 Sheet 範例】
| Ref. | English (ESV) | Chinese | Syn/Ant | Grammar |
|------|---------------|---------|---------|---------|
| Pro 31:6 | Give strong drink... | 可以把濃酒... | strong drink (烈酒) / watered down wine (淡酒) | 1️⃣[祈使句解析] 2️⃣[Give strong drink to him who is perishing] 3️⃣Ex. [Go and make disciples...] |

【V2 Sheet 範例】
| Ref. | 口語訳 | Grammar | Note | KRF | Syn/Ant | THSV11 |
|------|--------|---------|------|-----|---------|--------|

# V1 Sheet 欄位要求
# 1. Ref.：自動偵測經卷章節並用標準縮寫 (如 Pro, Rom, Gen)
# 2. English (ESV)：檢索對應英文經文
# 3. Chinese：填入使用者提供的中文原文
# 4. Syn/Ant：ESV 中的中高級單字或片語（含中/英翻譯），低於中級不列出
# 5. Grammar：嚴格符號化格式 1️⃣[解析] 2️⃣[補齊應用句] 3️⃣Ex. [中英對照例句]

# V2 Sheet 欄位要求
# 1. Ref.：同 V1
# 2. 口語訳：檢索日本《口語訳聖經》
# 3. Grammar：解析日文文法
# 4. Note：日文文法或語境補充說明
# 5. KRF：韓文《Korean Revised Version》
# 6. Syn/Ant：韓文高/中高級字詞
# 7. THSV11：泰文《Thai Holy Bible, Standard Version 2011》

待分析經文：{raw_text}"""
        else:
            # 模式 B：英文文稿分析
            full_prompt = f"""你是一位精通多國語言的聖經專家與語言學教授。

### 模式 B：【英文文稿分析時】＝》一定要產出 W + P Excel 格式（Markdown 表格）

⚠️ 輸出格式要求：請使用 **Markdown 表格格式**：

【W Sheet - 字詞表】
| No | Word/Phrase | Level | Chinese | Synonym | Antonym | Bible Example |
|----|-------------|-------|---------|---------|---------|---------------|
| 1 | steadfast | 高級 | 堅定不移的 | firm | wavering | 1Co 15:58 Therefore... |

【P Sheet - 文稿段落】
| Paragraph | English Refinement | 中英夾雜講章 |
|-----------|-----------------|---------------|
| 1 | We need to be steadfast... | 我們需要 (**steadfast**) ... |

【Grammar List】
| Pattern | Original | Analysis | Restoration | Example |
|---------|----------|----------|-------------|---------|
| 倒裝句 | Not only did he... | 1️⃣[Not only 前置形成倒裝] 2️⃣[He not only did...] 3️⃣Ex. [Not only will I guide you...] |

# 內容交錯 (I-V)
# 1. 純英文段落：修復句式 + 講員語氣 + 確保神學用詞精確優雅
# 2. 中英夾雜段落：完整中文敘述 + 對應高級英文詞彙嵌入括號
# 3. 重要術語用 **粗體** 表示，如 (**steadfast**)
# 4. 大綱標題與內容間須有空行

# 語言素材
# Vocabulary (20) & Phrases (15)：高級/中高級單字片語 + 中譯 + 同反義詞 + 中英對照例句
# Grammar List (6)：規則名 + 原稿範例 + 文法解析 + 結構還原 + 中英對照例句

待分析文稿：{raw_text}"""

        # 保存生成結果到 session_state
        st.session_state.original_text = raw_text
        st.session_state.main_input_value = full_prompt
        st.session_state.is_prompt_generated = True

    # ---------- 經文/文稿輸入與分析 ----------
    with st.expander("📝 經文輸入與 AI 分析", expanded=True):
        if not st.session_state.get('is_prompt_generated', False):
            st.caption("步驟 1：貼上經文或文稿後，點擊下方按鈕生成完整指令")
            
            raw_input = st.text_area(
                "原始輸入",
                height=200,
                value=st.session_state.get('original_text', ''),
                placeholder="請在此貼上內容：\n• 經文格式：31:6 可以把濃酒給將亡的人喝...\n• 文稿格式：直接貼上英文講稿",
                label_visibility="collapsed",
                key="raw_input_temp"
            )

            if st.button("⚡ 產生完整分析指令（自動加上 Prompt）", use_container_width=True, type="primary"):
                generate_full_prompt()
                st.rerun()
        else:
            st.caption(f"步驟 2：已生成 {'經文' if '模式 A' in st.session_state.main_input_value else '文稿'}分析指令")
            st.markdown("##### 📋 完整指令（點一下 → Cmd+C / Ctrl+C）")
            components.html(
                f"""
                <textarea
                    readonly
                    onclick="this.select()"
                    style="
                        width:100%;
                        height:300px;
                        padding:12px;
                        font-size:14px;
                        line-height:1.5;
                        border-radius:8px;
                        border:1px solid #ccc;
                        box-sizing:border-box;
                    "
                >{st.session_state.get('main_input_value','')}</textarea>
                """,
                height=330
            )

        st.divider()
            
            # 一排按鈕
            btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns([1.2, 1, 1, 0.8, 0.8])
            
            with btn_col1:
                encoded = urllib.parse.quote(st.session_state.get('main_input_value', ''))
                st.link_button("💬 GPT（自動）", f"https://chat.openai.com/?q={encoded}", use_container_width=True, type="primary")
            
            with btn_col2:
                st.link_button("🌙 Kimi", "https://kimi.com", use_container_width=True)
            
            with btn_col3:
                st.link_button("🔍 Google", "https://gemini.google.com", use_container_width=True)
            
            with btn_col4:
                if st.button("💾 存", use_container_width=True):
                    try:
                        ref = f"S_{dt.datetime.now().strftime('%m%d%H%M')}"
                        st.session_state.sentences[ref] = {
                            "ref": ref,
                            "content": st.session_state.get('main_input_value', ''),
                            "original": st.session_state.get('original_text', ''),
                            "type": "full_prompt",
                            "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        save_sentences(st.session_state.sentences)
                        st.success(f"✅ 已儲存：{ref}")
                    except Exception as e:
                        st.error(f"❌ 儲存失敗：{str(e)}")
            
            with btn_col5:
                if st.button("↩️ 清除", use_container_width=True):
                    st.session_state.is_prompt_generated = False
                    st.rerun()

    # ---------- 🔍 資料搜尋與管理（保持完整） ----------
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
                    results = [
                        {"key": k, "選": False, "Ref.": v.get("ref", k),
                         "內容": (v.get("en", v.get("content", ""))[:50] + "..."),
                         "日期": v.get("date_added", "")[:10]}
                        for k, v in st.session_state.sentences.items()
                        if kw in f"{v.get('ref','')} {v.get('en','')} {v.get('content','')}".lower()
                    ]
                    st.session_state.search_results = results
                    if not results:
                        st.info("找不到符合資料")

        search_results = st.session_state.get('search_results', [])
        if search_results:
            st.write(f"共 {len(search_results)} 筆")
            if st.checkbox("☑️ 全選", key="select_all"):
                for r in search_results:
                    r["選"] = True
                st.session_state.search_results = search_results
            
            if st.button("🗑️ 刪除勾選項目", key="delete_selected"):
                selected = [r["key"] for r in search_results if r.get("選")]
                if selected:
                    for k in selected:
                        st.session_state.sentences.pop(k, None)
                    save_sentences(st.session_state.sentences)
                    st.success(f"✅ 已刪除 {len(selected)} 筆")
                    st.session_state.search_results = []
                    st.rerun()
                else:
                    st.warning("請先勾選要刪除的項目")
            
            df = pd.DataFrame(search_results)
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
                if i < len(st.session_state.search_results):
                    st.session_state.search_results[i]["選"] = row["選"]

    # ---------- 底部統計（保持完整） ----------
    st.divider()
    total_count = len(st.session_state.get('sentences', {}))
    st.caption(f"💾 資料庫：{total_count} 筆")
    if st.session_state.get('sentences', {}):
        json_str = json.dumps(st.session_state.sentences, ensure_ascii=False, indent=2)
        st.download_button(
            "⬇️ 備份 JSON",
            json_str,
            file_name=f"backup_{dt.datetime.now().strftime('%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )

