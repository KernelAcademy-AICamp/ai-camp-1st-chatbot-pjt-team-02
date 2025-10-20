"""
검색(Retriever) 모듈
벡터스토어에서 관련 문서를 검색합니다.
"""

from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI


class DocumentRetriever:
    """문서 검색을 수행하는 클래스"""

    def __init__(
        self,
        vectorstore: FAISS,
        search_type: str = "similarity",
        k: int = 4,
        use_compression: bool = False
    ):
        """
        Args:
            vectorstore: FAISS 벡터스토어
            search_type: 검색 유형 ('similarity' 또는 'mmr')
            k: 반환할 문서 개수
            use_compression: 압축 retriever 사용 여부
        """
        self.vectorstore = vectorstore
        self.search_type = search_type
        self.k = k
        self.use_compression = use_compression

        # 기본 retriever 생성
        self.base_retriever = self._create_base_retriever()

        # 압축 retriever 생성 (선택사항)
        if use_compression:
            self.retriever = self._create_compression_retriever()
        else:
            self.retriever = self.base_retriever

    def _create_base_retriever(self):
        """기본 retriever를 생성합니다."""
        if self.search_type == "mmr":
            # MMR (Maximum Marginal Relevance) 검색
            return self.vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": self.k,
                    "fetch_k": self.k * 2,  # 후보군 크기
                    "lambda_mult": 0.5  # 다양성 vs 관련성 (0~1)
                }
            )
        else:
            # 일반 유사도 검색
            return self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": self.k}
            )

    def _create_compression_retriever(self):
        """압축 retriever를 생성합니다. (쿼리와 관련된 부분만 추출)"""
        llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        compressor = LLMChainExtractor.from_llm(llm)

        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=self.base_retriever
        )

        return compression_retriever

    def retrieve(self, query: str) -> List[Document]:
        """
        쿼리에 대한 관련 문서를 검색합니다.

        Args:
            query: 검색 쿼리

        Returns:
            관련 Document 객체 리스트
        """
        return self.retriever.invoke(query)

    def retrieve_with_scores(
        self,
        query: str,
        k: Optional[int] = None
    ) -> List[tuple[Document, float]]:
        """
        쿼리에 대한 관련 문서와 유사도 점수를 검색합니다.

        Args:
            query: 검색 쿼리
            k: 반환할 문서 개수 (None이면 기본값 사용)

        Returns:
            (Document, score) 튜플 리스트
        """
        k = k or self.k
        return self.vectorstore.similarity_search_with_score(query, k=k)

    def filter_by_source(
        self,
        query: str,
        source_file: str
    ) -> List[Document]:
        """
        특정 소스 파일에서만 검색합니다.

        Args:
            query: 검색 쿼리
            source_file: 소스 파일명

        Returns:
            관련 Document 객체 리스트
        """
        # 모든 문서 검색
        all_docs = self.retrieve(query)

        # 소스 파일로 필터링
        filtered_docs = [
            doc for doc in all_docs
            if doc.metadata.get("source_file") == source_file
        ]

        return filtered_docs


def create_retriever(
    vectorstore: FAISS,
    retriever_type: str = "basic",
    k: int = 4
) -> DocumentRetriever:
    """
    Retriever 타입에 따라 적절한 retriever를 생성합니다.

    Args:
        vectorstore: FAISS 벡터스토어
        retriever_type: retriever 타입 ('basic', 'mmr', 'compression')
        k: 반환할 문서 개수

    Returns:
        DocumentRetriever 인스턴스
    """
    if retriever_type == "basic":
        return DocumentRetriever(
            vectorstore=vectorstore,
            search_type="similarity",
            k=k,
            use_compression=False
        )
    elif retriever_type == "mmr":
        return DocumentRetriever(
            vectorstore=vectorstore,
            search_type="mmr",
            k=k,
            use_compression=False
        )
    elif retriever_type == "compression":
        return DocumentRetriever(
            vectorstore=vectorstore,
            search_type="similarity",
            k=k,
            use_compression=True
        )
    else:
        raise ValueError(f"Unknown retriever type: {retriever_type}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    from .rag_setup import RAGSetup

    load_dotenv()

    # 벡터스토어 로드
    rag_setup = RAGSetup()
    vectorstore = rag_setup.load_vectorstore()

    # Retriever 생성 및 테스트
    retriever = create_retriever(vectorstore, retriever_type="basic", k=3)

    # 검색 테스트
    query = "저칼륨 식품은 무엇인가요?"
    docs = retriever.retrieve(query)

    print(f"Query: {query}\n")
    for i, doc in enumerate(docs, 1):
        print(f"--- Document {i} ---")
        print(f"Source: {doc.metadata.get('source_file')}")
        print(f"Content: {doc.page_content[:200]}...\n")
