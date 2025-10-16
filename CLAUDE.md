# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**콩닥 식탁 (Kongdak Table)** - CKD(만성콩팥병) 환자를 위한 식단 코칭형 AI 챗봇 웹앱

- **대상**: CKD 환자 약 460만명 (국내 성인 유병률 8.4%)
- **목적**: 식약처 공공데이터와 대한신장학회 지침 기반 질환/영양 도메인 특화 식단 제공

## 아키텍처

### 3-Tier 구조

```
Frontend: Next.js (메인 UI) + Streamlit (AI 분석 시각화)
         ↓
Backend:  Nest.js (인증/권한/세션 관리) + FastAPI (AI 분석)
         ↓
Database: PostgreSQL (핵심 데이터) + MongoDB (벡터/캐시/LLM 내역)
```

### 주요 기술 스택

- **Frontend**: Next.js 14.x, React 18.x, TypeScript, Tailwind CSS, Streamlit 1.x
- **Backend**:
  - FastAPI 0.100+ (AI/ML 처리, 비동기)
  - Nest.js 10.x (인증, 비즈니스 로직)
- **AI/ML**: OpenAI GPT-4, GPT-Vision, LangChain, Sentence Transformers
- **Database**: PostgreSQL 15.x, MongoDB 6.x, Redis 7.x
- **Infrastructure**: Docker, AWS/GCP

## 핵심 도메인 지식

### 영양소 제한 기준 (한끼 식사)

```
필요 영양소:
- 열량: 500-800 kcal

제한 영양소:
- 나트륨: ≤650mg
- 칼륨: ≤650mg
- 인: ≤330mg
- 단백질: ≤0.4g

안전도 표시:
- 🟢 녹색(안전): 권장량의 0-80%
- 🟡 노란색(주의): 권장량의 80-100%
- 🔴 빨간색(위험): 권장량 초과
```

## 데이터베이스 설계

### PostgreSQL 주요 테이블

- **users**: 사용자 정보, CKD 단계, 투석 타입
- **foods**: 식품 영양성분 (칼륨, 인, 나트륨 등)
- **recipes**: 레시피 정보 및 영양소 추정치 (JSONB 재료 구조)
- **substitutes**: 대체재료 매핑 (고칼륨/고인 → 저함량 식품)
- **ai_jobs**: AI 처리 작업 추적 (job_id 기반)
- **nutrition_limits**: 사용자별 개인화 영양소 제한 기준

### MongoDB 컬렉션

- **embeddings**: 식품/레시피 임베딩 벡터 (벡터 유사도 검색용)
- **chat_logs**: LLM 대화 로그 (토큰 사용량, 레이턴시)
- **cache_responses**: LLM 응답 캐시 (TTL 기반)
- **reference_docs**: 의료/영양 참고문서 (RAG용)
- **feedbacks**: 사용자 피드백 및 퀴즈 결과

## API 통신 구조

### 인증 플로우 (Nest.js)

1. 사용자 → Next.js 로그인 폼 → `POST /auth/login` (Nest.js)
2. JWT access_token (메모리/httpOnly 쿠키) + refresh_token (httpOnly 쿠키) 발급
3. FastAPI 호출 시 `Authorization: Bearer <token>` 헤더 전달

### 주요 엔드포인트

**Nest.js (인증/CRUD)**:
- `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`
- `/api/users/me`: 사용자 프로필 및 영양 제한 조회
- `/api/recipes`: 레시피 CRUD
- `/api/foods?query=<검색어>`: 식품 검색

**FastAPI (AI 기능)**:
- `/ai/analyze-image`: 음식 사진 분석 → 재료 추출 → 영양소 계산 → 위험도 판정
- `/ai/analyze-recipe`: 텍스트 레시피 분석
- `/ai/recommend-substitutes`: 대체재료 추천
- `/ai/summary`: 문서 5줄 요약
- `/ai/generate-quiz`: 영양 교육용 퀴즈 생성
- `/ai/chat`: 대화형 챗봇

## 핵심 서비스 플로우

### 이미지 분석 플로우

1. **사용자 입력**: 요리 이미지 업로드 또는 레시피 텍스트
2. **LLM 분석**: GPT-Vision으로 요리명, 재료 추출
3. **영양성분 검색**: 국가표준식품성분표 벡터 DB 조회
4. **위험도 분석**: 칼륨/인 총량 계산 → 제한치 초과 시 "위험성분" 표시
5. **대체재료 탐색**: 벡터 유사도 검색으로 저함량 대체재 찾기
6. **대체 레시피 생성**: LLM이 대체재료 기반 새 레시피 작성
7. **피드백 퀴즈**: 저칼륨/저인 재료 맞추기 문제 생성

### Streamlit 시각화 페이지

- Next.js에서 "AI 분석 결과 보기" 클릭 → `/streamlit/analysis?job_id=<uuid>`
- Streamlit이 FastAPI의 `/ai/job/:job_id` 호출하여 결과 시각화
- 영양 비율 차트, 대체재 제안, 안전도 색상 표시, 교육용 퀴즈 제공

## 프롬프트 엔지니어링

### 시스템 프롬프트 구조

```python
SYSTEM_PROMPT = """
당신은 만성콩팥병(CKD) 환자를 위한 전문 영양 AI 코치 '콩닥'입니다.

핵심 역할:
1. CKD 환자의 식단 안전성 평가 및 개선안 제시
2. 대한신장학회 가이드라인 기반 조언
3. 친근하고 희망적인 톤으로 소통

영양소 제한 기준 (1일):
- 칼륨: 2000mg 이하
- 인: 800mg 이하
- 나트륨: 2000mg 이하
"""
```

### 주요 프롬프트 유형

- **IMAGE_ANALYSIS_PROMPT**: JSON 형식으로 음식명, 재료, 추정량 추출
- **SUBSTITUTE_PROMPT**: 칼륨/인 50% 이상 낮은 대체재 3개 추천
- **RECIPE_GENERATION_PROMPT**: 데치기/불리기 등 칼륨 제거 조리법 포함
- **QUIZ_GENERATION_PROMPT**: OX/4지선다/비교 문제 생성 (교육 목표 포함)

## 개발 환경 설정

### 로컬 Docker Compose 구성

```yaml
services:
  postgres:
    - PostgreSQL 13
    - 환경변수: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
  mongo:
    - MongoDB 5.0+
  redis:
    - 세션/캐시용 (선택)
  backend-fastapi:
    - FastAPI 앱
    - 포트: 8000
  backend-nest:
    - Nest.js 앱
    - 포트: 3001
  frontend-next:
    - Next.js 앱
    - 포트: 3000
```

### 환경변수 관리

- 로컬: `.env.local` 파일
- 배포: AWS Secrets Manager 또는 환경별 시크릿 관리

## 보안 고려사항

### 인증 보안

- JWT 서명: RS256 (비대칭 키) 권장
- Refresh token: httpOnly, Secure cookie, DB에 해시 저장
- 민감 데이터: at-rest encryption (KMS)

### API 보안

- 모든 통신 HTTPS/TLS 필수
- FastAPI는 JWT 서명/권한 검증
- Rate limiting (per-user)
- CORS 정책 적용

### 의료 정보 규제

- ⚠️ 진단/처방 금지 (참고용 명시)
- 각 결과에 면책조항 표시
- 데이터 출처 명시 및 정기 검증

## 데이터 출처

- **식품의약품안전처**: 영양성분 DB (https://various.foodsafetykorea.go.kr/)
- **국가표준식품성분표**: 농촌진흥청 (250426 공개 버전)
- **대한신장학회**: 혈액투석 환자 영양-식생활 관리 가이드
- **AI 허브**: 음식 이미지-레시피 데이터 (https://aihub.or.kr)

## 테스트 전략

- **단위 테스트**: Jest (Node.js), pytest (Python) - 목표 커버리지 80%
- **통합 테스트**: Supertest, FastAPI TestClient - 목표 70%
- **E2E 테스트**: Cypress, Playwright (핵심 플로우)
- **성능 테스트**: API 응답시간 <3초 목표

## 모니터링

- **Tracing**: OpenTelemetry (X-Request-ID 기반 서비스 간 추적)
- **Logging**: JSON 구조화 로그
- **Metrics**: Prometheus + Grafana
- **Alerts**: latency, error-rate, data-drift

## 배포 전략

### 클라우드 (AWS 예시)

- **PostgreSQL**: RDS (Multi-AZ, 자동 백업)
- **MongoDB**: MongoDB Atlas 또는 EC2 ReplicaSet
- **컨테이너**: ECS/Fargate 또는 EKS
- **CI/CD**: GitHub Actions → ECR push → ECS 업데이트

## 핵심 제약사항

1. **데이터 정확성**: 신뢰할 수 있는 영양 정보 필수
2. **응답 속도**: LLM 응답 3초 이내 (캐싱 전략 필수)
3. **의료 책임**: 의료행위 금지, 법률 검토 필수
4. **사용자 경험**: 직관적 UI, 3색 안전도 표시

## 개발 시 주의사항

### 영양소 계산

- 항상 100g 기준 영양성분을 실제 사용량(g)으로 환산
- 사용자별 개인화 제한 기준(`nutrition_limits`) 반영
- 결측치는 동일 카테고리 평균값 또는 유사 식품 참조

### 대체재료 추천

- 칼륨/인 감소율 50% 이상
- 벡터 유사도 0.7 이상 (맛/식감 유사성)
- 동일 조리법 적용 가능 여부 확인

### 프롬프트 최적화

- 사용자 프로필(CKD 단계, 투석 유형) 컨텍스트 추가
- Few-shot 예시로 응답 품질 향상
- 프롬프트 체이닝으로 복잡한 분석 수행

## 참고 문서 위치

- `DOC/PRD_기본2.md`: 전체 프로덕트 요구사항 정의서
- `DOC/DB_PROTOCOL.txt`: 데이터베이스 스키마 및 API 명세
- `DOC/Streamlit AI 분석 서브 페이지 설계서.txt`: Streamlit 페이지 상세 설계

## 주요 용어

- **CKD**: Chronic Kidney Disease (만성콩팥병)
- **칼륨(K)**: 신장 기능 저하 시 제한 필요한 무기질
- **인(P)**: 과다 시 혈관 석회화 유발
- **혈액투석**: 기계로 혈액을 정화하는 치료
- **RAG**: Retrieval-Augmented Generation (벡터 검색 기반 생성)
- **KFCT**: 한국 식품 성분표

## 협업 정보

- **소스 관리**: GitHub
- **프로젝트 관리**: Jira/Linear
- **커뮤니케이션**: Slack
- **문서**: Notion
- **디자인**: Figma

---

**문서 버전**: 1.0
**최종 수정**: 2025-10-16
**상태**: ACTIVE
