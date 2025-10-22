"""영양 계산 및 평가 도구"""

import logging
import json
from typing import List, Dict, Optional, Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from src.chains.common import get_llm

logger = logging.getLogger(__name__)


def evaluate_nutrition_with_llm(
    ingredients: List[Dict],
    model: str = "gpt-4o-mini",
    temperature: float = 0.3
) -> Dict:
    """
    LLM을 사용하여 재료의 영양 정보를 평가

    Args:
        ingredients: 파싱된 재료 리스트
        model: 사용할 LLM 모델
        temperature: LLM 온도 설정

    Returns:
        영양 평가 결과
    """
    try:
        logger.info("📊 영양 평가 시작...")

        if not ingredients:
            logger.warning("⚠️ 평가할 재료가 없음")
            return {}

        llm = get_llm(model=model, temperature=temperature)

        # 영양 평가 프롬프트
        evaluation_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 신장질환 환자를 위한 영양 전문가입니다.

주어진 재료들의 칼륨, 나트륨, 인 함량을 평가하세요.

출력 형식 (JSON):
```json
{{
    "summary": "전체 평가 요약",
    "total_risk_level": "low|medium|high",
    "ingredients": [
        {{
            "name": "재료명",
            "potassium_level": "low|medium|high",
            "sodium_level": "low|medium|high",
            "phosphorus_level": "low|medium|high",
            "risk_score": 1-10,
            "note": "특별 주의사항"
        }}
    ],
    "recommendations": ["추천사항1", "추천사항2"]
}}
```

평가 기준:
- high: 신장질환 환자에게 주의 필요
- medium: 적당량 섭취 가능
- low: 안전하게 섭취 가능

정확한 JSON만 반환하세요."""),
            ("user", """다음 재료들을 평가해주세요:

{ingredients_text}

신장질환 환자 관점에서 영양 평가를 JSON 형식으로 제공하세요.""")
        ])

        # 재료 텍스트 준비
        ingredients_text = "\n".join([
            f"- {ing.get('name', '')} {ing.get('amount', '')} {ing.get('unit', '')}"
            for ing in ingredients
        ])

        evaluation_chain = evaluation_prompt | llm | StrOutputParser()
        result = evaluation_chain.invoke({"ingredients_text": ingredients_text})

        # JSON 파싱
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()

        evaluation = json.loads(result)
        logger.info(f"✅ 영양 평가 완료: {evaluation.get('total_risk_level', 'unknown')}")

        return evaluation

    except json.JSONDecodeError as e:
        logger.warning(f"⚠️ JSON 파싱 실패: {e}")
        return fallback_evaluate(ingredients)

    except Exception as e:
        logger.error(f"❌ 영양 평가 오류: {e}")
        return fallback_evaluate(ingredients)


def fallback_evaluate(ingredients: List[Dict]) -> Dict:
    """
    간단한 규칙 기반 영양 평가 (fallback)

    Args:
        ingredients: 파싱된 재료 리스트

    Returns:
        영양 평가 결과
    """
    logger.info("📝 Fallback 영양 평가 사용")

    # 고위험 재료 목록
    high_risk_ingredients = {
        "김치": {"potassium": "high", "sodium": "high", "phosphorus": "medium"},
        "돼지고기": {"potassium": "medium", "sodium": "medium", "phosphorus": "high"},
        "소고기": {"potassium": "medium", "sodium": "medium", "phosphorus": "high"},
        "감자": {"potassium": "high", "sodium": "low", "phosphorus": "medium"},
        "토마토": {"potassium": "high", "sodium": "low", "phosphorus": "low"},
        "바나나": {"potassium": "high", "sodium": "low", "phosphorus": "low"},
        "시금치": {"potassium": "high", "sodium": "low", "phosphorus": "medium"},
        "우유": {"potassium": "medium", "sodium": "medium", "phosphorus": "high"},
        "치즈": {"potassium": "low", "sodium": "high", "phosphorus": "high"},
        "된장": {"potassium": "medium", "sodium": "high", "phosphorus": "medium"},
        "간장": {"potassium": "low", "sodium": "high", "phosphorus": "low"},
    }

    evaluated_ingredients = []
    total_risk_score = 0
    high_risk_count = 0

    for ing in ingredients:
        name = ing.get("name", "")

        # 기본값
        evaluation = {
            "name": name,
            "potassium_level": "medium",
            "sodium_level": "medium",
            "phosphorus_level": "medium",
            "risk_score": 5,
            "note": ""
        }

        # 알려진 재료인지 확인
        for known_name, levels in high_risk_ingredients.items():
            if known_name in name:
                evaluation["potassium_level"] = levels["potassium"]
                evaluation["sodium_level"] = levels["sodium"]
                evaluation["phosphorus_level"] = levels["phosphorus"]

                # 위험 점수 계산
                risk_score = 0
                if levels["potassium"] == "high":
                    risk_score += 3
                elif levels["potassium"] == "medium":
                    risk_score += 2
                else:
                    risk_score += 1

                if levels["sodium"] == "high":
                    risk_score += 3
                elif levels["sodium"] == "medium":
                    risk_score += 2
                else:
                    risk_score += 1

                if levels["phosphorus"] == "high":
                    risk_score += 3
                elif levels["phosphorus"] == "medium":
                    risk_score += 2
                else:
                    risk_score += 1

                evaluation["risk_score"] = min(risk_score, 10)

                if risk_score >= 7:
                    evaluation["note"] = "신장질환 환자는 주의 필요"
                    high_risk_count += 1

                break

        evaluated_ingredients.append(evaluation)
        total_risk_score += evaluation["risk_score"]

    # 전체 위험도 평가
    avg_risk = total_risk_score / max(len(ingredients), 1)
    if avg_risk >= 7 or high_risk_count >= len(ingredients) * 0.5:
        total_risk_level = "high"
    elif avg_risk >= 4:
        total_risk_level = "medium"
    else:
        total_risk_level = "low"

    recommendations = []
    if total_risk_level == "high":
        recommendations.append("고칼륨, 고나트륨 재료가 많아 대체재 사용을 권장합니다")
    if high_risk_count > 0:
        recommendations.append("일부 재료는 신장질환 환자에게 부담이 될 수 있습니다")

    return {
        "summary": f"총 {len(ingredients)}개 재료 중 {high_risk_count}개가 고위험군입니다",
        "total_risk_level": total_risk_level,
        "ingredients": evaluated_ingredients,
        "recommendations": recommendations
    }


def calculate_total_nutrition(ingredients: List[Dict], nutrition_db: Optional[Dict] = None) -> Dict:
    """
    재료들의 총 영양소 계산

    Args:
        ingredients: 파싱된 재료 리스트
        nutrition_db: 영양 데이터베이스 (선택)

    Returns:
        총 영양소 정보
    """
    try:
        logger.info("🧮 총 영양소 계산 중...")

        total = {
            "calories": 0,
            "potassium": 0,
            "sodium": 0,
            "phosphorus": 0,
            "protein": 0,
            "fat": 0,
            "carbs": 0
        }

        # 간단한 예시 데이터 (실제로는 DB나 API에서 가져와야 함)
        if nutrition_db is None:
            nutrition_db = {
                "돼지고기": {"calories": 242, "potassium": 423, "sodium": 62, "phosphorus": 200},
                "김치": {"calories": 15, "potassium": 150, "sodium": 500, "phosphorus": 30},
                "두부": {"calories": 76, "potassium": 121, "sodium": 7, "phosphorus": 92},
                # ... 더 많은 데이터
            }

        for ing in ingredients:
            name = ing.get("name", "")
            amount = ing.get("amount", "100")

            # 숫자만 추출
            try:
                amount_value = float(''.join(filter(str.isdigit, str(amount))))
            except:
                amount_value = 100  # 기본값

            # 영양 정보 찾기
            for food_name, nutrition in nutrition_db.items():
                if food_name in name:
                    # 100g 기준으로 비례 계산
                    ratio = amount_value / 100
                    for nutrient, value in nutrition.items():
                        if nutrient in total:
                            total[nutrient] += value * ratio
                    break

        # 소수점 정리
        for key in total:
            total[key] = round(total[key], 1)

        logger.info(f"✅ 영양소 계산 완료: {total['calories']} kcal")
        return total

    except Exception as e:
        logger.error(f"❌ 영양소 계산 오류: {e}")
        return {
            "calories": 0,
            "potassium": 0,
            "sodium": 0,
            "phosphorus": 0,
            "error": str(e)
        }


if __name__ == "__main__":
    # 테스트
    test_ingredients = [
        {"name": "돼지고기", "amount": "300", "unit": "g"},
        {"name": "김치", "amount": "200", "unit": "g"},
        {"name": "두부", "amount": "1", "unit": "모"}
    ]

    result = evaluate_nutrition_with_llm(test_ingredients)
    print(json.dumps(result, ensure_ascii=False, indent=2))