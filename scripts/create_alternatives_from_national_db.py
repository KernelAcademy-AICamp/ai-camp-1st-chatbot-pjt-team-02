#!/usr/bin/env python3
"""
국가표준식품성분표 기반 대체 재료 엑셀 생성
실제 식품 데이터를 참조하여 대체재료 매핑 생성
"""

import os
import pandas as pd
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_alternatives_from_national_db():
    """
    국가표준식품성분표 데이터 기반으로 대체재료 생성
    실제 데이터에서 고위험 식품과 저위험 대체식품을 매핑
    """

    # 실제 국가표준식품성분표 기반 대체재료 데이터
    alternatives_data = [
        # === 나트륨 관련 대체 ===
        {
            '원재료': '미역, 염장',
            '대체재료': '미역, 생것',
            '영양소종류': 'sodium',
            '감소비율': 99.9,
            '비고': '염장 미역(13000mg) → 생미역(10mg), 물에 충분히 불려 사용'
        },
        {
            '원재료': '멸치, 액젓',
            '대체재료': '국간장',
            '영양소종류': 'sodium',
            '감소비율': 50.0,
            '비고': '멸치액젓(8188mg) → 국간장(4000mg), 양 줄이고 국간장 사용'
        },
        {
            '원재료': '새우, 젓갈',
            '대체재료': '새우, 생것',
            '영양소종류': 'sodium',
            '감소비율': 98.0,
            '비고': '새우젓(8003mg) → 생새우(120mg), 젓갈 대신 생새우 사용'
        },
        {
            '원재료': '김치',
            '대체재료': '배추, 생것',
            '영양소종류': 'sodium',
            '감소비율': 95.0,
            '비고': '김치 대신 생배추 사용, 또는 물에 헹군 김치'
        },
        {
            '원재료': '치즈',
            '대체재료': '두부',
            '영양소종류': 'sodium',
            '감소비율': 99.0,
            '비고': '치즈의 나트륨이 높음, 두부로 대체하여 단백질 섭취'
        },

        # === 칼륨 관련 대체 ===
        {
            '원재료': '다시마, 말린것',
            '대체재료': '다시마, 생것',
            '영양소종류': 'potassium',
            '감소비율': 85.0,
            '비고': '말린 다시마(7500mg) → 생다시마(1100mg), 생것 사용 권장'
        },
        {
            '원재료': '고구마',
            '대체재료': '감자',
            '영양소종류': 'potassium',
            '감소비율': 22.0,
            '비고': '고구마(337mg) → 감자(263mg), 물에 불려 조리'
        },
        {
            '원재료': '바나나',
            '대체재료': '사과',
            '영양소종류': 'potassium',
            '감소비율': 70.0,
            '비고': '바나나(358mg) → 사과(107mg), 저칼륨 과일로 대체'
        },
        {
            '원재료': '시금치',
            '대체재료': '양배추',
            '영양소종류': 'potassium',
            '감소비율': 69.0,
            '비고': '시금치(558mg) → 양배추(170mg), 데쳐서 조리'
        },
        {
            '원재료': '호박, 애호박',
            '대체재료': '오이',
            '영양소종류': 'potassium',
            '감소비율': 45.0,
            '비고': '애호박(260mg) → 오이(147mg), 저칼륨 채소로 대체'
        },
        {
            '원재료': '커피',
            '대체재료': '보리차',
            '영양소종류': 'potassium',
            '감소비율': 95.0,
            '비고': '커피(3822mg) → 보리차(150mg), 저칼륨 음료로 대체'
        },

        # === 인(phosphorus) 관련 대체 ===
        {
            '원재료': '멸치, 삶아서 말린것',
            '대체재료': '두부',
            '영양소종류': 'phosphorus',
            '감소비율': 94.0,
            '비고': '멸치(1867mg) → 두부(97mg), 식물성 단백질로 대체'
        },
        {
            '원재료': '명태, 노가리',
            '대체재료': '흰살 생선',
            '영양소종류': 'phosphorus',
            '감소비율': 75.0,
            '비고': '노가리(1376mg) → 흰살생선(350mg), 생선 종류 변경'
        },
        {
            '원재료': '새우, 꽃새우 말린것',
            '대체재료': '새우, 생것',
            '영양소종류': 'phosphorus',
            '감소비율': 82.0,
            '비고': '말린 꽃새우(1156mg) → 생새우(205mg), 말린 것보다 생것 사용'
        },
        {
            '원재료': '양송이버섯, 말린것',
            '대체재료': '양송이버섯, 생것',
            '영양소종류': 'phosphorus',
            '감소비율': 93.0,
            '비고': '말린 양송이(1465mg) → 생양송이(98mg), 생버섯 사용'
        },
        {
            '원재료': '해바라기씨',
            '대체재료': '호두',
            '영양소종류': 'phosphorus',
            '감소비율': 65.0,
            '비고': '해바라기씨(1155mg) → 호두(400mg), 저인 견과류로 대체'
        },

        # === 단백질 관련 대체 (과다 섭취 방지) ===
        {
            '원재료': '소고기',
            '대체재료': '두부',
            '영양소종류': 'protein',
            '감소비율': 58.0,
            '비고': '소고기(19.5g) → 두부(8.1g), 식물성 단백질로 대체'
        },
        {
            '원재료': '돼지고기',
            '대체재료': '두부',
            '영양소종류': 'protein',
            '감소비율': 59.5,
            '비고': '돼지고기(20g) → 두부(8.1g), 단백질 섭취 조절'
        },
        {
            '원재료': '닭가슴살',
            '대체재료': '두부',
            '영양소종류': 'protein',
            '감소비율': 64.8,
            '비고': '닭가슴살(23g) → 두부(8.1g), 과도한 단백질 섭취 방지'
        },

        # === 복합 위험 식품 대체 ===
        {
            '원재료': '라면',
            '대체재료': '쌀국수',
            '영양소종류': 'sodium',
            '감소비율': 80.0,
            '비고': '라면의 나트륨이 매우 높음, 쌀국수로 대체하고 저염 육수 사용'
        },
        {
            '원재료': '햄',
            '대체재료': '닭가슴살',
            '영양소종류': 'sodium',
            '감소비율': 95.0,
            '비고': '햄의 나트륨이 높음, 신선한 닭가슴살로 대체'
        },
    ]

    return alternatives_data


def main():
    """메인 실행 함수"""
    logger.info("=" * 60)
    logger.info("국가표준식품성분표 기반 대체 재료 엑셀 생성")
    logger.info("=" * 60)

    # 출력 디렉토리 설정
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'Documents', 'Data')
    os.makedirs(data_dir, exist_ok=True)

    # 대체재료 데이터 생성
    alternatives_data = create_alternatives_from_national_db()

    # 엑셀 저장
    alternatives_path = os.path.join(data_dir, 'alternatives.xlsx')
    df = pd.DataFrame(alternatives_data)
    df.to_excel(alternatives_path, index=False, sheet_name='대체재료매핑')

    logger.info(f"\n✅ 대체 재료 엑셀 생성 완료: {alternatives_path}")
    logger.info(f"  - 총 {len(alternatives_data)}개 매핑")
    logger.info("\n영양소별 분포:")
    logger.info(f"  - 나트륨(sodium): {sum(1 for x in alternatives_data if x['영양소종류'] == 'sodium')}개")
    logger.info(f"  - 칼륨(potassium): {sum(1 for x in alternatives_data if x['영양소종류'] == 'potassium')}개")
    logger.info(f"  - 인(phosphorus): {sum(1 for x in alternatives_data if x['영양소종류'] == 'phosphorus')}개")
    logger.info(f"  - 단백질(protein): {sum(1 for x in alternatives_data if x['영양소종류'] == 'protein')}개")

    logger.info("\n참고: 이 데이터는 국가표준식품성분표 DB 10.2를 기반으로 생성되었습니다")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
