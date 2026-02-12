import streamlit as st
import requests

st.title("🔧 Notion 連線測試")

# 測試 1: 檢查 secrets 是否存在
st.subheader("1. Secrets 檢查")
if "notion" in st.secrets:
    st.success("✅ [notion] 區段存在")
    notion = st.secrets["notion"]
    st.write(f"Keys: {list(notion.keys())}")
    
    token = notion.get("token", "")
    db_id = notion.get("database_id", "")
    
    st.write(f"Token 長度: {len(token)}")
    st.write(f"Token 前10碼: {token[:10]}..." if token else "Token 為空")
    st.write(f"Database ID: {db_id[:15]}..." if db_id else "DB ID 為空")
else:
    st.error("❌ [notion] 區段不存在")
    st.write(f"可用的 keys: {list(st.secrets.keys())}")
    st.stop()

# 測試 2: API 連線測試
st.subheader("2. API 連線測試")

if token:
    # 測試 users/me (最簡單的 API)
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        response = requests.get("https://api.notion.com/v1/users/me", headers=headers)
        st.write(f"Users/me 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            st.success("✅ Token 有效！")
            st.json(response.json())
        else:
            st.error(f"❌ Token 無效: {response.text[:200]}")
    except Exception as e:
        st.error(f"❌ 請求失敗: {e}")

# 測試 3: 資料庫查詢測試
st.subheader("3. 資料庫查詢測試")

if token and db_id:
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    st.code(f"URL: {url}", language="text")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json={"page_size": 1})
        st.write(f"Query 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            st.success(f"✅ 資料庫連線成功！找到 {len(data.get('results', []))} 筆資料")
        else:
            st.error(f"❌ 查詢失敗: {response.text[:300]}")
    except Exception as e:
        st.error(f"❌ 請求失敗: {e}")
