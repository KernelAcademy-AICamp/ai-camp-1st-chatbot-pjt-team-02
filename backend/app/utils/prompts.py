"""
프롬프트 관리 유틸리티
"""

# 추가 프롬프트 템플릿을 여기에 정의할 수 있습니다.
# 현재는 config.py에 정의되어 있습니다.

def get_recipe_modification_prompt(food_name: str, dangerous_nutrients: list) -> str:
    """
    레시피 수정 프롬프트 생성

    Args:
        food_name: 음식명
        dangerous_nutrients: 위험 영양소 리스트

    Returns:
        프롬프트 텍스트
    """
    nutrients_text = ", ".join(dangerous_nutrients)

    return f"""
{food_name}의 {nutrients_text}을(를) 줄이기 위한 레시피 수정 방법을 알려주세요.

다음 항목을 포함해서 답변해주세요:
1. 대체 가능한 재료
2. 조리법 변경 방법
3. 영양소 감소 예상 효과
"""


def get_alternative_food_prompt(ingredient: str, nutrient_type: str) -> str:
    """
    대체 식품 추천 프롬프트 생성

    Args:
        ingredient: 재료명
        nutrient_type: 영양소 타입 (sodium, potassium, phosphorus, protein)

    Returns:
        프롬프트 텍스트
    """
    nutrient_names = {
        "sodium": "나트륨",
        "potassium": "칼륨",
        "phosphorus": "인",
        "protein": "단백질"
    }

    nutrient_kr = nutrient_names.get(nutrient_type, nutrient_type)

    return f"""
신장 투석 환자를 위해 '{ingredient}'를 대체할 수 있는 저{nutrient_kr} 식품을 추천해주세요.

다음 정보를 포함해주세요:
1. 대체 식품명
2. {nutrient_kr} 함량 비교
3. 맛과 식감 유사도
4. 조리 시 주의사항
"""
