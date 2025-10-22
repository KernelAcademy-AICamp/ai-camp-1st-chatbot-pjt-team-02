import os
import sys
import logging
import base64
import streamlit as st
from dotenv import load_dotenv
import requests
import io
from pypdf import PdfReader
from PIL import Image

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
# FastAPI 백엔드 설정
# ==============================================
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

# ==============================================
# 페르소나 설정
# ==============================================
PERSONA_NAME = "Nutri Coach"
PERSONA_ROLE = "신장질환 환자를 위한 맞춤형 영양 관리 전문가"

WELCOME_MESSAGE = f"""
안녕하세요! 😊 
                                                                                                                                                                                                                                                                                            
저는 신장질환 환자분들의 **맞춤형 영양 관리 전문가 {PERSONA_NAME}**입니다.

**🎯 제가 도와드릴 수 있는 기능**

1️⃣ **텍스트 기반 상담**
- 영양 정보 제공, 식단 관리 조언

2️⃣ **PDF 문서 분석**
- PDF 파일을 업로드하고 질문하세요
- 의료 보고서, 영양 정보 문서 분석 가능

3️⃣ **이미지 분석**
- 음식 사진을 업로드하고 질문하세요
- 칼륨, 나트륨, 인 함량 분석
- 신장질환 환자 적합도 평가

💡 **사용 방법**: 텍스트를 입력하거나, 파일을 업로드한 후 질문해주세요!
"""

FALLBACK_ERROR = "앗! 일시적인 오류가 발생했어요. 😓 잠시 후 다시 시도해주세요."

# ==============================================
# Streamlit 페이지 설정
# ==============================================
st.set_page_config(
    page_title=f"{PERSONA_NAME} - 신장질환 환자 영양 관리",
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
# FastAPI 백엔드 통신 함수
# ==============================================
def call_text_api(query: str, file_info=None):
    """텍스트 API 호출 (파일 정보 포함 가능)"""
    try:
        endpoint = f"{FASTAPI_URL}/chat/text/"
        data = {"query": query}
        if file_info:
            data["file_info"] = file_info

        response = requests.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"❌ Text API 오류: {e}")
        return {"status": "error", "response": str(e)}

def call_pdf_api(pdf_bytes: bytes, query: str):
    """PDF API 호출"""
    try:
        endpoint = f"{FASTAPI_URL}/chat/pdf/"
        files = {"file": ("document.pdf", pdf_bytes, "application/pdf")}
        data = {"query": query}

        response = requests.post(endpoint, files=files, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"❌ PDF API 오류: {e}")
        return {"status": "error", "response": str(e)}

def call_image_api(image_base64: str, query: str, file_name: str):
    """이미지 API 호출"""
    try:
        endpoint = f"{FASTAPI_URL}/chat/image/"
        data = {
            "image_base64": image_base64,
            "query": query,
            "file_name": file_name,
        }

        response = requests.post(endpoint, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"❌ Image API 오류: {e}")
        return {"status": "error", "response": str(e)}

# ==============================================
# 사이드바 UI
# ==============================================
with st.sidebar:
    st.title(f"💚 {PERSONA_NAME}")
    st.caption(f"{PERSONA_ROLE}")

    # FastAPI 상태 체크
    st.divider()

    st.subheader("📋 빠른 명령")

    quick_prompts = {
        "🥗 재료 대체 추천": "김치찌개에서 저칼륨 재료로 뭐 쓸 수 있어?",
        "📚 식단 정보 요약": "혈액투석 환자 식사 관리 주의사항 알려줘",
        "✏️ 영양 학습 문제": "저염식에 대한 퀴즈 3개 만들어줘"
    }

    for label, prompt in quick_prompts.items():
        if st.button(label, use_container_width=True):
            st.session_state.pending_input = prompt

    st.divider()
    st.subheader("📎 파일 업로드")

    uploaded_file = st.file_uploader(
        "PDF 또는 이미지 파일을 업로드하세요",
        type=["pdf", "jpg", "jpeg", "png"],
        help="PDF: 의료 보고서, 영양 정보\n이미지: 음식 사진"
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()

        if uploaded_file.type == "application/pdf":
            st.success(f"📄 PDF 업로드 완료: {uploaded_file.name}")
            st.caption("이제 PDF 내용에 대해 질문하세요!")
            st.session_state.uploaded_file_info = {
                "type": "pdf",
                "name": uploaded_file.name,
                "bytes": file_bytes,
            }
        else:
            # 이미지 파일
            st.success(f"🖼️ 이미지 업로드 완료: {uploaded_file.name}")
            st.image(file_bytes, caption=uploaded_file.name, use_container_width=True)
            st.caption("이제 이미지에 대해 질문하세요!")

            # Base64 인코딩
            image_base64 = f"data:image/{uploaded_file.name.split('.')[-1]};base64,{base64.b64encode(file_bytes).decode()}"
            st.session_state.uploaded_file_info = {
                "type": "image",
                "name": uploaded_file.name,
                "base64": image_base64,
                "bytes": file_bytes,
            }

    # if st.session_state.uploaded_file_info:
    #     if st.button("🗑️ 파일 제거", type="secondary", use_container_width=True):
    #         st.session_state.uploaded_file_info = None
    # #         st.rerun()

    st.divider()

    st.subheader("🔌 서버 상태")
    try:
        health_response = requests.get(f"{FASTAPI_URL}/health")
        if health_response.status_code == 200:
            st.success("✅ FastAPI 서버 연결됨")
        else:
            st.error("❌ FastAPI 서버 응답 없음")
    except:
        st.warning("⚠️ FastAPI 서버에 연결할 수 없습니다")

    st.divider()
    st.caption("⚠️ 본 서비스는 정보 제공 목적이며,\n의학적 진단/치료를 대체하지 않습니다.")

# ==============================================
# 메시지 렌더링 함수
# ==============================================
def render_message(message: dict):
    role = message.get("role", "user")
    avatar = "👩‍⚕️" if role == "assistant" else "🙋"

    with st.chat_message(role, avatar=avatar):
        # 파일 정보 표시
        if message.get("file_name"):
            if message.get("file_type") == "pdf":
                st.caption(f"📄 첨부: {message['file_name']}")
            elif message.get("file_type") == "image":
                image_bytes = message.get("file_bytes")
                if image_bytes:
                    st.image(image_bytes, caption=message["file_name"],width='stretch')
                else:
                    st.caption(f"🖼️ 첨부: {message['file_name']}")

        intent = message.get("intent")
        if intent and intent != "unknown":
            intent_emoji = {
                "recommendation": "🥗",
                "summary": "📚",
                "quiz": "✏️"
            }.get(intent, "💬")
            st.caption(f"{intent_emoji} 처리 의도: {intent}")

        # 메시지 내용 표시
        st.markdown(message.get("content", ""))

def render_chat_history():
    for msg in st.session_state.messages:
        render_message(msg)

# ==============================================
# 메인 화면
# ==============================================
st.title("🏥 NutriCoach - 신장질환 환자 영양 관리")
st.caption("멀티모달 지원: 텍스트, PDF, 이미지")

# 첫 방문 시 환영 메시지
if st.session_state.first_visit:
    st.session_state.messages.append({
        "role": "assistant",
        "content": WELCOME_MESSAGE
    })
    st.session_state.first_visit = False

chat_placeholder = st.empty()
with chat_placeholder.container():
    render_chat_history()

# ==============================================
# 사용자 입력 처리
# ==============================================
user_input = st.chat_input("무엇을 도와드릴까요? 😊")

# 빠른 명령 또는 직접 입력 처리
if user_input:
    st.session_state.pending_input = user_input

if st.session_state.pending_input is not None:
    query = st.session_state.pending_input
    # 사용자 메시지 구성
    user_msg = {
        "role": "user",
        "content": query
    }

    # 파일 정보 추가
    file_info = st.session_state.uploaded_file_info
    if file_info:
        user_msg["file_type"] = file_info["type"]
        user_msg["file_name"] = file_info["name"]
        if file_info["type"] == "image":
            user_msg["file_bytes"] = file_info.get("bytes")
            user_msg["file_base64"] = file_info.get("base64")
            st.session_state.uploaded_file_info = None

        elif file_info["type"] == "pdf":
            user_msg["file_bytes"] = file_info.get("bytes")
    
            st.session_state.uploaded_file_info = None
    # 사용자 메시지 저장 및 즉시 갱신
    st.session_state.messages.append(user_msg)
    chat_placeholder.empty()
    with chat_placeholder.container():
        render_chat_history()

    response = FALLBACK_ERROR
    intent = "unknown"
    result = {"status": "error", "response": FALLBACK_ERROR}

    try:
        with st.spinner(f"{PERSONA_NAME}가 답변을 준비하고 있어요..."):
            # 파일 타입에 따라 적절한 API 호출
            if file_info:
                if file_info["type"] == "pdf":
                    # PDF + 텍스트 처리
                    result = call_pdf_api(file_info["bytes"], query)
                elif file_info["type"] == "image":
                    # 이미지 + 텍스트 처리
                    result = call_image_api(file_info["base64"], query, file_info["name"])
                else:
                    # 텍스트만 처리
                    result = call_text_api(query)
            else:
                # 텍스트만 처리
                result = call_text_api(query)

        # 응답 처리
        if result["status"] == "success":
            response = result["response"]
            intent = result.get("intent", "unknown")
        else:
            response = f"❌ 오류 발생: {result.get('response', FALLBACK_ERROR)}"

    except Exception as e:
        logger.error(f"❌ 처리 오류: {e}", exc_info=True)
        response = FALLBACK_ERROR

    # 응답 저장 및 갱신
    assistant_msg = {
        "role": "assistant",
        "content": response
    }
    if intent and intent != "unknown":
        assistant_msg["intent"] = intent
    st.session_state.messages.append(assistant_msg)
    chat_placeholder.empty()
    with chat_placeholder.container():
        render_chat_history()

    # 입력 초기화
    st.session_state.pending_input = None
    
    # 파일 처리 완료 후 선택적으로 파일 정보 유지
    # (사용자가 같은 파일에 대해 추가 질문을 할 수 있도록)
    # st.session_state.uploaded_file_info = None

# ==============================================
# 푸터
# ==============================================
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🏥 NutriCoach v2.0")
with col2:
    st.caption("📚 RAG 기반 AI 어시스턴트")
with col3:
    st.caption("🔬 신장질환 전문")
