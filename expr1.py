import streamlit as st
import requests
import random
from google import genai
from google.genai import types
from google.oauth2 import service_account

# ====================================================================
# 1. 인증 설정 (Secrets 사용)
# ====================================================================
st.set_page_config(page_title="한-러 법률 번역 실험실", layout="wide")

# (A) Vertex AI용 (파인튜닝된 엔드포인트 전용)
gcp_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(gcp_info)
vertex_client = genai.Client(vertexai=True, project="groovy-design-496111-h1", 
                             location="us-central1", credentials=creds)

# (B) 일반 Gemini용 (데이터 분석 및 번역 연습용)
standard_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ====================================================================
# 2. 깃허브 데이터 로드
# ====================================================================
@st.cache_data
def get_data_from_github():
    urls = {
        "난민법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/난민법.txt",
        "출입국관리법": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/출입국관리법.txt",
        "법령해석": "https://raw.githubusercontent.com/jerllaekim/jusexpr1/main/data/법령해석.txt"
    }
    return {name: requests.get(url).text for name, url in urls.items() if requests.get(url).status_code == 200}

# ====================================================================
# 3. UI 및 기능 구현
# ====================================================================
tab1, tab2, tab3 = st.tabs(["💬 질문하기(일반 모델)", "✍️ 번역 연습", "🚀 파인튜닝 모델 번역"])

# TAB 1: 일반 모델이 데이터 분석 및 문장 추출
with tab1:
    st.subheader("🔍 일반 모델이 데이터에서 문장 찾기")
    data_dict = get_data_from_github()
    query = st.text_input("데이터에서 궁금한 점을 물어보세요.")
    
    if st.button("데이터 분석 및 추출"):
        # 전체 텍스트를 모델에게 넘겨서 질문에 맞는 문장 뽑기 요청
        combined_text = "\n".join([f"[{k}] {v}" for k, v in data_dict.items()])
        prompt = f"다음 법률 데이터를 분석하여 질문에 대한 답변과 관련 문장을 추출하세요.\n\n데이터:{combined_text}\n\n질문:{query}"
        
        with st.spinner("Gemini가 데이터를 읽고 있습니다..."):
            res = standard_client.models.generate_content(
                model="gemini-1.5-flash", 
                contents=prompt
            )
            st.info(res.text)

# TAB 2: 번역 연습 (기존 유지)
with tab2:
    st.subheader("✍️ 번역 연습 및 피드백")
    data = get_data_from_github()
    all_text = " ".join(data.values()).split("\n")
    if st.button("연습 문장 뽑기"): st.session_state.p_text = random.choice([t for t in all_text if len(t) > 20])
    
    p_text = st.session_state.get("p_text", "문장을 불러오세요.")
    st.markdown(f"> **원문:** {p_text}")
    trans = st.text_area("러시아어 번역 입력:")
    
    if st.button("피드백 받기"):
        fb = standard_client.models.generate_content(model="gemini-1.5-flash", 
             contents=f"원문:{p_text}\n번역:{trans}\n법률 관점에서 평가하시오.")
        st.success(fb.text)

# TAB 3: 파인튜닝 모델 번역 (기존 유지)
with tab3:
    st.subheader("🚀 파인튜닝 모델 번역")
    title = st.text_input("안건명")
    ctx = st.text_area("본문 입력")
    if st.button("번역 실행"):
        path = "projects/groovy-design-496111-h1/locations/us-central1/endpoints/36530724077043712"
        res = vertex_client.models.generate_content(model=path, contents=f"안건:{title}\n본문:{ctx}")
        st.markdown(res.text)
