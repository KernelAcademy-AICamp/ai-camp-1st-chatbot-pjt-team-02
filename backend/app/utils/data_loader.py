"""
식품 영양 데이터 로더 유틸리티
국가표준식품성분표 Excel 파일을 PostgreSQL로 로드
"""

import pandas as pd
from sqlalchemy.orm import Session
import logging

from app.models.database import Food

logger = logging.getLogger(__name__)


def load_foods_from_excel(db: Session, file_path: str) -> int:
    """
    Excel 파일에서 식품 영양 정보 로드

    Args:
        db: 데이터베이스 세션
        file_path: Excel 파일 경로

    Returns:
        로드된 레코드 수

    Excel 형식:
        - 식품명: 식품 이름
        - 나트륨: 나트륨 함량 (mg)
        - 칼륨: 칼륨 함량 (mg)
        - 인: 인 함량 (mg)
        - 단백질: 단백질 함량 (g)
        - 칼로리: 칼로리 (kcal)
        - 분류: 식품 카테고리 (선택)
    """
    try:
        logger.info(f"Excel 파일 로드 시작: {file_path}")

        # Excel 파일 읽기
        df = pd.read_excel(file_path)

        # 필수 컬럼 확인
        required_columns = ['식품명', '나트륨', '칼륨', '인', '단백질', '칼로리']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"필수 컬럼 없음: {missing_columns}")

        # 데이터 로드
        loaded_count = 0
        skipped_count = 0

        for idx, row in df.iterrows():
            try:
                # 식품명 확인
                food_name = str(row.get('식품명', '')).strip()
                if not food_name or food_name == 'nan':
                    skipped_count += 1
                    continue

                # 기존 데이터 확인
                existing_food = db.query(Food).filter(
                    Food.name == food_name
                ).first()

                if existing_food:
                    # 업데이트
                    existing_food.sodium = float(row.get('나트륨', 0) or 0)
                    existing_food.potassium = float(row.get('칼륨', 0) or 0)
                    existing_food.phosphorus = float(row.get('인', 0) or 0)
                    existing_food.protein = float(row.get('단백질', 0) or 0)
                    existing_food.calories = float(row.get('칼로리', 0) or 0)
                    existing_food.category = str(row.get('분류', '')) if pd.notna(row.get('분류')) else None
                    logger.debug(f"업데이트: {food_name}")
                else:
                    # 신규 추가
                    new_food = Food(
                        name=food_name,
                        sodium=float(row.get('나트륨', 0) or 0),
                        potassium=float(row.get('칼륨', 0) or 0),
                        phosphorus=float(row.get('인', 0) or 0),
                        protein=float(row.get('단백질', 0) or 0),
                        calories=float(row.get('칼로리', 0) or 0),
                        category=str(row.get('분류', '')) if pd.notna(row.get('분류')) else None
                    )
                    db.add(new_food)
                    logger.debug(f"추가: {food_name}")

                loaded_count += 1

                # 100개마다 커밋
                if loaded_count % 100 == 0:
                    db.commit()
                    logger.info(f"진행: {loaded_count}개 로드됨...")

            except Exception as e:
                logger.error(f"행 {idx} 처리 실패: {str(e)}")
                skipped_count += 1
                continue

        # 최종 커밋
        db.commit()

        logger.info(f"Excel 로드 완료: {loaded_count}개 로드, {skipped_count}개 스킵")
        return loaded_count

    except FileNotFoundError:
        logger.error(f"파일 없음: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Excel 로드 실패: {str(e)}")
        db.rollback()
        raise


def load_alternatives_from_excel(db: Session, file_path: str) -> int:
    """
    Excel 파일에서 대체 재료 정보 로드

    Args:
        db: 데이터베이스 세션
        file_path: Excel 파일 경로

    Returns:
        로드된 레코드 수

    Excel 형식:
        - 원래_식품: 원래 식품명
        - 대체_식품: 대체 식품명
        - 영양소_타입: sodium, potassium, phosphorus, protein 중 하나
        - 감소율: 감소 비율 (%)
        - 비고: 추가 설명 (선택)
    """
    try:
        from app.models.database import Alternative

        logger.info(f"대체재료 Excel 로드 시작: {file_path}")

        df = pd.read_excel(file_path)

        loaded_count = 0

        for idx, row in df.iterrows():
            try:
                original = str(row.get('원래_식품', '')).strip()
                alternative = str(row.get('대체_식품', '')).strip()
                nutrient = str(row.get('영양소_타입', '')).strip()

                if not original or not alternative or not nutrient:
                    continue

                new_alt = Alternative(
                    original_food=original,
                    alternative_food=alternative,
                    nutrient_type=nutrient,
                    reduction_percentage=float(row.get('감소율', 0) or 0),
                    notes=str(row.get('비고', '')) if pd.notna(row.get('비고')) else None
                )
                db.add(new_alt)
                loaded_count += 1

            except Exception as e:
                logger.error(f"행 {idx} 처리 실패: {str(e)}")
                continue

        db.commit()
        logger.info(f"대체재료 로드 완료: {loaded_count}개")
        return loaded_count

    except Exception as e:
        logger.error(f"대체재료 로드 실패: {str(e)}")
        db.rollback()
        raise


# 스크립트 실행용
if __name__ == "__main__":
    import sys
    from app.models.database import SessionLocal

    if len(sys.argv) < 3:
        print("사용법: python data_loader.py <foods|alternatives> <excel_file_path>")
        sys.exit(1)

    load_type = sys.argv[1]
    file_path = sys.argv[2]

    db = SessionLocal()

    try:
        if load_type == "foods":
            count = load_foods_from_excel(db, file_path)
            print(f"✅ {count}개 식품 로드 완료!")
        elif load_type == "alternatives":
            count = load_alternatives_from_excel(db, file_path)
            print(f"✅ {count}개 대체재료 로드 완료!")
        else:
            print("❌ load_type은 'foods' 또는 'alternatives'여야 합니다.")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        sys.exit(1)
    finally:
        db.close()
