import streamlit as st
import google.generativeai as genai
import feedparser
from newspaper import Article
import urllib.parse
import re

# --- 1. UI 및 보안 설정: 앱 이름 반영 ---
st.set_page_config(page_title="머스크노미 랩 (Muskonomy Lab)", layout="wide", page_icon="🚀")
st.title("🚀 머스크노미 랩 (Muskonomy Lab)")
st.caption("📱 테슬라, SpaceX, xAI의 유기적 연결과 글로벌 마켓을 분석하는 '딸깍' 공장")

# --- 2. 사이드바: 모든 종목 카테고리 및 뉴스 설정 (V2.7 카테고리 전체 유지) ---
with st.sidebar:
    st.header("🔑 보안 세션")
    user_api_key = st.text_input("Gemini API 키 입력:", type="password", help="서버에 저장되지 않으며 브라우저 종료 시 파기됩니다.")
    
    st.divider()
    st.header("⚙️ 정보 수집 설정")
    
    # 요청하신 모든 국내외 종목 및 거시경제 카테고리 (삭제 없음!)
    DEFAULT_THEMES = {
        "🧠 머스크노미 (Tesla/SpaceX/xAI)": "Tesla SpaceX xAI news Elon Musk Starlink",
        "🌎 거시경제 (환율/금리/채권)": "환율 금리 국채금리 거시경제 지표 전망 뉴스",
        "🇰🇷 국장 시황 (코스피/코스닥)": "코스피 코스닥 시황 증시 분석 뉴스",
        "💾 반도체 (삼성/SK/한미)": "삼성전자 SK하이닉스 한미반도체 반도체 뉴스",
        "🔋 2차전지 (SDI/에코프로)": "삼성SDI 에코프로 에코프로비엠 배터리 뉴스",
        "🚗 모빌리티 (현대차/만도)": "현대차 HL만도 자동차 모빌리티 뉴스",
        "🤖 로봇 (레인보우/옵티머스)": "레인보우로보틱스 로봇 산업 뉴스 Tesla Optimus",
        "🚀 방산/우주 (한화에어로/로켓랩)": "한화에어로스페이스 Rocket Lab RKLB news 방산 우주 뉴스",
        "⚡ 중공업/에너지 (효성중공업)": "효성중공업 전력 인프라 중공업 뉴스",
        "📈 나스닥/미장 시황": "Nasdaq 100 stock market news",
        "₿ 비트코인/코인": "Bitcoin crypto market news ETF",
        "➕ 직접 입력": "custom"
    }
    
    selected_theme = st.selectbox("분석 주제 선택:", list(DEFAULT_THEMES.keys()))
    search_keyword = st.text_input("검색어:") if selected_theme == "➕ 직접 입력" else DEFAULT_THEMES[selected_theme]
    # 국가별 3개씩 수집 제안하신 설정 유지
    news_count = st.slider("국가별 참고 뉴스 개수 (한/미 각각)", 1, 5, 3)

# --- 3. 분석 페르소나 스타일 설정 (사용자 제공 텍스트 기반) ---
PRESET_STYLES = {
    "🌌 로켓테슬라 스타일 (@rklb_invest)": "전략적 스토리텔링. '우연은 없다, 의도만 존재할 뿐' 문구 활용. 테슬라와 우주의 연결성 강조.",
    "🔥 미국개미 스타일 (@USAnt_IDEA)": "공격적이고 강한 확신. '똑똑히 들어라' 사용. 마무리 'Powered by #USAnt'.",
    "💎 반보 스타일 (@Banbo_Insight)": "비유(맛집 등) 활용 및 번호 매기기. [제목] 형식 사용. 친절한 분석.",
    "➕ 직접 스타일 업로드": "custom"
}

st.subheader("✍️ 분석 페르소나 선택")
selected_style_key = st.selectbox("누구의 시각으로 분석할까요?", list(PRESET_STYLES.keys()))

if selected_style_key == "➕ 직접 스타일 업로드":
    uploaded_file = st.file_uploader("벤치마킹 메모장(.txt) 업로드", type=['txt'])
    style_content = uploaded_file.getvalue().decode("utf-8") if uploaded_file else ""
else:
    style_content = PRESET_STYLES[selected_style_key]

# --- 4. 뉴스 수집 함수 (이미지 및 링크 포함) ---
def fetch_global_news(keyword, lang, geo, count):
    # 공백 오류 방지를 위한 URL 인코딩
    encoded_q = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl={lang}&gl={geo}&ceid={geo}:{lang}"
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:count]:
        try:
            article = Article(entry.link)
            article.download()
            article.parse()
            results.append({
                "title": entry.title,
                "link": entry.link,
                "image": article.top_image,
                "text": article.text[:1000]
            })
        except: continue
    return results

# --- 5. 메인 로직 실행 ---
if st.button("🚀 한/미 뉴스 종합 분석 및 포스팅 생성"):
    if not user_api_key or not search_keyword:
        st.error("API 키와 검색어를 확인해 주세요.")
    else:
        try:
            genai.configure(api_key=user_api_key)
            # 2026년 기준 최신 모델 별칭 사용
            model = genai.GenerativeModel('gemini-flash-latest')
            
            # (1) 미국 뉴스용 키워드 번역
            with st.spinner("미국 뉴스 검색을 위해 키워드 번역 중..."):
                trans_prompt = f"Translate '{search_keyword}' into a simple English news search keyword. Just provide the keyword."
                us_keyword = model.generate_content(trans_prompt).text.strip()
            
            # (2) 한/미 뉴스 동시 수집 (3+3)
            with st.spinner(f"한/미 양국에서 최신 소식을 가져오는 중..."):
                kr_news = fetch_global_news(search_keyword, "ko", "KR", news_count)
                us_news = fetch_global_news(us_keyword, "en", "US", news_count)
                all_news = kr_news + us_news

            # (3) 시각화: 수집된 뉴스 이미지와 링크 표시
            st.subheader("📰 분석 데이터 소스 (이미지 & 링크)")
            news_cols = st.columns(3)
            for idx, news in enumerate(all_news):
                with news_cols[idx % 3]:
                    if news['image']:
                        st.image(news['image'], use_container_width=True)
                    st.markdown(f"**[{news['title']}]({news['link']})**")
            
            # (4) 최종 포스팅 생성
            with st.spinner("머스크노미 관점에서 글로벌 데이터 분석 중..."):
                context = "\n".join([f"뉴스데이터: {n['text']}" for n in all_news])
                final_prompt = f"""
                [분석 데이터]:
                {context}
                
                [말투 가이드]:
                {style_content}
                
                [지침]:
                1. 한/미 양국의 정보를 종합하여 통찰력 있는 포스팅을 써줘.
                2. 선택된 말투의 특징(이모지, 어투, 줄바꿈)을 100% 반영해.
                3. 마지막에는 영어 이미지 프롬프트도 1줄 추가해줘.
                """
                response = model.generate_content(final_prompt)
                
                st.divider()
                st.subheader("✅ 머스크노미 랩 분석 결과")
                st.code(response.text, language='text')
                st.balloons()
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
