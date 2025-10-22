"""대체재 검색 유틸리티 - 벡터 기반 유사도 검색"""

import logging
import os
from typing import List, Dict, Optional, Any
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


def load_vector_stores():
    """
    벡터스토어 로드 (food_vectors, recipe_vectors)

    Returns:
        (food_vectorstore, recipe_vectorstore) 또는 (None, None)
    """
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings

        project_root = Path(__file__).resolve().parents[2]
        vector_dir = project_root / "data" / "vectorstore"

        food_vectorstore = None
        recipe_vectorstore = None

        # food_vectors 로드
        food_path = vector_dir / "food_vectors"
        if food_path.exists():
            try:
                embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                food_vectorstore = FAISS.load_local(
                    str(food_path),
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("✅ food_vectors 로드 완료")
            except Exception as e:
                logger.warning(f"⚠️ food_vectors 로드 실패: {e}")

        # recipe_vectors 로드
        recipe_path = vector_dir / "recipe_vectors"
        if recipe_path.exists():
            try:
                embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                recipe_vectorstore = FAISS.load_local(
                    str(recipe_path),
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("✅ recipe_vectors 로드 완료")
            except Exception as e:
                logger.warning(f"⚠️ recipe_vectors 로드 실패: {e}")

        return food_vectorstore, recipe_vectorstore

    except Exception as e:
        logger.warning(f"⚠️ 벡터스토어 로드 실패: {e}")
        return None, None


def search_alternatives_by_vector(
    ingredient: str,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    벡터 기반 유사도 검색으로 대체재 찾기

    Args:
        ingredient: 원재료명
        max_results: 최대 결과 개수

    Returns:
        대체재 정보 리스트
    """
    try:
        logger.info(f"🔍 벡터 기반 검색 시작: '{ingredient}'")

        food_vs, recipe_vs = load_vector_stores()

        results = []

        # food_vectors에서 검색
        if food_vs:
            try:
                docs = food_vs.similarity_search(ingredient, k=max_results)
                for doc in docs:
                    metadata = doc.metadata or {}
                    results.append({
                        "원재료": ingredient,
                        "대체식품": metadata.get("name", doc.page_content),
                        "조리방법": metadata.get("cooking_method", "조리 필요"),
                        "칼륨감소비율": metadata.get("potassium_reduction", 30),
                        "영양소종류": metadata.get("nutrient_type", "칼륨"),
                        "유사도점수": metadata.get("similarity_score", 0.8),
                        "source": "food_vectors"
                    })
                logger.info(f"✅ food_vectors에서 {len(docs)}개 결과 발견")
            except Exception as e:
                logger.debug(f"⚠️ food_vectors 검색 오류: {e}")

        # recipe_vectors에서도 검색 (더 많은 결과를 위해)
        if recipe_vs and len(results) < max_results:
            try:
                remaining = max_results - len(results)
                docs = recipe_vs.similarity_search(ingredient, k=remaining)
                for doc in docs:
                    metadata = doc.metadata or {}
                    results.append({
                        "원재료": ingredient,
                        "대체식품": metadata.get("name", doc.page_content),
                        "조리방법": metadata.get("cooking_method", "조리 필요"),
                        "칼륨감소비율": metadata.get("potassium_reduction", 30),
                        "영양소종류": metadata.get("nutrient_type", "칼륨"),
                        "유사도점수": metadata.get("similarity_score", 0.8),
                        "source": "recipe_vectors"
                    })
                logger.info(f"✅ recipe_vectors에서 {len(docs)}개 결과 발견")
            except Exception as e:
                logger.debug(f"⚠️ recipe_vectors 검색 오류: {e}")

        # 중복 제거 및 유사도로 정렬
        unique_results = {}
        for result in results:
            key = result["대체식품"]
            if key not in unique_results or result.get("유사도점수", 0) > unique_results[key].get("유사도점수", 0):
                unique_results[key] = result

        results = sorted(unique_results.values(), key=lambda x: x.get("유사도점수", 0), reverse=True)[:max_results]

        if results:
            logger.info(f"✅ 벡터 기반 검색: {len(results)}개 대체재 발견")
            return results

        logger.debug("ℹ️ 벡터 기반 검색 결과 없음")
        return []

    except Exception as e:
        logger.debug(f"⚠️ 벡터 기반 검색 오류: {e}")
        return []


def search_alternatives(
    ingredient: str,
    nutrient_types: Optional[List[str]] = None,
    max_results: int = 10,
    retriever=None,
    use_web_search: bool = False,
    mongo_client=None
) -> List[Dict[str, Any]]:
    """
    재료의 대체재를 검색 (우선순위: MongoDB -> RAG CSV -> RAG PDF -> Web)

    Args:
        ingredient: 원재료명
        nutrient_types: 영양소 종류 필터 (예: ['sodium', 'potassium'])
        max_results: 최대 결과 개수
        retriever: RAG 리트리버 (선택)
        use_web_search: 웹 검색 사용 여부
        mongo_client: MongoDB 클라이언트 (선택)

    Returns:
        대체재 정보 리스트
    """
    logger.info(f"🔍 '{ingredient}' 대체재 검색 시작 (우선순위: MongoDB -> RAG CSV -> RAG PDF -> Web)...")

    # 1. MongoDB에서 검색 (가장 우선)
    if mongo_client:
        try:
            mongo_results = mongo_client.find_alternatives(
                ingredient=ingredient,
                nutrient_types=nutrient_types,
                limit=max_results
            )
            if mongo_results:
                # MongoDB 결과에 source 추가
                for result in mongo_results:
                    result['source'] = 'MongoDB'
                logger.info(f"✅ MongoDB에서 {len(mongo_results)}개 대체재 발견")
                return mongo_results
        except Exception as e:
            logger.debug(f"⚠️ MongoDB 검색 오류: {e}")

    # 2. RAG (CSV) 검색
    if retriever:
        csv_rag_results = search_alternatives_from_rag_csv(ingredient, retriever, max_results)
        if csv_rag_results:
            logger.info(f"✅ RAG (CSV)에서 {len(csv_rag_results)}개 대체재 발견")
            return csv_rag_results

    # 3. RAG (PDF) 검색
    if retriever:
        rag_pdf_results = search_alternatives_from_rag_pdf(ingredient, retriever, max_results)
        if rag_pdf_results:
            logger.info(f"✅ RAG (PDF)에서 {len(rag_pdf_results)}개 대체재 발견")
            return rag_pdf_results

    # 4. Web 검색 (마지막)
    if use_web_search:
        web_results = search_alternatives_from_web(ingredient, max_results)
        if web_results:
            logger.info(f"✅ 웹 검색에서 {len(web_results)}개 대체재 발견")
            return web_results

    # 5. Fallback - 일반적인 대체재 제안
    fallback_results = get_fallback_alternatives(ingredient)
    if fallback_results:
        logger.info(f"✅ Fallback에서 {len(fallback_results)}개 대체재 제안")
        return fallback_results

    logger.warning(f"⚠️ '{ingredient}'의 대체재를 찾을 수 없음")
    return []


def search_alternatives_from_rag_csv(
    ingredient: str,
    retriever,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    RAG를 사용하여 CSV 기반 대체재 검색
    (recipe_df.csv, food_database_cleaned_df.csv 등)

    Args:
        ingredient: 원재료명
        retriever: RAG 리트리버
        max_results: 최대 결과 개수

    Returns:
        대체재 정보 리스트
    """
    try:
        logger.info(f"📊 RAG (CSV) 검색 시작: '{ingredient}'")

        if not retriever:
            logger.debug("⚠️ 리트리버가 없음, RAG (CSV) 검색 스킵")
            return []

        # CSV 기반 대체재 관련 문서 검색
        query = f"{ingredient} 대체식품 재료 저칼륨 저나트륨 영양"
        docs = retriever.get_relevant_documents(query)

        results = []
        seen_alternatives = set()

        for doc in docs[:max_results * 2]:  # 더 많은 문서에서 선택
            content = doc.page_content or ""
            metadata = doc.metadata or {}

            # 대체식품명 추출
            alternative_name = metadata.get("alternative_name") or metadata.get("name") or "대체식품"

            # 중복 제거
            if alternative_name in seen_alternatives:
                continue
            seen_alternatives.add(alternative_name)

            results.append({
                "원재료": ingredient,
                "대체식품": alternative_name,
                "조리방법": metadata.get("cooking_method", "조리 필요"),
                "칼륨감소비율": int(metadata.get("potassium_reduction", 20)) if metadata.get("potassium_reduction") else 20,
                "영양소종류": metadata.get("nutrient_type", "칼륨"),
                "source": "RAG (CSV)",
                "출처": "CSV 데이터베이스",
                "출처내용": content[:150] if content else ""
            })

            if len(results) >= max_results:
                break

        if results:
            logger.info(f"✅ RAG (CSV)에서 {len(results)}개 결과 발견")

        return results

    except Exception as e:
        logger.debug(f"⚠️ RAG (CSV) 검색 오류: {e}")
        return []


def search_alternatives_from_rag_pdf(
    ingredient: str,
    retriever,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    RAG를 사용하여 PDF 문서 기반 대체재 검색
    (의료/영양 전문 문서)

    Args:
        ingredient: 원재료명
        retriever: RAG 리트리버
        max_results: 최대 결과 개수

    Returns:
        대체재 정보 리스트
    """
    try:
        logger.info(f"📄 RAG (PDF) 검색 시작: '{ingredient}'")

        if not retriever:
            logger.debug("⚠️ 리트리버가 없음, RAG (PDF) 검색 스킵")
            return []

        # PDF 기반 대체재 관련 문서 검색
        # 신장질환 전문 정보로 특화된 쿼리
        query = f"{ingredient} 대체 식품 신장질환 칼륨 나트륨 인 제한"
        docs = retriever.get_relevant_documents(query)

        results = []
        seen_alternatives = set()

        for doc in docs[:max_results * 2]:  # 더 많은 문서에서 선택
            content = doc.page_content or ""
            metadata = doc.metadata or {}

            # 문서에서 대체식품명 추출 시도
            alternative_name = metadata.get("title") or metadata.get("alternative") or "대체식품"

            # 중복 제거
            if alternative_name in seen_alternatives:
                continue
            seen_alternatives.add(alternative_name)

            results.append({
                "원재료": ingredient,
                "대체식품": alternative_name,
                "조리방법": metadata.get("method", "의료진 상담 필요"),
                "칼륨감소비율": int(metadata.get("potassium_reduction", 25)) if metadata.get("potassium_reduction") else 25,
                "영양소종류": "칼륨",
                "source": "RAG (PDF)",
                "출처": metadata.get("source", "의료 문서"),
                "출처내용": content[:150] if content else ""
            })

            if len(results) >= max_results:
                break

        if results:
            logger.info(f"✅ RAG (PDF)에서 {len(results)}개 결과 발견")

        return results

    except Exception as e:
        logger.debug(f"⚠️ RAG (PDF) 검색 오류: {e}")
        return []


def search_alternatives_from_rag(
    ingredient: str,
    retriever,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    RAG (통합 검색) - 더 이상 사용되지 않음 (호환성 유지)
    대신 search_alternatives_from_rag_csv 또는 search_alternatives_from_rag_pdf 사용

    Args:
        ingredient: 원재료명
        retriever: RAG 리트리버
        max_results: 최대 결과 개수

    Returns:
        대체재 정보 리스트
    """
    # CSV 검색을 우선으로 시도
    csv_results = search_alternatives_from_rag_csv(ingredient, retriever, max_results)
    if csv_results:
        return csv_results

    # CSV에서 결과가 없으면 PDF 검색
    return search_alternatives_from_rag_pdf(ingredient, retriever, max_results)


def search_alternatives_from_web(
    ingredient: str,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    웹 검색을 사용하여 대체재 검색

    Args:
        ingredient: 원재료명
        max_results: 최대 결과 개수

    Returns:
        대체재 정보 리스트
    """
    try:
        logger.info(f"🌐 웹 검색 시작: '{ingredient}'")

        from src.utils.web_search import search_for_nutrition_info

        # 웹 검색으로 영양 정보 검색
        search_query = f"{ingredient} 신장질환 투석 대체식품 저칼륨"
        web_results = search_for_nutrition_info(search_query)

        if not web_results:
            logger.debug("ℹ️ 웹 검색 결과 없음")
            return []

        results = []
        for i, result in enumerate(web_results[:max_results], 1):
            results.append({
                "원재료": ingredient,
                "대체식품": result.get("title", f"대체식품_{i}"),
                "조리방법": "웹 자료 참고",
                "칼륨감소비율": 30,  # 기본값
                "영양소종류": "칼륨",
                "source": "Web",
                "링크": result.get("link", ""),
                "설명": result.get("snippet", "")[:200] if result.get("snippet") else ""
            })

        if results:
            logger.info(f"✅ 웹 검색에서 {len(results)}개 결과 발견")

        return results

    except Exception as e:
        logger.debug(f"⚠️ 웹 검색 오류: {e}")
        return []


def search_alternatives_from_csv(
    ingredient: str,
    nutrient_types: Optional[List[str]] = None,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    CSV 파일에서 대체재 검색

    Args:
        ingredient: 원재료명
        nutrient_types: 영양소 종류 필터
        max_results: 최대 결과 개수

    Returns:
        대체재 정보 리스트
    """
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(project_root, "data", "preprocess", "alternatives.csv")

        if not os.path.exists(csv_path):
            logger.debug(f"CSV 파일 없음: {csv_path}")
            return []

        df = pd.read_csv(csv_path)
        logger.debug(f"CSV 데이터 로드: {len(df)}행")

        # 재료명으로 필터링
        filtered = df[df["원재료"].str.contains(ingredient, case=False, na=False)]

        # 영양소 종류로 필터링
        if nutrient_types:
            nutrient_filter = df["영양소종류"].apply(
                lambda x: any(nt in str(x).lower() for nt in nutrient_types)
            )
            filtered = filtered[nutrient_filter]

        # 감소비율로 정렬
        filtered = filtered.sort_values("감소비율", ascending=False)

        # 딕셔너리 리스트로 변환
        results = filtered.head(max_results).to_dict('records')

        # 칼럼명 한글화 (필요시)
        for result in results:
            result["칼륨감소비율"] = result.get("감소비율", 0)

        return results

    except Exception as e:
        logger.debug(f"CSV 검색 오류: {e}")
        return []


def search_alternatives_from_excel(
    ingredient: str,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Excel 파일에서 대체재 검색

    Args:
        ingredient: 원재료명
        max_results: 최대 결과 개수

    Returns:
        대체재 정보 리스트
    """
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        excel_path = os.path.join(project_root, "data", "raw", "alternatives.xlsx")

        if not os.path.exists(excel_path):
            logger.debug(f"Excel 파일 없음: {excel_path}")
            return []

        # Excel 파일 읽기
        df = pd.read_excel(excel_path)
        logger.debug(f"Excel 데이터 로드: {len(df)}행")

        # 재료명으로 필터링
        filtered = df[df.iloc[:, 0].str.contains(ingredient, case=False, na=False)]

        # 딕셔너리 리스트로 변환
        results = []
        for _, row in filtered.head(max_results).iterrows():
            results.append({
                "원재료": row.iloc[0] if len(row) > 0 else "",
                "대체식품": row.iloc[1] if len(row) > 1 else "",
                "조리방법": row.iloc[2] if len(row) > 2 else "",
                "칼륨감소비율": row.iloc[3] if len(row) > 3 else 0,
                "영양소종류": "칼륨"  # 기본값
            })

        return results

    except Exception as e:
        logger.debug(f"Excel 검색 오류: {e}")
        return []


def get_fallback_alternatives(ingredient: str) -> List[Dict[str, Any]]:
    """
    일반적인 대체재 제안 (Fallback)

    Args:
        ingredient: 원재료명

    Returns:
        대체재 정보 리스트
    """
    # 일반적인 대체재 매핑
    common_alternatives = {
        "감자": [
            {"원재료": "감자", "대체식품": "고구마", "조리방법": "삶기", "칼륨감소비율": 30, "영양소종류": "칼륨"},
            {"원재료": "감자", "대체식품": "무", "조리방법": "삶기", "칼륨감소비율": 40, "영양소종류": "칼륨"},
        ],
        "시금치": [
            {"원재료": "시금치", "대체식품": "배추", "조리방법": "데치기", "칼륨감소비율": 50, "영양소종류": "칼륨"},
            {"원재료": "시금치", "대체식품": "양배추", "조리방법": "볶기", "칼륨감소비율": 45, "영양소종류": "칼륨"},
        ],
        "김치": [
            {"원재료": "김치", "대체식품": "백김치", "조리방법": "저염 발효", "칼륨감소비율": 40, "영양소종류": "나트륨"},
            {"원재료": "김치", "대체식품": "물김치", "조리방법": "저염 발효", "칼륨감소비율": 50, "영양소종류": "나트륨"},
        ],
        "돼지고기": [
            {"원재료": "돼지고기", "대체식품": "닭가슴살", "조리방법": "삶기", "칼륨감소비율": 20, "영양소종류": "인"},
            {"원재료": "돼지고기", "대체식품": "두부", "조리방법": "구이", "칼륨감소비율": 30, "영양소종류": "인"},
        ],
        "소고기": [
            {"원재료": "소고기", "대체식품": "닭고기", "조리방법": "삶기", "칼륨감소비율": 25, "영양소종류": "인"},
            {"원재료": "소고기", "대체식품": "생선", "조리방법": "구이", "칼륨감소비율": 35, "영양소종류": "인"},
        ],
        "우유": [
            {"원재료": "우유", "대체식품": "두유", "조리방법": "-", "칼륨감소비율": 20, "영양소종류": "인"},
            {"원재료": "우유", "대체식품": "아몬드밀크", "조리방법": "-", "칼륨감소비율": 60, "영양소종류": "칼륨"},
        ],
        "치즈": [
            {"원재료": "치즈", "대체식품": "리코타치즈", "조리방법": "-", "칼륨감소비율": 30, "영양소종류": "나트륨"},
            {"원재료": "치즈", "대체식품": "코티지치즈", "조리방법": "-", "칼륨감소비율": 40, "영양소종류": "나트륨"},
        ],
        "된장": [
            {"원재료": "된장", "대체식품": "저염된장", "조리방법": "-", "칼륨감소비율": 40, "영양소종류": "나트륨"},
            {"원재료": "된장", "대체식품": "청국장", "조리방법": "-", "칼륨감소비율": 20, "영양소종류": "나트륨"},
        ],
        "간장": [
            {"원재료": "간장", "대체식품": "저염간장", "조리방법": "-", "칼륨감소비율": 50, "영양소종류": "나트륨"},
            {"원재료": "간장", "대체식품": "레몬즙", "조리방법": "-", "칼륨감소비율": 90, "영양소종류": "나트륨"},
        ],
    }

    # 재료명에서 키워드 찾기
    for key, alternatives in common_alternatives.items():
        if key in ingredient.lower():
            return alternatives

    # 기본 대체재 제안
    return [
        {
            "원재료": ingredient,
            "대체식품": "저칼륨 대체재 검색 필요",
            "조리방법": "데치기, 삶기 권장",
            "칼륨감소비율": 30,
            "영양소종류": "칼륨",
            "note": "일반적인 조리법으로 칼륨 감소 가능"
        }
    ]


def format_alternatives_for_display(alternatives: List[Dict[str, Any]]) -> str:
    """
    대체재 정보를 보기 좋게 포맷팅

    Args:
        alternatives: 대체재 정보 리스트

    Returns:
        포맷팅된 문자열
    """
    if not alternatives:
        return "대체재 정보가 없습니다."

    formatted = []
    for i, alt in enumerate(alternatives[:5], 1):  # 상위 5개만
        text = f"{i}. **{alt.get('대체식품', 'N/A')}**\n"
        text += f"   - 조리방법: {alt.get('조리방법', 'N/A')}\n"
        text += f"   - 칼륨 감소: {alt.get('칼륨감소비율', 0)}%\n"

        if alt.get('note'):
            text += f"   - 참고: {alt['note']}\n"

        formatted.append(text)

    return "\n".join(formatted)


if __name__ == "__main__":
    # 테스트
    test_ingredients = ["감자", "김치", "돼지고기", "시금치"]

    for ingredient in test_ingredients:
        print(f"\n### {ingredient} 대체재 검색 ###")
        results = search_alternatives(ingredient, use_mongodb=False)
        print(format_alternatives_for_display(results))