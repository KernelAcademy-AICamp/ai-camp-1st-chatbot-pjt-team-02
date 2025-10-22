"""PDF 처리 라우터"""
import base64
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from src.backend.models import ChatResponse
from src.workflow.workflow import process_pdf_query, summarize_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat/pdf", tags=["pdf"])


@router.post("/", response_model=ChatResponse)
async def process_pdf_chat(
    file: UploadFile = File(...),
    query: str = Form(...)
):
    """
    PDF 파일 기반 채팅 (app_multimodal.py 호환)

    - **file**: PDF 파일
    - **query**: 사용자 질문
    """
    logger.info(f"📄 PDF 처리 요청: {file.filename}")

    try:
        # 파일 읽기
        pdf_bytes = await file.read()

        # 텍스트 추출
        from pypdf import PdfReader
        import io

        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PdfReader(pdf_file)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text()

        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_data_uri = f"data:application/pdf;base64,{pdf_b64}"

        # 워크플로우로 처리
        from src.backend.routes.text import get_workflow_app
        workflow_app = get_workflow_app()

        workflow_input = {
            "query": query,
            "file_type": "pdf",
            "file_name": file.filename,
            "pdf_text": pdf_text,
            "file_content": pdf_data_uri,
        }

        result = workflow_app.invoke(workflow_input)

        return ChatResponse(
            status="success",
            intent=result.get("intent"),
            response=result.get("final_result", "응답을 생성할 수 없습니다.")
        )

    except Exception as e:
        logger.error(f"❌ PDF 처리 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="PDF 처리 중 오류 발생")


@router.post("/query", response_model=ChatResponse)
async def query_pdf(
    file: UploadFile = File(...),
    query: str = Form(...)
):
    """
    PDF 파일 기반 쿼리 처리

    - **file**: PDF 파일
    - **query**: 사용자 질문
    """
    logger.info(f"📄 PDF 쿼리 요청: {file.filename}")

    try:
        # 파일 읽기
        pdf_bytes = await file.read()

        # workflow.py의 함수 호출
        result = process_pdf_query(pdf_bytes, query)

        if result["status"] == "success":
            return ChatResponse(
                status="success",
                response=result["response"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["response"])

    except Exception as e:
        logger.error(f"❌ PDF 쿼리 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="PDF 처리 중 오류 발생")


@router.post("/summarize", response_model=ChatResponse)
async def summarize_pdf_handler(file: UploadFile = File(...)):
    """
    PDF 파일 요약

    - **file**: PDF 파일
    """
    logger.info(f"📑 PDF 요약 요청: {file.filename}")

    try:
        # 파일 읽기
        pdf_bytes = await file.read()

        # workflow.py의 함수 호출
        result = summarize_pdf(pdf_bytes)

        if result["status"] == "success":
            return ChatResponse(
                status="success",
                response=result["summary"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["summary"])

    except Exception as e:
        logger.error(f"❌ PDF 요약 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="PDF 요약 중 오류 발생")


@router.get("/health", response_model=ChatResponse)
async def health_check():
    """PDF 서비스 헬스 체크"""
    return ChatResponse(
        status="ok",
        response="PDF 서비스 정상 작동 중"
    )
