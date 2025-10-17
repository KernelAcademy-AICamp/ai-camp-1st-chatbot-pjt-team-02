"""
RAG 시스템 설정 모듈
PDF 문서를 로드하고 벡터스토어를 생성합니다.
"""

import os
from typing import List
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


class RAGSetup:
    """PDF 문서를 로드하고 벡터스토어를 생성하는 클래스"""

    def __init__(
        self,
        pdf_directory: str = "./data/pdf",
        vectorstore_path: str = "./data/vectorstore",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_model: str = 'text-embedding-3-small'
    ):
        """
        Args:
            pdf_directory: PDF 파일이 있는 디렉토리 경로
            vectorstore_path: 벡터스토어를 저장할 경로
            chunk_size: 텍스트 청크 크기
            chunk_overlap: 청크 간 오버랩 크기
        """
        self.pdf_directory = Path(pdf_directory)
        self.vectorstore_path = Path(vectorstore_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 텍스트 분할기 초기화
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

        # 임베딩 모델 초기화
        self.embeddings = OpenAIEmbeddings(model=embedding_model)

    def load_pdfs(self) -> List[Document]:
        """
        PDF 디렉토리에서 모든 PDF 파일을 로드합니다.

        Returns:
            Document 객체 리스트
        """
        documents = []

        # PDF 파일 찾기
        pdf_files = list(self.pdf_directory.glob("*.pdf"))

        if not pdf_files:
            raise FileNotFoundError(f"No PDF files found in {self.pdf_directory}")

        print(f"Found {len(pdf_files)} PDF files")

        # 각 PDF 로드
        for pdf_path in pdf_files:
            print(f"Loading: {pdf_path.name}")
            loader = PyPDFLoader(str(pdf_path))
            docs = loader.load()

            # 메타데이터에 파일명 추가
            for doc in docs:
                doc.metadata["source_file"] = pdf_path.name

            documents.extend(docs)

        print(f"Loaded {len(documents)} pages total")
        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        문서를 작은 청크로 분할합니다.

        Args:
            documents: Document 객체 리스트

        Returns:
            분할된 Document 객체 리스트
        """
        print("Splitting documents into chunks...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"Created {len(chunks)} chunks")
        return chunks

    def create_vectorstore(self, chunks: List[Document]) -> FAISS:
        """
        청크로부터 벡터스토어를 생성합니다.

        Args:
            chunks: 분할된 Document 객체 리스트

        Returns:
            FAISS 벡터스토어
        """
        print("Creating vector store...")
        vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings
        )
        print("Vector store created successfully")
        return vectorstore

    def save_vectorstore(self, vectorstore: FAISS):
        """
        벡터스토어를 디스크에 저장합니다.

        Args:
            vectorstore: FAISS 벡터스토어
        """
        # 디렉토리 생성
        self.vectorstore_path.mkdir(parents=True, exist_ok=True)

        # 벡터스토어 저장
        save_path = str(self.vectorstore_path / "faiss_index")
        vectorstore.save_local(save_path)
        print(f"Vector store saved to {save_path}")

    def load_vectorstore(self) -> FAISS:
        """
        저장된 벡터스토어를 로드합니다.

        Returns:
            FAISS 벡터스토어
        """
        load_path = str(self.vectorstore_path / "faiss_index")

        if not Path(load_path).exists():
            raise FileNotFoundError(f"Vector store not found at {load_path}")

        vectorstore = FAISS.load_local(
            load_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        print(f"Vector store loaded from {load_path}")
        return vectorstore

    def setup_rag(self, force_rebuild: bool = False) -> FAISS:
        """
        RAG 시스템을 설정합니다. 벡터스토어가 없으면 생성하고, 있으면 로드합니다.

        Args:
            force_rebuild: True면 기존 벡터스토어를 무시하고 새로 생성

        Returns:
            FAISS 벡터스토어
        """
        vectorstore_exists = (self.vectorstore_path / "faiss_index").exists()

        if vectorstore_exists and not force_rebuild:
            print("Loading existing vector store...")
            return self.load_vectorstore()

        print("Building new vector store...")

        # PDF 로드
        documents = self.load_pdfs()

        # 문서 분할
        chunks = self.split_documents(documents)

        # 벡터스토어 생성
        vectorstore = self.create_vectorstore(chunks)

        # 저장
        self.save_vectorstore(vectorstore)

        return vectorstore


if __name__ == "__main__":
    from dotenv import load_dotenv

    # 환경변수 로드
    load_dotenv()

    # RAG 설정
    rag_setup = RAGSetup()
    vectorstore = rag_setup.setup_rag(force_rebuild=True)

    # 테스트 검색
    print("\n=== Testing retrieval ===")
    results = vectorstore.similarity_search("저칼륨 식품", k=3)

    for i, doc in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Source: {doc.metadata.get('source_file', 'Unknown')}")
        print(f"Content: {doc.page_content[:200]}...")
