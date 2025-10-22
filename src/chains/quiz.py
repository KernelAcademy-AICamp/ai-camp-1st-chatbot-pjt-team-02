"""문제 생성 체인 모듈"""

import logging
from typing import Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from .common import get_llm, get_context_for_quiz

logger = logging.getLogger(__name__)


def create_quiz_chain(
    retriever,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
):
    """
    문제 생성 체인 생성 (주관식/객관식 문제 3개 생성)

    Args:
        retriever: RAG 리트리버
        model: 사용할 모델명
        temperature: 응답의 창의성
        max_tokens: 최대 토큰 수

    Returns:
        문제 생성 체인
    """
    llm = get_llm(model=model, temperature=temperature, max_tokens=max_tokens)

    # 문제 생성 프롬프트
    quiz_prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 영양학 교육 문제 출제 전문가입니다.
식약처 자료를 바탕으로 학습 효과를 높이는 문제를 출제해주세요.

참고 자료:
{context}

다음 형식으로 정확히 3개의 문제를 출제해주세요:

**문제 1 (객관식)**
[문제 내용]
1) 선택지 1
2) 선택지 2
3) 선택지 3
4) 선택지 4

정답: [번호]
해설: [간단한 해설]

**문제 2 (객관식)**
[문제 내용]
1) 선택지 1
2) 선택지 2
3) 선택지 3
4) 선택지 4

정답: [번호]
해설: [간단한 해설]

**문제 3 (주관식)**
[문제 내용]

정답: [정답 내용]
해설: [간단한 해설]"""),
        ("user", "주제: {topic}\n\n위 주제에 대해 객관식 2문제, 주관식 1문제를 출제해주세요.")
    ])

    def get_quiz_context(inputs):
        """문제 생성을 위한 컨텍스트 검색"""
        topic = inputs["topic"]
        context = get_context_for_quiz(retriever, topic)
        return {**inputs, "context": context}

    # 문제 생성 체인 구성
    quiz_chain = (
        get_quiz_context
        | quiz_prompt
        | llm
        | StrOutputParser()
    )

    def run_quiz(inputs):
        """문제 생성 프로세스 실행"""
        logger.info(f"❓ 문제 생성 체인 실행 중... (주제: {inputs['topic']})")
        result = quiz_chain.invoke(inputs)
        logger.info("✅ 문제 생성 체인 완료")
        return result

    logger.info(f"문제 생성 체인 생성 완료 (model={model}, temperature={temperature})")
    return run_quiz
