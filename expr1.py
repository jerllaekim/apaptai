import streamlit as st
import requests
import random
import google.generativeai as genai_standard  # 일반 모델용
from google import genai as genai_vertex      # 파인튜닝 모델용
from google.oauth2 import service_account

st.set_page_config(page_title="한-러 법률 번역 실험실", layout="wide")

# 1. 인증 설정
# Vertex AI (파인튜닝용)
gcp_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(gcp_info)
vertex_client = genai_vertex.Client(vertexai=True, project="groovy-design-496111-h1", 
                                    location="us-central1", credentials=creds)

# 일반 Gemini (RAG/번역연습용) - 별도 라이브러리 사용
genai_standard.configure(api_key=st.secrets["GEMINI_API_KEY"])
model_std = genai_standard.GenerativeModel('gemini-1.5-flash')

# 2. 데이터 로드
@st.cache_data
def get_data_from_github():
    urls = {
        "난민법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/난민법.txt",
        "출입국관리법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/출입국관리법.txt",
        "법령해석": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/법령해석.txt"
    }
    return {k: requests.get(v).text for k, v in urls.items() if requests.get(v).status_code == 200}

# 3. 탭 구현
tab1, tab2, tab3 = st.tabs(["💬 질문하기", "✍️ 번역 연습", "🚀 파인튜닝 번역"])

with tab1:
    query = st.text_input("질문 입력")
    if st.button("답변받기"):
        data = get_data_from_github()
        prompt = f"데이터: {data}\n\n질문: {query}\n\n답변하시오."
        res = model_std.generate_content(prompt)
        st.info(res.text)

with tab2:
    data = get_data_from_github()
    all_text = " ".join(data.values()).split("\n")
    if st.button("문장 뽑기"): st.session_state.p_text = random.choice([t for t in all_text if len(t) > 20])
    p_text = st.session_state.get("p_text", "")
    st.markdown(f"> **원문:** {p_text}")
    trans = st.text_area("번역 입력")
    if st.button("피드백 받기"):
        fb = model_std.generate_content(f"원문:{p_text}\n번역:{trans}\n평가하시오.")
        st.success(fb.text)

with tab3:
    title = st.text_input("안건명")
    ctx = st.text_area("본문")
    if st.button("번역 실행"):
        path = "projects/groovy-design-496111-h1/locations/us-central1/endpoints/36530724077043712"
        res = vertex_client.models.generate_content(model=path, contents=f"안건:{title}\n본문:{ctx}")
        st.markdown(res.text)
