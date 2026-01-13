
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import time
import random
import requests
import base64
from datetime import datetime
from pathlib import Path
import sys

import streamlit as st

# -------------------------
# Page config - must be before any other st.* calls
# -------------------------
st.set_page_config(page_title="Memory Bible 2026", layout="wide", page_icon="📖")

# =========================
# Config / Constants
# =========================
BASE_URL = "https://getbible.net/v2"
LANG_MAP = {
    "EN": "eng",
    "CN": "chi",
    "JA": "jpn",
    "KO": "kor",
    "TH": "tha"
}
# Which books / chapters to fetch (example)
BOOKS = {"Proverbs": range(1, 2)
}
DATA_DIR = Path("data")
JSON_PATH = DATA_DIR / "bible_multilang.json"

# =========================
# Utility: HTTP get with retry
# =========================
def http_get_with_retry(url, timeout=20, retries=3, backoff=1.0):
    last_exc = None
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last_exc = e
            wait = backoff * (i + 1)
            print(f"[http] attempt {i+1} failed for {url}: {e}. sleeping {wait}s")
            time.sleep(wait)
    raise last_exc

def parse_jsonp_or_json(text):
    text = text.strip()
    # try direct JSON
    try:
        return json.loads(text)
    except Exception:
        pass
    # try find {...}
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end+1]
        try:
            return json.loads(snippet)
        except Exception:
            pass
    # try find [...]
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end+1]
        try:
            return json.loads(snippet)
        except Exception:
            pass
    return None

# =========================
# Data Layer – GetBible JSON (robust)
# =========================
def fetch_chapter(book, chapter, lang):
    url = f"{BASE_URL}/{lang}/{book}/{chapter}"
    r = http_get_with_retry(url)
    text = r.text
    print(f"[fetch] {url} -> {r.status_code} len={len(text)} head={text[:300]!r}")
    data = parse_jsonp_or_json(text)
    if data is None:
        raise ValueError(f"Cannot parse JSON from {url}; head: {text[:800]!r}")
    return data

def find_verses(data):
    if not data:
        return []
    # common shapes: dict with 'verses', list containing dicts with 'verses', nested
    if isinstance(data, dict):
        if "verses" in data and isinstance(data["verses"], list):
            return data["verses"]
        # search immediate values
        for v in data.values():
            if isinstance(v, list):
                for it in v:
                    if isinstance(it, dict) and "verses" in it and isinstance(it["verses"], list):
                        return it["verses"]
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "verses" in item and isinstance(item["verses"], list):
                return item["verses"]
    # deep search
    def dfs(o):
        if isinstance(o, dict):
            for k, vv in o.items():
                if k == "verses" and isinstance(vv, list):
                    return vv
                res = dfs(vv)
                if res:
                    return res
        elif isinstance(o, list):
            for it in o:
                res = dfs(it)
                if res:
                    return res
        return None
    found = dfs(data)
    return found or []

# map book display names if needed
BOOK_KEY_MAP = {
    "Psalms": "Psalm",
    "Proverbs": "Proverbs"
}

def build_bible_json():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    result = {}

    for book, chapters in BOOKS.items():
        for ch in chapters:
            print(f"📖 Fetching {book} {ch}")
            for short_lang, api_lang in LANG_MAP.items():
                try:
                    data = fetch_chapter(book, ch, api_lang)
                except Exception as e:
                    print(f"  ! fetch error for {book} {ch} ({short_lang}): {e}")
                    continue
                verses = find_verses(data)
                if not verses:
                    print(f"  ! no verses found in response for {book} {ch} ({short_lang})")
                    continue
                display_book = BOOK_KEY_MAP.get(book, book)
                for v in verses:
                    # adapt to possible key names
                    verse_num = v.get("verse") or v.get("verse_number") or v.get("v") or v.get("num")
                    text = v.get("text") or v.get("content") or v.get("verse_text") or ""
                    if verse_num is None:
                        continue
                    key = f"{display_book} {ch}:{verse_num}"
                    result.setdefault(key, {})
                    result[key][short_lang] = text.strip()
                time.sleep(0.4 + random.random() * 0.2)

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ Bible JSON saved to {JSON_PATH} with {len(result)} entries")
    return result

# -------------------------
# Load bible JSON (local -> remote -> fallback)
# -------------------------
@st.cache_data
def load_bible_json(local_path=str(JSON_PATH),
                    raw_url="https://raw.githubusercontent.com/charlot135567-dot/my-memory-app/main/bible_multilang.json",
                    timeout=8):
    # 1) local
    try:
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                text = f.read()
            if text.startswith("\ufeff"):
                text = text.lstrip("\ufeff")
            data = json.loads(text)
            return data
    except Exception as e:
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

    # fallback built-in sample
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

    st.markdown("按「重新載入」會依以下順序載入資料：1. 上傳的 JSON（若有）  2. 本地 data/bible_multilang.json（若存在）  3. GitHub raw URL（若可取得）  4. 程式內建範例")
    # Manual generate button (local)
    if st.button("📥 生成五種語言 Bible JSON（本機）"):
        with st.spinner("正在抓取資料，請稍候..."):
            try:
                result = build_bible_json()
                st.success(f"✅ Bible JSON 已生成，共 {len(result)} 節經文")
            except Exception as e:
                st.error(f"生成失敗：{e}")

    if st.button("🔄 重新載入"):
        # clear cached load
        load_bible_json.clear()
        st.experimental_rerun()

# Determine bible source: uploaded -> local/remote
if st.session_state.uploaded_bible:
    bible_data = st.session_state.uploaded_bible
else:
    # ensure we read the unified JSON_PATH
    bible_data = load_bible_json(local_path=str(JSON_PATH), raw_url=st.session_state.loaded_raw_url)

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
        st.markdown("<div style='margin-top:12px;'><span class='small-muted'>資料來源：</span> <code>local: data/bible_multilang.json</code> 或 <code>remote: GitHub raw</code> 或 <code>upload</code></div>", unsafe_allow_html=True)
    with right:
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

# =========================
# CLI 模式：只生成 JSON
# =========================
if __name__ == "__main__":
    # Use parse_known_args to avoid failing on Streamlit's CLI args when run under streamlit
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--no-ui", action="store_true", help="只生成 JSON，不啟動 Streamlit UI")
    args, _ = parser.parse_known_args()
    if args.no_ui:
        build_bible_json()
        sys.exit(0)
