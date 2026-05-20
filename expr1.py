import json
import streamlit as st
from google import genai
from google.genai import types
from google.oauth2 import service_account

st.set_page_config(page_title="한-러 법률 번역 실험실", page_icon="🧪", layout="wide")
st.title("🧪 한-러 법률 및 해석례 번역 실험실 (검색/입력 엔진)")
st.caption("파인튜닝 완료된 Gemini 3 Flash 모델의 번역 성능을 직접 테스트하는 샌드박스입니다.")

# ====================================================================
# 1. 백엔드 인증 일괄 처리 (Secrets 로드) - AttrDict 에러 완벽 수정
# ====================================================================
try:
    # json.loads 필요 없이 스트림릿이 준 객체 그대로 서비스 계정 인포에 주입합니다.
    gcp_account_info = st.secrets["gcp_service_account"]
    
    credentials = service_account.Credentials.from_service_account_info(
        gcp_account_info
    ).with_scopes(["https://www.googleapis.com/auth/cloud-platform"])
    
except Exception as e:
    st.error(f"❌ 백엔드 환경 설정(Secrets) 로드 실패: {e}")
    st.stop()
# ====================================================================
# 2. 파인튜닝 모델 호출 함수
# ====================================================================
def predict_law_translation(law_title, law_context):
    full_model_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    
    prompt = f"""
    당신은 대한민국 관세 및 법률 전문가이자 최고의 번역가입니다.
    다음 [제공된 대한민국 법률 및 해석례 정보]를 정밀히 분석하고, 정래님의 파인튜닝 가이드라인 스타일에 맞춰 이 내용의 요약 정보와 가이드를 정확한 러시아어(Russian)로 변환하여 출력하세요.

    [대상 안건/법령명]: {law_title}
    [제공된 대한민국 법률 및 해석례 정보]:
    {law_context}
    """
    try:
        response = client.models.generate_content(
            model=full_model_path,  
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2),
        )
        return response.text
    except Exception as e:
        return f"❌ 구글 튜닝 모델 호출 실패: {e}"

# ====================================================================
# 3. UI 및 입력 엔진 (과거 기능 복구)
# ====================================================================
st.write("---")
st.write("### 🔍 테스트할 법률 안건 및 본문 입력")

# 사용자에게 날것의 데이터를 입력받는 검색/입력 프레임 세팅
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
        value="[질의요지]\n여기에 고용노동부 질의나 회답, 혹은 관세법 관련 팩트 문장을 자유롭게 넣어보세요.\n\n[회답]\n파인튜닝된 뇌가 가이드라인 양식을 지키며 러시아어로 뿜어내게 됩니다.",
        height=200,
        placeholder="학습에 사용되지 않은 진짜 법령 본문이나 고용노동부 해석례를 붙여넣으세요."
    )

st.write("---")

# 번역 실행 트리거 버튼
if st.button("🚀 30만 문장 파인튜닝 모델 번역 가동", type="primary"):
    
    if not input_title.strip() or not input_context.strip():
        st.warning("⚠️ 안건명과 본문 내용을 모두 채워주셔야 완벽한 프롬프팅이 작동합니다.")
        st.stop()
        
    # 화면 좌우 분할 매칭
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("### 🇰🇷 입력된 한국어 팩트 원문")
        st.markdown(f"**⚖️ 대상 명칭:** {input_title}")
        st.info(input_context)
        
    with col2:
        st.success("### 🇷🇺 파인튜닝 모델 러시아어 가이드 출력")
        with st.spinner("🤖 정래님의 튜닝 엔드포인트(`41666...`)가 정밀 번역 중..."):
            translated_result = predict_law_translation(input_title, input_context)
        st.markdown(translated_result)
