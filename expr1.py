import json
import streamlit as st
from google.cloud import aiplatform
from google.oauth2 import service_account
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

# ====================================================================
# 1. 서비스 계정 JSON 키 인증 (Streamlit Secrets에서 가져옴)
# ====================================================================
try:
    # 이메일 ID가 아니라, 다운로드받은 JSON 파일 내용 전체를 사전 형태로 읽어옵니다.
    key_dict = json.loads(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(key_dict)
except Exception as e:
    st.error(f"⚠️ Secrets 인증 오류: {e}")
    st.stop()

# ====================================================================
# 2. 정래님이 확인한 구글 클라우드 정보 입력
# ====================================================================
PROJECT_ID = "gen-lang-client-0036116601"
LOCATION = "us-central1"               # 👈 [확인필요] 엔드포인트 화면에 적힌 지역명 입력
ENDPOINT_ID = "4166613057352499200"    # 👈 정래님이 찾으신 4로 시작하는 배포 키

# 인증 정보를 가지고 Vertex AI 시스템 초기화
aiplatform.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

# ====================================================================
# 3. 모델 호출 함수 정의
# ====================================================================
def predict_law_translation(text):
    # 만능열쇠(인증)를 들고 4...번 엔드포인트 사물함 주소로 찾아갑니다.
    endpoint = aiplatform.Endpoint(
        endpoint_name=f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    )
    
    # Gemini 튜닝 모델이 인식할 수 있는 정석 포맷으로 입력값 포장
    instances = [
        json_format.ParseDict({
            "contents": [{"role": "user", "parts": [{"text": text}]}]
        }, Value())
    ]
    
    # 구글 서버에 요청 후 결과 받기
    response = endpoint.predict(instances=instances)
    
    # 모델의 첫 번째 답변 텍스트만 추출
    return response.predictions[0]

# ====================================================================
# 4. Streamlit 챗봇 UI 
# ====================================================================
st.set_page_config(page_title="한-러 법률 번역기", page_icon="⚖️")
st.title("⚖️ 한-러 법률 번역 AI 챗봇")

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
        with st.spinner("파인튜닝된 모델이 번역 중입니다..."):
            try:
                answer = predict_law_translation(user_input)
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"호출 실패: {e}\n\n지역(LOCATION) 설정이나 서비스 계정 권한을 다시 확인해보세요.")
