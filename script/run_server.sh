#!/bin/bash

echo "🚀 NutriCoach FastAPI 서버 시작 스크립트"
echo "=========================================="

# 가상환경 확인
if [ ! -d ".venv" ]; then
    echo "⚠️  가상환경이 없습니다. 생성 중..."
    python3 -m venv .venv
fi

# 가상환경 활성화
echo "📦 가상환경 활성화 중..."
source .venv/bin/activate

# 패키지 확인
echo "📋 필요한 패키지 확인 중..."
pip show fastapi > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📥 패키지 설치 중..."
    pip install -r requirements.txt
fi

# 환경 변수 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다!"
    echo "   cp .env.example .env 실행 후 API 키를 설정하세요."
    exit 1
fi

echo ""
echo "✅ 준비 완료! FastAPI 서버 시작..."
echo "=========================================="
echo ""
echo "📍 API 문서: http://localhost:8000/docs"
echo "📍 헬스 체크: http://localhost:8000/health"
echo ""
echo "종료하려면 Ctrl+C를 누르세요."
echo ""

# FastAPI 서버 실행
python -m src.backend.main