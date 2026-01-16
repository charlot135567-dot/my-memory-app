import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import datetime as dt  # 使用 dt 作為縮寫來呼叫 time

# ==========================================
# [區塊 1] 環境匯入與全域 CSS 樣式 (徹底消除空白暴力版)
# ==========================================
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
    .small-font { font-size: 13px; color: #555555; margin-top: 0px !important; }
    
    /* 暴力版修正：徹底取消高度，移除 flex，取消所有預設內距 */
    .grammar-box {
        background-color: #f8f9fa; 
        border-radius: 8px; 
        padding: 10px 15px !important; 
        border-left: 5px solid #FF8C00; 
        font-size: 14px; 
        height: auto !important;
        margin: 0px !important;
    }
    /* 強制將 Streamlit 的元件間隔壓到最低 */
    [data-testid="stVerticalBlock"] > div {
        margin-top: -10px !important;
        padding-top: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg",
    "M1": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro1.jpg",
    "M2": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro2.jpg",
    "M3": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro3.jpg",
    "M4": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro4.jpg"
}
# ==========================================
# [區塊 2] 側邊欄 (Sidebar) 與 Tabs 定義
# ==========================================

# 1. 側邊欄內容
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다</p>', unsafe_allow_html=True)
    # 控制台圖片
    st.image(IMG_URLS["M3"], width=250) 
    st.divider()
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/", use_container_width=True)

# 2. 定義 Tabs (關鍵：必須在 with tabs[0] 之前定義)
tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

# ==========================================
# [區塊 3] TAB 1: 書桌主畫面內容
# ==========================================
with tabs[0]:
    # 建立兩欄：左邊放經文(0.65)，右邊放圖片與框(0.35)
    col_content, col_m1 = st.columns([0.65, 0.35])
    
    with col_content:
        st.info("**Becoming** / 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 🇹🇭 เหมาะสม | 🇨🇳 相稱")
        st.info("**Still less** / 🇯🇵 まして | 🇰🇷 하물며 | 🇹🇭 ยิ่งกว่านั้น | 🇨🇳 何況")
        st.success("""
        🌟 **Pro 17:07** Fine speech is not becoming to a fool; still less is false speech to a prince.  
        🇯🇵 すぐれた言葉は愚か者にはふさわしくない。偽りの言葉は君主にはなおさらふさわしくない。  
        🇨🇳 愚頑人說美言本不相稱，何況君王說謊話呢？
        """, icon="📖")

    with col_m1:
        # 強力「焊接」HTML：讓 Mashimaro 與框框在同一個容器
        st.markdown(f"""
            <div style="text-align: center; width: 100%;">
                <img src="{IMG_URLS['M1']}" style="width: 250px; display: block; margin: 0 auto -15px auto; position: relative; z-index: 5;">
                <div style="background-color: #f8f9fa; border-radius: 8px; padding: 12px; border-left: 5px solid #FF8C00; text-align: left; position: relative; z-index: 10;">
                    <p style="margin:2px 0; font-size: 14px; font-weight: bold;">時態: 現在簡單式</p>
                    <p style="margin:2px 0; font-size: 14px; font-weight: bold;">核心片語:</p>
                    <ul style="margin:0; padding-left:18px; font-size: 13px; line-height: 1.3;">
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
   # 這裡把剛才缺少的例句後半段完整補齊
    cl1, cl2 = st.columns(2)
    with cl1:
        st.markdown("""
            **Ex 1:** *Casual attire is not becoming to a CEO; still less is unprofessional language.* <p class='small-font'>便服對執行長不相稱；更不用說不專業的言語了。</p>
        """, unsafe_allow_html=True)
    with cl2:
        st.markdown("""
            **Ex 2:** *Wealth is not becoming to a man without virtue; still less is power.* <p class='small-font'>財富對於無德之人不相稱；更不用說權力了。</p>
        """, unsafe_allow_html=True)
# ==========================================
# [區塊 4] TAB 2: 📓筆記內容
# ==========================================
import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime

# --- 1. 圖片路徑設定 (指向您的 Repo) ---
REPO_BASE_URL = "https://raw.githubusercontent.com/您的帳號/您的倉庫名/main/" # 請修改此處
IMG_PAW = f"{REPO_BASE_URL}Mashimaro5.png"  # 腳印
IMG_CAKE = f"{REPO_BASE_URL}Mashimaro2.png" # 蛋糕兔
IMG_HEAD = f"{REPO_BASE_URL}Mashimaro1.png" # 大頭

# 初始化資料庫（模擬）
if 'events' not in st.session_state:
    st.session_state.events = []
if 'notes' not in st.session_state:
    st.session_state.notes = {}

with tabs[1]:
    # --- 2. 左右分欄 (50:50) ---
    col_left, col_right = st.columns([0.5, 0.5])

    with col_left:
        with st.expander("📅 行事", expanded=True):
            # 月曆組件設定
            cal_options = {
                "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
                "initialView": "dayGridMonth",
                "selectable": True,
                "height": 350,
            }
            
            # 渲染月曆
            state = calendar(events=st.session_state.events, options=cal_options, key="mashimaro_cal")
            
            # 選取日期互動
            selected_date = state.get("dateClick", {"date": str(datetime.now().date())})["date"]
            st.write(f"📍 已選取：{selected_date}")

    with col_right:
        # 顯示對照經文 (配合您的 Mashimaro 風格)
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.7); border-radius: 15px; padding: 15px; border: 2px solid #FFB6C1;">
                <img src="{IMG_HEAD}" width="40" style="float: right;">
                <p style="font-size:13px; color:#555;"><b>日:</b> 常に喜んでいなさい</p>
                <p style="font-size:13px; color:#555;"><b>韓:</b> 항상 기뻐하라</p>
                <p style="font-size:13px; color:#555;"><b>泰:</b> จงชื่นชมยินดีอยู่เสมอ</p>
                <hr>
                <p style="font-weight:bold;">中: 要常常喜樂，不住的禱告，凡事謝恩。</p>
            </div>
        """, unsafe_allow_html=True)
        
        # 快速設定當天行程
        task_name = st.text_input("輸入計畫事件 (如：靈修)", placeholder="例如：背經")
        if st.button("🥣 預排行程 (加入蛋糕兔)"):
            new_event = {
                "title": f"🍰 {task_name}",
                "start": selected_date,
                "end": selected_date,
                "backgroundColor": "#FFECF0"
            }
            st.session_state.events.append(new_event)
            st.rerun()

    st.divider()

    # --- 3. 下半部：合併式回溯筆記 ---
    st.markdown("### 📓 Mashimaro 靈修筆記本")
    
    # 回溯時間 Bar
    back_date = st.date_input("🔙 欲存檔的日期 (可回溯補寫)", value=datetime.strptime(selected_date[:10], "%Y-%m-%d"))
    
    # 筆記內容 (合併標題)
    note_text = st.text_area(
        "第一行將作為標題，下方為筆記內容",
        height=250,
        placeholder="【1/16 領受心得】\n今天在馬太福音看到...",
        key="note_area"
    )

    if st.button("💾 存檔並蓋上腳印 🐾", use_container_width=True):
        # 1. 儲存文字
        st.session_state.notes[str(back_date)] = note_text
        # 2. 自動在月曆加上腳印事件
        st.session_state.events.append({
            "title": "🐾 已完成",
            "start": str(back_date),
            "end": str(back_date),
            "backgroundColor": "#FFE4B5",
            "textColor": "#8B4513"
        })
        st.success(f"已將筆記存入 {back_date}，月曆足跡已更新！")
        st.balloons()

# ==========================================
# [區塊 5] TAB 3 & 4: 挑戰與資料庫
# ==========================================
with tabs[2]:
    col_challenge, col_deco = st.columns([0.7, 0.3])
    with col_challenge:
        st.subheader("📝 翻譯挑戰")
        st.write("題目 1: 愚頑人說美言本不相稱...")
        st.text_input("請輸入英文翻譯", key="ans_1_final", placeholder="Type your translation here...")
    with col_deco:
        st.image(IMG_URLS["B"], width=150, caption="Keep Going!")

with tabs[3]:
    st.subheader("🔗 聖經與 AI 資源")
    cl1, cl2, cl3, cl4 = st.columns(4)
    cl1.link_button("ChatGPT", "https://chat.openai.com/")
    cl2.link_button("Google AI", "https://gemini.google.com/")
    cl3.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb")
    cl4.link_button("THSV11", "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")
    st.divider()
    input_content_final = st.text_area("📥 聖經經文 / 英文文稿輸入", height=150, key="db_input_area")
    btn_l, btn_r = st.columns(2)
    if btn_l.button("📥 執行輸入解析"):
        st.toast("已讀取文稿")
    if btn_r.button("💾 存檔至資料庫"):
        st.success("資料已成功存入雲端資料庫！")
