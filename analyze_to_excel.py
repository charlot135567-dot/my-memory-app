#!/usr/bin/env python3
# analyze_to_excel.py  ──  Streamlit Cloud 用版本
import json, sys, argparse
import datetime
import os

# 嘗試匯入 Gemini API（如果有的話）
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

def generate_ref_no():
    """產生 Ref. No. 格式：年月日+序號"""
    today = datetime.datetime.now()
    date_str = today.strftime("%Y%m%d")
    # 簡單序號：時間後4碼
    seq = today.strftime("%H%M")
    return f"{date_str}{seq}"

def analyze_with_gemini(text):
    """使用 Gemini API 分析經文"""
    if not HAS_GEMINI:
        return None
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("KIMI_API_KEY")
    if not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""請分析以下英文經文，以 JSON 格式回傳：

{text[:2000]}

請回傳以下格式的 JSON：
{{
  "ref_no": "自動產生的編號",
  "ref_article": "經文的精煉英文版本",
  "words": [
    {{"Vocab": "單字", "Syn / Ant": "同義/反義", "Example": "例句", "口語訳": "日文", "KRF": "韓文", "THSV11": "泰文"}}
  ],
  "phrases": [
    {{"Phrase": "片語", "Syn / Ant": "同義/反義", "Example": "例句", "口語訳": "日文", "KRF": "韓文", "THSV11": "泰文"}}
  ],
  "grammar": [
    {{"Rule": "文法規則", "Example": "例句", "解析": "中文解析", "補齊句": "補充例句", "應用例": "應用例句"}}
  ]
}}

只回傳 JSON，不要其他文字。"""

        response = model.generate_content(prompt)
        result_text = response.text
        
        # 清理可能的 markdown 標記
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]
        
        return json.loads(result_text.strip())
        
    except Exception as e:
        print(f"Gemini API 錯誤：{e}", file=sys.stderr)
        return None

def main(in_file):
    # 讀取輸入檔案
    try:
        with open(in_file, "r", encoding="utf-8") as f:
            input_text = f.read().strip()
    except Exception as e:
        print(f"讀取輸入檔失敗：{e}", file=sys.stderr)
        input_text = ""

    # 嘗試用 AI 分析
    result = None
    if input_text and HAS_GEMINI:
        result = analyze_with_gemini(input_text)
    
    # 如果 AI 分析失敗，使用假資料但加上正確欄位
    if result is None:
        result = {
            "ref_no": generate_ref_no(),
            "ref_article": input_text[:200] + "..." if len(input_text) > 200 else input_text,
            "ref_article_zh": "（此為假資料模式，請設定 GEMINI_API_KEY 以啟用 AI 分析）",
            "words": [
                {
                    "Vocab": "becoming", 
                    "Syn / Ant": "fitting", 
                    "Example": "Fine speech is not becoming to a fool.", 
                    "口語訳": "愚か者にはふさわしくない", 
                    "KRF": "어울리지 않는다", 
                    "THSV11": "ไม่เหมาะสม"
                },
                {
                    "Vocab": "rescue", 
                    "Syn / Ant": "save/danger", 
                    "Example": "The Lord will rescue me from every evil deed.", 
                    "口語訳": "救い出す", 
                    "KRF": "구출하다", 
                    "THSV11": "ช่วยให้พ้น"
                }
            ],
            "phrases": [
                {
                    "Phrase": "fine speech", 
                    "Syn / Ant": "eloquent words", 
                    "Example": "Fine speech is not becoming to a fool.", 
                    "口語訳": "美辞麗句", 
                    "KRF": "아름다운 말", 
                    "THSV11": "วาจางาม"
                },
                {
                    "Phrase": "every evil deed", 
                    "Syn / Ant": "all bad actions", 
                    "Example": "The Lord will rescue me from every evil deed.", 
                    "口語訳": "あらゆる悪しき行い", 
                    "KRF": "모든 악한 행위", 
                    "THSV11": "การกระทำชั่วทุกอย่าง"
                }
            ],
            "grammar": [
                {
                    "Rule": "becoming to + N", 
                    "Example": "Fine speech is not becoming to a fool.", 
                    "解析": "『相稱』義形容詞片語", 
                    "補齊句": "Honesty is becoming to a leader.", 
                    "應用例": "Humility is becoming to us."
                },
                {
                    "Rule": "rescue + O + from", 
                    "Example": "The Lord will rescue me from every evil deed.", 
                    "解析": "『從...拯救』雙賓語結構", 
                    "補齊句": "He rescued the child from the fire.", 
                    "應用例": "God rescues us from sin."
                }
            ]
        }

    # 寫入結果檔
    out_file = "temp_result.json"
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"分析完成：{result['ref_no']}", file=sys.stderr)
    except Exception as e:
        print(f"寫入結果檔失敗：{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="輸入檔")
    args = ap.parse_args()
    main(args.file)
