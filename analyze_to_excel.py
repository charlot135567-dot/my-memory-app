#!/usr/bin/env python3
# analyze_to_excel.py  ──  Streamlit Cloud 用最小假資料版
import json, sys, argparse

def main(in_file):
    # 假資料：保證格式相容
    dummy = {
        "words": [
            {"Vocab": "becoming", "Syn / Ant": "fitting", "Example": "Fine speech is not becoming to a fool.", "口語訳": "愚か者にはふさわしくない", "KRF": "어울리지 않는다", "THSV11": "ไม่เหมาะสม"}
        ],
        "phrases": [
            {"Phrase": "fine speech", "Syn / Ant": "eloquent words", "Example": "Fine speech is not becoming to a fool.", "口語訳": "美辞麗句", "KRF": "아름다운 말", "THSV11": "วาจางาม"}
        ],
        "grammar": [
            {"Rule": "becoming to + N", "Example": "Fine speech is not becoming to a fool.", "解析": "『相稱』義形容詞片語", "補齊句": "Honesty is becoming to a leader.", "應用例": "Humility is becoming to us."}
        ]
    }
    out_file = "temp_result.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(dummy, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="輸入檔")
    args = ap.parse_args()
    main(args.file)
