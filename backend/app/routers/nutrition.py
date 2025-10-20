"""
영양 분석 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.models.database import get_db
from app.models.schemas import NutritionAnalysisRequest, NutritionAnalysisResponse, NutritionInfo
from app.services.nutrition import NutritionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=NutritionAnalysisResponse)
async def analyze_nutrition(
    request: NutritionAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    영양 분석 엔드포인트

    재료 리스트를 받아서 총 영양소를 계산하고 위험도를 평가합니다.
    """
    try:
        logger.info(f"영양 분석 요청: {request.ingredients}")

        # 영양 분석 서비스
        nutrition_service = NutritionService(db)

        # 총 영양소 계산
        nutrition = nutrition_service.calculate_nutrition(request.ingredients)

        # 위험도 평가
        risk_level, warnings = nutrition_service.assess_risk_level(nutrition)

        # 응답 구성
        response = NutritionAnalysisResponse(
            total_nutrition=NutritionInfo(**nutrition),
            warnings=warnings,
            risk_level=risk_level
        )

        logger.info(f"영양 분석 완료: 위험도={risk_level}")
        return response

    except Exception as e:
        logger.error(f"영양 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"영양 분석 실패: {str(e)}")
