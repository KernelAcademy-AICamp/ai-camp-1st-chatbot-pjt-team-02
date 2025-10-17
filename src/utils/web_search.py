"""
웹 검색 유틸리티 모듈
Tavily API를 사용하여 웹 검색을 수행합니다.
"""

import os
from typing import List, Optional
from tavily import TavilyClient


class WebSearcher:
    """Tavily를 사용한 웹 검색 클래스"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Tavily API Key (None이면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")

        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")

        self.client = TavilyClient(api_key=self.api_key)

    def search(
        self,
        query: str,
        max_results: int = 3,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None
    ) -> List[dict]:
        """
        웹 검색을 수행합니다.

        Args:
            query: 검색 쿼리
            max_results: 반환할 최대 결과 수
            search_depth: 검색 깊이 ("basic" 또는 "advanced")
            include_domains: 특정 도메인만 검색 (예: ["nih.gov", "who.int"])

        Returns:
            검색 결과 리스트 (각 결과는 title, url, content 포함)
        """
        try:
            # Tavily 검색 실행
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_domains=include_domains
            )

            # 결과 포맷팅
            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", "")
                })

            return results

        except Exception as e:
            print(f"Web search failed: {e}")
            return []

    def search_and_format(
        self,
        query: str,
        max_results: int = 3,
        include_domains: Optional[List[str]] = None
    ) -> str:
        """
        웹 검색을 수행하고 결과를 문자열로 포맷팅합니다.

        Args:
            query: 검색 쿼리
            max_results: 반환할 최대 결과 수
            include_domains: 특정 도메인만 검색

        Returns:
            포맷팅된 검색 결과 문자열
        """
        results = self.search(
            query=query,
            max_results=max_results,
            include_domains=include_domains
        )

        if not results:
            return "검색 결과를 찾을 수 없습니다."

        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"[출처 {i}] {result['title']}\n"
                f"URL: {result['url']}\n"
                f"내용: {result['content']}\n"
            )

        return "\n".join(formatted)


def search_for_nutrition_info(query: str, max_results: int = 3) -> str:
    """
    영양 관련 정보를 웹에서 검색합니다.

    Args:
        query: 검색 쿼리
        max_results: 반환할 최대 결과 수

    Returns:
        포맷팅된 검색 결과
    """
    try:
        searcher = WebSearcher()

        # 신뢰할 수 있는 영양/건강 관련 도메인 지정
        trusted_domains = [
            "nih.gov",           # 미국 국립보건원
            "who.int",           # 세계보건기구
            "mfds.go.kr",        # 식품의약품안전처
            "kdca.go.kr",        # 질병관리청
            "koreanhealthlog.com",  # 한국건강관리협회
        ]

        # 한글 쿼리에 영양/건강 키워드 추가
        enhanced_query = f"{query} 영양 건강 신장질환"

        results = searcher.search_and_format(
            query=enhanced_query,
            max_results=max_results,
            include_domains=None  # 모든 도메인 검색 (필요시 trusted_domains 사용)
        )

        return results

    except ValueError as e:
        return f"웹 검색을 사용할 수 없습니다: {e}"
    except Exception as e:
        return f"웹 검색 중 오류 발생: {e}"


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    # 테스트
    query = "저칼륨 식품 대체재"
    results = search_for_nutrition_info(query)
    print(f"검색 쿼리: {query}\n")
    print(results)
