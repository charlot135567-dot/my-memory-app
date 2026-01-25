# 0. 頂層只放「純 Python」套件與函式，不放任何 st.xxx
import streamlit as st
import datetime as dt
# ...其他 import

# ===================================================================
# TAB2 ─ 金句集（所有 st.xxx 與 datetime 都鎖在區塊內，頂層只剩純 Python）
# ===================================================================
with tabs[1]:
    import datetime as dt
    from datetime import datetime, timezone, timedelta

    # ① 只載一次：14 句預習庫
    if "sentences" not in st.session_state:
        st.session_state.sentences = {}

    # ② 每 2 小時即時經文（當題目來源）
    tz = timezone(timedelta(hours=8))
    HOUR_IDX = (int(datetime.now(tz).strftime("%H")) // 2) % len(VERSE_POOL)
    verse = VERSE_POOL[HOUR_IDX]          # 當前時段經文
    st.info(f"**{datetime.now(tz).strftime('%m/%d %H:%M')}**｜{verse['ref']}  \n{verse['zh']}")

    # ③ 英文 3 群折疊（5-5-4，當小考解答）
    st.subheader("📒 金句集")
    group_size = [5, 5, 4]
    start = 0
    for g, size in enumerate(group_size, 1):
        with st.expander(f"📑 英文解答 第 {g} 組（點我看）"):
            for i in range(start, start + size):
                v = st.session_state.sentences[str(dt.date.today() - timedelta(days=i))]
                st.markdown(f"**{v['ref']}**  \n{v['en']}")
                st.markdown('<div style="line-height:0.5;font-size:1px;">&nbsp;</div>',
            unsafe_allow_html=True)

    # ④ 中文整句直接顯示（當題目，句距壓半）
    for i in range(14):
        d = str(dt.date.today() - timedelta(days=i))
        v = st.session_state.sentences[d]
        st.markdown(f"**{d[-5:]}**｜{v['ref']}  \n{v['zh']}")
        st.markdown('<div style="line-height:0.5;font-size:1px;">&nbsp;</div>',
            unsafe_allow_html=True)

    # ⑤ 其餘功能：新增、匯出
    with st.expander("✨ 新增金句", expanded=True):
        new_sentence = st.text_input("中英並列", key="new_sentence")
        if st.button("儲存", type="primary"):
            if new_sentence:
                st.session_state.sentences[str(dt.date.today())] = new_sentence
                st.success("已儲存！")
            else:
                st.error("請輸入內容")

    if st.button("📋 匯出金句庫"):
        export = "\n".join([f"{k}  {v['ref']}  {v['en']}  {v['zh']}" for k, v in st.session_state.sentences.items()])
        st.code(export, language="text")
