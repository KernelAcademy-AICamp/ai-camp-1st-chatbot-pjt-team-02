"""요약 체인 모듈"""

import logging
from typing import Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from .common import get_llm, get_context_for_summary

logger = logging.getLogger(__name__)

CKD_NUTRITION_GUIDELINES = """만성신부전 환자의 영양 관리는 질환 단계(투석 전·중·이식 후)에 따라 달라지며, 다음의 6가지 조건을 중심으로 조정해야 합니다.
1. 조건 1은 **단백질 섭취**로, 투석 전에는 체중 1kg당 0.6~0.8g 수준의 저단백 식이를 유지해야 합니다. 투석 중에는 단백질 손실이 많아 체중 1kg당 1.2~1.3g의 고단백 식이가 필요하며, 이식 후에는 0.8~1.0g 정도로 조절해 과잉 섭취를 방지합니다.
2. 조건 2는 **나트륨(소금)** 섭취 제한이다. 투석 전에는 하루 5g 미만, 투석 중과 이식 후에는 하루 6g 미만으로 유지하며, 이는 고혈압과 부종을 예방하기 위한 조치입니다.
3. 조건 3은 **칼륨 섭취** 관리이다. 투석 전에는 하루 2000mg 미만을 권장하며, 투석 중에도 동일하게 유지하되 혈중 칼륨 농도에 따라 조정합니다. 이식 후에는 신기능이 회복되면 다소 완화할 수 있으나, 고칼륨혈증 위험이 있는 경우 주의가 필요합니다.
4. 조건 4는 **인(Phosphorus)** 섭취 조절이다. 투석 전에는 하루 800mg 미만, 투석 중에는 1000mg 미만, 이식 후에는 1200mg 미만으로 제한하며, 이는 뼈와 혈관의 석회화를 방지하기 위합입니다.
5. 조건 5은 **에너지 섭취량**이다. 투석 전과 투석 중에는 체중 1kg당 30~35kcal, 이식 후에는 30kcal 정도를 유지하며, 이는 체중을 안정적으로 유지하기 위한 목접입니다.
6. 조건 6는 각 영양소 섭취량을 기준으로 권장량의 0~80%는 안전 구간(녹색), 80~100%는 주의 구간(노란색), 100% 초과는 위험 구간(빨간색)으로 구분하여 식단의 안전성과 과잉 섭취를 판단하는 기준이다."""


def create_summary_chain(
    retriever,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
):
    """
    요약 체인 생성 (조리법 및 주의사항 요약, Q&A 생성)

    Args:
        retriever: RAG 리트리버
        model: 사용할 모델명
        temperature: 응답의 창의성
        max_tokens: 최대 토큰 수

    Returns:
        요약 체인
    """
    llm = get_llm(model=model, temperature=temperature, max_tokens=max_tokens)

    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", f"""당신은 신장 질환 환자를 위한 영양 교육 전문가입니다.
식약처 자료를 바탕으로 조리법과 주의사항을 요약하고, 이해를 돕는 Q&A를 생성해주세요.

참고 자료:
{{context}}

다음 형식으로 답변해주세요:
## 조리법 요약
(핵심 조리법 2-3가지)

## 주의사항
(반드시 지켜야 할 주의사항 2-3가지)

## Q&A
(자주 묻는 질문과 답변 2-3개)

{CKD_NUTRITION_GUIDELINES}"""),
        ("user", "주제: {topic}\n\n위 주제에 대해 조리법, 주의사항, Q&A를 생성해주세요.")
    ])

    def get_summary_context(inputs):
        """요약을 위한 컨텍스트 검색"""
        topic = inputs["topic"]
        context = get_context_for_summary(retriever, topic)
        return {**inputs, "context": context}

    # 요약 체인 구성
    summary_chain = (
        get_summary_context
        | summary_prompt
        | llm
        | StrOutputParser()
    )

    def run_summary(inputs):
        """요약 프로세스 실행"""
        logger.info(f"📝 요약 체인 실행 중... (주제: {inputs['topic']})")
        result = summary_chain.invoke(inputs)
        logger.info("✅ 요약 체인 완료")
        return result

    logger.info(f"요약 체인 생성 완료 (model={model}, temperature={temperature})")
    return run_summary
