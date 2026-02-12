import streamlit as st
import google.generativeai as genai
import feedparser
from newspaper import Article, Config
import urllib.parse

# --- 1. UI 설정 ---
st.set_page_config(page_title="머스크노미 랩 (Muskonomy Lab)", layout="wide", page_icon="🚀")
st.title("🚀 머스크노미 랩 (Muskonomy Lab)")
st.caption("📱 스타일 수정 후 발생한 수집 오류를 해결한 복구 버전입니다.")

# --- 2. 사이드바: 설정 (잘 작동하던 키워드로 복구) ---
with st.sidebar:
    st.header("🔑 보안 세션")
    user_api_key = st.text_input("Gemini API 키 입력:", type="password")
    
    st.divider()
    st.header("⚙️ 정보 수집 설정")
    
    # 아까 잘 됐던 시절의 직관적인 키워드들로 다시 되돌렸습니다.
    DEFAULT_THEMES = {
        "🧠 머스크노미 (Tesla/xAI)": "Tesla xAI Elon Musk",
        "🇰🇷 국장 시황 (코스피/코스닥)": "코스피 코스닥 시황",
        "🌎 거시경제 (환율/금리)": "환율 금리",
        "💾 반도체 (삼성/SK/한미)": "삼성전자 SK하이닉스 한미반도체",
        "🔋 2차전지 (SDI/에코프로)": "삼성SDI 에코프로 에코프로비엠",
        "🚗 모빌리티 (현대차/만도)": "현대차 HL만도",
        "🤖 로봇 (레인보우)": "레인보우로보틱스 로봇",
        "🚀 방산/우주 (한화에어로)": "한화에어로스페이스 방산",
        "⚡ 중공업 (효성중공업)": "효성중공업 전력",
        "📈 나스닥/미장 시황": "Nasdaq 100 stock",
        "₿ 비트코인/코인": "Bitcoin crypto news",
        "➕ 직접 입력": "custom"
    }
    
    selected_theme = st.selectbox("분석 주제 선택:", list(DEFAULT_THEMES.keys()))
    search_keyword = st.text_input("검색어:") if selected_theme == "➕ 직접 입력" else DEFAULT_THEMES[selected_theme]
    news_count = st.slider("국가별 참고 뉴스 개수", 1, 5, 3)

# --- 3. 스타일 가이드 (테슬라 언급 삭제, 문체만 유지) ---
PRESET_STYLES = {
    "🌌 로켓테슬라 스타일 (@rklb_invest)": "논리적 인과관계를 중시하는 전략적 스토리텔링. '우연은 없다, 의도만 존재할 뿐' 문구를 도입부에 활용하며 깊이 있는 분석 수행.",
    "☀️ 미국개미 스타일 (@USAnt_IDEA)": "열정적이고 친절한 멘토링. 핵심 데이터를 명확하게 짚어주는 긍정적인 톤. 마무리 문구 'Powered by #USAnt'.",
    "💎 반보 스타일 (@Banbo_Insight)": "비유와 예시를 활용한 쉬운 설명. [제목] 형식을 사용하고 정보를 다정하게 구조화함."
}

selected_style_key = st.selectbox("분석 페르소나:", list(PRESET_STYLES.keys()))
style_content = PRESET_STYLES[selected_style_key]

# --- 4. 뉴스 수집 함수 (차단 방지 및 디버깅 강화) ---
def fetch_news_safe(keyword, lang, geo, count):
    config = Config()
    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    
    encoded_q = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl={lang}&gl={geo}&ceid={geo}:{lang}"
    
    # 디버그용: 실제 생성된 RSS 주소를 화면에 출력 (나중에 지워도 됩니다)
    # st.write(f"🔍 검색 URL: {url}") 
    
    feed = feedparser.parse(url)
    results = []
    
    for entry in feed.entries[:count*2]:
        if len(results) >= count: break
        try:
            article = Article(entry.link, config=config)
            article.download(); article.parse()
            # 텍스트가 조금이라도 있으면 일단 수집 (조건 완화)
            content = article.text if len(article.text) > 50 else entry.get('summary', entry.title)
            results.append({
                "title": entry.title, "link": entry.link,
                "image": article.top_image, "text": content[:1200]
            })
        except: continue
    return results

# --- 5. 실행 로직 ---
if st.button("🚀 리포트 생성 시작"):
    if not user_api_key or not search_keyword:
        st.error("API 키와 주제를 확인해 주세요.")
    else:
        try:
            genai.configure(api_key=user_api_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            with st.spinner("최신 정보를 수집하고 있습니다..."):
                # 미국용 키워드 번역 (짧고 강력하게)
                us_keyword = model.generate_content(f"Translate '{search_keyword}' to 1-2 English news keywords. Result only.").text.strip()
                
                kr_news = fetch_news_safe(search_keyword, "ko", "KR", news_count)
                us_news = fetch_news_safe(us_keyword, "en", "US", news_count)
                all_news = kr_news + us_news

            if not all_news:
                st.error(f"🚨 '{search_keyword}' 뉴스 수집 실패. 검색어를 더 짧게 입력해 보세요.")
            else:
                st.subheader("📰 분석 데이터 원본")
                cols = st.columns(3)
                for idx, news in enumerate(all_news):
                    with cols[idx % 3]:
                        if news['image']: st.image(news['image'], use_container_width=True)
                        st.markdown(f"**[{news['title']}]({news['link']})**")
                
                with st.spinner("분석 중..."):
                    context = "\n".join([f"기사: {n['text']}" for n in all_news])
                    # 주제 집중을 위한 강력한 지침
                    prompt = f"""
                    지침: 제공된 [데이터] 내용에만 100% 집중해라. 테슬라 등 관련 없는 내용은 언급하지 마라.
                    데이터: {context}
                    말투: {style_content}
                    """
                    response = model.generate_content(prompt)
                    
                    st.divider()
                    st.subheader("✅ 머스크노미 랩 분석 결과")
                    st.code(response.text, language='text')
                    st.balloons()
        except Exception as e:
            st.error(f"오류 발생: {e}")
        
