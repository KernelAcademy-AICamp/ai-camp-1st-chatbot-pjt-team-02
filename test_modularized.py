"""모듈화된 코드 테스트 스크립트"""

import os
import logging
from dotenv import load_dotenv
from src.rag.rag_setup import RAGSetup
from src.workflow import create_workflow_app

# Logger 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경변수 로드
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found. Please set it in .env file")

logger.info("✅ 환경 설정 완료")

# RAG 설정 초기화
logger.info("RAG 시스템 초기화 중...")
rag_setup = RAGSetup(
    pdf_directory="./data/pdf",
    vectorstore_path="./data/vectorstore",
    chunk_size=300,
    chunk_overlap=30
)

# 벡터스토어 생성 또는 로드
vectorstore = rag_setup.setup_rag(force_rebuild=False)
logger.info("✅ RAG 시스템 초기화 완료")

# 워크플로우 생성
logger.info("\n워크플로우 생성 중...")
app = create_workflow_app(
    vectorstore,
    llm_config={
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": None,
    }
)

logger.info("\n" + "="*70)
logger.info("테스트 시작 - query만 입력")
logger.info("="*70)

# 테스트 쿼리들
test_queries = [
    "김치찌개 만들 때 저칼륨 재료로 대체할 수 있는 게 뭐야?",  # 단순 추천만
    "된장찌개 만드는 법을 저칼륨으로 어떻게 해야 하고 주의할 점은?",  # 조리법 + 주의사항 필요 → summary 추가
    "혈액투석 환자의 식사 관리 주의사항 요약해줘",  # summary 의도
    "저염식에 대한 퀴즈 3개 만들어줘",  # quiz 의도
]

for i, query in enumerate(test_queries, 1):
    logger.info(f"\n{'='*70}")
    logger.info(f"테스트 {i}: {query}")
    logger.info("="*70)

    # 워크플로우 실행 - query만 입력
    result = app.invoke({"query": query})

    logger.info("\n" + "-"*70)
    logger.info("결과:")
    logger.info("-"*70)
    print(result["final_result"])
    logger.info("\n")

logger.info("✅ 모든 테스트 완료")
