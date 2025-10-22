"""FastAPI 요청/응답 모델"""
from pydantic import BaseModel
from typing import Optional


class FileInfo(BaseModel):
    """파일 정보"""
    file_type: str  # "pdf", "image", None
    file_name: str
    file_content: str  # base64 또는 텍스트


class TextChatRequest(BaseModel):
    """텍스트 채팅 요청 (파일 지원)"""
    query: str
    session_id: Optional[str] = None
    file_info: Optional[FileInfo] = None  # 파일 정보 (선택사항)


class PDFChatRequest(BaseModel):
    """PDF 채팅 요청"""
    query: str
    session_id: Optional[str] = None


class ImageAnalysisRequest(BaseModel):
    """이미지 분석 요청"""
    image_url: str
    query: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """채팅 응답"""
    status: str
    intent: Optional[str] = None
    response: str
    session_id: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """헬스 체크 응답"""
    status: str
    message: str
