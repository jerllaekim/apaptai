import streamlit as st
import requests
import json
import google.auth.transport.requests
from google.oauth2 import service_account

# 1. 인증 정보 로드 (Secrets에서만 가져옴)
def get_auth():
    info = json.loads(st.secrets["GCP_JSON_STR"])
    creds = service_account.Credentials.from_service_account_info(info)
    return creds, info["project_id"]

# 2. Vertex AI 파인튜닝 모델 호출
def call_finetune(input_text):
    creds, project_id = get_auth()
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    
    url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/endpoints/36530724077043712:predict"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    payload = {"instances": [{"content": input_text}]}
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['predictions'][0]['content']
    return f"에러 발생: {response.status_code}"

# 3. UI 및 메인 로직
st.set_page_config(page_title="한-러 법률 번역기", layout="wide")
st.title("🧪 한-러 법률 파인튜닝 번역기")

# 번역 연습 탭
tab1, tab2 = st.tabs(["✍️ 번역 연습", "🚀 파인튜닝 번역"])

with tab1:
    st.markdown("### 번역 연습 및 피드백")
    원문 = st.text_area("원문 입력")
    번역 = st.text_area("번역 입력")
    if st.button("피드백 받기"):
        prompt = f"원문: {원문}\n번역: {번역}\n법률 전문가 관점에서 수정안과 피드백을 제시하시오."
        st.success(call_finetune(prompt))

with tab2:
    st.markdown("### 파인튜닝 번역 실행")
    title = st.text_input("안건명")
    ctx = st.text_area("본문 입력")
    if st.button("번역 실행"):
        prompt = f"안건: {title}\n본문: {ctx}"
        st.markdown(call_finetune(prompt))
