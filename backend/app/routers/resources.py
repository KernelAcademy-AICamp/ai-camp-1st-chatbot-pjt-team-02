"""
자료 추천 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.models.database import get_db, RecommendedResource
from app.models.schemas import ResourceRecommendResponse, ResourceInfo
from app.services.scraper import scrape_resources

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/recommend", response_model=ResourceRecommendResponse)
async def recommend_resources(
    keyword: str = Query(..., description="검색 키워드"),
    limit: int = Query(5, ge=1, le=20, description="결과 개수"),
    db: Session = Depends(get_db)
):
    """
    자료 추천 엔드포인트

    키워드를 받아서 관련 자료를 검색하고 추천합니다.
    캐시된 결과가 있으면 재사용합니다 (24시간 유효).
    """
    try:
        logger.info(f"자료 추천 요청: 키워드={keyword}, 제한={limit}")

        # 캐시 확인 (24시간 이내)
        cached = db.query(RecommendedResource).filter(
            RecommendedResource.keyword == keyword,
            RecommendedResource.last_updated >= datetime.now() - timedelta(hours=24)
        ).first()

        if cached:
            logger.info(f"캐시된 결과 사용: {keyword}")
            resources_data = cached.resources[:limit]
        else:
            # 웹 크롤링으로 자료 검색
            logger.info(f"웹 크롤링 시작: {keyword}")
            resources_data = await scrape_resources(keyword, limit)

            # 캐시 저장
            if resources_data:
                # 기존 캐시 삭제
                db.query(RecommendedResource).filter(
                    RecommendedResource.keyword == keyword
                ).delete()

                # 새 캐시 저장
                new_cache = RecommendedResource(
                    keyword=keyword,
                    resources=resources_data
                )
                db.add(new_cache)
                db.commit()

                logger.info(f"캐시 저장 완료: {keyword}")

        # 응답 구성
        resources = [ResourceInfo(**r) for r in resources_data]

        response = ResourceRecommendResponse(
            resources=resources,
            total=len(resources),
            keyword=keyword
        )

        logger.info(f"자료 추천 완료: {len(resources)}개")
        return response

    except Exception as e:
        logger.error(f"자료 추천 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"자료 추천 실패: {str(e)}")
