import streamlit as st
import google.generativeai as genai
import feedparser
from newspaper import Article
import urllib.parse
import re

# --- UI 설정 ---
st.set_page_config(page_title="Safe Investment Factory", layout="wide", page_icon="🛡️")
st.title("📱 이동식 투자 포스팅 생성기 (V2.7)")
st.caption("⚠️ 보안 모드: API 키는 저장되지 않으며, 매크로(환율/금리) 카테고리가 추가되었습니다.")

# --- [사이드바] 설정 ---
with st.sidebar:
    st.header("🔑 보안 세션 시작")
    user_api_key = st.text_input("Gemini API 키를 입력하세요:", type="password")
    st.caption("[키 발급처](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    st.header("⚙️ 정보 수집")
    
    # 거시경제 지표를 포함한 전체 테마 구성
    DEFAULT_THEMES = {
        "🌎 거시경제 (환율/금리/채권)": "환율 금리 국채금리 거시경제 지표 전망 뉴스",
        "🇰🇷 국장 시황 (코스피/코스닥)": "코스피 코스닥 시황 증시 분석 뉴스",
        "💾 반도체 (삼성/SK/한미)": "삼성전자 SK하이닉스 한미반도체 반도체 뉴스",
        "🔋 2차전지 (SDI/에코프로)": "삼성SDI 에코프로 에코프로비엠 배터리 뉴스",
        "🚗 모빌리티 (현대차/만도)": "현대차 HL만도 자동차 모빌리티 뉴스",
        "🤖 로봇 (레인보우)": "레인보우로보틱스 로봇 산업 뉴스",
        "🚀 방산/우주 (한화에어로)": "한화에어로스페이스 방산 우주 뉴스",
        "⚡ 중공업/에너지 (효성중공업)": "효성중공업 전력 인프라 중공업 뉴스",
        "📈 나스닥/미장 시황": "Nasdaq 100 stock market news",
        "🚗 테슬라 (TSLA)": "Tesla TSLA stock news FSD",
        "🚀 로켓랩 (RKLB)": "Rocket Lab RKLB news stock",
        "🧠 일론 머스크 & SpaceX": "Elon Musk SpaceX xAI news",
        "₿ 비트코인/코인": "Bitcoin crypto market news",
        "➕ 직접 입력": "custom"
    }
    
    selected_theme = st.selectbox("오늘의 뉴스 주제:", list(DEFAULT_THEMES.keys()))
    search_keyword = st.text_input("검색어:") if selected_theme == "➕ 직접 입력" else DEFAULT_THEMES[selected_theme]
    news_count = st.slider("참고 뉴스 개수", 1, 5, 3)

# --- [내재화] 벤치마킹 스타일 프리셋 ---
PRESET_STYLES = {
    "💎 반보 스타일 (@Banbo_Insight)": "비유(맛집 등) 활용 및 번호 매기기. [제목] 형식 사용.",
    "🔥 미국개미 스타일 (@USAnt_IDEA)": "공격적이고 강한 확신. '똑똑히 들어라' 사용. 마무리 'Powered by #USAnt'.",
    "🌌 로켓테슬라 스타일 (@rklb_invest)": "전략적 스토리텔링. '우연은 없다, 의도만 존재할 뿐' 문구 활용.",
    "➕ [커스텀] 메모장 업로드": "custom"
}

st.subheader("✍️ 타겟 스타일 선택")
selected_style_key = st.selectbox("누구의 영혼을 불러올까요?", list(PRESET_STYLES.keys()))

if selected_style_key == "➕ [커스텀] 메모장 업로드":
    uploaded_file = st.file_uploader("벤치마킹 메모장(.txt) 업로드", type=['txt'])
    selected_style_content = uploaded_file.getvalue().decode("utf-8") if uploaded_file else ""
else:
    selected_style_content = PRESET_STYLES[selected_style_key]

# --- 실행 버튼 ---
if st.button("🚀 포스팅 생성 (딸깍!)"):
    if not user_api_key:
        st.error("보안을 위해 API 키를 먼저 입력해 주세요!")
    elif not selected_style_content:
        st.error("말투 스타일이 설정되지 않았습니다.")
    else:
        try:
            genai.configure(api_key=user_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            with st.spinner("최신 정보를 수집하여 전문가의 글로 변환 중..."):
                encoded_keyword = urllib.parse.quote(search_keyword)
                rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
                
                feed = feedparser.parse(rss_url)
                news_data = ""
                
                if not feed.entries:
                    st.warning("수집된 뉴스가 없습니다. 키워드를 확인해 주세요.")
                else:
                    for entry in feed.entries[:news_count]:
                        try:
                            article = Article(entry.link)
                            article.download()
                            article.parse()
                            news_data += f"\n제목: {entry.title}\n내용: {article.text[:1000]}\n---"
                        except: continue

                    prompt = f"뉴스 정보: {news_data}\n\n말투 스타일 가이드: {selected_style_content}\n\n위 스타일을 복제해 포스팅을 써줘. 이미지 프롬프트(영어)도 1줄 추가해."
                    response = model.generate_content(prompt)
                    
                    st.divider()
                    st.subheader("✅ 생성된 결과물")
                    st.code(response.text, language='text')
                    st.balloons()
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
