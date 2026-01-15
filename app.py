import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from PIL import Image, ImageChops
import requests
from io import BytesIO

# --- 1. 頁面基礎設定 ---
st.set_page_config(layout="wide", page_title="Bible Study AI App 2026")

# --- 2. 自動裁切函數：刪除史努比圖片空白處 ---
def get_cropped_image(url):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        # 建立純白背景作為比對基準
        bg = Image.new(img.mode, img.size, (255, 255, 255, 255))
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox() # 尋找非空白邊界
        if bbox:
            return img.crop(bbox)
        return img
    except:
        return None

# --- 3. Google Sheets 連線 ---
# 提醒：請確保在 Streamlit Cloud 的 Secrets 設定好連結
conn = st.connection("gsheets", type=GSheetsConnection)

# 史努比照片網址 (位於根目錄)
IMG_URLS = {
    "A": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg",
    "B": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/f364bd220887627.67cae1bd07457.jpg",
    "C": "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/68254faebaafed9dafb41918f74c202e.jpg"
}

# --- 4. 主要 UI 配置 ---
tabs = st.tabs(["🏠 書桌", "📓 每日筆記", "✍️ 翻譯挑戰", "📂 資料庫"])

with tabs[0]: # TAB1: 書桌
    col_left, col_right = st.columns([0.6, 0.4])
    with col_left:
        st.subheader("📚 核心單字與片語")
        # 內容省略...
    
    with col_right:
        # 這裡會自動套用裁切邏輯，讓史努比緊貼邊框
        img_a = get_cropped_image(IMG_URLS["A"])
        if img_a: st.image(img_a, use_container_width=True)
        
        img_b = get_cropped_image(IMG_URLS["B"])
        if img_b: st.image(img_b, use_container_width=True)

# --- TAB4: 資料庫 (存檔功能) ---
with tabs[3]:
    st.subheader("📂 資料存檔")
    # ... (保留之前的資料庫存檔邏輯代碼)

# --- TAB1: 書桌 (🏠 + 待辦事項) ---
with tabs[0]:
    col_left, col_right = st.columns([0.6, 0.4])
    
    with col_left:
        st.subheader("📚 核心單字與片語")
        lang_show = st.multiselect("語言顯示選擇", ["日", "韓", "泰"], default=["日"])
        
        c1, c2 = st.columns(2)
        with c1:
            # 這裡之後可以改成從 Google Sheets 動態讀取最新一筆 W/P Sheet
            st.info("**單字 (Vocab)**\n\nBecoming / 相稱") 
            if "日" in lang_show: st.write("🇯🇵 ふさわしい")
            if "韓" in lang_show: st.write("🇰🇷 어울리는")
            if "泰" in lang_show: st.write("🇹🇭 เหมาะสม")
        with c2:
            st.info("**片語 (Phrase)**\n\nStill less / 何況")

        st.divider()
        st.subheader("🌟 今日金句 (V1 Sheet)")
        # 這裡之後可以改成從 Google Sheets 讀取今日經文
        st.success("**Pro 17:07**\n\nFine speech is not becoming to a fool; still less is false speech to a prince.")

        with st.expander("📝 文法解析 (V1 Sheet)", expanded=True):
            st.markdown("""
            - **時態**: 現在簡單式表達恆常真理。
            - **核心詞彙**: Becoming to (形容詞片語)。
            - **句型**: 倒裝句 (Still less is...)。
            """)

    with col_right:
        st.image(IMG_URLS["A"], use_container_width=True)
        st.image(IMG_URLS["B"], use_container_width=True)

# --- TAB2: 每日筆記 --- (省略中間重複代碼，保持結構一致)
with tabs[1]:
    # ... (保留你原本的月曆與篩選代碼)
    st.subheader("📅 筆記月曆")
    st.date_input("選擇日期以查看筆記", datetime.now())
    # 右側顯示多語對照 (V2 Sheet)
    # ...

# --- TAB4: 資料庫 (輸入與正式存檔邏輯) ---
with tabs[3]:
    st.subheader("🔗 聖經與 AI 資源")
    cl1, cl2, cl3, cl4 = st.columns(4)
    cl1.link_button("ChatGPT", "https://chat.openai.com/")
    cl2.link_button("Google AI", "https://gemini.google.com/")
    cl3.link_button("ESV", "https://wd.bible/bible/gen.1.cunps?parallel=esv.klb.jcb")
    cl4.link_button("THSV11", "https://www.bible.com/zh-TW/bible/174/GEN.1.THSV11")

    st.divider()
    
    # 資料輸入區
    input_ref = st.text_input("Ref. (例如: Pro 17:07)")
    input_content = st.text_area("📥 聖經經文 / 英文文稿輸入", height=150)
    
    btn_l, btn_r = st.columns(2)
    
    if btn_l.button("📥 輸入 - 經文/文稿"):
        st.toast("已讀取內容，請傳送至 AI 進行解析後回填。")
        
    if btn_r.button("💾 存檔 - AI 解析完資料"):
        if input_ref and input_content:
            try:
                # 1. 讀取現有的 Verse1 工作表
                df = conn.read(worksheet="Verse1")
                
                # 2. 建立新資料 (這裡假設你貼入的是 AI 產出的內容，暫時以簡化版示範)
                # 實務上可以針對 Markdown 表格做解析
                new_data = pd.DataFrame([{"Ref.": input_ref, "ESV": input_content}])
                
                # 3. 合併並更新
                updated_df = pd.concat([df, new_data], ignore_index=True)
                conn.update(worksheet="Verse1", data=updated_df)
                
                st.success(f"資料已成功存入 Google Sheets (Ref: {input_ref})！")
            except Exception as e:
                st.error(f"存檔至 Google Sheets 時發生錯誤: {e}")
        else:
            st.warning("請輸入 Ref. 與內容後再存檔。")
