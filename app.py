import streamlit as st
import google.generativeai as genai
import feedparser
from newspaper import Article, Config
import urllib.parse
import yfinance as yf  # 시세 데이터 수집을 위한 라이브러리 추가
import pandas as pd
from datetime import datetime

# --- 1. UI 설정 ---
st.set_page_config(page_title="머스크노미 랩 (Muskonomy Lab)", layout="wide", page_icon="🚀")
st.title("🚀 머스크노미 랩 (Muskonomy Lab)")
st.caption("📱 글로벌 시세 대시보드와 AI 뉴스 분석이 결합된 통합 투자 연구소")

# --- 2. [신규] 실시간 마켓 대시보드 기능 ---
st.divider()
st.subheader("📊 실시간 글로벌 마켓 대시보드")

def get_market_data():
    # 주요 지수 및 자산 티커 설정
    tickers = {
        "코스피": "^KS11", "코스닥": "^KQ11", 
        "S&P500": "^GSPC", "나스닥": "^IXIC",
        "비트코인": "BTC-USD", "이더리움": "ETH-USD",
        "원/달러 환율": "KRW=X",
        "금(Gold)": "GC=F", "은(Silver)": "SI=F", "구리(Copper)": "HG=F",
        "WTI유가": "CL=F"
    }
    
    data_list = []
    for name, ticker in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100
                data_list.append({"name": name, "price": current_price, "change": change, "pct": change_pct})
        except: continue
    return data_list

if st.button("📈 마켓 시세 새로고침"):
    market_data = get_market_data()
    if market_data:
        # 4열로 깔끔하게 배치
        cols = st.columns(4)
        for i, item in enumerate(market_data):
            with cols[i % 4]:
                color = "normal" if abs(item['pct']) < 0.1 else ("inverse" if item['pct'] > 0 else "normal")
                st.metric(
                    label=item['name'], 
                    value=f"{item['price']:,.2f}", 
                    delta=f"{item['pct']:.2f}%"
                )
    else:
        st.warning("시세 데이터를 불러오는 중입니다. 잠시 후 다시 시도해 주세요.")

st.divider()

# --- 3. 사이드바: 설정 (기존 모든 기능 유지) ---
with st.sidebar:
    st.header("🔑 보안 세션")
    user_api_key = st.text_input("Gemini API 키 입력:", type="password")
    
    st.divider()
    st.header("⚙️ 정보 수집 설정")
    
    DEFAULT_THEMES = {
        "🧠 머스크노미 (Tesla/xAI)": "Tesla xAI Elon Musk",
        "🇰🇷 국장 시황 (코스피/코스닥)": "코스피 코스닥 시황",
        "🌎 거시경제 (환율/금리/채권)": "환율 금리 국채금리 거시경제 지표 전망 뉴스",
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
    news_count = st.slider("국가별 참고 뉴스 개수 (한/미 각각)", 1, 5, 3)

# --- 4. 분석 페르소나 스타일 ---
PRESET_STYLES = {
    "🌌 로켓테슬라 스타일 (@rklb_invest)": "논리적 인과관계를 중시하는 전략적 스토리텔링. '우연은 없다, 의도만 존재할 뿐' 문구를 도입부에 활용하며 깊이 있는 분석 수행.",
    "☀️ 미국개미 스타일 (@USAnt_IDEA)": "열정적이고 친절한 멘토링. 핵심 데이터를 명확하게 짚어주는 긍정적인 톤. 마무리 문구 'Powered by #USAnt'.",
    "💎 반보 스타일 (@Banbo_Insight)": "비유와 예시를 활용한 다정하고 쉬운 설명. [제목] 형식을 사용하고 정보를 다정하게 구조화함."
}

selected_style_key = st.selectbox("분석 페르소나:", list(PRESET_STYLES.keys()))
style_content = PRESET_STYLES[selected_style_key]

# --- 5. 뉴스 수집 함수 ---
def fetch_news_safe(keyword, lang, geo, count):
    config = Config()
    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    encoded_q = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl={lang}&gl={geo}&ceid={geo}:{lang}"
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:count*2]:
        if len(results) >= count: break
        try:
            article = Article(entry.link, config=config)
            article.download(); article.parse()
            content = article.text if len(article.text) > 50 else entry.get('summary', entry.title)
            results.append({"title": entry.title, "link": entry.link, "image": article.top_image, "text": content[:1200]})
        except: continue
    return results

# --- 6. 실행 로직 (기사 시각화 및 이미지 프롬프트 유지) ---
if st.button("🚀 글로벌 뉴스 종합 분석 시작"):
    if not user_api_key or not search_keyword:
        st.error("API 키와 주제를 확인해 주세요.")
    else:
        try:
            genai.configure(api_key=user_api_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            with st.spinner("최신 정보를 수집하고 있습니다..."):
                us_keyword = model.generate_content(f"Translate '{search_keyword}' to 1-2 English news keywords. Result only.").text.strip()
                kr_news = fetch_news_safe(search_keyword, "ko", "KR", news_count)
                us_news = fetch_news_safe(us_keyword, "en", "US", news_count)
                all_news = kr_news + us_news

            if not all_news:
                st.error("🚨 뉴스 수집 실패. 검색어를 확인해 주세요.")
            else:
                st.subheader("📰 분석 데이터 원본 (이미지 & 링크)")
                cols = st.columns(3)
                for idx, news in enumerate(all_news):
                    with cols[idx % 3]:
                        if news['image']: st.image(news['image'], use_container_width=True)
                        st.markdown(f"**[{news['title']}]({news['link']})**")
                
                with st.spinner("분석 및 이미지 프롬프트 작성 중..."):
                    context = "\n".join([f"기사: {n['text']}" for n in all_news])
                    prompt = f"""
                    지침: 
                    1. 제공된 [데이터] 내용에만 집중하여 분석해라. 데이터에 없는 종목을 억지로 연결하지 마라.
                    2. [말투 가이드]의 문체와 형식을 따라 친절하게 작성해라.
                    3. 글의 맨 마지막에 포스팅 내용에 어울리는 고품질의 영어 이미지 프롬프트(Image Prompt) 한 줄을 반드시 추가해라.

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
