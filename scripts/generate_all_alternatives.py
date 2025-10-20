#!/usr/bin/env python3
"""
국가표준식품성분표 기반 전체 대체재료 자동 생성
모든 고위험 식품에 대해 저위험 대체재료를 자동 매칭
"""

import os
import pandas as pd
import numpy as np
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_alternative_food(df, original_food, nutrient_col, nutrient_name, category):
    """
    같은 식품군 내에서 영양소가 낮은 대체 식품 찾기
    """
    # 같은 식품군 내 식품들
    same_category = df[df['식품군'] == category].copy()

    if len(same_category) == 0:
        return None, 0

    # 원본 식품의 영양소 값
    original_value = original_food[nutrient_col]

    # 영양소 값이 원본의 50% 이하인 식품들 찾기
    target_value = original_value * 0.5
    candidates = same_category[same_category[nutrient_col] < target_value].copy()

    if len(candidates) == 0:
        # 50% 이하가 없으면 가장 낮은 것
        candidates = same_category.nsmallest(5, nutrient_col)

    # 자기 자신 제외
    candidates = candidates[candidates['식품명'] != original_food['식품명']]

    if len(candidates) == 0:
        return None, 0

    # 가장 낮은 것 선택
    alternative = candidates.iloc[0]

    # 감소 비율 계산
    if original_value > 0:
        reduction = ((original_value - alternative[nutrient_col]) / original_value) * 100
    else:
        reduction = 0

    return alternative, reduction


def generate_all_alternatives():
    """모든 고위험 식품에 대한 대체재료 생성"""

    # 국가표준식품성분표 읽기
    file_path = os.path.join('Documents', 'Data', '국가표준식품성분표_250426공개.xlsx')
    df = pd.read_excel(file_path, sheet_name='국가표준식품성분 Database 10.2', header=2)

    # 데이터 정리
    df['식품군'] = df.iloc[:, 2]
    df['식품명'] = df.iloc[:, 3]
    df['나트륨'] = pd.to_numeric(df.iloc[:, 26], errors='coerce')
    df['칼륨'] = pd.to_numeric(df.iloc[:, 25], errors='coerce')
    df['인'] = pd.to_numeric(df.iloc[:, 24], errors='coerce')
    df['단백질'] = pd.to_numeric(df.iloc[:, 7], errors='coerce')

    # 결측값 제거
    df = df.dropna(subset=['식품명', '식품군'])

    # 위험 기준
    HIGH_SODIUM = 500      # mg/100g
    HIGH_POTASSIUM = 400   # mg/100g
    HIGH_PHOSPHORUS = 250  # mg/100g
    HIGH_PROTEIN = 20      # g/100g

    # 조미료, 음료, 주류 제외
    exclude_categories = ['조미료류', '음료 및 주류', '기타']
    common_foods = df[~df['식품군'].isin(exclude_categories)].copy()

    alternatives_data = []

    # 1. 고나트륨 식품 처리
    logger.info("고나트륨 식품 대체재료 생성 중...")
    high_sodium = common_foods[common_foods['나트륨'] > HIGH_SODIUM].copy()

    for idx, row in high_sodium.iterrows():
        alt, reduction = find_alternative_food(df, row, '나트륨', 'sodium', row['식품군'])
        if alt is not None and reduction > 0:
            alternatives_data.append({
                '원재료': row['식품명'],
                '대체재료': alt['식품명'],
                '영양소종류': 'sodium',
                '감소비율': round(reduction, 1),
                '비고': f"{row['식품군']} - 나트륨 {row['나트륨']:.0f}mg → {alt['나트륨']:.0f}mg"
            })

    logger.info(f"  → 나트륨 대체재료 {len([x for x in alternatives_data if x['영양소종류'] == 'sodium'])}개 생성")

    # 2. 고칼륨 식품 처리
    logger.info("고칼륨 식품 대체재료 생성 중...")
    high_potassium = common_foods[common_foods['칼륨'] > HIGH_POTASSIUM].copy()

    for idx, row in high_potassium.iterrows():
        # 이미 나트륨으로 처리된 식품은 스킵
        if any(x['원재료'] == row['식품명'] for x in alternatives_data):
            continue

        alt, reduction = find_alternative_food(df, row, '칼륨', 'potassium', row['식품군'])
        if alt is not None and reduction > 0:
            alternatives_data.append({
                '원재료': row['식품명'],
                '대체재료': alt['식품명'],
                '영양소종류': 'potassium',
                '감소비율': round(reduction, 1),
                '비고': f"{row['식품군']} - 칼륨 {row['칼륨']:.0f}mg → {alt['칼륨']:.0f}mg"
            })

    logger.info(f"  → 칼륨 대체재료 {len([x for x in alternatives_data if x['영양소종류'] == 'potassium'])}개 생성")

    # 3. 고인 식품 처리
    logger.info("고인 식품 대체재료 생성 중...")
    high_phosphorus = common_foods[common_foods['인'] > HIGH_PHOSPHORUS].copy()

    for idx, row in high_phosphorus.iterrows():
        # 이미 처리된 식품은 스킵
        if any(x['원재료'] == row['식품명'] for x in alternatives_data):
            continue

        alt, reduction = find_alternative_food(df, row, '인', 'phosphorus', row['식품군'])
        if alt is not None and reduction > 0:
            alternatives_data.append({
                '원재료': row['식품명'],
                '대체재료': alt['식품명'],
                '영양소종류': 'phosphorus',
                '감소비율': round(reduction, 1),
                '비고': f"{row['식품군']} - 인 {row['인']:.0f}mg → {alt['인']:.0f}mg"
            })

    logger.info(f"  → 인 대체재료 {len([x for x in alternatives_data if x['영양소종류'] == 'phosphorus'])}개 생성")

    # 4. 고단백 식품 처리
    logger.info("고단백 식품 대체재료 생성 중...")
    high_protein = common_foods[common_foods['단백질'] > HIGH_PROTEIN].copy()

    for idx, row in high_protein.iterrows():
        # 이미 처리된 식품은 스킵
        if any(x['원재료'] == row['식품명'] for x in alternatives_data):
            continue

        alt, reduction = find_alternative_food(df, row, '단백질', 'protein', row['식품군'])
        if alt is not None and reduction > 0:
            alternatives_data.append({
                '원재료': row['식품명'],
                '대체재료': alt['식품명'],
                '영양소종류': 'protein',
                '감소비율': round(reduction, 1),
                '비고': f"{row['식품군']} - 단백질 {row['단백질']:.1f}g → {alt['단백질']:.1f}g"
            })

    logger.info(f"  → 단백질 대체재료 {len([x for x in alternatives_data if x['영양소종류'] == 'protein'])}개 생성")

    return alternatives_data


def main():
    """메인 실행 함수"""
    logger.info("=" * 80)
    logger.info("국가표준식품성분표 기반 전체 대체재료 자동 생성")
    logger.info("=" * 80)

    # 대체재료 생성
    alternatives_data = generate_all_alternatives()

    # 엑셀 저장
    output_path = os.path.join('Documents', 'Data', 'alternatives.xlsx')
    df = pd.DataFrame(alternatives_data)
    df.to_excel(output_path, index=False, sheet_name='대체재료매핑')

    logger.info("\n" + "=" * 80)
    logger.info(f"✅ 대체재료 엑셀 생성 완료: {output_path}")
    logger.info(f"  - 총 {len(alternatives_data)}개 매핑")
    logger.info("\n영양소별 분포:")
    logger.info(f"  - 나트륨(sodium): {sum(1 for x in alternatives_data if x['영양소종류'] == 'sodium')}개")
    logger.info(f"  - 칼륨(potassium): {sum(1 for x in alternatives_data if x['영양소종류'] == 'potassium')}개")
    logger.info(f"  - 인(phosphorus): {sum(1 for x in alternatives_data if x['영양소종류'] == 'phosphorus')}개")
    logger.info(f"  - 단백질(protein): {sum(1 for x in alternatives_data if x['영양소종류'] == 'protein')}개")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
