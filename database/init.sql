-- 콩닥식탁 데이터베이스 초기화 스크립트

-- 식품 영양 정보 테이블
CREATE TABLE IF NOT EXISTS foods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    sodium FLOAT DEFAULT 0,
    potassium FLOAT DEFAULT 0,
    phosphorus FLOAT DEFAULT 0,
    protein FLOAT DEFAULT 0,
    calories FLOAT DEFAULT 0,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 식품명 인덱스 생성 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_foods_name ON foods(name);
CREATE INDEX IF NOT EXISTS idx_foods_category ON foods(category);

-- 대체 재료 매핑 테이블
CREATE TABLE IF NOT EXISTS alternatives (
    id SERIAL PRIMARY KEY,
    original_food VARCHAR(255) NOT NULL,
    alternative_food VARCHAR(255) NOT NULL,
    nutrient_type VARCHAR(50) NOT NULL,
    reduction_percentage FLOAT DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 대체 재료 인덱스
CREATE INDEX IF NOT EXISTS idx_alternatives_original ON alternatives(original_food);
CREATE INDEX IF NOT EXISTS idx_alternatives_nutrient ON alternatives(nutrient_type);

-- 사용자 대화 기록 테이블
CREATE TABLE IF NOT EXISTS user_queries (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_question TEXT NOT NULL,
    bot_answer TEXT,
    nutrition_info JSONB,
    risk_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 세션별 인덱스
CREATE INDEX IF NOT EXISTS idx_user_queries_session ON user_queries(session_id);
CREATE INDEX IF NOT EXISTS idx_user_queries_created ON user_queries(created_at DESC);

-- 퀴즈 기록 테이블
CREATE TABLE IF NOT EXISTS quiz_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    user_answer TEXT,
    correct_answer TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    explanation TEXT,
    difficulty VARCHAR(20),
    question_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 퀴즈 히스토리 인덱스
CREATE INDEX IF NOT EXISTS idx_quiz_history_session ON quiz_history(session_id);
CREATE INDEX IF NOT EXISTS idx_quiz_history_created ON quiz_history(created_at DESC);

-- 추천 자료 캐시 테이블
CREATE TABLE IF NOT EXISTS recommended_resources (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL UNIQUE,
    resources JSONB NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 키워드 인덱스
CREATE INDEX IF NOT EXISTS idx_recommended_resources_keyword ON recommended_resources(keyword);

-- 트리거: updated_at 자동 갱신
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_foods_updated_at BEFORE UPDATE ON foods
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- 데이터 로딩 안내
-- ========================================
-- 실제 데이터는 엑셀 파일에서 로드됩니다.
-- 다음 스크립트를 실행하세요:
--   1. scripts/load_excel_to_db.py - 엑셀 파일에서 식품/대체재료 데이터 로드
--   2. scripts/load_pdfs_to_faiss.py - PDF 문서를 FAISS 벡터 저장소에 로드
--
-- 데이터 파일 위치:
--   - Documents/Data/foods.xlsx - 식품 영양 정보
--   - Documents/Data/alternatives.xlsx - 대체 재료 매핑
--   - Documents/Data/*.pdf - 식단 관련 참고 문서
-- ========================================

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '콩닥식탁 데이터베이스 스키마 초기화 완료!';
    RAISE NOTICE '※ 데이터 로딩은 scripts/load_excel_to_db.py를 실행하세요';
END $$;
