#!/bin/bash

# 콩닥식탁 실행 스크립트

echo "🥗 콩닥식탁 챗봇 시작..."
echo ""

# 환경 변수 확인
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다."
    echo "📝 .env.example을 복사하여 .env 파일을 생성하세요:"
    echo "   cp .env.example .env"
    echo ""
    echo "⚠️  다음 환경 변수를 설정해야 합니다:"
    echo "   - OPENAI_API_KEY: OpenAI API 키"
    echo "   - DB_PASSWORD: PostgreSQL 비밀번호"
    exit 1
fi

# OpenAI API 키 확인
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  OpenAI API 키가 설정되지 않았습니다."
    echo "📝 .env 파일에 OPENAI_API_KEY를 설정하세요."
    echo ""
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Docker 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되어 있지 않습니다."
    echo "📥 https://www.docker.com/get-started 에서 Docker를 설치하세요."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되어 있지 않습니다."
    echo "📥 https://docs.docker.com/compose/install/ 에서 Docker Compose를 설치하세요."
    exit 1
fi

# Docker 서비스 실행 여부 확인
if ! docker info &> /dev/null; then
    echo "❌ Docker 서비스가 실행되고 있지 않습니다."
    echo "🚀 Docker Desktop을 실행하세요."
    exit 1
fi

echo "✅ 환경 확인 완료"
echo ""

# 기존 컨테이너 중지 (선택사항)
echo "🔍 기존 컨테이너 확인 중..."
if docker-compose ps | grep -q "Up"; then
    echo "⚠️  기존 컨테이너가 실행 중입니다."
    read -p "기존 컨테이너를 중지하고 재시작하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 기존 컨테이너 중지 중..."
        docker-compose down
    fi
fi

echo ""
echo "🚀 Docker Compose 실행 중..."
echo "   - PostgreSQL (포트 5432)"
echo "   - FastAPI 백엔드 (포트 8000)"
echo "   - Streamlit 프론트엔드 (포트 8501)"
echo ""

# Docker Compose 실행 (백그라운드)
docker-compose up -d

# 서비스 시작 대기
echo ""
echo "⏳ 서비스 시작 대기 중..."
sleep 5

# 서비스 상태 확인
echo ""
echo "📊 서비스 상태 확인:"
docker-compose ps

# 헬스 체크
echo ""
echo "🏥 헬스 체크 중..."

# PostgreSQL 확인
if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
    echo "  ✅ PostgreSQL: 정상"
else
    echo "  ❌ PostgreSQL: 오류"
fi

# 백엔드 확인
if curl -s http://localhost:8000/health &> /dev/null; then
    echo "  ✅ 백엔드 (FastAPI): 정상"
else
    echo "  ❌ 백엔드 (FastAPI): 오류"
    echo "     로그 확인: docker-compose logs backend"
fi

# 프론트엔드 확인 (Streamlit은 시작 시간이 더 걸림)
sleep 3
if curl -s http://localhost:8501 &> /dev/null; then
    echo "  ✅ 프론트엔드 (Streamlit): 정상"
else
    echo "  ⏳ 프론트엔드 (Streamlit): 시작 중... (조금 더 기다려주세요)"
fi

echo ""
echo "✨ 콩닥식탁 챗봇이 실행되었습니다!"
echo ""
echo "📍 접속 정보:"
echo "   - 프론트엔드: http://localhost:8501"
echo "   - 백엔드 API: http://localhost:8000/api/docs"
echo "   - 데이터베이스: localhost:5432 (postgres/kongdak_db)"
echo ""
echo "📝 사용 가이드:"
echo "   1. 브라우저에서 http://localhost:8501 접속"
echo "   2. 채팅 탭에서 음식에 대해 질문하기"
echo "      예: '떡볶이 먹어도 될까요?'"
echo "   3. 영양 분석 탭에서 차트 확인"
echo "   4. 학습 자료 탭에서 추천 자료 검색"
echo ""
echo "🛑 종료 방법:"
echo "   docker-compose down"
echo ""
echo "📋 로그 확인:"
echo "   docker-compose logs -f"
echo ""

# 브라우저 자동 열기 (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    read -p "브라우저를 자동으로 여시겠습니까? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "🌐 브라우저 열기..."
        sleep 2
        open http://localhost:8501
    fi
fi

echo "Happy chatting! 🥗"
