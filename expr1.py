import json
import streamlit as st
import requests
import random
from google import genai
from google.genai import types
from google.oauth2 import service_account

# ====================================================================
# 0. 설정 및 인증
# ====================================================================
st.set_page_config(page_title="한-러 법률 번역 실험실", page_icon="🧪", layout="wide")
st.title("🧪 한-러 법률 및 해석례 번역 실험실")

try:
    gcp_account_info = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(
        gcp_account_info
    ).with_scopes(["https://www.googleapis.com/auth/cloud-platform"])
    
    PROJECT_ID = "groovy-design-496111-h1"
    LOCATION = "us-central1"
    ENDPOINT_ID = "36530724077043712"
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION, credentials=credentials)
except Exception as e:
    st.error(f"❌ 설정 실패: {e}")
    st.stop()

# ====================================================================
# 1. 데이터 로드 (깃허브 연동)
# ====================================================================
@st.cache_data
def get_data_from_github():
    urls = {
        "난민법": "https://raw.githubusercontent.com/사용자계정/레포지토리/main/난민법.txt",
        "출입국관리법": "https://raw.githubusercontent.com/사용자계정/레포지토리/main/출입국관리법.txt",
        "법령해석": "https://raw.githubusercontent.com/사용자계정/레포지토리/main/법령해석.txt"
    }
    return {name: requests.get(url).text for name, url in urls.items() if requests.get(url).status_code == 200}

# ====================================================================
# 2. 핵심 함수: 번역 및 RAG
# ====================================================================
def predict_law_translation(law_title, law_context):
    full_model_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    prompt = f"당신은 대한민국 법률 전문가입니다. [안건]: {law_title}\n[본문]: {law_context}\n위 내용을 러시아어로 번역하시오."
    response = client.models.generate_content(model=full_model_path, contents=prompt)
    return response.text

# ====================================================================
# 3. UI 구성 (탭 분리)
# ====================================================================
tab1, tab2, tab3 = st.tabs(["💬 법률 질문(RAG)", "✍️ 번역 연습실", "🚀 파인튜닝 모델 번역"])

# TAB 1: RAG 질의응답
with tab1:
    st.subheader("🔍 학습 데이터 기반 질의응답")
    query = st.text_input("질문 입력", placeholder="예: 난민 신청자의 권리는?")
    if st.button("질문하기"):
        data = get_data_from_github()
        prompt = f"데이터: {data}\n\n질문: {query}\n\n데이터에서 답을 찾으시오. 모르면 '데이터에서 찾을 수 없습니다'라고 하시오."
        res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        st.info(res.text)

# TAB 2: 번역 연습
with tab2:
    st.subheader("✍️ 번역 연습 및 피드백")
    data = get_data_from_github()
    all_text = " ".join(data.values()).split("\n")
    if st.button("연습 문장 뽑기"):
        st.session_state.practice_text = random.choice([t for t in all_text if len(t) > 20])
    
    p_text = st.session_state.get("practice_text", "버튼을 눌러 문장을 불러오세요.")
    st.markdown(f"> **원문:** {p_text}")
    
    user_trans = st.text_area("러시아어 번역 입력:")
    if st.button("결과 확인"):
        fb_prompt = f"원문: {p_text}\n사용자 번역: {user_trans}\n\n법률적 관점에서 피드백과 수정안을 주시오."
        feedback = client.models.generate_content(model="gemini-1.5-flash", contents=fb_prompt)
        st.success(feedback.text)

# TAB 3: 기존 파인튜닝 모델 활용
with tab3:
    st.subheader("🚀 파인튜닝 모델 번역 가동")
    col1, col2 = st.columns(2)
    with col1:
        in_title = st.text_input("안건명")
        in_ctx = st.text_area("본문 입력")
    with col2:
        if st.button("번역 실행"):
            st.markdown(predict_law_translation(in_title, in_ctx))
