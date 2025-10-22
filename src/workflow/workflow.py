"""LangGraph 워크플로우 모듈 - query만 입력받음"""

import base64
import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Literal, Optional, TypedDict

from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import END, StateGraph

from src.chains import (
    create_intent_classifier,
    create_summary_chain,
)
from src.chains.common import get_llm, retrieve_context, set_context_manager
from src.chains.integrated_quiz_chain import create_integrated_quiz_chain
from src.workflow.recommendation_subgraph import create_recommendation_subgraph
from src.utils.context_manager import MultiSourceContextManager
from src.utils.web_search import search_for_nutrition_info

logger = logging.getLogger(__name__)


# 상태 정의 - query만 필수 입력
class _WorkflowStateRequired(TypedDict):
    """필수 필드"""
    query: str  # 사용자 입력 (유일한 입력)


class WorkflowState(_WorkflowStateRequired, total=False):
    """워크플로우 상태 - query만 필수, 나머지는 자동 초기화"""
    file_type: Literal["pdf", "image", "text"]
    file_name: str
    file_content: str
    pdf_text: str
    image_analysis: str
    attachment_context: str
    enriched_query: str
    attachments_used: List[str]
    intent: str  # 의도 분류 결과
    final_result: str  # 최종 결과
    need_summary: bool  # 요약 필요 여부 (LLM이 판단)

    # RecommendationSubState 필드들 (서브그래프 호환성)
    dish_name: str  # 요리명
    ingredients_raw: str  # 추출된 원시 재료 텍스트
    ingredients_parsed: List[Dict]  # 파싱된 재료 리스트
    nutrition_evaluation: Dict  # 영양 검증 결과
    alternatives_found: Dict  # 발견된 대체재
    final_recommendation: str  # 최종 추천 결과
    requires_alternative: bool  # 대체재 필요 여부
    recommendation_result: Optional[str]  # 추천 결과


def create_workflow_app(
    vectorstore,
    llm_config: Optional[dict] = None,
):
    """
    LangGraph 워크플로우 앱 생성

    Args:
        vectorstore: RAG 벡터스토어
        llm_config: 체인별 LLM 설정 딕셔너리
            {
                "intent_classifier": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.3,
                    "max_tokens": None,
                },
                "recommendation": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.7,
                    "max_tokens": None,
                },
                "summary": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.7,
                    "max_tokens": None,
                },
                "quiz": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.7,
                    "max_tokens": None,
                }
            }

    Returns:
        컴파일된 워크플로우 그래프
    """
    if llm_config is None:
        llm_config = {}

    # 체인별 기본 설정
    default_configs = {
        "intent_classifier": {
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "max_tokens": None,
        },
        "recommendation": {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": None,
        },
        "summary": {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": None,
        },
        "quiz": {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": None,
        }
    }

    # 사용자 설정으로 업데이트
    for chain_name in default_configs:
        if chain_name in llm_config:
            default_configs[chain_name].update(llm_config[chain_name])

    # 리트리버 생성 (vectorstore가 있을 때만)
    retriever = None
    if vectorstore is not None:
        from src.rag.retriever import create_retriever
        try:
            retriever = create_retriever(vectorstore, retriever_type="basic", k=4)
            logger.info("✅ 메인 리트리버 생성 완료")
        except Exception as e:
            logger.warning(f"⚠️ 리트리버 생성 실패: {e}")
            retriever = None
    else:
        logger.info("ℹ️ Vectorstore 없음, 리트리버 없이 진행")

    # 다중 소스 컨텍스트 매니저 구성
    additional_retrievers: Dict[str, Optional[object]] = {}
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        project_root = Path(__file__).resolve().parents[2]
        vector_dir = project_root / "data" / "vectorstore"

        for name, folder in {"recipe": "recipe_vectors", "food": "food_vectors"}.items():
            vs_path = vector_dir / folder
            if not vs_path.exists():
                continue
            try:
                vector = FAISS.load_local(
                    str(vs_path),
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                from src.rag.retriever import create_retriever
                additional_retrievers[name] = create_retriever(vector, retriever_type="basic", k=4)
                logger.info("📚 추가 벡터스토어 로드: %s", name)
            except Exception as exc:
                logger.warning("⚠️ %s 벡터스토어 로드 실패: %s", name, exc)
    except Exception as exc:
        logger.warning("⚠️ 추가 벡터스토어 초기화 실패: %s", exc)

    mongo_client = None
    try:
        from src.database.mongo_client import get_mongo_client
        mongo_client = get_mongo_client()
    except Exception as exc:
        logger.warning("⚠️ MongoDB 클라이언트 초기화 실패: %s", exc)

    context_manager = MultiSourceContextManager(
        pdf_retriever=retriever,
        csv_retrievers=additional_retrievers,
        mongo_client=mongo_client,
        web_search_fn=search_for_nutrition_info,
    )
    set_context_manager(context_manager)

    # 체인 생성
    logger.info("워크플로우 초기화 중...")
    intent_classifier = create_intent_classifier(
        model=default_configs["intent_classifier"]["model"],
        temperature=default_configs["intent_classifier"]["temperature"],
        max_tokens=default_configs["intent_classifier"]["max_tokens"],
    )

    recommendation_subgraph = create_recommendation_subgraph(
        retriever,
        llm_config=default_configs["recommendation"],
        web_search_fn=search_for_nutrition_info,
        mongo_client=mongo_client
    )

    summary_chain = create_summary_chain(
        retriever,
        model=default_configs["summary"]["model"],
        temperature=default_configs["summary"]["temperature"],
        max_tokens=default_configs["summary"]["max_tokens"],
    )

    quiz_chain = create_integrated_quiz_chain(
        retriever,
        model=default_configs["quiz"]["model"],
        temperature=default_configs["quiz"]["temperature"],
    )

    # 노드 함수 정의
    def _decode_file_content(content: str) -> bytes:
        """data URI 또는 순수 base64 문자열을 디코딩"""
        if not content:
            return b""
        try:
            if content.startswith("data:") and "," in content:
                _, encoded_part = content.split(",", 1)
                return base64.b64decode(encoded_part)
            return base64.b64decode(content)
        except Exception as exc:
            logger.warning(f"⚠️ 파일 디코딩 실패: {exc}")
            raise

    def _extract_pdf_text(pdf_bytes: bytes) -> str:
        """PDF 바이트에서 텍스트 추출"""
        from pypdf import PdfReader

        pdf_buffer = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_buffer)
        extracted = []
        for page in reader.pages:
            try:
                page_text = page.extract_text()
                if page_text:
                    extracted.append(page_text)
            except Exception as exc:
                logger.warning(f"⚠️ PDF 페이지 텍스트 추출 실패: {exc}")
        return "\n".join(extracted)

    def _get_effective_query(state: WorkflowState) -> str:
        """첨부 기반 확장 쿼리가 있으면 우선 사용"""
        logger.info(f"🔍 효과적인 쿼리 결정 중... : {state.get('enriched_query') or state['query']}")
        return state.get("enriched_query") or state["query"]

    def prepare_multimodal_input(state: WorkflowState) -> WorkflowState:
        """첨부 파일을 전처리하여 쿼리에 필요한 컨텍스트를 추가"""
        base_query = state["query"]
        attachments_used: List[str] = []
        context_sections: List[str] = []

        pdf_text = state.get("pdf_text")
        image_analysis = state.get("image_analysis")
        file_type = state.get("file_type")
        file_content = state.get("file_content")

        # PDF 처리
        if file_type == "pdf" or (file_content and file_type == "application/pdf"):
            try:
                if not pdf_text and file_content:
                    pdf_bytes = _decode_file_content(file_content)
                    pdf_text = _extract_pdf_text(pdf_bytes)
                if pdf_text:
                    trimmed_pdf = pdf_text[:5000]  # 과도한 길이 방지
                    context_sections.append(f"[PDF 문서 내용]\n{trimmed_pdf}")
                    attachments_used.append("pdf")
            except Exception as exc:
                logger.error(f"❌ PDF 첨부 처리 실패: {exc}", exc_info=True)

        # 이미지 처리
        if file_type == "image" or (file_content and str(file_type).startswith("image/")):
            try:
                if not image_analysis and file_content:
                    analysis_result = analyze_food_image(file_content, base_query)
                    if analysis_result.get("status") == "success":
                        image_analysis = analysis_result.get("analysis")
                    else:
                        logger.warning("⚠️ 이미지 분석 실패, 첨부 컨텍스트에 포함되지 않음")
                if image_analysis:
                    logger.info(f'{image_analysis}')
                    context_sections.append(f"[이미지 분석 결과]\n{image_analysis}")
                    attachments_used.append("image")
            except Exception as exc:
                logger.error(f"❌ 이미지 첨부 처리 실패: {exc}", exc_info=True)

        # 기존 첨부 컨텍스트와 병합
        attachment_context = state.get("attachment_context", "")
        if context_sections:
            new_context = "\n\n".join(context_sections)
            attachment_context = f"{attachment_context}\n\n{new_context}".strip()

        enriched_query = base_query
        if attachment_context:
            enriched_query = f"{attachment_context}\n\n[사용자 질문]\n{base_query}"
            logger.info(f"📎 첨부 컨텍스트 적용: {attachments_used}")

        return {
            **state,
            "pdf_text": pdf_text,
            "image_analysis": image_analysis,
            "attachment_context": attachment_context,
            "enriched_query": enriched_query,
            "attachments_used": attachments_used,
        }

    def classify_intent(state: WorkflowState) -> WorkflowState:
        """사용자 의도를 분류합니다."""
        query = _get_effective_query(state)
        intent = intent_classifier.invoke({"query": query}).strip().lower()
        logger.info(f"🎯 의도 분류: {intent}")
        return {
            **state,
            "intent": intent,
            "need_summary": False,  # 초기값
        }

    def prepare_recommendation(state: WorkflowState) -> WorkflowState:
        """추천 전 준비 - 요리명 추출"""
        logger.info("🍳 추천 준비 중...")

        query_for_recommendation = _get_effective_query(state)

        llm = get_llm(
            model=default_configs["recommendation"]["model"],
            temperature=0.3
        )
        extract_dish_prompt = ChatPromptTemplate.from_messages([
            ("system", "사용자의 질문에서 요리명만 추출하세요. 한 단어 또는 짧은 구문만 반환하세요."),
            ("user", "{query}")
        ])
        dish_extractor = extract_dish_prompt | llm | StrOutputParser()
        dish_name = dish_extractor.invoke({"query": query_for_recommendation})
        logger.info(f"추출된 요리명: {dish_name.strip()}")

        return {
            **state,
            "dish_name": dish_name.strip(),
            "ingredients_raw": "",
            "ingredients_parsed": [],
            "nutrition_evaluation": {},
            "alternatives_found": {},
            "final_recommendation": "",
            "requires_alternative": False,
        }

    def evaluate_summary_need(state: WorkflowState) -> WorkflowState:
        """추천 후 요약 필요성 판단"""
        logger.info("✅ 추천 서브그래프 완료")
        logger.info("🤔 요약 필요성 판단 중...")

        llm = get_llm(
            model=default_configs["recommendation"]["model"],
            temperature=0.3
        )
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
        decision = summary_decision_chain.invoke({"query": _get_effective_query(state)}).strip().lower()

        need_summary = "yes" in decision
        logger.info(f"요약 필요성: {'필요' if need_summary else '불필요'} (판단: {decision})")

        # 최종 결과에 추천 내용 저장
        result = state.get("final_recommendation", "추천 결과를 생성할 수 없습니다.")

        return {
            **state,
            "recommendation_result": result,
            "final_result": result,
            "need_summary": need_summary,
        }

    def _is_food_nutrition_related(query: str) -> bool:
        """쿼리가 음식/영양 관련인지 판단"""

        # 단어 경계를 고려한 키워드 매칭을 위해 개선
        import re

        food_keywords = [
            # 음식 관련
            "요리", "음식", "식품", "레시피", "조리법", "만드는 법",
            "재료", "식재료", "반찬", "국", "찌개", "밥", "면", "빵",
            "김치", "된장", "고추장", "간장", "소금", "설탕",

            # 영양 관련
            "영양", "칼로리", "단백질", "탄수화물", "지방", "비타민", "무기질",
            "칼륨", "나트륨", "인산", "칼슘", "철분", "섬유질",  # "인" → "인산"으로 변경
            "저칼륨", "저나트륨", "저인", "저염", "저당",

            # 질환 관련
            "신장", "신장질환", "CKD", "투석", "혈액투석", "복막투석",
            "당뇨", "고혈압", "식단", "식이요법", "식사",  # "환자" 제거 (너무 일반적)

            # 기타 식품 관련
            "채소", "과일", "육류", "생선", "해산물", "유제품", "곡류",
            "견과류", "콩", "두부", "계란", "우유", "치즈",

            # 추가 음식 관련 키워드
            "끓이", "굽", "볶", "찜", "튀김", "삶", "조림"
        ]

        query_lower = query.lower()

        # 정확한 단어 매칭을 위한 패턴 (단어 경계 고려)
        for keyword in food_keywords:
            # 짧은 키워드(2글자 이하)는 단어 경계 체크
            if len(keyword) <= 2:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, query_lower):
                    logger.debug(f"🍳 음식 키워드 매칭: '{keyword}'")
                    return True
            else:
                # 긴 키워드는 부분 매칭 허용
                if keyword in query_lower:
                    logger.debug(f"🍳 음식 키워드 매칭: '{keyword}'")
                    return True

        return False

    def _handle_general_query(query: str, retriever) -> str:
        """일반 질의를 PDF + RAG + Web으로 처리"""
        logger.info("🔍 일반 질의 처리 중 (PDF + RAG + Web)...")

        try:
            # 1. RAG 검색
            context_data = retrieve_context(query, retriever, use_web_search=True)
            context = context_data.get("context", "")

            if not context:
                logger.warning("⚠️ RAG 검색 결과 없음")
                context = "관련 문서를 찾을 수 없습니다."

            # 2. LLM으로 답변 생성
            llm = get_llm(model="gpt-4o-mini", temperature=0.7)

            general_prompt = ChatPromptTemplate.from_messages([
                ("system", """당신은 유용한 AI 어시스턴트입니다.

제공된 컨텍스트를 바탕으로 사용자 질문에 답변해주세요.
컨텍스트에 답변이 없다면 일반 지식을 활용해서 답변해주세요.

답변 형식:
- 명확하고 구체적으로 설명
- 필요시 예시 포함
- 마크다운 형식 사용"""),
                ("user", """컨텍스트:
{context}

질문: {query}""")
            ])

            general_chain = general_prompt | llm | StrOutputParser()
            result = general_chain.invoke({
                "context": context,
                "query": query
            })

            # 웹 검색 정보 추가 (있는 경우)
            if "web_results" in context_data:
                result += "\n\n### 웹 검색 결과\n" + context_data["web_results"]

            logger.info("✅ 일반 질의 처리 완료")
            return result

        except Exception as e:
            logger.error(f"❌ 일반 질의 처리 오류: {e}")
            return f"질문에 대한 답변을 생성할 수 없습니다. 오류: {str(e)}"

    def run_summary(state: WorkflowState) -> WorkflowState:
        """요약 체인을 실행합니다."""
        logger.info("📝 요약 노드 실행 중...")

        query = _get_effective_query(state)

        # 음식/영양 관련 여부 확인
        if _is_food_nutrition_related(query):
            logger.info("🍳 음식/영양 관련 질문 - 전문 요약 체인 사용")

            summary_inputs = {"topic": query}
            if state.get("attachment_context"):
                summary_inputs["attachment_context"] = state["attachment_context"]

            result = summary_chain(summary_inputs)
            logger.info("✅ 요약 체인 완료")

            # 추천 결과가 있으면 결합, 없으면 그냥 요약 결과만 반환
            if state.get("recommendation_result"):
                final_result = f"{state['recommendation_result']}\n\n{'='*70}\n\n## 추가 정보\n\n{result}"
            else:
                final_result = result
        else:
            logger.info("📚 일반 질문 - RAG + Web 검색 처리")
            final_result = _handle_general_query(query, retriever)

        return {**state, "final_result": final_result}

    def _handle_general_quiz(query: str, retriever) -> str:
        """일반 주제에 대한 퀴즈 생성 (RAG + Web 기반)"""
        logger.info("📖 일반 퀴즈 생성 중 (RAG + Web 기반)...")

        try:
            # 1. RAG 검색으로 컨텍스트 확보
            context_data = retrieve_context(query, retriever, use_web_search=True)
            context = context_data.get("context", "")

            if not context:
                context = "일반 지식을 기반으로 문제를 생성합니다."

            # 2. LLM으로 퀴즈 생성
            llm = get_llm(model="gpt-4o-mini", temperature=0.7)

            quiz_prompt = ChatPromptTemplate.from_messages([
                ("system", """당신은 교육 전문가입니다.

주어진 주제와 컨텍스트를 바탕으로 학습용 문제를 생성하세요.

문제 생성 규칙:
1. 객관식 2개, 주관식 1개
2. 난이도는 중급 수준
3. 명확한 정답이 있어야 함
4. 교육적 가치가 있어야 함

출력 형식:
### 📝 학습 문제

#### 객관식 문제 1
[문제]
1) 선택지 1
2) 선택지 2
3) 선택지 3
4) 선택지 4
**정답**: [번호]
**해설**: [설명]

#### 객관식 문제 2
[문제]
1) 선택지 1
2) 선택지 2
3) 선택지 3
4) 선택지 4
**정답**: [번호]
**해설**: [설명]

#### 주관식 문제
[문제]
**예시 답안**: [답안]
**채점 포인트**: [포인트]"""),
                ("user", """컨텍스트:
{context}

주제: {query}

위 주제와 컨텍스트를 바탕으로 학습 문제를 생성해주세요.""")
            ])

            quiz_chain = quiz_prompt | llm | StrOutputParser()
            result = quiz_chain.invoke({
                "context": context,
                "query": query
            })

            logger.info("✅ 일반 퀴즈 생성 완료")
            return result

        except Exception as e:
            logger.error(f"❌ 일반 퀴즈 생성 오류: {e}")
            return f"퀴즈 생성 중 오류가 발생했습니다: {str(e)}"

    def run_quiz(state: WorkflowState) -> WorkflowState:
        """문제 생성 체인을 실행합니다."""
        logger.info("❓ 문제 생성 노드 실행 중...")

        query = _get_effective_query(state)

        # 음식/영양 관련 여부 확인
        if _is_food_nutrition_related(query):
            logger.info("🍳 음식/영양 관련 퀴즈 - 전문 퀴즈 체인 사용")

            # IntegratedQuizChain은 generate_quiz 메서드 사용
            result = quiz_chain.generate_quiz(
                topic=query,
                additional_context=state.get("attachment_context")
            )
        else:
            logger.info("📚 일반 주제 퀴즈 - RAG + Web 기반 생성")
            result = _handle_general_quiz(query, retriever)

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

    def route_intent(state: WorkflowState) -> Literal["prepare_recommendation", "summary", "quiz"]:
        """의도에 따라 다음 노드를 결정합니다"""
        intent = state["intent"]

        if "recommendation" in intent:
            logger.info("→ Prepare Recommendation 노드로 라우팅")
            return "prepare_recommendation"
        elif "quiz" in intent:
            logger.info("→ Quiz 노드로 라우팅")
            return "quiz"
        else:
            logger.info("→ Summary 노드로 라우팅")
            return "summary"

    # LangGraph 구성
    workflow = StateGraph(WorkflowState)

    # 노드 추가
    workflow.add_node("prepare_input", prepare_multimodal_input)
    workflow.add_node("classifier", classify_intent)
    workflow.add_node("prepare_recommendation", prepare_recommendation)
    workflow.add_node("recommendation_subgraph", recommendation_subgraph)
    workflow.add_node("evaluate_summary_need", evaluate_summary_need)
    workflow.add_node("summary", run_summary)
    workflow.add_node("quiz", run_quiz)

    # 엣지 추가
    workflow.set_entry_point("prepare_input")
    workflow.add_edge("prepare_input", "classifier")

    # 의도 분류 후 조건부 라우팅
    workflow.add_conditional_edges(
        "classifier",
        route_intent,
        {
            "prepare_recommendation": "prepare_recommendation",
            "summary": "summary",
            "quiz": "quiz",
        }
    )

    # 추천 파이프라인 엣지
    workflow.add_edge("prepare_recommendation", "recommendation_subgraph")
    workflow.add_edge("recommendation_subgraph", "evaluate_summary_need")

    # 요약 필요성에 따른 조건부 라우팅
    workflow.add_conditional_edges(
        "evaluate_summary_need",
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
    setattr(app, "context_manager", context_manager)

    return app


# ==================== PDF 처리 함수 ====================

def process_pdf_query(pdf_bytes: bytes, query: str) -> Dict:
    """
    PDF 파일 기반 쿼리 처리

    Args:
        pdf_bytes: PDF 파일 바이트
        query: 사용자 질문

    Returns:
        처리 결과 딕셔너리
    """
    try:
        from pypdf import PdfReader
        logger.info(f"📄 PDF 처리 시작: {len(pdf_bytes)} bytes")

        # PDF에서 텍스트 추출
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PdfReader(pdf_file)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text()

        # 추출된 텍스트와 쿼리를 결합
        combined_query = f"문서 내용:\n{pdf_text}\n\n사용자 질문: {query}"

        logger.info(f"✅ PDF 텍스트 추출 완료: {len(pdf_text)} 글자")

        return {
            "status": "success",
            "response": combined_query
        }

    except Exception as e:
        logger.error(f"❌ PDF 처리 오류: {e}", exc_info=True)
        return {
            "status": "error",
            "response": f"PDF 처리 중 오류: {str(e)}"
        }


def summarize_pdf(pdf_bytes: bytes) -> Dict:
    """
    PDF 파일 요약

    Args:
        pdf_bytes: PDF 파일 바이트

    Returns:
        요약 결과 딕셔너리
    """
    try:
        from pypdf import PdfReader
        logger.info(f"📑 PDF 요약 시작")

        # PDF에서 텍스트 추출
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PdfReader(pdf_file)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text()

        logger.info(f"✅ PDF 텍스트 추출 완료: {len(pdf_text)} 글자")

        return {
            "status": "success",
            "summary": f"PDF 요약:\n{pdf_text[:500]}..."
        }

    except Exception as e:
        logger.error(f"❌ PDF 요약 오류: {e}", exc_info=True)
        return {
            "status": "error",
            "summary": f"PDF 요약 중 오류: {str(e)}"
        }


# ==================== 이미지 처리 함수 ====================

def analyze_food_image(image_url: str, query: Optional[str] = None) -> Dict:
    """
    OpenAI Vision API를 사용하여 음식 이미지 분석

    Args:
        image_url: 이미지 URL 또는 base64 인코딩
        query: 사용자 질문

    Returns:
        분석 결과 딕셔너리
    """
    try:
        import base64
        from pathlib import Path
        import requests
        from src.chains.common import get_llm

        logger.info(f"🍽️ 음식 이미지 분석 시작 (Vision API)")

        # 이미지 준비
        image_data = _prepare_image_for_vision(image_url)

        # 이미지가 URL인지 Base64인지 확인
        if isinstance(image_data, dict) and "image_url" in image_data:
            image_content = image_data["image_url"]["url"]
        else:
            image_content = image_url

        analysis_prompt = f"""이미지에 나타난 음식을 분석하고, 어떠한 음식인지만 알려주세요."""

        # OpenAI Vision API로 직접 호출
        from openai import OpenAI
        client = OpenAI()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_content
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        logger.info("✅ 이미지 분석 완료")

        return {
            "status": "success",
            "analysis": response.choices[0].message.content
        }

    except Exception as e:
        logger.error(f"❌ 이미지 분석 오류: {e}", exc_info=True)
        return {
            "status": "error",
            "analysis": f"이미지 분석 중 오류: {str(e)}"
        }


def _prepare_image_for_vision(image_url: str) -> Dict:
    """
    이미지를 Vision API 호출에 적합한 형식으로 준비

    Args:
        image_url: 이미지 URL 또는 base64 인코딩

    Returns:
        Vision API용 이미지 데이터
    """
    try:
        # URL인 경우
        if image_url.startswith(("http://", "https://")):
            logger.info(f"🖼️ URL 이미지 로드: {image_url[:50]}...")
            return {
                "type": "image_url",
                "image_url": {"url": image_url}
            }

        # Base64 인코딩된 경우
        elif image_url.startswith("data:image"):
            logger.info(f"🖼️ Base64 이미지 처리")
            return {
                "type": "image_url",
                "image_url": {"url": image_url}
            }

        # 로컬 파일 경로인 경우
        else:
            import base64
            logger.info(f"🖼️ 로컬 파일 이미지: {image_url}")

            with open(image_url, "rb") as image_file:
                image_bytes = image_file.read()
                b64_image = base64.standard_b64encode(image_bytes).decode("utf-8")

                # 파일 확장자로부터 MIME 타입 추정
                file_ext = Path(image_url).suffix.lower()
                mime_type_map = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".webp": "image/webp"
                }
                mime_type = mime_type_map.get(file_ext, "image/jpeg")

                return {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}
                }

    except Exception as e:
        logger.error(f"❌ 이미지 준비 오류: {e}")
        raise


def recognize_ingredients_from_image(image_url: str) -> Dict:
    """
    OpenAI Vision API를 사용하여 이미지에서 식재료 인식

    Args:
        image_url: 이미지 URL 또는 base64 인코딩

    Returns:
        인식된 식재료 딕셔너리
    """
    try:
        from openai import OpenAI
        import json

        logger.info(f"🔍 식재료 인식 시작 (Vision API)")

        # OpenAI 클라이언트
        client = OpenAI()

        # 이미지 준비
        image_data = _prepare_image_for_vision(image_url)

        # 이미지가 URL인지 Base64인지 확인
        if isinstance(image_data, dict) and "image_url" in image_data:
            image_content = image_data["image_url"]["url"]
        else:
            image_content = image_url

        recognition_prompt = """이미지에서 모든 식재료를 인식하여 JSON 형식으로 반환하세요.

[필수 정보]
- ingredients: 식재료명 배열 (한글)
- quantities: 각 식재료의 예상 분량 (그램 기준)
- categories: 각 식재료의 분류 (채소/고기/곡류 등)

[응답 형식]
```json
{
  "ingredients": ["재료1", "재료2"],
  "quantities": [100, 150],
  "categories": ["채소", "고기"],
  "total_calories_estimate": "칼로리 예상값"
}
```

정확한 JSON만 반환하세요."""

        # OpenAI Vision API로 직접 호출
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": recognition_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_content
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )

        logger.info("✅ 식재료 인식 완료")

        return {
            "status": "success",
            "ingredients": response.choices[0].message.content
        }

    except Exception as e:
        logger.error(f"❌ 식재료 인식 오류: {e}", exc_info=True)
        return {
            "status": "error",
            "ingredients": f"식재료 인식 중 오류: {str(e)}"
        }


def calculate_nutrition_from_ingredients(ingredients_list: List[str]) -> Dict:
    """
    식재료 영양 계산

    Args:
        ingredients_list: 식재료 목록

    Returns:
        영양 계산 결과 딕셔너리
    """
    try:
        logger.info(f"📊 영양 계산 시작: {len(ingredients_list)}개 재료")

        # MongoDB 검색 → CSV 검색 → 웹 검색 순서로 데이터 수집
        nutrition_data = {}

        for ingredient in ingredients_list:
            ingredient_nutrition = _get_ingredient_nutrition(ingredient)
            nutrition_data[ingredient] = ingredient_nutrition

        logger.info("✅ 영양 계산 완료")

        return {
            "status": "success",
            "nutrition": nutrition_data
        }

    except Exception as e:
        logger.error(f"❌ 영양 계산 오류: {e}", exc_info=True)
        return {
            "status": "error",
            "nutrition": f"영양 계산 중 오류: {str(e)}"
        }


def _get_ingredient_nutrition(ingredient: str) -> Dict:
    """
    식재료 영양정보 조회 (우선순위: MongoDB → CSV → PDF → Web)

    Args:
        ingredient: 식재료명

    Returns:
        영양정보 딕셔너리
    """
    try:
        # 1. MongoDB에서 검색
        nutrition_from_db = _search_nutrition_in_mongodb(ingredient)
        if nutrition_from_db:
            logger.info(f"✅ MongoDB에서 찾음: {ingredient}")
            return nutrition_from_db

        # 2. CSV에서 검색
        nutrition_from_csv = _search_nutrition_in_csv(ingredient)
        if nutrition_from_csv:
            logger.info(f"✅ CSV에서 찾음: {ingredient}")
            return nutrition_from_csv

        # 3. PDF 문서에서 검색
        nutrition_from_pdf = _search_nutrition_in_pdf(ingredient)
        if nutrition_from_pdf:
            logger.info(f"✅ PDF에서 찾음: {ingredient}")
            return nutrition_from_pdf

        # 4. 웹 검색 (Fallback)
        nutrition_from_web = _search_nutrition_from_web(ingredient)
        logger.info(f"✅ 웹에서 찾음: {ingredient}")
        return nutrition_from_web

    except Exception as e:
        logger.error(f"❌ 영양정보 조회 오류 ({ingredient}): {e}")
        return {"error": str(e)}


def _search_nutrition_in_mongodb(ingredient: str) -> Optional[Dict]:
    """
    MongoDB에서 식재료 영양정보 검색

    Args:
        ingredient: 식재료명

    Returns:
        영양정보 또는 None
    """
    try:
        from src.database.mongo_client import get_mongo_client
        logger.info(f"🔍 MongoDB 검색 시도: {ingredient}")

        client = get_mongo_client()
        if client is None:
            logger.warning("⚠️ MongoDB 연결 실패 - CSV로 전환")
            return None

        db = client["nutrition_db"]
        foods_collection = db["foods"]

        # 정확한 이름 먼저 검색
        result = foods_collection.find_one({"name": ingredient})

        # 없으면 부분 일치 검색
        if not result:
            result = foods_collection.find_one({"name": {"$regex": ingredient, "$options": "i"}})

        if result:
            logger.info(f"✅ MongoDB에서 '{ingredient}' 찾음!")
            return {
                "source": "mongodb",
                "name": result.get("name"),
                "category": result.get("category"),
                "potassium": result.get("potassium"),
                "sodium": result.get("sodium"),
                "phosphorus": result.get("phosphorus"),
                "calories": result.get("calories")
            }

        logger.info(f"⚠️ MongoDB에 '{ingredient}' 데이터 없음")
        return None

    except Exception as e:
        logger.warning(f"⚠️ MongoDB 검색 오류: {e}")
        return None


def _search_nutrition_in_csv(ingredient: str) -> Optional[Dict]:
    """
    CSV 파일에서 식재료 영양정보 검색

    Args:
        ingredient: 식재료명

    Returns:
        영양정보 또는 None
    """
    try:
        import pandas as pd
        logger.info(f"🔍 CSV 검색 시도: {ingredient}")

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(project_root, "data", "preprocess", "food_database_cleaned_df.csv")

        if not os.path.exists(csv_path):
            logger.warning(f"⚠️ CSV 파일 없음: {csv_path}")
            return None

        df = pd.read_csv(csv_path)
        logger.info(f"📊 CSV 데이터 로드: {len(df)}행")

        # 정확한 일치 먼저 검색
        result = df[df["식품명"] == ingredient]

        # 부분 일치 검색
        if result.empty:
            result = df[df["식품명"].str.contains(ingredient, case=False, na=False)]

        if not result.empty:
            row = result.iloc[0]
            logger.info(f"✅ CSV에서 '{ingredient}' 찾음!")
            return {
                "source": "csv",
                "name": row.get("식품명"),
                "category": row.get("카테고리"),
                "potassium": row.get("칼륨"),
                "sodium": row.get("나트륨"),
                "phosphorus": row.get("인"),
                "calories": row.get("칼로리")
            }

        logger.info(f"⚠️ CSV에 '{ingredient}' 데이터 없음")
        return None

    except Exception as e:
        logger.warning(f"⚠️ CSV 검색 오류: {e}")
        return None


def _search_nutrition_in_pdf(ingredient: str) -> Optional[Dict]:
    """
    PDF 문서에서 식재료 영양정보 검색

    Args:
        ingredient: 식재료명

    Returns:
        영양정보 또는 None
    """
    try:
        from pypdf import PdfReader
        logger.info(f"🔍 PDF 검색: {ingredient}")

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pdf_dir = os.path.join(project_root, "data", "pdf")

        if not os.path.exists(pdf_dir):
            logger.warning(f"⚠️ PDF 디렉토리 없음: {pdf_dir}")
            return None

        for filename in os.listdir(pdf_dir):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(pdf_dir, filename)
                try:
                    with open(pdf_path, "rb") as f:
                        pdf_reader = PdfReader(f)
                        for page in pdf_reader.pages:
                            text = page.extract_text()
                            if ingredient.lower() in text.lower():
                                logger.info(f"✅ PDF에서 '{ingredient}' 찾음")
                                return {
                                    "source": "pdf",
                                    "name": ingredient,
                                    "found_in": filename,
                                    "excerpt": text[:200]
                                }
                except Exception as e:
                    logger.warning(f"⚠️ PDF 읽기 오류 ({filename}): {e}")
                    continue
        return None

    except Exception as e:
        logger.warning(f"⚠️ PDF 검색 오류: {e}")
        return None


def _search_nutrition_from_web(ingredient: str) -> Dict:
    """
    웹 검색으로 식재료 영양정보 검색 (Fallback)

    Args:
        ingredient: 식재료명

    Returns:
        영양정보 딕셔너리
    """
    try:
        from src.utils.web_search import search_nutrition_info
        logger.info(f"🔍 웹 검색: {ingredient}")

        result = search_nutrition_info(ingredient)
        if result:
            return {
                "source": "web",
                "name": ingredient,
                "nutrition_info": result
            }
        return {
            "source": "web",
            "name": ingredient,
            "nutrition_info": "정보 없음"
        }

    except Exception as e:
        logger.error(f"❌ 웹 검색 오류: {e}")
        return {
            "source": "web",
            "name": ingredient,
            "error": str(e)
        }
