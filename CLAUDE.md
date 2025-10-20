# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

이 프로젝트는 **신장질환(CKD) 환자를 위한 LLM 기반 영양 관리 챗봇**입니다. RAG(Retrieval-Augmented Generation)와 LangGraph를 활용하여 맞춤형 영양 정보 제공, 조리법 요약, 학습 문제 생성, 식재료 대체재 추천 기능을 제공합니다.

- **프로젝트 기간**: 2025.10.16 ~ 2025.10.22 (1주)
- **핵심 기술**: LangChain, LangGraph, OpenAI API, FAISS, RAG
- **특화 영역**: 신장질환 환자를 위한 저칼륨/저나트륨/저인 식단 관리

## 핵심 명령어

### 개발 환경 설정

```bash
# Conda 가상환경 생성 및 활성화
conda create --prefix ./venv python=3.11
conda activate ./venv

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
cp .env.example .env
# .env 파일에 OPENAI_API_KEY, TAVILY_API_KEY 등 설정
```

### RAG 시스템 초기화

```bash
# 벡터스토어 생성/재생성
python -c "from src.rag.rag_setup import RAGSetup; rag = RAGSetup(); rag.setup_rag(force_rebuild=True)"

# 기존 벡터스토어 로드
python -c "from src.rag.rag_setup import RAGSetup; rag = RAGSetup(); rag.setup_rag(force_rebuild=False)"
```

### 테스트 실행

```bash
# 통합 워크플로우 테스트 (4가지 시나리오)
python test_modularized.py

# 개별 체인 테스트
python -c "from src.chains import create_intent_classifier; clf = create_intent_classifier(); print(clf.invoke({'query': '김치찌개 재료 추천해줘'}))"
```

### FastAPI 백엔드 실행 (향후 구축)

```bash
cd src/backend
uvicorn main:app --reload --port 8000
```

### Streamlit 프론트엔드 실행 (향후 구축)

```bash
cd streamlit_app
streamlit run main.py
```

## 아키텍처 개요

### 디렉토리 구조

```
ChatBot_Jehun/
├── src/
│   ├── chains/              # LangChain 체인들
│   │   ├── common.py        # LLM 초기화, 컨텍스트 검색
│   │   ├── intent_classifier.py  # 의도 분류 (recommendation/summary/quiz)
│   │   ├── summary.py       # 조리법 요약 + Q&A 생성
│   │   ├── quiz.py          # 문제 생성 (객관식 2개, 주관식 1개)
│   │   └── recommendation.py # 재료 대체재 추천
│   ├── rag/
│   │   ├── rag_setup.py     # PDF → 벡터스토어 초기화
│   │   └── retriever.py     # 문서 검색 (basic/mmr/compression)
│   ├── workflow/
│   │   └── workflow.py      # LangGraph 워크플로우 (조건부 라우팅)
│   └── utils/
│       └── web_search.py    # Tavily 웹 검색 (RAG Fallback)
├── data/
│   ├── pdf/                 # 입력 PDF 문서
│   ├── preprocess/          # 전처리된 CSV (식품/레시피)
│   └── vectorstore/         # FAISS 벡터스토어
└── test_modularized.py      # 통합 테스트 스크립트
```

### 데이터 흐름

```
사용자 쿼리
    ↓
[의도 분류] (intent_classifier)
    ↓
┌──────────────┬──────────────┬──────────────┐
│Recommendation│   Summary    │    Quiz      │
│(재료 대체제) │(조리법/주의) │(문제 생성)   │
└──────┬───────┴──────┬───────┴──────┬───────┘
       ↓              ↓              ↓
   [RAG 검색] + [웹 검색 Fallback]
       ↓              ↓              ↓
   [LLM 처리] (각 체인별 프롬프트)
       ↓              ↓              ↓
   [결과 반환]
```

**조건부 라우팅 특징**:
- `recommendation` → 필요시 `summary` 추가 (LLM이 `need_summary` 플래그 판단)
- `summary`, `quiz` → 직접 종료

### RAG 시스템

**벡터스토어**: FAISS (CPU 기반)
**임베딩 모델**: OpenAI `text-embedding-3-small`
**청크 설정**: `chunk_size=300`, `chunk_overlap=30` (기본값은 1000/200)

**3가지 검색 모드**:
- `basic`: 유사도 검색
- `mmr`: Maximum Marginal Relevance (다양성 고려)
- `compression`: LLM 기반 압축 검색

**Fallback 메커니즘**:
- RAG 결과 부족 → Tavily 웹 검색 자동 보충

### LangGraph 워크플로우

**상태 정의** (`WorkflowState`):
```python
- query (필수): 사용자 입력
- intent: 의도 분류 결과
- recommendation_result: 추천 결과
- final_result: 최종 결과
- need_summary: 요약 필요 여부 (LLM 판단)
```

**노드 구조**:
```
classifier → route_intent →
├─ recommendation → route_after_recommendation →
│   ├─ summary → END
│   └─ END
├─ summary → END
└─ quiz → END
```

## 코딩 컨벤션 및 패턴

### 체인 생성 패턴

모든 체인은 다음 패턴을 따릅니다:

```python
def create_[chain_name]_chain(
    retriever,  # RAG retriever (필요시)
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
):
    """
    체인 설명

    Args:
        retriever: RAG 벡터스토어 리트리버
        model: LLM 모델명
        temperature: 응답의 창의성 (0~1)
        max_tokens: 최대 토큰 수

    Returns:
        RunnableSequence: 실행 가능한 체인
    """
    llm = get_llm(model=model, temperature=temperature, max_tokens=max_tokens)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "시스템 프롬프트..."),
        ("user", "{query}")
    ])

    return prompt | llm | StrOutputParser()
```

### 프롬프트 엔지니어링 원칙

1. **역할 정의 명확화**: "당신은 신장질환 환자 영양 관리 전문가입니다"
2. **출력 형식 지정**: 마크다운 리스트, JSON 등 구체적 형식 명시
3. **도메인 가이드라인 임베딩**: 칼륨/나트륨/인 제한 수치 명시
4. **Few-shot 예시 활용**: 예상 출력 형식 예시 제공

### 에러 처리

```python
try:
    result = chain.invoke({"query": user_query})
except Exception as e:
    logger.error(f"체인 실행 오류: {e}")
    return "죄송합니다. 응답을 생성할 수 없습니다."
```

## 도메인 지식

### 신장질환 영양 기준 (CKD Guidelines)

| 영양소 | 투석 전 | 투석 중 | 이식 후 |
|-------|--------|--------|--------|
| 단백질 | 0.6-0.8g/kg | 1.2-1.3g/kg | 0.8-1.0g/kg |
| 나트륨 | <5g/일 | <6g/일 | <6g/일 |
| 칼륨 | <2000mg/일 | <2000mg/일 | 조정 |
| 인 | <800mg/일 | <1000mg/일 | <1200mg/일 |
| 칼로리 | 30-35kcal/kg | 30-35kcal/kg | 30kcal/kg |

**위험도 표시**:
- 녹색 (0-80%): 안전
- 노란색 (80-100%): 주의
- 빨간색 (>100%): 위험

### 의도 분류 기준

1. **recommendation**: 재료 대체제, 대체 식품 추천 요청
   - 예: "김치찌개에서 저칼륨 재료로 뭐 쓸 수 있어?"

2. **summary**: 조리법, 주의사항, 정보 제공 요청
   - 예: "혈액투석 환자 식사 관리 주의사항은?"

3. **quiz**: 문제 출제 요청
   - 예: "저염식에 대한 퀴즈 3개 만들어줘"

## 테스트 시나리오

`test_modularized.py`에 포함된 4가지 테스트:

```python
test_queries = [
    "김치찌개 만들 때 저칼륨 재료로 대체할 수 있는 게 뭐야?",
    # → recommendation

    "된장찌개 만드는 법을 저칼륨으로 어떻게 해야 하고 주의할 점은?",
    # → recommendation + summary (조건부)

    "혈액투석 환자의 식사 관리 주의사항 요약해줘",
    # → summary

    "저염식에 대한 퀴즈 3개 만들어줘",
    # → quiz (객관식 2개, 주관식 1개)
]
```

## Git 워크플로우 규칙

**필수 절차**:
```bash
git pull origin main      # 1. 항상 pull 먼저
git add .                 # 2. 변경사항 스테이징
git commit -m "메시지"    # 3. 커밋 (한글 메시지)
git push origin main      # 4. 푸시
```

**커밋 메시지**: 한글로 작성
**충돌 발생 시**: 수동 해결 후 재커밋

## 환경변수 (.env)

```bash
OPENAI_API_KEY=sk-...                    # 필수
ANTHROPIC_API_KEY=sk-ant-...             # 선택
TAVILY_API_KEY=tvly-...                  # 선택 (웹 검색용)
OPENAI_MODEL=gpt-4o-mini                 # 기본 모델
VECTORSTORE_PATH=./data/vectorstore      # 벡터스토어 경로
```

## 향후 구축 예정

1. **FastAPI 백엔드**: RESTful API 엔드포인트
   - `POST /api/chat`: 텍스트 쿼리 처리
   - `POST /api/chat/image`: 이미지 분석 (Vision API)
   - `GET /health`: 상태 체크

2. **Streamlit 프론트엔드**: 3개 페이지
   - 텍스트 쿼리
   - 이미지 분석
   - 영양 정보 조회

3. **MongoDB 통합**: CSV 데이터 영구 저장
   - `foods` 컬렉션
   - `recipes` 컬렉션

4. **이미지 분석**: OpenAI Vision API로 음식 사진 분석

## 주요 의존성

```
langchain>=0.1.0
langchain-openai
langchain-community
langgraph
faiss-cpu
pypdf
tavily-python
python-dotenv
pydantic
pandas
```

## 참고 문서

- [LangChain 공식 문서](https://python.langchain.com/)
- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Tavily Search API](https://docs.tavily.com/)
