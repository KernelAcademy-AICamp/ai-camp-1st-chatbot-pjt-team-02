import openai
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from typing import Dict, List, Optional
import numpy as np
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
import os
from dotenv import load_dotenv

# ========== 1. 설정 ==========
load_dotenv()  # .env 파일에서 환경변수 로드

openai.api_key = os.getenv("OPENAI_API_KEY", "your-api-key")

# PostgreSQL 연결 설정
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", 5432),
    "database": os.getenv("DB_NAME", "kongdak_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "your-password")
}

# 영양소 제한 기준
LIMITS = {
    "sodium": 650,     # mg/끼
    "potassium": 650,  # mg/끼
    "phosphorus": 330, # mg/끼
    "protein": 40      # g/끼
}

# ========== 2. PostgreSQL 데이터베이스 구축 ==========
class NutritionDB:
    def __init__(self):
        """PostgreSQL 연결 초기화"""
        self.conn = None
        self.connect()
        self.create_tables()
        
    def connect(self):
        """PostgreSQL 데이터베이스 연결"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False  # 트랜잭션 관리를 위해
            print("PostgreSQL 연결 성공!")
        except psycopg2.Error as e:
            print(f"PostgreSQL 연결 실패: {e}")
            raise
            
    def create_tables(self):
        """테이블 생성"""
        try:
            with self.conn.cursor() as cursor:
                # foods 테이블 생성
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS foods (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        sodium FLOAT,
                        potassium FLOAT,
                        phosphorus FLOAT,
                        protein FLOAT,
                        calories FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 인덱스 생성 (검색 성능 향상)
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_foods_name 
                    ON foods(name)
                ''')
                
                # 대체 재료 테이블 생성
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alternatives (
                        id SERIAL PRIMARY KEY,
                        original_food VARCHAR(255),
                        alternative_food VARCHAR(255),
                        nutrient_type VARCHAR(50),
                        reduction_percentage FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 사용자 기록 테이블 생성
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_queries (
                        id SERIAL PRIMARY KEY,
                        user_question TEXT,
                        bot_answer TEXT,
                        nutrition_info JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                self.conn.commit()
                print("테이블 생성 완료!")
                
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"테이블 생성 실패: {e}")
            raise
    
    def load_from_excel(self, file_path):
        """엑셀에서 데이터 로드 (배치 처리로 성능 향상)"""
        try:
            df = pd.read_excel(file_path)
            
            with self.conn.cursor() as cursor:
                # 기존 데이터 삭제 (옵션)
                # cursor.execute("TRUNCATE TABLE foods RESTART IDENTITY")
                
                # 배치 INSERT 준비
                insert_query = '''
                    INSERT INTO foods (name, sodium, potassium, phosphorus, protein, calories)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        sodium = EXCLUDED.sodium,
                        potassium = EXCLUDED.potassium,
                        phosphorus = EXCLUDED.phosphorus,
                        protein = EXCLUDED.protein,
                        calories = EXCLUDED.calories,
                        updated_at = CURRENT_TIMESTAMP
                '''
                
                # 데이터 준비
                data_to_insert = []
                for _, row in df.iterrows():
                    data_to_insert.append((
                        row.get('식품명', ''),
                        float(row.get('나트륨', 0) or 0),
                        float(row.get('칼륨', 0) or 0),
                        float(row.get('인', 0) or 0),
                        float(row.get('단백질', 0) or 0),
                        float(row.get('칼로리', 0) or 0)
                    ))
                
                # 배치로 INSERT (성능 향상)
                cursor.executemany(insert_query, data_to_insert)
                self.conn.commit()
                print(f"{len(data_to_insert)}개 음식 데이터 로드 완료!")
                
        except Exception as e:
            self.conn.rollback()
            print(f"엑셀 데이터 로드 실패: {e}")
            raise
    
    def search_food(self, food_name: str) -> Optional[Dict]:
        """음식 영양 정보 검색"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 정확한 매칭 먼저 시도
                cursor.execute('''
                    SELECT * FROM foods 
                    WHERE LOWER(name) = LOWER(%s)
                    LIMIT 1
                ''', (food_name,))
                
                result = cursor.fetchone()
                
                # 부분 매칭 시도
                if not result:
                    cursor.execute('''
                        SELECT * FROM foods 
                        WHERE LOWER(name) LIKE LOWER(%s)
                        LIMIT 1
                    ''', (f'%{food_name}%',))
                    result = cursor.fetchone()
                
                return dict(result) if result else None
                
        except psycopg2.Error as e:
            print(f"음식 검색 실패: {e}")
            return None
    
    def search_multiple_foods(self, food_names: List[str]) -> List[Dict]:
        """여러 음식 한번에 검색 (성능 최적화)"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # IN 절을 사용한 일괄 검색
                placeholders = ','.join(['%s'] * len(food_names))
                cursor.execute(f'''
                    SELECT * FROM foods 
                    WHERE LOWER(name) IN ({placeholders})
                ''', tuple(name.lower() for name in food_names))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except psycopg2.Error as e:
            print(f"다중 음식 검색 실패: {e}")
            return []
    
    def save_user_query(self, question: str, answer: str, nutrition_info: Dict):
        """사용자 질의 기록 저장"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO user_queries (user_question, bot_answer, nutrition_info)
                    VALUES (%s, %s, %s::jsonb)
                ''', (question, answer, json.dumps(nutrition_info)))
                self.conn.commit()
                
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"질의 기록 저장 실패: {e}")
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
            print("PostgreSQL 연결 종료")

# ========== 3. RAG 시스템 구축 (변경 없음) ==========
class RAGSystem:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        
    def load_pdfs(self, pdf_paths: List[str]):
        """PDF 문서 로드 및 벡터화"""
        all_docs = []
        
        for pdf_path in pdf_paths:
            # PDF 로드
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # 텍스트 분할
            text_splitter = CharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            split_docs = text_splitter.split_documents(documents)
            all_docs.extend(split_docs)
        
        # 벡터 스토어 생성
        self.vector_store = FAISS.from_documents(all_docs, self.embeddings)
        
        # 로컬에 저장 (다음에 로드 가능)
        self.vector_store.save_local("faiss_index")
        print(f"{len(all_docs)}개 문서 벡터화 완료!")
        
    def search(self, query: str, k: int = 3):
        """관련 문서 검색"""
        if not self.vector_store:
            # 저장된 인덱스 로드
            self.vector_store = FAISS.load_local("faiss_index", self.embeddings)
            
        results = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in results]

# ========== 4. 메인 챗봇 시스템 ==========
class KongdakChatbot:
    def __init__(self):
        self.nutrition_db = NutritionDB()
        self.rag_system = RAGSystem()
        
    def __del__(self):
        """소멸자 - DB 연결 정리"""
        if hasattr(self, 'nutrition_db'):
            self.nutrition_db.close()
        
    def analyze_recipe(self, food_name: str) -> List[str]:
        """Step 1: LLM으로 레시피 분석"""
        prompt = f"{food_name}의 일반적인 재료를 리스트로 알려줘. 각 재료는 쉼표로 구분해줘."
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # 응답에서 재료 추출
            ingredients_text = response.choices[0].message.content
            # 실제 파싱 로직 구현 필요
            ingredients = [ing.strip() for ing in ingredients_text.split(',')]
            
            return ingredients[:10]  # 최대 10개 재료만
            
        except Exception as e:
            print(f"레시피 분석 실패: {e}")
            # 기본 재료 반환
            return ["떡", "고추장", "어묵", "파"]
    
    def calculate_nutrition(self, ingredients: List[str]) -> Dict:
        """Step 2: DB에서 영양 정보 계산"""
        total = {
            "sodium": 0.0,
            "potassium": 0.0,
            "phosphorus": 0.0,
            "protein": 0.0,
            "calories": 0.0
        }
        
        found_ingredients = []
        missing_ingredients = []
        
        for ingredient in ingredients:
            result = self.nutrition_db.search_food(ingredient)
            if result:
                total["sodium"] += result.get('sodium', 0) or 0
                total["potassium"] += result.get('potassium', 0) or 0
                total["phosphorus"] += result.get('phosphorus', 0) or 0
                total["protein"] += result.get('protein', 0) or 0
                total["calories"] += result.get('calories', 0) or 0
                found_ingredients.append(ingredient)
            else:
                missing_ingredients.append(ingredient)
        
        # 반올림
        for key in total:
            total[key] = round(total[key], 2)
        
        total['found_ingredients'] = found_ingredients
        total['missing_ingredients'] = missing_ingredients
        
        return total
    
    def get_alternatives(self, food_name: str, nutrition: Dict) -> str:
        """Step 3: RAG로 대체 방법 찾기"""
        # 위험 성분 확인
        dangerous = []
        for nutrient, value in nutrition.items():
            if nutrient in LIMITS and value > LIMITS[nutrient]:
                dangerous.append(f"{nutrient}({value}mg)")
        
        if not dangerous:
            return "모든 영양소가 안전 범위 내에 있습니다."
        
        # RAG 검색
        query = f"{food_name} {' '.join(dangerous)} 줄이는 방법 대체 재료 조리법"
        rag_results = self.rag_system.search(query)
        
        return "\n".join(rag_results)
    
    def generate_final_answer(self, food_name: str, nutrition: Dict, alternatives: str) -> str:
        """Step 4: 최종 답변 생성"""
        # 위험도 판단
        risk_level = "안전"
        warnings = []
        
        for nutrient, value in nutrition.items():
            if nutrient in LIMITS:
                if value > LIMITS[nutrient]:
                    risk_level = "위험"
                    warnings.append(f"⚠️ {nutrient}: {value}mg (제한: {LIMITS[nutrient]}mg)")
                elif value > LIMITS[nutrient] * 0.8:
                    if risk_level == "안전":
                        risk_level = "주의"
                    warnings.append(f"⚡ {nutrient}: {value}mg (제한: {LIMITS[nutrient]}mg)")
        
        # 최종 프롬프트
        prompt = f"""
        음식: {food_name}
        영양 분석:
        - 나트륨: {nutrition.get('sodium', 0)}mg
        - 칼륨: {nutrition.get('potassium', 0)}mg
        - 인: {nutrition.get('phosphorus', 0)}mg
        - 단백질: {nutrition.get('protein', 0)}g
        - 칼로리: {nutrition.get('calories', 0)}kcal
        
        위험도: {risk_level}
        경고사항: {', '.join(warnings) if warnings else '없음'}
        
        대체 방법 정보:
        {alternatives}
        
        위 정보를 바탕으로 신장 투석 환자에게 친절하고 실용적인 조언을 해주세요.
        1. 현재 음식의 위험도 설명
        2. 구체적인 대체 레시피 제안
        3. 조리 팁 제공
        답변은 이모지를 적절히 사용하여 친근하게 작성해주세요.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 신장 투석 환자를 위한 친절한 영양 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"최종 답변 생성 실패: {e}")
            return f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"
    
    def ask(self, question: str) -> str:
        """전체 프로세스 실행"""
        try:
            print(f"질문 받음: {question}")
            
            # 1. 음식명 추출 및 레시피 분석
            ingredients = self.analyze_recipe(question)
            print(f"재료 분석: {ingredients}")
            
            # 2. 영양 정보 계산
            nutrition = self.calculate_nutrition(ingredients)
            print(f"영양 계산: {nutrition}")
            
            # 3. RAG로 대체 방법 찾기
            alternatives = self.get_alternatives(question, nutrition)
            print(f"대체 방법: {alternatives[:100]}...")
            
            # 4. 최종 답변 생성
            answer = self.generate_final_answer(question, nutrition, alternatives)
            
            # 5. 질의 기록 저장
            self.nutrition_db.save_user_query(question, answer, nutrition)
            
            return answer
            
        except Exception as e:
            error_msg = f"처리 중 오류가 발생했습니다: {str(e)}"
            print(error_msg)
            return error_msg

# ========== 5. Docker Compose 설정 (docker-compose.yml) ==========
"""
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: kongdak_postgres
    environment:
      POSTGRES_DB: kongdak_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your-password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

volumes:
  postgres_data:
"""

# ========== 6. 환경변수 파일 (.env) ==========
"""
# OpenAI
OPENAI_API_KEY=your-openai-api-key

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kongdak_db
DB_USER=postgres
DB_PASSWORD=your-password
"""

# ========== 7. 실행 예시 ==========
if __name__ == "__main__":
    import json
    
    # 시스템 초기화
    print("콩닥 식탁 챗봇 시작...")
    chatbot = KongdakChatbot()
    
    # PDF 로드 (최초 1회만)
    # chatbot.rag_system.load_pdfs([
    #     "식약처_저염식_가이드.pdf",
    #     "대한신장학회_식단관리.pdf"
    # ])
    
    # 엑셀 데이터 로드 (최초 1회만)
    # chatbot.nutrition_db.load_from_excel("국가표준식품성분표.xlsx")
    
    # 테스트 질문들
    test_questions = [
        "떡볶이 먹어도 될까요?",
        "김치찌개는 어떻게 만들면 좋을까요?",
        "삼겹살 먹고 싶은데 괜찮을까요?"
    ]
    
    for question in test_questions[:1]:  # 첫 번째 질문만 테스트
        print(f"\n{'='*60}")
        print(f"질문: {question}")
        print(f"{'='*60}")
        
        answer = chatbot.ask(question)
        print(f"\n답변:\n{answer}")
        print(f"{'='*60}")
    
    # 연결 종료
    chatbot.nutrition_db.close()