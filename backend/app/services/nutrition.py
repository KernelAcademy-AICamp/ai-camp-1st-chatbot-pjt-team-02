"""
영양 분석 서비스
"""

from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
import logging

from app.models.database import Food, Alternative
from app.config import settings

logger = logging.getLogger(__name__)


class NutritionService:
    """영양 분석 서비스 클래스"""

    def __init__(self, db: Session):
        self.db = db
        self.limits = {
            "sodium": settings.SODIUM_LIMIT,
            "potassium": settings.POTASSIUM_LIMIT,
            "phosphorus": settings.PHOSPHORUS_LIMIT,
            "protein": settings.PROTEIN_LIMIT
        }

    def search_food(self, food_name: str) -> Dict:
        """
        식품 영양 정보 검색

        Args:
            food_name: 식품명

        Returns:
            영양 정보 딕셔너리 (없으면 None)
        """
        try:
            # 정확한 매칭 시도
            food = self.db.query(Food).filter(
                Food.name.ilike(food_name)
            ).first()

            # 부분 매칭 시도
            if not food:
                food = self.db.query(Food).filter(
                    Food.name.ilike(f"%{food_name}%")
                ).first()

            if food:
                return {
                    "id": food.id,
                    "name": food.name,
                    "sodium": food.sodium or 0,
                    "potassium": food.potassium or 0,
                    "phosphorus": food.phosphorus or 0,
                    "protein": food.protein or 0,
                    "calories": food.calories or 0,
                    "category": food.category
                }

            return None

        except Exception as e:
            logger.error(f"식품 검색 실패: {food_name} - {str(e)}")
            return None

    def calculate_nutrition(self, ingredients: List[str]) -> Dict:
        """
        재료 리스트의 총 영양소 계산

        Args:
            ingredients: 재료 리스트

        Returns:
            총 영양 정보 딕셔너리
        """
        total = {
            "sodium": 0.0,
            "potassium": 0.0,
            "phosphorus": 0.0,
            "protein": 0.0,
            "calories": 0.0,
            "found_ingredients": [],
            "missing_ingredients": []
        }

        for ingredient in ingredients:
            food_info = self.search_food(ingredient)

            if food_info:
                total["sodium"] += food_info.get("sodium", 0)
                total["potassium"] += food_info.get("potassium", 0)
                total["phosphorus"] += food_info.get("phosphorus", 0)
                total["protein"] += food_info.get("protein", 0)
                total["calories"] += food_info.get("calories", 0)
                total["found_ingredients"].append(ingredient)
            else:
                total["missing_ingredients"].append(ingredient)
                logger.warning(f"식품 정보 없음: {ingredient}")

        # 반올림
        for key in ["sodium", "potassium", "phosphorus", "protein", "calories"]:
            total[key] = round(total[key], 2)

        logger.info(f"영양 계산 완료: {len(total['found_ingredients'])}개 찾음, {len(total['missing_ingredients'])}개 없음")

        return total

    def assess_risk_level(self, nutrition: Dict, custom_limits: Dict = None) -> Tuple[str, List[str]]:
        """
        위험도 평가

        Args:
            nutrition: 영양 정보 딕셔너리
            custom_limits: 커스텀 제한치 (None이면 기본값 사용)

        Returns:
            (위험도, 경고 메시지 리스트) 튜플
        """
        limits = custom_limits or self.limits
        risk_level = "low"
        warnings = []

        nutrient_names = {
            "sodium": "나트륨",
            "potassium": "칼륨",
            "phosphorus": "인",
            "protein": "단백질"
        }

        for nutrient, value in nutrition.items():
            if nutrient in limits:
                limit = limits[nutrient]

                if value > limit:
                    risk_level = "high"
                    warnings.append(
                        f"⚠️ {nutrient_names[nutrient]}: {value}mg (제한 {limit}mg 초과)"
                    )
                elif value > limit * 0.8:
                    if risk_level == "low":
                        risk_level = "medium"
                    warnings.append(
                        f"⚡ {nutrient_names[nutrient]}: {value}mg (제한 {limit}mg 근접)"
                    )

        return risk_level, warnings

    def get_alternatives(self, ingredients: List[str], dangerous_nutrients: List[str]) -> List[Dict]:
        """
        대체 재료 추천

        Args:
            ingredients: 재료 리스트
            dangerous_nutrients: 위험 영양소 리스트

        Returns:
            대체 재료 정보 리스트
        """
        alternatives = []

        try:
            for ingredient in ingredients:
                for nutrient in dangerous_nutrients:
                    # 데이터베이스에서 대체 재료 검색
                    alt = self.db.query(Alternative).filter(
                        Alternative.original_food.ilike(f"%{ingredient}%"),
                        Alternative.nutrient_type == nutrient
                    ).first()

                    if alt:
                        alternatives.append({
                            "original": alt.original_food,
                            "alternative": alt.alternative_food,
                            "nutrient_type": nutrient,
                            "reduction": alt.reduction_percentage,
                            "notes": alt.notes
                        })

            logger.info(f"대체 재료 {len(alternatives)}개 찾음")

        except Exception as e:
            logger.error(f"대체 재료 검색 실패: {str(e)}")

        return alternatives

    def get_dangerous_nutrients(self, nutrition: Dict, custom_limits: Dict = None) -> List[str]:
        """
        위험 영양소 목록 추출

        Args:
            nutrition: 영양 정보 딕셔너리
            custom_limits: 커스텀 제한치

        Returns:
            위험 영양소 리스트
        """
        limits = custom_limits or self.limits
        dangerous = []

        for nutrient, value in nutrition.items():
            if nutrient in limits and value > limits[nutrient]:
                dangerous.append(nutrient)

        return dangerous
