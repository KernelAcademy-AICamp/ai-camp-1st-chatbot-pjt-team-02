"""LangGraph 워크플로우 모듈 - query만 입력받음"""

import logging
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from src.chains import (
    create_intent_classifier,
    create_recommendation_chain,
    create_summary_chain,
    create_quiz_chain,
)
from src.chains.common import get_llm

logger = logging.getLogger(__name__)


# 상태 정의 - query만 필수 입력
class _WorkflowStateRequired(TypedDict):
    """필수 필드"""
    query: str  # 사용자 입력 (유일한 입력)


class WorkflowState(_WorkflowStateRequired, total=False):
    """워크플로우 상태 - query만 필수, 나머지는 자동 초기화"""
    intent: str  # 의도 분류 결과
    recommendation_result: Optional[str]  # 추천 결과
    final_result: str  # 최종 결과
    need_summary: bool  # 요약 필요 여부 (LLM이 판단)


def create_workflow_app(
    vectorstore,
    llm_config: Optional[dict] = None,
):
    """
    LangGraph 워크플로우 앱 생성

    Args:
        vectorstore: RAG 벡터스토어
        llm_config: LLM 설정 딕셔너리
            {
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": None,
                ...
            }

    Returns:
        컴파일된 워크플로우 그래프
    """
    if llm_config is None:
        llm_config = {}

    # 기본값 설정
    default_config = {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": None,
    }
    default_config.update(llm_config)

    # 리트리버 생성
    from src.rag.retriever import create_retriever
    retriever = create_retriever(vectorstore, retriever_type="basic", k=4)

    # 체인 생성
    logger.info("워크플로우 초기화 중...")
    intent_classifier = create_intent_classifier(
        model=default_config["model"],
        temperature=0.3,  # 의도분류는 낮은 온도 사용
        max_tokens=default_config["max_tokens"],
    )

    recommendation_chain = create_recommendation_chain(
        retriever,
        model=default_config["model"],
        temperature=default_config["temperature"],
        max_tokens=default_config["max_tokens"],
    )

    summary_chain = create_summary_chain(
        retriever,
        model=default_config["model"],
        temperature=default_config["temperature"],
        max_tokens=default_config["max_tokens"],
    )

    quiz_chain = create_quiz_chain(
        retriever,
        model=default_config["model"],
        temperature=default_config["temperature"],
        max_tokens=default_config["max_tokens"],
    )

    # 노드 함수 정의

    def classify_intent(state: WorkflowState) -> WorkflowState:
        """사용자 의도를 분류합니다."""
        query = state["query"]
        intent = intent_classifier.invoke({"query": query}).strip().lower()
        logger.info(f"🎯 의도 분류: {intent}")
        return {
            **state,
            "intent": intent,
            "need_summary": False,  # 초기값
        }

    def extract_dish_name(query: str) -> str:
        """사용자 질문에서 요리명을 추출합니다."""
        llm = get_llm(model=default_config["model"], temperature=0.3)
        extract_dish_prompt = ChatPromptTemplate.from_messages([
            ("system", "사용자의 질문에서 요리명만 추출하세요. 한 단어 또는 짧은 구문만 반환하세요."),
            ("user", "{query}")
        ])
        dish_extractor = extract_dish_prompt | llm | StrOutputParser()
        dish_name = dish_extractor.invoke({"query": query})
        return dish_name.strip()

    def run_recommendation(state: WorkflowState) -> WorkflowState:
        """추천 체인을 실행하고, LLM으로 요약 필요성을 판단합니다."""
        logger.info("🍳 추천 노드 실행 중...")

        # 요리명 추출
        dish_name = extract_dish_name(state["query"])
        logger.info(f"추출된 요리명: {dish_name}")

        # 추천 체인 실행
        result = recommendation_chain({"dish_name": dish_name})
        logger.info("✅ 추천 체인 완료")

        # LLM으로 요약 필요성 판단
        logger.info("🤔 요약 필요성 판단 중...")
        llm = get_llm(model=default_config["model"], temperature=0.3)
        summary_decision_prompt = ChatPromptTemplate.from_messages([
            ("system", """사용자 쿼리를 분석하여 추천 후 조리법과 주의사항 요약이 필요한지 판단하세요.

다음 중 하나만 반환하세요:
- "yes": 요약이 필요한 경우 (사용자가 조리법, 주의사항, 팁 등을 요청한 경우)
- "no": 요약이 불필요한 경우 (단순 재료 대체 추천만 원하는 경우)

판단 기준:
- "만드는 법", "조리법", "어떻게", "방법", "주의", "팁", "알려줄래" 등의 키워드 포함 → yes
- "추천", "대체", "뭐", "뭘", "뭐가", "가능한", "할 수" 등만 포함 → no"""),
            ("user", "{query}")
        ])

        summary_decision_chain = summary_decision_prompt | llm | StrOutputParser()
        decision = summary_decision_chain.invoke({"query": state["query"]}).strip().lower()

        need_summary = "yes" in decision
        logger.info(f"요약 필요성: {'필요' if need_summary else '불필요'} (판단: {decision})")

        return {
            **state,
            "recommendation_result": result,
            "final_result": result,
            "need_summary": need_summary,
        }

    def run_summary(state: WorkflowState) -> WorkflowState:
        """요약 체인을 실행합니다."""
        logger.info("📝 요약 노드 실행 중...")

        result = summary_chain({"topic": state["query"]})
        logger.info("✅ 요약 체인 완료")

        # 추천 결과가 있으면 결합, 없으면 그냥 요약 결과만 반환
        if state.get("recommendation_result"):
            final_result = f"{state['recommendation_result']}\n\n{'='*70}\n\n## 추가 정보\n\n{result}"
        else:
            final_result = result

        return {**state, "final_result": final_result}

    def run_quiz(state: WorkflowState) -> WorkflowState:
        """문제 생성 체인을 실행합니다."""
        logger.info("❓ 문제 생성 노드 실행 중...")

        result = quiz_chain({"topic": state["query"]})
        logger.info("✅ 문제 생성 노드 완료")

        return {**state, "final_result": result}

    # 라우터 함수
    def route_after_recommendation(state: WorkflowState) -> Literal["summary", "end"]:
        """추천 후 요약 필요성에 따라 다음 노드를 결정합니다 (LangGraph conditional_edges)"""
        if state.get("need_summary", False):
            logger.info("→ Summary 노드로 라우팅")
            return "summary"
        else:
            logger.info("→ 종료")
            return "end"

    def route_intent(state: WorkflowState) -> Literal["recommendation", "summary", "quiz"]:
        """의도에 따라 다음 노드를 결정합니다"""
        intent = state["intent"]

        if "recommendation" in intent:
            logger.info("→ Recommendation 노드로 라우팅")
            return "recommendation"
        elif "quiz" in intent:
            logger.info("→ Quiz 노드로 라우팅")
            return "quiz"
        else:
            logger.info("→ Summary 노드로 라우팅")
            return "summary"

    # LangGraph 구성
    workflow = StateGraph(WorkflowState)

    # 노드 추가
    workflow.add_node("classifier", classify_intent)
    workflow.add_node("recommendation", run_recommendation)
    workflow.add_node("summary", run_summary)
    workflow.add_node("quiz", run_quiz)

    # 엣지 추가
    workflow.set_entry_point("classifier")

    # 의도 분류 후 조건부 라우팅
    workflow.add_conditional_edges(
        "classifier",
        route_intent,
        {
            "recommendation": "recommendation",
            "summary": "summary",
            "quiz": "quiz",
        }
    )

    # Recommendation 후 조건부 라우팅 (need_summary 플래그 기반)
    workflow.add_conditional_edges(
        "recommendation",
        route_after_recommendation,
        {
            "summary": "summary",
            "end": END,
        }
    )

    # 각 체인 노드에서 종료로 연결
    workflow.add_edge("summary", END)
    workflow.add_edge("quiz", END)

    # 그래프 컴파일
    app = workflow.compile()
    logger.info("✅ 워크플로우 컴파일 완료")

    return app
