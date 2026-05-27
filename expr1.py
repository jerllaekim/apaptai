import streamlit as st
import requests
import random
import json
import google.auth.transport.requests
from google.oauth2 import service_account

# 1. Vertex AI(파인튜닝 모델) 호출 함수 (모든 번역/피드백 통합)
def call_finetune(input_text):
    info = {
        "type": st.secrets["GCP_TYPE"],
        "project_id": st.secrets["GCP_PROJECT_ID"],
        "private_key_id": st.secrets["GCP_PRIVATE_KEY_ID"],
        "private_key": st.secrets["GCP_PRIVATE_KEY"].replace('\\n', '\n'),
        "client_email": st.secrets["GCP_CLIENT_EMAIL"],
        "client_id": st.secrets["GCP_CLIENT_ID"],
        "token_uri": st.secrets["GCP_TOKEN_URI"]
    }
    creds = service_account.Credentials.from_service_account_info(info)
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    
    url = "https://us-central1-aiplatform.googleapis.com/v1/projects/groovy-design-496111-h1/locations/us-central1/endpoints/36530724077043712:predict"
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    payload = {"instances": [{"content": input_text}]}
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['predictions'][0]['content']
    else:
        return f"파인튜닝 모델 호출 실패: {response.status_code}"

# 2. 데이터 로드
@st.cache_data
def get_data_from_github():
    urls = {
        "난민법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/난민법.txt",
        "출입국관리법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/출입국관리법.txt",
        "법령해석": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/법령해석.txt"
    }
    return {k: requests.get(v).text for k, v in urls.items() if requests.get(v).status_code == 200}

# 3. UI 구성
st.set_page_config(layout="wide")
tab1, tab2 = st.tabs(["💬 법률 질의(RAG)", "✍️ 파인튜닝 번역/연습"])

with tab1:
    query = st.text_input("질문 입력")
    if st.button("질문 분석"):
        # 질의응답은 범용 모델 대신 가벼운 모델로 변경하거나 위 로직 유지
        st.info("법률 질의 로직 실행 중...")

with tab2:
    data = get_data_from_github()
    sents = [s.strip() for s in " ".join(data.values()).split(".") if len(s) > 30]
    
    if st.button("연습 문장 뽑기"): 
        st.session_state.p_text = random.choice(sents)
    
    p_text = st.session_state.get('p_text', '버튼을 눌러 문장을 뽑으세요.')
    st.markdown(f"> **원문:** {p_text}")
    
    trans = st.text_area("러시아어 번역 입력:")
    if st.button("번역 및 피드백(파인튜닝)"):
        # 원문과 번역을 파인튜닝 모델에 함께 던져서 피드백 받기
        prompt = f"원문: {p_text}\n번역: {trans}\n위 번역문을 법률 전문가 관점에서 수정하고 피드백하시오."
        st.success(call_finetune(prompt))
