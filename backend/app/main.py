"""
콩닥식탁 FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.routers import chat, quiz, resources, nutrition

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="신장 투석 환자를 위한 AI 기반 맞춤형 식단 관리 챗봇",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 라우터 등록
app.include_router(
    chat.router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["채팅"]
)
app.include_router(
    quiz.router,
    prefix=f"{settings.API_V1_STR}/quiz",
    tags=["퀴즈"]
)
app.include_router(
    resources.router,
    prefix=f"{settings.API_V1_STR}/resources",
    tags=["자료 추천"]
)
app.include_router(
    nutrition.router,
    prefix=f"{settings.API_V1_STR}/nutrition",
    tags=["영양 분석"]
)


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info(f"{settings.PROJECT_NAME} v{settings.VERSION} 시작")
    logger.info(f"OpenAI 모델: {settings.OPENAI_MODEL}")
    logger.info(f"데이터베이스: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'Not configured'}")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info(f"{settings.PROJECT_NAME} 종료")


@app.get("/", tags=["루트"])
async def root():
    """루트 엔드포인트 - 서비스 상태 확인"""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "docs_url": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health", tags=["루트"])
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리"""
    logger.error(f"예외 발생: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "내부 서버 오류가 발생했습니다.",
            "error": str(exc) if settings.LOG_LEVEL == "DEBUG" else None
        }
    )
