"""
통합 퀴즈 체인 - PM 요구사항 충족
파일 위치: src/chains/integrated_quiz.py

특징:
1. 대화 기반 자동 주제 추출
2. 답변 후 자동 퀴즈 제안
3. 3개 고정 문제 생성
4. 퓨샷 러닝 적용
"""

import logging
import re
from typing import Optional, List, Dict
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from .common import get_llm, get_context_for_quiz

logger = logging.getLogger(__name__)

# 리트리버 타입 힌트
try:
    from src.rag.retriever import DocumentRetriever
    RetrieverType = DocumentRetriever
except ImportError:
    RetrieverType = any  # 타입 힌트만 제공

# 만성신부전 환자 영양 가이드라인
CKD_NUTRITION_GUIDELINES = """만성신부전 환자의 영양 관리는 질환 단계(투석 전·중·이식 후)에 따라 달라지며, 다음의 6가지 조건을 중심으로 조정해야 합니다.
1. 조건 1은 **단백질 섭취**로, 투석 전에는 체중 1kg당 0.6~0.8g 수준의 저단백 식이를 유지해야 합니다. 투석 중에는 단백질 손실이 많아 체중 1kg당 1.2~1.3g의 고단백 식이가 필요하며, 이식 후에는 0.8~1.0g 정도로 조절해 과잉 섭취를 방지합니다.
2. 조건 2는 **나트륨(소금)** 섭취 제한이다. 투석 전에는 하루 5g 미만, 투석 중과 이식 후에는 하루 6g 미만으로 유지하며, 이는 고혈압과 부종을 예방하기 위한 조치입니다.
3. 조건 3은 **칼륨 섭취** 관리이다. 투석 전에는 하루 2000mg 미만을 권장하며, 투석 중에도 동일하게 유지하되 혈중 칼륨 농도에 따라 조정합니다. 이식 후에는 신기능이 회복되면 다소 완화할 수 있으나, 고칼륨혈증 위험이 있는 경우 주의가 필요합니다.
4. 조건 4는 **인(Phosphorus)** 섭취 조절이다. 투석 전에는 하루 800mg 미만, 투석 중에는 1000mg 미만, 이식 후에는 1200mg 미만으로 제한하며, 이는 뼈와 혈관의 석회화를 방지하기 위합입니다.
5. 조건 5은 **에너지 섭취량**이다. 투석 전과 투석 중에는 체중 1kg당 30~35kcal, 이식 후에는 30kcal 정도를 유지하며, 이는 체중을 안정적으로 유지하기 위한 목적입니다.
6. 조건 6는 각 영양소 섭취량을 기준으로 권장량의 0~80%는 안전 구간(녹색), 80~100%는 주의 구간(노란색), 100% 초과는 위험 구간(빨간색)으로 구분하여 식단의 안전성과 과잉 섭취를 판단하는 기준이다."""

# 퓨샷 러닝 예시 (3개 문제 유형 - PM 요구사항)
FEW_SHOT_EXAMPLES = """
## 문제 출제 예시 (다음 형식을 참고하여 정확히 3개 문제를 만드세요)

### 예시 1: 객관식
**문제 1 (객관식)**
[혈액투석 환자의 1일 단백질 권장 섭취량은?]
1) 0.6-0.8 g/kg/일
2) 1.0 g/kg/일
3) 1.2 g/kg/일
4) 1.5 g/kg/일

정답: 3
해설: 혈액투석 시 6-8 g/회의 아미노산이 손실되므로, 투석 환자는 1.2 g/kg IBW/일의 단백질 섭취가 권장됩니다.

---

### 예시 2: OX 퀴즈
**문제 2 (OX퀴즈)**
[혈액투석 환자는 매 식사마다 단백질 식품을 섭취하는 것보다 한 끼에 몰아서 섭취하는 것이 더 효과적이다. (O/X)]

정답: X
해설: 과량의 단백질 섭취는 요독증을 야기할 수 있으므로, 허용된 양을 매끼 나누어 섭취하는 것이 효과적입니다.

---

### 예시 3: 주관식
**문제 3 (주관식)**
[투석 간 이상적인 체중 증가는 건체중의 ___% 이내로 유지해야 한다.]

정답: 4.0-4.5%
해설: 투석 간 체중 증가가 많을 경우 심혈관 질환 발생률이 높아지므로 건체중의 4.0-4.5% 이내로 관리해야 합니다.
"""


class IntegratedQuizChain:
    """
    PM 요구사항에 맞춘 통합 퀴즈 체인
    
    기능:
    1. 대화 히스토리에서 주제 자동 추출
    2. 답변 후 자동 퀴즈 제안
    3. 3개 문제 고정 생성
    4. 퓨샷 러닝 적용
    """
    
    def __init__(
        self,
        retriever,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
    ):
        """
        Args:
            retriever: RAG 리트리버
            model: 사용할 모델명
            temperature: 응답의 창의성
        """
        self.retriever = retriever
        self.llm = get_llm(model=model, temperature=temperature)
        self.quiz_suggestion_text = "\n\n💡 **이 주제로 퀴즈를 맞춰보시겠어요?**"
        
        # 퀴즈 생성 프롬프트
        self.quiz_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""당신은 혈액투석 환자 식단 교육을 위한 문제 출제 전문가입니다.
식약처 자료를 바탕으로 학습 효과를 높이는 문제를 출제해주세요.

참고 자료:
{{context}}

{FEW_SHOT_EXAMPLES}

위 예시들을 참고하여, 다음 형식으로 **정확히 3개**의 문제를 출제해주세요:

**문제 1 (문제유형)**
[문제 내용]
1) 선택지 1 (객관식인 경우)
2) 선택지 2
3) 선택지 3
4) 선택지 4

정답: [정답]
해설: [상세한 해설]

---

**문제 2 (문제유형)**
[문제 내용]
...

---

**문제 3 (문제유형)**
[문제 내용]
...

⚠️ 중요:
- 반드시 3개의 문제만 출제하세요
- 객관식, OX퀴즈, 주관식 등 다양한 유형을 섞어주세요
- 각 문제는 "---"로 구분하세요
- 해설은 구체적이고 교육적으로 작성하세요

{CKD_NUTRITION_GUIDELINES}"""),
            ("user", "주제: {topic}\n\n위 주제에 대해 3개의 문제를 출제해주세요.")
        ])
        
        logger.info(f"통합 퀴즈 체인 초기화 완료 (model={model})")
    
    def extract_topic_from_conversation(
        self,
        messages: List[Dict[str, str]],
        last_n: int = 3
    ) -> str:
        """
        대화 히스토리에서 주제 추출
        
        Args:
            messages: 대화 메시지 리스트 [{"role": "user/assistant", "content": "..."}]
            last_n: 최근 n개 메시지만 분석
            
        Returns:
            추출된 주제
        """
        if not messages:
            return "혈액투석 환자 식단 관리"
        
        # 최근 메시지 가져오기
        recent_messages = messages[-last_n:] if len(messages) > last_n else messages
        
        # 키워드 추출을 위한 정규식 패턴
        food_pattern = r'(김치찌개|불고기|된장찌개|비빔밥|삼계탕|갈비찜|[가-힣]+찌개|[가-힣]+탕|[가-힣]+구이)'
        nutrient_pattern = r'(칼륨|나트륨|인|단백질|저염|저칼륨|저인)'
        topic_pattern = r'(조리법|레시피|대체|관리|섭취|식단|영양)'
        
        extracted_keywords = []
        
        for msg in recent_messages:
            content = msg.get("content", "")
            
            # 요리명 추출
            foods = re.findall(food_pattern, content)
            extracted_keywords.extend(foods)
            
            # 영양소 키워드 추출
            nutrients = re.findall(nutrient_pattern, content)
            extracted_keywords.extend(nutrients)
            
            # 주제 키워드 추출
            topics = re.findall(topic_pattern, content)
            extracted_keywords.extend(topics)
        
        if extracted_keywords:
            # 가장 빈도 높은 키워드 조합
            unique_keywords = list(set(extracted_keywords))[:3]
            topic = " ".join(unique_keywords)
            logger.info(f"추출된 주제: {topic}")
            return topic
        
        # 기본값
        return "혈액투석 환자 식단 관리"
    
    def add_quiz_suggestion(self, response_text: str) -> str:
        """
        LLM 답변 끝에 퀴즈 제안 추가
        
        Args:
            response_text: 원본 답변
            
        Returns:
            퀴즈 제안이 추가된 답변
        """
        return response_text + self.quiz_suggestion_text
    
    def generate_quiz(
        self,
        topic: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        퀴즈 생성 (3개 고정)
        
        Args:
            topic: 명시적 주제 (없으면 대화에서 추출)
            conversation_history: 대화 히스토리
            
        Returns:
            생성된 퀴즈 텍스트
        """
        # 주제 결정
        if topic is None and conversation_history:
            topic = self.extract_topic_from_conversation(conversation_history)
        elif topic is None:
            topic = "혈액투석 환자 식단 관리"
        
        logger.info(f"❓ 퀴즈 생성 시작 (주제: {topic})")
        
        # RAG 컨텍스트 검색
        context = get_context_for_quiz(self.retriever, topic)
        
        # 퀴즈 생성
        quiz_chain = self.quiz_prompt | self.llm | StrOutputParser()
        result = quiz_chain.invoke({
            "topic": topic,
            "context": context
        })
        
        logger.info("✅ 퀴즈 생성 완료 (3개)")
        return result
    
    def parse_quiz(self, quiz_text: str) -> List[Dict]:
        """
        생성된 퀴즈를 구조화된 데이터로 파싱
        
        Args:
            quiz_text: 생성된 퀴즈 텍스트
            
        Returns:
            파싱된 퀴즈 리스트
        """
        questions = []
        parts = quiz_text.split("---")
        
        for i, part in enumerate(parts, 1):
            if not part.strip():
                continue
            
            # 정답 추출
            answer = ""
            if "정답:" in part:
                answer_line = part.split("정답:")[1].split("\n")[0].strip()
                answer = answer_line
            
            # 해설 추출
            explanation = ""
            if "해설:" in part:
                explanation = part.split("해설:")[1].split("---")[0].strip()
            
            # 문제 유형 추출
            question_type = "기타"
            type_match = re.search(r'\((.+?)\)', part)
            if type_match:
                question_type = type_match.group(1)
            
            questions.append({
                "id": i,
                "type": question_type,
                "content": part.strip(),
                "answer": answer,
                "explanation": explanation
            })
        
        return questions


# 편의 함수
def create_integrated_quiz_chain(
    retriever,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
):
    """
    통합 퀴즈 체인 생성 (팩토리 함수)
    
    Args:
        retriever: RAG 리트리버
        model: 사용할 모델명
        temperature: 응답의 창의성
        
    Returns:
        IntegratedQuizChain 인스턴스
    """
    return IntegratedQuizChain(
        retriever=retriever,
        model=model,
        temperature=temperature
    )


# 스트림릿 통합을 위한 헬퍼 함수
def integrate_with_chatbot(
    quiz_chain: IntegratedQuizChain,
    response_text: str,
    conversation_history: List[Dict[str, str]],
    auto_suggest: bool = True
) -> Dict[str, any]:
    """
    챗봇 응답에 퀴즈 기능 통합
    
    Args:
        quiz_chain: 퀴즈 체인 인스턴스
        response_text: LLM 원본 응답
        conversation_history: 대화 히스토리
        auto_suggest: 자동으로 퀴즈 제안 추가 여부
        
    Returns:
        {
            "response": 퀴즈 제안이 포함된 응답,
            "topic": 추출된 주제,
            "quiz_available": True
        }
    """
    # 주제 추출
    topic = quiz_chain.extract_topic_from_conversation(conversation_history)
    
    # 응답에 퀴즈 제안 추가
    if auto_suggest:
        final_response = quiz_chain.add_quiz_suggestion(response_text)
    else:
        final_response = response_text
    
    return {
        "response": final_response,
        "topic": topic,
        "quiz_available": True
    }
