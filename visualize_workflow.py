"""LangGraph 워크플로우 시각화 (로컬 렌더링 버전)"""

import os
import subprocess
from dotenv import load_dotenv
from src.rag.rag_setup import RAGSetup
from src.workflow.workflow import create_workflow_app
from IPython.display import Image, display

# ====================================
# 1️⃣ 환경 변수 설정
# ====================================
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found. Please set it in .env file")

print("✅ 환경 설정 완료")

# ====================================
# 2️⃣ RAG 시스템 초기화
# ====================================
print("📚 RAG 시스템 초기화 중...")
rag_setup = RAGSetup(
    pdf_directory="data/pdf",
    vectorstore_path="data/vectorstore/faiss_index",
    chunk_size=300,
    chunk_overlap=30
)
vectorstore = rag_setup.setup_rag(force_rebuild=False)
print("✅ RAG 시스템 초기화 완료")

# ====================================
# 3️⃣ 워크플로우 생성
# ====================================
print("🔧 워크플로우 생성 중...")
llm_config = {
    "intent_classifier": {"model": "gpt-4o-mini", "temperature": 0.3},
    "recommendation": {"model": "gpt-4o-mini", "temperature": 0.7},
    "summary": {"model": "gpt-4o-mini", "temperature": 0.7},
    "quiz": {"model": "gpt-4o-mini", "temperature": 0.7},
}
app = create_workflow_app(vectorstore, llm_config)
print("✅ 워크플로우 앱 생성 완료")

# ====================================
# 4️⃣ Mermaid 다이어그램 생성 및 로컬 렌더링
# ====================================
print("\n🎨 워크플로우 그래프 시각화...")

mermaid_file = "workflow_graph.mmd"
png_file = "workflow_graph.png"

try:
    # Mermaid 코드 추출
    mermaid_text = app.get_graph(xray=True).draw_mermaid()

    # Mermaid 파일로 저장
    with open(mermaid_file, "w") as f:
        f.write(mermaid_text)
    print(f"✅ {mermaid_file} 파일로 저장 완료")

    # Mermaid 텍스트 출력
    print("\n📊 Mermaid 그래프 (https://mermaid.live 에서 렌더링 가능):")
    print("-" * 70)
    print(mermaid_text)
    print("-" * 70)

    # mmdc (mermaid-cli)를 사용하여 PNG로 변환 시도
    try:
        result = subprocess.run(
            ["mmdc", "-i", mermaid_file, "-o", png_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ {png_file} 파일로 생성 완료")

            # Jupyter 환경에서 실행 중인 경우 직접 표시
            try:
                display(Image(png_file))
                print("✅ 그래프를 Jupyter에서 표시했습니다")
            except NameError:
                print(f"💡 Jupyter 환경이 아닙니다. 생성된 파일을 확인하세요: {png_file}")
        else:
            print(f"⚠️ PNG 생성 실패: {result.stderr}")
            print(f"대안: {mermaid_file}을 https://mermaid.live 에서 렌더링하세요")
    except FileNotFoundError:
        print("⚠️ mermaid-cli (mmdc)가 설치되지 않았습니다")
        print("설치: npm install -g @mermaid-js/mermaid-cli")
        print(f"대안: {mermaid_file}을 https://mermaid.live 에서 렌더링하세요")
    except subprocess.TimeoutExpired:
        print("⚠️ PNG 생성 타임아웃")
        print(f"대안: {mermaid_file}을 https://mermaid.live 에서 렌더링하세요")

except Exception as e:
    print(f"❌ 워크플로우 시각화 오류: {e}")
    import traceback
    traceback.print_exc()

# 그래프 구조 정보 출력
print("\n📋 워크플로우 구조 정보:")
graph = app.get_graph()
print("노드:")
for node in graph.nodes:
    print(f"  - {node}")
