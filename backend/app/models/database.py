"""
SQLAlchemy 데이터베이스 모델
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, TIMESTAMP, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime

from app.config import settings

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스
Base = declarative_base()


# 데이터베이스 세션 의존성
def get_db():
    """데이터베이스 세션 생성 및 종료"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== ORM 모델 ==========

class Food(Base):
    """식품 영양 정보 모델"""
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    sodium = Column(Float, default=0.0)
    potassium = Column(Float, default=0.0)
    phosphorus = Column(Float, default=0.0)
    protein = Column(Float, default=0.0)
    calories = Column(Float, default=0.0)
    category = Column(String(100), index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class Alternative(Base):
    """대체 재료 매핑 모델"""
    __tablename__ = "alternatives"

    id = Column(Integer, primary_key=True, index=True)
    original_food = Column(String(255), nullable=False, index=True)
    alternative_food = Column(String(255), nullable=False)
    nutrient_type = Column(String(50), nullable=False, index=True)
    reduction_percentage = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


class UserQuery(Base):
    """사용자 대화 기록 모델"""
    __tablename__ = "user_queries"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    user_question = Column(Text, nullable=False)
    bot_answer = Column(Text)
    nutrition_info = Column(JSON)
    risk_level = Column(String(20))
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)


class QuizHistory(Base):
    """퀴즈 기록 모델"""
    __tablename__ = "quiz_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    question = Column(Text, nullable=False)
    user_answer = Column(Text)
    correct_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    explanation = Column(Text)
    difficulty = Column(String(20))
    question_type = Column(String(20))
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)


class RecommendedResource(Base):
    """추천 자료 캐시 모델"""
    __tablename__ = "recommended_resources"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, nullable=False, index=True)
    resources = Column(JSON, nullable=False)
    last_updated = Column(TIMESTAMP, server_default=func.now())


# 테이블 생성
def create_tables():
    """모든 테이블 생성"""
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 테이블 생성 완료")


if __name__ == "__main__":
    create_tables()
