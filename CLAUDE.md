# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**콩닥식탁** - 신장 투석 환자를 위한 AI 기반 맞춤형 식단 관리 챗봇

이 프로젝트는 OpenAI GPT API와 RAG(Retrieval-Augmented Generation) 기술을 활용하여 신장 투석 환자가 안전하게 즐길 수 있는 맞춤형 레시피와 식단 가이드를 제공합니다.

## 기술 스택

### 백엔드
- **Framework**: FastAPI (비동기 처리)
- **Language**: Python 3.9+ (Conda 환경)
- **LLM**: OpenAI API (GPT-3.5-turbo/GPT-4)
- **Database**: PostgreSQL 15 (Docker Container)
- **Vector DB**: FAISS (RAG 시스템)

### 프론트엔드
- **Framework**: Streamlit
- **UI Components**: streamlit-chat, plotly, streamlit-aggrid

### 주요 라이브러리
- **RAG System**: LangChain, OpenAI Embeddings
- **PDF Processing**: PyPDFLoader
- **Data Processing**: Pandas, NumPy
- **Web Scraping**: BeautifulSoup4, Selenium
- **Environment**: python-dotenv

## 시스템 아키텍처

### 3-Tier 아키텍처
```
Frontend (Streamlit) ↔ Backend (FastAPI) ↔ LLM API (OpenAI)
                              ↓
                    PostgreSQL + FAISS
```

### 데이터 흐름
1. 사용자가 Streamlit UI에서 "떡볶이 먹어도 될까요?" 같은 질문 입력
2. FastAPI 백엔드가 LLM을 통해 레시피 재료 분석
3. PostgreSQL에서 재료별 영양 성분 조회 및 계산
4. 위험도 평가 후 RAG 시스템(FAISS)에서 대체 재료/조리법 검색
5. LLM이 최종 답변 생성 (영양 분석 + 대체 레시피 + 조리 팁)
6. Streamlit UI에 결과 시각화 (차트, 위험도 표시)

## 핵심 기능

### 1순위: 요약 및 Q&A 자동생성 [필수]
- 요리 정보 분석 및 영양 성분 계산
- 맞춤형 대체 재료 추천 (고칼륨 → 저칼륨)
- RAG 기반 조리법 요약 (식약처/대한신장학회 PDF 학습)

### 2순위: 과제/시험 문제 생성 [필수]
- 퀴즈 생성 시스템 (객관식, 주관식, O/X)
- 학습 효과 추적 및 오답 노트

### 3순위: 자료 추천 서비스 [부가]
- 웹 크롤링 기반 관련 자료 수집
- 신뢰도 검증 및 관련성 평가

## 데이터 초기화 (중요!)

**⚠️ 이 프로젝트는 국가표준식품성분표 엑셀 파일에서 데이터를 읽어 DB에 로드합니다.**

### 빠른 시작
```bash
# 1. 데이터 초기화 (최초 1회 필수)
cd scripts
./initialize_data.sh

# 위 스크립트가 다음을 자동 실행:
# - 국가표준식품성분표 → PostgreSQL 로드
# - alternatives.xlsx → PostgreSQL 로드 (있는 경우)
# - PDF 문서 → FAISS 로드 (있는 경우)
```

### 필수 데이터 파일
- `Documents/Data/국가표준식품성분표_250426공개.xlsx` - **필수** (1000+ 식품 영양 정보)
- `Documents/Data/alternatives.xlsx` - 선택 (대체 재료 매핑, 직접 작성)
- `Documents/Data/*.pdf` - 선택 (RAG용 참고 문서)

### 수동 실행
```bash
python3 scripts/load_excel_to_db.py         # 국가표준식품성분표 + alternatives → DB
python3 scripts/load_pdfs_to_faiss.py       # PDF → FAISS (선택)
```

**참고**:
- `database/init.sql`은 테이블 스키마만 정의
- 실제 데이터는 국가표준식품성분표에서 자동 로드
- 컬럼 매핑은 스크립트가 자동 처리

자세한 내용: [DATA_INITIALIZATION.md](Documents/Data생성설명/DATA_INITIALIZATION.md)

## 데이터베이스 스키마

### 주요 테이블
- **foods**: 식품 영양 정보 (나트륨, 칼륨, 인, 단백질, 칼로리)
- **alternatives**: 대체 재료 매핑
- **user_queries**: 사용자 대화 기록 (JSONB로 영양 정보 저장)
- **quiz_history**: 퀴즈 기록 및 정답률 추적
- **recommended_resources**: 추천 자료 캐시

### 성능 최적화
- `foods.name`에 인덱스 생성
- 다중 재료 검색 시 `IN` 절 사용
- 배치 INSERT로 성능 향상 (psycopg2.extras.execute_batch)

## 프로젝트 구조

```
ChatBot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 메인
│   │   ├── config.py            # 환경 설정
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
│   │   │   ├── nutrition.py     # 영양 검색 API
│   │   │   └── resources.py     # 자료 추천 API
│   │   └── utils/
│   │       └── prompts.py       # 프롬프트 관리
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                   # Streamlit 메인
│   ├── requirements.txt
│   └── Dockerfile
├── database/
│   └── init.sql                 # DB 스키마 (데이터는 엑셀에서 로드)
├── scripts/                     # ⭐ 데이터 로딩 스크립트
│   ├── load_excel_to_db.py      # 국가표준식품성분표 → PostgreSQL
│   ├── load_pdfs_to_faiss.py    # PDF → FAISS
│   ├── initialize_data.sh       # 통합 실행
│   └── requirements.txt
├── Documents/
│   ├── Data/                    # ⭐ 데이터 파일
│   │   ├── 국가표준식품성분표_250426공개.xlsx  # 식품 영양 정보 (필수)
│   │   ├── alternatives.xlsx    # 대체 재료 매핑 (선택)
│   │   └── *.pdf                # RAG용 참고 문서 (선택)
│   ├── kongdak_prd.md           # 상세 PRD
│   └── kongdak-참조소스.py      # 참조 구현 코드
├── docker-compose.yml           # Docker 오케스트레이션
├── .env.example                 # 환경 변수 템플릿
├── DATA_INITIALIZATION.md       # 데이터 초기화 가이드
└── README.md
```

## 개발 환경 설정

### 필수 환경변수 (.env)
```bash
# OpenAI
OPENAI_API_KEY=your-openai-api-key

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kongdak_db
DB_USER=postgres
DB_PASSWORD=your-password
```

### Docker로 PostgreSQL 실행
```bash
docker run -d \
  --name kongdak_postgres \
  -e POSTGRES_DB=kongdak_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your-password \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15
```

### Streamlit 실행
```bash
streamlit run frontend/app.py
```

### FastAPI 실행
```bash
uvicorn backend.app.main:app --reload --port 8000
```

## 영양소 제한 기준

신장 투석 환자 기준치 (1끼 기준):
- **나트륨**: 650mg
- **칼륨**: 650mg
- **인**: 330mg
- **단백질**: 40g

## 프롬프트 엔지니어링 전략

### 시스템 프롬프트
```python
SYSTEM_PROMPT = """
당신은 신장 투석 환자를 위한 전문 영양 상담 AI입니다.
역할:
1. 요리의 영양 성분을 정확히 분석
2. 신장 환자 기준치와 비교하여 위험도 평가
3. 안전한 대체 재료 제안
4. 친근하고 이해하기 쉬운 설명

답변 형식:
1. 영양 분석 결과 (이모지 활용)
2. 위험도 평가 (🟢안전/🟡주의/🔴위험)
3. 대체 레시피 제안
4. 조리 팁
"""
```

### Few-shot 학습 예시
답변 일관성을 위해 `utils/prompts.py`에 예시 Q&A 저장

## API 엔드포인트

### 채팅 API
```python
POST /api/chat
Request: {
    "message": "떡볶이 먹어도 될까요?",
    "session_id": "uuid",
    "limits": {...}  # 영양소 제한치
}
Response: {
    "answer": "...",
    "nutrition": {...},
    "risk_level": "high|medium|low",
    "alternatives": [...],
    "quiz_offer": true
}
```

### 퀴즈 API
```python
POST /api/quiz/generate
Request: {
    "topic": "떡볶이",
    "difficulty": "medium",
    "count": 3
}
```

### 자료 추천 API
```python
GET /api/resources/recommend?keyword=저염식&limit=5
```

### 영양 분석 API
```python
POST /api/nutrition/analyze
Request: {
    "ingredients": ["떡", "고추장", "어묵"]
}
```

## 학습 데이터 위치

### PDF 문서 (Documents/Data/)
- 2권_혈액투석_환자를_위한_영양-식생활_관리.pdf
- 대한신장학회(출판자료)_혈액투석_질환식_식단_레시피_가이드.pdf
- 식약처(교육자료)_나트륨줄이기자료집.pdf
- 식약처(교육자료)_삼삼한밥상7_(내지).pdf
- 식약처(교육자료)_우리몸을살리는저염식메뉴레시피1.pdf
- 신장질환 식품교환표-식사요법.pdf

### RAG 시스템 초기화
```python
# 최초 1회만 실행
chatbot.rag_system.load_pdfs([
    "Documents/Data/식약처(교육자료)_나트륨줄이기자료집.pdf",
    "Documents/Data/대한신장학회(출판자료)_혈액투석_질환식_식단_레시피_가이드.pdf"
    # ... 나머지 PDF
])
```

### 영양 데이터 로드
```python
# 국가표준식품성분표.xlsx에서 데이터 로드
chatbot.nutrition_db.load_from_excel("nutrition_data.xlsx")
```

## 워크플로우 구현 순서

### Phase 1: 기본 인프라 (Day 1-2)
1. PostgreSQL Docker 설정
2. FastAPI 프로젝트 구조
3. 기본 데이터베이스 스키마
4. 환경 설정 및 Docker Compose

### Phase 2: 핵심 기능 (Day 3-4)
1. LLM 연동 및 프롬프트 최적화
2. RAG 시스템 구현 (FAISS)
3. 영양 정보 분석 로직
4. 대체 재료 추천 알고리즘

### Phase 3: 부가 기능 (Day 5)
1. 퀴즈 생성 시스템
2. 웹 크롤링 및 자료 추천
3. Redis 캐싱 시스템

### Phase 4: 프론트엔드 (Day 6)
1. Streamlit UI 구현
2. Plotly 데이터 시각화
3. 실시간 채팅 인터페이스

### Phase 5: 테스트 및 최적화 (Day 7)
1. 통합 테스트
2. 성능 최적화
3. 발표 자료 준비

## 참조 구현 코드

`kongdak-참조소스.py` 파일에 전체 워크플로우 구현 예시가 포함되어 있습니다:
- NutritionDB 클래스: PostgreSQL 연동
- RAGSystem 클래스: FAISS 벡터 스토어
- KongdakChatbot 클래스: 전체 파이프라인

## 보안 고려사항

- API 키는 반드시 `.env` 파일에서 관리
- `.env` 파일은 `.gitignore`에 추가
- SQL Injection 방지 (parameterized query 사용)
- XSS 방지 (Streamlit 기본 제공)

## 성능 최적화

### 응답 시간 개선
- LLM 응답 스트리밍 (FastAPI StreamingResponse)
- PostgreSQL 인덱싱 (`CREATE INDEX idx_foods_name ON foods(name)`)
- Redis 캐싱 (자주 조회되는 음식)
- 배치 처리 (`executemany` 사용)

### 확장성
- FastAPI async/await 활용
- 데이터베이스 커넥션 풀링
- 로드밸런싱 준비

## 웹 크롤링 (3순위 기능)

### 신뢰할 수 있는 도메인
- mfds.go.kr (식약처)
- ksn.or.kr (대한신장학회)
- dietitian.or.kr (대한영양사협회)

### 크롤링 프로세스
1. 비동기 HTTP 요청 (aiohttp)
2. BeautifulSoup로 파싱
3. 관련성 점수 계산 (키워드 매칭)
4. URL 중복 제거 (MD5 해시)
5. 관련성 순으로 정렬

## 테스트 시나리오

### 사용자 시나리오 예시
1. "떡볶이 먹어도 될까요?" 입력
2. 영양 분석 결과 확인 (나트륨 초과 경고)
3. 대체 레시피 확인 (저염 떡볶이)
4. 퀴즈 풀기 버튼 클릭
5. 관련 자료 추천 확인

### API 테스트
```bash
# 채팅 테스트
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "떡볶이 먹어도 될까요?", "session_id": "test-123"}'

# 퀴즈 생성 테스트
curl -X POST http://localhost:8000/api/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "저염식", "difficulty": "easy", "count": 3}'
```

## 문제 해결

### PostgreSQL 연결 실패
```bash
# Docker 컨테이너 상태 확인
docker ps | grep postgres

# 로그 확인
docker logs kongdak_postgres
```

### FAISS 인덱스 로드 실패
```python
# 인덱스 재생성
chatbot.rag_system.load_pdfs([...])
```

### LLM API 오류
- API 키 확인: `.env` 파일의 `OPENAI_API_KEY`
- Rate Limit 확인: 요청 횟수 제한 초과 여부
- Timeout 설정: 긴 응답 시 timeout 증가

## 프로젝트 팀 정보

- **프로젝트 기간**: 2025.10.16 ~ 2025.10.22 (1주일)
- **협업 도구**: GitHub, Notion, Slack
- **배포 환경**: Local 환경 (Docker 컨테이너)

## 추가 참고 자료

- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Streamlit 공식 문서](https://docs.streamlit.io/)
- [LangChain 문서](https://python.langchain.com/)
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
