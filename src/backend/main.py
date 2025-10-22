"""FastAPI 메인 앱"""
import logging
import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.backend.models import HealthCheckResponse
from src.backend.routes import text, pdf, image

# 환경 변수 로드
load_dotenv()

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="NutriCoach API",
    description="신장질환 환자 영양 관리 챗봇 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (프로덕션에서는 제한 필요)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(text.router)
app.include_router(pdf.router)
app.include_router(image.router)


@app.on_event("startup")
async def startup_event():
    """앱 시작 이벤트"""
    logger.info("=" * 70)
    logger.info("🚀 NutriCoach API 시작")
    logger.info("=" * 70)
    logger.info("📋 등록된 라우터:")
    logger.info("  - /chat/text    : 텍스트 채팅")
    logger.info("  - /chat/pdf     : PDF 분석")
    logger.info("  - /chat/image   : 이미지 분석")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 이벤트"""
    logger.info("🛑 NutriCoach API 종료")


@app.get("/", response_model=HealthCheckResponse)
async def root():
    """루트 엔드포인트"""
    return HealthCheckResponse(
        status="ok",
        message="NutriCoach API 실행 중"
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """헬스 체크"""
    return HealthCheckResponse(
        status="ok",
        message="모든 서비스 정상"
    )


@app.get("/api/version")
async def get_version():
    """API 버전 조회"""
    return {
        "version": "1.0.0",
        "name": "NutriCoach API",
        "features": [
            "Text Chat (RAG 기반)",
            "PDF Analysis",
            "Food Image Recognition"
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
