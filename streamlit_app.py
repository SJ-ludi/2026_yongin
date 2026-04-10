import streamlit as st
from google import genai
import time

# 1. 사이트 설정
st.set_page_config(page_title="용인 AI 영상 제작소", layout="centered")
st.title("🎬 용인 미르아이 공유학교 AI 영상 제작소")

# 2. 최신형 Client 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Secrets 설정에서 GOOGLE_API_KEY를 입력해주세요.")
    st.stop()

# 찾아오신 최신 SDK 방식 사용
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# 3. 기억 장치 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_prompt" not in st.session_state:
    st.session_state.current_prompt = None

# 4. 채팅 내역 그리기
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "image" in msg: st.image(msg["image"])
        if "video" in msg: st.video(msg["video"])

# 5. 입력창
if prompt := st.chat_input("상상하는 장면을 설명해주세요!"):
    st.session_state.current_prompt = prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# 6. 작업 선택 상자
if st.session_state.current_prompt:
    with st.chat_message("assistant"):
        st.write(f"'{st.session_state.current_prompt}'(으)로 무엇을 만들까요?")
        col1, col2 = st.columns(2)
        
        # --- 이미지 생성 ---
        if col1.button("🖼️ 이미지 생성"):
            try:
                with st.spinner("이미지를 그리는 중..."):
                    # 최신 SDK의 이미지 생성 방식
                    response = client.models.generate_content(
                        model="imagen-3.0-generate-002",
                        contents=st.session_state.current_prompt
                    )
                    image_data = response.candidates[0].content.parts[0].inline_data.data
                    
                    st.session_state.messages.append({"role": "assistant", "content": "이미지 완성!", "image": image_data})
                    st.session_state.current_prompt = None
                    st.rerun()
            except Exception as e:
                st.error(f"이미지 오류: {e}")

# --- 영상 생성 (설정을 최소화해서 에러 방지) ---
        if col2.button("🎬 영상 생성"):
            try:
                with st.spinner("비디오를 생성 중입니다. (약 1분 소요)"):
                    # 설정을 복잡하게 넣지 않고 기본값으로 요청!
                    operation = client.models.generate_videos(
                        model="veo-3.1-lite-generate-preview",
                        prompt=st.session_state.current_prompt,
                        # config 부분을 최소화하거나 아예 빼버려도 돼!
                        config={"aspect_ratio": "16:9"} 
                    )
                    
                    while not operation.done:
                        time.sleep(5)
                        operation = client.operations.get(operation)
                    
                    video_data = operation.result.generated_videos[0].video.data
                    
                    st.session_state.messages.append({"role": "assistant", "content": "비디오 완성!", "video": video_data})
                    st.session_state.current_prompt = None
                    st.rerun()
            except Exception as e:
                st.error(f"비디오 오류 발생: {e}")
