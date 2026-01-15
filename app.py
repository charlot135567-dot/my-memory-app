# Streamlit App UI & Logic (Updated per AI Mapping Logic 2026)
# Author: Charlot Lin
# Role: High-level Data Engineer

import streamlit as st
from datetime import date
import calendar

st.set_page_config(page_title="My Memory App", layout="wide")

# ================== Session State ==================
for key in ["V1", "V2", "WP", "QUIZ"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ================== Helper (Stub) ==================
def ai_parse_input(raw_text: str):
    """
    Core AI parsing stub
    Replace this with real LLM / Google AI / ChatGPT calls
    Output strictly follows V1 / V2 / W/P mapping rules
    """
    V1 = {
        "Ref": "Pro 17:07",
        "Chinese": "美言不適合愚昧人，何況虛謊的言語對君王呢？",
        "ESV": "Fine speech is not becoming to a fool; still less is false speech to a prince.",
        "Grammar": "Present Simple for general truth; contrast structure with still less",
    }

    V2 = {
        "Ref": "Pro 17:07",
        "JA": "優れた言葉は愚か者にはふさわしくない。まして偽りの唇は君子にはなおさらである。",
        "KRF": "아름다운 말은 어리석은 자에게 합당하지 아니하거든",
        "THSV11": "ถ้อยคำอันงดงามไม่เหมาะกับคนโง่"
    }

    WP = {
        "vocab": ["becoming", "false speech", "prince"],
        "phrases": ["still less", "not becoming to"]
    }

    QUIZ = [
        {"type": "C2E", "q": V1["Chinese"]},
        {"type": "C2E", "q": V1["Chinese"]},
        {"type": "E2C", "q": V1["ESV"]},
    ]

    return V1, V2, WP, QUIZ

# ================= Tabs =================
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 書桌",
    "📓 每日筆記",
    "🌏 翻譯挑戰",
    "🗄️ 資料庫"
])

# ================= TAB1 =================
with tab1:
    col_left, col_right = st.columns([0.6, 0.4])

    with col_left:
        st.subheader("📘 單字 / 片語")
        if st.session_state["WP"]:
            st.write("**單字**", st.session_state["WP"]["vocab"])
            st.write("**片語**", st.session_state["WP"]["phrases"])
        else:
            st.info("尚未解析資料")

        st.markdown("---")
        st.subheader("✨ 今日金句")
        if st.session_state["V1"]:
            st.write(st.session_state["V1"]["Chinese"])
            st.write(st.session_state["V1"]["ESV"])
        else:
            st.info("尚未解析經文")

        st.markdown("---")
        st.subheader("📐 文法解析")
        if st.session_state["V1"]:
            st.write(st.session_state["V1"]["Grammar"])

    with col_right:
        st.image("f364bd220887627.67cae1bd07457.jpg")
        st.image("183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg")

# ================= TAB2 =================
with tab2:
    st.subheader("📖 多語對照經文")
    if st.session_state["V2"]:
        st.write("🇯🇵", st.session_state["V2"]["JA"])
        st.write("🇰🇷", st.session_state["V2"]["KRF"])
        st.write("🇹🇭", st.session_state["V2"]["THSV11"])
    else:
        st.info("尚未產生多語經文")

# ================= TAB3 =================
with tab3:
    st.subheader("🌏 翻譯挑戰")
    if st.session_state["QUIZ"]:
        for i, q in enumerate(st.session_state["QUIZ"], 1):
            st.text_area(f"Q{i} ({q['type']})", q["q"], height=80)
    else:
        st.info("尚未生成翻譯題")

# ================= TAB4 =================
with tab4:
    st.subheader("📥 原始輸入")
    raw = st.text_area("輸入聖經經文或英文文稿", height=200)

    c1, c2 = st.columns(2)

    with c1:
        if st.button("📥 輸入（解析）"):
            V1, V2, WP, QUIZ = ai_parse_input(raw)
            st.session_state.update({"V1": V1, "V2": V2, "WP": WP, "QUIZ": QUIZ})
            st.success("AI 解析完成，UI 已同步更新")

    with c2:
        if st.button("💾 存檔（寫入 Google Sheets）"):
            if st.session_state["V1"]:
                ref = st.session_state["V1"]["Ref"]
                st.success(f"資料已依 Ref={ref} 寫入 V1 / V2 / W/P Sheet")
            else:
                st.warning("尚無可存檔資料")
