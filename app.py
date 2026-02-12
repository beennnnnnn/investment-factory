import streamlit as st
import google.generativeai as genai
import feedparser
from newspaper import Article
import re

# --- UI 설정 ---
st.set_page_config(page_title="Safe Investment Factory", layout="wide", page_icon="🛡️")
st.title("📱 이동식 투자 포스팅 생성기 (보안 모드)")
st.caption("⚠️ 본 프로그램은 API 키를 서버에 저장하지 않습니다. 브라우저를 닫으면 정보가 즉시 파기됩니다.")

# --- [사이드바] 설정 ---
with st.sidebar:
    st.header("🔑 보안 세션 시작")
    # 매번 직접 입력하되, 화면에는 보이지 않게 password 타입으로 설정
    user_api_key = st.text_input("Gemini API 키를 입력하세요:", type="password", help="키는 저장되지 않으며 세션 종료 시 삭제됩니다.")
    st.caption("[키 발급처](https://aistudio.google.com/app/apikey)")
    
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
    selected_theme = st.selectbox("오늘의 뉴스 주제:", list(DEFAULT_THEMES.keys()))
    search_keyword = st.text_input("검색어:") if selected_theme == "➕ 직접 입력" else DEFAULT_THEMES[selected_theme]
    news_count = st.slider("참고 뉴스 개수", 1, 5, 3)

# --- [내재화] 벤치마킹 스타일 프리셋 ---
PRESET_STYLES = {
    "💎 반보 스타일 (@Banbo_Insight)": "비유(맛집 등)를 사용해 복잡한 용어를 쉽게 설명. [제목] 형식을 쓰고 번호를 매겨 깔끔하게 정리.",
    "🔥 미국개미 스타일 (@USAnt_IDEA)": "매우 공격적이고 강한 확신. '똑똑히 들어라' 등 강한 어조. 마지막은 'Powered by #USAnt'.",
    "🌌 로켓테슬라 스타일 (@rklb_invest)": "전략적 스토리텔링. '우연은 없다, 의도만 존재할 뿐' 문구 활용. 긴 호흡의 분석.",
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
            # 입력된 키를 세션 내에서만 사용
            genai.configure(api_key=user_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            with st.spinner("정보를 수집하여 전문가의 글로 변환 중..."):
                rss_url = f"https://news.google.com/rss/search?q={search_keyword}&hl=ko&gl=KR&ceid=KR:ko"
                feed = feedparser.parse(rss_url)
                news_data = ""
                for entry in feed.entries[:news_count]:
                    try:
                        article = Article(entry.link)
                        article.download()
                        article.parse()
                        news_data += f"\n제목: {entry.title}\n내용: {article.text[:1000]}\n---"
                    except: continue

                prompt = f"뉴스 정보: {news_data}\n\n말투 스타일 가이드: {selected_style_content}\n\n위 스타일을 복제해 X 포스팅을 쓰고 영어 이미지 프롬프트도 1줄 추가해."
                response = model.generate_content(prompt)
                
                st.divider()
                st.subheader("✅ 생성된 결과물")
                st.code(response.text, language='text')
                st.balloons()
        except Exception as e:
            st.error(f"오류가 발생했습니다(키 확인 필요): {e}")
