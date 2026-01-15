import streamlit as st
from PIL import Image
import calendar
from datetime import datetime
import pandas as pd
from openpyxl import Workbook

#-----------------------------------------
#TAB1
#-----------------------------------------# 設定語言選擇
language = st.selectbox('選擇語言', ['中文', 'English', '日本語', '한국어', 'ภาษาไทย'])

# 創建左右兩個區域
col_left, col_right = st.columns([0.6, 0.4])

# 左側區域內容
with col_left:
    # 單字與片語
    st.subheader('單字與片語')
    # 假設從資料庫獲取的單字與片語
    vocab = ['單字1', '單字2', '單字3']
    phrases = ['片語1', '片語2', '片語3']
    st.write('單字:', ', '.join(vocab))
    st.write('片語:', ', '.join(phrases))

    # 今日金句
    st.subheader('今日金句')
    # 假設從資料庫獲取的金句
    quote = '這是今日金句的內容。'
    st.write(quote)

    # 今日金句的文法解析
    st.subheader('文法解析')
    # 假設從資料庫獲取的文法解析
    grammar_analysis = '這是今日金句的文法解析。'
    st.write(grammar_analysis)

# 右側區域內容
with col_right:
    # 顯示史努比圖片
    image1 = Image.open('static/183ebb183330643.Y3JvcCw4MDgsNjMyLDAsMA.jpg')
    image2 = Image.open('static/68254faebaafed9dafb41918f74c202e.jpg')
    image3 = Image.open('static/f364bd220887627.67cae1bd07457.jpg')
    st.image(image1, caption='史努比圖片1')
    st.image(image2, caption='史努比圖片2')
    st.image(image3, caption='史努比圖片3')

#-----------------------------------------
#TAB2
#-----------------------------------------
# 顯示當前月份的月曆
st.subheader('當前月份月曆')
current_month = datetime.now().month
current_year = datetime.now().year
st.write(calendar.month(current_year, current_month))

# 右側顯示多語言經文
st.subheader('多語言經文')
# 假設從資料庫獲取的經文
japanese_verse = 'これは日本語の聖句です。'
korean_verse = '이것은 한국어 성경 구절입니다.'
thai_verse = 'นี่คือข้อพระคัมภีร์ภาษาไทย'

st.write('日文:', japanese_verse)
st.write('韓文:', korean_verse)
st.write('泰文:', thai_verse)

# 篩選功能
st.subheader('篩選筆記')
filter_option = st.selectbox('選擇篩選條件', ['標題', '內容', '待辦事項'])
filter_value = st.text_input(f'輸入{filter_option}')

# 顯示每日筆記
st.subheader('每日筆記')
# 假設從資料庫獲取的筆記
notes = [
    {'title': '筆記1', 'content': '這是筆記1的內容。'},
    {'title': '筆記2', 'content': '這是筆記2的內容。'}
]
for note in notes:
    st.write(f"**{note['title']}**")
    st.write(note['content'])

# 連結到 Google AI 的功能
if st.button('連結到 Google AI'):
    # 在此處添加連結邏輯
    st.write('連結到 Google AI')

#-----------------------------------------
#TAB3
#-----------------------------------------
# 篩選功能
st.subheader('選擇翻譯題目時間範圍')
time_range = st.selectbox('選擇時間範圍', ['最新一週', '一個月', '一季'])

# 顯示翻譯題目
st.subheader('翻譯題目')
# 假設從資料庫獲取的題目
chinese_to_english = ['題目1', '題目2', '題目3']
english_to_chinese = ['題目4', '題目5', '題目6']

st.write('中翻英:')
for item in chinese_to_english:
    st.write(f"- {item}")

st.write('英翻中:')
for item in english_to_chinese:
    st.write(f"- {item}")

# 作答區域
st.subheader('作答')
answer = st.text_area('請輸入您的答案')

# 連結到 Google AI 的功能
if st.button('連結到 Google AI'):
    # 在此處添加連結邏輯
    st.write('連結到 Google AI')

#-----------------------------------------
#TAB4
#-----------------------------------------
# 連結到各 AI 的按鈕
st.subheader('連結到各 AI')
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button('連結到 ChatGPT AI'):
        # 在此處添加連結邏輯
        st.write('連結到 ChatGPT AI')
with col2:
    if st.button('連結到 Google AI'):
        # 在此處添加連結邏輯
        st.write('連結到 Google AI')
with col3:
    if st.button('連結到 ESV'):
        # 在此處添加連結邏輯
        st.write('連結到 ESV')
with col4:
    if st.button('連結到 THSV11'):
        # 在此處添加連結邏輯
        st.write('連結到 THSV11')

# 輸入欄位
st.subheader('輸入聖經經文或英文文稿')
bible_verse = st.text_area('聖經經文')
english_text = st.text_area('英文文稿')

# 輸入和存檔按鈕
col1, col2 = st.columns(2)
with col1:
    if st.button('輸入'):
        # 在此處添加輸入邏輯
        st.write('已輸入')
with col2:
    if st.button('存檔'):
        # 在此處添加存檔邏輯
        st.write('已存檔')

#-----------------------------------------
#TAB5
#----------------------------------------- 
# 假設從用戶輸入獲取的資料
bible_verse = '這是聖經經文的內容。'
english_text = 'This is the English text.'

# 生成 Excel 表格
wb = Workbook()
ws = wb.active
ws.title = 'V1 Sheet'

# 寫入資料
ws.append(['Ref.', '經文'])
ws.append(['Pro 17:07', bible_verse])
ws.append(['Pro 17:08', english_text])

# 儲存檔案
wb.save('output.xlsx')
