import json
import os
import streamlit as st
from google.cloud import discoveryengine_v1beta as discoveryengine
from google.oauth2 import service_account

# ====================================================================
# 1. 보안 인증 설정 (Streamlit Secrets 활용)
# ====================================================================
# 깃허브에 올릴 때 키 노출을 막기 위해 st.secrets를 사용합니다.
try:
    key_dict = json.loads(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(key_dict)
except Exception as e:
    st.error(f"⚠️ Secrets 설정 오류: {e}")
    st.stop()

# ====================================================================
# 2. 구글 에이전트 정보 설정
# ====================================================================
PROJECT_ID = "gen-lang-client-0036116601"
LOCATION = "global"  # 에이전트는 global이 기본값입니다.
DATA_STORE_ID = "여기에_데이터스토어_ID_입력"  # 👈 발급받은 데이터스토어 ID 입력

# ====================================================================
# 3. 에이전트 호출 함수 정의
# ====================================================================
def ask_legal_agent(user_query):
    # 인증 정보를 주입하여 안전하게 클라이언트 생성
    client = discoveryengine.SearchServiceClient(credentials=credentials)
    
    # 에이전트 서빙 경로 설정
    serving_config = client.serving_config_path(
        project=PROJECT_ID,
        location=LOCATION,
        data_store=DATA_STORE_ID,
        serving_config="default_serving_config",
    )
    
    # 에이전트가 학습된 지식을 토대로 답변(Summary)을 생성하도록 요청 구조 설계
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=user_query,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                is_summary_enabled=True,
                summary_result_count=3
            )
        )
    )
    
    response = client.search(string_request=request)
    return response.summary.summary_text

# ====================================================================
# 4. Streamlit UI 구성 (챗봇 단일 도메인 전용)
# ====================================================================
st.set_page_config(
    page_title="한-러 법률 챗봇 에이전트", 
    page_icon="⚖️", 
    layout="centered"
)

st.title("⚖️ 한국 법률 지원 AI 에이전트")
st.caption("러시아어 화자를 위한 대한민국 법률 번역 및 상담 챗봇")

# 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 대화 내용 렌더링
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 사용자 입력창 (Chat Input)
if user_input := st.chat_input("질문할 한국어 법령이나 상담 내용을 입력하세요..."):
    
    # 1. 사용자 메시지 화면 출력 및 세션 저장
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. 에이전트 호출 및 답변 출력
    with st.chat_message("assistant"):
        with st.spinner("에이전트가 법률 지식을 분석하여 러시아어로 전환 중입니다..."):
            try:
                answer = ask_legal_agent(user_input)
                st.write(answer)
                # 3. 에이전트 답변 세션 저장
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"API 호출 중 에러가 발생했습니다: {e}")