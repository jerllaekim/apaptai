import json
import streamlit as st
from google import genai
from google.genai import types
from google.oauth2 import service_account

# ====================================================================
# 0. 스트림릿 기본 UI 페이지 설정
# ====================================================================
st.set_page_config(page_title="한-러 법률 번역 실험실", page_icon="🧪", layout="wide")
st.title("🧪 한-러 법률 및 해석례 번역 실험실")
st.caption("30만 문장 파인튜닝이 완료된 Gemini 3 Flash 모델의 번역 성능을 직접 테스트하는 샌드박스입니다.")

# ====================================================================
# 1. 친구분 GCP 계정 기반 백엔드 인증 처리 (Secrets 로드)
# ====================================================================
try:
    # 스트림릿 AttrDict 객체를 그대로 활용 (PEM 바이트 지옥 탈출)
    gcp_account_info = st.secrets["gcp_service_account"]
    
    credentials = service_account.Credentials.from_service_account_info(
        gcp_account_info
    ).with_scopes(["https://www.googleapis.com/auth/cloud-platform"])
    
except Exception as e:
    st.error(f"❌ 백엔드 환경 설정(Secrets) 로드 실패: {e}")
    st.stop()

# ====================================================================
# 2. 족보 일치 핵심 변수 정의 (친구 프로젝트 ID 및 찐 엔드포인트 번호 매칭)
# ====================================================================
PROJECT_ID = "groovy-design-496111-h1"     # 친구분 GCP 프로젝트 ID
LOCATION = "us-central1"                   # Vertex AI 기본 리전
ENDPOINT_ID = "36530724077043712"          # 🎯 정래님이 찾으신 진짜 엔드포인트 ID!

# 구글 Vertex AI 클라이언트 초기화 
try:
    client = genai.Client(
        vertexai=True, 
        project=PROJECT_ID, 
        location=LOCATION, 
        credentials=credentials
    )
except Exception as e:
    st.error(f"❌ 구글 클라이언트 초기화 실패: {e}")
    st.stop()

# ====================================================================
# 3. 404 에러 원천 차단용 엔드포인트 직렬 호출 번역 함수
# ====================================================================
def predict_law_translation(law_title, law_context):
    # 구글 SDK 내부 주소 빌드 버그를 방지하기 위해 프로젝트와 찐 엔드포인트 풀 경로를 결합합니다.
    full_model_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    
    prompt = f"""
    당신은 대한민국 관세 및 법률 전문가이자 최고의 번역가입니다.
    다음 [제공된 대한민국 법률 및 해석례 정보]를 정밀히 분석하고, 러시아어(Russian)로 변역한 문장만 내놓으시오.

    [대상 안건/법령명]: {law_title}
    [제공된 대한민국 법률 및 해석례 정보]:
    {law_context}
    """
    try:
        # model 인자에 꼬인 튜닝ID 대신 완벽하게 조립된 엔드포인트 풀 주소 주입!
        response = client.models.generate_content(
            model=full_model_path,  
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2),
        )
        return response.text
    except Exception as e:
        return f"❌ 구글 튜닝 모델 호출 실패: {e}"

# ====================================================================
# 4. 사용자 UI 및 텍스트 마이닝 입력창 생성
# ====================================================================
st.write("---")
st.write("### 🔍 테스트할 법률 안건 및 본문 입력")

col_in1, col_in2 = st.columns([1, 2])

with col_in1:
    input_title = st.text_input(
        "⚖️ 안건명 또는 법령명 입력", 
        value="고용노동부 법령해석 안건 테스트",
        placeholder="예: 채용시 건강진단 비용 관련 질의"
    )

with col_in2:
    input_context = st.text_area(
        "📂 법률 본문 또는 질의/회답 내용 입력 (Fact)",
        value="[질의요지]\n06.1.1 이후 채용 시 건강진단 비용을 산업안전보건관리비로 사용할 수 있는지 여부\n\n[회답]\n산업안전보건법 제30조 및 동법 시행령에 의거하여, 근로자의 건강관리를 위한 비용은 소관 규격에 따라 산정될 수 있으나 채용 시 건강진단 비용은 사업주가 전액 부담해야 하는 법적 의무 사항이므로...",
        height=200,
        placeholder="학습 데이터셋에 포함되지 않았던 찐 고용노동부 회답 문장을 복사해서 넣어보세요."
    )

st.write("---")

# ====================================================================
# 5. 번역 실행 트리거 및 결과 화면 매칭
# ====================================================================
if st.button("🚀 30만 문장 파인튜닝 모델 번역 가동", type="primary"):
    
    if not input_title.strip() or not input_context.strip():
        st.warning("⚠️ 안건명과 본문 내용을 모두 채워주셔야 프롬프팅이 완벽히 작동합니다.")
        st.stop()
        
    # 화면을 데칼코마니 형태로 반반 분할
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("### 🇰🇷 입력된 한국어 팩트 원문")
        st.markdown(f"**⚖️ 대상 명칭:** {input_title}")
        st.info(input_context)
        
    with col2:
        st.success("### 🇷🇺 파인튜닝 모델 러시아어 가이드 출력")
        with st.spinner("정밀 번역 중..."):
            translated_result = predict_law_translation(input_title, input_context)
        st.markdown(translated_result)
@st.cache_data
def get_data_from_github():
    urls = {
        "난민법": "https://raw.githubusercontent.com/.../난민법.txt",
        "출입국관리법": "https://raw.githubusercontent.com/.../출입국관리법.txt",
        "법령해석": "https://raw.githubusercontent.com/.../법령해석.txt"
    }
    return {name: requests.get(url).text for name, url in urls.items()}

# 탭 나누기
tab1, tab2 = st.tabs(["💬 법률 질문(RAG)", "✍️ 번역 연습실"])

# ====================================================================
# TAB 1: 법률 질문 (RAG)
# ====================================================================
with tab1:
    st.subheader("🔍 학습 데이터 기반 질의응답")
    query = st.text_input("질문 입력", placeholder="예: 난민법상 난민의 지위는?")
    if st.button("질문하기"):
        data = get_data_from_github()
        prompt = f"데이터: {data}\n\n질문: {query}\n\n위 데이터에서 답을 찾으시오. 모르면 '데이터에서 찾을 수 없습니다'라고 하시오."
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        st.info(response.text)

# ====================================================================
# TAB 2: 번역 연습 (원래 코드 확장)
# ====================================================================
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
        # 1. 사용자가 번역한 문장을 원래 만드신 파인튜닝 모델로 평가하기
        # 여기서는 평가용 프롬프트를 따로 구성합니다.
        feedback_prompt = f"원문: {p_text}\n사용자 번역: {user_trans}\n\n법률 전문가로서 이 번역의 정확도를 평가하고 수정안을 제시하시오."
        feedback = client.models.generate_content(model="gemini-1.5-flash", contents=feedback_prompt)
        st.success(feedback.text)

# ====================================================================
# 기존의 30만 문장 파인튜닝 모델 번역 (연습실 아래나 별도 섹션으로 배치)
# ====================================================================
st.write("---")
# [여기서부터 기존의 predict_law_translation 함수를 사용하는 번역 섹션을 배치하면 됩니다.]
