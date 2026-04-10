import streamlit as st
import google.generativeai as genai

# 1. 사이트 기본 설정
st.set_page_config(page_title="용인 AI 영상 제작소", layout="centered")
st.title("🎬 용인 미르아이 공유학교 디자인씽 AI 영상 제작소")

# 2. 보안 키 가져오기
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("설정에서 GOOGLE_API_KEY를 입력해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 3. 대화 기록 저장 주머니 만들기
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. 화면에 이전 기록들 보여주기
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "image" in msg: st.image(msg["image"])
        if "video" in msg: st.video(msg["video"])

# 5. 학생 입력창 만들기
if prompt := st.chat_input("상상하는 장면을 설명해주세요!"):
    # 학생이 보낸 말 기록
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # AI의 답변 공간
    with st.chat_message("assistant"):
        st.write("이 프롬프트로 무엇을 만들까요?")
        
        col1, col2 = st.columns(2)
        
        # 이미지 생성 버튼 클릭 시
        if col1.button("🖼️ 이미지 생성"):
            try:
                model = genai.GenerativeModel('gemini-3.1-flash-image-preview')
                with st.spinner("이미지를 그리고 있어요..."):
                    result = model.generate_content(prompt)
                    # 실제 API 호출 결과 처리는 여기에! (우선 텍스트 안내만)
                    st.success("이미지가 생성되었습니다!")
            except Exception as e:
                st.error(f"오류 발생: {e}")

        # 영상 생성 버튼 클릭 시
        if col2.button("🎬 영상 생성"):
            st.info("Veo 3.1 Lite로 영상을 생성 중입니다. 약 30초~1분 정도 소요됩니다.")
            # 영상 생성 로직 (API 연동 시 추가)
