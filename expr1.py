import streamlit as st
import requests
import random
import json
from google.oauth2 import service_account
from google import genai as genai_vtx
import google.generativeai as genai_std

# 1. UI 설정
st.set_page_config(page_title="한-러 법률 번역 실험실", layout="wide")
st.title("🧪 한-러 법률 및 해석례 번역 실험실")

# 2. 인증 설정 (가장 안전한 로드 방식)
def get_gcp_creds():
    # Secrets 값을 dict로 안전하게 변환
    info = dict(st.secrets["gcp_service_account"])
    # private_key의 줄바꿈 문자 복원
    if 'private_key' in info and '\\n' in info['private_key']:
        info['private_key'] = info['private_key'].replace('\\n', '\n')
    return service_account.Credentials.from_service_account_info(info)

# 클라이언트 초기화
creds = get_gcp_creds()
vtx_client = genai_vtx.Client(
    vertexai=True, 
    project="groovy-design-496111-h1", 
    location="us-central1", 
    credentials=creds
)
genai_std.configure(api_key=st.secrets["GEMINI_API_KEY"])
model_std = genai_std.GenerativeModel('gemini-1.5-flash')

# 3. 데이터 로드
@st.cache_data
def get_data_from_github():
    urls = {
        "난민법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/난민법.txt",
        "출입국관리법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/출입국관리법.txt",
        "법령해석": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/법령해석.txt"
    }
    return {k: requests.get(v).text for k, v in urls.items() if requests.get(v).status_code == 200}

# 4. 기능 탭
tab1, tab2, tab3 = st.tabs(["💬 질문하기", "✍️ 번역 연습", "🚀 파인튜닝 번역"])

with tab1:
    query = st.text_input("질문 입력")
    if st.button("질문 분석"):
        data = get_data_from_github()
        res = model_std.generate_content(f"데이터: {str(data)[:10000]}\n질문: {query}\n데이터에서 관련 법률 내용을 추출해.")
        st.info(res.text)

with tab2:
    data = get_data_from_github()
    sentences = [s.strip() for s in " ".join(data.values()).split(".") if len(s) > 30]
    if st.button("문장 뽑기"): st.session_state.p_text = random.choice(sentences)
    p_text = st.session_state.get("p_text", "버튼을 누르세요.")
    st.markdown(f"> **원문:** {p_text}")
    trans = st.text_area("러시아어 번역:")
    if st.button("피드백"):
        fb = model_std.generate_content(f"원문:{p_text}\n번역:{trans}\n법률 전문가 관점에서 수정안 제시.")
        st.success(fb.text)

with tab3:
    title = st.text_input("안건명")
    ctx = st.text_area("본문 입력")
    if st.button("번역 실행"):
        path = "projects/groovy-design-496111-h1/locations/us-central1/endpoints/36530724077043712"
        res = vtx_client.models.generate_content(model=path, contents=f"안건:{title}\n본문:{ctx}")
        st.markdown(res.text)
