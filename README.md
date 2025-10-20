# 🥗 콩닥식탁 - 신장 투석 환자 맞춤형 식단 관리 챗봇

신장 투석 환자를 위한 AI 기반 맞춤형 식단 관리 챗봇입니다. OpenAI GPT API와 RAG 기술을 활용하여 음식의 영양 성분을 분석하고, 안전한 대체 레시피를 제안합니다.

- **프로젝트 기간:** 2025.10.16 ~ 2025.10.22 (총 1주일)
- **배포 방식:** Docker Compose (로컬 환경)
- **프론트엔드:** http://localhost:8501
- **백엔드 API:** http://localhost:8000/api/docs

---

## 📌 주요 기능

### 1️⃣ 요약 및 Q&A 자동생성 [필수]
- **음식 영양 성분 분석**
  - "떡볶이 먹어도 될까요?" 같은 자연어 질문
  - LLM이 재료를 자동 추출 (떡, 고추장, 어묵, 파)
  - PostgreSQL에서 영양 정보 조회 및 계산
  - 나트륨, 칼륨, 인, 단백질, 칼로리 분석

- **위험도 평가**
  - 신장 환자 기준치 대비 평가 (🟢안전/🟡주의/🔴위험)
  - 초과 영양소 자동 감지

- **대체 레시피 제안**
  - RAG 기반 식약처/대한신장학회 가이드라인 검색
  - 저나트륨/저칼륨 대체 재료 추천
  - 조리 팁 제공

### 2️⃣ 맞춤형 퀴즈 생성 [필수]
- **학습 강화 퀴즈**
  - 객관식, 주관식, O/X 문제 자동 생성
  - 위험도 높은 음식 질문 시 퀴즈 제안
  - 정답/해설 즉시 피드백
  - 정답률 추적

### 3️⃣ 학습 자료 추천 [부가]
- **신뢰할 수 있는 자료 검색**
  - 식약처, 대한신장학회 등 공식 기관 자료
  - 웹 크롤링 기반 최신 자료 수집
  - 관련성 점수 평가 및 정렬

## 🎬 사용 시나리오

1. **채팅 탭**에서 "떡볶이 먹어도 될까요?" 질문
2. AI가 재료 분석 → 영양소 계산 → 위험도 평가
3. 나트륨 초과 경고 및 저염 레시피 제안
4. "📝 퀴즈로 복습하기" 버튼 클릭
5. **영양 분석 탭**에서 차트로 영양소 비율 확인
6. **학습 자료 탭**에서 "저염식 레시피" 검색

---

## **2. 활용 장비 및 협업 툴**

### **2.1 활용 장비**
- **개발 환경:** Windows 11 / macOS / Linux 기반 개인 PC
- **서버 환경:** Local 환경 구동 (필요시 Docker 컨테이너 활용)

### **2.2 협업 툴**
- **소스 관리:** GitHub
- **프로젝트 관리:** Notion, Jira
- **커뮤니케이션:** Slack, Discord
- **버전 관리:** Git

---

## **3. 최종 선정 AI 모델 구조**
- **모델 이름:** **OpenAI GPT-4o**, **Anthropic Claude 3** 등 (프로젝트에서 1종 이상 선택 활용)
- **구조 및 설명:** 본 프로젝트는 사전 학습된 LLM을 API 형태로 호출하여 사용합니다. 모델을 직접 학습하는 대신, **프롬프트 엔지니어링**을 통해 각 기능(요약, Q&A, 문제 생성)에 최적화된 결과물을 얻도록 제어하는 데 중점을 둡니다.
- **학습 데이터:** 사용자가 직접 입력하는 강의 노트, 기사, PDF 텍스트 등 비정형 데이터가 AI 모델의 주요 입력값으로 활용됩니다.
- **평가 지표:** 기능 요구사항 충족 여부를 기준으로 하며, 생성된 결과물(요약, 질문, 문제 등)의 **정확성, 일관성, 유용성**을 정성적으로 평가합니다.

---

## **4. 서비스 아키텍처**
### **4.1 시스템 구조도**
사용자 인터페이스(Streamlit)에서 입력을 받아 백엔드 서버(FastAPI)로 전달하고, 서버는 외부 LLM API와 통신하여 결과를 다시 사용자에게 보여주는 간단한 3-Tier 아키텍처를 따릅니다.
```
+------------------+      +---------------------+      +-----------------+
|   User (Client)  | <--> |   Backend Server    | <--> |  External LLM   |
| (Streamlit/Web)  |      | (FastAPI / Python)  |      | (OpenAI/Claude) |
+------------------+      +---------------------+      +-----------------+
```

### **4.2 데이터 흐름도**
1.  **사용자 입력:** 사용자가 UI를 통해 텍스트 문서를 입력합니다.
2.  **백엔드 요청:** Frontend(Streamlit)는 입력된 텍스트를 Backend(FastAPI) API로 전송합니다.
3.  **프롬프트 구성:** 백엔드는 사전에 설계된 프롬프트 템플릿에 사용자 텍스트를 결합합니다.
4.  **LLM API 호출:** 완성된 프롬프트를 OpenAI 또는 Claude API로 전송합니다.
5.  **결과 수신 및 파싱:** LLM이 생성한 응답(JSON, Bullet 형식)을 수신하여 파싱합니다.
6.  **결과 반환:** 파싱된 데이터를 UI가 표현하기 좋은 형태로 가공하여 Frontend로 반환합니다.

---

## **5. 사용 기술 스택**
### **5.1 백엔드**
- **Framework:** FastAPI (Python)
- **LLM API:** OpenAI, Anthropic

### **5.2 프론트엔드**
- **Framework:** Streamlit

### **5.3 머신러닝 및 데이터 분석**
- **LLM Libraries:** `openai`, `anthropic`
- **Data Handling:** `pandas` (필요시)

### **5.4 배포 및 운영**
- **Runtime Environment:** Python 3.9+
- **Containerization:** Docker (선택 사항)

---

## **6. 팀원 소개**


| ![박커널](https://avatars.githubusercontent.com/u/156163982?v=4) | ![이커널](https://avatars.githubusercontent.com/u/156163982?v=4) | ![최커널](https://avatars.githubusercontent.com/u/156163982?v=4) | ![김커널](https://avatars.githubusercontent.com/u/156163982?v=4) | 
| :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: | 
|            [박커널](https://github.com/)             |            [이커널](https://github.com/)             |            [최커널](https://github.com/)             |            [김커널](https://github.com/)             |   

---

## **7. Appendix**
### **7.1 참고 자료**
- **API 문서:** [OpenAI API Reference](https://platform.openai.com/docs/api-reference), [Anthropic API Documentation](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- **프레임워크:** [FastAPI 공식 문서](https://fastapi.tiangolo.com/), [Streamlit 공식 문서](https://docs.streamlit.io/)
- **프롬프트 가이드:** [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)

## 🚀 빠른 시작

<<<<<<< HEAD
### 1. 환경 설정
=======
2.  **가상환경 생성 및 활성화:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```
    ```bash ( 로컬 )
    conda create --prefix 환경이름 python=3.11
    conda env remove --prefix 환경이름  OR 그냥 지움
    conda activate 환경이름
    conda deactivate
    conda env list
    conda list   # 현재 환경의 패키지 목록 확인
    ```
>>>>>>> origin/main

```bash
# 1. Repository 클론
git clone https://github.com/KernelAcademy-AICamp/ai-camp-1st-chatbot-pjt-team-02.git
cd ChatBot

# 2. 환경 변수 설정
cp .env.example .env

### **7.3 Git 워크플로우**
**푸시 전 필수 규칙: 항상 Pull → 충돌 체크 → Commit → Push**
**커밋 메시지는 한글로 작성**
**LLM 에 커밋하고 푸쉬해라고 명령함**

```bash
# 1. 원격 저장소에서 최신 변경사항 가져오기 (충돌 체크)
git pull origin main

# 2. 변경사항 스테이징
git add .

# 3. 커밋
git commit -m "커밋 메시지"

# 4. 푸시
git push origin main
```

**충돌 발생 시 해결 방법:**
```bash
# 충돌 파일 확인
git status

# 충돌 수동 해결 후
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

### **7.4 주요 커밋 기록 및 업데이트 내역**

### 2. 데이터 초기화 (최초 1회)

**중요**: 이 프로젝트는 국가표준식품성분표 엑셀 파일에서 데이터를 읽어 PostgreSQL과 FAISS에 로드합니다.

```bash
# 자동 초기화 (권장)
cd scripts
./initialize_data.sh

# 수동 초기화
python3 scripts/load_excel_to_db.py         # 1. 국가표준식품성분표 → DB
python3 scripts/load_pdfs_to_faiss.py       # 2. FAISS 로드 (선택)
```

**필수 데이터 파일:**
- `Documents/Data/국가표준식품성분표_250426공개.xlsx` - **필수** (1000+ 식품 영양 정보)
- `Documents/Data/alternatives.xlsx` - 선택 (대체 재료 매핑, 직접 작성)
- `Documents/Data/*.pdf` - 선택 (RAG용 참고 문서)

자세한 내용: [DATA_INITIALIZATION.md](Documents/Data생성설명/DATA_INITIALIZATION.md)

### 3. 실행 방법

#### 방법 A: 자동 실행 스크립트 (권장)
```bash
# macOS/Linux
./start.sh

# Windows (Git Bash)
bash start.sh
```

#### 방법 B: Docker Compose 직접 실행
```bash
# 컨테이너 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 종료
docker-compose down
```

### 4. 접속 확인

- **프론트엔드 (Streamlit)**: http://localhost:8501
- **백엔드 API 문서**: http://localhost:8000/api/docs
- **PostgreSQL**: localhost:5432 (postgres/kongdak_db)

## 📁 프로젝트 구조

```
ChatBot/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py         # FastAPI 메인
│   │   ├── config.py       # 환경 설정
│   │   ├── models/         # DB 모델 & 스키마
│   │   ├── services/       # 비즈니스 로직
│   │   │   ├── llm_service.py      # OpenAI API
│   │   │   ├── rag_service.py      # FAISS RAG
│   │   │   ├── nutrition.py        # 영양 분석
│   │   │   └── scraper.py          # 웹 크롤링
│   │   ├── routers/        # API 라우터
│   │   └── utils/          # 프롬프트 관리
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # Streamlit 프론트엔드
│   ├── app.py              # 메인 UI
│   ├── Dockerfile
│   └── requirements.txt
├── database/                # DB 초기화
│   └── init.sql            # 테이블 스키마 (데이터는 엑셀에서 로드)
├── scripts/                 # 데이터 로딩 스크립트 ⭐
│   ├── load_excel_to_db.py         # 국가표준식품성분표 → PostgreSQL
│   ├── load_pdfs_to_faiss.py       # PDF → FAISS
│   ├── initialize_data.sh          # 통합 실행 스크립트
│   └── requirements.txt            # 스크립트 의존성
├── Documents/               # 학습 자료
│   ├── Data/               # 데이터 파일 ⭐
│   │   ├── 국가표준식품성분표_250426공개.xlsx  # 식품 영양 정보 (필수)
│   │   ├── alternatives.xlsx      # 대체 재료 매핑 (선택)
│   │   └── *.pdf                  # RAG용 참고 문서 (선택)
│   └── kongdak_prd.md      # 프로젝트 요구사항
├── docker-compose.yml       # Docker 오케스트레이션
├── .env.example            # 환경 변수 템플릿
├── start.sh                # 실행 스크립트
├── DATA_INITIALIZATION.md   # 데이터 초기화 가이드 ⭐
├── DEMO.md                 # 시연 가이드
├── TASK_LIST.md            # 작업 목록
└── CLAUDE.md               # Claude Code 가이드
```

## 📝 시연 가이드

자세한 시연 방법은 [DEMO.md](DEMO.md)를 참조하세요.

### 시연 시나리오 요약
1. **떡볶이 질문** → 나트륨 초과 경고 → 저염 레시피 제안
2. **퀴즈 생성** → 문제 풀기 → 정답 확인
3. **자료 검색** → 신뢰할 수 있는 기관 자료 추천

## ⚠️ 주의사항

### 필수 설정
- **OpenAI API Key**: `.env` 파일에 반드시 설정 필요
- **Docker**: Docker Desktop 실행 필수
- **포트**: 5432(PostgreSQL), 8000(Backend), 8501(Frontend) 사용 가능 확인

### 트러블슈팅
```bash
# 백엔드 연결 실패 시
docker-compose logs backend

# PostgreSQL 연결 확인
docker-compose exec postgres psql -U postgres -d kongdak_db

# 전체 재시작
docker-compose down -v
docker-compose up -d
```

## 📚 추가 문서

- **[DATA_INITIALIZATION.md](Documents/Data생성설명/DATA_INITIALIZATION.md)**: 데이터 초기화 상세 가이드 ⭐
- **[CLAUDE.md](CLAUDE.md)**: Claude Code 작업 가이드
- **[TASK_LIST.md](TASK_LIST.md)**: 상세 작업 리스트
- **[DEMO.md](DEMO.md)**: 시연 가이드
- **[Documents/kongdak_prd.md](Documents/kongdak_prd.md)**: 상세 PRD

## 🏆 팀원 소개

Team 02 - 콩닥식탁 개발팀
