"""재료 파싱 도구"""

import logging
import json
from typing import List, Dict, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from src.chains.common import get_llm

logger = logging.getLogger(__name__)


def parse_ingredients_with_llm(
    ingredients_text: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3
) -> List[Dict]:
    """
    LLM을 사용하여 재료 텍스트를 구조화된 형태로 파싱

    Args:
        ingredients_text: 원시 재료 텍스트
        model: 사용할 LLM 모델
        temperature: LLM 온도 설정

    Returns:
        파싱된 재료 리스트 [{name, amount, unit}, ...]
    """
    try:
        logger.info("🔍 재료 파싱 시작...")

        llm = get_llm(model=model, temperature=temperature)

        # 파싱 프롬프트
        parse_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 요리 재료를 정확하게 파싱하는 전문가입니다.

주어진 재료 텍스트를 JSON 형식으로 구조화하세요.

출력 형식:
```json
[
    {{"name": "재료명", "amount": "수량", "unit": "단위"}},
    {{"name": "재료명", "amount": "수량", "unit": "단위"}}
]
```

규칙:
- name: 재료의 이름 (예: "돼지고기", "김치")
- amount: 수량 (예: "300", "1", "2")
- unit: 단위 (예: "g", "개", "큰술")
- 수량이 명시되지 않은 경우 amount는 "적당량", unit은 빈 문자열
- 정확한 JSON 형식만 반환하세요."""),
            ("user", "재료:\n{ingredients}\n\n위 재료를 JSON 형식으로 파싱하세요.")
        ])

        parse_chain = parse_prompt | llm | StrOutputParser()
        result = parse_chain.invoke({"ingredients": ingredients_text})

        # JSON 파싱 시도
        # 코드블록 제거
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()

        parsed = json.loads(result)

        # 유효성 검증
        if not isinstance(parsed, list):
            logger.warning("⚠️ 파싱 결과가 리스트가 아님")
            return fallback_parse(ingredients_text)

        # 각 항목 검증
        validated = []
        for item in parsed:
            if isinstance(item, dict) and "name" in item:
                validated.append({
                    "name": str(item.get("name", "")).strip(),
                    "amount": str(item.get("amount", "적당량")).strip(),
                    "unit": str(item.get("unit", "")).strip()
                })

        logger.info(f"✅ {len(validated)}개 재료 파싱 완료")
        return validated

    except json.JSONDecodeError as e:
        logger.warning(f"⚠️ JSON 파싱 실패: {e}")
        return fallback_parse(ingredients_text)

    except Exception as e:
        logger.error(f"❌ 재료 파싱 오류: {e}")
        return fallback_parse(ingredients_text)


def fallback_parse(ingredients_text: str) -> List[Dict]:
    """
    간단한 규칙 기반 파싱 (fallback)

    Args:
        ingredients_text: 원시 재료 텍스트

    Returns:
        파싱된 재료 리스트
    """
    logger.info("📝 Fallback 파싱 사용")

    parsed = []
    lines = ingredients_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 간단한 패턴 매칭
        # 예: "돼지고기 300g", "김치 200g", "두부 1모"
        parts = line.split()

        if len(parts) >= 2:
            # 마지막 부분이 단위를 포함한 수량인 경우
            last_part = parts[-1]
            if any(unit in last_part for unit in ["g", "kg", "ml", "L", "개", "모", "큰술", "작은술"]):
                # 수량과 단위 분리 시도
                import re
                match = re.match(r'(\d+)(\D+)', last_part)
                if match:
                    amount = match.group(1)
                    unit = match.group(2)
                    name = " ".join(parts[:-1])
                else:
                    amount = "적당량"
                    unit = ""
                    name = line
            else:
                # 수량과 재료명이 분리된 경우
                try:
                    amount = parts[-1]
                    float(amount)  # 숫자인지 확인
                    name = " ".join(parts[:-1])
                    unit = ""
                except ValueError:
                    name = line
                    amount = "적당량"
                    unit = ""
        else:
            name = line
            amount = "적당량"
            unit = ""

        # "-", "*" 등 불필요한 문자 제거
        name = name.lstrip("-*• ")

        if name:
            parsed.append({
                "name": name,
                "amount": amount,
                "unit": unit
            })

    logger.info(f"✅ Fallback 파싱: {len(parsed)}개 재료")
    return parsed


def extract_main_ingredients(ingredients: List[Dict]) -> List[str]:
    """
    주요 재료명만 추출

    Args:
        ingredients: 파싱된 재료 리스트

    Returns:
        재료명 리스트
    """
    return [ing.get("name", "") for ing in ingredients if ing.get("name")]


if __name__ == "__main__":
    # 테스트
    test_text = """
    돼지고기 300g
    김치 200g
    두부 1모
    양파 1개
    대파 2대
    고춧가루 1큰술
    간장 2큰술
    """

    result = parse_ingredients_with_llm(test_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))