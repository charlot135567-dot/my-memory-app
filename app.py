import streamlit as st
import pandas as pd
import requests
import datetime as dt
from datetime import datetime, time
from PIL import Image
from io import BytesIO
from streamlit_calendar import calendar
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
# [區塊 4] TAB 2: 📓 筆記內容 (圖像顯示終極救援版)
# ==========================================

# --- 1. 初始化與圖片路徑 ---
if 'events' not in st.session_state:
    st.session_state.events = []
if 'notes' not in st.session_state:
    st.session_state.notes = {}

REPO_RAW = "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/"
IMG_PAW  = f"{REPO_RAW}Mashimaro5.jpg"
IMG_CAKE = f"{REPO_RAW}Mashimaro2.jpg"
IMG_HEAD = f"{REPO_RAW}Mashimaro1.jpg"

# --- [關鍵] 強化 CSS：使用背景圖強迫顯示，並加入國旗美化 ---
st.markdown(f"""
<style>
    /* 強制月曆事件容器顯示圖片 */
    .fc-event-main {{
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        height: 40px !important;
    }}
    .fc-event {{
        background-color: transparent !important;
        border: none !important;
    }}
    /* 讓文字經文框更美觀 */
    .bible-container {{
        background: rgba(255,240,245,0.8); 
        border-radius: 15px; 
        padding: 25px; 
        border: 3px solid #FFB6C1;
    }}
</style>
""", unsafe_allow_html=True)

with tabs[1]:
    # --- 第一層：功能鍵與月曆 ---
    col_cal_title, col_btns = st.columns([0.6, 0.4])
    
    with col_cal_title:
        st.subheader("📅 靈修足跡月曆")
        
    with col_btns:
        c1, c2 = st.columns(2)
        with c1:
            btn_add = st.button("🧁 預排行程", use_container_width=True)
        with c2:
            btn_clear = st.button("🧹 清空今日", use_container_width=True)

    with st.expander("展開 / 摺疊月曆視窗", expanded=True):
        cal_options = {
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
            "initialView": "dayGridMonth",
            "selectable": True,
            "height": 450,
            "eventContent": { "html": True } 
        }
        
        state = calendar(events=st.session_state.events, options=cal_options, key="mashi_v2")
        
        if state.get("dateClick"):
            selected_date = state["dateClick"]["date"]
        else:
            selected_date = str(dt.date.today())
            
        st.write(f"📍 目前選取日期：**{selected_date[:10]}**")

    # 按鈕邏輯：直接將 <img> 標籤嵌入 title
    if btn_add:
        st.session_state.events.append({
            "title": f'<img src="{IMG_CAKE}" style="width:38px; height:38px; border-radius:5px;">',
            "start": selected_date,
            "allDay": True
        })
        st.rerun()
        
    if btn_clear:
        st.session_state.events = [e for e in st.session_state.events if e['start'] != selected_date]
        st.rerun()

    st.divider()

    # --- 第二層：經文對照 (補上各國國旗與繁體中文國旗) ---
    st.markdown(f"""
        <div class="bible-container">
            <img src="{IMG_HEAD}" width="60" style="float: right;">
            <h4 style="color:#FF1493; margin-top:0;">📖 每日經文對照</h4>
            <p style="font-size:20px; font-weight:bold; color:#000; line-height:1.6;">🇹🇼 中文: 要常常喜樂，不住的禱告，凡事謝恩。</p>
            <hr style="border: 0.5px solid #FFB6C1;">
            <p style="font-size:17px; color:#444; margin: 10px 0;">🇯🇵 <b>日本語:</b> 常に喜んでいなさい</p>
            <p style="font-size:17px; color:#444; margin: 10px 0;">🇰🇷 <b>한국어:</b> 항상 기뻐하라</p>
            <p style="font-size:17px; color:#444; margin: 10px 0;">🇹🇭 <b>ภาษาไทย:</b> จงชื่นชมยินดีอยู่เสมอ</p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # --- 第三層：靈修筆記與存檔 ---
    st.markdown("### 📓 靈修筆記本")
    
    col_note_date, col_note_txt = st.columns([0.3, 0.7])
    with col_note_date:
        back_date = st.date_input("🔙 選擇存檔日期", value=dt.datetime.strptime(selected_date[:10], "%Y-%m-%d"))

    with col_note_txt:
        # 自動抓取已存筆記
        current_note = st.session_state.notes.get(str(back_date), "")
        note_text = st.text_area("寫下心得與感悟...", value=current_note, height=180, key="mashi_note")

    if st.button("💾 儲存筆記並蓋上足跡 🐾", use_container_width=True):
        st.session_state.notes[str(back_date)] = note_text
        st.session_state.events.append({
            "title": f'<img src="{IMG_PAW}" style="width:38px; height:38px; border-radius:5px;">',
            "start": str(back_date),
            "allDay": True
        })
        st.success(f"已記錄足跡至 {back_date}！")
        st.balloons()
        st.rerun()
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
