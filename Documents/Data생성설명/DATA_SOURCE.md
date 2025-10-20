# 데이터 소스 정보

## 📊 사용 데이터

### 1. 국가표준식품성분표 (메인 데이터)

**파일**: `Documents/Data/국가표준식품성분표_250426공개.xlsx`

**출처**: 식품의약품안전처
**버전**: Database 10.2 (2025년 4월 26일 공개)
**항목 수**: 3,312개 식품

#### 사용 컬럼 매핑

| 영양소 | 시트 컬럼 위치 | 컬럼명 | 단위 |
|--------|-------------|--------|------|
| 식품군 | 컬럼 2 | Unnamed: 2 | - |
| 식품명 | 컬럼 3 | Unnamed: 3 | - |
| 에너지 | 컬럼 5 | kcal | kcal |
| 단백질 | 컬럼 7 | g.1 | g |
| 인 | 컬럼 24 | mg.3 | mg |
| 칼륨 | 컬럼 25 | mg.4 | mg |
| 나트륨 | 컬럼 26 | mg.5 | mg |

**헤더 구조**:
- 1행: 대분류 (일반성분, 무기질, 비타민 등)
- 2행: 단위 (kcal, g, mg 등)
- 3행부터: 실제 데이터

**시트명**: `국가표준식품성분 Database 10.2`

---

### 2. 대체 재료 매핑 (수동 관리)

**파일**: `Documents/Data/alternatives.xlsx`

**출처**: 자체 제작 (신장 투석 환자 식단 가이드 기반)
**항목 수**: 14개 매핑

#### 컬럼 구조

| 컬럼명 | 타입 | 필수 | 설명 | 예시 |
|--------|------|------|------|------|
| 원재료 | 문자열 | ✅ | 원래 식품 | 김치 |
| 대체재료 | 문자열 | ✅ | 대체할 식품 | 저염 김치 |
| 영양소종류 | 문자열 | ✅ | sodium/potassium/phosphorus/protein | sodium |
| 감소비율 | 실수 | | 감소 % | 50.0 |
| 비고 | 문자열 | | 추가 설명 | 물에 헹구거나 저염 김치 사용 |

---

## 🔄 데이터 로딩 프로세스

### 1. 국가표준식품성분표 로딩

```python
# scripts/load_excel_to_db.py 내부 로직

# 1. 엑셀 읽기 (header=2로 3번째 행부터 데이터)
df = pd.read_excel(
    '국가표준식품성분표_250426공개.xlsx',
    sheet_name='국가표준식품성분 Database 10.2',
    header=2
)

# 2. 필요한 컬럼 추출 (컬럼 인덱스로 접근)
for idx, row in df.iterrows():
    food_name = row.iloc[3]      # 식품명
    category = row.iloc[2]        # 식품군
    calories = row.iloc[5]        # 에너지
    protein = row.iloc[7]         # 단백질
    phosphorus = row.iloc[24]     # 인
    potassium = row.iloc[25]      # 칼륨
    sodium = row.iloc[26]         # 나트륨

# 3. PostgreSQL INSERT
INSERT INTO foods (name, sodium, potassium, phosphorus, protein, calories, category)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (name) DO UPDATE SET ...
```

### 2. 대체 재료 로딩

```python
# 1. 엑셀 읽기 (일반 헤더)
df = pd.read_excel('alternatives.xlsx')

# 2. 데이터 추출
for idx, row in df.iterrows():
    original = row['원재료']
    alternative = row['대체재료']
    nutrient_type = row['영양소종류']
    reduction = row['감소비율']
    notes = row['비고']

# 3. PostgreSQL INSERT
INSERT INTO alternatives (...)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING
```

---

## 📈 데이터 통계

### 국가표준식품성분표

```
총 식품 수: 3,312개

식품군별 분포:
- 곡류 및 그 제품
- 감자 및 전분류
- 당류 및 그 제품
- 두류 및 그 제품
- 종실류 및 그 제품
- 채소류
- 버섯류
- 과일류
- 육류 및 그 제품
- 난류
- 어패류
- 해조류
- 유제품류
- 유지류
- 음료 및 주류
- 조미료류
- 기타
```

### 대체 재료 매핑

```
총 매핑 수: 14개

영양소별 분포:
- 나트륨(sodium) 감소: 4개
  * 김치 → 저염 김치 (50% 감소)
  * 고추장 → 저염 고추장 (40% 감소)
  * 된장 → 저염 된장 (40% 감소)
  * 어묵 → 두부 (99% 감소)

- 인(phosphorus) 감소: 3개
  * 돼지고기 → 닭가슴살 (14% 감소)
  * 소고기 → 닭가슴살 (30% 감소)
  * 멸치 → 두부 (88% 감소)

- 칼륨(potassium) 감소: 5개
  * 감자 → 당근 (25.4% 감소)
  * 파 → 양배추 (5.5% 감소)
  * 시금치 → 상추 (65.2% 감소)
  * 바나나 → 사과 (70.1% 감소)
  * 고구마 → 당근 (5% 감소)

- 단백질(protein) 감소: 2개
  * 돼지고기 → 두부 (59.5% 감소)
  * 멸치 → 두부 (86.5% 감소)
```

---

## 🔧 데이터 업데이트 방법

### 1. 국가표준식품성분표 업데이트

```bash
# 1. 최신 파일 다운로드
# 식약처 홈페이지에서 최신 국가표준식품성분표 다운로드

# 2. 파일 교체
cp ~/Downloads/국가표준식품성분표_XXXXXX공개.xlsx Documents/Data/

# 3. 스크립트 수정 (파일명이 바뀐 경우)
# scripts/load_excel_to_db.py 에서 파일명 수정

# 4. 데이터 재로드
python3 scripts/load_excel_to_db.py
```

### 2. 대체 재료 추가/수정

```bash
# 1. 엑셀 편집
# Documents/Data/alternatives.xlsx 열기

# 2. 행 추가/수정
# 원재료 | 대체재료 | 영양소종류 | 감소비율 | 비고

# 3. 저장 후 재로드
python3 scripts/load_excel_to_db.py
```

---

## 📚 참고 자료

### 공식 문서
- [식품의약품안전처 식품영양성분 데이터베이스](https://www.foodsafetykorea.go.kr/portal/healthyfoodlife/foodnutrient/nutrientDB.do)
- [대한신장학회 식단 가이드](http://www.ksn.or.kr/)

### 관련 파일
- [scripts/load_excel_to_db.py](scripts/load_excel_to_db.py) - 데이터 로딩 스크립트
- [scripts/create_sample_excel.py](scripts/create_sample_excel.py) - 샘플 대체재료 생성
- [database/init.sql](database/init.sql) - DB 스키마

---

## ⚠️ 주의사항

1. **국가표준식품성분표 형식 변경 시**
   - 컬럼 위치가 바뀌면 `load_excel_to_db.py`의 인덱스 수정 필요
   - 시트명이 바뀌면 `sheet_name` 파라미터 수정 필요

2. **데이터 정확성**
   - 결측값(NaN)은 0으로 처리
   - 식품명 중복 시 최신 데이터로 업데이트 (ON CONFLICT DO UPDATE)

3. **성능 최적화**
   - 배치 INSERT 사용 (100개씩)
   - 트랜잭션 단위로 커밋
   - 식품명에 인덱스 생성됨

---

*최종 업데이트: 2025-10-17*
