"""
콩닥식탁 Streamlit 프론트엔드
"""

import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# 환경 변수
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_BASE = f"{BACKEND_URL}/api"

# 페이지 설정
st.set_page_config(
    page_title="콩닥식탁 - 신장 환자 맞춤 식단 챗봇",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .risk-high {
        background-color: #ff4b4b;
        color: white;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .risk-medium {
        background-color: #ffa500;
        color: white;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .risk-low {
        background-color: #4caf50;
        color: white;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .nutrition-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{int(datetime.now().timestamp())}"
if 'show_quiz' not in st.session_state:
    st.session_state.show_quiz = False
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None

# 사이드바
with st.sidebar:
    st.title("⚙️ 설정")

    # 위험도 기준치 설정
    st.subheader("🎯 영양소 제한 기준 (1끼 기준)")
    sodium_limit = st.slider("나트륨 (mg)", 300, 1000, 650, help="권장 제한: 650mg")
    potassium_limit = st.slider("칼륨 (mg)", 300, 1000, 650, help="권장 제한: 650mg")
    phosphorus_limit = st.slider("인 (mg)", 200, 500, 330, help="권장 제한: 330mg")
    protein_limit = st.slider("단백질 (g)", 20, 60, 40, help="권장 제한: 40g")

    st.divider()

    # 대화 기록 관리
    st.subheader("💬 대화 관리")
    if st.button("대화 내역 초기화", type="secondary"):
        st.session_state.messages = []
        st.session_state.show_quiz = False
        st.session_state.quiz_data = None
        st.rerun()

    # 세션 정보
    st.caption(f"세션 ID: {st.session_state.session_id[:20]}...")

    st.divider()

    # 도움말
    with st.expander("📖 사용 가이드"):
        st.markdown("""
        **콩닥식탁 사용법:**

        1. **음식 질문하기**
           - 예: "떡볶이 먹어도 될까요?"
           - 예: "김치찌개는 어떻게 만들면 좋을까요?"

        2. **영양 분석 확인**
           - 나트륨, 칼륨, 인, 단백질 분석
           - 위험도 평가 (🟢안전/🟡주의/🔴위험)

        3. **대체 레시피 확인**
           - 안전한 재료로 대체하는 방법
           - 조리 팁 제공

        4. **퀴즈로 학습**
           - 식단 관리 지식 테스트
           - 정답률 확인
        """)

# 메인 화면
st.title("🥗 콩닥식탁")
st.markdown("### 신장 투석 환자를 위한 맞춤형 식단 관리 챗봇")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["💬 채팅", "📊 영양 분석", "📚 학습 자료"])

# ===== 채팅 탭 =====
with tab1:
    st.markdown("#### 무엇이든 물어보세요!")

    # 채팅 히스토리 표시
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # 영양 정보가 있으면 표시
            if message["role"] == "assistant" and "nutrition" in message:
                nutrition_data = message["nutrition"]

                # 위험도 표시
                if "risk_level" in message:
                    risk_level = message["risk_level"]
                    risk_class = f"risk-{risk_level}"
                    risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(risk_level, "⚪")
                    risk_text = {"high": "위험", "medium": "주의", "low": "안전"}.get(risk_level, "알 수 없음")

                    st.markdown(
                        f'<div class="{risk_class}">{risk_emoji} 위험도: {risk_text.upper()}</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown("")

                # 영양 정보 메트릭
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    delta = nutrition_data.get('sodium', 0) - sodium_limit
                    st.metric(
                        "나트륨",
                        f"{nutrition_data.get('sodium', 0)}mg",
                        f"{delta:+.0f}mg" if delta != 0 else "적정",
                        delta_color="inverse"
                    )
                with col2:
                    delta = nutrition_data.get('potassium', 0) - potassium_limit
                    st.metric(
                        "칼륨",
                        f"{nutrition_data.get('potassium', 0)}mg",
                        f"{delta:+.0f}mg" if delta != 0 else "적정",
                        delta_color="inverse"
                    )
                with col3:
                    delta = nutrition_data.get('phosphorus', 0) - phosphorus_limit
                    st.metric(
                        "인",
                        f"{nutrition_data.get('phosphorus', 0)}mg",
                        f"{delta:+.0f}mg" if delta != 0 else "적정",
                        delta_color="inverse"
                    )
                with col4:
                    delta = nutrition_data.get('protein', 0) - protein_limit
                    st.metric(
                        "단백질",
                        f"{nutrition_data.get('protein', 0)}g",
                        f"{delta:+.0f}g" if delta != 0 else "적정",
                        delta_color="inverse"
                    )

                # 퀴즈 제안
                if message.get("quiz_offer") and idx == len(st.session_state.messages) - 1:
                    if st.button("📝 퀴즈로 복습하기", key=f"quiz_btn_{idx}"):
                        st.session_state.show_quiz = True
                        st.rerun()

    # 사용자 입력
    if prompt := st.chat_input("요리에 대해 물어보세요... (예: 떡볶이 먹어도 될까요?)"):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # API 호출
        with st.chat_message("assistant"):
            with st.spinner("분석 중... 잠시만 기다려 주세요 🔍"):
                try:
                    response = requests.post(
                        f"{API_BASE}/chat",
                        json={
                            "message": prompt,
                            "session_id": st.session_state.session_id,
                            "limits": {
                                "sodium": sodium_limit,
                                "potassium": potassium_limit,
                                "phosphorus": phosphorus_limit,
                                "protein": protein_limit
                            }
                        },
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()

                        # 응답 표시
                        st.markdown(result["answer"])

                        # 응답 저장
                        message_data = {
                            "role": "assistant",
                            "content": result["answer"],
                            "nutrition": result.get("nutrition", {}),
                            "risk_level": result.get("risk_level", "unknown"),
                            "quiz_offer": result.get("quiz_offer", False)
                        }
                        st.session_state.messages.append(message_data)

                        st.rerun()
                    else:
                        st.error(f"서버 오류가 발생했습니다. (상태 코드: {response.status_code})")

                except requests.exceptions.ConnectionError:
                    st.error("⚠️ 백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
                except requests.exceptions.Timeout:
                    st.error("⏱️ 요청 시간이 초과되었습니다. 다시 시도해주세요.")
                except Exception as e:
                    st.error(f"오류 발생: {str(e)}")

# ===== 영양 분석 탭 =====
with tab2:
    st.subheader("📊 영양 성분 시각화")

    if st.session_state.messages:
        # 마지막 분석 결과 가져오기
        last_nutrition = None
        for msg in reversed(st.session_state.messages):
            if msg.get("role") == "assistant" and "nutrition" in msg:
                last_nutrition = msg["nutrition"]
                break

        if last_nutrition:
            col1, col2 = st.columns(2)

            with col1:
                # 도넛 차트
                fig = px.pie(
                    values=[
                        last_nutrition.get('sodium', 0),
                        last_nutrition.get('potassium', 0),
                        last_nutrition.get('phosphorus', 0),
                        last_nutrition.get('protein', 0)
                    ],
                    names=["나트륨", "칼륨", "인", "단백질"],
                    title="영양소 구성 비율",
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # 바 차트 - 기준치 대비
                fig2 = go.Figure()

                nutrients = ["나트륨", "칼륨", "인", "단백질"]
                current_values = [
                    last_nutrition.get('sodium', 0),
                    last_nutrition.get('potassium', 0),
                    last_nutrition.get('phosphorus', 0),
                    last_nutrition.get('protein', 0)
                ]
                limits = [sodium_limit, potassium_limit, phosphorus_limit, protein_limit]

                fig2.add_trace(go.Bar(name='현재값', x=nutrients, y=current_values, marker_color='lightblue'))
                fig2.add_trace(go.Bar(name='기준치', x=nutrients, y=limits, marker_color='coral'))

                fig2.update_layout(
                    title="기준치 대비 영양소 함량",
                    barmode='group',
                    yaxis_title="함량",
                    xaxis_title="영양소"
                )

                st.plotly_chart(fig2, use_container_width=True)

            # 상세 정보
            st.markdown("#### 상세 영양 정보")
            detail_col1, detail_col2 = st.columns(2)

            with detail_col1:
                st.info(f"""
                **발견된 재료:** {', '.join(last_nutrition.get('found_ingredients', []))}
                """)

            with detail_col2:
                if last_nutrition.get('missing_ingredients'):
                    st.warning(f"""
                    **정보 없는 재료:** {', '.join(last_nutrition.get('missing_ingredients', []))}
                    """)

        else:
            st.info("아직 분석한 음식이 없습니다. 채팅 탭에서 음식을 검색해주세요.")
    else:
        st.info("아직 분석한 음식이 없습니다. 채팅 탭에서 음식을 검색해주세요.")

# ===== 학습 자료 탭 =====
with tab3:
    st.subheader("📚 추천 학습 자료")

    search_keyword = st.text_input(
        "검색어를 입력하세요",
        "저염식 레시피",
        help="신장 환자 식단 관련 키워드를 입력하세요"
    )

    if st.button("🔍 자료 검색", type="primary"):
        with st.spinner("자료를 검색 중..."):
            try:
                response = requests.get(
                    f"{API_BASE}/resources/recommend",
                    params={"keyword": search_keyword, "limit": 5},
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    resources = result.get("resources", [])

                    if resources:
                        for resource in resources:
                            with st.container():
                                st.markdown(f"### [{resource['title']}]({resource['url']})")
                                st.markdown(f"**출처:** {resource['source']}")
                                st.markdown(f"**설명:** {resource['description']}")

                                # 관련성 별점
                                score = resource.get('relevance_score', 0)
                                stars = '⭐' * int(score * 5)
                                st.markdown(f"**관련성:** {stars} ({score:.2f})")

                                st.divider()
                    else:
                        st.warning("검색 결과가 없습니다.")

                else:
                    st.error("자료 검색에 실패했습니다.")

            except Exception as e:
                st.error(f"검색 오류: {str(e)}")

# 퀴즈 모달
if st.session_state.show_quiz:
    st.markdown("---")
    st.subheader("📝 복습 퀴즈")

    # 퀴즈 생성 (최초 1회만)
    if st.session_state.quiz_data is None:
        with st.spinner("퀴즈 생성 중..."):
            try:
                # 마지막 메시지에서 주제 추출
                last_user_msg = next(
                    (msg["content"] for msg in reversed(st.session_state.messages) if msg["role"] == "user"),
                    "신장 환자 식단"
                )

                response = requests.post(
                    f"{API_BASE}/quiz/generate",
                    json={
                        "topic": last_user_msg,
                        "difficulty": "medium",
                        "count": 3
                    },
                    timeout=15
                )

                if response.status_code == 200:
                    st.session_state.quiz_data = response.json()
                else:
                    st.error("퀴즈 생성 실패")
                    st.session_state.show_quiz = False
                    st.rerun()

            except Exception as e:
                st.error(f"퀴즈 생성 오류: {str(e)}")
                st.session_state.show_quiz = False
                st.rerun()

    # 퀴즈 표시
    if st.session_state.quiz_data:
        questions = st.session_state.quiz_data.get("questions", [])

        for idx, q in enumerate(questions):
            st.markdown(f"**문제 {idx + 1}:** {q['question']}")

            # 문제 유형에 따라 입력 방식 변경
            if q.get('question_type') == 'multiple_choice' and q.get('options'):
                answer = st.radio(
                    "답을 선택하세요:",
                    q['options'],
                    key=f"quiz_{idx}"
                )
            else:
                answer = st.text_input(
                    "답을 입력하세요:",
                    key=f"quiz_{idx}"
                )

            if st.button(f"제출", key=f"submit_{idx}"):
                is_correct = answer.strip().lower() == q['correct_answer'].strip().lower()

                if is_correct:
                    st.success(f"✅ 정답입니다! {q.get('explanation', '')}")
                else:
                    st.error(f"❌ 틀렸습니다. 정답은 '{q['correct_answer']}'입니다. {q.get('explanation', '')}")

            st.divider()

        if st.button("퀴즈 닫기"):
            st.session_state.show_quiz = False
            st.session_state.quiz_data = None
            st.rerun()

# 푸터
st.markdown("---")
st.caption("💡 콩닥식탁 v1.0 | 신장 투석 환자를 위한 맞춤형 식단 관리 챗봇")
