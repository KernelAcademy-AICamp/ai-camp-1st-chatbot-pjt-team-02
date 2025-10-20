"""
퀴즈 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.models.database import get_db, QuizHistory
from app.models.schemas import (
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizQuestion,
    QuizSubmitRequest,
    QuizSubmitResponse
)
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=QuizGenerateResponse)
async def generate_quiz(
    request: QuizGenerateRequest
):
    """
    퀴즈 생성 엔드포인트

    주제, 난이도, 문제 수를 받아서 퀴즈를 생성합니다.
    """
    try:
        logger.info(f"퀴즈 생성 요청: 주제={request.topic}, 난이도={request.difficulty}, 개수={request.count}")

        # 퀴즈 생성
        questions_data = llm_service.generate_quiz(
            topic=request.topic,
            difficulty=request.difficulty,
            count=request.count,
            question_type=request.question_type
        )

        # 응답 구성
        questions = [QuizQuestion(**q) for q in questions_data]

        response = QuizGenerateResponse(
            questions=questions,
            total_count=len(questions)
        )

        logger.info(f"퀴즈 생성 완료: {len(questions)}문제")
        return response

    except Exception as e:
        logger.error(f"퀴즈 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"퀴즈 생성 실패: {str(e)}")


@router.post("/submit", response_model=QuizSubmitResponse)
async def submit_quiz(
    request: QuizSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    퀴즈 답변 제출 엔드포인트

    사용자의 답변을 받아서 정답 여부를 확인하고 기록합니다.
    """
    try:
        logger.info(f"퀴즈 제출: 세션={request.session_id}")

        # 정답 확인
        is_correct = request.user_answer.strip().lower() == request.correct_answer.strip().lower()

        # 간단한 해설 생성 (실제로는 문제 생성 시 받은 해설 사용)
        explanation = f"정답은 '{request.correct_answer}'입니다."
        if not is_correct:
            explanation = f"틀렸습니다. {explanation}"
        else:
            explanation = f"정답입니다! {explanation}"

        # 퀴즈 기록 저장
        quiz_record = QuizHistory(
            session_id=request.session_id,
            question=request.question,
            user_answer=request.user_answer,
            correct_answer=request.correct_answer,
            is_correct=is_correct,
            explanation=explanation
        )
        db.add(quiz_record)
        db.commit()

        response = QuizSubmitResponse(
            is_correct=is_correct,
            explanation=explanation
        )

        logger.info(f"퀴즈 제출 완료: 정답={is_correct}")
        return response

    except Exception as e:
        logger.error(f"퀴즈 제출 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"퀴즈 제출 실패: {str(e)}")


@router.get("/history/{session_id}")
async def get_quiz_history(
    session_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    퀴즈 히스토리 조회

    Args:
        session_id: 세션 ID
        limit: 조회할 최대 개수

    Returns:
        퀴즈 기록 리스트
    """
    try:
        records = db.query(QuizHistory).filter(
            QuizHistory.session_id == session_id
        ).order_by(
            QuizHistory.created_at.desc()
        ).limit(limit).all()

        # 정답률 계산
        total = len(records)
        correct = sum(1 for r in records if r.is_correct)
        accuracy = (correct / total * 100) if total > 0 else 0

        return {
            "session_id": session_id,
            "total": total,
            "correct": correct,
            "accuracy": round(accuracy, 2),
            "history": [
                {
                    "id": r.id,
                    "question": r.question,
                    "user_answer": r.user_answer,
                    "correct_answer": r.correct_answer,
                    "is_correct": r.is_correct,
                    "explanation": r.explanation,
                    "created_at": r.created_at.isoformat()
                }
                for r in reversed(records)
            ]
        }

    except Exception as e:
        logger.error(f"퀴즈 히스토리 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="퀴즈 히스토리 조회 실패")
