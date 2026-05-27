import streamlit as st
import requests
import random
import google.auth.transport.requests
from google.oauth2 import service_account

# 1. Secrets가 없거나 키가 없어도 에러가 나지 않도록 방어 코드 추가
def get_secret(key):
    try:
        return st.secrets[key]
    except KeyError:
        st.error(f"⚠️ 설정 오류: '{key}' 값이 Secrets에 없습니다. 'Manage app' > 'Secrets'를 확인하세요.")
        st.stop()

# 2. 파인튜닝 모델 호출 (모든 작업 통합)
def call_finetune(input_text):
    # 안전하게 Secrets 값 가져오기
    info = {
        "type": get_secret("GCP_TYPE"),
        "project_id": get_secret("GCP_PROJECT_ID"),
        "private_key_id": get_secret("GCP_PRIVATE_KEY_ID"),
        "private_key": get_secret("GCP_PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": get_secret("GCP_CLIENT_EMAIL"),
        "client_id": get_secret("GCP_CLIENT_ID"),
        "token_uri": get_secret("GCP_TOKEN_URI")
    }
    
    creds = service_account.Credentials.from_service_account_info(info)
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    
    url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{info['project_id']}/locations/us-central1/endpoints/36530724077043712:predict"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    payload = {"instances": [{"content": input_text}]}
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['predictions'][0]['content']
    else:
        return f"파인튜닝 모델 호출 실패 (Status: {response.status_code}): {response.text}"

# 3. UI 및 기타 로직은 그대로 유지
# ... (이전 코드의 데이터 로드 및 탭 구성과 동일)
