"""공통 모듈: LLM, 컨텍스트 검색 함수, Logger"""

import logging
from typing import Optional

from langchain_openai import ChatOpenAI

from src.utils.context_manager import MultiSourceContextManager
from src.utils.web_search import search_for_nutrition_info

# Logger 설정
logger = logging.getLogger(__name__)

_context_manager: Optional[MultiSourceContextManager] = None


def set_context_manager(manager: Optional[MultiSourceContextManager]):
    """워크플로우 초기화 시 컨텍스트 매니저를 주입"""
    global _context_manager
    _context_manager = manager


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
    """재료 추출 컨텍스트"""
    if _context_manager:
        context = _context_manager.collect_recipe_context(dish_name, include_web=True)
        if context:
            return context

    query = f"{dish_name} 재료 레시피"
    docs = retriever.retrieve(query)
    total_length = sum(len(doc.page_content) for doc in docs)
    min_required_length = 300

    if total_length >= min_required_length:
        context = "\n\n".join([doc.page_content for doc in docs])
        logger.info("✅ '%s' RAG 검색 결과 사용", dish_name)
    else:
        logger.warning("⚠️ '%s' RAG 검색 결과 부족 → 웹 검색 실행", dish_name)
        rag_context = "\n\n".join([doc.page_content for doc in docs]) if docs else "검색 결과 없음"
        web_results = search_for_nutrition_info(f"{dish_name} 레시피 재료", max_results=2)
        context = f"[RAG 검색 결과]\n{rag_context}\n\n[웹 검색 결과]\n{web_results}"

    return context


def get_context_for_recommendation(retriever, dish_name: str) -> str:
    """추천 컨텍스트"""
    if _context_manager:
        context = _context_manager.collect_recipe_context(dish_name, include_web=True)
        if context:
            return context

    query = f"저칼륨 저인 식품 대체재 {dish_name}"
    docs = retriever.retrieve(query)
    total_length = sum(len(doc.page_content) for doc in docs)
    min_required_length = 500

    if total_length >= min_required_length:
        context = "\n\n".join([doc.page_content for doc in docs])
        logger.info("✅ 대체재 추천: RAG 검색 결과 사용")
    else:
        logger.warning("⚠️ 대체재 추천: RAG 검색 결과 부족 → 웹 검색 실행")
        rag_context = "\n\n".join([doc.page_content for doc in docs])
        web_results = search_for_nutrition_info(query, max_results=3)
        context = f"[RAG 검색 결과]\n{rag_context}\n\n[웹 검색 결과]\n{web_results}"

    return context


def get_context_for_summary(retriever, topic: str) -> str:
    """요약 컨텍스트"""
    if _context_manager:
        context = _context_manager.collect_general_context(topic, include_web=True)
        if context:
            return context

    docs = retriever.retrieve(topic)
    total_length = sum(len(doc.page_content) for doc in docs)
    min_required_length = 500

    if total_length >= min_required_length:
        context = "\n\n".join([doc.page_content for doc in docs])
        logger.info("✅ RAG 검색 결과 사용")
    else:
        logger.warning("⚠️ RAG 검색 결과 부족 → 웹 검색 실행")
        rag_context = "\n\n".join([doc.page_content for doc in docs])
        web_results = search_for_nutrition_info(topic, max_results=3)
        context = f"[RAG 검색 결과]\n{rag_context}\n\n[웹 검색 결과]\n{web_results}"

    return context


def get_context_for_quiz(retriever, topic: str) -> str:
    """퀴즈 컨텍스트"""
    if _context_manager:
        context = _context_manager.collect_general_context(topic, include_web=True)
        if context:
            return context

    docs = retriever.retrieve(topic)
    return "\n\n".join([doc.page_content for doc in docs])


def retrieve_context(query: str, retriever, use_web_search: bool = True) -> dict:
    """워크플로우용 통합 컨텍스트 검색"""
    if _context_manager:
        context = _context_manager.collect_general_context(query, include_web=use_web_search)
        if context:
            result = {"context": context}
            if use_web_search:
                # 이미 웹 검색이 포함돼 있을 수 있으므로 별도 필드로 노출하지 않음
                pass
            return result

    try:
        docs = retriever.retrieve(query) if hasattr(retriever, "retrieve") else retriever.invoke(query)

        if docs and hasattr(docs[0], "page_content"):
            rag_context = "\n\n".join([doc.page_content for doc in docs])
        elif docs and isinstance(docs[0], str):
            rag_context = "\n\n".join(docs)
        else:
            rag_context = ""

        result = {"context": rag_context}

        if use_web_search and len(rag_context) < 300:
            logger.info("⚠️ RAG 결과 부족(%d자) → 웹 검색 추가", len(rag_context))
            web_results = search_for_nutrition_info(query, max_results=3)
            if web_results:
                result["web_results"] = web_results
                result["context"] = f"{rag_context}\n\n[웹 검색 추가 정보]\n{web_results}"

        return result

    except Exception as e:
        logger.error("❌ 컨텍스트 검색 오류: %s", e)
        return {"context": "", "error": str(e)}
