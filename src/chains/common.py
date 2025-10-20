"""공통 모듈: LLM, 컨텍스트 검색 함수, Logger"""

import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from src.utils.web_search import search_for_nutrition_info

# Logger 설정
logger = logging.getLogger(__name__)


# LLM 초기화
def get_llm(
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    top_p: float = 1.0,
):
    """
    LLM 인스턴스 반환

    Args:
        model: 사용할 모델명 (기본값: gpt-4o-mini)
        temperature: 응답의 창의성 (0.0~2.0, 기본값: 0.7)
        max_tokens: 최대 토큰 수 (기본값: None - 제한 없음)
        top_p: 누적 확률 필터링 (기본값: 1.0)

    Returns:
        ChatOpenAI 인스턴스
    """
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
    )


# 컨텍스트 검색 함수들
def get_context_for_ingredients(retriever, dish_name: str) -> str:
    """재료 추출을 위한 컨텍스트 검색 (RAG + 웹 검색 Fallback)"""
    query = f"{dish_name} 재료 레시피"

    # 1. RAG 검색 시도
    docs = retriever.retrieve(query)
    total_length = sum(len(doc.page_content) for doc in docs)
    min_required_length = 300

    if total_length >= min_required_length:
        context = "\n\n".join([doc.page_content for doc in docs])
        logger.info(f"✅ '{dish_name}' RAG 검색 결과 사용")
    else:
        # Fallback: 웹 검색
        logger.warning(f"⚠️ '{dish_name}' RAG 검색 결과 부족 → 웹 검색 실행 중...")
        rag_context = "\n\n".join([doc.page_content for doc in docs]) if docs else "검색 결과 없음"
        web_results = search_for_nutrition_info(f"{dish_name} 레시피 재료", max_results=2)
        context = f"[RAG 검색 결과]\n{rag_context}\n\n[웹 검색 결과]\n{web_results}"
        logger.info("✅ RAG + 웹 검색 결과 결합 완료")

    return context


def get_context_for_recommendation(retriever, dish_name: str, ingredients: str = "") -> str:
    """
    추천을 위한 컨텍스트 검색 (MongoDB → RAG → 웹 검색 3단계 Fallback)

    Args:
        retriever: RAG retriever
        dish_name: 요리명
        ingredients: 추출된 재료 정보 (선택)

    Returns:
        통합 컨텍스트 문자열
    """
    from src.utils.alternative_search import search_alternatives_from_mongodb, extract_ingredients_from_text

    context_parts = []

    # 1단계: MongoDB에서 대체재 검색 (최우선)
    try:
        # 재료 리스트 추출
        if ingredients:
            ingredient_list = extract_ingredients_from_text(ingredients)
        else:
            # dish_name에서 일반적인 재료 추측 (간단한 버전)
            ingredient_list = [dish_name]

        logger.info(f"📋 음식 재료 추출 완료: {ingredient_list}")
        logger.info(f"🔍 MongoDB 대체재 검색 시작...")
        mongodb_results = search_alternatives_from_mongodb(ingredient_list, max_per_ingredient=3)

        if mongodb_results:
            context_parts.append(f"[MongoDB 대체재 검색 결과]\n{mongodb_results}")
            # 결과 간단히 요약해서 출력
            result_lines = mongodb_results.strip().split('\n')
            result_summary = result_lines[0] if result_lines else "대체재 발견"
            logger.info(f"✅ MongoDB 대체재 검색 완료: {result_summary[:80]}...")
        else:
            logger.warning("⚠️ MongoDB에서 대체재를 찾지 못했습니다.")
    except Exception as e:
        logger.error(f"❌ MongoDB 검색 실패: {e}")

    # 2단계: RAG 검색
    query = f"저칼륨 저인 식품 대체재 {dish_name}"
    docs = retriever.retrieve(query)
    total_length = sum(len(doc.page_content) for doc in docs)
    min_required_length = 500

    if total_length >= min_required_length:
        rag_context = "\n\n".join([doc.page_content for doc in docs])
        context_parts.append(f"[RAG 검색 결과]\n{rag_context}")
        logger.info("✅ 대체재 추천: RAG 검색 결과 사용")
    else:
        # 3단계: 웹 검색 Fallback
        logger.warning("⚠️ 대체재 추천: RAG 검색 결과 부족 -> 웹 검색 실행 중...")
        rag_context = "\n\n".join([doc.page_content for doc in docs]) if docs else "검색 결과 없음"
        web_results = search_for_nutrition_info(query, max_results=3)
        context_parts.append(f"[RAG 검색 결과]\n{rag_context}")
        context_parts.append(f"[웹 검색 결과]\n{web_results}")
        logger.info("✅ RAG + 웹 검색 결과 결합 완료")

    return "\n\n".join(context_parts)


def get_context_for_summary(retriever, topic: str) -> str:
    """요약을 위한 컨텍스트 검색 (RAG + 웹 검색 Fallback)"""
    docs = retriever.retrieve(topic)

    total_length = sum(len(doc.page_content) for doc in docs)
    min_required_length = 500

    if total_length >= min_required_length:
        context = "\n\n".join([doc.page_content for doc in docs])
        logger.info("✅ RAG 검색 결과 사용")
    else:
        logger.warning("⚠️ RAG 검색 결과 부족 -> 웹 검색 실행 중...")
        rag_context = "\n\n".join([doc.page_content for doc in docs])
        web_results = search_for_nutrition_info(topic, max_results=3)
        context = f"[RAG 검색 결과]\n{rag_context}\n\n[웹 검색 결과]\n{web_results}"
        logger.info("✅ RAG + 웹 검색 결과 결합 완료")

    return context


def get_context_for_quiz(retriever, topic: str) -> str:
    """문제 생성을 위한 컨텍스트 검색"""
    docs = retriever.retrieve(topic)
    context = "\n\n".join([doc.page_content for doc in docs])
    return context
