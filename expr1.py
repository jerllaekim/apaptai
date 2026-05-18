import json
import streamlit as st
from google import genai
from google.genai import types
from google.oauth2 import service_account

st.set_page_config(page_title="한-러 법률 번역기", page_icon="⚖️")
st.title("⚖️ 한-러 법률 번역 AI 챗봇")

# ====================================================================
# 1. 서비스 계정 인증 (Streamlit Secrets)
# ====================================================================
try:
    key_dict = json.loads(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(key_dict)
except Exception as e:
    st.error(f"❌ [Secrets 파일 오류] JSON 키 형식을 확인하세요: {e}")
    st.stop()

# ====================================================================
# 2. 정래님의 구글 클라우드 환경 설정값
# ====================================================================
PROJECT_ID = "gen-lang-client-0036116601"
LOCATION = "us-central1"               # 👈 엔드포인트 지역 (us-central1 또는 asia-northeast3)
ENDPOINT_ID = "4166613057352499200"    # 👈 4로 시작하는 긴 숫자 키

# 최신 GenAI 클라이언트에 인증 정보 주입하여 초기화
try:
    client = genai.Client(
        credentials=credentials,
        http_options={'api_version': 'v1alpha'}  # 튜닝 엔드포인트 호출을 위한 알파 버전 지정
    )
except Exception as e:
    st.error(f"❌ 구글 클라이언트 초기화 실패: {e}")
    st.stop()

# ====================================================================
# 3. 모델 호출 함수 정의 (최신 GenAI 정석 문법)
# ====================================================================
def predict_law_translation(text):
    # 최신 SDK에서 튜닝 모델 엔드포인트를 지정하는 정석 경로 표현식
    model_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    
    try:
        # 직렬화 오브젝트 없이 일반 텍스트 포맷으로 직접 찌릅니다.
        response = client.models.generate_content(
            model=model_path,
            contents=text,
            config=types.GenerateContentConfig(
                temperature=0.2,  # 법률 번역이므로 일관성을 위해 낮춤
            ),
        )
        return response.text
    except Exception as e:
        st.error(f"❌ 구글 API 호출 실패: {e}")
        st.info("💡 만약 여기서 에러가 난다면 하드코딩된 LOCATION이 틀렸거나, 서비스 계정에 'Vertex AI User' 권한이 누락된 것입니다.")
        return None

# ====================================================================
# 4. 챗봇 UI 및 대화 처리
# ====================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_input := st.chat_input("법제처 등에서 가져온 한국어 법률 문장을 입력하세요..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner("파인튜닝된 Gemini 모델이 번역 중..."):
            answer = predict_law_translation(user_input)
            if answer:
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
