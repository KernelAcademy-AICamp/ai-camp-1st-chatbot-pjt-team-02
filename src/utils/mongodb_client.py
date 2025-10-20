"""MongoDB Atlas 클라이언트 모듈"""

import os
import logging
from typing import Optional, List, Dict, Any
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB Atlas 클라이언트 클래스"""

    def __init__(self, connection_string: Optional[str] = None, database_name: str = "chatbot_nutrition"):
        """
        MongoDB 클라이언트 초기화

        Args:
            connection_string: MongoDB Atlas 연결 문자열 (기본값: 환경변수에서 로드)
            database_name: 데이터베이스 이름
        """
        self.connection_string = connection_string or os.getenv("MONGO_ATLAS_URL")

        if not self.connection_string:
            raise ValueError("MONGO_ATLAS_URL이 .env 파일에 설정되지 않았습니다.")

        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[database_name]
            # 연결 테스트
            self.client.admin.command('ping')
            logger.info(f"✅ MongoDB Atlas 연결 성공: {database_name}")
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB 연결 실패: {e}")
            raise

    def get_collection(self, collection_name: str):
        """
        컬렉션 반환

        Args:
            collection_name: 컬렉션 이름

        Returns:
            MongoDB 컬렉션 객체
        """
        return self.db[collection_name]

    def create_indexes(self, collection_name: str, indexes: List[tuple]):
        """
        인덱스 생성

        Args:
            collection_name: 컬렉션 이름
            indexes: 인덱스 필드 리스트 [(field_name, order), ...]
        """
        collection = self.get_collection(collection_name)
        for field, order in indexes:
            collection.create_index([(field, order)])
            logger.info(f"✅ 인덱스 생성: {collection_name}.{field}")

    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]], ordered: bool = False):
        """
        다중 문서 삽입

        Args:
            collection_name: 컬렉션 이름
            documents: 삽입할 문서 리스트
            ordered: 순서대로 삽입 여부 (False면 중복 무시하고 계속)

        Returns:
            삽입된 문서 개수
        """
        collection = self.get_collection(collection_name)
        try:
            result = collection.insert_many(documents, ordered=ordered)
            logger.info(f"✅ {len(result.inserted_ids)}개 문서 삽입 완료: {collection_name}")
            return len(result.inserted_ids)
        except DuplicateKeyError as e:
            logger.warning(f"⚠️ 중복 문서 무시: {e}")
            return 0

    def find_alternatives(
        self,
        ingredient: str,
        nutrient_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        재료명으로 대체재 검색

        Args:
            ingredient: 원재료명
            nutrient_types: 영양소 종류 필터 (예: ['sodium', 'potassium'])
            limit: 최대 결과 개수

        Returns:
            대체재 정보 리스트
        """
        collection = self.get_collection("alternatives")

        # 쿼리 구성
        query = {"원재료": {"$regex": ingredient, "$options": "i"}}  # 대소문자 무시 검색

        if nutrient_types:
            query["영양소종류"] = {"$in": nutrient_types}

        # 감소비율 내림차순 정렬
        results = list(collection.find(query).sort("감소비율", -1).limit(limit))

        logger.info(f"🔍 '{ingredient}' 대체재 검색: {len(results)}개 발견")
        return results

    def close(self):
        """MongoDB 연결 종료"""
        if self.client:
            self.client.close()
            logger.info("MongoDB 연결 종료")


# 싱글톤 인스턴스
_mongodb_client: Optional[MongoDBClient] = None


def get_mongodb_client() -> MongoDBClient:
    """
    MongoDB 클라이언트 싱글톤 반환

    Returns:
        MongoDBClient 인스턴스
    """
    global _mongodb_client
    if _mongodb_client is None:
        _mongodb_client = MongoDBClient()
    return _mongodb_client
