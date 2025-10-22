# NutriCoach - AI 기반 신장 투석 환자 영양 관리 챗봇

신장질환 환자(특히 투석 환자)의 맞춤형 식단 관리와 영양 교육을 지원하는 AI 챗봇 서비스입니다.

## 🎯 주요 기능

### 1️⃣ 재료 대체 추천 (Ingredient Substitution)
- 사용자가 원하는 음식의 저칼륨, 저나트륨 재료 대체안 제시
- 신장질환 환자에게 안전한 식재료 추천

### 2️⃣ 식단 정보 요약 (Dietary Information Summary)
- PDF, 이미지, 텍스트 기반 식단 정보 분석 및 요약
- 조리법 및 영양 정보 제공

### 3️⃣ 영양 학습 문제 생성 (Nutrition Quiz)
- 맞춤형 교육 문제 자동 생성
- 객관식 2문항, 주관식 1문항 구성

## 🏗️ 프로젝트 구조

```
├── app.py                          # Streamlit 프론트엔드
├── app_multimodal.py              # 멀티모달 기능 지원 앱
├── src/
│   ├── backend/
│   │   ├── main.py               # FastAPI 서버
│   │   ├── models.py             # 데이터 모델
│   │   └── routes/               # API 엔드포인트
│   ├── chains/                   # LangChain 체인
│   │   ├── intent_classifier.py  # 의도 분류
│   │   ├── quiz.py              # 퀴즈 생성
│   │   ├── summary.py           # 요약 생성
│   │   └── recommendation.py    # 재료 추천
│   ├── workflow/
│   │   ├── workflow.py          # LangGraph 메인 워크플로우
│   │   └── recommendation_subgraph.py
│   ├── rag/                     # RAG 시스템
│   │   ├── rag_setup.py
│   │   └── retriever.py
│   ├── database/                # 데이터베이스
│   │   └── mongo_client.py
│   ├── tools/                   # 유틸리티 도구
│   ├── utils/                   # 헬퍼 함수
│   └── preprocess/              # 데이터 전처리
├── data/
│   ├── pdf/                     # PDF 문서
│   ├── vectorstore/             # FAISS 벡터 저장소
│   └── preprocess/              # 전처리 데이터
└── requirements.txt
```

## 🚀 설치 및 실행

### 사전 요구사항
- Python 3.10 이상
- OpenAI API 키
- MongoDB (선택사항)

### 설치

```bash
# 1. 저장소 클론
git clone https://github.com/KernelAcademy-AICamp/ai-camp-1st-chatbot-pjt-team-02
cd ai-camp-1st-chatbot-pjt-team-02

# 2. 가상 환경 생성
python -m venv venv
# 또는
python3 -m venv venv

source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일에서 OpenAI API 키 등 설정

# 5. 데이터 다운로드
# 다음 링크에서 data 폴더를 다운로드하여 프로젝트 루트에 배치하세요
# https://drive.google.com/file/d/1TUFj49JUWk-uIaHU_s0-j4riwgdq4JCJ/view?usp=sharing
```

### Streamlit 프론트엔드 실행

```bash
streamlit run app_multimodal.py
```

앱이 `http://localhost:8501`에서 실행됩니다.

### FastAPI 백엔드 실행

```bash
python -m uvicorn src.backend.main:app --reload
```

API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

## 🔧 주요 기술 스택

### LLM & AI
- **OpenAI**: GPT-4o-mini, GPT-4-Vision
- **LangChain**: LLM 체인 구축
- **LangGraph**: 멀티스텝 워크플로우 오케스트레이션
- **FAISS**: 벡터 기반 유사도 검색

### 프레임워크 & 서버
- **Streamlit**: 웹 UI
- **FastAPI**: REST API 서버
- **Uvicorn**: ASGI 서버

### 데이터베이스 & 저장소
- **MongoDB**: 음식 및 영양 정보 저장
- **FAISS**: 벡터 임베딩 저장

### 기타
- **pypdf**: PDF 텍스트 추출
- **PIL/Pillow**: 이미지 처리
- **Pandas**: CSV 데이터 처리
- **python-dotenv**: 환경 변수 관리

## 📋 환경 변수

`.env` 파일에 다음 정보를 설정하세요:

```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# MongoDB (선택사항)
MONGO_URI=mongodb://localhost:27017

# 기타 설정
LOG_LEVEL=INFO
```

## 🔄 워크플로우

1. **사용자 입력 처리**
   - 텍스트, PDF, 이미지 멀티모달 입력 지원

2. **의도 분류**
   - 사용자 질문의 의도 분류 (추천/요약/퀴즈)

3. **의도별 처리**
   - 추천: 재료 대체안 제시
   - 요약: 식단 정보 요약
   - 퀴즈: 교육 문제 생성

4. **RAG 검색**
   - MongoDB, CSV, PDF, 웹 검색을 통한 정보 수집
   - 관련 컨텍스트 제공

5. **응답 생성**
   - LLM을 통한 최종 답변 생성

## 📚 API 엔드포인트

### 텍스트 채팅
```
POST /chat/text
```

### PDF 분석
```
POST /chat/pdf
```

### 이미지 분석
```
POST /chat/image
```

### 헬스 체크
```
GET /health
GET /api/version
```

## 🎓 특징

- **멀티소스 정보 검색**: MongoDB, CSV, PDF, 웹 검색
- **멀티모달 입력**: 텍스트, PDF, 이미지 동시 처리
- **조건부 워크플로우**: 의도에 따른 동적 라우팅
- **컨텍스트 관리**: 다중 소스의 컨텍스트 통합
- **의료 정보 제공**: 신장질환 특화 식단 정보

## ⚠️ 주의사항

본 서비스는 **정보 제공 목적**이며, 의학적 진단이나 치료를 대체하지 않습니다.
항상 의료 전문가의 조언을 구하세요.

## 📝 라이센스

MIT License

## 👥 팀

AI Camp 1기 팀02

## 📞 문의

이슈 및 질문은 GitHub Issues를 통해 등록해주세요.
