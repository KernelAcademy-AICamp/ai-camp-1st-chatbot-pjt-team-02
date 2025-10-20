#!/usr/bin/env python3
"""
PDF 문서를 FAISS 벡터 저장소로 로드하는 스크립트
RAG (Retrieval-Augmented Generation)을 위한 데이터 준비
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# LangChain imports
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_pdfs_to_faiss(pdf_dir: str, faiss_index_path: str):
    """
    PDF 문서들을 로드하여 FAISS 벡터 저장소 생성

    Args:
        pdf_dir: PDF 파일들이 있는 디렉토리
        faiss_index_path: FAISS 인덱스를 저장할 경로
    """
    # OpenAI API 키 확인
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다")
        sys.exit(1)

    # PDF 파일 목록 가져오기
    pdf_files = list(Path(pdf_dir).glob('*.pdf'))
    if not pdf_files:
        logger.warning(f"PDF 파일을 찾을 수 없습니다: {pdf_dir}")
        return

    logger.info(f"발견된 PDF 파일: {len(pdf_files)}개")
    for pdf_file in pdf_files:
        logger.info(f"  - {pdf_file.name}")

    # 문서 로드
    all_documents = []
    for pdf_file in pdf_files:
        try:
            logger.info(f"\n로드 중: {pdf_file.name}")
            loader = PyPDFLoader(str(pdf_file))
            documents = loader.load()
            all_documents.extend(documents)
            logger.info(f"  페이지 수: {len(documents)}")
        except Exception as e:
            logger.error(f"  로드 실패: {e}")
            continue

    if not all_documents:
        logger.error("로드된 문서가 없습니다")
        sys.exit(1)

    logger.info(f"\n총 문서 페이지 수: {len(all_documents)}")

    # 텍스트 분할 (청크 생성)
    logger.info("\n텍스트 청크 생성 중...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # 각 청크의 문자 수
        chunk_overlap=50,  # 청크 간 겹침
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )
    chunks = text_splitter.split_documents(all_documents)
    logger.info(f"생성된 청크 수: {len(chunks)}")

    # 임베딩 생성 및 FAISS 인덱스 구축
    logger.info("\n임베딩 생성 및 FAISS 인덱스 구축 중...")
    logger.info("(OpenAI API를 사용하므로 시간이 걸릴 수 있습니다)")

    try:
        embeddings = OpenAIEmbeddings(
            openai_api_key=api_key,
            model="text-embedding-ada-002"
        )

        # FAISS 벡터 저장소 생성
        vectorstore = FAISS.from_documents(chunks, embeddings)

        # 인덱스 저장
        os.makedirs(os.path.dirname(faiss_index_path), exist_ok=True)
        vectorstore.save_local(faiss_index_path)

        logger.info(f"\nFAISS 인덱스 저장 완료: {faiss_index_path}")
        logger.info(f"  - 총 벡터 수: {len(chunks)}")

        # 테스트 검색
        logger.info("\n테스트 검색 수행...")
        test_query = "신장 환자 식단"
        results = vectorstore.similarity_search(test_query, k=3)
        logger.info(f"'{test_query}' 검색 결과: {len(results)}개")
        for i, doc in enumerate(results, 1):
            preview = doc.page_content[:100].replace('\n', ' ')
            logger.info(f"  {i}. {preview}...")

    except Exception as e:
        logger.error(f"FAISS 인덱스 생성 실패: {e}")
        sys.exit(1)


def main():
    """메인 실행 함수"""
    logger.info("=" * 60)
    logger.info("PDF → FAISS 벡터 저장소 로딩 시작")
    logger.info("=" * 60)

    # 경로 설정 (프로젝트 루트 기준)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_dir = os.path.join(base_dir, 'Documents', 'Data')
    faiss_index_path = os.path.join(base_dir, 'data', 'faiss_index')

    logger.info(f"\nPDF 디렉토리: {pdf_dir}")
    logger.info(f"FAISS 저장 경로: {faiss_index_path}")

    # PDF 로드 및 FAISS 인덱스 생성
    load_pdfs_to_faiss(pdf_dir, faiss_index_path)

    logger.info("\n" + "=" * 60)
    logger.info("작업 완료!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
