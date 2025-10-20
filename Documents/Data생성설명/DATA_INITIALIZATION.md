# 데이터 초기화 가이드

콩닥식탁 프로젝트의 데이터를 초기화하는 방법을 안내합니다.

## 개요

이 프로젝트는 **엑셀 파일에서 데이터를 읽어 PostgreSQL과 FAISS에 로드**합니다.

### 데이터 흐름

```
엑셀 파일 (*.xlsx)  →  PostgreSQL (식품/대체재료 데이터)
PDF 파일 (*.pdf)    →  FAISS (벡터 임베딩 - RAG용)
```

## 빠른 시작

### 전제 조건

1. **국가표준식품성분표 파일 준비**
   - 파일: `Documents/Data/국가표준식품성분표_250426공개.xlsx`
   - 이미 있다면 바로 사용 가능! (변환 불필요)

2. **대체 재료 데이터 준비** (선택사항)
   - 파일: `Documents/Data/alternatives.xlsx`
   - 직접 작성하거나 없으면 스킵 가능

### 자동 초기화 (권장)

모든 단계를 한 번에 실행:

```bash
cd scripts
./initialize_data.sh
```

### 수동 초기화

각 단계를 개별적으로 실행하려면:

```bash
# 1단계: PostgreSQL 로드 (국가표준식품성분표 + alternatives)
python3 scripts/load_excel_to_db.py

# 2단계: FAISS 로드 (선택적 - PDF 문서가 있는 경우)
python3 scripts/load_pdfs_to_faiss.py
```

## 데이터 파일 형식

### 식품 영양 정보

**✅ 국가표준식품성분표를 직접 사용합니다!**

`Documents/Data/국가표준식품성분표_250426공개.xlsx` 파일을 그대로 사용하세요.
- 컬럼명 변경 **불필요**
- 파일명 변경 **불필요** (foods.xlsx로 바꿀 필요 없음)
- 스크립트가 자동으로 필요한 컬럼을 매핑합니다

**스크립트가 읽는 컬럼 매핑:**
- 시트명: `국가표준식품성분 Database 10.2`
- 식품군: 컬럼 2 (Unnamed: 2)
- 식품명: 컬럼 3 (Unnamed: 3)
- 에너지(kcal): 컬럼 5
- 단백질(g): 컬럼 7
- 인(mg): 컬럼 24
- 칼륨(mg): 컬럼 25
- 나트륨(mg): 컬럼 26

**DB 스키마로 자동 변환됩니다:**

| DB 컬럼명 | 타입 | 설명 | 국가표준식품성분표 컬럼 |
|-----------|------|------|------------------------|
| name | 문자열 | 식품 이름 | 컬럼 3 (식품명) |
| sodium | 실수 | mg/100g | 컬럼 26 (나트륨) |
| potassium | 실수 | mg/100g | 컬럼 25 (칼륨) |
| phosphorus | 실수 | mg/100g | 컬럼 24 (인) |
| protein | 실수 | g/100g | 컬럼 7 (단백질) |
| calories | 실수 | kcal/100g | 컬럼 5 (에너지) |
| category | 문자열 | 식품 카테고리 | 컬럼 2 (식품군) |

### 대체 재료 매핑 (alternatives.xlsx)

| 컬럼명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| 원재료 | 문자열 | ✅ | 원래 식품 | 김치 |
| 대체재료 | 문자열 | ✅ | 대체할 식품 | 저염 김치 |
| 영양소종류 | 문자열 | ✅ | sodium/potassium/phosphorus/protein | sodium |
| 감소비율 | 실수 | | 감소 % | 50.0 |
| 비고 | 문자열 | | 추가 설명 | 물에 헹구거나 저염 김치 사용 |

**예시:**
```
원재료  대체재료     영양소종류  감소비율  비고
김치    저염 김치    sodium     50.0     물에 헹구거나 저염 김치 사용
감자    당근         potassium  25.4     저칼륨 채소로 대체
```

## 스크립트 상세 설명

### 1. load_excel_to_db.py

**국가표준식품성분표**와 대체 재료 엑셀을 PostgreSQL에 로드합니다.

**기능:**
- psycopg2를 사용한 직접 DB 연결
- 국가표준식품성분표 자동 컬럼 매핑 (인덱스 기반)
- 배치 INSERT (100개씩)
- ON CONFLICT 처리 (중복 시 UPDATE)
- 트랜잭션 관리 (commit/rollback)

**읽는 파일:**
- `Documents/Data/국가표준식품성분표_250426공개.xlsx` - 식품 영양 정보 (자동 매핑)
- `Documents/Data/alternatives.xlsx` - 대체 재료 매핑

**환경 변수 (.env):**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kongdak_db
DB_USER=postgres
DB_PASSWORD=postgres
```

**실행:**
```bash
python3 scripts/load_excel_to_db.py
```

**출력 예시:**
```
식품 데이터 1234개 로드 완료 (국가표준식품성분표)
대체재료 14개 로드 완료
```

### 2. load_pdfs_to_faiss.py

PDF 문서를 읽어 FAISS 벡터 저장소를 생성합니다.

**기능:**
- LangChain을 사용한 PDF 로딩
- 텍스트 청크 생성 (500자, 50자 겹침)
- OpenAI 임베딩 (text-embedding-ada-002)
- FAISS 인덱스 저장

**필요 파일:**
- `Documents/Data/*.pdf` - 식단 관련 참고 문서

**환경 변수 (.env):**
```bash
OPENAI_API_KEY=your-api-key-here
```

**실행:**
```bash
python3 scripts/load_pdfs_to_faiss.py
```

## Docker 환경에서 실행

Docker Compose를 사용하는 경우:

```bash
# 1. 컨테이너 시작
docker-compose up -d postgres

# 2. 데이터 초기화 스크립트 실행
docker-compose exec backend python /app/scripts/load_excel_to_db.py
docker-compose exec backend python /app/scripts/load_pdfs_to_faiss.py
```

또는 backend 컨테이너 내부에서:

```bash
docker-compose exec backend bash
cd /app/scripts
./initialize_data.sh
```

## 커스텀 데이터 추가

### 다른 국가표준식품성분표 버전 사용하기

**이미 국가표준식품성분표를 사용 중입니다!**

다른 버전을 사용하려면:

1. **새로운 국가표준식품성분표 다운로드** (예: 2024년 버전)
2. `Documents/Data/` 폴더에 저장
3. `scripts/load_excel_to_db.py` 파일에서 파일명 수정:
   ```python
   # 208번 줄 수정
   foods_excel = os.path.join(base_dir, 'Documents', 'Data',
                               '국가표준식품성분표_새버전.xlsx')  # 파일명 변경
   ```
4. 시트명/컬럼 순서가 다른 경우 매핑 정보도 수정 (52-62번 줄)
5. `load_excel_to_db.py` 실행

**⚠️ 주의:** 컬럼 순서나 시트명이 다를 수 있으므로 엑셀 파일을 먼저 확인하세요!

### 대체 재료 데이터 작성하기

직접 `Documents/Data/alternatives.xlsx` 파일을 작성하세요:

**필수 컬럼:**
| 컬럼명 | 예시 |
|--------|------|
| 원재료 | 김치 |
| 대체재료 | 저염 김치 |
| 영양소종류 | sodium |
| 감소비율 | 50.0 |
| 비고 | 물에 헹구거나 저염 김치 사용 |

**참고:** 대체 재료 데이터가 없어도 기본 영양 분석은 동작합니다.

### PDF 문서 추가

1. CKD 관련 식단 가이드 PDF를 준비
2. `Documents/Data/` 디렉토리에 복사
3. `load_pdfs_to_faiss.py` 실행

## 데이터 확인

### PostgreSQL 확인

```bash
# Docker 환경
docker-compose exec postgres psql -U postgres -d kongdak_db -c "SELECT COUNT(*) FROM foods;"
docker-compose exec postgres psql -U postgres -d kongdak_db -c "SELECT COUNT(*) FROM alternatives;"

# 로컬 환경
psql -U postgres -d kongdak_db -c "SELECT COUNT(*) FROM foods;"
```

### FAISS 인덱스 확인

```bash
ls -lh data/faiss_index/
```

다음 파일이 생성되어야 합니다:
- `index.faiss` - 벡터 인덱스
- `index.pkl` - 메타데이터

## 트러블슈팅

### 1. psycopg2 설치 오류

```bash
# macOS
brew install postgresql
pip install psycopg2-binary

# Ubuntu/Debian
sudo apt-get install libpq-dev
pip install psycopg2-binary
```

### 2. OpenAI API 키 오류

`.env` 파일에 올바른 API 키가 설정되었는지 확인:

```bash
OPENAI_API_KEY=sk-...
```

### 3. DB 연결 오류

PostgreSQL이 실행 중인지 확인:

```bash
# Docker
docker-compose ps postgres

# 로컬
pg_isready -h localhost -p 5432
```

### 4. 엑셀 파일 읽기 오류

pandas 및 openpyxl 설치 확인:

```bash
pip install pandas openpyxl
```

### 5. FAISS 로딩 중 메모리 부족

청크 크기를 줄이거나 배치 처리:

```python
# load_pdfs_to_faiss.py에서 수정
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,  # 500 → 300으로 축소
    chunk_overlap=30,
)
```

## 참고 자료

- [kongdak-참조소스.py](Documents/kongdak-참조소스.py) - 원본 참조 구현
- [database/init.sql](database/init.sql) - DB 스키마 정의
- [DATA_LOADING_COMPLETE.md](DATA_LOADING_COMPLETE.md) - 구현 완료 요약 (참고용)

## 다음 단계

데이터 초기화 후:

1. **백엔드 시작**: `cd backend && uvicorn app.main:app --reload`
2. **프론트엔드 시작**: `cd frontend && streamlit run app.py`
3. **전체 시스템 시작**: `./start.sh` 또는 `docker-compose up`

API 테스트:
```bash
# 식품 검색
curl http://localhost:8000/api/nutrition/search?query=떡

# 채팅
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","food_name":"떡볶이"}'
```
