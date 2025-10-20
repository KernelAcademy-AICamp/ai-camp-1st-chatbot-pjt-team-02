"""
채팅 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.models.database import get_db, UserQuery
from app.models.schemas import ChatRequest, ChatResponse, NutritionInfo, AlternativeInfo
from app.services.llm_service import llm_service
from app.services.nutrition import NutritionService
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    채팅 엔드포인트

    전체 워크플로우:
    1. LLM으로 음식명에서 재료 추출
    2. DB에서 재료별 영양 정보 조회
    3. 총 영양소 계산 및 위험도 평가
    4. RAG로 대체 방법 검색
    5. LLM으로 최종 답변 생성
    6. 대화 기록 저장
    """
    try:
        logger.info(f"채팅 요청: {request.message} (세션: {request.session_id})")

        # 1. 재료 추출
        ingredients = llm_service.extract_ingredients(request.message)
        logger.info(f"추출된 재료: {ingredients}")

        # 2. 영양 분석
        nutrition_service = NutritionService(db)
        nutrition = nutrition_service.calculate_nutrition(ingredients)

        # 3. 위험도 평가
        custom_limits = request.limits if request.limits else None
        risk_level, warnings = nutrition_service.assess_risk_level(nutrition, custom_limits)

        # 4. 위험 영양소 추출
        dangerous_nutrients = nutrition_service.get_dangerous_nutrients(nutrition, custom_limits)

        # 5. RAG로 대체 방법 검색
        alternatives_text = ""
        if dangerous_nutrients:
            alternatives_text = rag_service.get_alternatives_from_rag(
                request.message,
                dangerous_nutrients
            )

        # 6. 대체 재료 추천
        alternatives = nutrition_service.get_alternatives(ingredients, dangerous_nutrients)

        # 7. 최종 답변 생성
        answer = llm_service.generate_final_answer(
            request.message,
            nutrition,
            alternatives_text,
            custom_limits
        )

        # 8. 대화 기록 저장
        user_query = UserQuery(
            session_id=request.session_id,
            user_question=request.message,
            bot_answer=answer,
            nutrition_info=nutrition,
            risk_level=risk_level
        )
        db.add(user_query)
        db.commit()

        # 9. 응답 구성
        response = ChatResponse(
            answer=answer,
            nutrition=NutritionInfo(**nutrition),
            risk_level=risk_level,
            alternatives=[
                AlternativeInfo(
                    original=alt["original"],
                    alternative=alt["alternative"],
                    nutrient_type=alt["nutrient_type"],
                    reduction=alt["reduction"]
                )
                for alt in alternatives
            ],
            quiz_offer=risk_level in ["medium", "high"]  # 위험도가 높으면 퀴즈 제안
        )

        logger.info(f"채팅 응답 완료: 위험도={risk_level}")
        return response

    except Exception as e:
        logger.error(f"채팅 처리 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류 발생: {str(e)}")


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    채팅 히스토리 조회

    Args:
        session_id: 세션 ID
        limit: 조회할 최대 개수

    Returns:
        대화 기록 리스트
    """
    try:
        queries = db.query(UserQuery).filter(
            UserQuery.session_id == session_id
        ).order_by(
            UserQuery.created_at.desc()
        ).limit(limit).all()

        return {
            "session_id": session_id,
            "total": len(queries),
            "history": [
                {
                    "id": q.id,
                    "question": q.user_question,
                    "answer": q.bot_answer,
                    "nutrition": q.nutrition_info,
                    "risk_level": q.risk_level,
                    "created_at": q.created_at.isoformat()
                }
                for q in reversed(queries)
            ]
        }

    except Exception as e:
        logger.error(f"히스토리 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="히스토리 조회 실패")
