import streamlit as st
import requests
import random
import os
import json
from google.oauth2 import service_account
from google import genai as genai_vtx
import google.generativeai as genai_std

# 1. UI 설정
st.set_page_config(page_title="한-러 법률 번역 실험실", layout="wide")
st.title("🧪 한-러 법률 및 해석례 번역 실험실")

# 2. 인증 설정 (Secrets 로드 및 캐싱)
@st.cache_resource(show_spinner=False)
def init_clients():
    # Vertex AI (파인튜닝용)
    # Secrets의 gcp_service_account를 dict로 변환하여 로드
    gcp_info = dict(st.secrets["gcp_service_account"])
    creds = service_account.Credentials.from_service_account_info(gcp_info)
    vtx_client = genai_vtx.Client(vertexai=True, project="groovy-design-496111-h1", 
                                 location="us-central1", credentials=creds)
    
    # 일반 모델 (API Key용)
    api_key = st.secrets.get("GEMINI_API_KEY")
    genai_std.configure(api_key=api_key)
    model_std = genai_std.GenerativeModel('gemini-1.5-flash')
    
    return vtx_client, model_std

vtx_client, model_std = init_clients()

# 3. 데이터 로드 (깃허브 연동)
@st.cache_data
def get_data_from_github():
    urls = {
        "난민법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/난민법.txt",
        "출입국관리법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/출입국관리법.txt",
        "법령해석": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/법령해석.txt"
    }
    return {k: requests.get(v).text for k, v in urls.items() if requests.get(v).status_code == 200}

# 4. 기능 탭 구현
tab1, tab2, tab3 = st.tabs(["💬 질문하기(RAG)", "✍️ 번역 연습", "🚀 파인튜닝 모델 번역"])

with tab1:
    st.subheader("🔍 데이터 내 법률 조문 검색")
    query = st.text_input("질문 입력")
    if st.button("질문 분석"):
        data = get_data_from_github()
        prompt = f"데이터: {str(data)[:10000]}\n질문: {query}\n위 데이터 내에서 질문과 관련된 법률 조문이나 해석례를 추출하여 답변하시오."
        res = model_std.generate_content(prompt)
        st.info(res.text)

with tab2:
    st.subheader("✍️ 법률 번역 연습")
    data = get_data_from_github()
    sentences = [s.strip() for s in " ".join(data.values()).split(".") if len(s) > 30]
    if st.button("연습 문장 뽑기"): st.session_state.p_text = random.choice(sentences)
    
    p_text = st.session_state.get("p_text", "버튼을 눌러주세요.")
    st.markdown(f"> **원문:** {p_text}")
    trans = st.text_area("러시아어 번역:")
    if st.button("피드백"):
        fb = model_std.generate_content(f"원문:{p_text}\n번역:{trans}\n법률 전문가 관점에서 평가하시오.")
        st.success(fb.text)

with tab3:
    st.subheader("🚀 파인튜닝 모델 번역 가동")
    title = st.text_input("안건명")
    ctx = st.text_area("본문 입력")
    if st.button("번역 실행"):
        path = "projects/groovy-design-496111-h1/locations/us-central1/endpoints/36530724077043712"
        res = vtx_client.models.generate_content(model=path, contents=f"안건:{title}\n본문:{ctx}")
        st.markdown(res.text)
