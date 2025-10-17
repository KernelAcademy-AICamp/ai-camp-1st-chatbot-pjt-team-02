"""의도 분류 체인 모듈"""

import logging
from typing import Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from .common import get_llm

logger = logging.getLogger(__name__)


def create_intent_classifier(
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
):
    """
    사용자 의도 분류 체인 생성

    Args:
        model: 사용할 모델명
        temperature: 응답의 창의성 (의도분류는 낮을수록 좋음)
        max_tokens: 최대 토큰 수

    Returns:
        의도 분류 체인
    """
    llm = get_llm(model=model, temperature=temperature, max_tokens=max_tokens)

    intent_classification_prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 사용자 의도를 분류하는 전문가입니다.
사용자의 질문을 분석하여 다음 중 하나로 분류해주세요:

1. recommendation - 요리 재료 대체재 추천 요청
   예: "김치찌개 만들 때 뭘 대체할 수 있을까?", "불고기에서 저칼륨 재료 추천해줘"

2. summary - 조리법, 주의사항 요약 또는 정보 제공 요청
   예: "저염식 조리법 알려줘", "신장 질환자 식사 주의사항은?"

3. quiz - 문제 출제 요청
   예: "영양 관리 퀴즈 만들어줘", "문제 출제해줘"

반드시 'recommendation', 'summary', 'quiz' 중 하나만 답변하세요."""),
        ("user", "{query}")
    ])

    intent_classifier = intent_classification_prompt | llm | StrOutputParser()
    logger.info(f"의도 분류 체인 생성 완료 (model={model}, temperature={temperature})")

    return intent_classifier
