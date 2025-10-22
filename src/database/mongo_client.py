"""MongoDB 클라이언트 모듈 - src.utils.mongodb_client를 래핑"""

import logging
from typing import Optional
from src.utils.mongodb_client import MongoDBClient, get_mongodb_client

logger = logging.getLogger(__name__)

# src.utils.mongodb_client의 함수를 재사용
def get_mongo_client() -> Optional[MongoDBClient]:
    """
    MongoDB 클라이언트 반환 (workflow.py 호환용)

    Returns:
        MongoDBClient 인스턴스 또는 연결 실패시 None
    """
    try:
        return get_mongodb_client()
    except Exception as e:
        logger.warning(f"⚠️ MongoDB 클라이언트 생성 실패: {e}")
        return None

# 다른 필요한 함수들도 export
__all__ = ["get_mongo_client", "MongoDBClient"]