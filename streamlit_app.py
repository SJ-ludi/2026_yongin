import streamlit as st
import google.generativeai as genai
import PIL.Image
import io

# 1. 사이트 설정
st.set_page_config(page_title="용인 AI 영상 제작소", layout="centered")
st.title("🎬 용인 미르아이 공유학교 디자인씽 AI 영상 제작소")

# 2. 보안 키 로드
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Secrets 설정에서 GOOGLE_API_KEY를 입력해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 3. 세션 기록 저장 (새로고침 전까지 유지)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. 이전 대화 렌더링
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "image" in msg:
            st.image(msg["image"])
        if "video" in msg:
            st.video(msg["video"])

# 5. 프롬프트 입력창
if prompt := st.chat_input("상상하는 장면을 설명해주세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        st.write(f"'{prompt}'(으)로 무엇을 만들까요?")
        
        col1, col2 = st.columns(2)
        
        # --- 이미지 생성 (Nano Banana 2) ---
        if col1.button("🖼️ 이미지 생성", key=f"img_{len(st.session_state.messages)}"):
            try:
                with st.spinner("Nano Banana 2가 그림을 그리는 중..."):
                    # 모델 호출 (Gemini 3.1 Flash Image)
                    model = genai.GenerativeModel('gemini-3.1-flash-image-preview')
                    response = model.generate_content(prompt)
                    
                    # 결과 이미지 가져오기
                    image = response.candidates[0].content.parts[0].inline_data.data
                    
                    # 기록 저장 및 출력
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "이미지가 완성되었습니다!",
                        "image": image
                    })
                    st.image(image)
                    st.rerun() # 화면 갱신
            except Exception as e:
                st.error(f"이미지 생성 실패: {e}")

        # --- 영상 생성 (Veo 3.1 Lite) ---
        if col2.button("🎬 영상 생성", key=f"vid_{len(st.session_state.messages)}"):
            try:
                with st.spinner("Veo 3.1 Lite가 영상을 만드는 중 (약 30초)..."):
                    model = genai.GenerativeModel('veo-3.1-lite-preview')
                    # 영상 생성 호출
                    response = model.generate_content(prompt)
                    video_data = response.candidates[0].content.parts[0].inline_data.data
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "영상이 완성되었습니다!",
                        "video": video_data
                    })
                    st.video(video_data)
                    st.rerun()
            except Exception as e:
                st.error(f"영상 생성 실패: {e}")
