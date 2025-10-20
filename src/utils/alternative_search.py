"""MongoDB 기반 식재료 대체재 검색 모듈"""

import logging
from typing import List, Dict, Any, Optional
from src.utils.mongodb_client import get_mongodb_client

logger = logging.getLogger(__name__)


def search_alternatives_from_mongodb(
    ingredients: List[str],
    nutrient_priority: Optional[List[str]] = None,
    max_per_ingredient: int = 3
) -> str:
    """
    재료 리스트에서 MongoDB 기반 대체재 검색

    Args:
        ingredients: 원재료 리스트 (예: ['김치', '된장', '두부'])
        nutrient_priority: 영양소 우선순위 (기본: ['sodium', 'potassium', 'phosphorus', 'protein'])
        max_per_ingredient: 재료당 최대 대체재 개수

    Returns:
        포맷팅된 대체재 정보 문자열
    """
    if nutrient_priority is None:
        nutrient_priority = ['sodium', 'potassium', 'phosphorus', 'protein']

    try:
        mongo_client = get_mongodb_client()
    except Exception as e:
        logger.error(f"❌ MongoDB 연결 실패: {e}")
        return "MongoDB 연결 실패"

    result_lines = []
    total_found = 0
    search_summary = []  # 검색 요약 로그용

    for ingredient in ingredients:
        # 재료명 전처리 (쉼표, 공백 등 제거)
        ingredient_clean = ingredient.strip().replace(',', '')

        if not ingredient_clean:
            continue

        try:
            # MongoDB에서 대체재 검색
            alternatives_raw = mongo_client.find_alternatives(
                ingredient=ingredient_clean,
                nutrient_types=nutrient_priority,
                limit=max_per_ingredient * 3  # 중복 제거를 위해 더 많이 가져옴
            )

            # 대체재료 기준으로 중복 제거 (첫 번째로 발견된 것만 유지)
            seen_replacements = set()
            alternatives = []
            for alt in alternatives_raw:
                replacement = alt.get('대체재료', 'N/A')
                if replacement not in seen_replacements:
                    seen_replacements.add(replacement)
                    alternatives.append(alt)
                    if len(alternatives) >= max_per_ingredient:
                        break

            if alternatives:
                # 로그용 요약 (재료명 -> 대체재명 리스트)
                alt_names = [alt.get('대체재료', 'N/A') for alt in alternatives]
                search_summary.append(f"   {len(search_summary)+1}. {ingredient_clean} → {', '.join(alt_names)}")

                result_lines.append(f"\n### 📌 '{ingredient_clean}' 대체재 ({len(alternatives)}개)")

                for idx, alt in enumerate(alternatives, 1):
                    original = alt.get('원재료', 'N/A')
                    replacement = alt.get('대체재료', 'N/A')
                    nutrient_type = alt.get('영양소종류', 'N/A')
                    reduction_rate = alt.get('감소비율', 0)
                    note = alt.get('비고', '')

                    # 영양소 종류 한글 변환
                    nutrient_kr = {
                        'sodium': '나트륨',
                        'potassium': '칼륨',
                        'phosphorus': '인',
                        'protein': '단백질'
                    }.get(nutrient_type, nutrient_type)

                    result_lines.append(
                        f"  {idx}. **{replacement}**\n"
                        f"     - 감소 영양소: {nutrient_kr}\n"
                        f"     - 감소율: {reduction_rate}%\n"
                        f"     - 비고: {note}"
                    )

                total_found += len(alternatives)
        except Exception as e:
            logger.warning(f"⚠️ '{ingredient_clean}' 검색 중 오류 발생: {e}")
            continue

    # 검색 결과 요약 로그 출력
    if search_summary:
        logger.info(f"📋 1차 재료 검색 결과 ({total_found}개):\n" + "\n".join(search_summary))

    if total_found == 0:
        return ""

    header = f"## 🔍 MongoDB 대체재 검색 결과 (총 {total_found}개)\n"
    return header + "\n".join(result_lines)


def extract_ingredients_from_text(text: str) -> List[str]:
    """
    텍스트에서 재료명 추출 (간단한 파싱)

    Args:
        text: 재료 정보가 포함된 텍스트

    Returns:
        추출된 재료명 리스트
    """
    # 줄바꿈 또는 쉼표로 구분된 재료 추출
    import re

    # 필터링할 설명문 키워드 (재료가 아닌 설명문 제거)
    skip_keywords = [
        '일반적으로', '다음과 같습니다', '재료는', '사용되는', '포함', '다음',
        '아래', '입니다', '습니다', '해당', '것입니다', '있습니다', '필요합니다',
        '단백질', '나트륨', '칼륨', '인 ', '칼로리', '영양소', '안전', '구간', '녹색', '빨간색', '노란색'
    ]

    # 패턴: "- 재료명" 또는 "재료명," 형태
    lines = text.split('\n')
    ingredients = []

    for line in lines:
        # 마크다운 강조 제거 (**, *, _)
        line_clean = re.sub(r'[\*_]+', '', line)

        # 콜론(:) 뒤의 영양소 수치 제거 (예: "돼지고기: 2000mg" → "돼지고기")
        if ':' in line_clean:
            line_clean = line_clean.split(':')[0].strip()

        # 설명문 필터링 (키워드가 포함된 경우 제외)
        if any(keyword in line_clean for keyword in skip_keywords):
            continue

        # "- " 또는 숫자. 형태 제거
        cleaned = re.sub(r'^[\s\-\d\.]+', '', line_clean).strip()

        # 괄호 안 내용 제거 (예: "김치 (100g)" → "김치")
        cleaned = re.sub(r'\([^)]*\)', '', cleaned).strip()

        # 숫자+단위 제거 (예: "김치 200g" → "김치")
        cleaned = re.sub(r'\d+\s*(g|kg|ml|L|개|컵|mg|kcal)', '', cleaned).strip()

        # 쉼표로 분리된 경우
        parts = [p.strip() for p in cleaned.split(',') if p.strip()]

        ingredients.extend(parts)

    # 중복 제거 및 빈 값 필터링 (길이가 1~20자인 것만 허용)
    # 숫자만 있는 것 제외
    unique_ingredients = list(dict.fromkeys([
        ing for ing in ingredients
        if ing and 1 < len(ing) <= 20 and not ing.isdigit()
    ]))

    return unique_ingredients


# 사용 예시
if __name__ == "__main__":
    # 테스트
    test_ingredients = ["김치", "된장", "두부", "돼지고기"]
    result = search_alternatives_from_mongodb(test_ingredients)
    print(result)
