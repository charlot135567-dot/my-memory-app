+import streamlit as st
+import pandas as pd
+import requests
+import io
+import re
+import os
+import random
+import time
+import json
+import base64
+from urllib.parse import quote
+from PIL import Image, ImageChops
+
+# optional: streamlit_lottie
+try:
+    from streamlit_lottie import st_lottie
+    LOTTIE_AVAILABLE = True
+except ImportError:
+    LOTTIE_AVAILABLE = False
+
+st.set_page_config(page_title="Memory Logic 2026", layout="wide", page_icon="🐶")
+THEME = {"bg": "#FFF9E3", "box": "#FFFFFF", "accent": "#FFCDD2", "text": "#4A4A4A", "sub": "#F06292", "keyword": "#E91E63"}
+
+# --- helper: load lottie json from full url
+def load_lottieurl(url):
+    try:
+        r = requests.get(url, timeout=6)
+        r.raise_for_status()
+        return r.json()
+    except Exception:
+        return None
+
+# --- helper: trim image borders (simple uniform background)
+def trim_image_keep_subject(in_path, out_path):
+    try:
+        im = Image.open(in_path).convert("RGBA")
+        bg = Image.new("RGBA", im.size, im.getpixel((0,0)))
+        diff = ImageChops.difference(im, bg)
+        bbox = diff.getbbox()
+        if bbox:
+            cropped = im.crop(bbox)
+            cropped.save(out_path)
+            return out_path
+        else:
+            im.save(out_path)
+            return out_path
+    except Exception:
+        return in_path
+
+# --- Google Sheet fetch (fixed URL) ---
+SHEET_ID = "1eiinJgMYXkCwIbU25P7lfsyNhO8MtD-m15wyUv3YgjQ"
+GIDS = {"📖 經節": "1454083804", "🔤 單字": "1400979824", "🔗 片語": "1657258260"}
+
+@st.cache_data(ttl=300)
+def fetch_data(gid):
+    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
+    try:
+        r = requests.get(url, timeout=10)
+        r.raise_for_status()
+        return pd.read_csv(io.StringIO(r.text)).fillna("")
+    except Exception as e:
+        st.error(f"讀取 Google Sheet 失敗: {e}")
+        return pd.DataFrame()
+
+# --- CSS ---
+st.markdown(f"""
+    <style>
+    @import url('https://fonts.googleapis.com/css2?family=Comic+Neue:wght@400;700&display=swap');
+    html, body, [data-testid="stAppViewContainer"] {{ background-color: {THEME['bg']}; font-family: 'Comic Neue', cursive; }}
+    .feature-box {{ background-color: {THEME['box']} !important; border-radius: 18px !important; padding: 15px !important; border: 2.5px solid {THEME['accent']} !important; box-shadow: 4px 4px 0px {THEME['accent']} !important; margin-bottom: 10px !important; min-height: 110px; }}
+    .kw {{ color: {THEME['keyword']}; font-weight: bolder; font-size: 1.2em; background-color: #FFFF00; padding: 2px 4px; border-radius: 4px; }}
+    .dict-btn {{ color: {THEME['sub']}; text-decoration: none; font-weight: bold; float: right; font-size: 11px; border: 1px solid; padding: 1px 4px; border-radius: 4px; }}
+    .fixed-bottom-img {{ position: fixed; bottom: 6px; right: 10px; z-index: 9999; width: 180px; pointer-events: none; opacity: 0.95; }}
+    </style>
+    """, unsafe_allow_html=True)
+
+# --- Lottie sample URLs (示範，可替換) ---
+LOTTIE_MARIO = "https://assets7.lottiefiles.com/packages/lf20_touohxv0.json"
+LOTTIE_DOG = "https://assets10.lottiefiles.com/packages/lf20_puciaact.json"
+
+# --- sidebar ---
+with st.sidebar:
+    st.markdown("### 🐾 系統控制台")
+    if 'score' not in st.session_state: st.session_state.score = 0
+    if 'lives' not in st.session_state: st.session_state.lives = 3
+    st.subheader(f"🏆 得分: {st.session_state.score}")
+    st.subheader(f"❤️ 生命: {'❤️' * st.session_state.lives}")
+    if st.button("♻️ 刷新內容"):
+        try:
+            st.cache_data.clear()
+        except:
+            pass
+        st.experimental_rerun()
+
+# --- tabs ---
+tab_home, tab_play, tab_tool, tab_game = st.tabs(["🏠 我的書桌", "🎯 隨機挑戰", "🧪 自動分類工具", "🎮 遊戲與語音"])
+
+with tab_home:
+    df_v = fetch_data(GIDS["📖 經節"])
+    df_w = fetch_data(GIDS["🔤 單字"])
+    df_p = fetch_data(GIDS["🔗 片語"])
+    v1 = df_v.sample(1).iloc[0] if not df_v.empty else {}
+    w1 = df_w.sample(1).iloc[0] if not df_w.empty else {"Vocab": "Study", "Definition": "學習", "Grammar": "保持學習！"}
+    p1 = df_p.sample(1).iloc[0] if not df_p.empty else {"Phrase": "Keep it up", "Definition": "加油"}
+
+    # top thumbnails
+    st.markdown('<div style="margin-top: -30px;"></div>', unsafe_allow_html=True)
+    img_files = ["snoopy1.png", "snoopy2.png", "snoopy3.png"]
+    img_cols = st.columns(6)
+    for idx, img_name in enumerate(img_files):
+        if os.path.exists(img_name) and idx < len(img_cols):
+            img_cols[idx].image(img_name, width=100)
+    st.markdown("---")
+    c1, c2, c3 = st.columns([1, 1.2, 1.8])
+    with c1:
+        v_word = w1.get("Vocab", "Study")
+        d_url = f"https://dictionary.cambridge.org/dictionary/english/{quote(str(v_word))}"
+        st.markdown(f'<div class="feature-box"><a href="{d_url}" target="_blank" class="dict-btn">🔍 字典</a><small>🔤 單字</small><br><b>{v_word}</b><br><small>{w1.get("Definition","")}</small></div>', unsafe_allow_html=True)
+    with c2:
+        phrase = p1.get("Phrase", "Keep it up")
+        p_url = f"https://www.google.com/search?q={quote(phrase + " meaning")}"
+        st.markdown(f'<div class="feature-box"><a href="{p_url}" target="_blank" class="dict-btn">🔗 參考</a><small>🔗 片語</small><br><b>{phrase}</b><br><small>{p1.get("Definition","")}</small></div>', unsafe_allow_html=True)
+    with c3:
+        st.markdown(f'<div class="feature-box" style="background-color:#E3F2FD !important;"><small>📝 關鍵文法</small><br><div style="font-size:14px; margin-top:5px;">{w1.get("Grammar", "保持學習！")}</div></div>', unsafe_allow_html=True)
+
+    # 今日金句（關鍵字高亮）
+    raw_ch = v1.get("Chinese", "載入中...")
+    kw = str(v1.get("Keyword", "") or "")
+    display_ch = raw_ch
+    if kw:
+        try:
+            kws = [k.strip() for k in kw.split(",") if k.strip()]
+            for k in kws:
+                display_ch = re.sub(re.escape(k), f'<span class="kw">{k}</span>', display_ch, flags=re.IGNORECASE)
+        except:
+            pass
+    st.markdown(f'<div class="feature-box" style="min-height:150px;"><h3 style="color:{THEME["sub"]}; margin-top:0;">💡 今日金句</h3><div style="font-size:28px; line-height:1.4; font-weight:bold;">“{display_ch}”</div><div style="color:gray; margin-top:10px; text-align:right;">— {v1.get("Reference","")}</div></div>', unsafe_allow_html=True)
+
+    # bottom snoopy (如果存在)
+    bottom_img = "snoopy_bottom.png"
+    if os.path.exists(bottom_img):
+        with open(bottom_img, "rb") as f:
+            b64 = base64.b64encode(f.read()).decode()
+        st.markdown(f'<img class="fixed-bottom-img" src="data:image/png;base64,{b64}" />', unsafe_allow_html=True)
+
+with tab_play:
+    m_data = load_lottieurl(LOTTIE_MARIO)
+    s_data = load_lottieurl(LOTTIE_DOG)
+    col_a, col_b = st.columns(2)
+    with col_a:
+        if LOTTIE_AVAILABLE and m_data:
+            st_lottie(m_data, height=150, key="mario")
+        else:
+            col_a.info("Mario Lottie 未載入（請安裝 streamlit_lottie 並填入正確 Lottie URL）")
+    with col_b:
+        if LOTTIE_AVAILABLE and s_data:
+            st_lottie(s_data, height=150, key="dog")
+        else:
+            col_b.info("Dog Lottie 未載入（請安裝 streamlit_lottie 並填入正確 Lottie URL）")
+
+    if 'current_vocab' not in st.session_state:
+        st.session_state.current_vocab = w1.get("Vocab", "Study")
+        st.session_state.current_def = w1.get("Definition", "學習")
+    st.subheader("⚡️ 瞬時翻譯挑戰")
+    st.write(f"題目： 「 **{st.session_state.current_def}** 」 的英文是？")
+    ans = st.text_input("輸入答案...", key="play_in")
+    if st.button("提交", key="submit_play"):
+        target = st.session_state.current_vocab
+        if ans.lower().strip() == str(target).lower().strip():
+            st.balloons()
+            st.session_state.score += 10
+            st.success("答對！+10 分")
+            if not df_w.empty:
+                st.session_state.current_vocab = df_w.sample(1).iloc[0].get("Vocab","Study")
+                st.session_state.current_def = df_w.sample(1).iloc[0].get("Definition","學習")
+        else:
+            st.session_state.lives -= 1
+            st.error(f"生命值 -1。答案是: {target}")
+
+with tab_tool:
+    st.info("🧪 分類工具已就緒。")
+    st.write("資料檢查（debug 用）")
+    df_check = fetch_data(GIDS["🔤 單字"])
+    if not df_check.empty:
+        st.write("欄位：", list(df_check.columns))
+        st.dataframe(df_check.head(10))
+    else:
+        st.write("單字表讀取為空，請檢查 Google Sheet 權限或 SHEET_ID/GID 是否正確。")
+
+with tab_game:
+    st.header("🎮 遊戲計時器與語音辨識示範")
+    st.markdown("下方示範使用客戶端的計時器、Lottie、Web Speech API 與 postMessage 回傳。")
+
+    sample_questions = [
+        {"id": 1, "q": "中翻英： 我愛你", "a": "I love you"},
+        {"id": 2, "q": "中翻英： 早安", "a": "Good morning"},
+        {"id": 3, "q": "英翻中： Hello", "a": "哈囉"},
+        {"id": 4, "q": "英翻中： Thank you", "a": "謝謝"}
+    ]
+    questions_json = json.dumps(sample_questions)
+
+    # HTML template with placeholder for JSON
+    game_html_template = r"""
+    <!doctype html>
+    <html>
+    <head>
+      <meta charset="utf-8" />
+      <script src="https://cdnjs.cloudflare.com/ajax/libs/bodymovin/5.7.6/lottie.min.js"></script>
+      <style>
+        body { font-family: Arial, Helvetica, sans-serif; background: transparent; }
+        .box { padding:10px; border-radius:8px; background:#fff; border:1px solid #ddd; }
+        .timer { font-size:22px; color:#d32f2f; font-weight:bold; }
+        .question { font-size:18px; margin-top:8px; }
+        .anim { width:180px; height:180px; }
+        .hint { color:#888; font-size:12px; }
+        button { padding:8px 12px; margin-top:8px; }
+      </style>
+    </head>
+    <body>
+      <div class="box">
+        <div>剩餘時間: <span class="timer" id="time">--:--</span></div>
+        <div class="question" id="question"></div>
+        <input id="answer" placeholder="輸入或按麥克風語音" style="width:60%;" />
+        <button id="submit">提交</button>
+        <button id="mic">🎤 語音</button>
+        <div class="hint" id="hint">當倒數低於20秒會顯示暈倒效果；答完顯示慶祝動畫。</div>
+        <div id="animContainer" class="anim"></div>
+      </div>
+
+      <script>
+        const questions = %%QUESTIONS_JSON%%;
+        let idx = 0;
+        let total = questions.length;
+        const totalSeconds = 60;
+        let remaining = totalSeconds;
+        let timerInterval = null;
+
+        const questionEl = document.getElementById('question');
+        const timeEl = document.getElementById('time');
+        const ansEl = document.getElementById('answer');
+        const animContainer = document.getElementById('animContainer');
+
+        let lottieAnim = null;
+        function loadLottie(url, loop=true) {
+          animContainer.innerHTML = '';
+          lottieAnim = lottie.loadAnimation({
+            container: animContainer,
+            renderer: 'svg',
+            loop: loop,
+            autoplay: true,
+            path: url
+          });
+        }
+
+        function renderQuestion() {
+          if (idx >= total) {
+            questionEl.innerText = '已完成所有題目！';
+            loadLottie('https://assets7.lottiefiles.com/packages/lf20_jbrw3hcz.json', true);
+            sendResult({event:'finished', score: total});
+            clearInterval(timerInterval);
+            return;
+          }
+          let q = questions[idx];
+          questionEl.innerText = `題目 (${idx+1}/${total}): ` + q.q;
+        }
+
+        function formatTime(sec) {
+          let m = Math.floor(sec/60);
+          let s = sec % 60;
+          return (m<10?('0'+m):m) + ':' + (s<10?('0'+s):s);
+        }
+
+        function startTimer() {
+          timeEl.innerText = formatTime(remaining);
+          timerInterval = setInterval(()=>{
+            remaining -= 1;
+            timeEl.innerText = formatTime(remaining);
+            if (remaining <= 20 && remaining > 0) {
+              loadLottie('https://assets2.lottiefiles.com/packages/lf20_kxsd2ytq.json', true);
+            }
+            if (remaining <= 0) {
+              clearInterval(timerInterval);
+              loadLottie('https://assets1.lottiefiles.com/packages/lf20_nt5eeb8p.json', false);
+              sendResult({event:'timeout', idx: idx});
+            }
+          }, 1000);
+        }
+
+        function sendResult(obj) {
+          const payload = {
+            isStreamlitMessage: true,
+            type: 'streamlit:setComponentValue',
+            value: JSON.stringify(obj)
+          };
+          window.parent.postMessage(payload, "*");
+        }
+
+        renderQuestion();
+        startTimer();
+
+        document.getElementById('submit').addEventListener('click', ()=>{
+          const user = ansEl.value.trim();
+          const correct = questions[idx].a;
+          const ok = user.toLowerCase() === correct.toLowerCase();
+          if (ok) {
+            loadLottie('https://assets2.lottiefiles.com/packages/lf20_8wREpI.json', true);
+            sendResult({event:'answer', idx:idx, correct:true});
+            idx += 1;
+            setTimeout(()=>{ renderQuestion(); }, 1200);
+          } else {
+            loadLottie('https://assets3.lottiefiles.com/packages/lf20_BQs7bK.json', false);
+            sendResult({event:'answer', idx:idx, correct:false});
+          }
+          ansEl.value = '';
+        });
+
+        let recognition = null;
+        const micBtn = document.getElementById('mic');
+        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
+          const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
+          recognition = new SpeechRecognition();
+          recognition.lang = 'zh-TW';
+          recognition.interimResults = false;
+          recognition.maxAlternatives = 1;
+          recognition.onresult = function(event) {
+            const spoken = event.results[0][0].transcript;
+            ansEl.value = spoken;
+          };
+          recognition.onerror = function(event) {
+            console.log('Speech recognition error', event);
+          };
+        } else {
+          micBtn.disabled = true;
+          micBtn.innerText = '語音不支援';
+        }
+
+        micBtn.addEventListener('click', ()=>{
+          if (!recognition) return;
+          try {
+            recognition.start();
+          } catch(e) {
+            console.warn(e);
+          }
+        });
+
+        loadLottie('https://assets3.lottiefiles.com/packages/lf20_tfb3estd.json', true);
+      </script>
+    </body>
+    </html>
+    """
+
+    game_html = game_html_template.replace("%%QUESTIONS_JSON%%", questions_json)
+
+    result = st.components.v1.html(game_html, height=520, scrolling=True)
+    if result:
+        try:
+            evt = json.loads(result)
+            st.write("從元件收到事件：", evt)
+        except Exception:
+            st.write("元件回傳（Raw）:", result)
+
+    st.markdown("---")
+    st.write("語音 (TTS) 範例：gTTS 或 ElevenLabs")
+
+    # --- gTTS 範例 ---
+    try:
+        from gtts import gTTS
+        def tts_gtts_play(text, lang='zh-tw'):
+            buf = io.BytesIO()
+            tts = gTTS(text=text, lang=lang)
+            tts.write_to_fp(buf)
+            st.audio(buf.getvalue(), format='audio/mp3')
+    except Exception:
+        def tts_gtts_play(text, lang='zh-tw'):
+            st.warning("gTTS 未安裝")
+
+    if st.button("播放範例語音：中文 '早安' (gTTS)"):
+        tts_gtts_play("早安", lang='zh-tw')
+
+    # --- ElevenLabs 範例（需在 st.secrets 設定 api_key） ---
+    def elevenlabs_tts(text, voice="alloy", api_key=None):
+        key = api_key or (st.secrets.get("elevenlabs", {}).get("api_key") if st.secrets else None)
+        if not key:
+            st.error("ElevenLabs API key 未設定，請設定 st.secrets['elevenlabs']['api_key']")
+            return None
+        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
+        headers = {"xi-api-key": key, "Content-Type": "application/json"}
+        payload = {"text": text}
+        try:
+            r = requests.post(url, headers=headers, json=payload, timeout=15)
+            r.raise_for_status()
+            return r.content
+        except Exception as e:
+            st.error(f"ElevenLabs TTS 失敗: {e}")
+            return None
+
+    if st.button("播放範例語音：中文 '早安' (ElevenLabs)"):
+        audio = elevenlabs_tts("早安", voice="alloy")
+        if audio:
+            st.audio(audio, format="audio/mp3")
+
*** End Patch
*** Add File: game_component/__init__.py
+#!/usr/bin/env python3
+# game_component/__init__.py
+import streamlit.components.v1 as components
+import json
+from pathlib import Path
+
+_RELEASE = False
+
+if not _RELEASE:
+    # local dev server (if you run a frontend dev server)
+    _component_func = components.declare_component("game_component", url="http://localhost:3001")
+else:
+    build_dir = str(Path(__file__).parent.joinpath("frontend/build"))
+    _component_func = components.declare_component("game_component", path=build_dir)
+
+def game_component(questions=None, key=None, height=460):
+    questions_json = json.dumps(questions or [])
+    return _component_func(questions_json=questions_json, key=key, height=height)
+
*** End Patch
*** Add File: game_component/frontend/index.html
+<!doctype html>
+<html>
+<head>
+  <meta charset="utf-8" />
+  <script src="https://cdnjs.cloudflare.com/ajax/libs/bodymovin/5.7.6/lottie.min.js"></script>
+  <style>
+    body { font-family: Arial, Helvetica, sans-serif; background: transparent; }
+    .box { padding:10px; border-radius:8px; background:#fff; border:1px solid #ddd; }
+    .timer { font-size:22px; color:#d32f2f; font-weight:bold; }
+    .question { font-size:18px; margin-top:8px; }
+    .anim { width:180px; height:180px; }
+    .hint { color:#888; font-size:12px; }
+    button { padding:8px 12px; margin-top:8px; }
+  </style>
+</head>
+<body>
+  <div class="box">
+    <div>剩餘時間: <span class="timer" id="time">--:--</span></div>
+    <div class="question" id="question"></div>
+    <input id="answer" placeholder="輸入或按麥克風語音" style="width:60%;" />
+    <button id="submit">提交</button>
+    <button id="mic">🎤 語音</button>
+    <div class="hint" id="hint">當倒數低於20秒會顯示暈倒效果；答完顯示慶祝動畫。</div>
+    <div id="animContainer" class="anim"></div>
+  </div>
+
+  <script>
+    // For component packaging, the component should accept questions (JSON) from parent
+    // If you use this file as a static HTML demo, replace QUESTIONS below with actual JSON.
+    const QUESTIONS = [
+      {"id":1,"q":"中翻英： 我愛你","a":"I love you"},
+      {"id":2,"q":"中翻英： 早安","a":"Good morning"}
+    ];
+
+    const questions = QUESTIONS;
+    let idx = 0;
+    let total = questions.length;
+    const totalSeconds = 60;
+    let remaining = totalSeconds;
+    let timerInterval = null;
+
+    const questionEl = document.getElementById('question');
+    const timeEl = document.getElementById('time');
+    const ansEl = document.getElementById('answer');
+    const animContainer = document.getElementById('animContainer');
+
+    let lottieAnim = null;
+    function loadLottie(url, loop=true) {
+      animContainer.innerHTML = '';
+      lottieAnim = lottie.loadAnimation({
+        container: animContainer,
+        renderer: 'svg',
+        loop: loop,
+        autoplay: true,
+        path: url
+      });
+    }
+
+    function renderQuestion() {
+      if (idx >= total) {
+        questionEl.innerText = '已完成所有題目！';
+        loadLottie('https://assets7.lottiefiles.com/packages/lf20_jbrw3hcz.json', true);
+        clearInterval(timerInterval);
+        return;
+      }
+      let q = questions[idx];
+      questionEl.innerText = `題目 (${idx+1}/${total}): ` + q.q;
+    }
+
+    function formatTime(sec) {
+      let m = Math.floor(sec/60);
+      let s = sec % 60;
+      return (m<10?('0'+m):m) + ':' + (s<10?('0'+s):s);
+    }
+
+    function startTimer() {
+      timeEl.innerText = formatTime(remaining);
+      timerInterval = setInterval(()=>{
+        remaining -= 1;
+        timeEl.innerText = formatTime(remaining);
+        if (remaining <= 20 && remaining > 0) {
+          loadLottie('https://assets2.lottiefiles.com/packages/lf20_kxsd2ytq.json', true);
+        }
+        if (remaining <= 0) {
+          clearInterval(timerInterval);
+          loadLottie('https://assets1.lottiefiles.com/packages/lf20_nt5eeb8p.json', false);
+        }
+      }, 1000);
+    }
+
+    renderQuestion();
+    startTimer();
+
+    document.getElementById('submit').addEventListener('click', ()=>{
+      const user = ansEl.value.trim();
+      const correct = questions[idx].a;
+      const ok = user.toLowerCase() === correct.toLowerCase();
+      if (ok) {
+        loadLottie('https://assets2.lottiefiles.com/packages/lf20_8wREpI.json', true);
+        idx += 1;
+        setTimeout(()=>{ renderQuestion(); }, 1200);
+      } else {
+        loadLottie('https://assets3.lottiefiles.com/packages/lf20_BQs7bK.json', false);
+      }
+      ansEl.value = '';
+    });
+
+    let recognition = null;
+    const micBtn = document.getElementById('mic');
+    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
+      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
+      recognition = new SpeechRecognition();
+      recognition.lang = 'zh-TW';
+      recognition.interimResults = false;
+      recognition.maxAlternatives = 1;
+      recognition.onresult = function(event) {
+        const spoken = event.results[0][0].transcript;
+        ansEl.value = spoken;
+      };
+    } else {
+      micBtn.disabled = true;
+      micBtn.innerText = '語音不支援';
+    }
+
+    micBtn.addEventListener('click', ()=>{
+      if (!recognition) return;
+      try {
+        recognition.start();
+      } catch(e) {
+        console.warn(e);
+      }
+    });
+
+    loadLottie('https://assets3.lottiefiles.com/packages/lf20_tfb3estd.json', true);
+  </script>
+</body>
+</html>
+
*** End Patch
*** Add File: requirements.txt
+streamlit>=1.18
+pandas
+requests
+Pillow
+gTTS
+streamlit-lottie
+
*** End Patch
*** Add File: .streamlit/secrets.toml.example
+[elevenlabs]
+api_key = "YOUR_ELEVENLABS_API_KEY"
+
*** End Patch

