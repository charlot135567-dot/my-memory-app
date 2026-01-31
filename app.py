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
# 6. TAB4 ─AI 控制台 Sidebar背景圖挑選＋K2/Google prompt＋完整版AI prompts
# ===================================================================
with tabs[3]:
    import os, json, datetime as dt, pandas as pd, urllib.parse, base64, re

    # ---------- 背景圖片（使用 Sidebar 選擇的圖片）----------
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
    except:
        pass

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
    if 'show_prompt_for_copy' not in st.session_state:
        st.session_state.show_prompt_for_copy = False
    if 'copy_target' not in st.session_state:
        st.session_state.copy_target = ""
    if 'just_copied' not in st.session_state:
        st.session_state.just_copied = False

    # 智能偵測內容類型
    def detect_content_mode(text):
        text = text.strip()
        if text.startswith("{"):
            return "json"
        if re.search(r'\b\d+\s*:\s*\d+\b', text[:100]):
            return "scripture"
        return "document"

    # ---------- 📝 經文輸入與AI分析（含完整 Prompt） ----------
    with st.expander("📝 經文輸入與AI分析", expanded=True):
        
        def on_input_change():
            st.session_state.input_dirty = True
        
        if user_input:
            # ... (判定 mode 與生成 prompt 的邏輯保持不變) ...
            mode = detect_content_mode(user_input)
            # ... (prompt 字串生成保持不變) ...
            # ==================== Excel 格式顯示（只有當輸入是 JSON 時） ====================
            is_valid_json = False
            parsed_data = None
            if user_input.startswith("{"):
                try:
                    parsed_data = json.loads(user_input)
                    is_valid_json = True
                    
                    # 顯示為漂亮表格（無下載按鈕）
                    st.success(f"📖 已解析：{parsed_data.get('ref_no', '未指定')} | 點擊下方 AI 進行分析，或編輯上方內容")
                    
                    tab_words, tab_phrases, tab_grammar = st.tabs(["📋 Words", "🔗 Phrases", "📚 Grammar"])
                    
                    with tab_words:
                        if 'words' in parsed_data and parsed_data['words']:
                            df = pd.DataFrame(parsed_data['words'])
                            df_display = df.rename(columns={
                                'word': '單字', 'level': '級別', 'meaning': '中文解釋',
                                'synonym': '同義詞', 'antonym': '反義詞'
                            })
                            st.dataframe(df_display, use_container_width=True, height=min(400, len(df)*35+40), hide_index=True)
                        else:
                            st.info("無單字資料")
                    
                    with tab_phrases:
                        if 'phrases' in parsed_data and parsed_data['phrases']:
                            df = pd.DataFrame(parsed_data['phrases'])
                            st.dataframe(df.rename(columns={'phrase': '片語', 'meaning': '中文解釋'}), 
                                        use_container_width=True, hide_index=True)
                        else:
                            st.info("無片語資料")
                    
                    with tab_grammar:
                        if 'grammar' in parsed_data and parsed_data['grammar']:
                            df = pd.DataFrame(parsed_data['grammar'])
                            st.dataframe(df.rename(columns={'pattern': '文法結構', 'explanation': '解析'}), 
                                        use_container_width=True, hide_index=True)
                        else:
                            st.info("無文法資料")
                            
                except json.JSONDecodeError:
                    pass # 不是合法 JSON，就當作文稿顯示原始輸入

            # ==================== AI 按鈕與複製介面 ====================
            encoded = urllib.parse.quote(prompt)
            st.divider()
            st.caption(f"{'📖 經文模式' if mode in ['json','scripture'] else '📝 文稿模式'} | {len(user_input)} 字元")
            
            show_copy_ui = st.session_state.get('show_prompt_for_copy', False)
            target = st.session_state.get('copy_target', '')
            
            if show_copy_ui:
                import streamlit.components.v1 as components
                
                st.markdown(f"**📋 以下為 {target} 專用的完整 Prompt：**")
                
                # 使用 text_area 讓使用者容易看到完整內容，同時有原生複製功能
                st.text_area("Prompt 內容（可在此複製或點擊下方按鈕）", value=prompt, height=200, key="prompt_display", label_visibility="collapsed")
                
                # 客製化複製按鈕（實際會複製到剪貼簿）
                copy_html = f"""
                <script>
                function copyText() {{
                    const text = `{prompt.replace('`', '\\`')}`;
                    navigator.clipboard.writeText(text).then(function() {{
                        document.getElementById('copy-status').innerText = "✅ 已複製！";
                        document.getElementById('copy-btn').style.backgroundColor = "#28a745";
                        // 延遲一點後再關閉，讓使用者看到成功訊息
                        setTimeout(function() {{
                            window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'close_prompt'}}, '*');
                            // 模擬點擊關閉（實際上要配合 Streamlit 的按鈕）
                        }}, 800);
                    }}, function(err) {{
                        document.getElementById('copy-status').innerText = "❌ 複製失敗，請手動複製上方文字";
                    }});
                }}
                </script>
                <button id="copy-btn" onclick="copyText()" style="width:100%; padding:10px; background-color:#FF6B6B; color:white; border:none; border-radius:5px; cursor:pointer; font-size:16px;">
                    📋 點擊此處複製 Prompt
                </button>
                <div id="copy-status" style="text-align:center; margin-top:8px; font-weight:bold; color:#28a745;"></div>
                """
                components.html(copy_html, height=80)
                
                # 由於 JS 無法直接觸發 Python callback，我們保留一個確認按鈕來關閉
                if st.button("✅ 複製完成（關閉此區塊）", use_container_width=True, type="primary", key="confirm_close"):
                    st.session_state.show_prompt_for_copy = False
                    st.session_state.copy_target = ""
                    st.rerun()
                
                st.divider()
                st.caption("同時提供其他 AI 連結（無需關閉即可點擊）：")
                
                # 修正：Google 和 Kimi 都顯示，不論觸發的是誰
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.link_button("💬 ChatGPT", f"https://chat.openai.com/?q={encoded}", use_container_width=True, type="primary")
                with c2:
                    st.link_button("🌙 前往 Kimi", "https://kimi.com", use_container_width=True)
                with c3:
                    st.link_button("🔍 前往 Google", "https://gemini.google.com", use_container_width=True)
                    
                if st.button("❌ 取消", use_container_width=True, key="cancel_copy"):
                    st.session_state.show_prompt_for_copy = False
                    st.session_state.copy_target = ""
                    st.rerun()
            
            else:
                # 主按鈕列（四個都在）
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.link_button("💬 GPT", f"https://chat.openai.com/?q={encoded}", use_container_width=True, type="primary")
                with c2:
                    if st.button("🌙 K2", use_container_width=True):
                        st.session_state.show_prompt_for_copy = True
                        st.session_state.copy_target = "Kimi"
                        st.rerun()
                with c3:
                    if st.button("🔍 G", use_container_width=True):
                        st.session_state.show_prompt_for_copy = True
                        st.session_state.copy_target = "Google"
                        st.rerun()
                with c4:
                    if st.button("💾 存", type="primary", use_container_width=True):
                        # 儲存邏輯（判斷是否為 JSON 決定儲存方式）
                        if is_valid_json:
                            ref = parsed_data.get('ref_no') or f"R_{dt.datetime.now().strftime('%m%d%H%M')}"
                            st.session_state.sentences[ref] = {
                                "ref": ref, **parsed_data, "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                        else:
                            ref = f"N_{dt.datetime.now().strftime('%m%d%H%M')}"
                            st.session_state.sentences[ref] = {
                                "ref": ref, "en": user_input, "zh": "",
                                "words": [], "phrases": [], "grammar": [],
                                "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                        save_sentences(st.session_state.sentences)
                        st.success(f"✅ 已存：{ref}")
                        st.session_state["main_input"] = ""
                        st.rerun()
            
            # ==================== 模式 A：完整聖經經文 Prompt ====================
            if mode in ["json", "scripture"]:
                prompt = f"""你是一位精通多國語言的聖經專家與語言學教授。
請根據使用者輸入的內容類型，選擇對應的模式輸出。

### 模式 A：【聖經經文模式】
當使用者輸入為「中文聖經經文」時，請嚴格產出以下 V1 與 V2 表格數據，禁止產出講章。

🔹 V1 Sheet 要求：
1. Ref.：自動找尋經卷章節並用縮寫 (如: Pro, Rom, Gen)。
2. English (ESV)：檢索對應的 ESV 英文經文。
3. Chinese：填入我提供的中文原文。
4. Syn/Ant：ESV 中的中高級單字或片語（含中/英翻譯），低於中級不列出。
5. Grammar：嚴格遵守符號化格式：
   1️⃣[文法邏輯解析] 
   2️⃣[補齊後的完整應用句] 
   3️⃣Ex. [中英對照聖經應用例句]

🔹 V2 Sheet 要求：
1. Ref.：同 V1。
2. 口語訳：檢索對應的日本《口語訳聖經》(1955)。
3. Grammar：解析日文文法（格式同 V1，使用 1️⃣2️⃣3️⃣Ex.）。
4. Note：日文文法或語境的補充說明。
5. KRF：檢索對應的韓文《Korean Revised Version》。
6. Syn/Ant：韓文高/ 中高級字（含日/韓/中翻譯）。
7. THSV11：檢索對應的泰文《Thai Holy Bible, Standard Version 2011》。

請分析以下經文，並以 JSON 格式回傳（方便程式解析）：
{{
  "ref_no": "經文編號（自動偵測並用縮寫，如 Prov 31:10, Gen 1:1, John 3:16）",
  "ref_article": "完整英文經文（ESV）",
  "zh_translation": "中文原文",
  "words": [{{"word": "單字", "level": "高級/中高級", "meaning": "中文解釋", "synonym": "同義詞", "antonym": "反義詞"}}],
  "phrases": [{{"phrase": "片語", "meaning": "中文解釋"}}],
  "grammar": [{{"pattern": "文法", "explanation": "1️⃣[解析] 2️⃣[還原句] 3️⃣Ex. [中英例句]"}}]
}}

⚠️ 重要：若輸入缺少書卷名（如只有"31:10"），請根據經文內容關鍵詞推斷正確書卷：
• "才德的婦人/珍珠" → Prov（箴言）
• "太初有道" → John（約翰福音）
• "起初神創造天地" → Gen（創世記）
• "虛心的人有福了" → Matt（馬太福音）
• "愛是恆久忍耐" → 1Co（哥林多前書13章）
以此類推，使用標準縮寫：Gen, Exo, Lev, Num, Deu, Jos, Jdg, Rut, 1Sa, 2Sa, 1Ki, 2Ki, 1Ch, 2Ch, Ezr, Neh, Est, Job, Psa, Pro, Ecc, Son, Isa, Jer, Lam, Eze, Dan, Hos, Joe, Amo, Oba, Jon, Mic, Nah, Hab, Zep, Hag, Zec, Mal, Mat, Mar, Luk, Joh, Act, Rom, 1Co, 2Co, Gal, Eph, Phi, Col, 1Th, 2Th, 1Ti, 2Ti, Tit, Phm, Heb, Jam, 1Pe, 2Pe, 1Jo, 2Jo, 3Jo, Jud, Rev。

待分析經文：{user_input}"""
                mode_label = "📖 經文模式"

            # ==================== 模式 B：完整英文文稿 Prompt ====================
            else:
                prompt = f"""你是一位精通多國語言的聖經專家與語言學教授。
嚴格根據使用者輸入的內容類型，選擇對應模式輸出。
當使用者輸入為###模式B：【英文文稿模式】時，請執行以下步驟：

🔹 第一步｜內容交錯 (I-V)：
嚴格執行將逐字稿轉化為流暢、文法正確，
保留原文中的高級/中高級字與片語及中心思想的完整文章，不得偏離原稿內容
段落呈現：「一段純英文精煉稿」隨即接「一段中英夾雜講章」的格式。

1. 純英文段落：修復句式＋講員語氣＋確保神學用詞精確優雅但不用艱深的字加重閱讀難度。
2. 中英夾雜段落：要完整的中文敘述，並對應的高級及中高級英文詞彙與片語嵌入括號中對照。
3. 上面☝️1&2的關鍵並重要英文術語嵌入中文括號要"加粗体"，如：我們需要保持忠心 (steadfast)。
4. 排版：大綱標題與內容間須有空行。

🔹 第二步｜語言素材：
1. Vocabulary (20個) & Phrases (15個): 
    高級/中高級字詞＋片語；含中譯、含中譯之同反義詞、中英對照聖經完整例句。
    翻譯請完全對照聖經裡的經文，禁止自己亂翻，聖經沒時才按邏輯翻譯。

2.Grammar List (6個)：規則名 + 原稿範例 + 文法解析 + 結構還原 + [中英對照應用例句]。
           語法邏輯還原 (Grammar Restoration)：針對包含「倒裝、省略、介係詞前置」
           等高難度結構的句子，
           嚴格遵守符號化格式：
           1️⃣[摘錄講稿中的原句作文法邏輯解析] ：
                 簡單說明語法結構的變化邏輯（如：介係詞為何前移）
           2️⃣[結構還原完整應用句] 
           3️⃣Ex. [中英對照聖經應用例句]

注意！！單字/片語/同反義詞的挑選規則：
              嚴格執行優先挑選高級單字-》中高級-》中級-》最後才其他

待分析文稿：{user_input}"""
                mode_label = "📝 文稿模式"

            encoded = urllib.parse.quote(prompt)
            st.caption(f"{mode_label} | {len(user_input)} 字元 | 含書卷推斷")
            
            # ============================================================
            # 複製介面邏輯（打勾自動關閉，不精簡）
            # ============================================================
            show_copy_ui = st.session_state.get('show_prompt_for_copy', False)
            target = st.session_state.get('copy_target', '')
            
            if show_copy_ui:
                # 顯示複製介面
                st.divider()
                st.markdown(f"**📋 已為 {target} 生成完整 Prompt：**")
                st.code(prompt, language="text")
                
                # 檢查是否剛完成複製（打勾狀態）
                if st.session_state.get('just_copied', False):
                    # 顯示打勾並自動關閉
                    st.success("✅ 已複製！自動關閉中...")
                    st.session_state.show_prompt_for_copy = False
                    st.session_state.just_copied = False
                    st.session_state.copy_target = ""
                    st.rerun()
                else:
                    # 顯示複製按鈕列
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        # 點擊「我已複製」→ 標記為已複製 → rerun → 顯示打勾 → 自動關閉
                        if st.button("📋 我已複製（點此打勾關閉）", use_container_width=True, type="primary"):
                            st.session_state.just_copied = True
                            st.rerun()
                    with c2:
                        # 直接前往連結
                        if "Kimi" in target:
                            st.link_button("🌙 前往 Kimi", "https://kimi.com", use_container_width=True)
                        else:
                            st.link_button("🔍 前往 Gemini", "https://gemini.google.com", use_container_width=True)
                    with c3:
                        # 取消/關閉按鈕
                        if st.button("❌ 取消", use_container_width=True):
                            st.session_state.show_prompt_for_copy = False
                            st.session_state.copy_target = ""
                            st.session_state.just_copied = False
                            st.rerun()
                    
                    # GPT 自動帶入連結（下方提供）
                    st.caption("或開啟 ChatGPT（自動帶入完整 Prompt）：")
                    st.link_button("💬 GPT 自動帶入", f"https://chat.openai.com/?q={encoded}", 
                                  use_container_width=True, type="secondary")
            
            else:
                # 正常 AI 按鈕列（未開啟複製介面時）
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.link_button("💬 GPT", f"https://chat.openai.com/?q={encoded}", 
                                  use_container_width=True, type="primary")
                with c2:
                    if st.button("🌙 K2", use_container_width=True):
                        st.session_state.show_prompt_for_copy = True
                        st.session_state.copy_target = "Kimi"
                        st.rerun()
                with c3:
                    if st.button("🔍 G", use_container_width=True):
                        st.session_state.show_prompt_for_copy = True
                        st.session_state.copy_target = "Google"
                        st.rerun()
                with c4:
                    if st.button("💾 存", type="primary", use_container_width=True):
                        try:
                            data = json.loads(user_input)
                            ref = data.get("ref_no") or f"R_{dt.datetime.now().strftime('%m%d%H%M')}"
                            st.session_state.sentences[ref] = {
                                "ref": ref,
                                "en": data.get("ref_article", data.get("en", "")),
                                "zh": data.get("zh_translation", data.get("zh", "")),
                                "words": data.get("words", []),
                                "phrases": data.get("phrases", []),
                                "grammar": data.get("grammar", []),
                                "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                        except:
                            ref = f"N_{dt.datetime.now().strftime('%m%d%H%M')}"
                            st.session_state.sentences[ref] = {
                                "ref": ref, "en": user_input, "zh": "",
                                "words": [], "phrases": [], "grammar": [],
                                "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                        save_sentences(st.session_state.sentences)
                        st.success(f"✅ 已存：{ref}")
                        st.session_state["main_input"] = ""
                        st.session_state.show_prompt_for_copy = False
                        st.session_state.just_copied = False
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
                         "內容": (v.get("en", "")[:50] + "...") if len(v.get("en", "")) > 50 else v.get("en", ""),
                         "日期": v.get("date_added", "")[:10]}
                        for k, v in st.session_state.sentences.items()
                        if kw in f"{v.get('ref','')} {v.get('en','')} {v.get('zh','')}".lower()
                    ]
                    st.session_state.search_results = results
                    if not results:
                        st.info("找不到符合資料")

        # 安全檢查
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

    # ---------- 底部統計 ----------
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
