"""MongoDB 통합 테스트 스크립트 (간소화 버전)"""

import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.alternative_search import search_alternatives_from_mongodb, extract_ingredients_from_text
from src.utils.mongodb_client import get_mongodb_client

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


def test_mongodb_connection():
    """MongoDB 연결 테스트"""
    print("="*70)
    print("📋 테스트 1: MongoDB 연결")
    print("="*70)

    try:
        client = get_mongodb_client()
        collection = client.get_collection("alternatives")
        count = collection.count_documents({})
        print(f"✅ MongoDB 연결 성공!")
        print(f"📊 alternatives 컬렉션 문서 수: {count}개\n")
        return True
    except Exception as e:
        print(f"❌ MongoDB 연결 실패: {e}\n")
        return False


def test_alternative_search():
    """대체재 검색 기능 테스트"""
    print("="*70)
    print("📋 테스트 2: 대체재 검색 기능")
    print("="*70)

    test_cases = [
        {
            "dish": "김치찌개",
            "ingredients": ["김치", "두부", "돼지고기", "양파"]
        },
        {
            "dish": "된장찌개",
            "ingredients": ["된장", "두부", "호박", "버섯"]
        }
    ]

    for test in test_cases:
        print(f"\n🍲 요리: {test['dish']}")
        print(f"📝 재료: {', '.join(test['ingredients'])}\n")

        try:
            result = search_alternatives_from_mongodb(
                test['ingredients'],
                max_per_ingredient=2
            )

            if result:
                print(result)
            else:
                print("⚠️ 검색 결과 없음")

            print("\n" + "-"*70)

        except Exception as e:
            print(f"❌ 오류 발생: {e}\n")


def test_ingredient_extraction():
    """재료 추출 기능 테스트"""
    print("\n" + "="*70)
    print("📋 테스트 3: 재료 추출 기능")
    print("="*70)

    sample_text = """
    김치찌개 재료:
    - 김치 200g
    - 두부 1/2모
    - 돼지고기 100g
    - 양파 1/2개
    - 대파 1줌
    """

    print(f"\n원본 텍스트:\n{sample_text}")

    extracted = extract_ingredients_from_text(sample_text)
    print(f"\n추출된 재료: {extracted}\n")


def main():
    """전체 테스트 실행"""
    print("\n" + "🔬 MongoDB 통합 테스트 시작".center(70, "="))
    print()

    # 1. MongoDB 연결 테스트
    if not test_mongodb_connection():
        print("❌ MongoDB 연결 실패로 테스트 중단")
        return

    # 2. 대체재 검색 테스트
    test_alternative_search()

    # 3. 재료 추출 테스트
    test_ingredient_extraction()

    print("\n" + "✅ MongoDB 통합 테스트 완료!".center(70, "="))


if __name__ == "__main__":
    main()
