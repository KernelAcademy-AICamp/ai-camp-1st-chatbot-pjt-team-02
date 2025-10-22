"""추천 서브그래프 모듈"""

import logging
from typing import TypedDict, Dict, List, Optional, Literal
from langgraph.graph import StateGraph, END
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from src.chains.common import get_llm
from src.tools.ingredient_parser import parse_ingredients_with_llm
from src.tools.nutrition_calculator import evaluate_nutrition_with_llm
from src.utils.alternative_search import search_alternatives
import json

logger = logging.getLogger(__name__)


class RecommendationSubState(TypedDict, total=False):
    """추천 서브그래프 상태"""
    query: str  # 사용자 쿼리
    dish_name: str  # 요리명
    ingredients_raw: str  # 추출된 원시 재료 텍스트
    ingredients_parsed: List[Dict]  # 파싱된 재료 리스트
    nutrition_evaluation: Dict  # 영양 검증 결과
    alternatives_found: Dict  # 발견된 대체재
    final_recommendation: str  # 최종 추천 결과
    requires_alternative: bool  # 대체재 필요 여부


def create_recommendation_subgraph(retriever, llm_config: Optional[Dict] = None, web_search_fn=None, mongo_client=None):
    """
    추천 서브그래프 생성

    Args:
        retriever: RAG 리트리버
        llm_config: LLM 설정
        web_search_fn: 웹 검색 함수 (선택)
        mongo_client: MongoDB 클라이언트 (선택)

    Returns:
        컴파일된 서브그래프
    """
    if llm_config is None:
        llm_config = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": None,
        }

    logger.info("🔧 추천 서브그래프 생성 중...")

    # LLM 인스턴스 생성
    llm = get_llm(
        model=llm_config["model"],
        temperature=llm_config["temperature"],
        max_tokens=llm_config.get("max_tokens")
    )

    def extract_ingredients(state: RecommendationSubState) -> RecommendationSubState:
        """요리에서 재료를 추출합니다."""
        logger.info(f"🥘 재료 추출 중: {state['dish_name']}")

        try:
            # RAG 검색으로 레시피 찾기
            from src.chains.common import retrieve_context
            context_data = retrieve_context(state["dish_name"], retriever, use_web_search=False)
            context = context_data.get("context", "")

            if not context:
                logger.warning(f"⚠️ '{state['dish_name']}'에 대한 레시피를 찾을 수 없음")
                # 일반 지식으로 추출 시도
                context = f"일반적인 {state['dish_name']} 레시피"

            # 재료 추출 프롬프트
            extract_prompt = ChatPromptTemplate.from_messages([
                ("system", """당신은 요리 전문가입니다.
주어진 요리명과 컨텍스트를 바탕으로 필요한 재료들을 추출하세요.

출력 형식:
- 재료명과 분량을 명확히 구분
- 각 재료는 줄바꿈으로 구분
- 예시: "돼지고기 300g", "김치 200g", "두부 1모"
"""),
                ("user", """요리명: {dish_name}

컨텍스트:
{context}

위 요리에 필요한 모든 재료를 나열하세요.""")
            ])

            extract_chain = extract_prompt | llm | StrOutputParser()
            ingredients_raw = extract_chain.invoke({
                "dish_name": state["dish_name"],
                "context": context
            })

            logger.info(f"✅ 재료 추출 완료: {len(ingredients_raw.split())} 단어")

            return {
                **state,
                "ingredients_raw": ingredients_raw
            }

        except Exception as e:
            logger.error(f"❌ 재료 추출 오류: {e}")
            return {
                **state,
                "ingredients_raw": f"{state['dish_name']}의 일반적인 재료들"
            }

    def parse_ingredients(state: RecommendationSubState) -> RecommendationSubState:
        """추출된 재료를 구조화된 형태로 파싱합니다."""
        logger.info("🔍 재료 파싱 중...")

        try:
            # 재료 파싱 (LLM 사용)
            parsed = parse_ingredients_with_llm(state["ingredients_raw"])

            if not parsed:
                logger.warning("⚠️ 재료 파싱 결과 없음")
                # 간단한 파싱 시도
                lines = state["ingredients_raw"].strip().split("\n")
                parsed = []
                for line in lines:
                    if line.strip():
                        parsed.append({
                            "name": line.strip(),
                            "amount": "적당량",
                            "unit": ""
                        })

            logger.info(f"✅ {len(parsed)}개 재료 파싱 완료")

            return {
                **state,
                "ingredients_parsed": parsed
            }

        except Exception as e:
            logger.error(f"❌ 재료 파싱 오류: {e}")
            return {
                **state,
                "ingredients_parsed": []
            }

    def evaluate_nutrition(state: RecommendationSubState) -> RecommendationSubState:
        """파싱된 재료의 영양 정보를 평가합니다."""
        logger.info("📊 영양 평가 중...")

        try:
            if not state["ingredients_parsed"]:
                logger.warning("⚠️ 파싱된 재료가 없어 영양 평가 생략")
                return {
                    **state,
                    "nutrition_evaluation": {},
                    "requires_alternative": False
                }

            # 영양 평가 수행
            evaluation = evaluate_nutrition_with_llm(state["ingredients_parsed"])

            # 대체재 필요 여부 판단
            requires_alternative = False
            if evaluation:
                # 고칼륨, 고나트륨, 고인 재료가 있는지 확인
                for ingredient in evaluation.get("ingredients", []):
                    if any([
                        ingredient.get("potassium_level") == "high",
                        ingredient.get("sodium_level") == "high",
                        ingredient.get("phosphorus_level") == "high"
                    ]):
                        requires_alternative = True
                        break

            logger.info(f"✅ 영양 평가 완료 - 대체재 필요: {requires_alternative}")

            return {
                **state,
                "nutrition_evaluation": evaluation,
                "requires_alternative": requires_alternative
            }

        except Exception as e:
            logger.error(f"❌ 영양 평가 오류: {e}")
            return {
                **state,
                "nutrition_evaluation": {},
                "requires_alternative": True  # 안전을 위해 대체재 검색
            }

    def find_alternatives(state: RecommendationSubState) -> RecommendationSubState:
        """문제가 있는 재료의 대체재를 찾습니다. (우선순위: MongoDB -> RAG CSV -> RAG PDF -> Web)"""
        logger.info("🔄 대체재 검색 중 (우선순위: MongoDB -> RAG CSV -> RAG PDF -> Web)...")

        try:
            alternatives = {}

            # 영양 평가 결과에서 문제 재료 찾기
            evaluation = state.get("nutrition_evaluation", {})
            for ingredient in evaluation.get("ingredients", []):
                name = ingredient.get("name", "")

                # 고칼륨, 고나트륨, 고인 재료에 대해 대체재 검색
                if any([
                    ingredient.get("potassium_level") == "high",
                    ingredient.get("sodium_level") == "high",
                    ingredient.get("phosphorus_level") == "high"
                ]):
                    logger.info(f"🔍 '{name}'의 대체재 검색 중...")

                    # MongoDB -> RAG (CSV) -> RAG (PDF) -> Web 우선순위로 검색
                    alt_result = search_alternatives(
                        ingredient=name,
                        nutrient_types=None,
                        max_results=5,
                        retriever=retriever,  # RAG 리트리버 전달
                        use_web_search=True,  # 웹 검색 활성화
                        mongo_client=mongo_client  # MongoDB 클라이언트 전달
                    )

                    if alt_result and len(alt_result) > 0:
                        alternatives[name] = alt_result
                        source = alt_result[0].get('source', 'unknown')
                        logger.info(f"✅ '{name}'의 대체재 {len(alt_result)}개 발견 (소스: {source})")

            logger.info(f"✅ 대체재 검색 완료: {len(alternatives)}개 재료의 대체재 발견")

            return {
                **state,
                "alternatives_found": alternatives
            }

        except Exception as e:
            logger.error(f"❌ 대체재 검색 오류: {e}")
            return {
                **state,
                "alternatives_found": {}
            }

    def generate_recommendation(state: RecommendationSubState) -> RecommendationSubState:
        """최종 추천 결과를 생성합니다."""
        logger.info("📝 최종 추천 생성 중...")

        try:
            # 추천 생성 프롬프트
            recommendation_prompt = ChatPromptTemplate.from_messages([
                ("system", """당신은 신장질환 환자를 위한 영양 전문가입니다.

주어진 정보를 바탕으로 친절하고 실용적인 추천을 제공하세요.

응답 형식:
1. 요리 개요
2. 주요 재료 분석
3. 대체재 추천 (있는 경우)
4. 조리 시 주의사항
5. 영양 팁

마크다운 형식을 사용하여 읽기 쉽게 작성하세요."""),
                ("user", """요리명: {dish_name}

재료 목록:
{ingredients}

영양 평가:
{evaluation}

발견된 대체재:
{alternatives}

위 정보를 바탕으로 신장질환 환자를 위한 추천을 작성하세요.""")
            ])

            # 데이터 준비
            ingredients_text = "\n".join([
                f"- {ing.get('name', '')} {ing.get('amount', '')} {ing.get('unit', '')}"
                for ing in state.get("ingredients_parsed", [])
            ])

            evaluation_text = json.dumps(state.get("nutrition_evaluation", {}), ensure_ascii=False, indent=2)

            alternatives_text = ""
            for original, alts in state.get("alternatives_found", {}).items():
                alternatives_text += f"\n**{original}의 대체재:**\n"
                for alt in alts[:3]:  # 상위 3개만
                    source = alt.get('source', 'unknown')
                    조리방법 = alt.get('조리방법', '조리 필요')
                    감소비율 = alt.get('칼륨감소비율', 'N/A')

                    alternatives_text += f"- {alt.get('대체식품', 'N/A')} "
                    alternatives_text += f"(칼륨 {감소비율}% 감소) "
                    alternatives_text += f"[{source}]\n"
                    alternatives_text += f"  조리방법: {조리방법}\n"

                    # 출처에 따른 추가 정보 표시
                    if source == "MongoDB":
                        alternatives_text += f"  출처: MongoDB 대체재 데이터베이스\n"
                    elif source == "RAG (CSV)":
                        출처 = alt.get('출처', '데이터베이스')
                        alternatives_text += f"  출처: {출처}\n"
                    elif source == "RAG (PDF)":
                        출처 = alt.get('출처', '의료 문서')
                        alternatives_text += f"  출처: {출처}\n"
                        출처내용 = alt.get('출처내용', '')
                        if 출처내용:
                            alternatives_text += f"  참고: {출처내용}...\n"
                    elif source == "Web":
                        설명 = alt.get('설명', '')
                        if 설명:
                            alternatives_text += f"  참고: {설명}...\n"

            if not alternatives_text:
                alternatives_text = "특별한 대체재가 필요하지 않습니다."

            # 추천 생성
            recommendation_chain = recommendation_prompt | llm | StrOutputParser()
            recommendation = recommendation_chain.invoke({
                "dish_name": state["dish_name"],
                "ingredients": ingredients_text,
                "evaluation": evaluation_text,
                "alternatives": alternatives_text
            })

            logger.info("✅ 추천 생성 완료")

            return {
                **state,
                "final_recommendation": recommendation
            }

        except Exception as e:
            logger.error(f"❌ 추천 생성 오류: {e}")
            return {
                **state,
                "final_recommendation": f"'{state['dish_name']}'에 대한 추천을 생성할 수 없습니다."
            }

    def route_after_evaluation(state: RecommendationSubState) -> Literal["find_alternatives", "generate_recommendation"]:
        """영양 평가 후 라우팅"""
        if state.get("requires_alternative", False):
            logger.info("→ 대체재 검색 필요")
            return "find_alternatives"
        else:
            logger.info("→ 바로 추천 생성")
            return "generate_recommendation"

    # 서브그래프 구성
    workflow = StateGraph(RecommendationSubState)

    # 노드 추가
    workflow.add_node("extract_ingredients", extract_ingredients)
    workflow.add_node("parse_ingredients", parse_ingredients)
    workflow.add_node("evaluate_nutrition", evaluate_nutrition)
    workflow.add_node("find_alternatives", find_alternatives)
    workflow.add_node("generate_recommendation", generate_recommendation)

    # 엣지 추가
    workflow.set_entry_point("extract_ingredients")
    workflow.add_edge("extract_ingredients", "parse_ingredients")
    workflow.add_edge("parse_ingredients", "evaluate_nutrition")

    # 조건부 라우팅
    workflow.add_conditional_edges(
        "evaluate_nutrition",
        route_after_evaluation,
        {
            "find_alternatives": "find_alternatives",
            "generate_recommendation": "generate_recommendation"
        }
    )

    workflow.add_edge("find_alternatives", "generate_recommendation")
    workflow.add_edge("generate_recommendation", END)

    # 컴파일
    app = workflow.compile()
    logger.info("✅ 추천 서브그래프 생성 완료")

    return app