import json
import random
import requests
import streamlit as st
from google import genai
from google.genai import types
from google.oauth2 import service_account
from bs4 import BeautifulSoup  # 👈 HTML로 오는 본문을 깨끗하게 닦아내기 위해 사용

st.set_page_config(page_title="법제처 실시간 저격 실험실", page_icon="🧪", layout="wide")
st.title("🧪 법제처 메인 API 팩트 연동 실험실")
st.caption("카테고리를 다 긁어올 필요 없이, 타겟 ID만 무작위로 실시간 저격합니다.")

# ====================================================================
# 1. 백엔드 인증 (Secrets에서 구글 마스터키 및 법제처 OC 키 로드)
# ====================================================================
try:
    key_dict = json.loads(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(
        key_dict
    ).with_scopes(["https://www.googleapis.com/auth/cloud-platform"])
    
    # 법제처 공식 OC 인증키 백엔드 로드
    LAW_GO_OC = st.secrets["data_go_kr_key"] 
except Exception as e:
    st.error(f"❌ 백엔드 환경 설정(Secrets) 로드 실패: {e}")
    st.stop()

# 구글 클라이언트 초기화
PROJECT_ID = "gen-lang-client-0036116601"
LOCATION = "us-central1"               
ENDPOINT_ID = "4166613057352499200"    

try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION, credentials=credentials)
except Exception as e:
    st.error(f"❌ 구글 클라이언트 초기화 실패: {e}")
    st.stop()

# ====================================================================
# 2. [수정] 보내주신 모바일 가이드 기준 실시간 본문 호출 함수
# ====================================================================
def get_law_expc_realtime():
    # 보내주신 법제처 메인 서버 URL
    url = "http://www.law.go.kr/DRF/lawService.do"
    
    # 💡 실험용으로 널리 쓰이는 법령해석례 일련번호(ID) 범위를 지정합니다.
    # 테스트를 위해 대략 최근 데이터 ID 범위인 30000 ~ 32000 사이를 무작위로 찌릅니다.
    random_id = random.randint(30000, 32000)
    
    params = {
        "OC": LAW_GO_OC,
        "target": "expc",       # 👈 법령해석례 타겟 명시
        "ID": str(random_id),   # 👈 랜덤으로 생성한 일련번호 저격
        "type": "HTML",         # 👈 가이드대로 HTML 지정
        "mobileYn": "Y"         # 👈 가이드 필수값 설정
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None, f"법제처 통신 실패 (코드: {response.status_code})"
            
        # 법제처가 준 HTML 덩어리에서 글자 찌꺼기를 파이썬 BeautifulSoup으로 청소합니다.
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 전체 텍스트 추출 및 공백 정리
        cleaned_text = soup.get_text(separator="\n").strip()
        
        if "조회된 데이터가 없습니다" in cleaned_text or len(cleaned_text) < 100:
            # 주사위 번호가 빈 사물함일 경우 한 번 더 재귀 호출하거나 패스
            return None, "빈 사물함(존재하지 않는 ID)이 뽑혔습니다. 다시 눌러보세요."
            
        return random_id, cleaned_text
    except Exception as e:
        return None, f"API 가동 에러: {e}"

# ====================================================================
# 3. 파인튜닝 모델 호출 함수
# ====================================================================
def predict_law_translation(law_context):
    full_model_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    
    prompt = f"""
    당신은 대한민국 법률 전문가이자 최고의 번역가입니다.
    다음 [법제처 실시간 해석례 본문]을 분석하고, 핵심 질의와 답변 내용을 요약하여 정확한 러시아어(Russian)로 전문적인 번역 가이드를 출력하세요.

    [법제처 실시간 해석례 본문]:
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
# 4. 실험실 UI (버튼)
# ====================================================================
st.write("---")
if st.button("🎲 법제처 메인 서버에서 랜덤 ID 저격 호출하기", type="primary"):
    
    with st.spinner("법제처 메인 서버에 무작위 ID 찌르는 중..."):
        picked_id, fetched_context = get_law_expc_realtime()
        
    if picked_id:
        st.toast(f"📥 ID {picked_id}번 저격 성공!", icon="✅")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"### 🇰🇷 법제처 실시간 원문 (ID: {picked_id})")
            # 텍스트가 너무 길면 보기 힘드니까 스크롤 박스 형태로 출력
            st.text_area("HTML 파싱 완료된 원본 데이터", fetched_context, height=450)
            
        with col2:
            st.success("### 🇷🇺 파인튜닝 모델 러시아어 가이드")
            with st.spinner("튜닝 모델이 원문을 기반으로 변환 중..."):
                translated_result = predict_law_translation(fetched_context)
            st.markdown(translated_result)
    else:
        # 빈 사물함 떴을 때 안내
        st.warning(fetched_context)
