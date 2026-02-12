import streamlit as st
import google.generativeai as genai
import feedparser
from newspaper import Article
import urllib.parse
import re

# --- 1. UI 및 보안 설정 ---
st.set_page_config(page_title="Global Investment Factory", layout="wide", page_icon="🌐")
st.title("🌐 글로벌 '딸깍' 투자 포스팅 공장")
st.caption("⚠️ 보안 최우선: API 키는 서버에 저장되지 않으며, 한/미 뉴스 이미지와 링크가 포함됩니다.")

# --- 2. 사이드바: 종목 및 뉴스 설정 (V2.7 모든 카테고리 포함) ---
with st.sidebar:
    st.header("🔑 보안 세션")
    user_api_key = st.text_input("Gemini API 키 입력:", type="password")
    
    st.divider()
    st.header("⚙️ 정보 수집 설정")
    
    # 요청하신 삼성, SDI, 현대차, 에코프로 등 모든 종목 카테고리 유지
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
    news_count_per_region = st.slider("국가별 참고 뉴스 개수 (한/미 각각)", 1, 5, 3)

# --- 3. 말투 스타일 프리셋 (사용자 제공 텍스트 기반) ---
PRESET_STYLES = {
    "💎 반보 스타일 (@Banbo_Insight)": "비유(맛집 등) 활용 및 번호 매기기. [제목] 형식 사용. 친절하고 전문적인 설명.",
    "🔥 미국개미 스타일 (@USAnt_IDEA)": "공격적이고 강한 확신. '똑똑히 들어라' 사용. 마무리 'Powered by #USAnt'.",
    "🌌 로켓테슬라 스타일 (@rklb_invest)": "전략적 스토리텔링. '우연은 없다, 의도만 존재할 뿐' 문구 활용. 타래 형식의 깊은 분석.",
    "➕ [커스텀] 메모장 업로드": "custom"
}

st.subheader("✍️ 타겟 스타일 선택")
selected_style_key = st.selectbox("누구의 영혼을 불러올까요?", list(PRESET_STYLES.keys()))

if selected_style_key == "➕ [커스텀] 메모장 업로드":
    uploaded_file = st.file_uploader("벤치마킹 메모장(.txt) 업로드", type=['txt'])
    selected_style_content = uploaded_file.getvalue().decode("utf-8") if uploaded_file else ""
else:
    selected_style_content = PRESET_STYLES[selected_style_key]

# --- 4. 뉴스 수집 함수 (이미지 및 링크 포함) ---
def fetch_global_news(keyword, lang_code, geo_code, count):
    encoded_q = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl={lang_code}&gl={geo_code}&ceid={geo_code}:{lang_code}"
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:count]:
        try:
            article = Article(entry.link)
            article.download()
            article.parse()
            results.append({
                "title": entry.title, "link": entry.link,
                "image": article.top_image, "text": article.text[:1000]
            })
        except: continue
    return results

# --- 5. 메인 실행 로직 ---
if st.button("🚀 한/미 뉴스 종합 분석 & 포스팅 생성"):
    if not user_api_key or not search_keyword:
        st.error("API 키와 주제를 확인해 주세요.")
    else:
        try:
            genai.configure(api_key=user_api_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            # (1) 미국 뉴스용 키워드 번역
            with st.spinner("미국 뉴스 검색을 위해 키워드 번역 중..."):
                trans_prompt = f"Translate '{search_keyword}' into a simple English news search keyword. Just the keyword."
                us_keyword = model.generate_content(trans_prompt).text.strip()
            
            # (2) 한/미 뉴스 동시 수집
            with st.spinner("한/미 양국에서 최신 정보를 긁어오는 중..."):
                kr_news = fetch_global_news(search_keyword, "ko", "KR", news_count_per_region)
                us_news = fetch_global_news(us_keyword, "en", "US", news_count_per_region)
                all_news = kr_news + us_news

            # (3) 수집된 원본 뉴스 시각화 (이미지 + 링크)
            st.subheader("📰 분석에 참고한 원본 뉴스")
            news_cols = st.columns(3)
            for idx, news in enumerate(all_news):
                with news_cols[idx % 3]:
                    if news['image']:
                        st.image(news['image'], use_container_width=True)
                    st.markdown(f"**[{news['title']}]({news['link']})**")
            
            # (4) 포스팅 생성
            with st.spinner("글로벌 데이터를 분석하여 전문가의 말투로 포스팅 작성 중..."):
                combined_context = "\n".join([f"소스: {n['text']}" for n in all_news])
                final_prompt = f"""
                [데이터 정보]:
                {combined_context}
                
                [말투 가이드]:
                {selected_style_content}
                
                [지침]:
                1. 한/미 양국의 정보를 종합하여 인사이트 있는 포스팅을 써줘.
                2. 선택된 말투의 특징(이모지, 어투, 줄바꿈)을 100% 재현해.
                3. 마지막엔 영어 이미지 프롬프트도 1줄 추가해줘.
                """
                response = model.generate_content(final_prompt)
                
                st.divider()
                st.subheader("✅ 완성된 글로벌 포스팅")
                st.code(response.text, language='text')
                st.balloons()
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
