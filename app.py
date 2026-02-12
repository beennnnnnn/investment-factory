import streamlit as st
import google.generativeai as genai
import feedparser
from newspaper import Article

# --- UI 설정 ---
st.set_page_config(page_title="Investment Content Factory", layout="wide", page_icon="🚀")
st.title("📱 이동식 투자 포스팅 '딸깍' 시스템")

# --- [사이드바] 설정 ---
with st.sidebar:
    st.header("🔑 개인 설정")
    user_api_key = st.text_input("Gemini API 키 입력:", type="password")
    st.caption("[API 키 발급처](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    st.header("⚙️ 정보 수집")
    DEFAULT_THEMES = {
        "🚀 로켓랩 (RKLB)": "Rocket Lab RKLB news stock",
        "🧠 일론 머스크 & SpaceX": "Elon Musk SpaceX xAI news",
        "₿ 비트코인/코인": "Bitcoin crypto market news",
        "📈 나스닥/미장 시황": "Nasdaq 100 stock market news",
        "🤖 반도체/AI 산업": "Semiconductor HBM AI industry news",
        "➕ 직접 입력": "custom"
    }
    selected_theme = st.selectbox("뉴스 주제:", list(DEFAULT_THEMES.keys()))
    search_keyword = st.text_input("검색어:") if selected_theme == "➕ 직접 입력" else DEFAULT_THEMES[selected_theme]
    news_count = st.slider("참고 뉴스 개수", 1, 5, 3)

# --- [내재화] 벤치마킹 스타일 프리셋 ---
PRESET_STYLES = {
    "💎 반보 스타일 (@Banbo_Insight)": """
    말투 특징: 비유(맛집, 셰프 등)를 활용해 복잡한 용어를 쉽게 설명함. [제목] 형식을 쓰고 번호를 매겨 깔끔하게 정리. 전문적이면서 친절한 톤.
    - 예시: [소부장? 그게 뭔데?] 1. IDM 종합반도체 - 식당 주인. 피자 반죽부터 배달까지 다 하는 대기업입니다. 관련종목: 삼성전자...
    - 마무리: 해시태그와 함께 깔끔한 요약.
    """,
    
    "🔥 미국개미 스타일 (@USAnt_IDEA)": """
    말투 특징: 매우 공격적이고 선동적이며 강한 확신을 줌. "똑똑히 들어라", "쫄지 마라" 등 강한 어조 사용. 굵은 글씨와 불렛포인트 활용.
    - 예시: 똑똑히 들어라. 엔비디아 GPU만 보는 놈들은 하수다. 구글이 판을 뒤집고 있다. 지금 안 사면 평생 후회한다.
    - 마무리: 항상 "Powered by #USAnt"로 끝남.
    """,
    
    "🌌 로켓테슬라 스타일 (@rklb_invest)": """
    말투 특징: 깊이 있는 스토리텔링과 전략적 분석. "우연은 없다, 의도만 있을 뿐" 같은 철학적 문구 활용. 트위터 타래 형식의 긴 호흡을 선호하며 논리적임.
    - 예시: 머스크노미, 들어본 적 있어? 이건 단순한 확장이 아니야. 거대한 국가처럼 연결된 구조지. 왜 SpaceX가 xAI를 샀을까? 그 내막을 풀어볼게.
    - 마무리: "각자만의 알파를 찾길 바랄게" 또는 "구독으로 응원해줘" 등 소통형 마무리.
    """,
    
    "➕ [커스텀] 메모장 업로드": "custom"
}

# --- 스타일 선택 UI ---
st.subheader("✍️ 타겟 스타일 선택")
selected_style_key = st.selectbox("누구의 영혼을 불러올까요?", list(PRESET_STYLES.keys()))

if selected_style_key == "➕ [커스텀] 메모장 업로드":
    uploaded_file = st.file_uploader("추가 벤치마킹용 메모장(.txt)을 올려주세요", type=['txt'])
    selected_style_content = uploaded_file.getvalue().decode("utf-8") if uploaded_file else ""
else:
    selected_style_content = PRESET_STYLES[selected_style_key]
    with st.expander("스타일 가이드 미리보기"):
        st.write(selected_style_content)

# --- 실행 버튼 ---
if st.button("🚀 포스팅 생성 (딸깍!)"):
    if not user_api_key or not selected_style_content:
        st.error("설정이 부족합니다. 키와 스타일을 확인해 주세요.")
    else:
        try:
            genai.configure(api_key=user_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            with st.spinner("최신 뉴스를 긁어와 전문가의 글로 변환 중..."):
                # 뉴스 수집
                rss_url = f"https://news.google.com/rss/search?q={search_keyword}&hl=ko&gl=KR&ceid=KR:ko"
                feed = feedparser.parse(rss_url)
                news_data = ""
                for entry in feed.entries[:news_count]:
                    try:
                        article = Article(entry.link); article.download(); article.parse()
                        news_data += f"\n제목: {entry.title}\n내용: {article.text[:1200]}\n---"
                    except: continue

                # AI 프롬프트
                prompt = f"""
                너는 투자 전문 인플루언서야. 다음 [뉴스 정보]를 바탕으로 [선택된 스타일]을 완벽히 복제한 포스팅을 작성해라.
                
                [선택된 스타일 가이드]:
                {selected_style_content}
                
                [뉴스 정보]:
                {news_data}
                
                [지침]:
                1. 선택된 스타일의 시그니처 문구, 이모지 사용 빈도, 줄바꿈 방식을 그대로 따를 것.
                2. 주식 전문가가 봐도 손색없을 정도의 팩트 중심 분석을 포함할 것.
                3. 마지막에는 포스팅 분위기에 맞는 이미지 생성용 '영어 프롬프트'를 한 줄로 작성할 것.
                """
                response = model.generate_content(prompt)
                
                st.divider()
                st.subheader("✅ 생성된 포스팅")
                st.code(response.text, language='text')
                st.balloons()
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")