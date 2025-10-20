"""
Pydantic 스키마 (Request/Response 모델)
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ========== 채팅 API 스키마 ==========

class ChatRequest(BaseModel):
    """채팅 요청 스키마"""
    message: str = Field(..., description="사용자 질문", min_length=1, max_length=500)
    session_id: str = Field(..., description="세션 ID")
    limits: Optional[Dict[str, int]] = Field(
        default=None,
        description="영양소 제한치 (sodium, potassium, phosphorus, protein)"
    )


class NutritionInfo(BaseModel):
    """영양 정보 스키마"""
    sodium: float = Field(0.0, description="나트륨 (mg)")
    potassium: float = Field(0.0, description="칼륨 (mg)")
    phosphorus: float = Field(0.0, description="인 (mg)")
    protein: float = Field(0.0, description="단백질 (g)")
    calories: float = Field(0.0, description="칼로리 (kcal)")
    found_ingredients: Optional[List[str]] = Field(default=[], description="찾은 재료")
    missing_ingredients: Optional[List[str]] = Field(default=[], description="못 찾은 재료")


class AlternativeInfo(BaseModel):
    """대체 재료 정보 스키마"""
    original: str = Field(..., description="원래 재료")
    alternative: str = Field(..., description="대체 재료")
    nutrient_type: str = Field(..., description="영양소 타입")
    reduction: float = Field(..., description="감소율 (%)")


class ChatResponse(BaseModel):
    """채팅 응답 스키마"""
    answer: str = Field(..., description="챗봇 답변")
    nutrition: NutritionInfo = Field(..., description="영양 정보")
    risk_level: str = Field(..., description="위험도 (low/medium/high)")
    alternatives: List[AlternativeInfo] = Field(default=[], description="대체 재료 제안")
    quiz_offer: bool = Field(default=False, description="퀴즈 제안 여부")


# ========== 영양 분석 API 스키마 ==========

class NutritionAnalysisRequest(BaseModel):
    """영양 분석 요청 스키마"""
    ingredients: List[str] = Field(..., description="재료 리스트", min_items=1)


class NutritionAnalysisResponse(BaseModel):
    """영양 분석 응답 스키마"""
    total_nutrition: NutritionInfo = Field(..., description="총 영양 정보")
    warnings: List[str] = Field(default=[], description="경고 메시지")
    risk_level: str = Field(..., description="위험도")


# ========== 퀴즈 API 스키마 ==========

class QuizGenerateRequest(BaseModel):
    """퀴즈 생성 요청 스키마"""
    topic: str = Field(..., description="퀴즈 주제", min_length=1, max_length=100)
    difficulty: str = Field("medium", description="난이도 (easy/medium/hard)")
    count: int = Field(3, description="문제 수", ge=1, le=10)
    question_type: Optional[str] = Field(None, description="문제 유형 (multiple_choice/short_answer/ox)")


class QuizQuestion(BaseModel):
    """퀴즈 문제 스키마"""
    question: str = Field(..., description="문제")
    options: Optional[List[str]] = Field(None, description="선택지 (객관식인 경우)")
    correct_answer: str = Field(..., description="정답")
    explanation: str = Field(..., description="해설")
    question_type: str = Field(..., description="문제 유형")


class QuizGenerateResponse(BaseModel):
    """퀴즈 생성 응답 스키마"""
    questions: List[QuizQuestion] = Field(..., description="퀴즈 문제 리스트")
    total_count: int = Field(..., description="총 문제 수")


class QuizSubmitRequest(BaseModel):
    """퀴즈 제출 요청 스키마"""
    session_id: str = Field(..., description="세션 ID")
    question: str = Field(..., description="문제")
    user_answer: str = Field(..., description="사용자 답변")
    correct_answer: str = Field(..., description="정답")


class QuizSubmitResponse(BaseModel):
    """퀴즈 제출 응답 스키마"""
    is_correct: bool = Field(..., description="정답 여부")
    explanation: str = Field(..., description="해설")


# ========== 자료 추천 API 스키마 ==========

class ResourceInfo(BaseModel):
    """자료 정보 스키마"""
    title: str = Field(..., description="자료 제목")
    url: str = Field(..., description="자료 URL")
    description: str = Field("", description="자료 설명")
    source: str = Field(..., description="출처")
    relevance_score: float = Field(..., description="관련성 점수 (0-1)")
    published_date: Optional[str] = Field(None, description="발행일")


class ResourceRecommendResponse(BaseModel):
    """자료 추천 응답 스키마"""
    resources: List[ResourceInfo] = Field(..., description="추천 자료 리스트")
    total: int = Field(..., description="총 자료 수")
    keyword: str = Field(..., description="검색 키워드")


# ========== 식품 정보 스키마 ==========

class FoodInfo(BaseModel):
    """식품 정보 스키마"""
    id: int
    name: str
    sodium: float
    potassium: float
    phosphorus: float
    protein: float
    calories: float
    category: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
