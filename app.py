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
# [區塊 2] 側邊欄 (Sidebar) 控制台(Mashimaro3 縮小)
# ==========================================
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다</p>', unsafe_allow_html=True)
    # 控制台圖片縮小
    st.image(IMG_URLS["M3"], width=250) 
    st.divider()
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/", use_container_width=True)
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
        # 這裡把圖片和框框鎖在一起
        st.markdown(f"""
            <div style="text-align: center;">
                <img src="{IMG_URLS['M1']}" style="width: 250px; display: block; margin: 0 auto;">
                <div style="background-color: #f8f9fa; border-radius: 8px; padding: 12px; border-left: 5px solid #FF8C00; text-align: left; margin-top: -10px;">
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
    # 下方例句也用兩欄，這樣手機版會自動疊在一起，電腦版則橫排
    cl1, cl2 = st.columns(2)
    with cl1:
        st.markdown("**Ex 1:** *Casual attire is not becoming to a CEO...* <p class='small-font'>便服對執行長不相稱。</p>", unsafe_allow_html=True)
    with cl2:
        st.markdown("**Ex 2:** *Wealth is not becoming to a man without virtue...* <p class='small-font'>財富對於無德之人不相稱。</p>", unsafe_allow_html=True)
# [區塊 4] TAB 2: 筆記與折疊式待辦
# ==========================================
with tabs[1]:
    with st.expander("📅 點擊展開：日期篩選、待辦事項與鬧鈴設定", expanded=False):
        c1, c2, c3 = st.columns([0.3, 0.4, 0.3])
        sel_date = c1.date_input("選擇日期", value=datetime(2026, 1, 16))
        todo_task = c2.text_input("待辦事項內容", placeholder="輸入任務...")
        alarm_t = c3.time_input("設定提醒鬧鈴", dt.time(9, 0))
        if st.button("➕ 確認存入待辦清單", use_container_width=True):
            st.toast(f"已排程 {sel_date} {alarm_t}: {todo_task}")

    st.divider()

    t2_left, t2_right = st.columns([0.7, 0.3])
    with t2_left:
        note_name = st.text_input("筆記標題", value=f"{sel_date} 靈修筆記", label_visibility="collapsed")
        if st.button(f"💾 存檔筆記：{note_name[:15]}...", use_container_width=True):
            st.success("筆記已存檔！")
    with t2_right:
        st.write("<span style='font-size:12px;'><b>日:</b> すぐれた言葉は...<br><b>韓:</b> 미련한 자에게...<br><b>泰:</b> ริมฝีปากที่ประเสริฐ...</span>", unsafe_allow_html=True)
        st.image(IMG_URLS["C"], width=80)

    st.text_area("筆記📝", height=250, placeholder="", label_visibility="visible")

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
