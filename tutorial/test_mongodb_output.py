#!/usr/bin/env python
"""MongoDB 출력 테스트 스크립트 - Jupyter 외부에서 실행"""

import os
import sys

# 프로젝트 루트 경로 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))

from src.utils.alternative_search import search_alternatives_from_mongodb, extract_ingredients_from_text

# 테스트용 재료 텍스트
test_text = """**재료 목록:**
1. 김치 | 문제 영양소: 나트륨: 800mg ⚠️, 칼륨: 500mg ⚠️ | 위험도: 빨간색
2. 돼지고기 | 문제 영양소: 인: 200mg ⚠️ | 위험도: 노란색
3. 두부 | 문제 영양소: 없음 | 위험도: 녹색
4. 양파 | 문제 영양소: 없음 | 위험도: 녹색
5. 대파 | 문제 영양소: 없음 | 위험도: 녹색
6. 마늘 | 문제 영양소: 없음 | 위험도: 녹색
7. 고춧가루 | 문제 영양소: 없음 | 위험도: 녹색"""

# 재료 추출
ingredients = extract_ingredients_from_text(test_text)
print("="*70)
print("📋 추출된 재료:", ingredients)
print("="*70)

# MongoDB 검색
print("\n🔍 MongoDB 대체재 검색 중...")
results = search_alternatives_from_mongodb(ingredients, max_per_ingredient=3)

print("\n" + "="*70)
print("📊 MongoDB 검색 결과:")
print("="*70)
print(results)
print("="*70)

# 결과를 파일로도 저장
output_file = os.path.join(project_root, 'tutorial', 'mongodb_results.txt')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("MongoDB 검색 결과\n")
    f.write("="*70 + "\n")
    f.write(results)
    f.write("\n" + "="*70 + "\n")

print(f"\n💾 결과가 {output_file}에도 저장되었습니다.")