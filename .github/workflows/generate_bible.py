#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
import os
import time
import random
from pathlib import Path

BASE_URL = "https://getbible.net/v2"
LANG_MAP = {
    "EN": "eng",
    "CN": "chi",
    "JA": "jpn",
    "KO": "kor",
    "TH": "tha"
}
# 依您原本程式需求，示範抓 Psalms 與 Proverbs
BOOKS = {
    "Psalms": range(1, 151),
    "Proverbs": range(1, 32)
}
DATA_DIR = Path("data")
JSON_PATH = DATA_DIR / "bible_multilang.json"

# timeout and retry
def http_get_with_retry(url, timeout=20, retries=3, backoff=1.0):
    last_exc = None
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last_exc = e
            time.sleep(backoff * (i + 1))
    raise last_exc

def parse_jsonp_or_json(text):
    text = text.strip()
    # 嘗試直接解析
    try:
        return json.loads(text)
    except Exception:
        pass
    # 嘗試找到第一個 { 與最後一個 }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end+1]
        try:
            return json.loads(snippet)
        except Exception:
            pass
    # 嘗試解析第一個 [ ... ]
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end+1]
        try:
            return json.loads(snippet)
        except Exception:
            pass
    # 最後回傳 None 表示解析失敗
    return None

def fetch_chapter(book, chapter, lang):
    url = f"{BASE_URL}/{lang}/{book}/{chapter}"
    r = http_get_with_retry(url)
    text = r.text
    # debug head
    print(f"[fetch] {url} -> {r.status_code} len={len(text)} head={text[:300]!r}")
    data = parse_jsonp_or_json(text)
    if data is None:
        raise ValueError(f"Cannot parse JSON from {url}; head: {text[:800]!r}")
    return data

def find_verses(data):
    # 嘗試各種常見結構
    if not data:
        return []
    if isinstance(data, dict):
        if "verses" in data and isinstance(data["verses"], list):
            return data["verses"]
        # 有些 API 回傳 list 包 dict
        for v in data.values():
            if isinstance(v, list):
                for it in v:
                    if isinstance(it, dict) and "verses" in it and isinstance(it["verses"], list):
                        return it["verses"]
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "verses" in item:
                return item["verses"]
    # 深度搜尋任何 'verses' key
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
                    # v 可能有 keys 'verse' and 'text' or 'verse' and 'content'
                    verse_num = v.get("verse") or v.get("verse_number") or v.get("v") or v.get("num")
                    text = v.get("text") or v.get("content") or v.get("verse_text") or ""
                    if verse_num is None:
                        continue
                    key = f"{display_book} {ch}:{verse_num}"
                    result.setdefault(key, {})
                    result[key][short_lang] = text.strip()
                # respect API; small delay
                time.sleep(0.4 + random.random() * 0.2)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ Bible JSON saved to {JSON_PATH} with {len(result)} entries")
    return result

if __name__ == "__main__":
    build_bible_json()
