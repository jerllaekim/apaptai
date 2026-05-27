import streamlit as st
import requests
import random
import json
from google.oauth2 import service_account
from google import genai as genai_vtx
import google.generativeai as genai_std

# 1. 환경 설정
st.set_page_config(page_title="한-러 법률 번역 실험실", layout="wide")

# 2. 인증 객체 생성
def get_auth():
    # Secrets에서 JSON 형태로 안전하게 로드
    info = dict(st.secrets["gcp_service_account"])
    # private_key 내부의 줄바꿈 문자 처리
    if 'private_key' in info and '\\n' in info['private_key']:
        info['private_key'] = info['private_key'].replace('\\n', '\n')
    
    creds = service_account.Credentials.from_service_account_info(info)
    
    # 클라이언트 초기화
    vtx_client = genai_vtx.Client(vertexai=True, project=info["project_id"], location="us-central1", credentials=creds)
    genai_std.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_std = genai_std.GenerativeModel('gemini-1.5-flash')
    
    return vtx_client, model_std

vtx_client, model_std = get_auth()

# 3. 데이터 로드
@st.cache_data
def get_data_from_github():
    urls = {
        "난민법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/난민법.txt",
        "출입국관리법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/출입국관리법.txt",
        "법령해석": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/법령해석.txt"
    }
    return {k: requests.get(v).text for k, v in urls.items() if requests.get(v).status_code == 200}

# 4. 기능 구현
tab1, tab2, tab3 = st.tabs(["💬 질문하기", "✍️ 번역 연습", "🚀 파인튜닝 번역"])

with tab1:
    query = st.text_input("질문 입력")
    if st.button("분석 시작"):
        data = get_data_from_github()
        res = model_std.generate_content(f"질문: {query}\n데이터: {str(data)[:5000]}")
        st.info(res.text)

with tab2:
    data = get_data_from_github()
    sents = [s.strip() for s in " ".join(data.values()).split(".") if len(s) > 30]
    if st.button("문장 뽑기"): st.session_state.p_text = random.choice(sents)
    st.markdown(f"> **원문:** {st.session_state.get('p_text', '버튼 클릭')}")
    trans = st.text_area("번역 입력")
    if st.button("피드백 확인"):
        fb = model_std.generate_content(f"원문:{st.session_state.p_text}\n번역:{trans}\n평가하시오.")
        st.success(fb.text)

with tab3:
    title = st.text_input("안건명")
    ctx = st.text_area("본문 입력")
    if st.button("실행"):
        path = "projects/groovy-design-496111-h1/locations/us-central1/endpoints/36530724077043712"
        res = vtx_client.models.generate_content(model=path, contents=f"안건:{title}\n본문:{ctx}")
        st.markdown(res.text)
