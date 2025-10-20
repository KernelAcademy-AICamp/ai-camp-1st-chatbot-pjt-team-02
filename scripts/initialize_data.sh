#!/bin/bash
# 데이터 초기화 통합 스크립트
# 1. 국가표준식품성분표 → PostgreSQL 로드
# 2. 대체재료 엑셀 → PostgreSQL 로드
# 3. PDF → FAISS 로드 (선택적)

set -e  # 에러 발생 시 즉시 중단

echo "=========================================="
echo "콩닥식탁 데이터 초기화 시작"
echo "=========================================="

# 스크립트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Python 실행 파일 찾기
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ Python이 설치되어 있지 않습니다"
    exit 1
fi

echo ""
echo "Python: $PYTHON"
echo ""

# 1단계: 필수 파일 확인
echo "=========================================="
echo "[1/3] 필수 파일 확인"
echo "=========================================="

NATIONAL_DB="../Documents/Data/국가표준식품성분표_250426공개.xlsx"
ALTERNATIVES="../Documents/Data/alternatives.xlsx"

if [ ! -f "$NATIONAL_DB" ]; then
    echo "❌ 국가표준식품성분표 파일이 없습니다: $NATIONAL_DB"
    echo "   파일을 Documents/Data/ 디렉토리에 추가하세요"
    exit 1
fi

if [ ! -f "$ALTERNATIVES" ]; then
    echo "⚠️  대체재료 파일이 없습니다: $ALTERNATIVES"
    echo "   대체재료 없이 계속 진행합니다 (기본 영양 분석만 가능)"
    echo "   대체재료 추천 기능을 사용하려면 alternatives.xlsx를 직접 작성하세요"
fi

echo "✅ 필수 파일 확인 완료"
echo "  - 국가표준식품성분표: $NATIONAL_DB"
if [ -f "$ALTERNATIVES" ]; then
    echo "  - 대체재료: $ALTERNATIVES"
else
    echo "  - 대체재료: (없음 - 선택사항)"
fi
echo ""

# 2단계: 엑셀 데이터를 PostgreSQL로 로드
echo "=========================================="
echo "[2/3] 엑셀 → PostgreSQL 데이터 로드"
echo "=========================================="
$PYTHON load_excel_to_db.py
if [ $? -ne 0 ]; then
    echo "❌ DB 로드 실패"
    exit 1
fi
echo "✅ DB 로드 완료"
echo ""

# 3단계: PDF를 FAISS로 로드 (선택적)
echo "=========================================="
echo "[3/3] PDF → FAISS 벡터 저장소 로드"
echo "=========================================="

# PDF 파일 존재 여부 확인
PDF_DIR="../Documents/Data"
PDF_COUNT=$(find "$PDF_DIR" -name "*.pdf" 2>/dev/null | wc -l)

if [ $PDF_COUNT -eq 0 ]; then
    echo "⚠️  PDF 파일이 없습니다 (선택적 단계 - 스킵)"
    echo "   PDF 파일을 $PDF_DIR 에 추가하면 RAG 기능이 활성화됩니다"
else
    echo "발견된 PDF 파일: $PDF_COUNT 개"
    $PYTHON load_pdfs_to_faiss.py
    if [ $? -ne 0 ]; then
        echo "⚠️  FAISS 로드 실패 (선택적 단계 - 계속 진행)"
    else
        echo "✅ FAISS 로드 완료"
    fi
fi

echo ""
echo "=========================================="
echo "✅ 데이터 초기화 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "1. 백엔드 서버 시작: cd ../backend && uvicorn app.main:app --reload"
echo "2. 프론트엔드 시작: cd ../frontend && streamlit run app.py"
echo "3. 또는 Docker 사용: cd .. && docker-compose up"
echo ""
