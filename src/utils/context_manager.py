"""다중 소스 컨텍스트 매니저

MongoDB → CSV 기반 벡터스토어 → PDF RAG → Tavily 웹 검색 순으로
컨텍스트를 수집해 체인에서 활용할 수 있도록 제공합니다.
"""

import logging
import re
from typing import Dict, Iterable, List, Optional

from langchain.schema import Document

logger = logging.getLogger(__name__)


def _clean_text(value) -> str:
    """값을 문자열로 변환하고 공백을 정리"""
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(_clean_text(item) for item in value if item)
    if isinstance(value, dict):
        parts = [f"{k}: {v}" for k, v in value.items() if k != "_id" and v]
        return ", ".join(parts)
    text = str(value).strip()
    return re.sub(r"\s+", " ", text)


class MultiSourceContextManager:
    """다중 데이터 소스를 순차적으로 조회해 컨텍스트를 생성"""

    def __init__(
        self,
        pdf_retriever=None,
        csv_retrievers: Optional[Dict[str, Optional[object]]] = None,
        mongo_client=None,
        web_search_fn: Optional[callable] = None,
        max_length: int = 6000,
        max_docs: int = 3,
    ):
        self.pdf_retriever = pdf_retriever
        self.csv_retrievers = csv_retrievers or {}
        self.mongo_client = mongo_client
        self.web_search_fn = web_search_fn
        self.max_length = max_length
        self.max_docs = max_docs

    # ------------------------- 공개 API -------------------------
    def collect_recipe_context(self, dish_name: str, include_web: bool = True) -> str:
        return self._collect_context(
            query=dish_name,
            mongo_collections=["recipes", "alternatives", "foods"],
            csv_sources=["recipe", "food"],
            include_web=include_web,
        )

    def collect_general_context(self, query: str, include_web: bool = True) -> str:
        return self._collect_context(
            query=query,
            mongo_collections=["recipes", "alternatives", "foods", "knowledge"],
            csv_sources=list(self.csv_retrievers.keys()),
            include_web=include_web,
        )

    def collect_ingredient_context(self, ingredient: str, include_web: bool = True) -> str:
        return self._collect_context(
            query=ingredient,
            mongo_collections=["alternatives", "foods"],
            csv_sources=["food"],
            include_web=include_web,
        )

    # ------------------------- 내부 구현 -------------------------
    def _collect_context(
        self,
        query: str,
        mongo_collections: Iterable[str],
        csv_sources: Iterable[str],
        include_web: bool,
    ) -> str:
        sections: List[str] = []

        mongo_section = self._fetch_from_mongo(query, mongo_collections)
        if mongo_section:
            sections.append(f"[MongoDB]\n{mongo_section}")

        csv_section = self._fetch_from_csv_retrievers(query, csv_sources)
        if csv_section:
            sections.append(csv_section)

        pdf_section = self._fetch_from_retriever(self.pdf_retriever, query, label="PDF")
        if pdf_section:
            sections.append(pdf_section)

        if include_web and self.web_search_fn:
            web_result = self._safe_web_search(query)
            if web_result:
                sections.append(f"[웹 검색]\n{web_result}")

        context = "\n\n".join(part for part in sections if part)
        return context[: self.max_length] if context else ""

    def _fetch_from_mongo(self, query: str, collections: Iterable[str]) -> str:
        if not self.mongo_client:
            return ""

        try:
            available_collections = set(self.mongo_client.db.list_collection_names())
        except Exception as exc:
            logger.warning("MongoDB 컬렉션 조회 실패: %s", exc)
            return ""

        regex = {"$regex": query, "$options": "i"}
        snippets: List[str] = []

        for name in collections:
            if name not in available_collections:
                continue
            try:
                collection = self.mongo_client.get_collection(name)
                docs = list(
                    collection.find(
                        {
                            "$or": [
                                {"원재료": regex},
                                {"대체식품": regex},
                                {"식품명": regex},
                                {"name": regex},
                                {"title": regex},
                                {"요리명": regex},
                                {"topic": regex},
                                {"내용": regex},
                                {"description": regex},
                                {"summary": regex},
                            ]
                        }
                    ).limit(self.max_docs)
                )
                for doc in docs:
                    formatted = ", ".join(
                        f"{k}: {_clean_text(v)}"
                        for k, v in doc.items()
                        if k != "_id" and _clean_text(v)
                    )
                    if formatted:
                        snippets.append(f"- {name}: {formatted}")
            except Exception as exc:
                logger.debug("MongoDB '%s' 검색 실패: %s", name, exc)
                continue

        return "\n".join(snippets[: self.max_docs])

    def _fetch_from_csv_retrievers(self, query: str, sources: Iterable[str]) -> str:
        sections: List[str] = []
        for name in sources:
            retriever = self.csv_retrievers.get(name)
            if retriever is None:
                continue
            section = self._fetch_from_retriever(retriever, query, label=f"{name.upper()} 벡터")
            if section:
                sections.append(section)
        return "\n\n".join(sections)

    def _fetch_from_retriever(self, retriever, query: str, label: str) -> str:
        if retriever is None:
            return ""
        try:
            docs: List[Document] = retriever.retrieve(query)
            if not docs:
                return ""
            snippets = []
            for doc in docs[: self.max_docs]:
                text = _clean_text(doc.page_content)
                if not text:
                    continue
                source = doc.metadata.get("source_file") if hasattr(doc, "metadata") else None
                if source:
                    snippets.append(f"- {source}: {text}")
                else:
                    snippets.append(f"- {text}")
            if not snippets:
                return ""
            return f"[{label}]\n" + "\n".join(snippets)
        except Exception as exc:
            logger.debug("%s 컨텍스트 검색 실패: %s", label, exc)
            return ""

    def _safe_web_search(self, query: str) -> str:
        try:
            return self.web_search_fn(query)
        except Exception as exc:
            logger.debug("웹 검색 실패: %s", exc)
            return ""


__all__ = ["MultiSourceContextManager"]
