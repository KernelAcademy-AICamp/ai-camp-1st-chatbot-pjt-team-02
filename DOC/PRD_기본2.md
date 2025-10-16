# 🧠 PRD (v2): 식단 코치 AI 챗봇 "콩닥 식탁"
### — Next.js + FastAPI + Nest.js 통합 구조 반영 —

## 1. 프로젝트 개요

- **제품명:** 콩닥 식탁 (Kongdak Table)
- **유형:** CKD(만성콩팥병) 환자 식단 코칭형 LLM 웹앱
- **대상 사용자:** CKD 환자 약 460만명 (국내 성인 유병률 8.4%)
- **개발 구조:**
  - **Frontend:** Next.js 중심 UI, Streamlit은 AI 분석 및 시각화용 서브 페이지로 연결
  - **Backend:** FastAPI(AI 분석) + Nest.js(인증/권한/세션 관리)
  - **LLM API:** OpenAI GPT 기반
  - **DB:** PostgreSQL(핵심 데이터) + MongoDB(LLM 관련 캐시/내역/질의결과 저장) + Docker

## 2. 서비스 배경 및 목적

### 2.1 배경
- **국내 현황:** 2021년 국민건강영양조사 기준 성인 CKD 유병률 약 8.4%
- **문제점:**
  - 신장 투석 환자는 칼륨, 인, 나트륨 제한식이 필수
  - 시중 레시피/식단 앱은 칼륨·인 데이터 누락
  - 환자/보호자가 직접 성분표 확인하고 대체재료 찾아야 함
  - 시간·노력·정보 접근성 모두 비효율적

### 2.2 목적
식약처 공공데이터와 대한신장학회 지침을 기반으로 질환/영양 도메인에 특화된 식단/답변을 제공하는 AI 코치 서비스 구축

## 3. 핵심 목표 및 KPI

| 구분 | 목표 | KPI | 주요 산출물 |
|------|------|-----|------------|
| **기획 목표** | 의료식단 AI 코치 서비스 설계 | 사용자 만족도 ≥4.5/5 | 서비스 시나리오, UI/UX 설계 |
| **개발 목표** | FastAPI + Nest.js 통합형 챗봇 | 응답 시간 ≤3초 | 웹앱 MVP, API 문서 |
| **AI 목표** | LLM 기반 질의응답 + 분석 | LLM 응답 품질 ≥85% | 프롬프트 엔지니어링 |
| **데이터 목표** | 영양성분 DB 구축 | 분석 정확도 ≥90% | 통합 영양성분 DB |
| **비즈니스 목표** | 사용자 확보 | 사용 유지율 ≥70% | 마케팅 전략 |

## 4. 주요 사용자 및 페르소나

| 구분 | 역할 | 요구사항 | 사용 시나리오 |
|------|------|----------|-------------|
| **환자** | CKD 3~5단계, 투석 중 | 음식의 안전 여부 즉시 확인 | 외식 시 메뉴 사진 촬영 후 확인 |
| **보호자** | 조리 담당자 | 대체 레시피, 재료 조합 제안 | 일주일 식단 계획 수립 |
| **영양사** | 모니터링 담당 | 환자별 기록 확인, 분석 | 환자 상담 시 참고자료 활용 |
| **의료인** | 진료 보조 | 교육용 식단 상담 활용 | 진료 중 식단 지도 |
| **일반 사용자** | 건강관리 관심 | 저염/저인 레시피 참고 | 예방적 건강관리 |
| **개발자(교육생)** | 프롬프트 설계 실습 | 요약/Q&A/퀴즈/추천 구현 | LLM 활용 학습 |

## 5. 신장 투석 환자 영양소 제한 기준

```
한끼 식사 기준:
┌────────────────────────────────────────────┐
│ 필요 영양소                                │
│ • 열량: 500-800 kcal                      │
├────────────────────────────────────────────┤
│ 제한 영양소                                │
│ • 나트륨: ≤650mg                          │
│ • 칼륨: ≤650mg                            │
│ • 인: ≤330mg                              │
│ • 단백질: ≤0.4g                           │
├────────────────────────────────────────────┤
│ 안전도 표시 기준                           │
│ • 녹색(안전): 권장량의 0-80%              │
│ • 노란색(주의): 권장량의 80-100%          │
│ • 빨간색(위험): 권장량 초과               │
└────────────────────────────────────────────┘
```

## 6. 서비스 플로우

### 6.1 메인 서비스 플로우
1. **사용자 입력**: 요리 이미지 업로드 또는 레시피 텍스트 입력 ("이 요리 맛있어 보이는데 만드는 법 알려줘")
2. **LLM 분석**: 이미지/텍스트에서 요리명, 레시피, 재료 추출
3. **프롬프트 생성**: 서비스 특화 프롬프트 + 조건별 서브 프롬프트 생성
4. **영양성분 검색**: 국가표준식품성분표 벡터 DB에서 재료별 칼륨, 인 함량 조회
5. **위험도 분석**: 총 칼륨/인 함량 계산 → 제한치 초과 시 "위험성분" 표시
6. **대체재료 탐색**: 고함량 재료를 저함량 재료로 자동 검색
7. **대체 레시피 생성**: LLM이 대체재료 기반 새 레시피 작성
8. **응답 반환**: FastAPI를 통해 사용자에게 결과 전달
9. **피드백 퀴즈**: "저칼륨, 저인 재료 맞추기" 문제 생성 및 제공

### 6.2 플로우차트
```
사용자 입력 → 이미지/텍스트 분석 → 재료 추출 → 영양성분 DB 조회
     ↓                                              ↓
피드백 퀴즈 ← 결과 표시 ← 대체 레시피 생성 ← 위험도 판정
```

## 7. 주요 기능 상세

| 구분 | 기능명 | 상세 설명 | 기술 구현 | 예시 |
|------|--------|-----------|-----------|------|
| ① | **이미지 질의 응답** | 음식 사진을 올리면 "이 음식은 먹어도 될까?" AI가 분석 | GPT-Vision API | 떡볶이 사진 → 위험도 분석 |
| ② | **레시피 성분 분석** | 사용자 입력 레시피에서 재료 자동 인식 및 성분 추출 | NLP + 정규표현식 | "피망 100g" → 칼륨 218mg |
| ③ | **대체 재료 검색** | 고칼륨·고인 식품을 저함량 식품으로 자동 치환 | 벡터 유사도 검색 | 피망 → 오이로 대체 |
| ④ | **조리법 생성** | 투석 환자용 대체 레시피 자동 생성 | LLM 프롬프트 | 저칼륨 떡볶이 레시피 |
| ⑤ | **안전성 피드백** | 대체 후 예상 칼륨·인 총량 계산 및 등급 표시 | 임계치 기반 판정 | 3색 신호등 표시 |
| ⑥ | **피드백 퀴즈 생성** | 저칼륨/저인 재료 맞추기 문제 자동 생성 | 문제 생성 프롬프트 | "라면 vs 도너츠 중 고인 식품은?" |
| ⑦ | **요약 및 Q&A** | 레시피/문서 5줄 요약 + 질문 응답 | RAG 기반 | 영양 가이드 요약 |
| ⑧ | **자료 추천** | 신뢰도 높은 식단 자료 링크 추천 | 임베딩 유사도 | 관련 학회 자료 링크 |
| ⑨ | **Streamlit 시각화** | 영양비율 차트, 트렌드 분석 대시보드 | 데이터 시각화 | 주간 영양섭취 그래프 |

## 8. 기술 아키텍처

### 8.1 시스템 구성도
```
┌─────────────────────────────────────────────────────┐
│                    Frontend Layer                    │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │   Next.js    │  │  Streamlit  │  │ Mobile App │ │
│  │   (Main UI)  │  │ (Analytics) │  │  (Future)  │ │
│  └──────┬───────┘  └──────┬──────┘  └─────┬──────┘ │
└─────────┼──────────────────┼───────────────┼────────┘
          │                  │               │
    ┌─────▼──────────────────▼───────────────▼─────┐
    │              API Gateway (Nginx)              │
    └─────────┬──────────────────┬──────────────────┘
              │                  │
    ┌─────────▼────────┐ ┌──────▼──────────┐
    │  Nest.js Backend │ │ FastAPI Backend │
    │  ┌─────────────┐ │ │ ┌─────────────┐ │
    │  │Auth Service │ │ │ │ AI Service  │ │
    │  │User Service │ │ │ │ LLM Service │ │
    │  │Recipe Mgmt  │ │ │ │Vector Search│ │
    │  └─────────────┘ │ │ └─────────────┘ │
    └─────────┬────────┘ └──────┬──────────┘
              │                  │
    ┌─────────▼──────────────────▼────────────┐
    │              Database Layer              │
    │  ┌────────────┐  ┌──────────┐  ┌─────┐ │
    │  │PostgreSQL  │  │ MongoDB  │  │Redis│ │
    │  │(Main DB)   │  │(Vectors) │  │Cache│ │
    │  └────────────┘  └──────────┘  └─────┘ │
    └──────────────────────────────────────────┘
              │
    ┌─────────▼────────────────────────────────┐
    │         External Services                 │
    │  • OpenAI API (GPT-4, GPT-Vision)        │
    │  • 식약처 공공데이터 API                 │
    │  • AWS S3 (Image Storage)                │
    └──────────────────────────────────────────┘
```

### 8.2 기술 스택 상세

| 계층 | 기술 | 버전 | 용도 |
|------|------|------|------|
| **Frontend** | Next.js | 14.x | SSR/SSG React 프레임워크 |
| | React | 18.x | UI 컴포넌트 |
| | TypeScript | 5.x | 타입 안정성 |
| | Tailwind CSS | 3.x | 스타일링 |
| | Streamlit | 1.x | 데이터 분석 대시보드 |
| **Backend** | FastAPI | 0.100+ | AI/ML 처리, 비동기 처리 |
| | Nest.js | 10.x | 인증, 비즈니스 로직 |
| | Node.js | 20.x | JavaScript 런타임 |
| **AI/ML** | OpenAI GPT-4 | latest | 텍스트 생성, 분석 |
| | GPT-Vision | latest | 이미지 분석 |
| | LangChain | 0.1.x | LLM 오케스트레이션 |
| | Sentence Transformers | 2.x | 임베딩 생성 |
| **Database** | PostgreSQL | 15.x | 구조화된 데이터 |
| | MongoDB | 6.x | 벡터 저장, 캐싱 |
| | Redis | 7.x | 세션 캐싱 |
| | Docker | latest | 컨테이너화 |
| **인프라** | AWS/GCP | - | 클라우드 호스팅 |
| | Nginx | latest | 리버스 프록시 |
| | GitHub Actions | - | CI/CD |

## 9. 데이터 구조

### 9.1 PostgreSQL 스키마

```sql
-- 식품 영양성분 테이블
CREATE TABLE foods (
    id SERIAL PRIMARY KEY,
    food_name VARCHAR(100) NOT NULL,
    food_name_en VARCHAR(100),
    food_group VARCHAR(50),
    food_subgroup VARCHAR(50),
    potassium_mg_100g DECIMAL(10,2),
    phosphorus_mg_100g DECIMAL(10,2),
    sodium_mg_100g DECIMAL(10,2),
    protein_g_100g DECIMAL(10,2),
    calories_kcal_100g DECIMAL(10,2),
    carbohydrate_g_100g DECIMAL(10,2),
    fat_g_100g DECIMAL(10,2),
    fiber_g_100g DECIMAL(10,2),
    water_g_100g DECIMAL(10,2),
    source VARCHAR(100),
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_food_name (food_name),
    INDEX idx_nutrients (potassium_mg_100g, phosphorus_mg_100g)
);

-- 레시피 테이블
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    recipe_name VARCHAR(200) NOT NULL,
    recipe_description TEXT,
    ingredients JSONB, -- [{food_id, amount_g, unit}]
    cooking_method TEXT,
    cooking_time_min INTEGER,
    serving_size INTEGER DEFAULT 1,
    total_potassium_mg DECIMAL(10,2),
    total_phosphorus_mg DECIMAL(10,2),
    total_sodium_mg DECIMAL(10,2),
    total_calories_kcal DECIMAL(10,2),
    safety_level VARCHAR(20), -- 'safe', 'caution', 'danger'
    is_original BOOLEAN DEFAULT TRUE,
    parent_recipe_id INTEGER REFERENCES recipes(id),
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 대체재료 테이블
CREATE TABLE substitutes (
    id SERIAL PRIMARY KEY,
    original_food_id INTEGER REFERENCES foods(id),
    substitute_food_id INTEGER REFERENCES foods(id),
    substitution_category VARCHAR(50), -- 'vegetable', 'protein', 'grain'
    substitution_reason TEXT,
    potassium_reduction_pct DECIMAL(5,2),
    phosphorus_reduction_pct DECIMAL(5,2),
    similarity_score DECIMAL(3,2), -- 0.00 to 1.00
    usage_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(original_food_id, substitute_food_id)
);

-- 사용자 테이블
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    user_type VARCHAR(50), -- 'patient', 'caregiver', 'nutritionist', 'doctor'
    ckd_stage INTEGER, -- 1-5 for patients
    dialysis_type VARCHAR(50), -- 'hemodialysis', 'peritoneal', 'none'
    daily_potassium_limit_mg DECIMAL(10,2),
    daily_phosphorus_limit_mg DECIMAL(10,2),
    daily_sodium_limit_mg DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- 분석 이력 테이블
CREATE TABLE analysis_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    analysis_type VARCHAR(50), -- 'image', 'text', 'recipe'
    input_data TEXT,
    image_url VARCHAR(500),
    detected_foods JSONB,
    total_potassium_mg DECIMAL(10,2),
    total_phosphorus_mg DECIMAL(10,2),
    total_sodium_mg DECIMAL(10,2),
    safety_assessment TEXT,
    suggestions JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 퀴즈 결과 테이블
CREATE TABLE quiz_results (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    quiz_type VARCHAR(50),
    questions JSONB,
    answers JSONB,
    score INTEGER,
    total_questions INTEGER,
    completed_at TIMESTAMP DEFAULT NOW()
);
```

### 9.2 MongoDB 컬렉션 구조

```javascript
// embeddings 컬렉션
{
  "_id": ObjectId,
  "food_name": "피망",
  "food_id": 123,
  "embedding_vector": [0.123, -0.456, ...], // 768차원
  "metadata": {
    "category": "vegetable",
    "potassium_level": "high",
    "phosphorus_level": "low"
  },
  "created_at": ISODate
}

// chat_logs 컬렉션
{
  "_id": ObjectId,
  "user_id": 456,
  "session_id": "uuid",
  "query": "떡볶이 레시피 분석해줘",
  "query_type": "recipe_analysis",
  "llm_response": "떡볶이는 칼륨이 높은 음식입니다...",
  "tokens_used": 1234,
  "response_time_ms": 2500,
  "timestamp": ISODate
}

// cache_responses 컬렉션
{
  "_id": ObjectId,
  "query_hash": "md5_hash",
  "query": "피망의 칼륨 함량",
  "response": "피망 100g당 칼륨 218mg",
  "ttl": 86400,
  "hit_count": 15,
  "created_at": ISODate,
  "expires_at": ISODate
}

// reference_docs 컬렉션
{
  "_id": ObjectId,
  "doc_name": "대한신장학회_식단가이드",
  "doc_type": "pdf",
  "content": "혈액투석 환자의 식단 관리...",
  "chunks": [
    {
      "chunk_id": 1,
      "text": "칼륨 제한의 중요성...",
      "embedding": [0.234, -0.567, ...]
    }
  ],
  "metadata": {
    "source": "대한신장학회",
    "year": 2024,
    "pages": 120
  }
}

// quiz_questions 컬렉션
{
  "_id": ObjectId,
  "question": "다음 중 칼륨이 가장 낮은 식품은?",
  "type": "multiple_choice",
  "options": ["바나나", "사과", "오이", "감자"],
  "correct_answer": 2,
  "explanation": "오이는 100g당 칼륨 147mg으로...",
  "difficulty": "easy",
  "category": "potassium",
  "used_count": 230
}
```

## 10. LLM 프롬프트 전략

### 10.1 프롬프트 유형별 상세 설계

#### 1) 시스템 프롬프트
```python
SYSTEM_PROMPT = """
당신은 만성콩팥병(CKD) 환자를 위한 전문 영양 AI 코치 '콩닥'입니다.

핵심 역할:
1. CKD 환자의 식단 안전성을 평가하고 개선안을 제시
2. 의학적 정확성을 유지하며 친근하게 소통
3. 대한신장학회 가이드라인 기반 조언 제공

영양소 제한 기준 (1일):
- 칼륨: 2000mg 이하
- 인: 800mg 이하
- 나트륨: 2000mg 이하
- 단백질: 체중 kg당 0.6-0.8g

한끼 기준 (1일의 1/3):
- 칼륨: 650mg 이하
- 인: 330mg 이하
- 나트륨: 650mg 이하

안전도 판정:
🟢 안전 (0-80%): 안심하고 섭취 가능
🟡 주의 (80-100%): 양 조절 필요
🔴 위험 (100% 초과): 대체 필요

대화 원칙:
- 전문 용어는 쉽게 풀어서 설명
- 긍정적이고 희망적인 톤 유지
- 실천 가능한 구체적 조언 제공
"""
```

#### 2) 이미지 분석 프롬프트
```python
IMAGE_ANALYSIS_PROMPT = """
이 음식 이미지를 분석하여 다음 정보를 JSON 형식으로 추출하세요:

{
  "dish_name": "음식명",
  "ingredients": [
    {"name": "재료명", "estimated_amount_g": 추정량},
    ...
  ],
  "cooking_method": "조리법 추정",
  "serving_size": "인분",
  "confidence": 0.0-1.0
}

추정 기준:
- 일반적인 레시피 기준
- 시각적 비율로 재료량 추정
- 한국 음식은 표준 레시피 참고
"""
```

#### 3) 대체재료 추천 프롬프트
```python
SUBSTITUTE_PROMPT = """
현재 재료: {original_food}
- 칼륨: {potassium_mg}mg/100g
- 인: {phosphorus_mg}mg/100g

CKD 환자용 대체재료 3개를 추천하세요:

선정 기준:
1. 칼륨/인 함량이 50% 이상 낮을 것
2. 맛과 식감이 유사할 것
3. 쉽게 구할 수 있을 것
4. 동일 조리법 적용 가능할 것

응답 형식:
1. [대체재료명]: 칼륨 Xmg, 인 Ymg
   - 대체 이유: 
   - 조리 팁:
"""
```

#### 4) 레시피 생성 프롬프트
```python
RECIPE_GENERATION_PROMPT = """
다음 정보로 CKD 환자용 레시피를 작성하세요:

원본 요리: {dish_name}
대체 재료: {substituted_ingredients}
목표 영양소:
- 칼륨: 650mg 이하/1인분
- 인: 330mg 이하/1인분

레시피 구성:
1. 재료 (1인분 기준)
2. 조리 과정 (칼륨/인 제거 팁 포함)
3. 영양 정보
4. 맛 유지 팁

특별 지침:
- 데치기, 불리기로 칼륨 제거
- 양념 대체안 제시
- 조리 시간 명시
"""
```

#### 5) 요약 프롬프트
```python
SUMMARY_PROMPT = """
다음 내용을 CKD 환자 관점에서 5줄로 요약하세요:

{content}

요약 원칙:
1. 핵심 영양소 제한 정보 우선
2. 실천 가능한 조언 포함
3. 의학적 정확성 유지
4. 일상 용어 사용
5. 희망적 마무리
"""
```

#### 6) 퀴즈 생성 프롬프트
```python
QUIZ_GENERATION_PROMPT = """
CKD 환자 교육용 퀴즈 5개를 생성하세요.

주제: {topic}
난이도: {difficulty}

퀴즈 유형:
1. OX 문제 2개
2. 4지선다 2개
3. 비교 문제 1개

예시:
Q: 다음 중 칼륨이 가장 높은 과일은?
A: 1)바나나 2)사과 3)포도 4)배
정답: 1
해설: 바나나는 100g당 칼륨 358mg으로...

교육 목표:
- 일상 식품의 영양소 인식
- 대체 식품 학습
- 조리법 이해
"""
```

### 10.2 프롬프트 최적화 기법

```python
class PromptOptimizer:
    def __init__(self):
        self.templates = {}
        self.performance_metrics = {}
    
    def add_context(self, prompt, user_profile):
        """사용자 맞춤 컨텍스트 추가"""
        context = f"""
        환자 정보:
        - CKD 단계: {user_profile['ckd_stage']}
        - 투석 유형: {user_profile['dialysis_type']}
        - 일일 제한: K {user_profile['k_limit']}mg
        """
        return context + prompt
    
    def add_examples(self, prompt, examples):
        """Few-shot 예시 추가"""
        example_text = "\n예시:\n"
        for ex in examples:
            example_text += f"입력: {ex['input']}\n"
            example_text += f"출력: {ex['output']}\n\n"
        return prompt + example_text
    
    def chain_prompts(self, prompts):
        """프롬프트 체이닝"""
        results = []
        for prompt in prompts:
            result = self.execute_prompt(prompt, 
                                        previous=results)
            results.append(result)
        return results
```

## 11. 데이터 소스 및 전처리

### 11.1 데이터 소스

#### 공공 데이터
| 소스 | URL | 활용 내용 |
|------|-----|-----------|
| 식품의약품안전처 | https://various.foodsafetykorea.go.kr/ | 영양성분 DB |
| AI 허브 | https://aihub.or.kr | 음식 이미지-레시피 데이터 |
| 국가표준식품성분표 | 농촌진흥청 | 250426공개 버전 |

#### 전문 자료
| 소스 | 문서명 | 활용 내용 |
|------|--------|-----------|
| 대한신장학회 | 혈액투석 환자를 위한 영양-식생활 관리 | 가이드라인, 레시피 |
| 영양사협회 | https://www.kdclub.com | 전문 식단 정보 |

#### 참고 서비스
| 서비스 | URL | 벤치마킹 포인트 |
|--------|-----|----------------|
| 메디솔라 | https://www.medisola.co.kr | UI/UX, 식단 검색 |
| 그리팅 | https://www.greating.co.kr | 맞춤 식단 추천 |

### 11.2 데이터 전처리 파이프라인

```python
class DataPreprocessor:
    def __init__(self):
        self.food_db = None
        self.synonym_dict = {}
    
    def preprocess_pipeline(self):
        """전체 전처리 파이프라인"""
        steps = [
            self.load_raw_data,
            self.clean_food_names,
            self.standardize_units,
            self.fill_missing_values,
            self.create_embeddings,
            self.validate_data
        ]
        
        for step in steps:
            print(f"실행 중: {step.__name__}")
            step()
    
    def clean_food_names(self):
        """재료명 정제"""
        # 1. 유사어 통합
        synonyms = {
            '피망': ['파프리카', '단고추'],
            '감자': ['포테이토', '알감자'],
            '당근': ['홍당무', 'carrot']
        }
        
        # 2. 특수문자 제거
        # 3. 표준명 매핑
        
    def standardize_units(self):
        """단위 표준화"""
        unit_conversions = {
            '1컵': 200,  # g
            '1큰술': 15,  # g
            '1작은술': 5,  # g
            '1개(중)': 100  # g (평균)
        }
        
    def fill_missing_values(self):
        """결측치 보간"""
        # 1. 동일 카테고리 평균값
        # 2. 유사 식품 참조
        # 3. 영양학적 추정
```

## 12. API 명세

### 12.1 RESTful API 엔드포인트

```yaml
# FastAPI 엔드포인트 (AI 서비스)
/api/v1/ai:
  /analyze-image:
    method: POST
    body: multipart/form-data (image file)
    response: {
      dish_name: string,
      ingredients: array,
      nutrition: object,
      safety_level: string
    }
  
  /analyze-recipe:
    method: POST
    body: {recipe_text: string}
    response: {
      parsed_ingredients: array,
      total_nutrition: object,
      suggestions: array
    }
  
  /get-substitutes:
    method: POST
    body: {food_id: integer, reason: string}
    response: {
      substitutes: array[{
        food_id: integer,
        name: string,
        reduction_percent: float
      }]
    }
  
  /generate-recipe:
    method: POST
    body: {
      original_recipe_id: integer,
      substituted_ingredients: array
    }
    response: {
      new_recipe: object,
      nutrition_comparison: object
    }

# Nest.js 엔드포인트 (비즈니스 로직)
/api/v1:
  /auth:
    /register: POST
    /login: POST
    /refresh: POST
    /logout: POST
  
  /users:
    /profile: GET, PUT
    /settings: GET, PUT
    /history: GET
  
  /recipes:
    /: GET (list), POST (create)
    /{id}: GET, PUT, DELETE
    /{id}/favorite: POST, DELETE
  
  /foods:
    /search: GET
    /{id}: GET
    /categories: GET
```

### 12.2 WebSocket 이벤트 (실시간 기능)

```javascript
// Socket.IO 이벤트
socket.on('analyze:start', (data) => {
  // 분석 시작 알림
});

socket.on('analyze:progress', (data) => {
  // 진행률 업데이트
});

socket.on('analyze:complete', (data) => {
  // 분석 완료 및 결과
});

socket.on('quiz:answer', (data) => {
  // 퀴즈 답변 처리
});
```

## 13. 테스트 및 검증 계획

### 13.1 테스트 전략

| 테스트 유형 | 대상 | 도구 | 목표 커버리지 |
|------------|------|------|--------------|
| 단위 테스트 | 개별 함수/메서드 | Jest, pytest | 80% |
| 통합 테스트 | API 엔드포인트 | Supertest, FastAPI TestClient | 70% |
| E2E 테스트 | 사용자 시나리오 | Cypress, Playwright | 핵심 플로우 |
| 성능 테스트 | API 응답시간 | K6, Locust | <3초 |
| 부하 테스트 | 동시 사용자 | Apache JMeter | 1000 동시접속 |

### 13.2 검증 메트릭

```python
class ValidationMetrics:
    """검증 지표 관리"""
    
    @staticmethod
    def nutrition_accuracy(predicted, actual):
        """영양성분 분석 정확도"""
        mape = mean_absolute_percentage_error(actual, predicted)
        return 100 - mape
    
    @staticmethod
    def substitute_relevance(original, substitute):
        """대체재 적합도"""
        # 1. 영양소 감소율
        k_reduction = (original.k - substitute.k) / original.k
        p_reduction = (original.p - substitute.p) / original.p
        
        # 2. 카테고리 일치도
        category_match = original.category == substitute.category
        
        # 3. 벡터 유사도
        similarity = cosine_similarity(
            original.embedding, 
            substitute.embedding
        )
        
        return {
            'nutrient_reduction': (k_reduction + p_reduction) / 2,
            'category_match': category_match,
            'similarity': similarity,
            'overall': weighted_average(...)
        }
```

## 14. 보안 및 규제 준수

### 14.1 보안 요구사항

| 영역 | 요구사항 | 구현 방법 |
|------|----------|-----------|
| 인증 | 안전한 사용자 인증 | JWT + Refresh Token |
| 권한 | 역할 기반 접근 제어 | RBAC in Nest.js |
| 암호화 | 민감 데이터 보호 | AES-256, bcrypt |
| 통신 | 암호화된 전송 | HTTPS, TLS 1.3 |
| 개인정보 | GDPR/KISA 준수 | 암호화, 가명화 |
| 로깅 | 감사 추적 | Structured logging |

### 14.2 의료 정보 관련 규제

```
주의사항:
1. 의료 행위 금지 조항 준수
   - 진단/처방 금지
   - "참고용" 명시
   - 의사 상담 권유

2. 책임 한계 고지
   - 이용약관에 명시
   - 각 결과에 면책조항

3. 데이터 정확성
   - 출처 명시
   - 정기적 검증
   - 업데이트 이력
```

## 15. 개발 로드맵

### 15.1 Phase 1: MVP (4주)

**Week 1-2: 기반 구축**
- [ ] 프로젝트 설정 (Next.js, FastAPI, Nest.js)
- [ ] DB 스키마 구축
- [ ] 기본 인증 시스템
- [ ] 영양성분 데이터 임포트

**Week 3-4: 핵심 기능**
- [ ] 이미지 업로드 및 분석
- [ ] 텍스트 레시피 파싱
- [ ] 영양성분 계산
- [ ] 안전도 판정 UI

### 15.2 Phase 2: AI 강화 (4주)

**Week 5-6: LLM 통합**
- [ ] GPT API 연동
- [ ] 프롬프트 최적화
- [ ] 대체재료 추천 알고리즘
- [ ] 레시피 생성 기능

**Week 7-8: 고급 기능**
- [ ] 벡터 DB 구축
- [ ] RAG 시스템
- [ ] 퀴즈 생성
- [ ] Streamlit 대시보드

### 15.3 Phase 3: 최적화 (4주)

**Week 9-10: 성능 개선**
- [ ] 캐싱 전략
- [ ] 쿼리 최적화
- [ ] 응답시간 개선
- [ ] 비동기 처리

**Week 11-12: 사용성 개선**
- [ ] UI/UX 개선
- [ ] 모바일 최적화
- [ ] A/B 테스트
- [ ] 사용자 피드백 반영

### 15.4 Phase 4: 확장 (추가)

- [ ] 의료기관 API
- [ ] 모바일 앱 (React Native)
- [ ] 음성 인터페이스
- [ ] 다국어 지원
- [ ] B2B 기능

## 16. 리스크 관리

### 16.1 기술적 리스크

| 리스크 | 발생확률 | 영향도 | 대응 방안 |
|--------|---------|--------|-----------|
| LLM API 장애 | 중 | 높음 | 폴백 시스템, 캐싱 |
| 데이터 정확성 오류 | 중 | 높음 | 다중 검증, 전문가 검수 |
| 확장성 문제 | 낮음 | 중간 | 마이크로서비스, 오토스케일링 |
| 보안 침해 | 낮음 | 높음 | 정기 보안 감사, 모니터링 |

### 16.2 비즈니스 리스크

| 리스크 | 대응 전략 |
|--------|-----------|
| 의료 책임 이슈 | 법률 검토, 면책조항, 보험 |
| 사용자 확보 실패 | 의료기관 파트너십, 마케팅 |
| 경쟁 서비스 등장 | 차별화 기능, 빠른 개선 |
| 수익화 어려움 | 다양한 BM (B2C, B2B, 구독) |

## 17. 성과 측정 (KPI)

### 17.1 제품 지표

| 지표 | 목표 (3개월) | 목표 (6개월) | 측정 방법 |
|------|-------------|-------------|-----------|
| DAU | 100명 | 500명 | Google Analytics |
| MAU | 500명 | 2,000명 | Google Analytics |
| 평균 세션 시간 | 5분 | 8분 | 앱 내 측정 |
| 재방문율 | 40% | 60% | 코호트 분석 |
| NPS | 40 | 60 | 설문조사 |

### 17.2 기술 지표

| 지표 | 목표 | 측정 도구 |
|------|------|-----------|
| API 응답시간 (p95) | <3초 | DataDog |
| 에러율 | <1% | Sentry |
| 가용성 | 99.5% | UptimeRobot |
| 분석 정확도 | 90% | 자체 평가 |

### 17.3 비즈니스 지표

| 지표 | 3개월 | 6개월 | 12개월 |
|------|--------|--------|---------|
| 가입자 수 | 500 | 2,000 | 10,000 |
| 유료 전환율 | - | 5% | 10% |
| MRR | - | $2,000 | $10,000 |
| CAC | $20 | $15 | $10 |
| LTV | $50 | $100 | $200 |

## 18. 팀 구성 및 역할

### 18.1 개발팀 구성

| 역할 | 인원 | 주요 책임 | 필요 스킬 |
|------|------|-----------|-----------|
| **PM/PO** | 1 | 제품 전략, 요구사항 | 프로젝트 관리, 도메인 지식 |
| **Tech Lead** | 1 | 기술 아키텍처, 코드 리뷰 | 풀스택, 시스템 설계 |
| **Frontend** | 2 | UI 개발, UX 구현 | React, Next.js, TypeScript |
| **Backend** | 2 | API 개발, 비즈니스 로직 | Node.js, Python, DB |
| **AI/ML** | 1 | LLM 통합, 프롬프트 | Python, LangChain, NLP |
| **데이터** | 1 | DB 관리, ETL | SQL, MongoDB, 전처리 |
| **QA** | 1 | 테스트, 품질 관리 | 자동화 테스트, 도메인 지식 |
| **디자이너** | 1 | UI/UX 디자인 | Figma, 웹 디자인 |

### 18.2 협업 체계

```
스프린트: 2주 단위
일일 스탠드업: 오전 10시
스프린트 리뷰: 금요일 오후
레트로스펙티브: 격주 금요일

도구:
- 소스 관리: GitHub
- 프로젝트: Jira/Linear
- 커뮤니케이션: Slack
- 문서: Notion
- 디자인: Figma
```

## 19. 예산 계획

### 19.1 초기 투자 (3개월)

| 항목 | 월 비용 | 3개월 총액 | 비고 |
|------|---------|------------|------|
| **인프라** | | | |
| AWS/GCP | $300 | $900 | EC2, RDS, S3 |
| MongoDB Atlas | $100 | $300 | M10 클러스터 |
| Vercel/Netlify | $50 | $150 | Frontend 호스팅 |
| **API/서비스** | | | |
| OpenAI GPT-4 | $500 | $1,500 | 예상 사용량 |
| 도메인/SSL | $20 | $60 | 연간 계약 |
| **개발 도구** | | | |
| GitHub | $50 | $150 | Team 플랜 |
| 모니터링 | $100 | $300 | DataDog, Sentry |
| **마케팅** | | | |
| 광고 | $200 | $600 | 초기 사용자 확보 |
| **총계** | $1,320 | $3,960 | |

### 19.2 운영 비용 (월)

| 항목 | 비용 | 비고 |
|------|------|------|
| 인프라 | $500-1,000 | 스케일링 대응 |
| API 사용료 | $500-2,000 | 사용량 증가 |
| 인건비 | $15,000 | 팀 규모별 |
| 마케팅 | $500 | 지속적 홍보 |
| 기타 | $500 | 라이선스, 도구 |

## 20. 마케팅 전략

### 20.1 타겟 채널

| 채널 | 전략 | KPI |
|------|------|-----|
| **의료기관** | B2B 파트너십 | 계약 3곳 |
| **환자 커뮤니티** | 콘텐츠 마케팅 | 회원 500명 |
| **SNS** | 교육 콘텐츠 | 팔로워 1,000명 |
| **검색 광고** | 키워드 광고 | CTR 3% |
| **앱스토어** | ASO 최적화 | 다운로드 1,000 |

### 20.2 컨텐츠 전략

```
주간 콘텐츠:
- 월: 저칼륨 레시피 소개
- 수: 영양 정보 카드뉴스
- 금: 사용자 성공 사례

월간 이벤트:
- 레시피 공모전
- 영양 퀴즈 대회
- 전문가 웨비나
```

## 21. 성공 요인

### 21.1 핵심 성공 요인 (CSF)

1. **데이터 정확성**: 신뢰할 수 있는 영양 정보
2. **사용자 경험**: 직관적이고 빠른 인터페이스
3. **AI 품질**: 정확한 분석과 유용한 추천
4. **의료 신뢰성**: 전문가 검증 및 인증
5. **커뮤니티**: 활발한 사용자 참여

### 21.2 차별화 포인트

| 경쟁사 | 우리의 차별점 |
|--------|--------------|
| 일반 식단 앱 | CKD 특화, 칼륨/인 데이터 |
| 의료 앱 | AI 기반 즉시 분석 |
| 영양 계산기 | 대체 레시피 자동 생성 |

## 22. 부록

### 22.1 용어 정의

| 용어 | 설명 |
|------|------|
| CKD | Chronic Kidney Disease (만성콩팥병) |
| 칼륨 (K) | 신장 기능 저하 시 제한 필요한 무기질 |
| 인 (P) | 뼈 건강과 관련, 과다 시 혈관 석회화 |
| 혈액투석 | 기계로 혈액을 정화하는 치료 |
| 복막투석 | 복막을 이용한 투석 |
| KFCT | 한국 식품 성분표 |
| RAG | Retrieval-Augmented Generation |

### 22.2 참고 자료

- 대한신장학회: https://ksn.or.kr
- 식품의약품안전처: https://mfds.go.kr
- CKD 가이드라인: KDIGO 2024
- 영양 데이터베이스: 농촌진흥청 국가표준식품성분DB

### 22.3 연락처

- 프로젝트 매니저: pm@kongdak.com
- 기술 지원: tech@kongdak.com
- 비즈니스 문의: biz@kongdak.com

---

**문서 정보**
- 버전: 2.0 (완전판)
- 최종 수정: 2025-01-17
- 작성: 콩닥 식탁 개발팀
- 상태: DRAFT
- 다음 리뷰: 2025-01-24

**변경 이력**
- v2.0 (2025-01-17): 전체 내용 통합 및 상세화
- v1.0 (2025-01-15): 초안 작성

---

*이 문서는 콩닥 식탁 프로젝트의 기획 및 개발 가이드입니다.*
*정기적으로 업데이트되며, 최신 버전은 프로젝트 저장소에서 확인하세요.*