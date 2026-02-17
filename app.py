# ===================================================================
# 0. 套件 & 全域函式（一定放最頂）
# ===================================================================
import streamlit as st  
import subprocess, sys, os, datetime as dt, pandas as pd, io, json, re, tomli, tomli_w
from streamlit_calendar import calendar
import streamlit.components.v1 as components
import requests

# 在文件最開始初始化所有 session state 變量
def init_session_state():
    defaults = {
        "is_prompt_generated": False,
        # 其他變量...
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

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

# ---------- 背景圖片套用（補上這段！）----------
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
    pass  # 背景圖失敗時靜默處理

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
# 3. TAB1 ─ 書桌 (輪流顯示版 - 資料分離修正版)
# ===================================================================
with tabs[0]:
    import csv, random, re, datetime as dt
    from io import StringIO

    # --- Session State 初始化（確保每次都有值）---
    if "tab1_vocab_index" not in st.session_state:
        st.session_state.tab1_vocab_index = 0
    if "tab1_phrase_index" not in st.session_state:
        st.session_state.tab1_phrase_index = 15
    if "tab1_grammar_index" not in st.session_state:
        st.session_state.tab1_grammar_index = 0
    if "tab1_verse_index" not in st.session_state:
        st.session_state.tab1_verse_index = 0
    if "tab1_last_update" not in st.session_state:
        st.session_state.tab1_last_update = dt.datetime.now()

    # 檢查是否需要更新（超過1小時）
    current_time = dt.datetime.now()
    time_diff = (current_time - st.session_state.tab1_last_update).total_seconds()
    
    if time_diff > 3600:
        st.session_state.tab1_last_update = current_time
        st.session_state.tab1_vocab_index += 1
        st.session_state.tab1_phrase_index += 4
        st.session_state.tab1_grammar_index += 1
        st.session_state.tab1_verse_index += 1
        st.rerun()
    
    sentences = st.session_state.get('sentences', {})
    
    if not sentences:
        st.warning("資料庫為空，請先在 TAB4 載入 Notion 資料")
    else:
        def parse_csv(content):
            if not content: 
                return []
            try:
                reader = csv.DictReader(StringIO(content.strip()))
                rows = list(reader)
                return [row for row in rows if any(v.strip() for v in row.values())]
            except:
                return []

        # ============================================================
        # 關鍵修正：分離模式A和模式B的資料
        # ============================================================
        
        # 收集所有模式A資料（有V1的）和模式B資料（有W Sheet但無V1的）
        all_mode_a = []  # 單字、金句來源
        all_mode_b = []  # 片語來源
        all_grammar_sources = []  # 文法來源（A或B都可以）
        
        for ref, data in sentences.items():
            v1_content = data.get('v1_content', '')
            w_content = data.get('w_sheet', '')
            g_content = data.get('grammar_list', '')
            
            v1_rows = parse_csv(v1_content)
            v2_rows = parse_csv(data.get('v2_content', ''))
            w_rows = parse_csv(w_content)
            g_rows = parse_csv(g_content)
            
            # 模式A：有V1資料 → 用於單字、金句
            if v1_rows:
                all_mode_a.append({
                    'ref': ref,
                    'v1': v1_rows,
                    'v2': v2_rows,
                    'v1_count': len(v1_rows)
                })
                # 文法也可以來自V1
                for i, row in enumerate(v1_rows):
                    all_grammar_sources.append({
                        'type': 'A',
                        'ref': ref,
                        'row': row,
                        'v2_row': v2_rows[i] if i < len(v2_rows) else {},
                        'index': i,
                        'total_in_file': len(v1_rows)
                    })
            
            # 模式B：有W Sheet → 用於片語（修正：只要有W Sheet就加入）
            if w_rows and len(w_rows) > 0:
                all_mode_b.append({
                    'ref': ref,
                    'w': w_rows,
                    'w_count': len(w_rows)
                })
            
            # Grammar List（模式B的文法）
            if g_rows:
                for i, row in enumerate(g_rows):
                    all_grammar_sources.append({
                        'type': 'B',
                        'ref': ref,
                        'row': row,
                        'v2_row': {},
                        'index': i,
                        'total_in_file': len(g_rows)
                    })
        
        # ============================================================
        # 1) 單字：V1 Syn/Ant + V2 Syn/Ant + THSV11
        # ============================================================
        vocab_display = []
        current_vocab_ref = "N/A"
        
        if all_mode_a:
            # 輪流選擇哪個模式A檔案
            total_vocab_items = sum(f['v1_count'] for f in all_mode_a)
            if total_vocab_items > 0:
                vocab_counter = st.session_state.tab1_vocab_index % total_vocab_items
                # 找到對應的檔案和行
                cumulative = 0
                vocab_file = None
                row_idx = 0
                for f in all_mode_a:
                    if cumulative + f['v1_count'] > vocab_counter:
                        vocab_file = f
                        row_idx = vocab_counter - cumulative
                        break
                    cumulative += f['v1_count']
                
                if vocab_file:
                    v1_row = vocab_file['v1'][row_idx]
                    v2_row = vocab_file['v2'][row_idx % len(vocab_file['v2'])] if vocab_file['v2'] else {}
                    
                    current_vocab_ref = v1_row.get('Ref.', vocab_file['ref'])
                    
                    # V1 Syn/Ant - 解析同義詞和反義詞
                    v1_syn_ant = v1_row.get('Syn/Ant', '')
                    v1_syn_list = []
                    v1_ant_list = []
                    
                    if v1_syn_ant:
                        if 'Syn:' in v1_syn_ant or 'Ant:' in v1_syn_ant:
                            syn_match = re.search(r'Syn:\s*([^/;]+)', v1_syn_ant)
                            ant_match = re.search(r'Ant:\s*([^/;]+)', v1_syn_ant)
                            if syn_match:
                                v1_syn_list = [s.strip() for s in syn_match.group(1).split(',') if s.strip()]
                            if ant_match:
                                v1_ant_list = [a.strip() for a in ant_match.group(1).split(',') if a.strip()]
                        else:
                            parts = re.split(r'[/|]', v1_syn_ant)
                            if len(parts) >= 2:
                                v1_syn_list = [p.strip() for p in parts[0].split(',') if p.strip()]
                                v1_ant_list = [p.strip() for p in parts[1].split(',') if p.strip()]
                    
                    # V2 Syn/Ant (韓文) + THSV11 (泰文)
                    v2_syn_ant = v2_row.get('Syn/Ant', '') if v2_row else ''
                    v2_th = v2_row.get('THSV11', '') if v2_row else ''
                    
                    vocab_items = []
                    if v1_syn_list:
                        vocab_items.append(f"<span style='color:#2E8B57;'>✨{', '.join(v1_syn_list)}</span>")
                    if v1_ant_list:
                        vocab_items.append(f"<span style='color:#CD5C5C;'>❄️{', '.join(v1_ant_list)}</span>")
                    if v2_syn_ant:
                        vocab_items.append(f"<span style='color:#4682B4;'>🇰🇷 {v2_syn_ant}</span>")
                    if v2_th:
                        vocab_items.append(f"<span style='color:#9932CC;'>🇹🇭 {v2_th}</span>")
                    
                    vocab_display = vocab_items
        
        # ============================================================
        # 2) 片語：只從模式B的W Sheet輪流（第16個開始）
        # ============================================================
        w_phrases = []
        current_phrase_ref = "N/A"
        
        # 收集所有可用的片語（從第16個開始，索引15）
        all_available_phrases = []
        
        for mb in all_mode_b:
            w_rows = mb.get('w', [])
            w_count = len(w_rows)
            
            # 只有超過15筆的檔案才加入
            if w_count > 15:
                for idx in range(15, w_count):
                    all_available_phrases.append({
                        'data': w_rows[idx],
                        'ref': mb['ref'],
                        'original_idx': idx + 1  # 1-based for display
                    })
        
        # 輪流顯示4個片語
        if len(all_available_phrases) > 0:
            total_available = len(all_available_phrases)
            # 確保索引在範圍內
            start_idx = st.session_state.tab1_phrase_index % total_available
            
            # 取4個片語（循環）
            for i in range(4):
                idx = (start_idx + i) % total_available
                item = all_available_phrases[idx]
                w_phrases.append(item['data'])
                # 記錄第一個的ref作為顯示用
                if i == 0:
                    current_phrase_ref = f"{item['ref']} #{item['original_idx']}"
        
        # ============================================================
        # 3) 金句：從模式A的V1 Sheet輪流
        # ============================================================
        verse_lines = []
        current_verse_ref = "N/A"
        
        if all_mode_a:
            total_verse_items = sum(f['v1_count'] for f in all_mode_a)
            if total_verse_items > 0:
                verse_counter = st.session_state.tab1_verse_index % total_verse_items
                cumulative = 0
                verse_file = None
                row_idx = 0
                
                for f in all_mode_a:
                    if cumulative + f['v1_count'] > verse_counter:
                        verse_file = f
                        row_idx = verse_counter - cumulative
                        break
                    cumulative += f['v1_count']
                
                if verse_file:
                    v1_verse = verse_file['v1'][row_idx]
                    v2_verse = verse_file['v2'][row_idx % len(verse_file['v2'])] if verse_file['v2'] else {}
                    
                    current_verse_ref = v1_verse.get('Ref.', verse_file['ref'])
                    
                    en_text = v1_verse.get('English (ESV)', '')
                    cn_text = v1_verse.get('Chinese', '')
                    jp_text = v2_verse.get('口語訳', '') if v2_verse else ''
                    kr_text = v2_verse.get('KRF', '') if v2_verse else ''
                    th_text = v2_verse.get('THSV11', '') if v2_verse else ''
                    
                    if en_text:
                        verse_lines.append(f"🇬🇧 **{current_verse_ref}** {en_text}")
                    if cn_text:
                        verse_lines.append(f"🇨🇳 {cn_text}")
                    if jp_text:
                        verse_lines.append(f"🇯🇵 {jp_text}")
                    if kr_text:
                        verse_lines.append(f"🇰🇷 {kr_text}")
                    if th_text:
                        verse_lines.append(f"🇹🇭 {th_text}")
        
        # ============================================================
        # 4) 文法：從兩處來，加入V2口語訳+Grammar+Note
        # ============================================================
        grammar_html = "等待資料中..."
        current_grammar_ref = "N/A"
        
        if all_grammar_sources:
            g_idx = st.session_state.tab1_grammar_index % len(all_grammar_sources)
            g_source = all_grammar_sources[g_idx]
            g_row = g_source['row']
            v2_row = g_source.get('v2_row', {})
            current_grammar_ref = f"{g_source['ref']}-{g_source['index']+1}"
            
            all_grammar = []
            
            if g_source['type'] == 'A':
                # 模式A文法（來自V1 Grammar欄位）
                g_ref = g_row.get('Ref.', '')
                g_en = g_row.get('English (ESV)', '')
                g_cn = g_row.get('Chinese', '')
                g_syn = g_row.get('Syn/Ant', '')
                g_grammar = g_row.get('Grammar', '')
                
                # 經文標題行：Ref緊貼英文（無空格）
                if g_ref and g_en:
                    all_grammar.append(f"<b>{g_ref}</b>{g_en}")
                elif g_en:
                    all_grammar.append(g_en)
                
                # 中文
                if g_cn:
                    all_grammar.append(g_cn)
                
                # Syn/Ant 同一行顯示（修正：確保Syn和Ant都顯示）
                if g_syn:
                    syn_ant_html = ""
                    # 解析 Syn 和 Ant
                    syn_text = ""
                    ant_text = ""
                    
                    # 嘗試多種格式解析
                    if 'Syn:' in g_syn or 'Ant:' in g_syn:
                        syn_match = re.search(r'Syn:\s*([^/;]+?)(?=\s*Ant:|$)', g_syn)
                        ant_match = re.search(r'Ant:\s*([^/;]+)', g_syn)
                        if syn_match:
                            syn_text = syn_match.group(1).strip()
                        if ant_match:
                            ant_text = ant_match.group(1).strip()
                    else:
                        # 嘗試用 / 或 | 分隔
                        parts = re.split(r'[/|]', g_syn)
                        if len(parts) >= 2:
                            syn_text = parts[0].strip()
                            ant_text = parts[1].strip()
                        else:
                            syn_text = g_syn.strip()
                    
                    # 組合顯示
                    if syn_text:
                        syn_ant_html += f'<span style="color:#2E8B57;">✨Syn:{syn_text}</span>'
                    if ant_text:
                        if syn_text:
                            syn_ant_html += ' '
                        syn_ant_html += f'<span style="color:#CD5C5C;">❄️Ant:{ant_text}</span>'
                    
                    if syn_ant_html:
                        all_grammar.append(syn_ant_html)
                
                # Grammar解析（縮排對齊）
                if g_grammar:
                    lines = []
                    text = str(g_grammar)
                    # 處理 1️⃣2️⃣3️⃣4️⃣ 標記
                    text = text.replace('1️⃣[', '1️⃣[')
                    text = text.replace('2️⃣[', '<br>2️⃣[')
                    text = text.replace('3️⃣[', '<br>3️⃣[')
                    text = text.replace('4️⃣[', '<br>4️⃣[')
                    text = text.replace(']', ']')
                    all_grammar.append(text)
                
                # V2資料：口語訳 + Grammar + Note
                v2_jp = v2_row.get('口語訳', '') if v2_row else ''
                v2_grammar = v2_row.get('Grammar', '') if v2_row else ''
                v2_note = v2_row.get('Note', '') if v2_row else ''
                
                if v2_jp:
                    v2_parts = ["<br>"]
                    v2_ref = v2_row.get('Ref.', g_ref) if v2_row else g_ref
                    v2_parts.append(f"<b>{v2_ref}</b>{v2_jp}")
                    
                    if v2_grammar:
                        v2_parts.append(f'<span style="color:#4682B4;">文法：</span>{v2_grammar}')
                    if v2_note:
                        v2_parts.append(f'<span style="color:#D2691E;">備註：</span>{v2_note}')
                    
                    all_grammar.append("<br>".join(v2_parts))
                    
            else:
                # 模式B文法（來自Grammar List）
                orig = g_row.get('Original Sentence', '')
                rule = g_row.get('Grammar Rule', '')
                analysis = g_row.get('Analysis & Example', '')
                
                if orig:
                    all_grammar.append(f"📝 <b>{orig}</b>")
                if rule:
                    all_grammar.append(f"📌 {rule}")
                if analysis:
                    af = str(analysis)
                    af = af.replace('1️⃣', '<br>1️⃣')
                    af = af.replace('2️⃣', '<br>2️⃣')
                    af = af.replace('3️⃣', '<br>3️⃣')
                    af = af.replace('4️⃣', '<br>4️⃣')
                    all_grammar.append(af)
            
            if all_grammar:
                grammar_html = "<br>".join(all_grammar)
        
        # ============================================================
        # 渲染畫面
        # ============================================================
        col_left, col_right = st.columns([0.67, 0.33])
        
        with col_left:
            # 單字區塊
            if vocab_display:
                st.markdown(
                    "<div style='margin-bottom:4px; line-height:1.6;'>" + 
                    " ; ".join(vocab_display) + 
                    "</div>", 
                    unsafe_allow_html=True
                )
            else:
                st.caption("無單字資料（請確認有模式A資料）")
            
            st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

            # 片語區塊（修正：顯示調試資訊）
            if w_phrases:
                for i, row in enumerate(w_phrases):
                    # 嘗試多種可能的欄位名稱
                    p = (row.get('Word/Phrase', '') or 
                         row.get('Word/phrase', '') or 
                         row.get('words/phrases', '') or 
                         row.get('Word', ''))
                    c = row.get('Chinese', '')
                    s = (row.get('Synonym+中文對照', '') or 
                         row.get('Synonym', '') or 
                         row.get('Syn', ''))
                    a = (row.get('Antonym+中文對照', '') or 
                         row.get('Antonym', '') or 
                         row.get('Ant', ''))
                    bible_ex = (row.get('全句聖經中英對照例句', '') or 
                               row.get('Bible Example', '') or 
                               row.get('Example', ''))
                    
                    if p:
                        parts = [f"🔤 **{p}**"]
                        if c: 
                            parts.append(f"<span style='color:#666;'>{c}</span>")
                        if s or a:
                            sa_parts = []
                            if s: 
                                sa_parts.append(f"<span style='color:#2E8B57;'>✨{s}</span>")
                            if a: 
                                sa_parts.append(f"<span style='color:#CD5C5C;'>❄️{a}</span>")
                            parts.append("<span style='font-size:0.9em;'>" + " | ".join(sa_parts) + "</span>")
                        
                        st.markdown(
                            "<div style='margin-bottom:2px;'>" + " ".join(parts) + "</div>", 
                            unsafe_allow_html=True
                        )
                        
                        if bible_ex:
                            match = re.match(r'([^(]+)(\([^)]+\))?$', bible_ex)
                            if match:
                                eng_part = match.group(1).strip()
                                cn_part = match.group(2) if match.group(2) else ""
                                bible_html = f"<span style='font-size:1.15em; font-weight:500;'>{eng_part}</span> <span style='font-size:0.9em; color:#666;'>{cn_part}</span>"
                            else:
                                bible_html = f"<span style='font-size:1.15em;'>{bible_ex}</span>"
                            
                            st.markdown(
                                f"<div style='margin-bottom:4px; margin-left:20px;'>📖 {bible_html}</div>", 
                                unsafe_allow_html=True
                            )
                        
                        if i < len(w_phrases) - 1:
                            st.markdown("<div style='margin:4px 0;'></div>", unsafe_allow_html=True)
            else:
                # 顯示調試資訊
                st.caption(f"無片語資料（模式B={len(all_mode_b)}個）")
                if all_mode_b:
                    for mb in all_mode_b:
                        st.caption(f"  - {mb['ref']}: {mb['w_count']}筆")

            st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

            # 金句區塊
            if verse_lines:
                st.markdown(f"<div style='margin-bottom:4px;'>{verse_lines[0]}</div>", unsafe_allow_html=True)
                for v in verse_lines[1:]:
                    st.markdown(f"<div style='margin-bottom:2px;'>{v}</div>", unsafe_allow_html=True)
            else:
                st.caption("📖 無金句資料（請確認有模式A資料）")

        with col_right:
            # 文法區塊
            st.markdown(f"""
                <div style="background-color:#1E1E1E; color:#FFFFFF; padding:10px; border-radius:8px; 
                            border-left:4px solid #FF8C00; font-size:13px; line-height:1.5; 
                            min-height:100%; display:flex; flex-direction:column;">
                    {grammar_html}
                </div>
                """, unsafe_allow_html=True)
            
            minutes_left = max(0, (3600 - time_diff) / 60)
            st.caption(f"單字:{current_vocab_ref} | 片語:{current_phrase_ref} | 金句:{current_verse_ref}")
            st.caption(f"文法:{current_grammar_ref} | {minutes_left:.0f}分後更新")
            st.caption(f"資料統計: A={len(all_mode_a)}個, B={len(all_mode_b)}個, 文法={len(all_grammar_sources)}個")

# ===================================================================
# 4. TAB2 ─ 月曆待辦 + 時段金句 + 收藏金句（修正版）
# ===================================================================
with tabs[1]:
    import datetime as dt, re, os, json
    from streamlit_calendar import calendar
    from io import StringIO
    import csv

    # 全局CSS：壓縮所有間距
    st.markdown("""
        <style>
        /* 壓縮所有元素間距 */
        div[data-testid="stVerticalBlock"] > div {padding: 0px !important; margin: 0px !important;}
        div[data-testid="stVerticalBlock"] > div > div {padding: 0px !important; margin: 0px !important;}
        p {margin: 0px !important; padding: 0px !important; line-height: 1.2 !important;}
        .stMarkdown {margin: 0px !important; padding: 0px !important;}
        /* 壓縮按鈕 */
        .stButton button {padding: 0px 4px !important; min-height: 24px !important; font-size: 12px !important; margin: 0px !important;}
        /* 壓縮分隔線 */
        hr {margin: 2px 0 !important; padding: 0 !important;}
        /* 壓縮expander */
        div[data-testid="stExpander"] {margin: 2px 0 !important;}
        div[data-testid="stExpander"] > div {padding: 0px 8px !important;}
        /* 壓縮columns間距 */
        div[data-testid="column"] {padding: 0px 2px !important;}
        </style>
    """, unsafe_allow_html=True)

    # ---------- 0. 檔案設定 ----------
    DATA_DIR = "data"
    os.makedirs(DATA_DIR, exist_ok=True)
    TODO_FILE = os.path.join(DATA_DIR, "todos.json")
    FAVORITE_FILE = os.path.join(DATA_DIR, "favorite_sentences.json")

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

    def load_favorites():
        if os.path.exists(FAVORITE_FILE):
            try:
                with open(FAVORITE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return []

    def save_favorites():
        with open(FAVORITE_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.favorite_sentences, f, ensure_ascii=False, indent=2)

    # ---------- 1. Session State ----------
    if "todo" not in st.session_state:
        st.session_state.todo = load_todos()
    if "favorite_sentences" not in st.session_state:
        st.session_state.favorite_sentences = load_favorites()
    if "sel_date" not in st.session_state:
        st.session_state.sel_date = str(dt.date.today())
    if "cal_key" not in st.session_state:
        st.session_state.cal_key = 0
    if "active_del_id" not in st.session_state:
        st.session_state.active_del_id = None
    if "active_fav_del" not in st.session_state:
        st.session_state.active_fav_del = None

    # ---------- 2. 月曆 ----------
    def build_events():
        ev = []
        for d, items in st.session_state.todo.items():
            if isinstance(items, list):
                for t in items:
                    ev.append({
                        "title": t.get("title", ""),
                        "start": f"{d}T{t.get('time','00:00:00')}",
                        "backgroundColor": "#FFE4E1",
                        "borderColor": "#FFE4E1",
                        "textColor": "#333"
                    })
        return ev

    with st.expander("📅 聖經學習生活月曆", expanded=True):
        cal_options = {
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
            "initialView": "dayGridMonth",
            "displayEventTime": False,
            "height": "auto"
        }
        state = calendar(events=build_events(), options=cal_options, key=f"cal_{st.session_state.cal_key}")
        if state.get("dateClick"):
            st.session_state.sel_date = state["dateClick"]["date"][:10]
            st.rerun()

    # ---------- 3. 三日清單（修正：顯示選中日期的前後一天）----------
    st.markdown('<p style="margin:0;padding:0;font-size:14px;font-weight:bold;">📋 待辦事項</p>', unsafe_allow_html=True)

    try:
        base_date = dt.datetime.strptime(st.session_state.sel_date, "%Y-%m-%d").date()
    except:
        base_date = dt.date.today()

    # 顯示選中日期及其前後各一天（共3天）
    dates_to_show = [base_date - dt.timedelta(days=1), base_date, base_date + dt.timedelta(days=1)]
    
    has_todo = False
    for d_obj in dates_to_show:
        d_str = str(d_obj)
        
        if d_str in st.session_state.todo and st.session_state.todo[d_str]:
            has_todo = True
            
            for idx, item in enumerate(st.session_state.todo[d_str]):
                item_id = f"{d_str}_{idx}"
                title = item.get("title", "") if isinstance(item, dict) else str(item)
                time_str = item.get('time', '')[:5] if isinstance(item, dict) and item.get('time') else ""

                # 極緊湊布局
                c1, c2, c3 = st.columns([0.3, 8, 1.2])
                
                with c1:
                    if st.button("💟", key=f"h_{item_id}"):
                        st.session_state.active_del_id = None if st.session_state.active_del_id == item_id else item_id
                        st.rerun()

                with c2:
                    # 使用html壓縮行距
                    st.markdown(f'<p style="margin:0;padding:0;line-height:1.2;font-size:13px;">{d_obj.month}/{d_obj.day} {time_str} {title}</p>', unsafe_allow_html=True)

                with c3:
                    if st.session_state.active_del_id == item_id:
                        if st.button("🗑️", key=f"d_{item_id}"):
                            st.session_state.todo[d_str].pop(idx)
                            if not st.session_state.todo[d_str]:
                                del st.session_state.todo[d_str]
                            save_todos()
                            st.session_state.cal_key += 1
                            st.session_state.active_del_id = None
                            st.rerun()
                # 每個項目後極小間距
                st.markdown('<div style="height:1px;"></div>', unsafe_allow_html=True)
    
    if not has_todo:
        st.caption("尚無待辦事項")

    # ---------- 4. 新增待辦 ----------
    with st.expander("➕ 新增待辦", expanded=False):
        with st.form("todo_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                in_date = st.date_input("日期", base_date)
            with c2:
                in_time = st.time_input("時間", dt.time(9, 0))
            in_title = st.text_input("待辦事項（可含 Emoji）")
            
            if st.form_submit_button("💾 儲存"):
                if in_title:
                    k = str(in_date)
                    if k not in st.session_state.todo:
                        st.session_state.todo[k] = []
                    st.session_state.todo[k].append({"title": in_title, "time": str(in_time)})
                    save_todos()
                    st.session_state.cal_key += 1
                    st.rerun()

    st.markdown('<hr style="margin:4px 0;">', unsafe_allow_html=True)
    
    # ---------- 5. 時段金句 ----------
    st.markdown('<p style="margin:0;padding:0;font-size:14px;font-weight:bold;">📖 今日時段金句</p>', unsafe_allow_html=True)
    
    sentences = st.session_state.get('sentences', {})
    all_verses = []
    
    for ref, data in sentences.items():
        v1_content = data.get('v1_content', '')
        v2_content = data.get('v2_content', '')
        if v1_content:
            try:
                v1_rows = list(csv.DictReader(StringIO(v1_content.strip())))
                v2_rows = list(csv.DictReader(StringIO(v2_content.strip()))) if v2_content else []
                
                for i, row in enumerate(v1_rows):
                    v2_row = v2_rows[i] if i < len(v2_rows) else {}
                    verse_ref = row.get('Ref.', ref)
                    en = row.get('English (ESV)', '')
                    cn = row.get('Chinese', '')
                    jp = v2_row.get('口語訳 (1955)', '') if isinstance(v2_row, dict) else ''
                    kr = v2_row.get('KRF', '') if isinstance(v2_row, dict) else ''
                    th = v2_row.get('THSV11 (Key Phrases)', '') if isinstance(v2_row, dict) else ''
                    
                    verse_text = f"🇬🇧 {verse_ref} {en}"
                    if jp:
                        verse_text += f"<br>🇯🇵 {jp}"
                    if kr:
                        verse_text += f"<br>🇰🇷 {kr}"
                    if th:
                        verse_text += f"<br>🇹🇭 {th}"
                    if cn:
                        verse_text += f"<br>🇨🇳 {cn}"
                    
                    all_verses.append(verse_text)
            except:
                pass

    hour = dt.datetime.now().hour
    
    if 7 <= hour < 11:
        period_name, period_idx = "早晨 7-11", 0
    elif 11 <= hour < 15:
        period_name, period_idx = "午間 11-15", 1
    elif 15 <= hour < 19:
        period_name, period_idx = "下午 15-19", 2
    elif 19 <= hour < 23:
        period_name, period_idx = "晚間 19-23", 3
    else:
        period_name, period_idx = "深夜", -1

    st.markdown(f'<p style="margin:0;padding:0;font-size:11px;color:#FF8C00;">⏰ {period_name}</p>', unsafe_allow_html=True)

    if all_verses and period_idx >= 0:
        total = len(all_verses)
        start = (period_idx * 6) % total
        
        for i in range(6):
            idx = (start + i) % total
            st.markdown(f'<p style="margin:2px 0;padding:0;font-size:12px;line-height:1.3;"><b>{i+1}.</b> {all_verses[idx]}</p>', unsafe_allow_html=True)
            if i < 5:
                st.markdown('<hr style="margin:2px 0;border:none;border-top:1px solid #eee;">', unsafe_allow_html=True)
    else:
        st.caption("尚無金句資料")

    st.markdown('<hr style="margin:4px 0;">', unsafe_allow_html=True)

    # ---------- 6. 收藏金句 ----------
    st.markdown('<p style="margin:0;padding:0;font-size:14px;font-weight:bold;">🔽 收藏金句</p>', unsafe_allow_html=True)

    for idx, fav in enumerate(st.session_state.favorite_sentences[:8]):
        fav_id = f"fav_{idx}"
        c1, c2, c3 = st.columns([0.3, 8.5, 1.2])
        
        with c1:
            if st.button("💝", key=f"favh_{fav_id}"):
                st.session_state.active_fav_del = None if st.session_state.active_fav_del == fav_id else fav_id
                st.rerun()
        
        with c2:
            st.markdown(f'<p style="margin:0;padding:0;font-size:12px;line-height:1.2;">{fav}</p>', unsafe_allow_html=True)
        
        with c3:
            if st.session_state.active_fav_del == fav_id:
                if st.button("🗑️", key=f"favd_{fav_id}"):
                    st.session_state.favorite_sentences.pop(idx)
                    save_favorites()
                    st.session_state.active_fav_del = None
                    st.rerun()
        st.markdown('<div style="height:1px;"></div>', unsafe_allow_html=True)

    if len(st.session_state.favorite_sentences) < 8:
        with st.form("add_fav", clear_on_submit=True):
            new_fav = st.text_area("新增收藏", height=50)
            if st.form_submit_button("➕ 加入"):
                if new_fav:
                    st.session_state.favorite_sentences.append(new_fav)
                    save_favorites()
                    st.rerun()

    st.caption(f"收藏: {len(st.session_state.favorite_sentences)}/8")
    
# ===================================================================
# 5. TAB3 ─ 挑戰（簡化版：直接給題目，最後給答案）
# ===================================================================
with tabs[2]:
    import csv
    from io import StringIO
    import random
    
    if 'tab3_quiz_seed' not in st.session_state:
        st.session_state.tab3_quiz_seed = random.randint(1, 1000)
        st.session_state.tab3_show_answers = False
    
    sentences = st.session_state.get('sentences', {})
    
    if not sentences:
        st.warning("資料庫為空，請先在 TAB4 儲存資料")
    else:
        # 排序資料
        sorted_refs = sorted(sentences.keys(), 
                           key=lambda x: sentences[x].get('date_added', ''), 
                           reverse=True)
        total = len(sorted_refs)
        
        new_refs = sorted_refs[:int(total*0.6)] if total >= 5 else sorted_refs
        mid_refs = sorted_refs[int(total*0.6):int(total*0.9)] if total >= 10 else []
        old_refs = sorted_refs[int(total*0.9):] if total >= 10 else []
        
        weighted_pool = (new_refs * 6) + (mid_refs * 3) + (old_refs * 1)
        if not weighted_pool:
            weighted_pool = sorted_refs
        
        random.seed(st.session_state.tab3_quiz_seed)
        
        # 收集所有經文資料
        all_verses = []
        for ref in weighted_pool[:10]:  # 取前10筆資料
            data = sentences[ref]
            v1_content = data.get('v1_content', '')
            if v1_content:
                try:
                    lines = v1_content.strip().split('\n')
                    if lines:
                        reader = csv.DictReader(lines)
                        for row in reader:
                            all_verses.append({
                                'ref': row.get('Ref.', ''),
                                'english': row.get('English (ESV)', ''),
                                'chinese': row.get('Chinese', '')
                            })
                except:
                    pass
        
        # 隨機選6題（3題中翻英，3題英翻中）
        random.shuffle(all_verses)
        selected = all_verses[:6] if len(all_verses) >= 6 else all_verses
        
        # 分配題目
        zh_to_en = selected[:3]  # 中翻英
        en_to_zh = selected[3:6] if len(selected) > 3 else []  # 英翻中
        
        st.subheader("📝 翻譯挑戰")
        
        # ===== 題目 1-3：中翻英 =====
        for i, q in enumerate(zh_to_en, 1):
            st.markdown(f"**{i}.** {q['chinese'][:60]}")
            st.text_input("", key=f"quiz_zh_en_{i}", placeholder="請翻譯成英文...", label_visibility="collapsed")
            st.write("")
        
        # ===== 題目 4-6：英翻中 =====
        for i, q in enumerate(en_to_zh, 4):
            st.markdown(f"**{i}.** {q['english'][:100]}")
            st.text_input("", key=f"quiz_en_zh_{i}", placeholder="請翻譯成中文...", label_visibility="collapsed")
            st.write("")
        
        # ===== 單字題（3題）=====
        # 從 Syn/Ant 提取單字
        word_pool = []
        for ref in weighted_pool[:5]:
            data = sentences[ref]
            v1_content = data.get('v1_content', '')
            if v1_content:
                try:
                    lines = v1_content.strip().split('\n')
                    if lines:
                        reader = csv.DictReader(lines)
                        for row in reader:
                            syn_ant = row.get('Syn/Ant', '')
                            if '/' in syn_ant:
                                parts = syn_ant.split('/')
                                for p in parts:
                                    match = re.match(r'(.+?)\s*\((.+?)\)', p.strip())
                                    if match:
                                        word_pool.append({
                                            'en': match.group(1).strip(),
                                            'cn': match.group(2).strip()
                                        })
                except:
                    pass
        
        random.shuffle(word_pool)
        selected_words = word_pool[:3] if len(word_pool) >= 3 else word_pool
        
        for i, w in enumerate(selected_words, 7):
            st.markdown(f"**{i}.** {w['cn']}（請寫出英文）")
            st.text_input("", key=f"quiz_word_{i}", placeholder="English word...", label_visibility="collapsed")
            st.write("")
        
        # ===== 翻看答案按 =====
        col_btn, col_answer = st.columns([1, 3])
        with col_btn:
            if st.button("👁️ 翻看正確答案", use_container_width=True, type="primary"):
                st.session_state.tab3_show_answers = True
                st.rerun()
        
        with col_answer:
            if st.session_state.tab3_show_answers:
                with st.expander("📖 正確答案", expanded=True):
                    # 顯示中翻英答案
                    st.markdown("**中翻英：**")
                    for i, q in enumerate(zh_to_en, 1):
                        st.caption(f"{i}. {q['english'][:100]}")
                    
                    # 顯示英翻中答案
                    st.markdown("**英翻中：**")
                    for i, q in enumerate(en_to_zh, 4):
                        st.caption(f"{i}. {q['chinese'][:60]}")
                    
                    # 顯示單字答案
                    st.markdown("**單字：**")
                    for i, w in enumerate(selected_words, 7):
                        st.caption(f"{i}. {w['en']}")
                             
                if st.button("🔄 換一批題目", use_container_width=True):
                    st.session_state.tab3_quiz_seed = random.randint(1, 1000)
                    st.session_state.tab3_show_answers = False
                    st.rerun()
            
# ===================================================================
# 6. TAB4 ─ AI 控制台 + Notion Database 整合（支援多工作表）
# ===================================================================
with tabs[3]:
    import os, json, datetime as dt, pandas as pd, urllib.parse, base64, re, csv, requests
    from io import StringIO
    import streamlit.components.v1 as components

    # ═══════════════════════════════════════════════════════════════
    # 🔒 NOTION 設定集中管理區（更新時請勿修改此區塊結構）
    # ═══════════════════════════════════════════════════════════════
    NOTION_TOKEN = ""
    DATABASE_ID = ""
    
    try:
        if "notion" in st.secrets:
            notion_cfg = st.secrets["notion"]
            NOTION_TOKEN = notion_cfg.get("token", "")
            DATABASE_ID = notion_cfg.get("database_id", "2f910510e7fb80c4a67ff8735ea90cdf")
            
            if NOTION_TOKEN and DATABASE_ID:
                st.sidebar.success(f"✅ Notion 設定載入成功")
            else:
                st.sidebar.warning(f"⚠️ Notion 設定不完整")
        else:
            st.sidebar.error("❌ secrets.toml 缺少 [notion] 區段")
            DATABASE_ID = "2f910510e7fb80c4a67ff8735ea90cdf"
    except Exception as e:
        st.sidebar.error(f"❌ 讀取 Notion 設定失敗: {e}")
        DATABASE_ID = "2f910510e7fb80c4a67ff8735ea90cdf"
    
    NOTION_API_VERSION = "2022-06-28"
    NOTION_BASE_URL = "https://api.notion.com/v1"

    # ---------- 背景圖片套用 ----------
    try:
        selected_img_file = bg_options.get(st.session_state.get('selected_bg', '🐶 Snoopy'), 'Snoopy.jpg')
        current_bg_size = st.session_state.get('bg_size', 15)
        current_bg_bottom = st.session_state.get('bg_bottom', 30)
        
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

    # ---------- Google Sheet 連線檢查 ----------
    sheet_connected = False
    GCP_SA = None
    SHEET_ID = None
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        GCP_SA = st.secrets.get("gcp_service_account", {})
        SHEET_ID = st.secrets.get("sheets", {}).get("spreadsheet_id", "")
        if GCP_SA and SHEET_ID:
            sheet_connected = True
    except:
        pass

    # ---------- 輔助函式 ----------
    def get_notion_text(prop_dict):
        rt = prop_dict.get("rich_text", [])
        if rt and len(rt) > 0:
            return rt[0].get("text", {}).get("content", "")
        return ""

    # ---------- Notion 核心函式 ----------
    def load_from_notion():
        if not NOTION_TOKEN:
            st.sidebar.error("❌ NOTION_TOKEN 未設定")
            return {}
        
        url = f"{NOTION_BASE_URL}/databases/{DATABASE_ID}/query"
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_API_VERSION,
            "Content-Type": "application/json"
        }

        all_data = {}
        has_more = True
        start_cursor = None

        try:
            with st.spinner("☁️ 正在從 Notion 載入資料..."):
                while has_more:
                    payload = {"page_size": 100}
                    if start_cursor:
                        payload["start_cursor"] = start_cursor

                    response = requests.post(url, headers=headers, json=payload)
                    
                    if response.status_code != 200:
                        st.sidebar.error(f"🚫 Notion API 錯誤 ({response.status_code})")
                        return {}

                    data = response.json()

                    for page in data.get("results", []):
                        props = page.get("properties", {})
                        ref = get_notion_text(props.get("Ref_No", {})) or "unknown"
                        translation = get_notion_text(props.get("Translation", {}))

                        v1_content = ""
                        v2_content = ""
                        w_sheet = ""
                        p_sheet = ""
                        grammar_list = ""
                        
                        if translation:
                            # 解析各個工作表
                            if "【V1 Sheet】" in translation:
                                parts = translation.split("【V2 Sheet】")
                                v1_content = parts[0].split("【V1 Sheet】")[-1].strip() if len(parts) > 0 else ""
                                rest = parts[1] if len(parts) > 1 else ""
                                
                                if "【W Sheet】" in rest:
                                    v2_parts = rest.split("【W Sheet】")
                                    v2_content = v2_parts[0].replace("【其他工作表】", "").strip()
                                    w_rest = v2_parts[1] if len(v2_parts) > 1 else ""
                                    
                                    if "【P Sheet】" in w_rest:
                                        w_parts = w_rest.split("【P Sheet】")
                                        w_sheet = w_parts[0].strip()
                                        p_rest = w_parts[1] if len(w_parts) > 1 else ""
                                        
                                        if "【Grammar List】" in p_rest:
                                            p_parts = p_rest.split("【Grammar List】")
                                            p_sheet = p_parts[0].strip()
                                            grammar_list = p_parts[1].split("【其他補充】")[0].strip() if len(p_parts) > 1 else ""
                                    else:
                                        w_sheet = w_rest.split("【其他補充】")[0].strip() if "【其他補充】" in w_rest else w_rest.strip()
                                else:
                                    v2_content = rest.split("【其他工作表】")[0].strip() if "【其他工作表】" in rest else rest.strip()

                        title_list = props.get("Content", {}).get("title", [])
                        original = title_list[0].get("text", {}).get("content", "") if title_list else ""

                        all_data[ref] = {
                            "ref": ref,
                            "original": original,
                            "v1_content": v1_content,
                            "v2_content": v2_content,
                            "w_sheet": w_sheet,
                            "p_sheet": p_sheet,
                            "grammar_list": grammar_list,
                            "other": "",
                            "ai_result": translation,
                            "type": props.get("Type", {}).get("select", {}).get("name", "Scripture"),
                            "mode": props.get("Source_Mode", {}).get("select", {}).get("name", "Mode A"),
                            "date_added": props.get("Date_Added", {}).get("date", {}).get("start", "") if props.get("Date_Added", {}).get("date") else "",
                            "notion_page_id": page.get("id"),
                            "notion_synced": True,
                            "saved_sheets": []
                        }
                        
                        # 標記已儲存的工作表
                        if v1_content:
                            all_data[ref]["saved_sheets"].append("V1 Sheet")
                        if v2_content:
                            all_data[ref]["saved_sheets"].append("V2 Sheet")
                        if w_sheet:
                            all_data[ref]["saved_sheets"].append("W Sheet")
                        if p_sheet:
                            all_data[ref]["saved_sheets"].append("P Sheet")
                        if grammar_list:
                            all_data[ref]["saved_sheets"].append("Grammar List")

                    has_more = data.get("has_more", False)
                    start_cursor = data.get("next_cursor")

            if all_data:
                st.sidebar.success(f"✅ 已從 Notion 載入 {len(all_data)} 筆資料")
            return all_data

        except Exception as e:
            st.sidebar.error(f"❌ 載入失敗：{e}")
            return {}

    def save_to_notion(data_dict):
        if not NOTION_TOKEN:
            return False, "NOTION_TOKEN 未設定", None

        url = f"{NOTION_BASE_URL}/pages"
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_API_VERSION
        }

        # 組合所有工作表內容
        full_content = f"""【V1 Sheet】
{data_dict.get('v1_content', '無')}

【V2 Sheet】
{data_dict.get('v2_content', '無')}

【W Sheet】
{data_dict.get('w_sheet', '無')}

【P Sheet】
{data_dict.get('p_sheet', '無')}

【Grammar List】
{data_dict.get('grammar_list', '無')}

【其他補充】
{data_dict.get('other', '無')}
"""

        properties = {
            "Content": {"title": [{"text": {"content": data_dict.get('original', '空白資料')[:100]}}]},
            "Translation": {"rich_text": [{"text": {"content": full_content[:2000]}}]},
            "Ref_No": {"rich_text": [{"text": {"content": data_dict.get("ref", "BLANK")}}]},
            "Source_Mode": {"select": {"name": data_dict.get("mode", "Mode A")}},
            "Type": {"select": {"name": data_dict.get("type", "Blank")}},
            "Date_Added": {"date": {"start": dt.datetime.now().isoformat()}}
        }

        try:
            response = requests.post(url, headers=headers, json={
                "parent": {"database_id": DATABASE_ID},
                "properties": properties
            })
            if response.status_code == 200:
                page_id = response.json().get("id")
                return True, "成功", page_id
            else:
                return False, f"API Error: {response.text}", None
        except Exception as e:
            return False, str(e), None

    # ---------- 本地資料庫 ----------
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

    # ---------- Session State 初始化 ----------
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
    if 'content_mode' not in st.session_state:
        st.session_state.content_mode = ""
    if 'raw_input_value' not in st.session_state:
        st.session_state.raw_input_value = ""
    if 'ref_number' not in st.session_state:
        st.session_state.ref_number = ""
    if 'current_entry' not in st.session_state:
        st.session_state.current_entry = {
            'v1': '', 'v2': '', 'w_sheet': '', 
            'p_sheet': '', 'grammar_list': '', 'other': ''
        }
    if 'saved_entries' not in st.session_state:
        st.session_state.saved_entries = []
    # 新增：編輯模式相關
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'edit_ref' not in st.session_state:
        st.session_state.edit_ref = None

    # 顯示連線狀態（Sidebar）
    with st.sidebar:
        st.divider()
        st.subheader("☁️ 連線狀態")
        if NOTION_TOKEN:
            st.success("✅ Notion Token 已設定")
        else:
            st.error("❌ Notion Token 未設定")
        
        if sheet_connected:
            st.success("✅ Google Sheet 已連線")
        else:
            st.error("❌ Google Sheet 未連線")

    # ═══════════════════════════════════════════════════════════════
    # 🆕 新增：快速功能區（空白資料建立器 + 編輯現有資料）
    # ═══════════════════════════════════════════════════════════════
    st.markdown("<h6>⚡ 快速功能</h6>", unsafe_allow_html=True)
    
    quick_cols = st.columns([1, 1, 2])
    
    with quick_cols[0]:
        # 空白資料建立器
        with st.expander("➕ 建立空白資料", expanded=False):
            blank_mode = st.selectbox("選擇模式", ["Mode A (經文)", "Mode B (文稿)"], key="blank_mode")
            blank_ref = st.text_input("參考編號", value=f"BLANK_{dt.datetime.now().strftime('%m%d%H%M')}", key="blank_ref")
            
            if st.button("🆕 建立空白資料結構", use_container_width=True):
                # 建立空白工作表結構
                if "Mode A" in blank_mode:
                    blank_structure = {
                        "ref": blank_ref,
                        "original": "[空白資料-待填入經文]",
                        "v1_content": "Ref.\tEnglish (ESV)\tChinese\tSyn/Ant\tGrammar\n",
                        "v2_content": "Ref.\t口語訳\tGrammar\tNote\tKRF\tSyn/Ant\tTHSV11\n",
                        "w_sheet": "",
                        "p_sheet": "",
                        "grammar_list": "",
                        "other": "",
                        "saved_sheets": ["V1 Sheet", "V2 Sheet"],
                        "type": "Scripture",
                        "mode": "A",
                        "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "blank_template": True
                    }
                else:
                    blank_structure = {
                        "ref": blank_ref,
                        "original": "[空白資料-待填入文稿]",
                        "v1_content": "",
                        "v2_content": "",
                        "w_sheet": "No\tWord/Phrase\tChinese\tSynonym+中文對照\tAntonym+中文對照\t全句聖經中英對照例句\n",
                        "p_sheet": "Paragraph\tEnglish Refinement\t中英夾雜講章\n",
                        "grammar_list": "No\tOriginal Sentence\tGrammar Rule\tAnalysis & Example\n",
                        "other": "",
                        "saved_sheets": ["W Sheet", "P Sheet", "Grammar List"],
                        "type": "Document",
                        "mode": "B",
                        "date_added": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "blank_template": True
                    }
                
                # 存入 session_state
                st.session_state.sentences[blank_ref] = blank_structure
                save_sentences(st.session_state.sentences)
                
                # 自動進入編輯模式
                st.session_state.edit_mode = True
                st.session_state.edit_ref = blank_ref
                st.session_state.current_entry = {
                    'v1': blank_structure['v1_content'],
                    'v2': blank_structure['v2_content'],
                    'w_sheet': blank_structure['w_sheet'],
                    'p_sheet': blank_structure['p_sheet'],
                    'grammar_list': blank_structure['grammar_list'],
                    'other': ''
                }
                st.success(f"✅ 已建立空白資料：{blank_ref}")
                st.rerun()
    
    with quick_cols[1]:
        # 編輯現有資料
        with st.expander("✏️ 編輯現有資料", expanded=False):
            if st.session_state.sentences:
                edit_select = st.selectbox(
                    "選擇要編輯的資料",
                    list(st.session_state.sentences.keys()),
                    format_func=lambda x: f"{x} ({st.session_state.sentences[x].get('type', 'Unknown')})",
                    key="edit_select"
                )
                
                if st.button("📝 載入編輯", use_container_width=True):
                    item = st.session_state.sentences[edit_select]
                    st.session_state.edit_mode = True
                    st.session_state.edit_ref = edit_select
                    st.session_state.current_entry = {
                        'v1': item.get('v1_content', ''),
                        'v2': item.get('v2_content', ''),
                        'w_sheet': item.get('w_sheet', ''),
                        'p_sheet': item.get('p_sheet', ''),
                        'grammar_list': item.get('grammar_list', ''),
                        'other': item.get('other', '')
                    }
                    st.session_state.saved_entries = item.get('saved_sheets', [])
                    st.rerun()
            else:
                st.info("尚無資料可編輯")
    
    with quick_cols[2]:
        # 顯示目前狀態
        if st.session_state.edit_mode and st.session_state.edit_ref:
            st.info(f"📝 目前正在編輯：**{st.session_state.edit_ref}**")
            if st.button("❌ 結束編輯模式", use_container_width=True):
                st.session_state.edit_mode = False
                st.session_state.edit_ref = None
                st.session_state.saved_entries = []
                st.session_state.current_entry = {
                    'v1': '', 'v2': '', 'w_sheet': '', 
                    'p_sheet': '', 'grammar_list': '', 'other': ''
                }
                st.rerun()
        else:
            st.caption("💡 使用左側按鈕快速建立或編輯資料")

    st.divider()

    # ═══════════════════════════════════════════════════════════════
    # 🆕 新增：編輯模式介面（當 edit_mode = True 時顯示）
    # ═══════════════════════════════════════════════════════════════
    if st.session_state.edit_mode and st.session_state.edit_ref:
        st.markdown(f"<h6>✏️ 編輯模式：{st.session_state.edit_ref}</h6>", unsafe_allow_html=True)
        
        item = st.session_state.sentences.get(st.session_state.edit_ref, {})
        current_mode = item.get('mode', 'A')
        
        # 根據模式顯示對應的工作表編輯區
        if current_mode == 'A':
            edit_tabs = st.tabs(["V1 Sheet", "V2 Sheet", "其他補充", "儲存"])
            
            with edit_tabs[0]:
                new_v1 = st.text_area(
                    "V1 Sheet 內容",
                    value=st.session_state.current_entry['v1'],
                    height=300,
                    key="edit_v1"
                )
                st.session_state.current_entry['v1'] = new_v1
            
            with edit_tabs[1]:
                new_v2 = st.text_area(
                    "V2 Sheet 內容",
                    value=st.session_state.current_entry['v2'],
                    height=300,
                    key="edit_v2"
                )
                st.session_state.current_entry['v2'] = new_v2
            
            with edit_tabs[2]:
                new_other = st.text_area(
                    "其他補充",
                    value=st.session_state.current_entry['other'],
                    height=200,
                    key="edit_other"
                )
                st.session_state.current_entry['other'] = new_other
            
            with edit_tabs[3]:
                st.write("確認修改後儲存：")
                save_cols = st.columns(4)
                
                with save_cols[0]:
                    if st.button("💾 存到本地", use_container_width=True):
                        st.session_state.sentences[st.session_state.edit_ref].update({
                            'v1_content': st.session_state.current_entry['v1'],
                            'v2_content': st.session_state.current_entry['v2'],
                            'other': st.session_state.current_entry['other'],
                            'saved_sheets': ['V1 Sheet', 'V2 Sheet'] if st.session_state.current_entry['v1'] else [],
                            'date_added': dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        save_sentences(st.session_state.sentences)
                        st.success("✅ 已更新本地資料！")
                
                with save_cols[1]:
                    if NOTION_TOKEN:
                        if st.button("🚀 同步 Notion", use_container_width=True, type="primary"):
                            data = {
                                "original": item.get('original', ''),
                                "v1_content": st.session_state.current_entry['v1'],
                                "v2_content": st.session_state.current_entry['v2'],
                                "w_sheet": "",
                                "p_sheet": "",
                                "grammar_list": "",
                                "other": st.session_state.current_entry['other'],
                                "ref": st.session_state.edit_ref,
                                "mode": f"Mode {current_mode}",
                                "type": item.get('type', 'Scripture')
                            }
                            success, msg, page_id = save_to_notion(data)
                            if success:
                                st.session_state.sentences[st.session_state.edit_ref]['notion_synced'] = True
                                st.session_state.sentences[st.session_state.edit_ref]['notion_page_id'] = page_id
                                save_sentences(st.session_state.sentences)
                                st.success("✅ 已同步 Notion！")
                            else:
                                st.error(f"❌ 同步失敗：{msg}")
                    else:
                        st.button("🚀 Notion", disabled=True, use_container_width=True)
                
                with save_cols[2]:
                    st.button("📊 Google", disabled=True, use_container_width=True)
                
                with save_cols[3]:
                    if st.button("💾🚀 本地+Notion", use_container_width=True):
                        # 本地
                        st.session_state.sentences[st.session_state.edit_ref].update({
                            'v1_content': st.session_state.current_entry['v1'],
                            'v2_content': st.session_state.current_entry['v2'],
                            'other': st.session_state.current_entry['other'],
                            'saved_sheets': ['V1 Sheet', 'V2 Sheet'] if st.session_state.current_entry['v1'] else [],
                            'date_added': dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        save_sentences(st.session_state.sentences)
                        
                        # Notion
                        if NOTION_TOKEN:
                            data = {
                                "original": item.get('original', ''),
                                "v1_content": st.session_state.current_entry['v1'],
                                "v2_content": st.session_state.current_entry['v2'],
                                "w_sheet": "",
                                "p_sheet": "",
                                "grammar_list": "",
                                "other": st.session_state.current_entry['other'],
                                "ref": st.session_state.edit_ref,
                                "mode": f"Mode {current_mode}",
                                "type": item.get('type', 'Scripture')
                            }
                            success, msg, page_id = save_to_notion(data)
                            if success:
                                st.session_state.sentences[st.session_state.edit_ref]['notion_synced'] = True
                                st.session_state.sentences[st.session_state.edit_ref]['notion_page_id'] = page_id
                                save_sentences(st.session_state.sentences)
                        
                        st.success("✅ 已同步本地與 Notion！")
        
        else:  # Mode B
            edit_tabs = st.tabs(["W Sheet", "P Sheet", "Grammar List", "其他補充", "儲存"])
            
            with edit_tabs[0]:
                new_w = st.text_area(
                    "W Sheet 內容",
                    value=st.session_state.current_entry['w_sheet'],
                    height=300,
                    key="edit_w"
                )
                st.session_state.current_entry['w_sheet'] = new_w
            
            with edit_tabs[1]:
                new_p = st.text_area(
                    "P Sheet 內容",
                    value=st.session_state.current_entry['p_sheet'],
                    height=300,
                    key="edit_p"
                )
                st.session_state.current_entry['p_sheet'] = new_p
            
            with edit_tabs[2]:
                new_g = st.text_area(
                    "Grammar List 內容",
                    value=st.session_state.current_entry['grammar_list'],
                    height=300,
                    key="edit_g"
                )
                st.session_state.current_entry['grammar_list'] = new_g
            
            with edit_tabs[3]:
                new_other = st.text_area(
                    "其他補充",
                    value=st.session_state.current_entry['other'],
                    height=200,
                    key="edit_other_b"
                )
                st.session_state.current_entry['other'] = new_other
            
            with edit_tabs[4]:
                st.write("確認修改後儲存：")
                save_cols = st.columns(4)
                
                with save_cols[0]:
                    if st.button("💾 存到本地", use_container_width=True):
                        st.session_state.sentences[st.session_state.edit_ref].update({
                            'w_sheet': st.session_state.current_entry['w_sheet'],
                            'p_sheet': st.session_state.current_entry['p_sheet'],
                            'grammar_list': st.session_state.current_entry['grammar_list'],
                            'other': st.session_state.current_entry['other'],
                            'saved_sheets': ['W Sheet', 'P Sheet', 'Grammar List'],
                            'date_added': dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        save_sentences(st.session_state.sentences)
                        st.success("✅ 已更新本地資料！")
                
                with save_cols[1]:
                    if NOTION_TOKEN:
                        if st.button("🚀 同步 Notion", use_container_width=True, type="primary"):
                            data = {
                                "original": item.get('original', ''),
                                "v1_content": "",
                                "v2_content": "",
                                "w_sheet": st.session_state.current_entry['w_sheet'],
                                "p_sheet": st.session_state.current_entry['p_sheet'],
                                "grammar_list": st.session_state.current_entry['grammar_list'],
                                "other": st.session_state.current_entry['other'],
                                "ref": st.session_state.edit_ref,
                                "mode": f"Mode {current_mode}",
                                "type": item.get('type', 'Document')
                            }
                            success, msg, page_id = save_to_notion(data)
                            if success:
                                st.session_state.sentences[st.session_state.edit_ref]['notion_synced'] = True
                                st.session_state.sentences[st.session_state.edit_ref]['notion_page_id'] = page_id
                                save_sentences(st.session_state.sentences)
                                st.success("✅ 已同步 Notion！")
                            else:
                                st.error(f"❌ 同步失敗：{msg}")
                    else:
                        st.button("🚀 Notion", disabled=True, use_container_width=True)
                
                with save_cols[2]:
                    st.button("📊 Google", disabled=True, use_container_width=True)
                
                with save_cols[3]:
                    if st.button("💾🚀 本地+Notion", use_container_width=True):
                        st.session_state.sentences[st.session_state.edit_ref].update({
                            'w_sheet': st.session_state.current_entry['w_sheet'],
                            'p_sheet': st.session_state.current_entry['p_sheet'],
                            'grammar_list': st.session_state.current_entry['grammar_list'],
                            'other': st.session_state.current_entry['other'],
                            'saved_sheets': ['W Sheet', 'P Sheet', 'Grammar List'],
                            'date_added': dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        save_sentences(st.session_state.sentences)
                        
                        if NOTION_TOKEN:
                            data = {
                                "original": item.get('original', ''),
                                "v1_content": "",
                                "v2_content": "",
                                "w_sheet": st.session_state.current_entry['w_sheet'],
                                "p_sheet": st.session_state.current_entry['p_sheet'],
                                "grammar_list": st.session_state.current_entry['grammar_list'],
                                "other": st.session_state.current_entry['other'],
                                "ref": st.session_state.edit_ref,
                                "mode": f"Mode {current_mode}",
                                "type": item.get('type', 'Document')
                            }
                            success, msg, page_id = save_to_notion(data)
                            if success:
                                st.session_state.sentences[st.session_state.edit_ref]['notion_synced'] = True
                                st.session_state.sentences[st.session_state.edit_ref]['notion_page_id'] = page_id
                                save_sentences(st.session_state.sentences)
                        
                        st.success("✅ 已同步本地與 Notion！")
        
        st.divider()

    # ═══════════════════════════════════════════════════════════════
    # 原有的 AI 分析工作流程（只在非編輯模式時顯示）
    # ═══════════════════════════════════════════════════════════════
    if not st.session_state.edit_mode:
        st.markdown("<h6>📝 AI 分析工作流程</h6>", unsafe_allow_html=True)
        
        # ... [原有的 STEP 1-4 程式碼保持不變] ...
        # === STEP 1: 輸入區 ===
        with st.expander("步驟 1：輸入經文或文稿", expanded=not st.session_state.is_prompt_generated):
            raw_input = st.text_area(
                "原始輸入",
                height=200,
                value=st.session_state.get('raw_input_value', ''),
                placeholder="請在此貼上內容：\n• 經文格式：31:6 可以把濃酒給將亡的人喝...\n• 文稿格式：直接貼上英文講稿",
                label_visibility="collapsed",
                key="raw_input_temp"
            )
            
            if not st.session_state.is_prompt_generated:
                if st.button("⚡ 產生完整分析指令", use_container_width=True, type="primary"):
                    # generate_full_prompt() 函數保持不變
                    raw_text = st.session_state.get("raw_input_temp", "").strip()
                    if raw_text:
                        mode = "A" if re.search(r'[\u4e00-\u9fa5]', raw_text) else "B"
                        # ... [原有的 prompt 產生邏輯] ...
                        st.session_state.content_mode = mode
                        st.session_state.original_text = raw_text
                        st.session_state.is_prompt_generated = True
                        st.session_state.ref_number = f"REF_{dt.datetime.now().strftime('%m%d%H%M')}"
                        st.rerun()

        # ... [原有的 STEP 2-4 程式碼] ...

    # ---------- 底部統計 ----------
    st.divider()
    total_count = len(st.session_state.get('sentences', {}))
    st.caption(f"💾 資料庫：{total_count} 筆")

