# 3일 Implementation Plan: MongoDB + FastAPI + Streamlit + 이미지 분석

## 📋 개요

이 계획은 기존 프로젝트에 MongoDB 데이터베이스, FastAPI 백엔드, Streamlit 프론트엔드를 3일 내에 추가하고, 이미지 입력을 **기존 LangGraph 체인에 통합**하는 최소 기능 버전(MVP)입니다.

### 🔑 핵심 아이디어
- **이미지 → 텍스트 변환**: OpenAI Vision API로 이미지 분석
- **기존 워크플로우 활용**: 변환된 텍스트를 기존 LangGraph 체인에 입력
- **최소한의 코드 변경**: 기존 `src/chains/`, `src/workflow/` 구조 유지

---

## 📅 3일 일정

| 날짜 | 작업 | 소요시간 |
|------|------|---------|
| **Day 1** | MongoDB 설정 + CSV → MongoDB 마이그레이션 | 3~4시간 |
| **Day 2** | FastAPI 백엔드 구축 + 기존 워크플로우 연동 | 4~5시간 |
| **Day 3** | Streamlit 프론트엔드 (3개 페이지) + 통합 테스트 | 3~4시간 |

---

## 🗓️ Day 1: MongoDB 설정 + 데이터 마이그레이션

### 목표
- MongoDB 로컬 인스턴스 실행
- CSV 파일을 MongoDB에 저장
- 인덱싱 설정

### 1-1. MongoDB 설치 및 실행

**Option 1: Docker 사용 (권장)**
```bash
docker run -d -p 27017:27017 --name mongodb mongo
```

**Option 2: 로컬 설치**
- macOS: `brew install mongodb-community && brew services start mongodb-community`
- Windows: https://www.mongodb.com/try/download/community 에서 설치

### 1-2. 환경 변수 설정

`.env` 파일에 추가:
```
MONGODB_URI=mongodb://localhost:27017/nutrition_db
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

### 1-3. 마이그레이션 스크립트 작성

**파일**: `src/database/migration.py`

```python
import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB 연결
mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/nutrition_db")
client = MongoClient(mongodb_uri)
db = client["nutrition_db"]

print("🔄 데이터 마이그레이션 시작...")

# 1. foods 컬렉션
print("📥 food_database_cleaned_df.csv 로드 중...")
foods_df = pd.read_csv("data/preprocess/food_database_cleaned_df.csv")

# ObjectId 제거 (CSV의 첫 번째 컬럼)
if foods_df.columns[0] == 'Unnamed: 0':
    foods_df = foods_df.drop(columns=['Unnamed: 0'])

# foods 컬렉션 초기화 (기존 데이터 제거)
db.foods.delete_many({})

# 데이터 삽입
foods_dict = foods_df.to_dict('records')
result = db.foods.insert_many(foods_dict)
print(f"✅ {len(result)}개의 식품 데이터 저장 완료")

# 인덱싱
db.foods.create_index("식품명")
db.foods.create_index("식품군")
print("✅ foods 인덱싱 완료")

# 2. recipes 컬렉션
print("\n📥 recipe_df.csv 로드 중...")
recipes_df = pd.read_csv("data/preprocess/recipe_df.csv")

# ObjectId 제거
if recipes_df.columns[0] == 'Unnamed: 0':
    recipes_df = recipes_df.drop(columns=['Unnamed: 0'])

# recipes 컬렉션 초기화
db.recipes.delete_many({})

# 데이터 삽입
recipes_dict = recipes_df.to_dict('records')
result = db.recipes.insert_many(recipes_dict)
print(f"✅ {len(result)}개의 레시피 데이터 저장 완료")

# 인덱싱
db.recipes.create_index("요리명")
print("✅ recipes 인덱싱 완료")

print("\n✅ 마이그레이션 완료!")
print(f"   - Foods: {db.foods.count_documents({})}")
print(f"   - Recipes: {db.recipes.count_documents({})}")
```

### 1-4. 마이그레이션 실행

```bash
cd /Users/jaehuncho/Coding/ai-camp-1st-chatbot-pjt-team-02
python src/database/migration.py
```

**예상 출력:**
```
🔄 데이터 마이그레이션 시작...
📥 food_database_cleaned_df.csv 로드 중...
✅ 3456개의 식품 데이터 저장 완료
✅ foods 인덱싱 완료

📥 recipe_df.csv 로드 중...
✅ 45678개의 레시피 데이터 저장 완료
✅ recipes 인덱싱 완료

✅ 마이그레이션 완료!
   - Foods: 3456
   - Recipes: 45678
```

### 1-5. MongoDB 헬퍼 함수 작성

**파일**: `src/database/mongo_helpers.py`

```python
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDBHelper:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017/nutrition_db"))
        self.db = self.client["nutrition_db"]

    def search_food(self, name: str):
        """식품명으로 검색"""
        return self.db.foods.find_one({"식품명": {"$regex": name, "$options": "i"}})

    def search_recipe(self, name: str):
        """요리명으로 레시피 검색"""
        return self.db.recipes.find_one({"요리명": {"$regex": name, "$options": "i"}})

    def search_foods_by_category(self, category: str, limit: int = 5):
        """식품군으로 검색"""
        return list(self.db.foods.find(
            {"식품군": category},
            {"식품명": 1, "에너지(kcal)": 1, "단백질(mg)": 1, "칼륨(mg)": 1, "나트륨(mg)": 1}
        ).limit(limit))

    def get_alternatives(self, food_name: str, limit: int = 5):
        """대체 식재료 추천"""
        food = self.search_food(food_name)
        if not food:
            return []
        return self.search_foods_by_category(food.get("식품군"), limit)

mongo_helper = MongoDBHelper()
```

---

## 🗓️ Day 2: FastAPI 백엔드 + LangGraph 통합

### 목표
- FastAPI 앱 생성
- `intent_classifier` chat template에 이미지 옵션 추가
- 이미지 → 쿼리 변환 → 기존 LangGraph 워크플로우로 처리
- MongoDB 연동

### 2-1. 디렉토리 구조

```bash
mkdir -p src/backend
```

### 2-2. FastAPI requirements 파일

**파일**: `src/backend/requirements.txt`

```
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
pymongo==4.6.0
pillow==10.1.0
openai==1.3.5
python-dotenv==1.0.0
requests==2.31.0
```

### 2-3. intent_classifier 수정 (이미지 옵션 추가)

**파일**: `src/chains/intent_classifier.py` (기존 파일 수정)

```python
"""의도 분류 체인 모듈"""

import logging
from typing import Optional, Union
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from .common import get_llm
import base64

logger = logging.getLogger(__name__)


def create_intent_classifier(
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
):
    """
    사용자 의도 분류 체인 생성
    - 텍스트 쿼리 또는 이미지 입력 모두 지원

    Args:
        model: 사용할 모델명
        temperature: 응답의 창의성 (의도분류는 낮을수록 좋음)
        max_tokens: 최대 토큰 수

    Returns:
        의도 분류 체인 (invoke 메서드 호출 시 query 또는 image 파라미터 받음)

    사용 예시:
    # 텍스트 입력
    classifier.invoke({"query": "떡국 대체재 추천해줘"})

    # 이미지 입력
    with open("food.jpg", "rb") as f:
        image_data = f.read()
    classifier.invoke({"image": image_data})
    """
    llm = get_llm(model=model, temperature=temperature, max_tokens=max_tokens)

    # ChatPromptTemplate with vision capability
    intent_classification_prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 사용자 의도를 분류하는 전문가입니다.

사용자의 질문 또는 이미지를 분석하여 다음 중 하나로 분류해주세요:

1. recommendation - 요리 재료 대체재 추천 요청
   예: "김치찌개 만들 때 뭘 대체할 수 있을까?", "불고기에서 저칼륨 재료 추천해줘"
   이미지: 음식 사진 → "이 음식의 대체재 추천해줘"로 판단

2. summary - 조리법, 주의사항 요약 또는 정보 제공 요청
   예: "저염식 조리법 알려줘", "신장 질환자 식사 주의사항은?"
   이미지: 음식 사진 → "이 음식의 영양정보 알려줘"로 판단

3. quiz - 문제 출제 요청
   예: "영양 관리 퀴즈 만들어줘", "문제 출제해줘"

반드시 'recommendation', 'summary', 'quiz' 중 하나만 답변하세요."""),
        ("user", [
            {
                "type": "text",
                "text": "{query_text}"
            }
        ])
    ])

    # 프롬프트 체인
    intent_classifier = intent_classification_prompt | llm | StrOutputParser()
    logger.info(f"의도 분류 체인 생성 완료 (model={model}, temperature={temperature})")

    return intent_classifier


def create_image_to_query_converter(
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
):
    """
    이미지를 텍스트 쿼리로 변환하는 체인 생성

    사용 예시:
    converter = create_image_to_query_converter()
    query = converter.invoke({"image": image_data})
    """
    llm = get_llm(model=model, temperature=temperature, max_tokens=max_tokens)

    image_to_query_prompt = ChatPromptTemplate.from_messages([
        ("system", """음식 사진을 분석하여 사용자 의도를 파악하고, 이를 자연스러운 텍스트 쿼리로 변환해주세요.

음식 사진에서 다음 정보를 추출하세요:
1. 요리명: 사진에 보이는 음식의 이름
2. 주요 재료: 보이는 주요 재료들
3. 제안할 쿼리: "이 음식의 영양정보와 저칼륨 대체재료를 추천해줘" 형식

응답 형식:
요리명: [요리명]
재료: [재료1, 재료2, ...]
쿼리: [생성된 쿼리]

생성된 쿼리만 최종적으로 반환하세요."""),
        ("user", [
            {
                "type": "image_url",
                "image_url": {
                    "url": "{image_url}"
                }
            }
        ])
    ])

    image_converter = image_to_query_prompt | llm | StrOutputParser()
    return image_converter
```

### 2-4. common.py에 이미지 처리 유틸리티 추가

**파일**: `src/chains/common.py` (기존 파일에 추가)

```python
# 파일 끝에 추가

def process_image_input(image_data: bytes) -> str:
    """
    이미지 데이터를 base64로 인코딩하여 Vision API 호출 가능한 형식으로 변환

    Args:
        image_data: 바이너리 이미지 데이터

    Returns:
        base64 인코딩된 이미지 URL 형식 문자열
    """
    import base64
    b64_image = base64.b64encode(image_data).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_image}"
```

### 2-5. FastAPI 메인 앱

**파일**: `src/backend/main.py`

```python
import os
import sys
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio
import base64

# 기존 모듈 import
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from workflow.workflow import create_workflow_app
from database.mongo_helpers import mongo_helper
from chains.intent_classifier import create_image_to_query_converter
from chains.common import process_image_input
from rag.rag_setup import RAGSetup

load_dotenv()

# FastAPI 앱 초기화
app = FastAPI(title="Nutrition API with LangGraph", version="1.0.0")

# CORS 설정 (Streamlit 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG 및 LangGraph 워크플로우 초기화
print("🚀 서비스 초기화 중...")
try:
    rag = RAGSetup()
    vectorstore = rag.vectorstore
    workflow_app = create_workflow_app(vectorstore)
    image_to_query_converter = create_image_to_query_converter()
    print("✅ 서비스 초기화 완료")
except Exception as e:
    print(f"❌ 서비스 초기화 실패: {e}")
    vectorstore = None
    workflow_app = None
    image_to_query_converter = None

# 요청 스키마
class QueryRequest(BaseModel):
    query: str

# ─────────────────────────────────────────
# 1. 텍스트 쿼리 처리 (기존 워크플로우)
# ─────────────────────────────────────────
@app.post("/api/chat")
async def chat(request: QueryRequest):
    """
    텍스트 쿼리를 LangGraph 워크플로우로 처리

    예:
    {
        "query": "신부전 환자를 위한 저칼륨 식단 추천해줘"
    }
    """
    try:
        if not workflow_app:
            raise HTTPException(status_code=503, detail="워크플로우 초기화 실패")

        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="쿼리가 비어있습니다")

        # LangGraph 워크플로우 실행
        input_state = {"query": query}
        result = await asyncio.to_thread(workflow_app.invoke, input_state)

        return {
            "success": True,
            "query": query,
            "result": result.get("final_result", "응답을 생성할 수 없습니다"),
            "intent": result.get("intent", "unknown")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 오류: {str(e)}")

# ─────────────────────────────────────────
# 2. 이미지 입력 → 워크플로우 처리
# ─────────────────────────────────────────
@app.post("/api/chat/image")
async def chat_with_image(file: UploadFile = File(...)):
    """
    1. 이미지 업로드
    2. LangGraph intent_classifier의 image_to_query_converter로 쿼리 생성
    3. 생성된 쿼리를 LangGraph 워크플로우로 처리

    흐름:
    Image → process_image_input (base64 변환)
         → image_to_query_converter (Vision API로 쿼리 생성)
         → workflow.invoke (기존 LangGraph 파이프라인)

    반환:
    {
        "success": True,
        "generated_query": "떡국의 영양정보와 저칼륨 대체재료를 추천해줘",
        "workflow_result": {
            "result": "...",
            "intent": "recommendation"
        }
    }
    """
    try:
        if not workflow_app or not image_to_query_converter:
            raise HTTPException(status_code=503, detail="워크플로우 또는 컨버터 초기화 실패")

        # 파일 검증
        if file.content_type not in ["image/jpeg", "image/jpg", "image/png"]:
            raise HTTPException(status_code=400, detail="JPG 또는 PNG 파일만 지원합니다")

        # 이미지 데이터 읽기
        image_data = await file.read()
        if len(image_data) > 20 * 1024 * 1024:  # 20MB
            raise HTTPException(status_code=400, detail="파일이 너무 큽니다 (최대 20MB)")

        # Step 1: 이미지를 base64로 변환
        print("🖼️  이미지 변환 중...")
        image_url = await asyncio.to_thread(process_image_input, image_data)

        # Step 2: 이미지 → 쿼리 변환 (LangGraph intent_classifier chain 사용)
        print("🔄 이미지를 쿼리로 변환 중...")
        generated_query = await asyncio.to_thread(
            image_to_query_converter.invoke,
            {"image_url": image_url}
        )

        # Step 3: 생성된 쿼리를 워크플로우로 처리
        print("⚙️  워크플로우 실행 중...")
        input_state = {"query": generated_query.strip()}
        workflow_result = await asyncio.to_thread(workflow_app.invoke, input_state)

        return {
            "success": True,
            "generated_query": generated_query.strip(),
            "workflow_result": {
                "result": workflow_result.get("final_result", "응답을 생성할 수 없습니다"),
                "intent": workflow_result.get("intent", "unknown")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 오류: {str(e)}")

# ─────────────────────────────────────────
# 3. 헬스 체크
# ─────────────────────────────────────────
@app.get("/health")
def health_check():
    """API 상태 확인"""
    try:
        foods_count = mongo_helper.db.foods.count_documents({})
        recipes_count = mongo_helper.db.recipes.count_documents({})
        return {
            "status": "healthy",
            "mongodb": "connected",
            "workflow": "initialized" if workflow_app else "failed",
            "foods_count": foods_count,
            "recipes_count": recipes_count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# ─────────────────────────────────────────
# 루트
# ─────────────────────────────────────────
@app.get("/")
def root():
    """API 정보"""
    return {
        "title": "Nutrition API with LangGraph",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "POST /api/chat - 텍스트 쿼리 처리 (기존 워크플로우)",
            "POST /api/chat/image - 이미지 분석 후 워크플로우 처리",
            "GET /health - 상태 확인"
        ],
        "architecture": "Image → LangGraph intent_classifier → Workflow Pipeline"
    }
```

### 2-5. FastAPI 실행

```bash
cd src/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

---

## 🗓️ Day 3: Streamlit 프론트엔드

### 목표
- Streamlit 웹 UI 생성
- 3개의 기능 페이지: 텍스트 쿼리, 이미지 분석, 영양 정보
- FastAPI 백엔드와 연동

### 3-1. 디렉토리 구조

```bash
mkdir -p streamlit_app/pages
cd streamlit_app
```

### 3-2. Streamlit requirements

**파일**: `streamlit_app/requirements.txt`

```
streamlit==1.28.1
requests==2.31.0
pillow==10.1.0
```

### 3-3. 메인 페이지

**파일**: `streamlit_app/main.py`

```python
import streamlit as st

st.set_page_config(
    page_title="Nutrition AI",
    page_icon="🥘",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🥘 AI 영양 추천 시스템")

st.write("""
## 기능 소개

좌측 사이드바에서 원하는 기능을 선택해주세요.

- 💬 **텍스트 쿼리**: 자연어로 영양 정보 및 추천 요청
- 📸 **이미지 분석**: 음식 사진을 업로드하면 자동 분석 및 추천
- 🍎 **영양 정보**: 음식의 상세 영양정보 조회

---

### 사용 예시

**텍스트 쿼리:**
- "신부전 환자를 위한 저칼륨 식단 추천해줘"
- "떡국의 영양정보는?"
- "귀리의 대체 식재료가 뭐가 있어?"

**이미지 분석:**
- 음식 사진 업로드 → 요리명 자동 인식 → 영양 정보 및 추천 표시

---

""")

import requests

try:
    response = requests.get("http://localhost:8000/health", timeout=2)
    if response.status_code == 200:
        data = response.json()
        st.success(f"✅ 백엔드 연결 (식품: {data['foods_count']:,}개, 레시피: {data['recipes_count']:,}개)")
    else:
        st.error("❌ 백엔드 연결 실패")
except:
    st.error("❌ 백엔드 연결 실패 (http://localhost:8000에서 FastAPI 실행 중인지 확인)")
```

### 3-4. 페이지 1: 텍스트 쿼리

**파일**: `streamlit_app/pages/1_💬_Text_Query.py`

```python
import streamlit as st
import requests

st.title("💬 텍스트 쿼리")

st.write("자연어로 영양 정보 및 추천을 요청하세요.")

st.info("예시:\n- '신부전 환자를 위한 저칼륨 식단 추천해줘'\n- '떡국의 영양정보는?'\n- '귀리의 대체 식재료가 뭐가 있어?'")

query = st.text_area("쿼리 입력", height=100, placeholder="예: 신부전 환자 식단 추천...")

if st.button("🚀 전송"):
    if query.strip():
        with st.spinner("처리 중..."):
            try:
                response = requests.post(
                    "http://localhost:8000/api/chat",
                    json={"query": query},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()

                    st.success("✅ 처리 완료!")

                    st.subheader(f"의도: {data.get('intent', 'unknown')}")

                    st.write("**응답:**")
                    st.info(data.get('result', '응답이 없습니다'))
                else:
                    st.error(f"❌ 오류: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("❌ 백엔드 연결 실패 (FastAPI가 실행 중인지 확인하세요)")
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
    else:
        st.warning("쿼리를 입력해주세요")
```

### 3-5. 페이지 2: 이미지 분석

**파일**: `streamlit_app/pages/2_📸_Image_Analysis.py`

```python
import streamlit as st
import requests
from PIL import Image
import io

st.title("📸 이미지 분석")

st.write("음식 사진을 업로드하면 요리명, 재료, 영양정보를 자동으로 분석합니다.")

st.info("⚠️ 지원 형식: JPG, JPEG, PNG (최대 20MB)")

uploaded_file = st.file_uploader(
    "음식 사진 업로드",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:
    # 이미지 미리보기
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드한 이미지", use_column_width=True)

    if st.button("🔍 분석"):
        with st.spinner("이미지를 분석 중입니다..."):
            try:
                files = {"file": uploaded_file.getvalue()}
                response = requests.post(
                    "http://localhost:8000/api/chat/image",
                    files=files,
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()

                    st.success("✅ 분석 완료!")

                    # 이미지 분석 결과
                    image_analysis = data.get('image_analysis', {})
                    st.subheader(f"🍴 인식된 요리: {image_analysis.get('dish_name', 'N/A')}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**재료**: {image_analysis.get('ingredients', 'N/A')}")
                    with col2:
                        st.write(f"**설명**: {image_analysis.get('description', 'N/A')}")

                    st.divider()

                    # 워크플로우 결과
                    workflow_result = data.get('workflow_result', {})
                    st.subheader("💡 AI 추천")

                    st.write(f"**의도**: {workflow_result.get('intent', 'unknown')}")
                    st.info(workflow_result.get('result', '응답이 없습니다'))

                    # 상세 데이터
                    if st.checkbox("상세 데이터 보기"):
                        st.json(data)
                else:
                    st.error(f"❌ 분석 실패: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("❌ 백엔드 연결 실패 (FastAPI가 실행 중인지 확인하세요)")
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
```

### 3-6. 페이지 3: 영양 정보

**파일**: `streamlit_app/pages/3_🍎_Nutrition_Info.py`

```python
import streamlit as st
import requests

st.title("🍎 영양 정보")

st.write("음식명을 입력하여 상세 영양정보를 조회합니다.")

query = st.text_input("음식명 입력", value="귀리", placeholder="예: 귀리, 쌀, 계란, 떡국")

if st.button("🔍 조회"):
    if query.strip():
        with st.spinner("조회 중..."):
            try:
                # 단순히 쿼리하여 영양정보만 가져오기
                response = requests.post(
                    "http://localhost:8000/api/chat",
                    json={"query": f"{query}의 영양정보를 알려줘"},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()

                    st.success("✅ 조회 완료!")

                    st.subheader(f"📊 {query} 영양정보")

                    st.info(data.get('result', '정보가 없습니다'))

                    if st.checkbox("상세 응답 보기"):
                        st.json(data)
                else:
                    st.error(f"❌ 조회 실패: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("❌ 백엔드 연결 실패")
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
    else:
        st.warning("음식명을 입력해주세요")
```

### 3-7. Streamlit 실행

```bash
cd streamlit_app
streamlit run main.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 📊 아키텍처 다이어그램

### 전체 흐름 (텍스트 + 이미지 입력)

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Streamlit Frontend (포트 8501)                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Page 1: 💬 텍스트 쿼리                                       │  │
│  │ Page 2: 📸 이미지 분석                                       │  │
│  │ Page 3: 🍎 영양 정보                                        │  │
│  └───────────────────────────────────────────────────────────────┘  │
└──────────────┬─────────────────────────────────────────┬────────────┘
               │ POST /api/chat                          │ POST /api/chat/image
               ▼                                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (포트 8000)                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  텍스트 입력 흐름:                  이미지 입력 흐름:               │
│  ┌─────────────┐                 ┌──────────────┐                 │
│  │ Text Query  │                 │ Image File   │                 │
│  └──────┬──────┘                 └──────┬───────┘                 │
│         │                               │                         │
│         └──────────────┬────────────────┘                         │
│                        │                                         │
│                        ▼                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ common.process_image_input()                            │   │
│  │   → Base64 인코딩 (이미지만)                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                        │                                         │
│                        ▼                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ intent_classifier.create_image_to_query_converter()      │   │
│  │   → ChatPromptTemplate with Vision capability            │   │
│  │   → OpenAI Vision API로 이미지 분석                     │   │
│  │   → 자연스러운 쿼리로 변환 (이미지만)                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                        │                                         │
│                        ▼                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  LangGraph Workflow                                     │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │ classifier node (intent_classifier)              │  │   │
│  │  │  → 텍스트/변환된 쿼리에서 의도 분류            │  │   │
│  │  │  → recommendation, summary, quiz 중 하나 결정  │  │   │
│  │  └──────────┬─────────────────────────────────────┘  │   │
│  │             │                                        │   │
│  │      ┌──────┼──────┐                                │   │
│  │      ▼      ▼      ▼                                │   │
│  │  ┌────┐ ┌───────┐ ┌────┐                            │   │
│  │  │Rec │ │Summary│ │Quiz│ (조건부 라우팅)          │   │
│  │  └──┬─┘ └───┬───┘ └──┬─┘                            │   │
│  │     │       │       │                               │   │
│  │     └───────┼───────┘                               │   │
│  │             ▼                                       │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ RAG + MongoDB + LLM 체인                    │  │   │
│  │  │ → 문서 검색 (RAG)                          │  │   │
│  │  │ → 영양 정보 조회 (MongoDB)                │  │   │
│  │  │ → LLM으로 최종 응답 생성                  │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │             │                                       │   │
│  │             ▼                                       │   │
│  │  final_result 반환                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                        │                                     │
│                        ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ JSON 응답 반환 (FastAPI)                              │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│               MongoDB (포트 27017)                            │
│  ├─ foods collection (3456개 식품)                           │
│  └─ recipes collection (45678개 레시피)                      │
└──────────────────────────────────────────────────────────────┘
```

### 핵심 변경점

**이전 방식**: 이미지 → 별도 Vision API → 텍스트 → 워크플로우

**새로운 방식**: 이미지 → LangGraph chain (의도분류)에서 처리 → 통합된 워크플로우

**이점**:
- 이미지 처리 로직이 LangGraph에 완전히 통합
- 재사용 가능한 체인 구조
- 일관된 프롬프트 관리 (ChatPromptTemplate 사용)
- 모든 처리가 LangGraph 파이프라인 내에서 실행

---

## 📁 최종 디렉토리 구조

```
project_root/
├── src/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── migration.py              # ✅ Day 1: CSV → MongoDB
│   │   └── mongo_helpers.py          # ✅ Day 1: MongoDB 헬퍼
│   │
│   ├── utils/
│   │   ├── image_analyzer.py         # ✅ Day 2: Vision API 분석
│   │   ├── web_search.py             # (기존)
│   │   └── ...
│   │
│   ├── backend/                      # ✅ Day 2
│   │   ├── main.py                   # FastAPI 앱
│   │   └── requirements.txt
│   │
│   ├── chains/                       # (기존 - 변경 없음)
│   ├── rag/                          # (기존 - 변경 없음)
│   ├── preprocess/                   # (기존 - 변경 없음)
│   ├── workflow/                     # (기존 - 변경 없음)
│   └── ...
│
├── streamlit_app/                    # ✅ Day 3
│   ├── main.py
│   ├── requirements.txt
│   └── pages/
│       ├── 1_💬_Text_Query.py
│       ├── 2_📸_Image_Analysis.py
│       └── 3_🍎_Nutrition_Info.py
│
├── data/                             # (기존)
├── tutorial/                         # (기존)
├── .env                              # (업데이트)
└── IMPLEMENTATION_PLAN_3DAYS.md      # 이 파일
```

---

## 🚀 실행 순서 (3일)

### Day 1: MongoDB 마이그레이션
```bash
# 1. MongoDB 실행
docker run -d -p 27017:27017 --name mongodb mongo

# 2. 마이그레이션 실행
cd /Users/jaehuncho/Coding/ai-camp-1st-chatbot-pjt-team-02
python src/database/migration.py

# 3. 확인
# MongoDB 콘솔에서 확인
docker exec -it mongodb mongosh
> use nutrition_db
> db.foods.count()       # 3456
> db.recipes.count()     # 45678
```

### Day 2: FastAPI 백엔드
```bash
# 터미널 1: FastAPI 실행
cd src/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 테스트 (터미널 2)
curl http://localhost:8000/health

# API 문서 확인
# 브라우저: http://localhost:8000/docs
```

### Day 3: Streamlit 프론트엔드
```bash
# 터미널 1: FastAPI 계속 실행 (위에서)
# 터미널 2: Streamlit 실행
cd streamlit_app
pip install -r requirements.txt
streamlit run main.py

# 브라우저: http://localhost:8501
```

---

## ✅ 체크리스트

### Day 1 완료 확인
- [ ] MongoDB 실행 중
- [ ] `src/database/migration.py` 작성 및 실행
- [ ] `src/database/mongo_helpers.py` 작성
- [ ] MongoDB에 foods (3456개) + recipes (45678개) 저장됨
- [ ] 인덱싱 완료

### Day 2 완료 확인
- [ ] `src/utils/image_analyzer.py` 작성
- [ ] `src/backend/main.py` 작성
- [ ] `src/backend/requirements.txt` 작성
- [ ] FastAPI 실행 중 (http://localhost:8000)
- [ ] `/health` 엔드포인트 응답 확인
- [ ] `/api/chat` 테스트 완료
- [ ] `/api/chat/image` 테스트 완료

### Day 3 완료 확인
- [ ] `streamlit_app/` 디렉토리 구성 완료
- [ ] 3개 페이지 파일 작성 완료
- [ ] `streamlit_app/requirements.txt` 작성
- [ ] Streamlit 실행 중 (http://localhost:8501)
- [ ] 3개 기능 모두 정상 작동 확인

---

## 🔌 통합 테스트 순서

### Step 1: MongoDB 연결 확인
```bash
python -c "from src.database.mongo_helpers import mongo_helper; print(f'Foods: {mongo_helper.db.foods.count_documents({})}')"
```

### Step 2: FastAPI 테스트
```bash
# 텍스트 쿼리
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"query":"신부전 환자 식단 추천해줘"}'

# 이미지 분석 (이미지 파일 필요)
curl -X POST "http://localhost:8000/api/chat/image" \
  -F "file=@path/to/image.jpg"
```

### Step 3: Streamlit 테스트
- http://localhost:8501 접속
- 각 페이지별 기능 테스트

---

## 📝 핵심 개선 사항

| 항목 | 이전 | 이후 |
|------|------|------|
| **데이터 저장** | CSV 메모리 로드 | MongoDB 지속성 저장 |
| **백엔드** | Jupyter Notebook | FastAPI REST API |
| **프론트엔드** | 터미널/Notebook | Streamlit 웹 UI |
| **이미지 입력** | ❌ 없음 | ✅ Vision API 분석 |
| **이미지 처리** | 별도 모듈 | LangGraph 워크플로우 통합 |
| **확장성** | 낮음 | 높음 (API 기반) |

---

## 🐛 트러블슈팅

### MongoDB 연결 오류
```bash
# MongoDB 확인
docker ps | grep mongodb

# 재시작
docker restart mongodb
```

### FastAPI 포트 충돌
```bash
# 다른 포트로 실행
uvicorn main:app --port 8001
```

### 이미지 분석 오류
```
Error: OpenAI API key not found
→ .env에 OPENAI_API_KEY 설정 확인
```

### Streamlit 연결 실패
```bash
# FastAPI 실행 확인
curl http://localhost:8000/health

# Streamlit 캐시 초기화
streamlit cache clear
```

---

## 📚 필수 패키지

```bash
# 한번에 설치
pip install pymongo pandas python-dotenv fastapi uvicorn python-multipart pydantic openai streamlit requests pillow

# 또는 각 폴더에서
cd src/backend && pip install -r requirements.txt
cd ../.. && cd streamlit_app && pip install -r requirements.txt
```

---

## 📖 참고 자료

- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Streamlit 공식 문서](https://docs.streamlit.io/)
- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)
- [MongoDB 공식 문서](https://docs.mongodb.com/)

---

**작성 날짜**: 2024년 10월 18일
**예상 완료 기간**: 3일
**주요 특징**: 기존 LangGraph 체인에 이미지 입력 통합
