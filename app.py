import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import datetime as dt  # 使用 dt 作為縮寫來呼叫 time

# ==========================================
# [區塊 1] 環境匯入與全域樣式設定 (CSS)
# ==========================================
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import datetime as dt  

st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap');
    .cute-korean { font-family: 'Gamja+Flower', cursive; font-size: 20px; color: #FF8C00; text-align: center; }
    .small-font { font-size: 13px; color: #555555; }
    
    .grammar-box {
        background-color: #f8f9fa; border-radius: 8px; padding: 15px;
        border-left: 5px solid #FF8C00; font-size: 14px; 
        height: 250px; 
        display: flex; flex-direction: column; justify-content: space-between;
    }
    
    .stVerticalBlock { gap: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg",
    "M1": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro1.jpg",
    "M3": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/Mashimaro3.jpg"
}

# ==========================================
# [區塊 2] 側邊欄 (Sidebar) 控制台
# ==========================================
with st.sidebar:
    st.markdown('<p class="cute-korean">당신은 하나님의 소중한 보물입니다<br><span style="font-size:12px;">(你是上帝寶貴的珍寶)</span></p>', unsafe_allow_html=True)
    # 控制台圖片 (Mashimaro3)
    st.image(IMG_URLS["M3"], use_container_width=True)
    st.divider()
    st.link_button("✨ 快速開啟 Google AI", "https://gemini.google.com/", use_container_width=True)

# ==========================================
# [區塊 3] TAB 1: 書桌主畫面 (今日金句與文法)
# ==========================================
tabs = st.tabs(["🏠 書桌", "📓 筆記", "✍️ 挑戰", "📂 資料庫"])

with tabs[0]:
    col_content, col_m1 = st.columns([0.65, 0.35])
    
    with col_content:
        st.info("**Becoming** / 🇯🇵 ふさわしい | 🇰🇷 어울리는 | 泰: เหมาะสม | 🇨🇳 相稱")
        st.info("**Still less** / 🇯🇵 まして | 🇰🇷 하물며 | 泰: ยิ่งกว่านั้น | 🇨🇳 何況")
        st.success("""
        🌟 **Pro 17:07** Fine speech is not becoming to a fool; still less is false speech to a prince.  
        🇯🇵 すぐれた言葉は愚か者にはふさわしくない。偽りの言葉は君主にはなおさらふさわしくない。  
        🇨🇳 愚頑人說美言本不相稱，何況君王說謊話呢？
        """, icon="📖")

    with col_m1:
        st.image(IMG_URLS["M1"], use_container_width=True)
        st.markdown("""
        <div class="grammar-box">
            <div>
                <b>時態(Tense):</b> 現在簡單式表達恆常真理<br>
                <b>核心片語與詞彙:</b><br>
                • Fine speech (優美言辭)<br>
                • Becoming to (相稱/合宜)<br>
                • Still less (何況)<br>
                • False speech (虛假言辭)
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    cg1, cg2 = st.columns(2)
    with cg1:
        st.markdown("**Ex 1:** Casual attire is not becoming to a CEO... <br><p class='small-font'>便服對執行長不相稱；更不用說不專業言語了。</p>", unsafe_allow_html=True)
    with cg2:
        st.markdown("**Ex 2:** Wealth is not becoming to a man without virtue... <br><p class='small-font'>財富對於無德之人不相稱；更不用說權力了。</p>", unsafe_allow_html=True)

# ==========================================
# [區塊 4] TAB 2: 每日筆記與待辦提醒
# ==========================================
with tabs[1]:
    top_l, top_r = st.columns([0.5, 0.5])
    
    with top_l:
        sel_date = st.date_input("選擇日期", value=datetime(2026, 1, 16), label_visibility="collapsed")
        st.write(f"📅 **{sel_date} 待辦與提醒設定**")
        
        c_todo, c_time = st.columns([0.7, 0.3])
        todo_item = c_todo.text_input("填入待辦事項", placeholder="輸入任務...", label_visibility="collapsed")
        remind_time = c_time.time_input("設定提醒", dt.time(9, 0), label_visibility="collapsed")
        
        if st.button("🔔 設定提醒並加入清單"):
            st.toast(f"已設定 {remind_time} 提醒：{todo_item}")

    with top_r:
        st.write("**📖 Pro 17:07 多語對照**")
        st.write("<span style='font-size:13px;'><b>日:</b> すぐれた言葉は愚か者には...<br><b>韓:</b> 미련한 자에게 격에 맞지 않는 말이...<br><b>泰:</b> ริมฝีปากที่ประเสริฐไม่คู่ควรกับคนโง่...</span>", unsafe_allow_html=True)
        st.image(IMG_URLS["C"], width=150)

    st.divider()

    note_col, save_col = st.columns([0.7, 0.3])
    note_name = note_col.text_input("筆記標題", value="2026-01-16 靈修筆記", label_visibility="collapsed")
    if save_col.button(f"💾 存檔: {note_name[:10]}...", use_container_width=True):
        st.success(f"筆記 '{note_name}' 已成功存檔！")

    st.text_area(label="筆記📝", value="", height=250, placeholder="筆記📝", label_visibility="visible")

# ==========================================
# [區塊 5] TAB 3 & 4: 挑戰與資料庫
# ==========================================
with tabs[2]:
    col_challenge, col_deco = st.columns([0.7, 0.3])
    with col_challenge:
        st.subheader("📝 翻譯挑戰")
        st.write("題目 1: 愚頑人說美言本不相稱...")
        st.text_input("請輸入英文翻譯", key="ans_1", placeholder="Type your translation here...")
    with col_deco:
        st.image(IMG_URLS["B"], width=200, caption="Keep Going!")

with tabs[3]:
    st.subheader("🔗 聖經與 AI 資源")
    cl1, cl2, cl3, cl4 = st.columns(4)
    cl1.link_button("ChatGPT", "https://chat.openai.com/")
    cl2.link_button("Google AI", "https://gemini.google.com/")
    cl3.link_button("ESV Bible", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb")
    cl4.link_button("THSV11", "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")
    st.divider()
    input_content = st.text_area("📥 聖經經文 / 英文文稿輸入", height=150, help="輸入中文經文(V 卷章節)或英文文稿")
    btn_l, btn_r = st.columns(2)
    if btn_l.button("📥 輸入 - 經文/文稿"):
        st.toast("已讀取文稿")
    if btn_r.button("💾 存檔 - AI 解析完資料"):
        st.success("資料已成功存入雲端資料庫！")
