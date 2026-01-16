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
with tabs[1]:
    # --- [保留原有的摺疊區概念，但視覺升級] ---
    with st.expander("📅 點擊展開：日期篩選與互動月曆", expanded=True):
        # 1. 月曆元件 (保留 c1 的功能)
        sel_date = st.date_input("選擇日期", value=datetime(2026, 1, 16))
        
        st.divider()

        # --- [這裡就是你想要的「彈跳窗感」輸入區] ---
        # 我們把原本的 c2 (任務) 和 c3 (鬧鈴) 裝進史努比背景裡
        st.markdown(f"""
            <div style="background-image: url('{IMG_URLS.get('SNOOPY_BG', 'https://example.com/snoopy.jpg')}'); 
                        background-size: cover; border-radius: 15px; padding: 20px;">
                <div style="background-color: rgba(255, 255, 255, 0.9); padding: 15px; border-radius: 10px; border: 1px solid #ddd;">
                    <p style="margin:0; font-weight:bold; color:#1E90FF;">📍 {sel_date} 事件設定</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 這裡放原本的 c2, c3 元件
        col_task, col_alarm = st.columns([0.6, 0.4])
        with col_task:
            todo_task = st.text_input("在此輸入事件", placeholder="例如：靈修、背經...", label_visibility="collapsed")
        with col_alarm:
            alarm_t = st.time_input("設定提醒鬧鈴", dt.time(15, 0), label_visibility="collapsed")
        
        # 原本的「確認存入」按鈕
        if st.button("✅ 確認儲存並開啟提醒", use_container_width=True):
            st.toast(f"已排程 {sel_date} {alarm_t}: {todo_task}")

    st.divider()

    # --- [下方筆記區：保留你原本的右側小提示] ---
    t2_left, t2_right = st.columns([0.7, 0.3])
    with t2_left:
        # 保留你的動態標題邏輯
        note_name = st.text_input("筆記標題", value=f"{sel_date} 靈修筆記")
        st.text_area("筆記📝", height=250, placeholder="在此輸入心得...")
        if st.button(f"💾 存檔筆記", use_container_width=True):
            st.success("筆記已存檔！")
            
    with t2_right:
        # 保留你精緻的多語系提示與圖片
        st.write("<span style='font-size:12px;'><b>日:</b> すぐれた言葉は...<br><b>韓:</b> 미련한 자에게...<br><b>泰:</b> ริมฝีปากที่ประเสริฐ...</span>", unsafe_allow_html=True)
        st.image(IMG_URLS.get("C", "https://via.placeholder.com/80"), width=80)

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
