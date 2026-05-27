import streamlit as st
import requests
import random
import os
from google.oauth2 import service_account
from google import genai as genai_vtx

# 1. 파인튜닝용 Vertex AI 클라이언트 (이미 잘 작동하던 방식 유지)
@st.cache_resource(show_spinner=False)
def get_vtx_client():
    gcp_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(gcp_info)
    return genai_vtx.Client(vertexai=True, project="groovy-design-496111-h1", location="us-central1", credentials=creds)

vtx_client = get_vtx_client()

# 2. 일반 모델용 호출 (SDK 대신 requests 사용 - NotFound 에러 차단)
def call_gemini_direct(prompt):
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"에러 발생: {response.status_code} - {response.text}"

# 3. 데이터 로드
@st.cache_data
def get_data_from_github():
    urls = {
        "난민법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/난민법.txt",
        "출입국관리법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/출입국관리법.txt",
        "법령해석": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/법령해석.txt"
    }
    return {k: requests.get(v).text for k, v in urls.items() if requests.get(v).status_code == 200}

# 4. UI
st.set_page_config(page_title="한-러 법률 번역 실험실", layout="wide")
tab1, tab2, tab3 = st.tabs(["💬 질문하기", "✍️ 번역 연습", "🚀 파인튜닝 번역"])

with tab1:
    query = st.text_input("질문 입력")
    if st.button("답변받기"):
        data = get_data_from_github()
        res = call_gemini_direct(f"데이터:{str(data)[:10000]}\n질문:{query}\n데이터에서만 답하시오.")
        st.info(res)

with tab2:
    data = get_data_from_github()
    sentences = [s.strip() for s in " ".join(data.values()).split(".") if len(s) > 30]
    if st.button("문장 뽑기"): st.session_state.p_text = random.choice(sentences)
    p_text = st.session_state.get("p_text", "버튼을 누르세요.")
    st.markdown(f"> **원문:** {p_text}")
    trans = st.text_area("번역 입력")
    if st.button("피드백 받기"):
        fb = call_gemini_direct(f"원문:{p_text}\n번역:{trans}\n법률 전문가 관점에서 수정안 제시.")
        st.success(fb)

with tab3:
    title = st.text_input("안건명")
    ctx = st.text_area("본문")
    if st.button("번역 실행"):
        path = "projects/groovy-design-496111-h1/locations/us-central1/endpoints/36530724077043712"
        res = vtx_client.models.generate_content(model=path, contents=f"안건:{title}\n본문:{ctx}")
        st.markdown(res.text)
