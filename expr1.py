import json
import random
import requests
import streamlit as st
from google import genai
from google.genai import types
from google.oauth2 import service_account

st.set_page_config(page_title="한-러 법률 번역 실험실", page_icon="🧪", layout="wide")
st.title("🧪 법제처 공식 JSON API 연동 실험실")
st.caption("제공해주신 공식 URL을 기반으로 백엔드에서 실시간 랜덤 데이터를 추출하여 번역합니다.")

# ====================================================================
# 1. 백엔드 인증 일괄 처리 (Secrets 로드)
# ====================================================================
try:
    key_dict = json.loads(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(
        key_dict
    ).with_scopes(["https://www.googleapis.com/auth/cloud-platform"])
    
    # 💡 정래님의Secrets에 등록된 data_go_kr_key를 법제처 OC(인증값)로 사용합니다.
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
# 2. [완벽 수정] 자바 코드 기반 공식 JSON API 호출 및 랜덤 추출 함수
# ====================================================================
def get_random_law_from_official_api():
    # 찐 법제처 공식 JSON 검색 엔드포인트 URL
    url = "https://www.law.go.kr/DRF/lawSearch.do"
    
    # 정래님이 주신 규격에 맞춰 파라미터 빌드
    params = {
        "OC": LAW_GO_OC,      # 💡 Secrets에 저장해둔 정래님의 OC인증값 (jlk092 등)
        "target": "law",       # 서비스 대상 (법령)
        "type": "json"         # 👈 완벽한 JSON 포맷 요청
    }
    
    # 스트림릿 서버 차단 방지용 일반 브라우저 가면(Header) 착용
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        # 실시간 호출
        response = requests.get(url, params=params, headers=headers, timeout=12)
        
        if response.status_code != 200:
            return None, f"❌ 법제처 응답 에러 (Status Code: {response.status_code})"
            
        # 껍질 벗길 필요 없이 곧바로 파이썬 JSON 데이터로 로드!
        data = response.json()
        
        # 법제처 검색 서비스의 실제 JSON 트리 구조를 추적하여 목록 추출
        # 구조: data['SearchLawService']['law'] -> 리스트 형태
        try:
            laws_list = data.get("SearchLawService", {}).get("law", [])
        except AttributeError:
            return None, f"🚨 예상치 못한 JSON 구조입니다. 원본 데이터: {data}"
            
        if not laws_list:
            return None, "조회된 법령 데이터 목록이 비어있습니다."
            
        # 🎲 [핵심] 넘어온 법령 목록 중에서 주사위를 굴려 단 1개만 랜덤 선택!
        selected_law = random.choice(laws_list)
        
        # 실제 법제처 JSON 내부의 표준 키값들로 안전하게 맵핑
        title = selected_law.get("법령명한글", "알 수 없는 법령")
        law_id = selected_law.get("법령ID", "ID 없음")
        link = selected_law.get("법령상세링크", "")
        main_info = selected_law.get("소관부처명", "소관부처 미정")
        
        st.toast(f"📥 실시간 랜덤 법령 선택 완료: {title}", icon="🎲")
        
        # 팩트 컨텍스트 구성
        context = f"""
        [법령명]: {title}
        [법령 고유 ID]: {law_id}
        [소관 부처]: {main_info}
        [상세 링크]: https://www.law.go.kr{link}
        """
        return title, context
        
    except Exception as e:
        return None, f"🚨 백엔드 API 결합 가동 실패: {e}"

# ====================================================================
# 3. 파인튜닝 모델 호출 함수
# ====================================================================
def predict_law_translation(law_title, law_context):
    full_model_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    
    prompt = f"""
    당신은 대한민국 관세 및 법률 전문가이자 최고의 번역가입니다.
    [법제처 실시간 호출 법령 정보]를 정밀히 분석하고, 정래님의 파인튜닝 가이드라인 스타일 스타일에 맞춰 이 법령의 요약 정보와 가이드를 정확한 러시아어(Russian)로 변환하여 출력하세요.

    [대상 법령]: {law_title}
    [법제처 실시간 호출 법령 정보]:
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
# 4. 실험실 UI (버튼 제어)
# ====================================================================
st.write("---")
st.write("### 🎲 무작위 법령 호출 및 번역 시스템")

if st.button("🚀 찐 법제처 API 랜덤 저격 및 러시아어 번역 시작", type="primary"):
    
    with st.spinner("1. 정래님의 찐 API 주소로 실시간 JSON 데이터 긁어오는 중..."):
        result = get_random_law_from_official_api()
        
    if result and result[0]:
        law_title, fetched_context = result
        
        # 화면 좌우 분할
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("### 🇰🇷 법제처 실시간 수신 데이터")
            st.markdown(f"**⚖️ 선택된 법령:** {law_title}")
            st.text_area("파싱된 JSON 내부 정보 데이터", fetched_context, height=300)
            
        with col2:
            st.success("### 🇷🇺 파인튜닝 모델 러시아어 가이드")
            with st.spinner("2. 내 튜닝 모델이 원문 기반 번역문 가동 중..."):
                translated_result = predict_law_translation(law_title, fetched_context)
            st.markdown(translated_result)
    else:
        # 에러 핸들링 메세지 출력
        st.error(result[1] if result else "데이터를 로드하지 못했습니다.")
