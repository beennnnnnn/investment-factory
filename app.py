import streamlit as st
import google.generativeai as genai
import feedparser
from newspaper import Article
import urllib.parse
import re

# --- 1. UI 설정 (이름 및 보안 캡션 유지) ---
st.set_page_config(page_title="머스크노미 랩 (Muskonomy Lab)", layout="wide", page_icon="🚀")
st.title("🚀 머스크노미 랩 (Muskonomy Lab)")
st.caption("📱 글로벌 데이터를 분석하여 주제에 100% 집중한 전문가 리포트를 생성합니다.")

# --- 2. 사이드바: 모든 종목 카테고리 (삭제 없이 전체 유지) ---
with st.sidebar:
    st.header("🔑 보안 세션")
    user_api_key = st.text_input("Gemini API 키 입력:", type="password", help="서버에 저장되지 않는 휘발성 입력 방식입니다.")
    
    st.divider()
    st.header("⚙️ 정보 수집 설정")
    
    # [V2.7 기준] 요청하신 모든 국내외 종목 및 거시경제 카테고리 완벽 보존
    DEFAULT_THEMES = {
        "🧠 머스크노미 (Tesla/SpaceX/xAI)": "Tesla SpaceX xAI news Elon Musk",
        "🇰🇷 국장 시황 (코스피/코스닥)": "코스피 코스닥 시황 증시 분석 뉴스",
        "🌎 거시경제 (환율/금리/채권)": "환율 금리 국채금리 거시경제 지표 전망 뉴스",
        "💾 반도체 (삼성/SK/한미)": "삼성전자 SK하이닉스 한미반도체 반도체 뉴스",
        "🔋 2차전지 (SDI/에코프로)": "삼성SDI 에코프로 에코프로비엠 배터리 뉴스",
        "🚗 모빌리티 (현대차/만도)": "현대차 HL만도 자동차 모빌리티 뉴스",
        "🤖 로봇 (레인보우)": "레인보우로보틱스 로봇 산업 뉴스",
        "🚀 방산/우주 (한화에어로)": "한화에어로스페이스 방산 우주 뉴스",
        "⚡ 중공업/에너지 (효성중공업)": "효성중공업 전력 인프라 중공업 뉴스",
        "📈 나스닥/미장 시황": "Nasdaq 100 stock market news",
        "₿ 비트코인/코인": "Bitcoin crypto market news ETF",
        "➕ 직접 입력": "custom"
    }
    
    selected_theme = st.selectbox("분석 주제 선택:", list(DEFAULT_THEMES.keys()))
    search_keyword = st.text_input("검색어:") if selected_theme == "➕ 직접 입력" else DEFAULT_THEMES[selected_theme]
    news_count = st.slider("국가별 참고 뉴스 개수 (한/미 각각)", 1, 5, 3)

# --- 3. 분석 페르소나 스타일 (문체 중심의 친절한 버전으로 수정) ---
PRESET_STYLES = {
    "🌌 로켓테슬라 스타일 (@rklb_invest)": "논리적 인과관계를 중시하는 전략적 스토리텔링. '우연은 없다, 의도만 존재할 뿐'이라는 문구를 도입부에 활용하며, 깊이 있는 타래 형식을 선호함.",
    "☀️ 미국개미 스타일 (@USAnt_IDEA)": "열정적이고 친절한 멘토링. 핵심 데이터를 명확하게 짚어주며 독자들을 응원하는 긍정적인 톤. 마무리 문구 'Powered by #USAnt' 고수.",
    "💎 반보 스타일 (@Banbo_Insight)": "비유와 예시를 활용한 다정하고 쉬운 설명. [제목] 형식을 반드시 사용하고 번호를 매겨 정보를 구조화함. 다정한 가이드 톤.",
    "➕ 직접 스타일 업로드": "custom"
}

st.subheader("✍️ 분석 페르소나 선택")
selected_style_key = st.selectbox("누구의 문체로 분석할까요?", list(PRESET_STYLES.keys()))

style_content = ""
if selected_style_key == "➕ 직접 스타일 업로드":
    uploaded_file = st.file_uploader("메모장 업로드", type=['txt'])
    if uploaded_file: style_content = uploaded_file.getvalue().decode("utf-8")
else:
    style_content = PRESET_STYLES[selected_style_key]

# --- 4. 뉴스 수집 함수 (URL 인코딩 및 이미지/링크 기능 유지) ---
def fetch_global_news(keyword, lang, geo, count):
    # 공백 오류 방지를 위한 quote 처리 유지
    encoded_q = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl={lang}&gl={geo}&ceid={geo}:{lang}"
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:count]:
        try:
            article = Article(entry.link)
            article.download(); article.parse()
            results.append({
                "title": entry.title, "link": entry.link,
                "image": article.top_image, "text": article.text[:1000]
            })
        except: continue
    return results

# --- 5. 실행 로직 (글로벌 3+3 분석 및 시각화 유지) ---
if st.button("🚀 글로벌 뉴스 종합 분석 시작"):
    if not user_api_key or not search_keyword:
        st.error("API 키와 주제를 확인해 주세요.")
    else:
        try:
            genai.configure(api_key=user_api_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            with st.spinner("데이터 수집 중..."):
                # 한글 검색어를 영어로 번역하여 미국 뉴스 수집
                us_keyword_prompt = f"Translate '{search_keyword}' to English for news search. Return only the keyword."
                us_keyword = model.generate_content(us_keyword_prompt).text.strip()
                
                # 한/미 뉴스 각각 수집 (삭제 없음!)
                kr_news = fetch_global_news(search_keyword, "ko", "KR", news_count)
                us_news = fetch_global_news(us_keyword, "en", "US", news_count)
                all_news = kr_news + us_news

            # 시각화: 이미지 및 링크 레이아웃 유지
            st.subheader("📰 분석 데이터 원본 (이미지 & 링크)")
            cols = st.columns(3)
            for idx, news in enumerate(all_news):
                with cols[idx % 3]:
                    if news['image']: st.image(news['image'], use_container_width=True)
                    st.markdown(f"**[{news['title']}]({news['link']})**")
            
            with st.spinner("주제에 100% 집중하여 분석 리포트 작성 중..."):
                context = "\n".join([f"뉴스내용: {n['text']}" for n in all_news])
                # 강력한 주제 집중 지침 적용
                final_prompt = f"""
                [필독 지침]:
                - 너는 오직 아래 제공된 [뉴스 데이터]의 내용만 분석해야 한다.
                - 데이터에 없는 종목을 억지로 연결하거나 언급하지 마라.
                - 선택된 [말투 가이드]의 문체와 형식만 가져와서 친절하게 작성해라.

                [뉴스 데이터]:
                {context}
                
                [말투 가이드]:
                {style_content}
                
                분석 결과(마지막에 영어 이미지 프롬프트 1줄 추가):
                """
                response = model.generate_content(final_prompt)
                
                st.divider()
                st.subheader("✅ 머스크노미 랩 분석 결과")
                st.code(response.text, language='text')
                st.balloons()
        except Exception as e:
            st.error(f"오류 발생: {e}")
