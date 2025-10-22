"""이미지 분석 라우터"""
import logging
from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel
from src.backend.models import ChatResponse
from src.backend.routes.text import get_workflow_app
from src.workflow.workflow import (
    analyze_food_image,
    recognize_ingredients_from_image,
    calculate_nutrition_from_ingredients
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat/image", tags=["image"])


# ImageChatRequest 클래스는 Form 방식으로 대체되어 사용하지 않음
# 필요시 JSON 방식을 위해 보존
class ImageChatRequest(BaseModel):
    """이미지 채팅 요청 모델 (JSON)"""
    image_base64: str
    query: str


@router.post("/", response_model=ChatResponse)
async def analyze_image_json(
    image_base64: str = Form(...),
    query: str = Form(...),
    file_name: str = Form("uploaded_image")
):
    """
    이미지 + 텍스트 멀티모달 질의 (워크플로우 연동)

    - **image_base64**: Base64 인코딩된 이미지
    - **query**: 사용자 질문
    - **file_name**: 원본 파일명 (선택)
    """
    logger.info("🍽️ 이미지 멀티모달 요청 수신")

    try:
        workflow_app = get_workflow_app()
        workflow_input = {
            "query": query,
            "file_type": "image",
            "file_name": file_name,
            "file_content": image_base64,
        }

        result = workflow_app.invoke(workflow_input)

        return ChatResponse(
            status="success",
            intent=result.get("intent"),
            response=result.get("final_result", "응답을 생성할 수 없습니다.")
        )

    except Exception as e:
        logger.error(f"❌ 이미지 멀티모달 처리 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="이미지 처리 중 오류 발생")


@router.post("/analyze", response_model=ChatResponse)
async def analyze_food_image_handler(
    image_url: str = Form(...),
    query: str = Form(None)
):
    """
    음식 이미지 분석 (URL 기반)

    - **image_url**: 이미지 URL (또는 base64 인코딩)
    - **query**: (선택) 사용자 질문
    """
    logger.info(f"🍽️ 음식 이미지 분석 요청")

    try:
        # workflow.py의 함수 호출
        result = analyze_food_image(image_url, query)

        if result["status"] == "success":
            return ChatResponse(
                status="success",
                response=result["analysis"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["analysis"])

    except Exception as e:
        logger.error(f"❌ 이미지 분석 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="이미지 분석 중 오류 발생")


@router.post("/recognize-ingredients", response_model=ChatResponse)
async def recognize_ingredients_handler(image_url: str = Form(...)):
    """
    이미지에서 식재료 인식 (URL 기반)

    - **image_url**: 이미지 URL
    """
    logger.info("🔍 식재료 인식 요청")

    try:
        # workflow.py의 함수 호출
        result = recognize_ingredients_from_image(image_url)

        if result["status"] == "success":
            return ChatResponse(
                status="success",
                response=result["ingredients"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["ingredients"])

    except Exception as e:
        logger.error(f"❌ 식재료 인식 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="식재료 인식 중 오류 발생")


@router.post("/calculate-nutrition", response_model=ChatResponse)
async def calculate_nutrition_handler(ingredients_list: list = Form(...)):
    """
    식재료 영양 계산

    - **ingredients_list**: 식재료 목록 (JSON)
    """
    logger.info(f"📊 영양 계산 요청: {len(ingredients_list)}개 재료")

    try:
        # workflow.py의 함수 호출
        result = calculate_nutrition_from_ingredients(ingredients_list)

        if result["status"] == "success":
            return ChatResponse(
                status="success",
                response=result["nutrition"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["nutrition"])

    except Exception as e:
        logger.error(f"❌ 영양 계산 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="영양 계산 중 오류 발생")


@router.get("/health", response_model=ChatResponse)
async def health_check():
    """이미지 서비스 헬스 체크"""
    return ChatResponse(
        status="ok",
        response="이미지 서비스 정상 작동 중"
    )
