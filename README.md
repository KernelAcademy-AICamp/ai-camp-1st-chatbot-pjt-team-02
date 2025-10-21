# 🍲 콩닥식탁 - AI 기반 신장 투석 환자 맞춤형 식단 관리 챗봇

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.0.340-green)](https://python.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange)](https://openai.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green)](https://www.mongodb.com/atlas)

## 📋 프로젝트 개요

**콩닥식탁**은 신장 투석 환자를 위한 AI 기반 맞춤형 식단 관리 챗봇입니다. RAG(Retrieval-Augmented Generation) 기술과 MongoDB를 활용하여 환자가 안전하게 즐길 수 있는 레시피와 대체 재료를 추천합니다.

### 주요 특징
- 🎯 **맞춤형 대체재 추천**: MongoDB 기반 5만개 이상의 검증된 대체 재료 데이터베이스
- 📊 **영양 성분 분석**: 나트륨, 칼륨, 인, 단백질 자동 계산
- 🤖 **RAG 시스템**: 식약처/대한신장학회 PDF 학습 기반 정확한 정보 제공
- 📝 **LangGraph 워크플로우**: 자동 의도 분류 및 적절한 처리 체인 선택

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 저장소 클론
git clone https://github.com/KernelAcademy-AICamp/ai-camp-1st-chatbot-pjt-team-02.git
cd ai-camp-1st-chatbot-pjt-team-02
```

#### 옵션 A: Conda 환경 (권장)
```bash
# Conda 환경 생성 (Python 3.11)
conda create --prefix .conda_chatbot python=3.11
conda activate ./.conda_chatbot

# 패키지 설치
pip install -r requirements.txt
```

#### 옵션 B: venv 환경
```bash
# Python 3.11이 설치되어 있는지 확인
python3.11 --version

# venv 가상환경 생성
python3.11 -m venv venv

# 가상환경 활성화
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일 생성:
```bash
# OpenAI
OPENAI_API_KEY=your-openai-api-key

# MongoDB Atlas
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

# 선택사항
ANTHROPIC_API_KEY=your-anthropic-key  # Claude 사용 시
TAVILY_API_KEY=your-tavily-key  # 웹 검색 사용 시
```

### 3. MongoDB 대체재 데이터 업로드
```bash
# MongoDB에 대체재 데이터 업로드
python scripts/upload_alternatives_to_mongodb.py
```

### 4. Jupyter Notebook 실행
```bash
# Jupyter 서버 시작 (출력 제한 해제)
cd tutorial
./start_jupyter_no_limit.sh

# 또는 일반 실행
jupyter notebook
```

## 📁 프로젝트 구조

```
ChatBot_Jehun/
├── src/                      # 핵심 소스 코드
│   ├── rag/                 # RAG 시스템
│   │   ├── rag_setup.py    # 벡터스토어 설정
│   │   └── retriever.py    # 문서 검색
│   └── utils/               # 유틸리티
│       ├── alternative_search.py  # MongoDB 대체재 검색 ⭐
│       ├── mongodb_client.py      # MongoDB 연결
│       └── web_search.py         # 웹 검색 (Tavily)
│
├── tutorial/                # 실습 및 테스트
│   ├── tutorial_rag.ipynb # 메인 실습 노트북 ⭐
│   ├── start_jupyter_no_limit.sh  # Jupyter 실행 스크립트
│   └── test_mongodb_output.py     # MongoDB 테스트
│
├── scripts/                 # 데이터 관리 스크립트
│   └── upload_alternatives_to_mongodb.py  # MongoDB 업로드
│
├── data/                    # 데이터 저장소
│   ├── pdf/                # 학습용 PDF 문서
│   ├── vectorstore/        # FAISS 벡터 DB
│   └── alternatives/       # 대체재 엑셀 데이터
│
├── .env.example            # 환경 변수 템플릿
├── requirements.txt        # 패키지 의존성
├── CLAUDE.md              # Claude Code 가이드
└── README.md              # 프로젝트 문서
```

## 💻 주요 기능 상세

### 1. MongoDB 대체재 검색 시스템
```python
# src/utils/alternative_search.py
search_alternatives_from_mongodb(
    ingredients=['김치', '돼지고기'],  # 검색할 재료
    max_per_ingredient=3              # 재료당 최대 대체재 수
)
```
- **국가표준식품성분표 기반 53,871개 대체재 데이터**
- 영양소별 감소율 자동 계산 (나트륨, 칼륨, 인, 단백질)
- 실시간 검색 및 캐싱
- context 최상단에 배치하여 LLM 우선 참조

### 2. RAG 시스템 (PDF 학습)
```python
# src/rag/rag_setup.py
rag_setup = RAGSetup(
    pdf_directory="data/pdf",
    vectorstore_path="data/vectorstore",
    chunk_size=300
)
vectorstore = rag_setup.setup_rag()
```
- 식약처, 대한신장학회 공식 PDF 문서 학습
- FAISS 벡터 DB로 빠른 검색
- OpenAI Embeddings 활용
- 문서 부족 시 웹 검색 Fallback

### 3. LangGraph 워크플로우
```python
# tutorial/tutorial_rag.ipynb - cell-17~19
workflow = StateGraph(WorkflowState)
workflow.add_node("classifier", classify_intent)
workflow.add_node("recommendation", run_recommendation)
workflow.add_node("summary", run_summary)
workflow.add_node("quiz", run_quiz)
```
- **자동 의도 분류**: 추천/요약/퀴즈 자동 라우팅
- **체인별 독립 실행**: 각 기능별 최적화된 처리
- **상태 관리**: 워크플로우 상태 추적

## 📊 영양소 제한 기준

### 신장 투석 환자 일일 권장량
| 영양소 | 투석 전 | 투석 중 | 단위 |
|-------|---------|---------|------|
| 단백질 | 0.6-0.8 | 1.2-1.3 | g/kg |
| 나트륨 | < 5 | < 6 | g/일 |
| 칼륨 | < 2000 | < 2000 | mg/일 |
| 인 | < 800 | < 1000 | mg/일 |

### 위험도 평가 기준 (100g 기준)
- 🟢 **녹색** (안전): 칼륨 < 200mg, 인 < 100mg, 나트륨 < 100mg
- 🟡 **노란색** (주의): 칼륨 200-400mg, 인 100-200mg, 나트륨 100-500mg
- 🔴 **빨간색** (위험): 칼륨 > 400mg, 인 > 200mg, 나트륨 > 500mg

## 🧪 테스트 실행

### Jupyter Notebook 실습
1. `tutorial/tutorial_rag.ipynb` 열기
2. 순차적으로 셀 실행:

| 셀 번호 | 기능 | 설명 |
|--------|------|------|
| cell-3 | 환경 설정 | 프로젝트 경로 및 환경변수 로드 |
| cell-4 | 출력 설정 | Jupyter 출력 200줄 제한 해제 |
| cell-6 | RAG 초기화 | FAISS 벡터스토어 로드/생성 |
| cell-7 | 재료 추출 | 요리명 → 재료 및 영양 분석 |
| **cell-8** | **MongoDB 통합** | **대체재 검색 + RAG + 웹 검색** ⭐ |
| cell-11 | 디버깅 | MongoDB 결과 확인용 |
| cell-12~14 | 요약/퀴즈 | 요약 및 퀴즈 생성 체인 |
| cell-17~19 | LangGraph | 워크플로우 구성 및 컴파일 |
| cell-23 | 통합 테스트 | 전체 워크플로우 테스트 |

### 테스트 스크립트
```bash
# MongoDB 출력 테스트
python tutorial/test_mongodb_output.py

# 결과는 mongodb_results.txt 파일로도 저장됨
```

## 🔧 문제 해결

### Jupyter 출력이 잘릴 때
```bash
# 출력 제한 없이 Jupyter 실행
./tutorial/start_jupyter_no_limit.sh

# 또는 수동 설정
jupyter notebook --NotebookApp.iopub_data_rate_limit=1e10 --NotebookApp.iopub_msg_rate_limit=1e10

# VSCode 사용 시: .vscode/settings.json에 설정 포함됨
```

### MongoDB 연결 실패
```python
# .env 파일 확인
MONGODB_URI=mongodb+srv://...

# 연결 테스트
from src.utils.mongodb_client import get_mongodb_client
client = get_mongodb_client()
```

### RAG 검색 결과 부족
```python
# 벡터스토어 재구축
rag_setup.setup_rag(force_rebuild=True)
```

### 디버깅 방법
```python
# cell-10에 ipdb 브레이크포인트 설정됨
# VSCode: 줄 번호 클릭 → Debug Cell 실행
# 단축키: F10(다음 줄), F11(함수 진입), F5(계속)
```

## 📚 학습 데이터

### PDF 문서 (data/pdf/)
- 2권_혈액투석_환자를_위한_영양-식생활_관리.pdf
- 대한신장학회_혈액투석_질환식_식단_레시피_가이드.pdf
- 식약처_나트륨줄이기자료집.pdf
- 식약처_삼삼한밥상7.pdf
- 신장질환_식품교환표-식사요법.pdf

### 대체재 데이터 (data/alternatives/)
- 국가표준식품성분표_기반_대체재.xlsx (53,871개)
- 영양소별 감소율 계산 포함

## 🎬 시연 시나리오

1. **채팅 예시**: "김치찌개 먹어도 될까요?"
   - 재료 자동 추출: 김치, 돼지고기, 두부 등
   - MongoDB에서 대체재 검색
   - 영양 분석 및 위험도 평가
   - 저나트륨 대체 레시피 제안

2. **워크플로우 테스트** (cell-23)
   - "된장찌개 만들 때 저칼륨 재료로 대체할 수 있는 게 뭐야?"
   - "혈액투석 환자의 식사 관리 주의사항 요약해줘"
   - "저염식에 대한 퀴즈 3개 만들어줘"

## 🤝 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Git 워크플로우

```bash
# 푸시 전 필수 규칙: Pull → 충돌 체크 → Commit → Push
git pull origin kimunsuk
git add .
git commit -m "변경 내용 설명"
git push origin kimunsuk
```

## 👥 팀 정보

**AI Camp 1기 ChatBot Project Team 02**
- 프로젝트 기간: 2025.10.16 ~ 2025.10.22
- 개발 브랜치: kimunsuk
- GitHub: [ai-camp-1st-chatbot-pjt-team-02](https://github.com/KernelAcademy-AICamp/ai-camp-1st-chatbot-pjt-team-02)

## 📚 참고 문서

### API 문서
- [OpenAI API](https://platform.openai.com/docs)
- [LangChain 문서](https://python.langchain.com/)
- [MongoDB Atlas](https://www.mongodb.com/atlas)

### 의료 정보
- [대한신장학회](https://www.ksn.or.kr/)
- [식품의약품안전처](https://www.mfds.go.kr/)
- [국가표준식품성분표](https://various.foodsafetykorea.go.kr/nutrient/)

---
*본 프로젝트는 FastCampus AI Camp 1기 과정의 일환으로 개발되었습니다.*