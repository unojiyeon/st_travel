import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib
import squarify
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# 페이지 설정
st.set_page_config(page_title="중국인 관광객 분석 대시보드", layout="wide")

# 데이터 로드 함수
@st.cache_data
def load_data(file_path):
    encodings = ['utf-8', 'cp949', 'euc-kr']
    for enc in encodings:
        try:
            return pd.read_csv(file_path, encoding=enc)
        except:
            continue
    return pd.read_csv(file_path)

# 데이터 로드 환경 설정 (로컬 vs 배포 환경 호환)
DATA_PREFIX = "p1_airbnb/" if os.path.exists("p1_airbnb") else ""

# 데이터 로드
try:
    df_country = load_data(f"{DATA_PREFIX}국가별 관광소비 유형.csv")
    df_consume = load_data(f"{DATA_PREFIX}중국 관광객 신용카드 관광소비 유형.csv")
    df_visit = load_data(f"{DATA_PREFIX}중국 관광객 지역별 방문비율.csv")
    df_cons_region = load_data(f"{DATA_PREFIX}중국 관광객 지역별 신용카드 소비비율_f.csv")
except Exception as e:
    st.error(f"데이터 파일 로드 중 오류 발생: {e}")
    st.info("GitHub 레포지토리에 CSV 파일들이 올바른 위치에 업로드되었는지 확인해주세요.")
    st.stop()

# 사이드바
st.sidebar.title("💳 관광 데이터 분석")
st.sidebar.info("중국인 관광객의 소비 패턴과 서울 지역별 수익 효율성을 분석하여 최적의 숙박 운영 전략을 제안합니다.")

menu = st.sidebar.radio("메뉴 선택", ["데이터 개요", "소비 패턴 분석", "서울 지역 분석", "수익 전략 제안"])

# 1. 데이터 개요
if menu == "데이터 개요":
    st.title("📊 중국인 관광객 데이터 EDA 개요")
    st.markdown("""
    ### 분석의 핵심 질문
    > **"중국인 관광 수요 구조를 고려할 때, 서울 어느 지역에서 어떤 숙박 유형으로 운영해야 수익성이 높은가?"**
    
    중국인은 방문객 1위(21.1%), 관광소비 1위(29.4%)를 차지하는 핵심 시장이지만, 실제 숙박 공급은 수요와 지역·유형 모두 불일치하고 있습니다. 이 불균형 지점을 데이터를 통해 분석합니다.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("국가별 관광소비 비중")
        fig = px.pie(df_country, values='소비 비율', names='국가', title='국가별 소비 점유율', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("중국인 업종별 소비 유형")
        df_consume_filtered = df_consume[df_consume['비율'] > 0]
        fig = px.treemap(df_consume_filtered, path=['업종별'], values='비율', title='중국인 소비 항목 (Treemap)')
        st.plotly_chart(fig, use_container_width=True)

# 2. 소비 패턴 분석
elif menu == "소비 패턴 분석":
    st.title("🛍️ 업종별 소비 상세 분석")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("국가별 소비 TOP 15")
        df_country_top = df_country.sort_values(by='소비 비율', ascending=True).tail(15)
        fig = px.bar(df_country_top, x='소비 비율', y='국가', orientation='h', text='소비 비율', 
                     color='소비 비율', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.markdown("### 주요 인사이트")
        st.write("- **중국(29.4%)**이 압도적 1위로 미국, 일본보다 2배 이상 높음")
        st.write("- **쇼핑(51.7%)**이 전체 소비의 절반 이상")
        st.write("- **의료웰니스(16.9%)**가 주요 고부가가치 항목으로 부상")
        st.write("- 상대적으로 낮은 **숙박업(11.5%)** 비중 → 성장 잠재력 존재")

# 3. 서울 지역 분석
elif menu == "서울 지역 분석":
    st.title("📍 서울 자치구별 수요-공급 분석")
    
    seoul_visit = df_visit[df_visit['시도명'] == '서울특별시'].copy()
    seoul_cons = df_cons_region[df_cons_region['시도명'] == '서울특별시'].copy().rename(columns={'시군구 명': '시군구명'})
    
    merged = pd.merge(seoul_visit[['시군구명', '시군구 방문자 비율']], 
                      seoul_cons[['시군구명', '시군구 소비 비율']], on='시군구명')
    
    # 방문 vs 소비 이중축 차트 (Plotly)
    st.subheader("자치구별 방문 비율 vs 소비 비율")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=merged['시군구명'], y=merged['시군구 방문자 비율'], name="방문 비율"), secondary_y=False)
    fig.add_trace(go.Scatter(x=merged['시군구명'], y=merged['시군구 소비 비율'], name="소비 비율", mode='lines+markers', line=dict(color='red')), secondary_y=True)
    
    fig.update_layout(title_text="서울 구별 방문 vs 소비 비교", xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # 자치구 데이터 테이블
    if st.checkbox("전체 데이터 보기"):
        st.dataframe(merged.sort_values(by='시군구 소비 비율', ascending=False), use_container_width=True)

# 4. 수익 전략 제안
elif menu == "수익 전략 제안":
    st.title("💡 자치구별 수익 최적화 전략")
    
    # 효율성 지수 계산
    seoul_visit = df_visit[df_visit['시도명'] == '서울특별시'].copy()[['시군구명', '시군구 방문자 비율']]
    seoul_cons = df_cons_region[df_cons_region['시도명'] == '서울특별시'].copy()[['시군구 명', '시군구 소비 비율']].rename(columns={'시군구 명': '시군구명'})
    merged = pd.merge(seoul_visit, seoul_cons, on='시군구명')
    merged['효율성 지수'] = merged['시군구 소비 비율'] / merged['시군구 방문자 비율']
    merged = merged.sort_values(by='효율성 지수', ascending=False)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("수익 효율성 지수 (Efficiency Index)")
        fig = px.bar(merged, x='효율성 지수', y='시군구명', orientation='h', color='효율성 지수', color_continuous_scale='coolwarm')
        fig.add_vline(x=1.0, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("지역별 타겟 전략")
        strategy_data = {
            '자치구': ['강남구', '중구', '마포구', '서초구', '종로구'],
            '추천 테마': ['의료/럭셔리 쇼핑', '대중 쇼핑/관광', 'MZ 문화/트렌드', '비즈니스/의료', '역사/전통문화'],
            '숙소 모델': ['프리미엄 펜트하우스', '대형 게스트하우스', '부티크 디자인 하우스', '비즈니스 스튜디오', '한옥 스테이']
        }
        st.table(pd.DataFrame(strategy_data))
    
    st.markdown("""
    ---
    ### 🏁 최종 결론
    - **강남구**: 방문객 대비 소비 효율이 **3.5배**로 가장 높음. 의료 관광 및 명품 쇼핑객을 겨냥한 **고단가 프리미엄 숙소** 운영이 가장 수익성 높음.
    - **중구**: 절대적인 소비량 1위. 쇼핑 물량이 많은 단체 및 가족 관광객을 위한 **수하물 편의성이 강화된 대형 숙소** 적합.
    - **공급 GAP 해소**: 단순 숙박을 넘어 지역별 소비 특성(강남-회복, 중구-쇼핑)을 결합한 **특화 서비스**가 수익 극대화의 열쇠.
    """)

st.sidebar.markdown("---")
st.sidebar.caption("Data Source: 한국관광공사 & 신용카드 데이터 (2025/2026)")
