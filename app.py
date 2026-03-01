# ===================================================================
# 3. TAB1 ─ 書桌 (輪流顯示版 - 支援CSV和Markdown雙格式)
# ===================================================================
with tabs[0]:
    import csv, random, re, datetime as dt
    from io import StringIO

    # --- Session State 初始化（確保每次都有值）---
    if "tab1_vocab_index" not in st.session_state:
        st.session_state.tab1_vocab_index = 0
    if "tab1_phrase_index" not in st.session_state:
        st.session_state.tab1_phrase_index = 15  # 片語從第16個開始(索引15)
    if "tab1_grammar_index" not in st.session_state:
        st.session_state.tab1_grammar_index = 0
    if "tab1_verse_index" not in st.session_state:
        st.session_state.tab1_verse_index = 0
    if "tab1_last_update" not in st.session_state:
        st.session_state.tab1_last_update = dt.datetime.now()

    # 檢查是否需要更新（超過1小時）
    current_time = dt.datetime.now()
    time_diff = (current_time - st.session_state.tab1_last_update).total_seconds()
    
    if time_diff > 3600:
        st.session_state.tab1_last_update = current_time
        st.session_state.tab1_vocab_index += 1
        st.session_state.tab1_phrase_index += 4
        st.session_state.tab1_grammar_index += 1
        st.session_state.tab1_verse_index += 1
        st.rerun()
    
    sentences = st.session_state.get('sentences', {})
    
    if not sentences:
        st.warning("資料庫為空，請先在 TAB4 載入資料")
    else:
        # 修正：更穩健的解析函式，支援 \t 分隔
        def parse_csv(content):
            """解析CSV格式（支援 \t 分隔）"""
            if not content or not content.strip(): 
                return []
            try:
                # 檢查是否為Markdown表格
                if '|' in content and '\n' in content and content.strip().startswith('|'):
                    return []  # 交給parse_markdown處理
                
                # 使用 \t 作為分隔符
                from io import StringIO
                reader = csv.DictReader(StringIO(content.strip()), delimiter='\t')
                rows = list(reader)
                return [row for row in rows if any(v.strip() for v in row.values())]
            except Exception as e:
                st.write(f"CSV解析錯誤: {e}")
                return []

        def parse_markdown_table(content):
            """解析Markdown表格格式"""
            if not content or not content.strip():
                return []
            
            lines = content.strip().split('\n')
            rows = []
            
            # 找到表格開始行（以|開頭）
            table_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith('|'):
                    table_lines.append(line)
            
            if len(table_lines) < 2:  # 需要標題行和分隔行
                return []
            
            # 解析標題行
            header_line = table_lines[0]
            headers = [h.strip() for h in header_line.split('|')[1:-1]]  # 去掉首尾空字串
            
            # 跳過分隔行（第2行，通常是 |---|---| 這種）
            data_lines = table_lines[2:]
            
            for line in data_lines:
                if not line.strip() or line.strip().replace('|', '').strip() == '':
                    continue
                    
                # 解析資料行
                cells = [c.strip() for c in line.split('|')[1:-1]]
                
                # 確保欄位數量一致
                while len(cells) < len(headers):
                    cells.append('')
                
                row_dict = {}
                for i, header in enumerate(headers):
                    # 清理Markdown標記（**粗體**）
                    cell_value = cells[i] if i < len(cells) else ''
                    # 移除 ** 標記但保留內容
                    cell_value = re.sub(r'\*\*(.*?)\*\*', r'\1', cell_value)
                    row_dict[header] = cell_value
                
                # 只加入有資料的行
                if any(v.strip() for v in row_dict.values()):
                    rows.append(row_dict)
            
            return rows

        # ============================================================
        # 關鍵修正：分離模式A和模式B的資料，支援雙格式
        # ============================================================
        
        # 收集所有模式A資料（有V1的）和模式B資料（有W Sheet但無V1的）
        all_mode_a = []  # 單字、金句來源
        all_mode_b = []  # 片語來源
        all_grammar_sources = []  # 文法來源（A或B都可以）
        
        for ref, data in sentences.items():
            v1_content = data.get('v1_content', '')
            v2_content = data.get('v2_content', '')
            w_content = data.get('w_sheet', '')
            g_content = data.get('grammar_list', '')
            
            # 嘗試CSV格式（\t分隔），失敗則嘗試Markdown格式
            v1_rows = parse_csv(v1_content) or parse_markdown_table(v1_content)
            v2_rows = parse_csv(v2_content) or parse_markdown_table(v2_content)
            w_rows = parse_csv(w_content) or parse_markdown_table(w_content)
            g_rows = parse_csv(g_content) or parse_markdown_table(g_content)
            
            # 模式A：有V1資料 → 用於單字、金句
            if v1_rows:
                all_mode_a.append({
                    'ref': ref,
                    'v1': v1_rows,
                    'v2': v2_rows,
                    'v1_count': len(v1_rows)
                })
                # 文法也可以來自V1
                for i, row in enumerate(v1_rows):
                    all_grammar_sources.append({
                        'type': 'A',
                        'ref': ref,
                        'row': row,
                        'v2_row': v2_rows[i] if i < len(v2_rows) else {},
                        'index': i,
                        'total_in_file': len(v1_rows)
                    })
            
            # 模式B：有W Sheet → 用於片語（修正：只要有W Sheet就加入）
            if w_rows and len(w_rows) > 0:
                all_mode_b.append({
                    'ref': ref,
                    'w': w_rows,
                    'w_count': len(w_rows)
                })
            
            # Grammar List（模式B的文法）
            if g_rows:
                for i, row in enumerate(g_rows):
                    all_grammar_sources.append({
                        'type': 'B',
                        'ref': ref,
                        'row': row,
                        'v2_row': {},
                        'index': i,
                        'total_in_file': len(g_rows)
                    })
        
        # ============================================================
        # 1) 單字：V1 Syn/Ant + V2 Syn/Ant + THSV11 + 多語言
        # ============================================================
        vocab_display = []
        current_vocab_ref = "N/A"
        
        if all_mode_a:
            # 輪流選擇哪個模式A檔案
            total_vocab_items = sum(f['v1_count'] for f in all_mode_a)
            if total_vocab_items > 0:
                vocab_counter = st.session_state.tab1_vocab_index % total_vocab_items
                # 找到對應的檔案和行
                cumulative = 0
                vocab_file = None
                row_idx = 0
                for f in all_mode_a:
                    if cumulative + f['v1_count'] > vocab_counter:
                        vocab_file = f
                        row_idx = vocab_counter - cumulative
                        break
                    cumulative += f['v1_count']
                
                if vocab_file:
                    v1_row = vocab_file['v1'][row_idx]
                    v2_row = vocab_file['v2'][row_idx % len(vocab_file['v2'])] if vocab_file['v2'] else {}
                    
                    current_vocab_ref = v1_row.get('Ref.', vocab_file['ref'])
                    
                    # 修正：完整提取 V1 Syn/Ant
                    v1_syn_ant = v1_row.get('Syn/Ant', '')
                    v1_syn_list = []
                    v1_ant_list = []
                    
                    if v1_syn_ant:
                        # 解析 Syn/Ant 格式
                        if 'Syn:' in v1_syn_ant or 'Ant:' in v1_syn_ant:
                            syn_match = re.search(r'Syn:\s*([^/;]+)', v1_syn_ant)
                            ant_match = re.search(r'Ant:\s*([^/;]+)', v1_syn_ant)
                            if syn_match:
                                v1_syn_list = [s.strip() for s in syn_match.group(1).split(',') if s.strip()]
                            if ant_match:
                                v1_ant_list = [a.strip() for a in ant_match.group(1).split(',') if a.strip()]
                        else:
                            # 嘗試用 / 或 | 分隔
                            parts = re.split(r'[/|]', v1_syn_ant)
                            if len(parts) >= 2:
                                v1_syn_list = [p.strip() for p in parts[0].split(',') if p.strip()]
                                v1_ant_list = [p.strip() for p in parts[1].split(',') if p.strip()]
                            else:
                                v1_syn_list = [v1_syn_ant.strip()]
                    
                    # 修正：完整提取 V2 多語言資料
                    v2_syn_ant = v2_row.get('Syn/Ant', '') if v2_row else ''
                    v2_th = v2_row.get('THSV11', '') if v2_row else ''
                    v2_kr = v2_row.get('KRF', '') if v2_row else ''  # 韓文經文
                    v2_jp = v2_row.get('口語訳', '') if v2_row else ''  # 日文
                    
                    # 修正：組合單字顯示（包含所有語言）
                    vocab_items = []
                    
                    # V1 Syn（英文同義詞）
                    if v1_syn_list:
                        vocab_items.append(f"<span style='color:#2E8B57;'>✨{', '.join(v1_syn_list)}</span>")
                    
                    # V1 Ant（英文反義詞）
                    if v1_ant_list:
                        vocab_items.append(f"<span style='color:#CD5C5C;'>❄️{', '.join(v1_ant_list)}</span>")
                    
                    # V2 韓文 Syn/Ant
                    if v2_syn_ant:
                        vocab_items.append(f"<span style='color:#4682B4;'>🇰🇷 {v2_syn_ant}</span>")
                    
                    # V2 泰文 (THSV11)
                    if v2_th:
                        vocab_items.append(f"<span style='color:#9932CC;'>🇹🇭 {v2_th}</span>")
                    
                    # V2 日文 (口語訳)
                    if v2_jp:
                        vocab_items.append(f"<span style='color:#FF6347;'>🇯🇵 {v2_jp}</span>")
                    
                    vocab_display = vocab_items
        
        # ============================================================
        # 2) 片語：只從模式B的W Sheet輪流（第16個開始，索引15）
        # ============================================================
        w_phrases = []
        current_phrase_ref = "N/A"
        
        # 收集所有可用的片語（從第16個開始，索引15）
        all_available_phrases = []
        
        for mb in all_mode_b:
            w_rows = mb.get('w', [])
            w_count = len(w_rows)
            
            # 只有超過15筆的檔案才加入（從第16個開始）
            if w_count > 15:
                for idx in range(15, w_count):
                    all_available_phrases.append({
                        'data': w_rows[idx],
                        'ref': mb['ref'],
                        'original_idx': idx + 1  # 1-based for display
                    })
        
        # 輪流顯示4個片語
        if len(all_available_phrases) > 0:
            total_available = len(all_available_phrases)
            # 確保索引在範圍內
            start_idx = st.session_state.tab1_phrase_index % total_available
            
            # 取4個片語（循環）
            for i in range(4):
                idx = (start_idx + i) % total_available
                item = all_available_phrases[idx]
                w_phrases.append(item['data'])
                # 記錄第一個的ref作為顯示用
                if i == 0:
                    current_phrase_ref = f"{item['ref']} #{item['original_idx']}"
        
        # ============================================================
        # 3) 金句：從模式A的V1 Sheet輪流（與單字錯開6句）
        # ============================================================
        verse_lines = []
        current_verse_ref = "N/A"
        
        if all_mode_a:
            total_verse_items = sum(f['v1_count'] for f in all_mode_a)
            if total_verse_items > 0:
                # 關鍵修改：金句索引 = 當前索引 + 6，與單字錯開
                verse_counter = (st.session_state.tab1_verse_index + 6) % total_verse_items
                cumulative = 0
                verse_file = None
                row_idx = 0
                
                for f in all_mode_a:
                    if cumulative + f['v1_count'] > verse_counter:
                        verse_file = f
                        row_idx = verse_counter - cumulative
                        break
                    cumulative += f['v1_count']
                
                if verse_file:
                    v1_verse = verse_file['v1'][row_idx]
                    v2_verse = verse_file['v2'][row_idx % len(verse_file['v2'])] if verse_file['v2'] else {}
                    
                    current_verse_ref = v1_verse.get('Ref.', verse_file['ref'])
                    
                    # 修正：完整提取所有語言版本
                    en_text = v1_verse.get('English (ESV)', '')
                    cn_text = v1_verse.get('Chinese', '')
                    jp_text = v2_verse.get('口語訳', '') if v2_verse else ''
                    kr_text = v2_verse.get('KRF', '') if v2_verse else ''  # 韓文經文
                    th_text = v2_verse.get('THSV11', '') if v2_verse else ''
                    
                    # 組合金句顯示（多語言）
                    verse_lines = []
                    if en_text:
                        verse_text = f"🇬🇧 <b>{current_verse_ref}</b> {en_text}"
                        verse_lines.append(verse_text)
                    if jp_text:
                        verse_lines.append(f"🇯🇵 {jp_text}")
                    if kr_text:
                        verse_lines.append(f"🇰🇷 {kr_text}")
                    if th_text:
                        verse_lines.append(f"🇹🇭 {th_text}")
                    if cn_text:
                        verse_lines.append(f"🇨🇳 {cn_text}")
        
        # ============================================================
        # 4) 文法解析：完整顯示 Syn/Ant + 多語言
        # ============================================================
        grammar_html = "等待資料中..."
        current_grammar_ref = "N/A"
        
        if all_grammar_sources:
            g_idx = st.session_state.tab1_grammar_index % len(all_grammar_sources)
            g_source = all_grammar_sources[g_idx]
            g_row = g_source['row']
            v2_row = g_source.get('v2_row', {})
            current_grammar_ref = f"{g_source['ref']}-{g_source['index']+1}"
            
            all_grammar = []
            
            if g_source['type'] == 'A':
                # 模式A文法（來自V1 Grammar欄位）
                g_ref = g_row.get('Ref.', '')
                g_en = g_row.get('English (ESV)', '')
                g_cn = g_row.get('Chinese', '')
                g_syn = g_row.get('Syn/Ant', '')
                g_grammar = g_row.get('Grammar', '')
                
                # 修正：經文標題行（Ref緊貼英文）
                if g_ref and g_en:
                    all_grammar.append(f"<b>{g_ref}</b>{g_en}")
                elif g_en:
                    all_grammar.append(g_en)
                
                # 中文
                if g_cn:
                    all_grammar.append(g_cn)
                
                # 修正：Syn/Ant 同一行顯示（確保兩者都顯示）
                if g_syn:
                    syn_ant_html = ""
                    # 解析 Syn 和 Ant
                    syn_text = ""
                    ant_text = ""
                    
                    # 嘗試多種格式解析
                    if 'Syn:' in g_syn or 'Ant:' in g_syn:
                        syn_match = re.search(r'Syn:\s*([^/;]+?)(?=\s*Ant:|$)', g_syn)
                        ant_match = re.search(r'Ant:\s*([^/;]+)', g_syn)
                        if syn_match:
                            syn_text = syn_match.group(1).strip()
                        if ant_match:
                            ant_text = ant_match.group(1).strip()
                    else:
                        # 嘗試用 / 或 | 分隔
                        parts = re.split(r'[/|]', g_syn)
                        if len(parts) >= 2:
                            syn_text = parts[0].strip()
                            ant_text = parts[1].strip()
                        else:
                            syn_text = g_syn.strip()
                    
                    # 組合顯示
                    if syn_text:
                        syn_ant_html += f'<span style="color:#2E8B57;">✨Syn:{syn_text}</span>'
                    if ant_text:
                        if syn_text:
                            syn_ant_html += ' '
                        syn_ant_html += f'<span style="color:#CD5C5C;">❄️Ant:{ant_text}</span>'
                    
                    if syn_ant_html:
                        all_grammar.append(syn_ant_html)
                
                # Grammar解析（縮排對齊）
                if g_grammar:
                    # 處理 1️⃣2️⃣3️⃣4️⃣ 標記
                    text = str(g_grammar)
                    text = text.replace('1️⃣[', '1️⃣[')
                    text = text.replace('2️⃣[', '<br>2️⃣[')
                    text = text.replace('3️⃣[', '<br>3️⃣[')
                    text = text.replace('4️⃣[', '<br>4️⃣[')
                    all_grammar.append(text)
                
                # 修正：V2資料完整顯示（口語訳 + Grammar + Note + Korean + THSV11）
                v2_jp = v2_row.get('口語訳', '') if v2_row else ''
                v2_grammar = v2_row.get('Grammar', '') if v2_row else ''
                v2_note = v2_row.get('Note', '') if v2_row else ''
                v2_kr = v2_row.get('KRF', '') if v2_row else ''
                v2_kr_syn = v2_row.get('Korean Syn/Ant', '') if v2_row else ''
                v2_th = v2_row.get('THSV11', '') if v2_row else ''
                
                if v2_jp or v2_grammar or v2_note or v2_kr or v2_kr_syn or v2_th:
                    v2_parts = ["<br>"]  # 分隔線
                    v2_ref = v2_row.get('Ref.', g_ref) if v2_row else g_ref
                    
                    if v2_jp:
                        v2_parts.append(f"<b>{v2_ref}</b>{v2_jp}")
                    
                    if v2_grammar:
                        v2_parts.append(f'<span style="color:#4682B4;">文法：</span>{v2_grammar}')
                    if v2_note:
                        v2_parts.append(f'<span style="color:#D2691E;">備註：</span>{v2_note}')
                    if v2_kr:
                        v2_parts.append(f'<span style="color:#32CD32;">🇰🇷 {v2_kr}</span>')
                    if v2_kr_syn:
                        v2_parts.append(f'<span style="color:#4682B4;">🇰🇷 Syn/Ant: {v2_kr_syn}</span>')
                    if v2_th:
                        v2_parts.append(f'<span style="color:#9932CC;">🇹🇭 {v2_th}</span>')
                    
                    all_grammar.append("<br>".join(v2_parts))
                    
            else:
                # 模式B文法（來自Grammar List）
                orig = (g_row.get('Original Sentence (from text)', '') or 
                        g_row.get('Original Sentence', ''))
                rule = g_row.get('Grammar Rule', '')
                analysis = (g_row.get('Analysis & Example (1️⃣2️⃣3️⃣4️⃣)', '') or
                           g_row.get('Analysis & Example', '') or
                           g_row.get('Analysis', ''))
                
                html_parts = []
                
                # 1) 經文：黃色字體，加大
                if orig:
                    html_parts.append(
                        f'<div style="margin-bottom:2px; color:#FFD700; font-size:15px; font-weight:bold;">'
                        f'{orig}</div>'
                    )
                
                # 2) 規則+解析
                if analysis:
                    af = str(analysis).strip()
                    
                    if rule:
                        af = af.replace('1️⃣', f'📌 {rule}<br>1️⃣', 1)
                    
                    # 1-4標題呈綠色
                    af = af.replace(
                        '1️⃣**[分段解析+語法標籤]**：',
                        '<div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">1️⃣[分段解析+語法標籤]：</span>'
                    )
                    af = af.replace(
                        '2️⃣**[詞性辨析]**：',
                        '</div><div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">2️⃣[詞性辨析]：</span>'
                    )
                    af = af.replace(
                        '3️⃣**[修辭與結構]**：',
                        '</div><div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">3️⃣[修辭與結構]：</span>'
                    )
                    af = af.replace(
                        '4️⃣**[語意解釋]**：',
                        '</div><div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">4️⃣[語意解釋]：</span>'
                    )
                    
                    # 如果上面的沒匹配到，試試看沒有 ** 的版本
                    af = af.replace(
                        '1️⃣[分段解析+語法標籤]：',
                        '<div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">1️⃣[分段解析+語法標籤]：</span>'
                    )
                    af = af.replace(
                        '2️⃣[詞性辨析]：',
                        '</div><div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">2️⃣[詞性辨析]：</span>'
                    )
                    af = af.replace(
                        '3️⃣[修辭與結構]：',
                        '</div><div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">3️⃣[修辭與結構]：</span>'
                    )
                    af = af.replace(
                        '4️⃣[語意解釋]：',
                        '</div><div style="margin-top:2px; line-height:1.2;">'
                        '<span style="color:#2E8B57; font-weight:bold;">4️⃣[語意解釋]：</span>'
                    )
                    
                    af = af + '</div>'
                    
                    html_parts.append(af)
                
                all_grammar = html_parts
                
            if all_grammar:
                grammar_html = "<br>".join(all_grammar)        
        # ============================================================
        # 渲染畫面
        # ============================================================
        col_left, col_right = st.columns([0.67, 0.33])
        
        with col_left:
            # 單字區塊
            if vocab_display:
                st.markdown(
                    "<div style='margin-bottom:4px; line-height:1.6;'>" + 
                    " ; ".join(vocab_display) + 
                    "</div>", 
                    unsafe_allow_html=True
                )
            else:
                st.caption("無單字資料（請確認有模式A資料）")
            
            st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

            # 片語區塊
            if w_phrases:
                for i, row in enumerate(w_phrases):
                    # 嘗試多種可能的欄位名稱（支援Markdown和CSV的欄位名稱差異）
                    p = (row.get('Word/Phrase', '') or 
                         row.get('Word/phrase', '') or 
                         row.get('words/phrases', '') or 
                         row.get('Word', '') or
                         row.get('No', ''))
                    
                    c = (row.get('Chinese', '') or 
                         row.get('Chinese Meaning', '') or
                         row.get('Meaning', ''))
                    
                    s = (row.get('Synonym+中文對照', '') or 
                         row.get('Synonym', '') or 
                         row.get('Syn', ''))
                    
                    a = (row.get('Antonym+中文對照', '') or 
                         row.get('Antonym', '') or 
                         row.get('Ant', ''))
                    
                    bible_ex = (row.get('全句聖經中英對照例句', '') or 
                               row.get('Bible Example', '') or 
                               row.get('Example', '') or
                               row.get('全句聖經中英對照例句 ', ''))
                    
                    if p and p != str(i+16):  # 確保不是只顯示編號
                        parts = [f"🔤 **{p}**"]
                        if c: 
                            parts.append(f"<span style='color:#666;'>{c}</span>")
                        if s or a:
                            sa_parts = []
                            if s: 
                                sa_parts.append(f"<span style='color:#2E8B57;'>✨{s}</span>")
                            if a: 
                                sa_parts.append(f"<span style='color:#CD5C5C;'>❄️{a}</span>")
                            parts.append("<span style='font-size:0.9em;'>" + " | ".join(sa_parts) + "</span>")
                        
                        st.markdown(
                            "<div style='margin-bottom:2px;'>" + " ".join(parts) + "</div>", 
                            unsafe_allow_html=True
                        )
                        
                        if bible_ex:
                            match = re.match(r'([^(]+)(\([^)]+\))?$', bible_ex)
                            if match:
                                eng_part = match.group(1).strip()
                                cn_part = match.group(2) if match.group(2) else ""
                                bible_html = f"<span style='font-size:1.15em; font-weight:500;'>{eng_part}</span> <span style='font-size:0.9em; color:#666;'>{cn_part}</span>"
                            else:
                                bible_html = f"<span style='font-size:1.15em;'>{bible_ex}</span>"
                            
                            st.markdown(
                                f"<div style='margin-bottom:4px; margin-left:20px;'>📖 {bible_html}</div>", 
                                unsafe_allow_html=True
                            )
                        
                        if i < len(w_phrases) - 1:
                            st.markdown("<div style='margin:4px 0;'></div>", unsafe_allow_html=True)
            else:
                st.caption(f"無片語資料（模式B={len(all_mode_b)}個）")

            st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

            # 金句區塊
            if verse_lines:
                st.markdown(f"<div style='margin-bottom:4px;'>{verse_lines[0]}</div>", unsafe_allow_html=True)
                for v in verse_lines[1:]:
                    st.markdown(f"<div style='margin-bottom:2px;'>{v}</div>", unsafe_allow_html=True)
            else:
                st.caption("📖 無金句資料（請確認有模式A資料）")

        with col_right:
            # 文法區塊
            st.markdown(f"""
                <div style="background-color:#1E1E1E; color:#FFFFFF; padding:10px; border-radius:8px; 
                            border-left:4px solid #FF8C00; font-size:13px; line-height:1.5; 
                            min-height:100%; display:flex; flex-direction:column;">
                    {grammar_html}
                </div>
                """, unsafe_allow_html=True)
            
            minutes_left = max(0, (3600 - time_diff) / 60)
            st.caption(f"單字:{current_vocab_ref} | 片語:{current_phrase_ref} | 金句:{current_verse_ref}")
            st.caption(f"文法:{current_grammar_ref} | {minutes_left:.0f}分後更新")
            st.caption(f"資料統計: A={len(all_mode_a)}個, B={len(all_mode_b)}個, 文法={len(all_grammar_sources)}個")
