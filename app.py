#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import streamlit as st
import json
import os
import requests
import time
import random
import base64
from datetime import datetime
# =========================
# Data Layer – GetBible JSON
# =========================
BASE_URL = "https://getbible.net/v2"
LANG_MAP = {
    "EN": "eng",
    "CN": "chi",
    "JA": "jpn",
    "KO": "kor",
    "TH": "tha"
}
BOOKS = {
    "Psalms": range(1, 151),
    "Proverbs": range(1, 32)
}
DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "bible_multilang.json")
def fetch_chapter(book, chapter, lang):
    url = f"{BASE_URL}/{lang}/{book}/{chapter}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def build_bible_json():
    os.makedirs(DATA_DIR, exist_ok=True)
    result = {}

    for book, chapters in BOOKS.items():
        for ch in chapters:
            st.write(f"📖 Fetching {book} {ch}")
            for short_lang, api_lang in LANG_MAP.items():
                data = fetch_chapter(book, ch, api_lang)
                for v in data.get("verses", []):
                    key = (
                        f"Psalm {ch}:{v['verse']}"
                        if book == "Psalms"
                        else f"Proverbs {ch}:{v['verse']}"
                    )
                    result.setdefault(key, {})
                    result[key][short_lang] = v["text"].strip()
                time.sleep(0.4)

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result

def load_bible_data():
    if not os.path.exists(JSON_PATH):
        st.warning("Bible JSON 不存在，開始建立（只會跑一次）")
        return build_bible_json()
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Memory Bible 2026", layout="wide", page_icon="📖")

# -------------------------
# Helper: load bible JSON
# -------------------------
@st.cache_data
def load_bible_json(local_path="bible_multilang.json",
                    raw_url="https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/bible_multilang.json",
                    timeout=8):
    """
    Load JSON in order:
      1) local file (local_path)
      2) remote raw_url (GitHub raw)
    Returns dict (possibly empty).
    """
    # 1) local
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                text = f.read()
            if text.startswith("\ufeff"):
                text = text.lstrip("\ufeff")
            data = json.loads(text)
            return data
        except Exception as e:
            # fallback to remote
            print("Error loading local JSON:", e)

    # 2) remote
    try:
        r = requests.get(raw_url, timeout=timeout)
        r.raise_for_status()
        text = r.text
        if text.startswith("\ufeff"):
            text = text.lstrip("\ufeff")
        data = json.loads(text)
        return data
    except Exception as e:
        print("Error fetching remote JSON:", e)

    # 3) fallback built-in sample (minimal)
    return {
      "Genesis 1:1": {
        "CN": "起初，神創造天地。",
        "EN": "In the beginning God created the heavens and the earth.",
        "KO": "태초에 하나님이 천지를 창조하시니라.",
        "JA": "初めに、神は天地を創造された。",
        "TH": "ในปฐมกาล พระเจ้าทรงสร้างฟ้าและแผ่นดินโลก"
      },
      "Psalm 23:1": {
        "CN": "耶和華是我的牧者，我必不至缺乏。",
        "EN": "The Lord is my shepherd; I shall not want.",
        "KO": "여호와는 나의 목자시니 내게 부족함이 없으리로다.",
        "JA": "主は私の羊飼い。私は乏しいことがない。",
        "TH": "พระยาห์เวห์ทรงเป็นผู้เลี้ยงของฉัน ฉันจะไม่ขาดสิ่งใด"
      },
      "John 3:16": {
        "CN": "神愛世人，甚至將他的獨生子賜給他們，叫一切信他的，不至滅亡，反得永生。",
        "EN": "For God so loved the world that he gave his only Son, that whoever believes in him should not perish but have eternal life.",
        "KO": "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니 이는 그를 믿는 자마다 멸망치 않고 영생을 얻게 하려 하심이라.",
        "JA": "神はそのひとり子をお与えになったほどに世を愛された。それは彼を信じる者が滅びることなく、永遠の命を得るためである。",
        "TH": "เพราะพระเจ้าทรงรักโลกจนประทานพระบุตรองค์เดียวของพระองค์ เพื่อทุกผู้ที่เชื่อในพระองค์จะไม่พินาศ แต่มีชีวิตนิรันดร์"
      }
    }

# -------------------------
# Session defaults
# -------------------------
if "my_notes" not in st.session_state:
    st.session_state.my_notes = ""
if "todo_list" not in st.session_state:
    st.session_state.todo_list = []
if "hourly_ref" not in st.session_state:
    st.session_state.hourly_ref = {"ref": None, "time": 0}
if "uploaded_bible" not in st.session_state:
    st.session_state.uploaded_bible = None
if "loaded_raw_url" not in st.session_state:
    st.session_state.loaded_raw_url = "https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/bible_multilang.json"

# -------------------------
# UI style (cute & simple)
# -------------------------
st.markdown("""
    <style>
    .stApp { background: #FCFDFF; }
    .banner { background: linear-gradient(90deg,#E3F2FD,#FFF7E6); padding:16px; border-radius:12px; border:1px solid #E0F2FF; }
    .note-box { background: #FFFFFF; border-radius:10px; padding:12px; border:1px dashed #FFDDAA; box-shadow: 0 4px 10px rgba(0,0,0,0.03); }
    .todo-item { padding:10px; border-radius:10px; background:#FFF; border:1px solid #F0F0F0; margin-bottom:8px; }
    .small-muted { color:#666; font-size:0.9em; }
    </style>
""", unsafe_allow_html=True)

# -------------------------
# Top panel: load bible data (local / remote / uploaded)
# -------------------------
with st.expander("🔧 資料來源設定（點開可更換 raw URL 或上傳 JSON）", expanded=False):
    col_a, col_b = st.columns([3, 2])
    with col_a:
        raw_input = st.text_input("GitHub Raw JSON URL（若空白將使用預設）", value=st.session_state.loaded_raw_url)
        st.session_state.loaded_raw_url = raw_input.strip() if raw_input.strip() else st.session_state.loaded_raw_url
    with col_b:
        uploaded = st.file_uploader("上傳 bible_multilang.json（暫時使用，不會自動覆蓋本地）", type=["json"])
        if uploaded:
            try:
                text = uploaded.read().decode("utf-8")
                if text.startswith("\ufeff"):
                    text = text.lstrip("\ufeff")
                parsed = json.loads(text)
                st.session_state.uploaded_bible = parsed
                st.success("已載入上傳的 JSON（暫時使用）。")
            except Exception as e:
                st.error(f"上傳 JSON 解析失敗：{e}")

    st.markdown("按「重新載入」會依以下順序載入資料：1. 上傳的 JSON（若有）  2. 本地 bible_multilang.json（若存在）  3. GitHub raw URL（若可取得）  4. 程式內建範例")
    if st.button("🔄 重新載入"):
        # clear cached load
        load_bible_json.clear()
        st.experimental_rerun()

# Determine bible source: uploaded -> local/remote
if st.session_state.uploaded_bible:
    bible_data = st.session_state.uploaded_bible
else:
    bible_data = load_bible_json(local_path="bible_multilang.json", raw_url=st.session_state.loaded_raw_url)

# -------------------------
# Scheduled verse (hourly)
# -------------------------
def get_hourly_verse(bible_dict):
    refs = list(bible_dict.keys())
    if not refs:
        return None, {}
    now = time.time()
    if (st.session_state.hourly_ref["ref"] is None) or (now - st.session_state.hourly_ref["time"] > 3600):
        ref = random.choice(refs)
        st.session_state.hourly_ref = {"ref": ref, "time": now}
    return st.session_state.hourly_ref["ref"], bible_dict.get(st.session_state.hourly_ref["ref"], {})

ref, verses = get_hourly_verse(bible_data)

# Top banner
st.markdown(f"""
<div class="banner">
  <h3 style="margin:0;">📖 今日經文 — {ref if ref else '（無可用經文）'}</h3>
  <p style="margin:6px 0 2px;"><b>中文：</b> {verses.get('CN','')}</p>
  <p style="margin:0;"><b>English：</b> {verses.get('EN','')}</p>
  <hr style="margin:8px 0;">
  <p style="margin:0; font-size:0.95em;">🇯🇵 {verses.get('JA','')} &nbsp;&nbsp; 🇰🇷 {verses.get('KO','')} &nbsp;&nbsp; 🇹🇭 {verses.get('TH','')}</p>
</div>
""", unsafe_allow_html=True)

# -------------------------
# Main tabs: Home / Notes / Todo / Bible Browser
# -------------------------
tab_home, tab_notes, tab_todo, tab_bible = st.tabs(["🏠 我的桌面", "📝 每日筆記", "✅ 待辦與提醒", "📚 查經庫"])

with tab_home:
    left, right = st.columns([3,1])
    with left:
        st.markdown("<div class='note-box'><h2 style='margin:6px 0;'>主內平安</h2><p style='margin:6px 0;'>歡迎回來！您可以在「每日筆記」紀錄靈感，或在「待辦與提醒」管理日常事項。</p></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:12px;'><span class='small-muted'>資料來源：</span> <code>local: bible_multilang.json</code> 或 <code>remote: GitHub raw</code> 或 <code>upload</code></div>", unsafe_allow_html=True)
    with right:
        # cute image placeholder
        img_src = "https://via.placeholder.com/320x200.png?text=🌸+Memory+Bible"
        st.image(img_src, use_column_width=True)

with tab_notes:
    st.subheader("📓 每日靈修筆記（建議定期匯出備份）")
    st.info("筆記儲存在本次 session；請用匯出按鈕保存重要內容。")
    st.session_state.my_notes = st.text_area("在此輸入今天的靈修或感動...", value=st.session_state.my_notes, height=420, placeholder="今天哪段經文觸動你？")
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("💾 匯出 TXT"):
            st.download_button("下載 .txt", data=st.session_state.my_notes, file_name=f"Note_{datetime.now().strftime('%Y%m%d')}.txt")
    with c2:
        if st.button("📄 匯出 MD"):
            st.download_button("下載 .md", data=st.session_state.my_notes, file_name=f"Note_{datetime.now().strftime('%Y%m%d')}.md")
    with c3:
        if st.button("🗑️ 清空筆記"):
            st.session_state.my_notes = ""
            st.experimental_rerun()

with tab_todo:
    st.subheader("✅ 每日待辦與提醒")
    tc, tb = st.columns([4,1])
    with tc:
        new_task = st.text_input("新增事項", placeholder="例如：下午兩點禱告 / 備課")
    with tb:
        if st.button("➕ 新增") and new_task.strip():
            st.session_state.todo_list.append({"task": new_task.strip(), "done": False, "created": datetime.now().strftime("%H:%M")})
            st.experimental_rerun()

    st.write("---")
    if not st.session_state.todo_list:
        st.info("尚無待辦事項，請新增一項。")
    for i, item in enumerate(st.session_state.todo_list):
        cols = st.columns([0.05, 4, 1, 1])
        done = cols[0].checkbox("", value=item.get("done", False), key=f"td_{i}")
        item["done"] = done
        label = f"~~{item['task']}~~" if done else item["task"]
        cols[1].markdown(f"<div class='todo-item'><strong>{label}</strong><div class='small-muted'>設定：{item.get('created','')}</div></div>", unsafe_allow_html=True)
        if cols[2].button("🔁", key=f"edit_{i}"):
            st.session_state.todo_edit_index = i
            st.session_state.todo_edit_value = item["task"]
            st.experimental_rerun()
        if cols[3].button("🗑️", key=f"del_{i}"):
            st.session_state.todo_list.pop(i)
            st.experimental_rerun()

# inline edit handler
if "todo_edit_index" in st.session_state:
    idx = st.session_state.todo_edit_index
    val = st.session_state.get("todo_edit_value", "")
    new_val = st.text_input("編輯事項", value=val, key="edit_input")
    edit_cols = st.columns([1,1,1])
    if edit_cols[0].button("✅ 儲存編輯"):
        if new_val.strip():
            st.session_state.todo_list[idx]["task"] = new_val.strip()
        st.session_state.pop("todo_edit_index", None)
        st.session_state.pop("todo_edit_value", None)
        st.experimental_rerun()
    if edit_cols[1].button("取消"):
        st.session_state.pop("todo_edit_index", None)
        st.session_state.pop("todo_edit_value", None)
        st.experimental_rerun()

with tab_bible:
    st.subheader("📚 查經庫（五種語言）")
    cols = st.columns([3,1])
    with cols[0]:
        q = st.text_input("搜尋經節（例如：Genesis 1:1 或 John 3:16）", value="")
        if st.button("🔎 搜尋"):
            key = q.strip()
            if not key:
                st.warning("請輸入要搜尋的經節，例如: John 3:16")
            else:
                entry = bible_data.get(key)
                if not entry:
                    st.error("找不到該經節，請確認格式或改用近似搜尋。")
                else:
                    st.markdown(f"**{key}**")
                    st.write(f"中文：{entry.get('CN','')}")
                    st.write(f"English：{entry.get('EN','')}")
                    st.write(f"日本語：{entry.get('JA','')}")
                    st.write(f"한국어：{entry.get('KO','')}")
                    st.write(f"ไทย：{entry.get('TH','')}")
    with cols[1]:
        st.markdown("快速小工具")
        if st.button("顯示前三個經節 key"):
            st.write(list(bible_data.keys())[:3])
        if st.button("下載 JSON（目前載入資料）"):
            try:
                txt = json.dumps(bible_data, ensure_ascii=False, indent=2)
                st.download_button("下載 bible_multilang.json", data=txt, file_name="bible_multilang.json", mime="application/json")
            except Exception as e:
                st.error(f"產生下載失敗：{e}")

# -------------------------
# Footer: tips
# -------------------------
st.markdown("---")
st.markdown("小提醒：若您要把 JSON 放到 GitHub，建議放到 repo 根目錄或 data/ 資料夾，並使用 Raw URL（例如：https://raw.githubusercontent.com/username/repo/main/bible_multilang.json）。若 repo 為 private，請改為在部署環境包含該檔或上傳到伺服器。")

# End of file

