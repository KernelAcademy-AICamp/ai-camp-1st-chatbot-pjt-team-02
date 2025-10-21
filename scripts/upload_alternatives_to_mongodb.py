"""alternatives.xlsx 데이터를 MongoDB Atlas에 업로드하는 스크립트"""

import os
import sys
import pandas as pd
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.mongodb_client import get_mongodb_client
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def upload_alternatives_to_mongodb(
    excel_path: str = "data/raw/alternatives.xlsx",
    drop_existing: bool = False
):
    """
    alternatives.xlsx 파일을 MongoDB에 업로드

    Args:
        excel_path: Excel 파일 경로
        drop_existing: 기존 컬렉션 삭제 여부
    """
    # 1. Excel 파일 읽기
    excel_full_path = project_root / excel_path
    logger.info(f"📂 Excel 파일 읽는 중: {excel_full_path}")

    try:
        df = pd.read_excel(excel_full_path)
        logger.info(f"✅ Excel 파일 로드 완료: {len(df)}개 행")
    except Exception as e:
        logger.error(f"❌ Excel 파일 읽기 실패: {e}")
        return

    # 2. 데이터 확인
    logger.info(f"컬럼: {df.columns.tolist()}")
    logger.info(f"샘플 데이터:\n{df.head(3)}")

    # 3. MongoDB 클라이언트 연결
    try:
        mongo_client = get_mongodb_client()
        collection = mongo_client.get_collection("alternatives")
    except Exception as e:
        logger.error(f"❌ MongoDB 연결 실패: {e}")
        return

    # 4. 기존 컬렉션 삭제 (옵션)
    if drop_existing:
        collection.drop()
        logger.info("🗑️ 기존 alternatives 컬렉션 삭제 완료")

    # 5. 데이터 변환 (DataFrame → Dict)
    documents = df.to_dict('records')

    # 6. MongoDB에 삽입
    try:
        logger.info(f"💾 MongoDB에 {len(documents)}개 문서 삽입 중...")
        result = collection.insert_many(documents, ordered=False)  # 중복 무시하고 계속
        logger.info(f"✅ {len(result.inserted_ids)}개 문서 삽입 완료")
    except Exception as e:
        logger.error(f"⚠️ 삽입 중 일부 오류 발생: {e}")

    # 7. 인덱스 생성 (검색 속도 향상)
    logger.info("🔧 인덱스 생성 중...")
    mongo_client.create_indexes("alternatives", [
        ("원재료", 1),          # 원재료명 인덱스
        ("영양소종류", 1),      # 영양소 종류 인덱스
        ("감소비율", -1)        # 감소비율 내림차순 인덱스
    ])

    # 8. 검증: 총 문서 수 확인
    total_count = collection.count_documents({})
    logger.info(f"📊 최종 저장된 문서 수: {total_count}개")

    # 9. 샘플 검색 테스트
    logger.info("\n🔍 샘플 검색 테스트: '김치' 관련 대체재")
    sample_results = list(collection.find({"원재료": {"$regex": "김치", "$options": "i"}}).limit(3))
    for idx, doc in enumerate(sample_results, 1):
        logger.info(f"  {idx}. {doc.get('원재료')} → {doc.get('대체재료')} ({doc.get('영양소종류')}, 감소율: {doc.get('감소비율')}%)")

    logger.info("\n✅ 업로드 완료!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="alternatives.xlsx를 MongoDB에 업로드")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="기존 alternatives 컬렉션을 삭제하고 새로 생성"
    )
    parser.add_argument(
        "--file",
        type=str,
        default="data/raw/alternatives.xlsx",
        help="Excel 파일 경로 (기본값: data/raw/alternatives.xlsx)"
    )

    args = parser.parse_args()

    upload_alternatives_to_mongodb(excel_path=args.file, drop_existing=args.drop)
