#!/bin/bash

echo "🎨 NutriCoach Streamlit UI 시작 스크립트"
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
pip show streamlit > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📥 패키지 설치 중..."
    pip install -r requirements.txt
fi

# FastAPI 서버 확인
echo "🔍 FastAPI 서버 상태 확인 중..."
curl -s http://localhost:8000/health > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  FastAPI 서버가 실행 중이 아닙니다!"
    echo "   다른 터미널에서 다음 명령을 실행하세요:"
    echo "   ./run_server.sh"
    echo ""
    echo "계속 진행하시겠습니까? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
else
    echo "✅ FastAPI 서버 실행 중 확인됨"
fi

echo ""
echo "✅ 준비 완료! Streamlit UI 시작..."
echo "=========================================="
echo ""
echo "📍 웹 브라우저에서 자동으로 열립니다"
echo "📍 수동 접속: http://localhost:8501"
echo ""
echo "종료하려면 Ctrl+C를 누르세요."
echo ""

# Streamlit 앱 실행
streamlit run app_multimodal.py