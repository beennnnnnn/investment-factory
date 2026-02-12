import streamlit as st
import google.generativeai as genai
import feedparser
from newspaper import Article
import urllib.parse
import re

# --- 1. UI 설정 ---
st.set_page_config(page_title="머스크노미 랩 (Muskonomy Lab)", layout="wide", page_icon="🚀")
st.title("🚀 머스크노미 랩 (Muskonomy Lab)")
st.caption("📱 데이터 기반의 정교한 분석 리포트 공장")

# --- 2. 사이드바: 검색어 최적화 (검색 성공률을 위해 키워드 단축) ---
with st.sidebar:
    st.header("🔑 보안 세션")
    user_api_key = st.text_input("Gemini API 키 입력:", type="password")
    
    st.divider()
    st.header("⚙️ 정보 수집 설정")
    
    # [수정] 검색이 잘 되도록 키워드를 핵심 종목명 위주로 짧게 수정했습니다.
    DEFAULT_THEMES = {
        "🇰🇷 국장 시황 (코스피/코스닥)": "코스피 코스닥 시황",
        "🌎 거시경제 (환율/금리)": "환율 금리 전망",
        "💾 반도체 (삼성/SK/한미)": "삼성전자 SK하이닉스 한미반도체",
        "🔋 2차전지 (SDI/에코프로)": "삼성SDI 에코프로 에코프로비엠",
        "🚗 모빌리티 (현대차/만도)": "현대차 HL만도",
        "🤖 로봇 (레인보우)": "레인보우로보틱스 로봇",
        "🚀 방산/우주 (한화에어로)": "한화에어로스페이스 방산",
        "⚡ 중공업 (효성중공업)": "효성중공업 전력",
        "🧠 머스크노미 (Tesla/xAI)": "Tesla xAI Elon Musk",
        "📈 나스닥/미장 시황": "Nasdaq 100 stock",
        "₿ 비트코인/코인": "Bitcoin crypto news",
        "➕ 직접 입력": "custom"
    }
    
    selected_theme = st.selectbox("분석 주제 선택:", list(DEFAULT_THEMES.keys()))
    search_keyword = st.text_input("검색어:") if selected_theme == "➕ 직접 입력" else DEFAULT_THEMES[selected_theme]
    news_count = st.slider("국가별 참고 뉴스 개수", 1, 5, 3)

# --- 3. 문체 스타일 가이드 ---
PRESET_STYLES = {
    "🌌 로켓테슬라 스타일 (@rklb_invest)": "논리적 인과관계를 중시하는 전략적 스토리텔링. '우연은 없다, 의도만 존재할 뿐'이라는 문구를 도입부에 활용하며, 깊이 있는 타래 형식을 선호함.",
    "☀️ 미국개미 스타일 (@USAnt_IDEA)": "열정적이고 친절한 멘토링. 핵심 데이터를 명확하게 짚어주며 독자들을 응원하는 긍정적인 톤. 마무리 문구 'Powered by #USAnt' 고수.",
    "💎 반보 스타일 (@Banbo_Insight)": "비유와 예시를 활용한 다정하고 쉬운 설명. [제목] 형식을 반드시 사용하고 번호를 매겨 정보를 구조화함.",
    "➕ 직접 스타일 업로드": "custom"
}

st.subheader("✍️ 분석 페르소나 선택")
selected_style_key = st.selectbox("누구의 문체로 분석할까요?", list(PRESET_STYLES.keys()))
style_content = PRESET_STYLES[selected_style_key]

# --- 4. 뉴스 수집 함수 ---
def fetch_global_news(keyword, lang, geo, count):
    encoded_q = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl={lang}&gl={geo}&ceid={geo}:{lang}"
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:count]:
        try:
            article = Article(entry.link)
            article.download(); article.parse()
            if len(article.text) > 200: # 텍스트가 너무 짧은 광고성 링크 제외
                results.append({"title": entry.title, "link": entry.link, "image": article.top_image, "text": article.text[:1200]})
        except: continue
    return results

# --- 5. 실행 로직 ---
if st.button("🚀 분석 리포트 생성 시작"):
    if not user_api_key or not search_keyword:
        st.error("API 키와 주제를 확인해 주세요.")
    else:
        try:
            genai.configure(api_key=user_api_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            with st.spinner("데이터 수집 및 번역 중..."):
                # 미국 뉴스용 검색어 번역
                us_keyword = model.generate_content(f"Translate '{search_keyword}' to a short English news search keyword. Keyword only.").text.strip()
                
                kr_news = fetch_global_news(search_keyword, "ko", "KR", news_count)
                us_news = fetch_global_news(us_keyword, "en", "US", news_count)
                all_news = kr_news + us_news

            if not all_news:
                st.warning(f"'{search_keyword}'에 대한 최신 뉴스를 찾을 수 없습니다. 검색어를 더 짧게 수정해 보세요.")
            else:
                # 시각화
                st.subheader("📰 분석 데이터 원본")
                cols = st.columns(3)
                for idx, news in enumerate(all_news):
                    with cols[idx % 3]:
                        if news['image']: st.image(news['image'], use_container_width=True)
                        st.markdown(f"**[{news['title']}]({news['link']})**")
                
                with st.spinner("리포트 작성 중..."):
                    context = "\n".join([f"기사제목: {n['title']}\n내용: {n['text']}" for n in all_news])
                    final_prompt = f"""
                    [지침]:
                    - 반드시 제공된 [뉴스 데이터]의 내용만 분석하라.
                    - 데이터가 부족해도 절대 다른 종목(테슬라 등)을 끌어오지 마라.
                    - 오직 [말투 가이드]의 문체(톤, 형식)만 가져와서 친절하게 작성하라.

                    [뉴스 데이터]:
                    {context}
                    
                    [말투 가이드]:
                    {style_content}
                    """
                    response = model.generate_content(final_prompt)
                    
                    st.divider()
                    st.subheader("✅ 머스크노미 랩 분석 결과")
                    st.code(response.text, language='text')
                    st.balloons()
        except Exception as e:
            st.error(f"오류 발생: {e}")
