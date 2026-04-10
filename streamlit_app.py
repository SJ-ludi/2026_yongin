import streamlit as st
import google.generativeai as genai

# 1. 사이트 설정 및 보안
st.set_page_config(page_title="용인 AI 영상 제작소", layout="centered")
st.title("🎬 용인 미르아이 공유학교 AI 영상 제작소")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Secrets 설정에서 GOOGLE_API_KEY를 입력해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 2. 기억장치(session_state) 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_prompt" not in st.session_state:
    st.session_state.current_prompt = None

# 3. 이전 대화 렌더링 (채팅방처럼 보이게)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "image" in msg: st.image(msg["image"])
        if "video" in msg: st.video(msg["video"])

# 4. 학생 입력창
if prompt := st.chat_input("상상하는 장면을 설명해주세요!"):
    st.session_state.current_prompt = prompt  # 현재 프롬프트를 기억함
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun() # 화면을 다시 그려서 질문 상자를 띄움

# 5. 질문 상자 (프롬프트가 있을 때만 등장)
if st.session_state.current_prompt:
    with st.chat_message("assistant"):
        st.write(f"'{st.session_state.current_prompt}'(으)로 무엇을 만들까요?")
        col1, col2 = st.columns(2)
        
        # 이미지 버튼 클릭 시
        if col1.button("🖼️ 이미지 생성"):
            try:
                with st.spinner("Nano Banana 2가 그림을 그리는 중..."):
                    model = genai.GenerativeModel('gemini-3.1-flash-image-preview')
                    response = model.generate_content(st.session_state.current_prompt)
                    image_data = response.candidates[0].content.parts[0].inline_data.data
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "이미지가 완성됐어!", 
                        "image": image_data
                    })
                    st.session_state.current_prompt = None # 작업 완료 후 초기화
                    st.rerun()
            except Exception as e:
                st.error(f"이미지 생성 실패: {e}")

        # 영상 버튼 클릭 시
        if col2.button("🎬 영상 생성"):
            try:
                with st.spinner("Veo 3.1 Lite가 영상을 만드는 중 (약 30초)..."):
                    model = genai.GenerativeModel('veo-3.1-lite-preview')
                    response = model.generate_content(st.session_state.current_prompt)
                    video_data = response.candidates[0].content.parts[0].inline_data.data
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "영상이 완성됐어!", 
                        "video": video_data
                    })
                    st.session_state.current_prompt = None # 작업 완료 후 초기화
                    st.rerun()
            except Exception as e:
                st.error(f"영상 생성 실패: {e}")
