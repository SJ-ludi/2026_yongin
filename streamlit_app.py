import streamlit as st
import google.generativeai as genai

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="용인 AI 영상 제작소", layout="centered")
st.title("🎬 용인 미르아이 공유학교 AI 영상 제작소")
st.markdown("---")

# 2. API 보안 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("설정(Secrets)에서 GOOGLE_API_KEY를 입력해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 3. 기억 장치 (Session State) 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []  # 전체 대화 기록
if "current_prompt" not in st.session_state:
    st.session_state.current_prompt = None  # 지금 막 입력한 프롬프트

# 4. 이전 대화 렌더링 (채팅 인터페이스)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "image" in msg:
            st.image(msg["image"])
        if "video" in msg:
            st.video(msg["video"])

# 5. 학생 입력창
if prompt := st.chat_input("상상하는 장면을 설명해주세요! (예: 우주에서 서핑하는 고양이)"):
    st.session_state.current_prompt = prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# 6. 선택 상자 (프롬프트 입력 직후에만 등장)
if st.session_state.current_prompt:
    with st.chat_message("assistant"):
        st.write(f"🔍 **'{st.session_state.current_prompt}'**(으)로 무엇을 만들까요?")
        col1, col2 = st.columns(2)
        
        # --- [버튼 1: 이미지 생성] ---
        if col1.button("🖼️ 이미지 생성 (Imagen)", use_container_width=True):
            try:
                with st.spinner("이미지를 그리는 중입니다..."):
                    model = genai.GenerativeModel('gemini-3.1-flash-image-preview')
                    response = model.generate_content(st.session_state.current_prompt)
                    image_data = response.candidates[0].content.parts[0].inline_data.data
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "이미지가 완성되었습니다!", 
                        "image": image_data
                    })
                    st.session_state.current_prompt = None # 작업 완료 후 초기화
                    st.rerun()
            except Exception as e:
                st.error(f"이미지 생성 중 오류 발생: {e}")

        # --- [버튼 2: 영상 생성] ---
        if col2.button("🎬 영상 생성 (Veo)", use_container_width=True):
            try:
                with st.spinner("영상을 만드는 중입니다 (약 1분 소요)..."):
                    # 확인된 정확한 모델 명칭 사용
                    model = genai.GenerativeModel('veo-3.1-lite-generate-preview')
                    
                    # 영상 생성 호출
                    response = model.generate_content(st.session_state.current_prompt)
                    video_data = response.candidates[0].content.parts[0].inline_data.data
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "영상이 완성되었습니다!", 
                        "video": video_data
                    })
                    st.session_state.current_prompt = None # 작업 완료 후 초기화
                    st.rerun()
            except Exception as e:
                st.error(f"영상 생성 중 오류 발생: {e}")
