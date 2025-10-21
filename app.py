import os
import sys
import logging
import base64
import streamlit as st
from dotenv import load_dotenv

# ==============================================
# 로거 설정
# ==============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================================
# 경로 및 환경 변수 로드
# ==============================================
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)
load_dotenv()
logger.info("✅ 환경 설정 완료")

# ==============================================
# 페르소나 설정
# ==============================================
PERSONA_NAME = "Nutri Coach"
PERSONA_ROLE = "투석 환자를 위한 질환 식단 전문 영양사"

WELCOME_MESSAGE = f"""
안녕하세요! 😊 저는 투석 치료를 받고 계신 분들의 **질환 맞춤 식단 관리** & **학습 어시스턴트 {PERSONA_NAME}**입니다.

식단 관리가 어렵고 복잡하게 느껴지시죠? 함께 차근차근 해결해 나가요! 💪

---

### 🍽️ 제가 도와드릴 수 있는 3가지
1️⃣ **재료 대체 추천** 🥗  
2️⃣ **식단 정보 요약** 📚  
3️⃣ **영양 학습 문제 생성** ✏️
"""

FALLBACK_ERROR = "앗! 일시적인 오류가 발생했어요. 😓 잠시 후 다시 시도해주세요."

# ==============================================
# Streamlit 페이지 설정
# ==============================================
st.set_page_config(
    page_title=f"{PERSONA_NAME} - 투석 환자 영양 관리",
    page_icon="🏥",
    layout="wide"
)

# ==============================================
# 세션 상태 초기화
# ==============================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.first_visit = True
if "uploaded_file_info" not in st.session_state:
    st.session_state.uploaded_file_info = None
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

# ==============================================
# RAG 및 워크플로우 초기화
# ==============================================
from src.rag.rag_setup import RAGSetup
from src.workflow.workflow import create_workflow_app

@st.cache_resource(show_spinner=False)
def init_rag_system():
    logger.info("🔧 RAG 시스템 초기화 중...")
    rag_setup = RAGSetup(
        pdf_directory=os.path.join(project_root, "data/pdf"),
        vectorstore_path=os.path.join(project_root, "data/vectorstore"),
        chunk_size=300,
        chunk_overlap=30
    )
    vectorstore = rag_setup.setup_rag(force_rebuild=False)
    llm_config = {"model": "gpt-4o-mini", "temperature": 0.7}
    return create_workflow_app(vectorstore, llm_config)

workflow_app = st.session_state.get("workflow_app")
if workflow_app is None:
    with st.spinner("🏥 Nutri Coach가 준비 중이에요..."):
        workflow_app = init_rag_system()
        st.session_state.workflow_app = workflow_app
    st.success("✅ Nutri Coach 준비 완료!", icon="✅")

# ==============================================
# 사이드바 UI – 파일 업로드 및 빠른 명령
# ==============================================
with st.sidebar:
    st.title(f"💚 {PERSONA_NAME}")
    st.caption(f"{PERSONA_ROLE}")
    st.divider()
    st.subheader("📋 빠른 명령")

    quick_prompts = {
        "🥗 재료 대체 추천": "김치찌개에서 저칼륨 재료 추천해줘",
        "📚 식단 정보 요약": "저염식 조리법 알려줘",
        "✏️ 영양 학습 문제": "영양 관리 퀴즈 만들어줘"
    }

    for label, prompt in quick_prompts.items():
        if st.button(label, use_container_width=True):
            st.session_state.pending_input = prompt

    st.divider()
    st.subheader("📎 파일 업로드")

    uploaded_file = st.file_uploader(
        "PDF 또는 이미지 파일을 업로드하세요",
        type=["pdf", "jpg", "jpeg", "png"],
        key="file_uploader_key"
    )
    if uploaded_file is not None:
        file_content = uploaded_file.read()
        file_content_b64 = base64.b64encode(file_content).decode()
        file_type = "pdf" if uploaded_file.type == "application/pdf" else "image"
        st.session_state.uploaded_file_info = {
            "file_type": file_type,
            "file_name": uploaded_file.name,
            "file_content": file_content_b64
        }
        st.success(f"📎 파일 업로드 완료: {uploaded_file.name}")

    st.divider()
    st.caption("⚠️ 본 서비스는 정보 제공 목적이며, 의학적 진단/치료를 대체하지 않습니다.")        
# ==============================================
# 메시지 렌더링 함수
# ==============================================
def render_message(message: dict):
    role = message.get("role", "user")
    avatar = "👩‍⚕️" if role == "assistant" else "🙋"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message.get("content", ""))
        if message.get("file_type") == "image" and "file_content" in message:
            st.image(
                base64.b64decode(message["file_content"]),
                caption=message.get("file_name", "첨부 이미지")
            )
        elif message.get("file_type") == "pdf":
            st.caption(f"📄 첨부파일: {message.get('file_name', '')}")

def render_chat_history():
    for msg in st.session_state.messages:
        render_message(msg)

# ==============================================
# 메인 화면
# ==============================================
st.title("🏥 NutriCoach - 신장 투석 환자 영양 관리")

if st.session_state.first_visit:
    st.session_state.messages.append({"role": "assistant", "content": WELCOME_MESSAGE})
    st.session_state.first_visit = False
render_chat_history()

# ==============================================
# 사용자 입력 처리
# ==============================================
user_input = st.chat_input("무엇을 도와드릴까요? 😊")
if user_input:
    st.session_state.pending_input = user_input

if st.session_state.pending_input is not None:
    # 사용자 메시지 저장
    user_msg = {"role": "user", "content": st.session_state.pending_input}
    # 파일이 업로드되어 있다면 메시지에 포함
    if st.session_state.uploaded_file_info:
        user_msg.update(st.session_state.uploaded_file_info)
        st.session_state.uploaded_file_info = None
    st.session_state.messages.append(user_msg)
    render_chat_history()

    # 응답 생성
    with st.chat_message("assistant", avatar="👩‍⚕️"):
        with st.spinner(f"{PERSONA_NAME}가 답변을 준비하고 있어요..."):
            try:
                workflow_input = {"query": user_msg["content"]}
                if user_msg.get("file_type"):
                    workflow_input.update({
                        "file_type": user_msg["file_type"],
                        "file_name": user_msg["file_name"],
                        "file_content": user_msg["file_content"]
                    })
                result = workflow_app.invoke(workflow_input)
                response = result["final_result"]
            except Exception as e:
                logger.error(f"❌ 워크플로우 오류: {e}", exc_info=True)
                response = FALLBACK_ERROR

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            render_chat_history()

    # pending_input 초기화
    st.session_state.pending_input = None
