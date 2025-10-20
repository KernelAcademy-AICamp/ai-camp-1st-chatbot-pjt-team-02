# 콩닥식탁 챗봇 구현 Task List

## 📋 프로젝트 개요
신장 투석 환자를 위한 AI 기반 맞춤형 식단 관리 챗봇 구현

## 🎯 Task 분류 및 우선순위

### Phase 1: 인프라 설정 (필수 선행 작업)

#### Task 1: 프로젝트 구조 생성
- **설명**: 백엔드, 프론트엔드, 데이터베이스, Docker 폴더 구조 생성
- **의존성**: 없음
- **출력**:
  - `backend/`, `frontend/`, `database/`, `docker/`, `data/` 폴더 생성
  - 각 폴더별 `__init__.py` 및 기본 파일 생성

#### Task 2: 환경 설정 파일
- **설명**: .env.example, .gitignore 생성
- **의존성**: Task 1
- **출력**:
  - `.env.example` (OpenAI API Key, DB 설정 템플릿)
  - `.gitignore` (Python, Docker, IDE 설정)

#### Task 3: Docker 설정
- **설명**: docker-compose.yml 및 Dockerfile 작성
- **의존성**: Task 1
- **출력**:
  - `docker-compose.yml` (PostgreSQL, Backend, Frontend 서비스)
  - `backend/Dockerfile`
  - `frontend/Dockerfile`

#### Task 4: 데이터베이스 스키마
- **설명**: PostgreSQL 초기화 SQL 스크립트
- **의존성**: Task 1
- **출력**: `database/init.sql` (foods, alternatives, user_queries, quiz_history, recommended_resources 테이블)

---

### Phase 2: 백엔드 핵심 기능 (순차 실행)

#### Task 5: 백엔드 기본 구조
- **설명**: FastAPI 프로젝트 설정 및 기본 config
- **의존성**: Task 1, 2
- **출력**:
  - `backend/app/main.py` (FastAPI 앱 초기화)
  - `backend/app/config.py` (환경 변수 로드)
  - `backend/requirements.txt`

#### Task 6: 데이터베이스 모델
- **설명**: SQLAlchemy 모델 및 Pydantic 스키마
- **의존성**: Task 5
- **출력**:
  - `backend/app/models/database.py` (ORM 모델)
  - `backend/app/models/schemas.py` (Request/Response 스키마)

#### Task 7: LLM 서비스
- **설명**: OpenAI API 연동 및 프롬프트 관리
- **의존성**: Task 5
- **출력**:
  - `backend/app/services/llm_service.py` (LLM 호출 로직)
  - `backend/app/utils/prompts.py` (시스템 프롬프트 및 Few-shot 예시)

#### Task 8: 영양 분석 서비스
- **설명**: 재료 분석 및 영양소 계산 로직
- **의존성**: Task 6, 7
- **출력**:
  - `backend/app/services/nutrition.py` (영양소 계산, 위험도 평가)

#### Task 9: RAG 시스템
- **설명**: FAISS 벡터 스토어 및 PDF 임베딩
- **의존성**: Task 5, 7
- **출력**:
  - `backend/app/services/rag_service.py` (PDF 로드, 벡터 검색)

#### Task 10: 채팅 API 라우터
- **설명**: POST /api/chat 엔드포인트
- **의존성**: Task 7, 8, 9
- **출력**: `backend/app/routers/chat.py`
- **기능**: 질문 → 재료 분석 → 영양 계산 → RAG 검색 → 최종 답변

#### Task 11: 영양 분석 API
- **설명**: POST /api/nutrition/analyze
- **의존성**: Task 8
- **출력**: `backend/app/routers/nutrition.py`
- **기능**: 재료 리스트 입력 → 총 영양소 계산

#### Task 12: 퀴즈 생성 API
- **설명**: POST /api/quiz/generate
- **의존성**: Task 7
- **출력**: `backend/app/routers/quiz.py`
- **기능**: 주제/난이도 입력 → 객관식/주관식/OX 퀴즈 생성

#### Task 13: 자료 추천 API
- **설명**: GET /api/resources/recommend (웹 크롤링)
- **의존성**: Task 5
- **출력**: `backend/app/routers/resources.py`, `backend/app/services/scraper.py`
- **기능**: 키워드 검색 → 웹 크롤링 → 관련성 평가 → 추천 결과

---

### Phase 3: 프론트엔드 (백엔드 완료 후)

#### Task 14: Streamlit 기본 구조
- **설명**: 페이지 설정 및 세션 관리
- **의존성**: Task 1
- **출력**:
  - `frontend/app.py` (메인 앱)
  - `frontend/requirements.txt`

#### Task 15: 채팅 인터페이스
- **설명**: 메인 채팅 탭 구현
- **의존성**: Task 10, 14
- **출력**: `frontend/pages/chat.py` (채팅 UI, 메시지 표시, API 호출)

#### Task 16: 영양 분석 시각화
- **설명**: Plotly 차트 (도넛, 바 차트)
- **의존성**: Task 15
- **출력**: `frontend/components/nutrition_chart.py` (영양소 비율, 기준치 대비 차트)

#### Task 17: 퀴즈 인터페이스
- **설명**: 퀴즈 생성 및 결과 표시
- **의존성**: Task 12, 14
- **출력**: `frontend/pages/quiz.py` (문제 표시, 답변 입력, 피드백)

#### Task 18: 자료 추천 UI
- **설명**: 검색 및 추천 결과 표시
- **의존성**: Task 13, 14
- **출력**: `frontend/pages/resources.py` (검색창, 결과 카드)

---

### Phase 4: 데이터 및 통합 테스트

#### Task 19: 샘플 데이터 준비
- **설명**: 영양 정보 DB 초기 데이터
- **의존성**: Task 4
- **출력**: `database/sample_foods.sql` (떡, 고추장, 어묵 등 기본 식품 영양 정보)

#### Task 20: RAG PDF 임베딩
- **설명**: 식약처/대한신장학회 PDF 처리
- **의존성**: Task 9
- **출력**: `data/faiss_index/` (FAISS 벡터 인덱스)
- **처리 파일**:
  - Documents/Data/식약처(교육자료)_나트륨줄이기자료집.pdf
  - Documents/Data/대한신장학회(출판자료)_혈액투석_질환식_식단_레시피_가이드.pdf

#### Task 21: 통합 테스트
- **설명**: 전체 워크플로우 E2E 테스트
- **의존성**: Task 10-18
- **출력**: `backend/tests/test_integration.py`
- **테스트 시나리오**:
  1. "떡볶이 먹어도 될까요?" → 영양 분석 → 대체 레시피
  2. 퀴즈 생성 → 답변 제출 → 피드백
  3. 자료 추천 검색

#### Task 22: 시연 준비
- **설명**: 데모 시나리오 및 실행 스크립트
- **의존성**: Task 21
- **출력**:
  - `DEMO.md` (시연 시나리오 가이드)
  - `start.sh` (Docker Compose 실행 스크립트)

---

## 🔄 의존성 그래프

```
Task 1 (프로젝트 구조)
  ├─→ Task 2 (환경 설정)
  ├─→ Task 3 (Docker 설정)
  ├─→ Task 4 (DB 스키마)
  └─→ Task 5 (백엔드 기본 구조)
        ├─→ Task 6 (DB 모델)
        ├─→ Task 7 (LLM 서비스)
        │     ├─→ Task 9 (RAG 시스템)
        │     ├─→ Task 12 (퀴즈 API)
        │     └─→ Task 8 (영양 분석)
        │           └─→ Task 11 (영양 분석 API)
        ├─→ Task 10 (채팅 API) ← Task 7, 8, 9
        └─→ Task 13 (자료 추천 API)

Task 14 (Streamlit 기본)
  ├─→ Task 15 (채팅 UI) ← Task 10
  │     └─→ Task 16 (영양 시각화)
  ├─→ Task 17 (퀴즈 UI) ← Task 12
  └─→ Task 18 (자료 추천 UI) ← Task 13

Task 19 (샘플 데이터) ← Task 4
Task 20 (PDF 임베딩) ← Task 9
Task 21 (통합 테스트) ← Task 10-18
Task 22 (시연 준비) ← Task 21
```

---

## ⚠️ 사용자 개입 필요 항목

### 필수 설정 (Task 실행 전 알림 예정)
1. **OpenAI API Key**
   - Task 7 실행 전 알림
   - `.env` 파일에 `OPENAI_API_KEY=your-key-here` 설정 필요

2. **PostgreSQL 비밀번호**
   - Task 3 실행 전 알림
   - `.env` 파일에 `DB_PASSWORD=your-password` 설정 필요

3. **Docker 실행 확인**
   - Task 3 완료 후 알림
   - `docker-compose up -d` 실행 필요

### 선택 사항
- Redis 캐시 설정 (성능 향상, 현재 미구현)
- 영양 데이터 엑셀 파일 (샘플 데이터로 대체 가능)

---

## 📊 예상 소요 시간

- **Phase 1** (Task 1-4): 30분
- **Phase 2** (Task 5-13): 2-3시간
- **Phase 3** (Task 14-18): 1-2시간
- **Phase 4** (Task 19-22): 1시간
- **총 예상 시간**: 4-6시간

---

## 🚀 실행 명령어

### 개발 환경 설정
```bash
# 1. .env 파일 생성
cp .env.example .env
# OPENAI_API_KEY와 DB_PASSWORD 입력

# 2. Docker Compose 실행
docker-compose up -d

# 3. 백엔드 서버 확인
curl http://localhost:8000/docs

# 4. ��론트엔드 실행
streamlit run frontend/app.py
```

### 시연 실행
```bash
# 통합 실행 스크립트
./start.sh
```

---

## ✅ 완료 체크리스트

### Phase 1: 인프라
- [ ] Task 1: 프로젝트 구조 생성
- [ ] Task 2: 환경 설정 파일
- [ ] Task 3: Docker 설정
- [ ] Task 4: 데이터베이스 스키마

### Phase 2: 백엔드
- [ ] Task 5: 백엔드 기본 구조
- [ ] Task 6: 데이터베이스 모델
- [ ] Task 7: LLM 서비스
- [ ] Task 8: 영양 분석 서비스
- [ ] Task 9: RAG 시스템
- [ ] Task 10: 채팅 API 라우터
- [ ] Task 11: 영양 분석 API
- [ ] Task 12: 퀴즈 생성 API
- [ ] Task 13: 자료 추천 API

### Phase 3: 프론트엔드
- [ ] Task 14: Streamlit 기본 구조
- [ ] Task 15: 채팅 인터페이스
- [ ] Task 16: 영양 분석 시각화
- [ ] Task 17: 퀴즈 인터페이스
- [ ] Task 18: 자료 추천 UI

### Phase 4: 통합
- [ ] Task 19: 샘플 데이터 준비
- [ ] Task 20: RAG PDF 임베딩
- [ ] Task 21: 통합 테스트
- [ ] Task 22: 시연 준비

---

## 📝 참고 사항

1. **컨텍스트 토큰 관리**: 각 Task는 독립적으로 실행 가능하도록 설계
2. **버그 방지**: 의존성 순서를 엄격히 준수
3. **시연 가능**: Task 22 완료 시 전체 시스템 시연 가능
4. **폴더 분리**: 백엔드, 프론트엔드, DB, Docker 각각 독립 폴더
