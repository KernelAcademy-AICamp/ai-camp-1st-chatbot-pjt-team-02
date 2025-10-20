# 콩닥식탁 챗봇 PRD (Product Requirements Document)

## 1. 프로젝트 개요

### 1.1 프로젝트명
**콩닥식탁** - 신장 투석 환자를 위한 AI 기반 맞춤형 식단 관리 챗봇

### 1.2 프로젝트 배경 및 목적
- **배경**: 신장 투석 환자들은 나트륨, 칼륨, 인, 단백질 섭취를 엄격히 제한해야 하지만, 일반 요리의 영양 성분을 파악하기 어려움
- **목적**: LLM과 RAG 기술을 활용하여 투석 환자가 안전하게 즐길 수 있는 맞춤형 레시피와 식단 가이드 제공
- **해결 과제**: 
  - 요리별 영양 성분 자동 분석
  - 위험 성분 대체 재료 추천
  - 식약처 가이드라인 기반 조리법 제공
  - 학습 강화를 위한 퀴즈 기능

### 1.3 기대 효과
- 투석 환자의 식단 관리 부담 감소
- 안전한 식사를 위한 실시간 가이드 제공
- 의료진과 환자 간 식단 관리 커뮤니케이션 개선

## 2. 기술 스택

### 2.1 백엔드
- **Framework**: FastAPI (비동기 처리, 자동 API 문서화)
- **Language**: Python 3.9+ (Conda 환경)
- **LLM Integration**: OpenAI API (GPT-3.5-turbo/GPT-4)

### 2.2 데이터베이스
- **Main DB**: PostgreSQL 15 (Docker Container)
- **Vector DB**: FAISS (RAG용 벡터 스토어)
- **Cache**: Redis (선택사항, 응답 속도 개선)

### 2.3 프론트엔드
- **Framework**: Streamlit
- **UI Components**: 
  - streamlit-chat (대화형 인터페이스)
  - plotly (영양 성분 시각화)
  - streamlit-aggrid (데이터 테이블)

### 2.4 추가 라이브러리
- **RAG System**: LangChain, OpenAI Embeddings
- **PDF Processing**: PyPDFLoader
- **Data Processing**: Pandas, NumPy
- **Web Scraping**: BeautifulSoup4, Selenium (3순위 기능)
- **Environment**: python-dotenv

## 3. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Streamlit)               │
├─────────────────────────────────────────────────────┤
│                   FastAPI Backend                    │
├─────────────┬───────────────┬───────────────────────┤
│   LLM API   │   RAG System  │   Web Scraping        │
│  (OpenAI)   │   (FAISS)     │   (BeautifulSoup)     │
├─────────────┴───────────────┴───────────────────────┤
│           PostgreSQL          │      Redis           │
│           (Docker)            │     (Cache)          │
└───────────────────────────────┴─────────────────────┘
```

## 4. 핵심 기능 명세

### 4.1 1순위 기능: 요약 및 Q&A 자동생성 [필수]

#### 4.1.1 요리 정보 분석 및 영양 성분 계산
- **입력**: "떡볶이 먹어도 될까요?" 형태의 자연어 질의
- **처리 과정**:
  1. LLM을 통한 요리명 추출 및 레시피 분석
  2. 재료별 영양 성분 DB 조회 (국가표준식품성분표)
  3. 총 영양소 계산 (나트륨, 칼륨, 인, 단백질, 칼로리)
  4. 위험도 평가 (신장 환자 기준치 대비)

#### 4.1.2 맞춤형 대체 재료 추천
- **위험 성분 감지**: 기준치 초과 영양소 식별
- **대체 재료 제안**: 
  - 고칼륨 야채 → 저칼륨 대체재
  - 고인 단백질 → 저인 단백질원
  - 실시간 영양 재계산

#### 4.1.3 RAG 기반 조리법 요약
- **PDF 학습 자료**:
  - 식약처 저염식 가이드
  - 대한신장학회 식단관리 가이드
- **출력**: 5줄 이내 핵심 조리법 및 주의사항

### 4.2 2순위 기능: 과제/시험 문제 생성 [필수]

#### 4.2.1 퀴즈 생성 시스템
- **트리거**: 답변 후 "퀴즈로 복습하시겠어요?" 제안
- **문제 유형**:
  - 객관식 (4지선다)
  - 주관식 (단답형)
  - O/X 문제
- **문제 구성**: 문제/정답/해설 포함
- **난이도 조절**: 사용자 레벨에 맞춤

#### 4.2.2 학습 효과 추적
- 사용자별 퀴즈 성과 저장
- 오답 노트 기능
- 재학습 추천

### 4.3 3순위 기능: 자료 추천 서비스 [부가]

#### 4.3.1 관련 자료 웹 크롤링
- **수집 대상**:
  - 대한영양사협회 레시피
  - 식품의약품안전처 공식 자료
  - 병원 영양팀 블로그
  - 신장 환자 커뮤니티 인기 레시피

#### 4.3.2 링크 검증 및 필터링
- **검증 프로세스**:
  1. URL 유효성 확인 (HTTP 200 체크)
  2. 콘텐츠 관련성 평가 (키워드 매칭)
  3. 신뢰도 평가 (도메인 화이트리스트)
  4. 중복 제거

#### 4.3.3 추천 결과 포맷
```json
{
  "title": "저칼륨 김치찌개 만들기",
  "description": "칼륨을 50% 줄인 특별 레시피",
  "url": "https://example.com/recipe/123",
  "source": "서울대병원 영양팀",
  "relevance_score": 0.95,
  "published_date": "2024-10-15"
}
```

## 5. 데이터베이스 스키마

### 5.1 주요 테이블 구조

```sql
-- 식품 영양 정보
CREATE TABLE foods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    sodium FLOAT,
    potassium FLOAT,
    phosphorus FLOAT,
    protein FLOAT,
    calories FLOAT,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 대체 재료 매핑
CREATE TABLE alternatives (
    id SERIAL PRIMARY KEY,
    original_food VARCHAR(255),
    alternative_food VARCHAR(255),
    nutrient_type VARCHAR(50),
    reduction_percentage FLOAT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 대화 기록
CREATE TABLE user_queries (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255),
    user_question TEXT,
    bot_answer TEXT,
    nutrition_info JSONB,
    risk_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 퀴즈 기록
CREATE TABLE quiz_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255),
    question TEXT,
    user_answer TEXT,
    correct_answer TEXT,
    is_correct BOOLEAN,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 추천 자료 캐시
CREATE TABLE recommended_resources (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255),
    resources JSONB,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 6. API 엔드포인트

### 6.1 주요 API 명세

```python
# 1. 채팅 API
POST /api/chat
Request: {
    "message": "떡볶이 먹어도 될까요?",
    "session_id": "uuid-string"
}
Response: {
    "answer": "떡볶이 분석 결과...",
    "nutrition": {...},
    "risk_level": "high",
    "alternatives": [...],
    "quiz_offer": true
}

# 2. 퀴즈 API
POST /api/quiz/generate
Request: {
    "topic": "떡볶이",
    "difficulty": "medium",
    "count": 3
}
Response: {
    "questions": [...]
}

# 3. 자료 추천 API
GET /api/resources/recommend?keyword=저염식&limit=5
Response: {
    "resources": [...],
    "total": 5
}

# 4. 영양 분석 API
POST /api/nutrition/analyze
Request: {
    "ingredients": ["떡", "고추장", "어묵"]
}
Response: {
    "total_nutrition": {...},
    "warnings": [...]
}
```

## 7. 프론트엔드 UI/UX 설계

### 7.1 주요 화면 구성

#### 7.1.1 메인 채팅 화면
```python
# Streamlit 레이아웃
- 상단: 로고 및 서비스 소개
- 좌측 사이드바: 
  - 세션 관리
  - 대화 히스토리
  - 설정 (위험도 기준치)
- 중앙: 채팅 인터페이스
  - 메시지 입력창
  - 대화 내역
  - 영양 정보 카드
  - 위험도 게이지
- 우측: 
  - 추천 자료 패널
  - 퀴즈 섹션
```

#### 7.1.2 영양 정보 시각화
- **차트 유형**:
  - 도넛 차트: 영양소별 비율
  - 바 차트: 기준치 대비 현재값
  - 신호등 표시: 위험도 (🟢안전/🟡주의/🔴위험)

#### 7.1.3 퀴즈 인터페이스
- 문제 표시 영역
- 답변 입력/선택
- 즉각적 피드백
- 점수 및 진행률 표시

### 7.2 반응형 디자인
- 모바일 대응 (최소 너비: 320px)
- 다크모드 지원
- 접근성 고려 (ARIA labels)

## 8. 구현 로드맵

### Phase 1: 기본 인프라 구축 (Day 1-2)
- [x] PostgreSQL Docker 설정
- [x] FastAPI 프로젝트 구조
- [x] 기본 데이터베이스 스키마
- [ ] 환경 설정 및 Docker Compose

### Phase 2: 핵심 기능 개발 (Day 3-4)
- [ ] LLM 연동 및 프롬프트 최적화
- [ ] RAG 시스템 구현
- [ ] 영양 정보 분석 로직
- [ ] 대체 재료 추천 알고리즘

### Phase 3: 부가 기능 개발 (Day 5)
- [ ] 퀴즈 생성 시스템
- [ ] 웹 크롤링 및 자료 추천
- [ ] 캐싱 시스템

### Phase 4: 프론트엔드 개발 (Day 6)
- [ ] Streamlit UI 구현
- [ ] 데이터 시각화
- [ ] 실시간 채팅 인터페이스

### Phase 5: 테스트 및 최적화 (Day 7)
- [ ] 통합 테스트
- [ ] 성능 최적화
- [ ] 발표 자료 준비

## 9. 프롬프트 엔지니어링 전략

### 9.1 시스템 프롬프트
```python
SYSTEM_PROMPT = """
당신은 신장 투석 환자를 위한 전문 영양 상담 AI입니다.
역할:
1. 요리의 영양 성분을 정확히 분석
2. 신장 환자 기준치와 비교하여 위험도 평가
3. 안전한 대체 재료 제안
4. 친근하고 이해하기 쉬운 설명

제한사항:
- 나트륨: 650mg/끼
- 칼륨: 650mg/끼
- 인: 330mg/끼
- 단백질: 40g/끼

답변 형식:
1. 영양 분석 결과 (이모지 활용)
2. 위험도 평가
3. 대체 레시피 제안
4. 조리 팁
"""
```

### 9.2 Few-shot 예시
```python
EXAMPLES = [
    {
        "input": "김치찌개 먹어도 될까요?",
        "output": """
        🍲 김치찌개 영양 분석
        
        ⚠️ 위험도: 높음
        - 나트륨: 1,200mg (초과 ❌)
        - 칼륨: 450mg (안전 ✅)
        
        💡 대체 레시피:
        - 김치 → 저염 김치 사용
        - 돼지고기 → 닭가슴살로 대체
        - 국물 양 줄이기
        
        👨‍🍳 조리 팁: 김치를 물에 헹구면 나트륨 30% 감소
        """
    }
]
```

## 10. 성능 최적화 전략

### 10.1 응답 시간 개선
- LLM 응답 스트리밍
- PostgreSQL 인덱싱 최적화
- Redis 캐싱 (자주 조회되는 음식)
- 배치 처리 (다중 재료 조회)

### 10.2 확장성 고려
- 비동기 처리 (FastAPI async)
- 데이터베이스 커넥션 풀링
- 로드밸런싱 준비

## 11. 보안 및 규정 준수

### 11.1 데이터 보안
- API 키 환경변수 관리
- SQL Injection 방지
- XSS 방지
- HTTPS 적용

### 11.2 개인정보보호
- 세션별 데이터 분리
- 민감 정보 암호화
- 로그 마스킹

## 12. 테스트 계획

### 12.1 단위 테스트
- 영양 계산 로직
- 데이터베이스 쿼리
- API 엔드포인트

### 12.2 통합 테스트
- End-to-end 시나리오
- 부하 테스트
- 사용자 수용 테스트

## 13. 배포 전략

### 13.1 Docker 컨테이너화
```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: kongdak_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  backend:
    build: .
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@postgres:5432/kongdak_db
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports:
      - "8000:8000"
  
  frontend:
    build: ./frontend
    depends_on:
      - backend
    ports:
      - "8501:8501"
```

### 13.2 CI/CD 파이프라인
- GitHub Actions
- 자동 테스트
- Docker Hub 푸시

## 14. 모니터링 및 로깅

### 14.1 메트릭 수집
- API 응답 시간
- 에러율
- 사용자 활동

### 14.2 로깅
- 구조화된 로깅 (JSON)
- 로그 레벨 관리
- 중앙화된 로그 수집

## 15. 발표 준비 체크리스트

### 15.1 데모 시나리오
1. 서비스 소개 (2분)
2. 실시간 채팅 데모 (3분)
   - "떡볶이 먹어도 될까요?"
   - 영양 분석 및 대체 레시피
3. 퀴즈 기능 시연 (2분)
4. 자료 추천 시연 (1분)
5. 기술 스택 설명 (2분)

### 15.2 준비 사항
- [ ] 테스트 데이터 준비
- [ ] 백업 계획 (오프라인 데모)
- [ ] 발표 슬라이드
- [ ] Q&A 예상 질문

## 16. 프로젝트 파일 구조

```
kongdak-chatbot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 메인
│   │   ├── config.py            # 설정 관리
│   │   ├── models/
│   │   │   ├── database.py      # DB 모델
│   │   │   └── schemas.py       # Pydantic 스키마
│   │   ├── services/
│   │   │   ├── llm_service.py   # LLM 연동
│   │   │   ├── rag_service.py   # RAG 시스템
│   │   │   ├── nutrition.py     # 영양 분석
│   │   │   └── scraper.py       # 웹 크롤링
│   │   ├── routers/
│   │   │   ├── chat.py          # 채팅 API
│   │   │   ├── quiz.py          # 퀴즈 API
│   │   │   └── resources.py     # 자료 추천 API
│   │   └── utils/
│   │       └── prompts.py       # 프롬프트 관리
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                   # Streamlit 메인
│   ├── pages/
│   │   ├── chat.py
│   │   ├── quiz.py
│   │   └── resources.py
│   ├── components/
│   │   ├── nutrition_chart.py
│   │   └── message_box.py
│   ├── requirements.txt
│   └── Dockerfile
├── data/
│   ├── pdfs/                    # 학습용 PDF
│   ├── nutrition_data.xlsx      # 영양 데이터
│   └── init.sql                 # DB 초기화
├── docker-compose.yml
├── .env.example
├── README.md
└── .gitignore
```

## 17. 주요 구현 코드 예시

### 17.1 웹 크롤링 서비스 (3순위 기능)
```python
# services/scraper.py
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict
import hashlib

class ResourceScraper:
    def __init__(self):
        self.trusted_domains = [
            "mfds.go.kr",           # 식약처
            "ksn.or.kr",            # 대한신장학회
            "dietitian.or.kr",      # 대한영양사협회
            "health.kr"             # 건강정보
        ]
        
    async def search_resources(self, keyword: str, limit: int = 5) -> List[Dict]:
        """관련 자료 검색 및 수집"""
        results = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for domain in self.trusted_domains:
                tasks.append(self.scrape_site(session, domain, keyword))
            
            site_results = await asyncio.gather(*tasks)
            
            # 결과 통합 및 정렬
            for site_result in site_results:
                results.extend(site_result)
            
            # 관련성 점수로 정렬
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # 중복 제거
            seen_urls = set()
            unique_results = []
            for item in results:
                url_hash = hashlib.md5(item['url'].encode()).hexdigest()
                if url_hash not in seen_urls:
                    seen_urls.add(url_hash)
                    unique_results.append(item)
            
            return unique_results[:limit]
    
    async def scrape_site(self, session, domain: str, keyword: str) -> List[Dict]:
        """특정 사이트 크롤링"""
        try:
            search_url = f"https://{domain}/search?q={keyword}"
            async with session.get(search_url, timeout=5) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    # 사이트별 파싱 로직
                    articles = soup.find_all('article', limit=3)
                    
                    for article in articles:
                        title = article.find('h3')
                        link = article.find('a')
                        description = article.find('p')
                        
                        if title and link:
                            results.append({
                                'title': title.text.strip(),
                                'url': f"https://{domain}{link.get('href')}",
                                'description': description.text.strip() if description else '',
                                'source': domain,
                                'relevance_score': self.calculate_relevance(
                                    title.text, description.text if description else '', keyword
                                )
                            })
                    
                    return results
        except Exception as e:
            print(f"Error scraping {domain}: {e}")
            return []
    
    def calculate_relevance(self, title: str, description: str, keyword: str) -> float:
        """관련성 점수 계산"""
        score = 0.0
        keyword_lower = keyword.lower()
        
        # 제목에 키워드 포함
        if keyword_lower in title.lower():
            score += 0.5
        
        # 설명에 키워드 포함
        if keyword_lower in description.lower():
            score += 0.3
        
        # 추가 관련 키워드
        related_keywords = ['신장', '투석', '저염', '저칼륨', '식단']
        for related in related_keywords:
            if related in title.lower() or related in description.lower():
                score += 0.1
        
        return min(score, 1.0)
```

### 17.2 Streamlit 프론트엔드 메인
```python
# frontend/app.py
import streamlit as st
import requests
import plotly.express as px
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="콩닥식탁 - 신장 환자 맞춤 식단 챗봇",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .risk-high { background-color: #ff4b4b; color: white; padding: 10px; border-radius: 5px; }
    .risk-medium { background-color: #ffa500; color: white; padding: 10px; border-radius: 5px; }
    .risk-low { background-color: #4caf50; color: white; padding: 10px; border-radius: 5px; }
    .nutrition-card { 
        border: 2px solid #e0e0e0; 
        border-radius: 10px; 
        padding: 15px; 
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(datetime.now().timestamp())

# 사이드바
with st.sidebar:
    st.title("⚙️ 설정")
    
    # 위험도 기준치 설정
    st.subheader("🎯 영양소 제한 기준")
    sodium_limit = st.slider("나트륨 (mg/끼)", 300, 1000, 650)
    potassium_limit = st.slider("칼륨 (mg/끼)", 300, 1000, 650)
    phosphorus_limit = st.slider("인 (mg/끼)", 200, 500, 330)
    protein_limit = st.slider("단백질 (g/끼)", 20, 60, 40)
    
    st.divider()
    
    # 대화 기록
    st.subheader("💬 대화 기록")
    if st.button("대화 내역 초기화"):
        st.session_state.messages = []
        st.rerun()
    
    # 최근 검색어
    st.subheader("🔍 최근 검색")
    recent_searches = ["떡볶이", "김치찌개", "삼겹살", "라면"]
    for search in recent_searches:
        if st.button(f"📍 {search}", key=f"recent_{search}"):
            st.session_state.messages.append({
                "role": "user",
                "content": f"{search} 먹어도 될까요?"
            })

# 메인 화면
st.title("🥗 콩닥식탁")
st.markdown("### 신장 투석 환자를 위한 맞춤형 식단 관리 챗봇")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["💬 채팅", "📊 영양 분석", "📚 추천 자료"])

with tab1:
    # 채팅 히스토리 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # 영양 정보가 있으면 표시
            if "nutrition" in message:
                nutrition_data = message["nutrition"]
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("나트륨", f"{nutrition_data.get('sodium', 0)}mg", 
                             f"{nutrition_data.get('sodium', 0) - sodium_limit}mg")
                with col2:
                    st.metric("칼륨", f"{nutrition_data.get('potassium', 0)}mg",
                             f"{nutrition_data.get('potassium', 0) - potassium_limit}mg")
                with col3:
                    st.metric("인", f"{nutrition_data.get('phosphorus', 0)}mg",
                             f"{nutrition_data.get('phosphorus', 0) - phosphorus_limit}mg")
                with col4:
                    st.metric("단백질", f"{nutrition_data.get('protein', 0)}g",
                             f"{nutrition_data.get('protein', 0) - protein_limit}g")
    
    # 사용자 입력
    if prompt := st.chat_input("요리에 대해 물어보세요... (예: 떡볶이 먹어도 될까요?)"):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # API 호출
        with st.chat_message("assistant"):
            with st.spinner("분석 중..."):
                try:
                    response = requests.post(
                        "http://localhost:8000/api/chat",
                        json={
                            "message": prompt,
                            "session_id": st.session_state.session_id,
                            "limits": {
                                "sodium": sodium_limit,
                                "potassium": potassium_limit,
                                "phosphorus": phosphorus_limit,
                                "protein": protein_limit
                            }
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # 응답 표시
                        st.markdown(result["answer"])
                        
                        # 위험도 표시
                        risk_level = result.get("risk_level", "unknown")
                        risk_class = f"risk-{risk_level}"
                        risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(risk_level, "⚪")
                        
                        st.markdown(f'<div class="{risk_class}">{risk_emoji} 위험도: {risk_level.upper()}</div>', 
                                  unsafe_allow_html=True)
                        
                        # 응답 저장
                        message_data = {
                            "role": "assistant",
                            "content": result["answer"],
                            "nutrition": result.get("nutrition", {}),
                            "risk_level": risk_level
                        }
                        st.session_state.messages.append(message_data)
                        
                        # 퀴즈 제안
                        if result.get("quiz_offer"):
                            if st.button("📝 퀴즈로 복습하기"):
                                st.session_state.show_quiz = True
                                st.rerun()
                    else:
                        st.error("서버 오류가 발생했습니다.")
                        
                except Exception as e:
                    st.error(f"연결 오류: {str(e)}")

with tab2:
    st.subheader("📊 영양 성분 시각화")
    
    if st.session_state.messages:
        # 마지막 분석 결과 가져오기
        last_nutrition = None
        for msg in reversed(st.session_state.messages):
            if msg.get("role") == "assistant" and "nutrition" in msg:
                last_nutrition = msg["nutrition"]
                break
        
        if last_nutrition:
            # 도넛 차트
            fig = px.pie(
                values=list(last_nutrition.values())[:4],
                names=["나트륨", "칼륨", "인", "단백질"],
                hole=0.4,
                title="영양소 구성 비율"
            )
            st.plotly_chart(fig)
            
            # 바 차트 - 기준치 대비
            comparison_data = {
                "영양소": ["나트륨", "칼륨", "인", "단백질"],
                "현재값": [
                    last_nutrition.get('sodium', 0),
                    last_nutrition.get('potassium', 0),
                    last_nutrition.get('phosphorus', 0),
                    last_nutrition.get('protein', 0)
                ],
                "기준치": [sodium_limit, potassium_limit, phosphorus_limit, protein_limit]
            }
            
            fig2 = px.bar(
                comparison_data,
                x="영양소",
                y=["현재값", "기준치"],
                barmode='group',
                title="기준치 대비 영양소 함량"
            )
            st.plotly_chart(fig2)
    else:
        st.info("아직 분석한 음식이 없습니다. 채팅 탭에서 음식을 검색해주세요.")

with tab3:
    st.subheader("📚 추천 학습 자료")
    
    search_keyword = st.text_input("검색어를 입력하세요", "저염식 레시피")
    
    if st.button("🔍 자료 검색"):
        with st.spinner("자료를 검색 중..."):
            try:
                response = requests.get(
                    f"http://localhost:8000/api/resources/recommend",
                    params={"keyword": search_keyword, "limit": 5}
                )
                
                if response.status_code == 200:
                    resources = response.json()["resources"]
                    
                    for resource in resources:
                        with st.container():
                            st.markdown(f"### [{resource['title']}]({resource['url']})")
                            st.markdown(f"**출처**: {resource['source']}")
                            st.markdown(f"**설명**: {resource['description']}")
                            st.markdown(f"**관련성**: {'⭐' * int(resource['relevance_score'] * 5)}")
                            st.divider()
                else:
                    st.error("자료 검색에 실패했습니다.")
                    
            except Exception as e:
                st.error(f"검색 오류: {str(e)}")

# 퀴즈 모달 (세션 상태 체크)
if st.session_state.get('show_quiz', False):
    with st.container():
        st.subheader("📝 복습 퀴즈")
        # 퀴즈 로직 구현
        st.session_state.show_quiz = False
```

## 18. 마무리 체크리스트

- [ ] 모든 필수 기능 구현 완료
- [ ] API 문서화 (FastAPI 자동 생성)
- [ ] 에러 처리 및 로깅
- [ ] 성능 테스트
- [ ] 보안 점검
- [ ] 배포 준비
- [ ] 발표 자료 및 시연 준비

---
