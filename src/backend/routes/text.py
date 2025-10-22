"""텍스트 채팅 라우터"""
import logging
from fastapi import APIRouter, HTTPException
from src.backend.models import TextChatRequest, ChatResponse
from src.workflow.workflow import create_workflow_app
from src.rag.rag_setup import RAGSetup
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat/text", tags=["text"])

# 싱글톤 패턴으로 워크플로우 앱 유지
_workflow_app = None


def get_workflow_app():
    """워크플로우 앱 가져오기 (싱글톤)"""
    global _workflow_app
    if _workflow_app is None:
        logger.info("🔄 워크플로우 앱 초기화 중...")
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # 벡터스토어 경로 확인
        vectorstore_path = os.path.join(project_root, "data", "vectorstore", "faiss_index")

        # 기존 벡터스토어가 있는지 확인
        if os.path.exists(vectorstore_path) and os.path.exists(os.path.join(vectorstore_path, "index.faiss")):
            logger.info(f"📚 기존 벡터스토어 발견: {vectorstore_path}")
            try:
                from langchain_community.vectorstores import FAISS
                from langchain_openai import OpenAIEmbeddings

                embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
                logger.info("✅ 기존 벡터스토어 로드 완료")
            except Exception as e:
                logger.warning(f"⚠️ 벡터스토어 로드 실패: {e}")
                vectorstore = None
        else:
            # PDF 디렉토리 확인 후 새로 생성 시도
            pdf_dir = os.path.join(project_root, "data", "pdf")
            pdf_files_exist = os.path.exists(pdf_dir) and any(
                f.endswith('.pdf') for f in os.listdir(pdf_dir)
            ) if os.path.exists(pdf_dir) else False

            if pdf_files_exist:
                logger.info(f"📚 PDF 파일로 새 벡터스토어 생성 시도: {pdf_dir}")
                rag_setup = RAGSetup(
                    pdf_directory=pdf_dir,
                    vectorstore_path=os.path.join(project_root, "data", "vectorstore"),
                    chunk_size=300,
                    chunk_overlap=30
                )
                try:
                    vectorstore = rag_setup.setup_rag(force_rebuild=False)
                    logger.info("✅ 새 벡터스토어 생성 완료")
                except Exception as e:
                    logger.warning(f"⚠️ 벡터스토어 생성 실패: {e}")
                    vectorstore = None
            else:
                logger.warning(f"⚠️ 벡터스토어와 PDF 모두 없음, RAG 없이 진행")
                vectorstore = None
        llm_config = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": None,
        }
        _workflow_app = create_workflow_app(vectorstore, llm_config)
        logger.info("✅ 워크플로우 앱 초기화 완료")
    return _workflow_app


@router.post("/", response_model=ChatResponse)
async def chat_with_text(request: TextChatRequest):
    """
    텍스트 기반 채팅 (파일 지원)

    - **query**: 사용자 질문
    - **session_id**: (선택) 세션 ID
    - **file_info**: (선택) 파일 정보 (file_type, file_name, file_content)
    """
    logger.info(f"📨 텍스트 채팅 요청: {request.query[:50]}...")

    try:
        workflow_app = get_workflow_app()

        # 워크플로우 input 구성
        workflow_input = {"query": request.query}

        # 파일 정보가 있으면 추가
        if request.file_info:
            logger.info(f"📎 파일 첨부: {request.file_info.file_type} - {request.file_info.file_name}")
            workflow_input.update({
                "file_type": request.file_info.file_type,
                "file_name": request.file_info.file_name,
                "file_content": request.file_info.file_content,
            })

        # 워크플로우 실행
        result = workflow_app.invoke(workflow_input)

        logger.info(f"✅ 텍스트 채팅 완료 - 의도: {result.get('intent', 'unknown')}")

        return ChatResponse(
            status="success",
            intent=result.get("intent"),
            response=result.get("final_result", "응답을 생성할 수 없습니다."),
            session_id=request.session_id
        )

    except Exception as e:
        logger.error(f"❌ 텍스트 채팅 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="채팅 처리 중 오류 발생")


@router.get("/health", response_model=ChatResponse)
async def health_check():
    """텍스트 서비스 헬스 체크"""
    return ChatResponse(
        status="ok",
        response="텍스트 서비스 정상 작동 중"
    )
