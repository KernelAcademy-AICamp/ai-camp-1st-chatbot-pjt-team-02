"""
RAG (Retrieval-Augmented Generation) 서비스
FAISS 벡터 스토어를 사용한 문서 검색
"""

import os
from typing import List
from pathlib import Path
import logging

try:
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import FAISS
    from langchain.document_loaders import PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    # langchain이 없는 경우 더미 클래스
    class OpenAIEmbeddings:
        pass
    class FAISS:
        @staticmethod
        def from_documents(*args, **kwargs):
            return None
        @staticmethod
        def load_local(*args, **kwargs):
            return None
    class PyPDFLoader:
        pass
    class RecursiveCharacterTextSplitter:
        pass

from app.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """RAG 서비스 클래스"""

    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self.index_path = settings.FAISS_INDEX_PATH
        self.pdf_path = settings.PDF_DATA_PATH

        # OpenAI Embeddings 초기화
        try:
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY
            )
            logger.info("OpenAI Embeddings 초기화 완료")
        except Exception as e:
            logger.error(f"OpenAI Embeddings 초기화 실패: {str(e)}")

        # 기존 인덱스 로드 시도
        self._load_existing_index()

    def _load_existing_index(self):
        """기존 FAISS 인덱스 로드"""
        try:
            if os.path.exists(self.index_path) and self.embeddings:
                self.vector_store = FAISS.load_local(
                    self.index_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"FAISS 인덱스 로드 완료: {self.index_path}")
            else:
                logger.warning(f"FAISS 인덱스 없음: {self.index_path}")
        except Exception as e:
            logger.error(f"FAISS 인덱스 로드 실패: {str(e)}")

    def load_pdfs(self, pdf_paths: List[str] = None):
        """
        PDF 문서 로드 및 벡터화

        Args:
            pdf_paths: PDF 파일 경로 리스트 (None이면 기본 경로 사용)
        """
        try:
            if not self.embeddings:
                logger.error("OpenAI Embeddings가 초기화되지 않았습니다.")
                return

            # PDF 경로 설정
            if pdf_paths is None:
                pdf_dir = Path(self.pdf_path)
                if not pdf_dir.exists():
                    logger.error(f"PDF 디렉토리 없음: {pdf_dir}")
                    return

                pdf_paths = [str(p) for p in pdf_dir.glob("*.pdf")]

            if not pdf_paths:
                logger.warning("PDF 파일이 없습니다.")
                return

            logger.info(f"{len(pdf_paths)}개 PDF 파일 로드 중...")

            all_docs = []

            # 각 PDF 파일 처리
            for pdf_path in pdf_paths:
                try:
                    loader = PyPDFLoader(pdf_path)
                    documents = loader.load()

                    # 텍스트 분할
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=settings.CHUNK_SIZE,
                        chunk_overlap=settings.CHUNK_OVERLAP,
                        separators=["\n\n", "\n", " ", ""]
                    )
                    split_docs = text_splitter.split_documents(documents)

                    all_docs.extend(split_docs)
                    logger.info(f"PDF 로드 완료: {os.path.basename(pdf_path)} ({len(split_docs)}개 청크)")

                except Exception as e:
                    logger.error(f"PDF 로드 실패: {pdf_path} - {str(e)}")

            if not all_docs:
                logger.warning("로드된 문서가 없습니다.")
                return

            # FAISS 벡터 스토어 생성
            logger.info(f"총 {len(all_docs)}개 문서 청크 벡터화 중...")
            self.vector_store = FAISS.from_documents(all_docs, self.embeddings)

            # 인덱스 저장
            os.makedirs(self.index_path, exist_ok=True)
            self.vector_store.save_local(self.index_path)

            logger.info(f"FAISS 인덱스 저장 완료: {self.index_path}")

        except Exception as e:
            logger.error(f"PDF 로드 실패: {str(e)}")

    def search(self, query: str, k: int = 3) -> List[str]:
        """
        유사 문서 검색

        Args:
            query: 검색 쿼리
            k: 반환할 문서 수

        Returns:
            검색된 문서 내용 리스트
        """
        try:
            if not self.vector_store:
                logger.warning("벡터 스토어가 없습니다. 빈 결과 반환")
                return []

            # 유사도 검색
            results = self.vector_store.similarity_search(query, k=k)

            # 문서 내용 추출
            documents = [doc.page_content for doc in results]

            logger.info(f"RAG 검색 완료: '{query}' -> {len(documents)}개 문서")

            return documents

        except Exception as e:
            logger.error(f"RAG 검색 실패: {str(e)}")
            return []

    def get_alternatives_from_rag(self, food_name: str, dangerous_nutrients: List[str]) -> str:
        """
        RAG를 사용한 대체 방법 검색

        Args:
            food_name: 음식명
            dangerous_nutrients: 위험 영양소 리스트

        Returns:
            대체 방법 텍스트
        """
        try:
            # 검색 쿼리 생성
            nutrients_text = ", ".join(dangerous_nutrients)
            query = f"{food_name} {nutrients_text} 줄이는 방법 대체 재료 조리법"

            # RAG 검색
            documents = self.search(query, k=3)

            if not documents:
                return f"{food_name}의 {nutrients_text}을(를) 줄이는 방법에 대한 참고 자료를 찾지 못했습니다."

            # 문서 내용 결합
            result = "\n\n".join(documents)

            # 길이 제한 (너무 길면 잘라냄)
            max_length = 2000
            if len(result) > max_length:
                result = result[:max_length] + "..."

            return result

        except Exception as e:
            logger.error(f"RAG 대체 방법 검색 실패: {str(e)}")
            return "대체 방법 검색 중 오류가 발생했습니다."


# 싱글톤 인스턴스
rag_service = RAGService()
