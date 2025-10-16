# 🏥 콩닥 식탁 프로젝트 Task 체크리스트

> **작업 방식**: 각 task를 순서대로 진행하며, 완료된 항목은 `[ ]`를 `[x]`로 변경합니다.
>
> **우선순위 표시**:
>
> - 🔴 **블로킹 작업** - 반드시 순서대로 진행 필요
> - 🟢 **병렬 가능** - 다른 작업과 동시 진행 가능
> - ⚠️ **설치 필요** - 사전 설치/설정 작업 필요

---

## 📦 Phase 0: 환경 설정 및 필수 설치

### ⚠️ Docker 설치 및 설정

- [ ] 0.1 Docker Desktop 설치 확인

  - macOS: `brew install --cask docker` 또는 [Docker 공식 사이트](https://www.docker.com/products/docker-desktop)
  - 설치 후: `docker --version` 및 `docker-compose --version` 확인
- [ ] 0.2 Docker Compose 파일 생성

  - `docker-compose.yml` 작성 (PostgreSQL, MongoDB, Redis)
- [ ] 0.3 Docker 컨테이너 실행 및 확인

  - `docker-compose up -d`
  - `docker ps` 로 컨테이너 상태 확인

### ⚠️ 외부 서비스 API 키 발급

- [ ] 0.4 OpenAI API 키 발급

  - [OpenAI Platform](https://platform.openai.com/api-keys)에서 발급
  - `.env` 파일에 `OPENAI_API_KEY=` 추가
- [ ] 0.5 식약처 공공데이터 API 키 발급 (옵션)

  - [식약처 공공데이터포털](https://www.foodsafetykorea.go.kr/api/)
  - `.env` 파일에 `MFDS_API_KEY=` 추가

### 🟢 Git 설정

- [ ] 0.6 .gitignore 파일 설정 확인
- [ ] 0.7 초기 커밋 생성
  - `git add .`
  - `git commit -m "chore: 프로젝트 초기 설정"`

---

## 🗄️ Phase 1: DATA_PREMAKE - 데이터베이스 구축

### 🔴 1.1 기초 환경 설정 (시작점)

- [ ] 1.1.1 데이터 전처리용 Python 가상환경 생성

  ```bash
  python3 -m venv venv_data
  source venv_data/bin/activate
  ```
- [ ] 1.1.2 필수 라이브러리 설치

  ```bash
  pip install pandas numpy psycopg2-binary pymongo python-dotenv openpyxl sqlalchemy
  ```
- [ ] 1.1.3 데이터 디렉토리 구조 생성

  ```bash
  mkdir -p data/{raw,processed,embeddings}
  ```
- [ ] 1.1.4 데이터 전처리 스크립트 디렉토리 생성

  ```bash
  mkdir -p scripts/data_preprocessing
  ```

### 🔴 1.2 PostgreSQL 스키마 구축 (순차 실행 필수)

- [ ] 1.2.1 PostgreSQL 연결 유틸리티 작성

  - 파일: `scripts/data_preprocessing/utils/db_connection.py`
  - PostgreSQL 연결 테스트
- [ ] 1.2.2 `users` 테이블 생성 스크립트 작성 및 실행

  - 파일: `scripts/data_preprocessing/schema/01_create_users.sql`
  - UUID, email UNIQUE, password_hash, role, ckd_stage 등
- [ ] 1.2.3 `foods` 테이블 생성 스크립트 작성 및 실행

  - 파일: `scripts/data_preprocessing/schema/02_create_foods.sql`
  - 영양성분 컬럼, GIN 인덱스 (trigram 검색)
- [ ] 1.2.4 `recipes` 테이블 생성 스크립트 작성 및 실행

  - 파일: `scripts/data_preprocessing/schema/03_create_recipes.sql`
  - JSONB ingredients, GIN 인덱스
- [ ] 1.2.5 `substitutes` 테이블 생성

  - 파일: `scripts/data_preprocessing/schema/04_create_substitutes.sql`
- [ ] 1.2.6 `nutrition_limits` 테이블 생성

  - 파일: `scripts/data_preprocessing/schema/05_create_nutrition_limits.sql`
- [ ] 1.2.7 `ai_jobs` 테이블 생성

  - 파일: `scripts/data_preprocessing/schema/06_create_ai_jobs.sql`
- [ ] 1.2.8 나머지 테이블 생성 (`sessions`, `user_recipes`, `analysis_history`, `logs`)

  - 파일: `scripts/data_preprocessing/schema/07_create_others.sql`

### 🟢 1.3 데이터 수집 (병렬 가능)

- [ ] 1.3.1 국가표준식품성분표 Excel 파일 다운로드

  - [농촌진흥청 식품성분 DB](https://koreanfood.rda.go.kr/)
  - 저장: `data/raw/food_composition.xlsx`
- [ ] 1.3.2 대한신장학회 PDF 다운로드

  - 혈액투석 환자 영양 가이드
  - 저장: `data/raw/kidney_nutrition_guide.pdf`

### 🔴 1.4 데이터 전처리 (1.2, 1.3 완료 후 순차 실행)

- [ ] 1.4.1 국가표준식품성분표 파싱 스크립트 작성

  - 파일: `scripts/data_preprocessing/parse_food_data.py`
  - Excel → pandas DataFrame 변환
  - 컬럼명 표준화
- [ ] 1.4.2 식품명 정제 로직 구현

  - 파일: `scripts/data_preprocessing/clean_food_names.py`
  - 유사어 통합, 특수문자 제거, aliases 생성
- [ ] 1.4.3 단위 표준화 함수 구현

  - 1컵=200g, 1큰술=15g, 1작은술=5g 변환
- [ ] 1.4.4 결측치 처리 로직 구현

  - 동일 카테고리 평균값 보간
- [ ] 1.4.5 PostgreSQL `foods` 테이블에 데이터 삽입

  - Batch insert (1000건 단위)
  - 실행: `python scripts/data_preprocessing/insert_foods.py`

### 🔴 1.5 대체재료 매핑 (1.4.5 완료 후 실행)

- [ ] 1.5.1 고칼륨/고인 식품 필터링

  - K>200mg or P>150mg per 100g
- [ ] 1.5.2 저함량 대체재 매칭 알고리즘 구현

  - 파일: `scripts/data_preprocessing/generate_substitutes.py`
  - 동일 카테고리 내 K/P 50% 이상 감소
- [ ] 1.5.3 `substitutes` 테이블에 데이터 삽입

  - score, reason, reduction_pct 계산

### 🟢 1.6 MongoDB 컬렉션 구축 (병렬 가능)

- [ ] 1.6.1 MongoDB 연결 유틸리티 작성

  - 파일: `scripts/data_preprocessing/utils/mongo_connection.py`
- [ ] 1.6.2 MongoDB 컬렉션 생성 스크립트

  - 파일: `scripts/data_preprocessing/setup_mongo_collections.py`
  - embeddings, chat_logs, cache_responses, reference_docs, feedbacks
- [ ] 1.6.3 인덱스 생성

  - text index, TTL index

### 🔴 1.7 임베딩 생성 (1.4.5 완료 후, 시간 소요 큼)

- [ ] 1.7.1 Sentence Transformers 설치

  ```bash
  pip install sentence-transformers
  ```
- [ ] 1.7.2 임베딩 생성 스크립트 작성

  - 파일: `scripts/data_preprocessing/generate_embeddings.py`
  - 모델: `paraphrase-multilingual-MiniLM-L12-v2`
  - 배치 처리 500건 단위
- [ ] 1.7.3 MongoDB `embeddings` 컬렉션에 저장

  - 실행: `python scripts/data_preprocessing/generate_embeddings.py`

### 🟢 1.8 데이터 검증 (병렬 가능)

- [ ] 1.8.1 PostgreSQL 데이터 무결성 검사

  - 파일: `scripts/data_preprocessing/validate_postgres.py`
  - NULL 비율, 이상치 검출
- [ ] 1.8.2 MongoDB 임베딩 품질 검사

  - 벡터 차원 확인, 샘플 유사도 테스트
- [ ] 1.8.3 데이터 통계 리포트 생성

  - 총 레코드 수, 카테고리별 분포
  - 출력: `data/processed/data_report.txt`

---

## 🔧 Phase 2: BACKEND - FastAPI + Nest.js

### 🟢 2.1 프로젝트 초기화 (병렬 가능)

- [ ] 2.1.1 백엔드 디렉토리 구조 생성

  ```bash
  mkdir -p BACKEND/{fastapi,nestjs}
  ```
- [ ] 2.1.2 FastAPI 프로젝트 구조 생성

  ```bash
  cd BACKEND/fastapi
  mkdir -p app/{routers,models,services,utils}
  touch app/{__init__.py,main.py}
  ```
- [ ] 2.1.3 FastAPI 가상환경 및 의존성 설치

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install fastapi uvicorn sqlalchemy asyncpg pymongo motor python-dotenv openai pydantic
  ```
- [ ] 2.1.4 Nest.js 프로젝트 생성

  ```bash
  cd BACKEND/nestjs
  npm install -g @nestjs/cli
  nest new . --skip-git
  ```
- [ ] 2.1.5 Nest.js 필수 패키지 설치

  ```bash
  npm install @nestjs/config @nestjs/typeorm typeorm pg bcrypt @nestjs/jwt @nestjs/passport passport passport-jwt
  npm install -D @types/bcrypt @types/passport-jwt
  ```

### 🔴 2.2 FastAPI 기본 설정 (순차 실행)

- [ ] 2.2.1 FastAPI main.py 작성

  - CORS 설정, 미들웨어
- [ ] 2.2.2 PostgreSQL 연결 설정

  - 파일: `BACKEND/fastapi/app/utils/db_postgres.py`
  - asyncpg 또는 SQLAlchemy
- [ ] 2.2.3 MongoDB 연결 설정

  - 파일: `BACKEND/fastapi/app/utils/db_mongo.py`
  - motor (async driver)
- [ ] 2.2.4 Pydantic 모델 정의

  - 파일: `BACKEND/fastapi/app/models/schemas.py`
  - FoodModel, RecipeModel, AnalysisRequest/Response
- [ ] 2.2.5 헬스체크 엔드포인트 작성

  - `GET /health` - DB 연결 상태 확인
  - 테스트: `curl http://localhost:8000/health`

### 🔴 2.3 Nest.js 인증 시스템 (순차 실행, 블로킹)

- [ ] 2.3.1 TypeORM 설정

  - 파일: `BACKEND/nestjs/src/config/database.config.ts`
  - PostgreSQL 연결
- [ ] 2.3.2 User 엔티티 생성

  - 파일: `BACKEND/nestjs/src/users/entities/user.entity.ts`
  - id, email, password_hash, role, ckd_stage 등
- [ ] 2.3.3 Users 모듈 생성

  ```bash
  nest g module users
  nest g service users
  nest g controller users
  ```
- [ ] 2.3.4 Auth 모듈 생성

  ```bash
  nest g module auth
  nest g service auth
  nest g controller auth
  ```
- [ ] 2.3.5 JWT 전략 구현

  - 파일: `BACKEND/nestjs/src/auth/strategies/jwt.strategy.ts`
  - Passport-JWT 설정
- [ ] 2.3.6 `POST /auth/register` 구현

  - 이메일 중복 체크, bcrypt 해싱
  - 테스트: Postman 또는 curl
- [ ] 2.3.7 `POST /auth/login` 구현

  - JWT access_token + refresh_token 발급
- [ ] 2.3.8 `POST /auth/refresh` 구현

  - refresh_token 검증 후 새 access_token 발급
- [ ] 2.3.9 `POST /auth/logout` 구현

  - sessions 테이블 revoked_at 업데이트
- [ ] 2.3.10 JWT Guard 구현 및 적용

  - `@UseGuards(JwtAuthGuard)` 데코레이터

### 🟢 2.4 Nest.js CRUD API (2.3 완료 후 병렬 가능)

- [ ] 2.4.1 `GET /api/users/me` 구현

  - JWT에서 user_id 추출, nutrition_limits 조인
- [ ] 2.4.2 `PUT /api/users/me` 구현

  - 사용자 정보 업데이트
- [ ] 2.4.3 Recipes 모듈 생성

  ```bash
  nest g resource recipes
  ```
- [ ] 2.4.4 `POST /api/recipes` 구현

  - JSONB ingredients 저장
  - 영양소 합계 자동 계산
- [ ] 2.4.5 `GET /api/recipes/:id` 구현
- [ ] 2.4.6 `GET /api/recipes` (목록) 구현

  - 페이지네이션, 필터링
- [ ] 2.4.7 Foods 컨트롤러 생성

  - `GET /api/foods?query=감자&limit=10`
  - trigram 검색
- [ ] 2.4.8 `POST /api/feedbacks` 구현

  - MongoDB feedbacks 컬렉션에 저장

### 🔴 2.5 FastAPI AI 기능 (핵심, 순차 실행)

- [ ] 2.5.1 OpenAI API 클라이언트 설정

  - 파일: `BACKEND/fastapi/app/services/openai_client.py`
  - `.env`에서 `OPENAI_API_KEY` 로드
- [ ] 2.5.2 시스템 프롬프트 템플릿 작성

  - 파일: `BACKEND/fastapi/app/prompts/system_prompt.py`
  - CKD 전문 영양 코치 역할 정의
- [ ] 2.5.3 `POST /ai/analyze-recipe` 구현

  - 텍스트 레시피 파싱 (정규표현식 + LLM)
  - 재료명, 양 추출
- [ ] 2.5.4 재료 매칭 로직 구현

  - PostgreSQL foods 테이블 trigram 검색
  - 폴백: MongoDB embeddings 벡터 검색
- [ ] 2.5.5 영양소 계산 함수 구현

  - `amount_g * (nutrient_per_100g / 100)`
  - 총합 계산
- [ ] 2.5.6 안전도 판정 로직 구현

  - nutrition_limits와 비교
  - status: safe/warning/danger
- [ ] 2.5.7 `POST /ai/analyze-image` 구현

  - GPT-Vision API 호출
  - 음식명, 예상 재료 추출
  - analyze-recipe 로직 재사용
- [ ] 2.5.8 `POST /ai/recommend-substitutes` 구현

  - 위험 재료 식별
  - substitutes 테이블 조회
  - score 순 정렬
- [ ] 2.5.9 `POST /ai/generate-recipe` 구현

  - 대체 재료 기반 새 레시피 생성 프롬프트
  - LLM 호출 (조리법, 팁)
- [ ] 2.5.10 `POST /ai/summary` 구현

  - 5줄 요약 프롬프트
  - 환자 친화적 언어
- [ ] 2.5.11 `POST /ai/generate-quiz` 구현

  - OX, 4지선다 문제 생성
  - MongoDB quiz_questions 저장
- [ ] 2.5.12 `POST /ai/chat` 구현

  - 세션 기반 대화 히스토리 관리
  - context window 20턴 제한
- [ ] 2.5.13 `GET /ai/job/{job_id}` 구현 (Streamlit용)

  - ai_jobs 테이블 조회 + 결과 반환

### 🟢 2.6 캐싱 및 성능 최적화 (병렬 가능)

- [ ] 2.6.1 Redis 연결 설정

  - FastAPI + aioredis
- [ ] 2.6.2 LLM 응답 캐싱 구현

  - query_hash = md5(prompt + params)
  - MongoDB cache_responses TTL 7일
- [ ] 2.6.3 API Rate Limiting 구현

  - slowapi (per-user)
- [ ] 2.6.4 Connection Pool 최적화

  - asyncpg, motor pool size 설정

### 🟢 2.7 로깅 및 모니터링 (병렬 가능)

- [ ] 2.7.1 구조화된 로깅 설정

  - JSON 포맷 (timestamp, level, user_id, request_id)
- [ ] 2.7.2 X-Request-ID 헤더 전파 미들웨어
- [ ] 2.7.3 에러 핸들링 미들웨어

  - 500 에러 로깅
- [ ] 2.7.4 MongoDB logs 테이블에 행동 로그 저장

### 🟢 2.8 테스트 작성 (병렬 가능)

- [ ] 2.8.1 FastAPI 단위 테스트

  - pytest, 영양소 계산 함수
- [ ] 2.8.2 FastAPI 통합 테스트

  - TestClient, /ai/analyze-recipe E2E
- [ ] 2.8.3 Nest.js 단위 테스트

  - Jest, AuthService
- [ ] 2.8.4 Nest.js E2E 테스트

  - Supertest, /auth/login

---

## 🎨 Phase 3: FRONTEND - Next.js + Streamlit

### 🟢 3.1 Next.js 프로젝트 초기화 (병렬 가능)

- [ ] 3.1.1 Next.js 14 프로젝트 생성

  ```bash
  cd FRONTEND
  npx create-next-app@latest . --typescript --tailwind --app --no-src-dir
  ```
- [ ] 3.1.2 프로젝트 디렉토리 구조 설정

  ```bash
  mkdir -p {components,lib,types,styles}
  ```
- [ ] 3.1.3 환경변수 파일 작성

  - `.env.local` 생성
  - `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] 3.1.4 Tailwind CSS 커스텀 테마 설정

  - `tailwind.config.ts` 수정
  - 안전도 색상 정의 (green-500, yellow-400, red-500)
- [ ] 3.1.5 필수 패키지 설치

  ```bash
  npm install next-auth axios react-hot-toast
  npm install -D @types/node
  ```

### 🔴 3.2 인증 UI (2.3 완료 후 순차 실행)

- [ ] 3.2.1 NextAuth.js 설정

  - 파일: `app/api/auth/[...nextauth]/route.ts`
  - Credentials Provider (Nest.js JWT)
- [ ] 3.2.2 로그인 페이지 작성

  - 파일: `app/auth/login/page.tsx`
  - 이메일/비밀번호 폼
- [ ] 3.2.3 회원가입 페이지 작성

  - 파일: `app/auth/register/page.tsx`
  - CKD 단계, 투석 타입 선택
- [ ] 3.2.4 인증 상태 관리

  - `useSession()` 훅 사용
  - Protected Routes HOC
- [ ] 3.2.5 로그아웃 기능 구현

### 🟢 3.3 메인 대시보드 (3.2 완료 후 병렬 가능)

- [ ] 3.3.1 레이아웃 컴포넌트 작성

  - 파일: `components/Layout.tsx`
  - Header, Sidebar, Footer
- [ ] 3.3.2 홈 대시보드 페이지

  - 파일: `app/page.tsx`
  - 사용자 영양 제한 요약 카드
- [ ] 3.3.3 네비게이션 컴포넌트

  - 파일: `components/Navigation.tsx`

### 🔴 3.4 이미지 분석 기능 (2.5.7 완료 후 순차 실행)

- [ ] 3.4.1 이미지 업로드 컴포넌트 작성

  - 파일: `components/ImageUpload.tsx`
  - Drag & Drop, 파일 선택
- [ ] 3.4.2 이미지 분석 페이지

  - 파일: `app/analyze/image/page.tsx`
- [ ] 3.4.3 이미지 업로드 API 호출

  - FormData multipart/form-data
  - `POST /ai/analyze-image`
- [ ] 3.4.4 분석 결과 표시 컴포넌트

  - 파일: `components/AnalysisResult.tsx`
  - 음식명, 재료 테이블, 영양소 총합
- [ ] 3.4.5 안전도 뱃지 컴포넌트

  - 파일: `components/SafetyBadge.tsx`
  - 녹색/노랑/빨강 색상

### 🔴 3.5 레시피 분석 기능 (2.5.3 완료 후 순차 실행)

- [ ] 3.5.1 텍스트 레시피 입력 폼

  - 파일: `app/analyze/recipe/page.tsx`
- [ ] 3.5.2 레시피 분석 API 호출

  - `POST /ai/analyze-recipe`
- [ ] 3.5.3 분석 결과 표시 (AnalysisResult 재사용)
- [ ] 3.5.4 대체재료 추천 UI

  - 파일: `components/SubstituteList.tsx`

### 🔴 3.6 대체 레시피 생성 (2.5.9 완료 후)

- [ ] 3.6.1 대체재료 선택 UI (Checkbox)
- [ ] 3.6.2 "대체 레시피 생성" 버튼 구현

  - `POST /ai/generate-recipe`
- [ ] 3.6.3 생성된 레시피 표시
- [ ] 3.6.4 레시피 저장 기능

  - `POST /api/recipes`

### 🟢 3.7 내 레시피 관리 (2.4.4 완료 후 병렬 가능)

- [ ] 3.7.1 레시피 목록 페이지

  - 파일: `app/recipes/page.tsx`
- [ ] 3.7.2 레시피 상세 페이지

  - 파일: `app/recipes/[id]/page.tsx`
- [ ] 3.7.3 레시피 수정/삭제 기능

### 🟢 3.8 사용자 설정 페이지 (병렬 가능)

- [ ] 3.8.1 설정 페이지 레이아웃

  - 파일: `app/settings/page.tsx`
- [ ] 3.8.2 개인정보 수정 폼

  - `PUT /api/users/me`
- [ ] 3.8.3 영양 제한 설정

### 🟢 3.9 Streamlit 시각화 페이지 (2.5.13 완료 후 독립 가능)

- [ ] 3.9.1 Streamlit 프로젝트 생성

  ```bash
  mkdir -p FRONTEND/streamlit
  cd FRONTEND/streamlit
  python3 -m venv venv
  source venv/bin/activate
  pip install streamlit plotly pandas requests
  ```
- [ ] 3.9.2 Streamlit 앱 메인 파일 작성

  - 파일: `FRONTEND/streamlit/app.py`
- [ ] 3.9.3 job_id 파라미터 읽기

  - `st.query_params['job_id']`
- [ ] 3.9.4 FastAPI 분석 결과 조회

  - `GET /ai/job/{job_id}`
- [ ] 3.9.5 요약 카드 표시

  - st.metric()
- [ ] 3.9.6 영양 비율 차트 (Plotly)

  - 도넛 차트
- [ ] 3.9.7 재료 테이블

  - st.dataframe()
- [ ] 3.9.8 대체재 제안 섹션
- [ ] 3.9.9 퀴즈 모듈

  - st.radio(), 즉시 채점

### 🟢 3.10 고급 UI/UX (병렬 가능)

- [ ] 3.10.1 로딩 스피너 컴포넌트
- [ ] 3.10.2 토스트 알림

  - react-hot-toast
- [ ] 3.10.3 반응형 디자인 최적화

### 🟢 3.11 테스트 (병렬 가능)

- [ ] 3.11.1 컴포넌트 단위 테스트

  - Jest + React Testing Library
- [ ] 3.11.2 E2E 테스트

  - Playwright

---

## 🔗 Phase 4: 통합 및 배포

### 🔴 4.1 Docker 컨테이너화 (순차 실행)

- [ ] 4.1.1 FastAPI Dockerfile 작성

  - 파일: `BACKEND/fastapi/Dockerfile`
- [ ] 4.1.2 Nest.js Dockerfile 작성

  - 파일: `BACKEND/nestjs/Dockerfile`
- [ ] 4.1.3 Next.js Dockerfile 작성

  - 파일: `FRONTEND/Dockerfile`
- [ ] 4.1.4 Streamlit Dockerfile 작성

  - 파일: `FRONTEND/streamlit/Dockerfile`
- [ ] 4.1.5 전체 Docker Compose 통합 테스트

  - `docker-compose up --build`

### 🟢 4.2 CI/CD 파이프라인 (독립 가능)

- [ ] 4.2.1 GitHub Actions 워크플로우 작성

  - 파일: `.github/workflows/ci.yml`
- [ ] 4.2.2 테스트 자동 실행 설정
- [ ] 4.2.3 ECR 이미지 푸시 설정 (AWS 사용 시)

### 🔴 4.3 최종 통합 테스트 (전체 팀)

- [ ] 4.3.1 인증 플로우 E2E 테스트
- [ ] 4.3.2 이미지 분석 전체 플로우 테스트
- [ ] 4.3.3 성능 테스트 (K6 또는 Locust)
- [ ] 4.3.4 보안 검사

---

## 📝 진행 상황 메모

### 현재 진행 중인 Task:

### 완료된 Phase:

### 발생한 이슈:

### 다음 단계:

---

**마지막 업데이트**: 2025-10-16
