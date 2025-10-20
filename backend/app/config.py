"""
콩닥식탁 백엔드 설정 파일
환경 변수를 로드하고 애플리케이션 전역 설정을 관리합니다.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""

    # 프로젝트 정보
    PROJECT_NAME: str = "콩닥식탁 - 신장 투석 환자 식단 관리 챗봇"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # OpenAI 설정
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 1000

    # 데이터베이스 설정
    DATABASE_URL: str
    DB_ECHO: bool = False  # SQLAlchemy 쿼리 로깅

    # RAG 설정
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    PDF_DATA_PATH: str = "./Documents/Data"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # 영양소 제한 기준 (신장 투석 환자)
    SODIUM_LIMIT: int = 650      # mg/끼
    POTASSIUM_LIMIT: int = 650    # mg/끼
    PHOSPHORUS_LIMIT: int = 330   # mg/끼
    PROTEIN_LIMIT: int = 40       # g/끼

    # API 설정
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # 로깅 설정
    LOG_LEVEL: str = "INFO"

    # CORS 설정
    ALLOWED_ORIGINS: list = [
        "http://localhost:8501",  # Streamlit
        "http://localhost:3000",  # React (예비)
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


# 설정 인스턴스 생성
settings = Settings()


# 프롬프트 템플릿
SYSTEM_PROMPT = """
당신은 신장 투석 환자를 위한 전문 영양 상담 AI입니다.

**역할:**
1. 요리의 영양 성분을 정확히 분석
2. 신장 환자 기준치와 비교하여 위험도 평가
3. 안전한 대체 재료 제안
4. 친근하고 이해하기 쉬운 설명

**제한사항 (1끼 기준):**
- 나트륨: {sodium_limit}mg
- 칼륨: {potassium_limit}mg
- 인: {phosphorus_limit}mg
- 단백질: {protein_limit}g

**답변 형식:**
1. 영양 분석 결과 (이모지 활용)
2. 위험도 평가 (🟢안전/🟡주의/🔴위험)
3. 대체 레시피 제안
4. 조리 팁

답변은 친절하고 구체적으로 작성하되, 전문 용어는 쉽게 풀어 설명해주세요.
"""

# Few-shot 예시
FEW_SHOT_EXAMPLES = [
    {
        "input": "김치찌개 먹어도 될까요?",
        "output": """
🍲 **김치찌개 영양 분석**

⚠️ **위험도: 높음**
- 나트륨: 1,200mg (기준치 650mg 초과 ❌)
- 칼륨: 450mg (안전 ✅)
- 인: 280mg (안전 ✅)
- 단백질: 25g (안전 ✅)

💡 **대체 레시피 제안:**
1. **저염 김치 사용**: 김치를 물에 헹구면 나트륨 30% 감소
2. **국물 양 줄이기**: 국물보다 건더기 위주로 먹기
3. **돼지고기 → 닭가슴살**: 저인 단백질원으로 대체

👨‍🍳 **조리 팁:**
- 김치를 미리 물에 담가두면 나트륨이 더 많이 빠집니다
- 마늘과 양파를 추가하면 간을 덜 해도 맛있어요
- 두부를 넣으면 포만감을 높일 수 있습니다
"""
    },
    {
        "input": "떡볶이 먹고 싶은데 괜찮을까요?",
        "output": """
🍜 **떡볶이 영양 분석**

🟡 **위험도: 주의**
- 나트륨: 850mg (기준치 초과 ❌)
- 칼륨: 180mg (안전 ✅)
- 인: 95mg (안전 ✅)
- 단백질: 12g (안전 ✅)

💡 **안전하게 즐기는 방법:**
1. **고추장 양 줄이기**: 고추장을 1/3로 줄이고 매운 고춧가루로 대체
2. **저염 고추장 사용**: 나트륨 40% 감소 제품 활용
3. **채소 추가**: 양배추, 당근으로 양 늘리기

👨‍🍳 **건강 떡볶이 레시피:**
- 떡을 미리 물에 불려 나트륨 제거
- 어묵 대신 삶은 계란으로 단백질 보충
- 국물을 적게 만들어 간을 덜하게
"""
    }
]
