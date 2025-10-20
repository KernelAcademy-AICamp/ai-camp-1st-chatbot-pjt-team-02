"""
LLM 서비스 - OpenAI API 연동
"""

import openai
import json
from typing import List, Dict, Optional
import logging

from app.config import settings, SYSTEM_PROMPT, FEW_SHOT_EXAMPLES

logger = logging.getLogger(__name__)

# OpenAI API 키 설정
openai.api_key = settings.OPENAI_API_KEY


class LLMService:
    """LLM 서비스 클래스"""

    def __init__(self):
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS

    def extract_ingredients(self, food_name: str) -> List[str]:
        """
        음식명에서 재료 추출

        Args:
            food_name: 음식명

        Returns:
            재료 리스트
        """
        try:
            prompt = f"""
다음 음식의 일반적인 재료를 쉼표(,)로 구분하여 나열해주세요.
재료명만 간단하게 작성하고, 설명은 생략하세요.

음식: {food_name}

예시:
- 떡볶이 -> 떡, 고추장, 어묵, 파
- 김치찌개 -> 김치, 돼지고기, 두부, 파

재료:
"""

            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 한국 음식 전문가입니다. 재료를 간단하게 나열해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            content = response.choices[0].message.content.strip()

            # 재료 파싱
            ingredients = [ing.strip() for ing in content.split(',')]
            ingredients = [ing for ing in ingredients if ing and len(ing) < 20]

            logger.info(f"재료 추출 완료: {food_name} -> {ingredients}")
            return ingredients[:10]  # 최대 10개

        except Exception as e:
            logger.error(f"재료 추출 실패: {str(e)}")
            # 기본 재료 반환
            return ["떡", "고추장", "어묵", "파"] if "떡볶이" in food_name else []

    def generate_final_answer(
        self,
        food_name: str,
        nutrition: Dict,
        alternatives_text: str,
        limits: Dict[str, int] = None
    ) -> str:
        """
        최종 답변 생성

        Args:
            food_name: 음식명
            nutrition: 영양 정보 딕셔너리
            alternatives_text: RAG에서 가져온 대체 방법 텍스트
            limits: 영양소 제한치 (None이면 기본값 사용)

        Returns:
            최종 답변 텍스트
        """
        try:
            # 제한치 설정
            if limits is None:
                limits = {
                    "sodium": settings.SODIUM_LIMIT,
                    "potassium": settings.POTASSIUM_LIMIT,
                    "phosphorus": settings.PHOSPHORUS_LIMIT,
                    "protein": settings.PROTEIN_LIMIT
                }

            # 위험도 판단 및 경고 메시지
            warnings = []
            risk_level = "low"

            for nutrient, value in nutrition.items():
                if nutrient in limits:
                    if value > limits[nutrient]:
                        risk_level = "high"
                        warnings.append(f"⚠️ {nutrient}: {value}mg (제한: {limits[nutrient]}mg 초과)")
                    elif value > limits[nutrient] * 0.8:
                        if risk_level == "low":
                            risk_level = "medium"
                        warnings.append(f"⚡ {nutrient}: {value}mg (제한: {limits[nutrient]}mg 근접)")

            # 시스템 프롬프트 포맷팅
            system_message = SYSTEM_PROMPT.format(
                sodium_limit=limits["sodium"],
                potassium_limit=limits["potassium"],
                phosphorus_limit=limits["phosphorus"],
                protein_limit=limits["protein"]
            )

            # 사용자 프롬프트
            user_message = f"""
음식: {food_name}

영양 분석 결과:
- 나트륨: {nutrition.get('sodium', 0)}mg
- 칼륨: {nutrition.get('potassium', 0)}mg
- 인: {nutrition.get('phosphorus', 0)}mg
- 단백질: {nutrition.get('protein', 0)}g
- 칼로리: {nutrition.get('calories', 0)}kcal

위험도: {risk_level}
경고사항: {', '.join(warnings) if warnings else '없음'}

대체 방법 참고 자료:
{alternatives_text}

위 정보를 바탕으로 신장 투석 환자에게 친절하고 실용적인 조언을 해주세요.
반드시 다음 형식으로 답변해주세요:
1. 영양 분석 결과 (이모지 활용)
2. 위험도 평가
3. 구체적인 대체 레시피 제안
4. 조리 팁
"""

            # Few-shot 메시지 구성
            messages = [
                {"role": "system", "content": system_message}
            ]

            # Few-shot 예시 추가
            for example in FEW_SHOT_EXAMPLES:
                messages.append({"role": "user", "content": example["input"]})
                messages.append({"role": "assistant", "content": example["output"]})

            # 실제 질문 추가
            messages.append({"role": "user", "content": user_message})

            # OpenAI API 호출
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            answer = response.choices[0].message.content
            logger.info(f"최종 답변 생성 완료: {food_name}")

            return answer

        except Exception as e:
            logger.error(f"최종 답변 생성 실패: {str(e)}")
            return f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"

    def generate_quiz(
        self,
        topic: str,
        difficulty: str = "medium",
        count: int = 3,
        question_type: Optional[str] = None
    ) -> List[Dict]:
        """
        퀴즈 생성

        Args:
            topic: 퀴즈 주제
            difficulty: 난이도 (easy/medium/hard)
            count: 문제 수
            question_type: 문제 유형 (None이면 랜덤)

        Returns:
            퀴즈 문제 리스트
        """
        try:
            type_instruction = ""
            if question_type == "multiple_choice":
                type_instruction = "모든 문제를 4지선다 객관식으로 만들어주세요."
            elif question_type == "short_answer":
                type_instruction = "모든 문제를 단답형으로 만들어주세요."
            elif question_type == "ox":
                type_instruction = "모든 문제를 O/X 문제로 만들어주세요."
            else:
                type_instruction = "객관식, 단답형, O/X 문제를 섞어서 만들어주세요."

            prompt = f"""
신장 투석 환자를 위한 식단 관리에 대한 퀴즈를 만들어주세요.

주제: {topic}
난이도: {difficulty}
문제 수: {count}
{type_instruction}

각 문제는 다음 형식의 JSON으로 작성해주세요:
{{
    "question": "문제 내용",
    "options": ["선택지1", "선택지2", "선택지3", "선택지4"],  // 객관식인 경우만
    "correct_answer": "정답",
    "explanation": "해설",
    "question_type": "multiple_choice|short_answer|ox"
}}

문제는 실용적이고 환자에게 도움이 되는 내용으로 작성해주세요.
JSON 배열 형식으로만 답변해주세요.
"""

            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 신장 투석 환자를 위한 영양 교육 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )

            content = response.choices[0].message.content.strip()

            # JSON 파싱
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()

            questions = json.loads(content)

            logger.info(f"퀴즈 생성 완료: {topic}, {len(questions)}문제")
            return questions

        except Exception as e:
            logger.error(f"퀴즈 생성 실패: {str(e)}")
            # 기본 퀴즈 반환
            return [{
                "question": f"{topic}에 대한 퀴즈를 생성하지 못했습니다.",
                "correct_answer": "오류",
                "explanation": str(e),
                "question_type": "short_answer"
            }]


# 싱글톤 인스턴스
llm_service = LLMService()
