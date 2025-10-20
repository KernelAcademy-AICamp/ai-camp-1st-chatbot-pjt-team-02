"""
웹 크롤링 서비스 (3순위 기능)
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict
import hashlib
import logging

logger = logging.getLogger(__name__)

# 신뢰할 수 있는 도메인
TRUSTED_DOMAINS = [
    "mfds.go.kr",           # 식약처
    "ksn.or.kr",            # 대한신장학회
    "dietitian.or.kr",      # 대한영양사협회
    "kdca.go.kr"            # 질병관리청
]


async def scrape_resources(keyword: str, limit: int = 5) -> List[Dict]:
    """
    웹 크롤링으로 자료 검색

    Args:
        keyword: 검색 키워드
        limit: 결과 개수

    Returns:
        자료 정보 리스트
    """
    try:
        # 실제 구현: 각 도메인을 크롤링
        # 현재는 더미 데이터 반환 (실제 크롤링은 사이트별 파싱 로직 필요)

        logger.info(f"웹 크롤링: {keyword}")

        # 더미 데이터 (실제로는 웹 크롤링 결과)
        dummy_resources = [
            {
                "title": f"{keyword} 관련 식약처 가이드",
                "url": "https://www.mfds.go.kr/",
                "description": f"{keyword}에 대한 식약처 공식 가이드라인입니다.",
                "source": "식약처",
                "relevance_score": 0.95,
                "published_date": "2024-10-15"
            },
            {
                "title": f"신장 환자를 위한 {keyword} 식단 관리",
                "url": "https://www.ksn.or.kr/",
                "description": "대한신장학회에서 제공하는 식단 관리 자료입니다.",
                "source": "대한신장학회",
                "relevance_score": 0.90,
                "published_date": "2024-09-20"
            },
            {
                "title": f"{keyword} 영양 정보",
                "url": "https://www.dietitian.or.kr/",
                "description": "영양사 협회의 영양 정보 자료입니다.",
                "source": "대한영양사협회",
                "relevance_score": 0.85,
                "published_date": "2024-08-10"
            }
        ]

        # 실제 크롤링 로직 (주석 처리 - 실제 구현 시 활성화)
        # results = []
        # async with aiohttp.ClientSession() as session:
        #     tasks = []
        #     for domain in TRUSTED_DOMAINS:
        #         tasks.append(scrape_site(session, domain, keyword))
        #
        #     site_results = await asyncio.gather(*tasks)
        #
        #     for site_result in site_results:
        #         results.extend(site_result)
        #
        #     # 관련성 점수로 정렬
        #     results.sort(key=lambda x: x['relevance_score'], reverse=True)
        #
        #     # 중복 제거
        #     seen_urls = set()
        #     unique_results = []
        #     for item in results:
        #         url_hash = hashlib.md5(item['url'].encode()).hexdigest()
        #         if url_hash not in seen_urls:
        #             seen_urls.add(url_hash)
        #             unique_results.append(item)
        #
        #     return unique_results[:limit]

        return dummy_resources[:limit]

    except Exception as e:
        logger.error(f"웹 크롤링 실패: {str(e)}")
        return []


async def scrape_site(session: aiohttp.ClientSession, domain: str, keyword: str) -> List[Dict]:
    """
    특정 사이트 크롤링 (실제 구현 예시 - 주석 처리)
    """
    try:
        search_url = f"https://{domain}/search?q={keyword}"

        async with session.get(search_url, timeout=5) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                results = []
                articles = soup.find_all('article', limit=3)

                for article in articles:
                    title_elem = article.find('h3')
                    link_elem = article.find('a')
                    desc_elem = article.find('p')

                    if title_elem and link_elem:
                        results.append({
                            'title': title_elem.text.strip(),
                            'url': f"https://{domain}{link_elem.get('href')}",
                            'description': desc_elem.text.strip() if desc_elem else '',
                            'source': domain,
                            'relevance_score': calculate_relevance(
                                title_elem.text,
                                desc_elem.text if desc_elem else '',
                                keyword
                            )
                        })

                return results

    except Exception as e:
        logger.error(f"사이트 크롤링 실패: {domain} - {str(e)}")
        return []


def calculate_relevance(title: str, description: str, keyword: str) -> float:
    """관련성 점수 계산"""
    score = 0.0
    keyword_lower = keyword.lower()

    # 제목에 키워드 포함
    if keyword_lower in title.lower():
        score += 0.5

    # 설명에 키워드 포함
    if keyword_lower in description.lower():
        score += 0.3

    # 추가 관련 키워드
    related_keywords = ['신장', '투석', '저염', '저칼륨', '식단']
    for related in related_keywords:
        if related in title.lower() or related in description.lower():
            score += 0.1

    return min(score, 1.0)
