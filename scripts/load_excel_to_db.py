#!/usr/bin/env python3
"""
엑셀 데이터를 PostgreSQL로 로드하는 스크립트
kongdak-참조소스.py의 패턴을 참조하여 작성
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """PostgreSQL 연결 생성"""
    load_dotenv()

    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'kongdak_db')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        logger.info("PostgreSQL 연결 성공")
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL 연결 실패: {e}")
        sys.exit(1)


def load_foods_from_excel(conn, file_path: str):
    """
    국가표준식품성분표 엑셀에서 식품 영양 정보 로드

    국가표준식품성분표 형식:
    - header=2 (3번째 행부터 데이터)
    - 시트명: '국가표준식품성분 Database 10.2'
    - 컬럼 매핑:
      * 식품군: 컬럼 2 (Unnamed: 2)
      * 식품명: 컬럼 3 (Unnamed: 3)
      * 에너지: 컬럼 5 (kcal)
      * 단백질: 컬럼 7 (g.1)
      * 나트륨: 컬럼 26 (mg.5)
      * 칼륨: 컬럼 25 (mg.4)
      * 인: 컬럼 24 (mg.3)
    """
    if not os.path.exists(file_path):
        logger.warning(f"파일이 존재하지 않습니다: {file_path}")
        return 0

    try:
        # 국가표준식품성분표 형식으로 읽기
        sheet_name = '국가표준식품성분 Database 10.2'
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=2)
        logger.info(f"국가표준식품성분표 로드 완료: {len(df)}개 행")

        # 데이터 준비
        data_to_insert = []
        for idx, row in df.iterrows():
            # 식품명 (컬럼 3)
            food_name = str(row.iloc[3] if pd.notna(row.iloc[3]) else '').strip()
            if not food_name or food_name == '':
                continue

            # 식품군 (컬럼 2)
            category = str(row.iloc[2] if pd.notna(row.iloc[2]) else '')

            # 영양소 추출 (결측값은 0으로 처리)
            calories = float(row.iloc[5]) if pd.notna(row.iloc[5]) else 0.0
            protein = float(row.iloc[7]) if pd.notna(row.iloc[7]) else 0.0
            phosphorus = float(row.iloc[24]) if pd.notna(row.iloc[24]) else 0.0
            potassium = float(row.iloc[25]) if pd.notna(row.iloc[25]) else 0.0
            sodium = float(row.iloc[26]) if pd.notna(row.iloc[26]) else 0.0

            data_to_insert.append((
                food_name,
                sodium,
                potassium,
                phosphorus,
                protein,
                calories,
                category if category else None
            ))

        # 배치 INSERT (ON CONFLICT 처리)
        insert_query = '''
            INSERT INTO foods (name, sodium, potassium, phosphorus, protein, calories, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                sodium = EXCLUDED.sodium,
                potassium = EXCLUDED.potassium,
                phosphorus = EXCLUDED.phosphorus,
                protein = EXCLUDED.protein,
                calories = EXCLUDED.calories,
                category = EXCLUDED.category,
                updated_at = CURRENT_TIMESTAMP
        '''

        with conn.cursor() as cursor:
            execute_batch(cursor, insert_query, data_to_insert, page_size=100)
            conn.commit()

        logger.info(f"식품 데이터 {len(data_to_insert)}개 로드 완료")
        return len(data_to_insert)

    except Exception as e:
        logger.error(f"식품 데이터 로드 실패: {e}")
        logger.error(f"상세 에러: {str(e)}", exc_info=True)
        conn.rollback()
        return 0


def load_alternatives_from_excel(conn, file_path: str):
    """
    엑셀에서 대체 재료 매핑 로드

    엑셀 컬럼:
    - 원재료 (필수)
    - 대체재료 (필수)
    - 영양소종류 (sodium/potassium/phosphorus/protein)
    - 감소비율 (%)
    - 비고
    """
    if not os.path.exists(file_path):
        logger.warning(f"파일이 존재하지 않습니다: {file_path}")
        return 0

    try:
        df = pd.read_excel(file_path)
        logger.info(f"엑셀 파일 로드 완료: {len(df)}개 행")

        # 필수 컬럼 확인
        required_columns = ['원재료', '대체재료', '영양소종류']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"필수 컬럼 누락: {col}")
                return 0

        # 데이터 준비
        data_to_insert = []
        for idx, row in df.iterrows():
            original = str(row.get('원재료', '')).strip()
            alternative = str(row.get('대체재료', '')).strip()
            nutrient_type = str(row.get('영양소종류', '')).strip().lower()

            if not original or not alternative or not nutrient_type:
                continue

            data_to_insert.append((
                original,
                alternative,
                nutrient_type,
                float(row.get('감소비율', 0) or 0),
                str(row.get('비고', '')) or None
            ))

        # 배치 INSERT
        insert_query = '''
            INSERT INTO alternatives (original_food, alternative_food, nutrient_type, reduction_percentage, notes)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        '''

        with conn.cursor() as cursor:
            execute_batch(cursor, insert_query, data_to_insert, page_size=100)
            conn.commit()

        logger.info(f"대체재료 데이터 {len(data_to_insert)}개 로드 완료")
        return len(data_to_insert)

    except Exception as e:
        logger.error(f"대체재료 데이터 로드 실패: {e}")
        conn.rollback()
        return 0


def main():
    """메인 실행 함수"""
    logger.info("=" * 60)
    logger.info("엑셀 데이터 → PostgreSQL 로딩 시작")
    logger.info("=" * 60)

    # DB 연결
    conn = get_db_connection()

    try:
        # 엑셀 파일 경로 (프로젝트 루트 기준)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 국가표준식품성분표 파일 사용
        foods_excel = os.path.join(base_dir, 'Documents', 'Data', '국가표준식품성분표_250426공개.xlsx')
        alternatives_excel = os.path.join(base_dir, 'Documents', 'Data', 'alternatives.xlsx')

        # 식품 데이터 로드 (국가표준식품성분표)
        logger.info("\n[1/2] 식품 영양 정보 로드 중...")
        logger.info(f"파일: {foods_excel}")
        foods_count = load_foods_from_excel(conn, foods_excel)

        # 대체 재료 데이터 로드
        logger.info("\n[2/2] 대체 재료 매핑 로드 중...")
        logger.info(f"파일: {alternatives_excel}")
        alternatives_count = load_alternatives_from_excel(conn, alternatives_excel)

        # 결과 출력
        logger.info("\n" + "=" * 60)
        logger.info("데이터 로딩 완료!")
        logger.info(f"  - 식품: {foods_count}개 (국가표준식품성분표)")
        logger.info(f"  - 대체재료: {alternatives_count}개")
        logger.info("=" * 60)

    finally:
        conn.close()
        logger.info("DB 연결 종료")


if __name__ == "__main__":
    main()
