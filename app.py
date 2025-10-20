"""
NutriCoach - 신장 투석 환자용 영양 코치 AI
"""
import os
import sys
import streamlit as st
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# 환경 변수 로드
load_dotenv()

# ================== 페르소나 & 메시지 설정 ==================
PERSONA_NAME = "Nutri Coach"
PERSONA_AGE = "30대"
PERSONA_ROLE = "투석 환자를 위한 질환 식단 전문 영양사"

# 고정 인사말
WELCOME_MESSAGE = f"""
안녕하세요! 😊 저는 투석 치료를 받고 계신 분들의 **질환 맞춤 식단 관리** & **학습 어시스턴트 {PERSONA_NAME}**입니다.

투석 치료를 받고 계신 분들의 **질환 맞춤 식단 관리**를 위해 여기 있어요.
식단 관리가 어렵고 복잡하게 느껴지시죠? 함께 차근차근 해결해 나가요! 💪

---

### 🍽️ 제가 도와드릴 수 있는 3가지

**1. 재료 대체 추천** 🥗
- 요리명 입력 → 고칼륨/고인 재료 분석 → 저칼륨/인 대체재 추천
- 예: "김치찌개 만들 때 뭘 대체할 수 있을까?"

**2. 식단 정보 요약** 📚
- 조리법, 주의사항, Q&A 자동 생성
- 예: "저염식 조리법 알려줘"

**3. 영양 학습 문제** ✏️
- 객관식 2문제 + 주관식 1문제 자동 생성
- 예: "혈액투석 영양 관리 퀴즈 만들어줘"

---

💬 **편하게 질문해 주세요!**
"""

# Fallback 메시지 (3가지)
FALLBACK_UNCLEAR = """
앗, 질문을 정확히 이해하지 못했어요. 😅

혹시 이런 질문이셨나요?
- 🥗 **재료 대체**: "김치찌개에서 저칼륨 재료 추천해줘"
- 📚 **정보 요약**: "저염식 주의사항 알려줘"
- ✏️ **문제 생성**: "영양 관리 퀴즈 만들어줘"

조금 더 구체적으로 말씀해 주시면 도움드릴게요! 🙏
"""

FALLBACK_OUT_OF_SCOPE = """
죄송해요, 저는 **투석 환자 질환 식단 전문**이라 그 부분은 잘 모르겠어요. 😔

제가 도와드릴 수 있는 것은:
✅ 투석 환자 식단 관리 (재료 대체, 조리법, 문제 생성)

**의학적 질문**은 꼭 담당 의료진과 상담해 주세요! 💕
"""

FALLBACK_ERROR = """
앗! 일시적인 오류가 발생했어요. 😓

잠시 후 다시 시도해 주시거나, 문제가 계속되면 관리자에게 문의해 주세요.

**긴급한 경우 담당 의료진에게 연락하세요!** 🏥
"""

# ================== RAG 및 체인 초기화 ==================
from src.rag.rag_setup import RAGSetup
from src.rag.retriever import create_retriever
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

# 페이지 설정
st.set_page_config(
    page_title=f"{PERSONA_NAME} - 투석 환자 영양 관리",
    page_icon="🏥",
    layout="wide"
)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.first_visit = True

# RAG 시스템 초기화 (최초 1회만)
@st.cache_resource
def init_rag_system():
    """RAG 시스템 및 LangGraph 워크플로우 초기화"""
    # RAG 설정
    rag_setup = RAGSetup(
        pdf_directory=os.path.join(project_root, "data/pdf"),
        vectorstore_path=os.path.join(project_root, "data/vectorstore"),
        chunk_size=300,
        chunk_overlap=30
    )
    vectorstore = rag_setup.setup_rag(force_rebuild=False)
    retriever = create_retriever(vectorstore, retriever_type="basic", k=4)
    
    # LLM 초기화
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    # ========== tutorial_rag.ipynb의 프롬프트 그대로 사용 ==========
    
    # 1. 재료 추출 프롬프트
    ingredient_extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 요리 전문가입니다. 주어진 요리명에 대해 일반적으로 사용되는 재료들을 나열해주세요.

참고 자료:
{context}

재료명, 단백질, 나트륨, 칼륨, 인과 칼로리들을 나열하되, 각 재료는 줄바꿈으로 구분해주세요. 이때 용량은 mg으로 통일하여 고지하세요.

만성신부전 환자의 영양 관리 조건:
1. 단백질: 투석 전 0.6~0.8g/kg, 투석 중 1.2~1.3g/kg
2. 나트륨: 투석 전 5g 미만, 투석 중·이식 후 6g 미만
3. 칼륨: 2000mg 미만 권장
4. 인: 투석 전 800mg, 투석 중 1000mg, 이식 후 1200mg 미만
5. 에너지: 30~35kcal/kg
6. 안전 구간: 0~80%(녹색), 80~100%(노란색), 100% 초과(빨간색)로 표시
"""),
        ("user", "요리명: {dish_name}")
    ])
    
    # 2. 대체재 추천 프롬프트
    recommendation_prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 신장 질환 환자를 위한 영양 전문가입니다.
주어진 요리 재료들을 분석하고, 식약처 자료를 참고하여 저칼륨/저인 대체재를 추천해주세요.

참고 자료:
{context}

다음 형식으로 답변해주세요:
1. 고칼륨/고인 재료 분석
2. 추천 대체재
3. 조리 팁

만성신부전 환자의 영양 관리 조건을 고려하세요."""),
        ("user", """요리: {dish_name}
재료:
{ingredients}

위 재료들 중 신장 질환 환자에게 부담이 될 수 있는 재료와 대체재를 추천해주세요.""")
    ])
    
    # 3. 요약 프롬프트
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 신장 질환 환자를 위한 영양 교육 전문가입니다.
식약처 자료를 바탕으로 조리법과 주의사항을 요약하고, 이해를 돕는 Q&A를 생성해주세요.

참고 자료:
{context}

다음 형식으로 답변해주세요:
## 조리법 요약
## 주의사항
## Q&A"""),
        ("user", "주제: {topic}\n\n위 주제에 대해 조리법, 주의사항, Q&A를 생성해주세요.")
    ])
    
    # 4. 문제 생성 프롬프트
    quiz_prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 영양학 교육 문제 출제 전문가입니다.
식약처 자료를 바탕으로 학습 효과를 높이는 문제를 출제해주세요.

참고 자료:
{context}

다음 형식으로 정확히 3개의 문제를 출제해주세요:

**문제 1 (객관식)**
[문제 내용]
1) 선택지 1
2) 선택지 2
3) 선택지 3
4) 선택지 4

정답: [번호]
해설: [간단한 해설]

**문제 2 (객관식)**
**문제 3 (주관식)**"""),
        ("user", "주제: {topic}\n\n위 주제에 대해 객관식 2문제, 주관식 1문제를 출제해주세요.")
    ])
    
    # ========== 체인 구성 (tutorial_rag.ipynb 방식) ==========
    
    def get_context_for_ingredients(dish_name_input: dict):
        dish_name = dish_name_input["dish_name"]
        query = f"{dish_name} 재료 레시피"
        docs = retriever.retrieve(query)
        context = "\n\n".join([doc.page_content for doc in docs])
        return {"dish_name": dish_name, "context": context}
    
    ingredient_chain = (
        RunnablePassthrough.assign(context=get_context_for_ingredients)
        | ingredient_extraction_prompt
        | llm
        | StrOutputParser()
    )
    
    def get_context_for_recommendation(inputs):
        dish_name = inputs['dish_name']
        query = f"저칼륨 저인 식품 대체재 {dish_name}"
        docs = retriever.retrieve(query)
        context = "\n\n".join([doc.page_content for doc in docs])
        return {**inputs, "context": context}
    
    recommendation_chain = recommendation_prompt | llm | StrOutputParser()
    
    def get_context_for_summary(inputs):
        topic = inputs["topic"]
        docs = retriever.retrieve(topic)
        context = "\n\n".join([doc.page_content for doc in docs])
        return {**inputs, "context": context}
    
    summary_chain = (
        get_context_for_summary
        | summary_prompt
        | llm
        | StrOutputParser()
    )
    
    def get_context_for_quiz(inputs):
        topic = inputs["topic"]
        docs = retriever.retriever.invoke(topic)
        context = "\n\n".join([doc.page_content for doc in docs])
        return {**inputs, "context": context}
    
    quiz_chain = (
        get_context_for_quiz
        | quiz_prompt
        | llm
        | StrOutputParser()
    )
    
    # ========== LangGraph 워크플로우 ==========
    
    class WorkflowState(TypedDict):
        query: str
        intent: str
        result: str
    
    # 의도 분류
    intent_prompt = ChatPromptTemplate.from_messages([
        ("system", """사용자 의도를 'recommendation', 'summary', 'quiz' 중 하나로 분류하세요.
- recommendation: 재료 대체 요청
- summary: 정보 요약 요청
- quiz: 문제 출제 요청
하나의 단어만 답변하세요."""),
        ("user", "{query}")
    ])
    
    intent_classifier = intent_prompt | llm | StrOutputParser()
    
    def classify_intent(state: WorkflowState):
        intent = intent_classifier.invoke({"query": state["query"]}).strip().lower()
        return {**state, "intent": intent}
    
    def extract_dish_name(query: str) -> str:
        extract_prompt = ChatPromptTemplate.from_messages([
            ("system", "사용자 질문에서 요리명만 추출하세요. 한 단어만 반환."),
            ("user", "{query}")
        ])
        extractor = extract_prompt | llm | StrOutputParser()
        return extractor.invoke({"query": query}).strip()
    
    def run_recommendation(state: WorkflowState):
        dish_name = extract_dish_name(state["query"])
        ingredients = ingredient_chain.invoke({'dish_name': dish_name})
        inputs = get_context_for_recommendation({"dish_name": dish_name, "ingredients": ingredients})
        result = recommendation_chain.invoke(inputs)
        return {**state, "result": result}
    
    def run_summary(state: WorkflowState):
        result = summary_chain.invoke({"topic": state["query"]})
        return {**state, "result": result}
    
    def run_quiz(state: WorkflowState):
        result = quiz_chain.invoke({"topic": state["query"]})
        return {**state, "result": result}
    
    def route_intent(state: WorkflowState) -> Literal["recommendation", "summary", "quiz"]:
        intent = state["intent"]
        if "recommendation" in intent:
            return "recommendation"
        elif "quiz" in intent:
            return "quiz"
        else:
            return "summary"
    
    # 워크플로우 구성
    workflow = StateGraph(WorkflowState)
    workflow.add_node("classifier", classify_intent)
    workflow.add_node("recommendation", run_recommendation)
    workflow.add_node("summary", run_summary)
    workflow.add_node("quiz", run_quiz)
    
    workflow.set_entry_point("classifier")
    workflow.add_conditional_edges("classifier", route_intent, {
        "recommendation": "recommendation",
        "summary": "summary",
        "quiz": "quiz"
    })
    
    workflow.add_edge("recommendation", END)
    workflow.add_edge("summary", END)
    workflow.add_edge("quiz", END)
    
    return workflow.compile()

# RAG 시스템 로드 (캐싱)
with st.spinner("🏥 Nutri Coach가 준비 중이에요..."):
    workflow_app = init_rag_system()

# ================== UI 구성 ==================

# 사이드바
with st.sidebar:
    st.title(f"💚 {PERSONA_NAME}")
    st.caption(f"{PERSONA_ROLE}")
    st.divider()
    
    st.subheader("📋 주요 기능")
    
    if st.button("🥗 재료 대체 추천", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "김치찌개에서 저칼륨 재료 추천해줘"})
        st.rerun()
    
    if st.button("📚 식단 정보 요약", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "저염식 조리법 알려줘"})
        st.rerun()
    
    if st.button("✏️ 영양 학습 문제", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "영양 관리 퀴즈 만들어줘"})
        st.rerun()
    
    st.divider()
    st.caption("⚠️ 본 서비스는 정보 제공 목적이며, 의학적 진단/치료를 대체하지 않습니다.")

# 메인 화면
st.title("🏥 NutriCoach - 신장 투석 환자 영양 관리")

# 첫 방문 시 환영 메시지
if st.session_state.first_visit:
    with st.chat_message("assistant", avatar="👩‍⚕️"):
        st.markdown(WELCOME_MESSAGE)
    st.session_state.first_visit = False

# 대화 기록 표시
for message in st.session_state.messages:
    avatar = "👩‍⚕️" if message["role"] == "assistant" else "🙋"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 사용자 입력
if user_input := st.chat_input("무엇을 도와드릴까요? 😊"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🙋"):
        st.markdown(user_input)
    
    with st.chat_message("assistant", avatar="👩‍⚕️"):
        with st.spinner(f"{PERSONA_NAME}가 답변을 준비하고 있어요..."):
            try:
                result = workflow_app.invoke({"query": user_input})
                response = result["result"]
            except Exception as e:
                response = FALLBACK_ERROR
                print(f"Error: {e}")
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

st.divider()
st.caption("💡 **Tip:** 구체적으로 질문하실수록 더 정확한 답변을 드릴 수 있어요!")