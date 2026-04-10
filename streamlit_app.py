import streamlit as st
from google import genai
import time
from PIL import Image
import io

# 1. 사이트 설정
st.set_page_config(page_title="용인 AI 영상 제작소", layout="wide") # 넓게 보기
st.title("🎨 용인 미르아이 공유학교 멀티모달 제작소")

# 2. API 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Secrets 설정에서 GOOGLE_API_KEY를 입력해주세요.")
    st.stop()

client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# 3. 사이드바 - 이미지 업로드 기능
with st.sidebar:
    st.header("📂 이미지 업로드")
    uploaded_file = st.file_uploader("참고할 이미지를 올려주세요 (I2I, I2V용)", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, caption="업로드된 이미지", use_container_width=True)
        # 이미지를 AI가 읽을 수 있는 바이트 형태로 변환
        img_bytes = uploaded_file.getvalue()
    else:
        img_bytes = None

# 4. 기억 장치 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_prompt" not in st.session_state:
    st.session_state.current_prompt = None

# 5. 채팅 내역 그리기
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "image" in msg: st.image(msg["image"])
        if "video" in msg: st.video(msg["video"])

# 6. 입력창
if prompt := st.chat_input("이미지에 대한 설명이나 만들고 싶은 장면을 적어주세요!"):
    st.session_state.current_prompt = prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# 7. 작업 선택 버튼
if st.session_state.current_prompt:
    with st.chat_message("assistant"):
        mode_text = "🖼️ 이미지 변형(I2I)" if img_bytes else "🖼️ 이미지 생성"
        mode_video = "🎬 영상 변환(I2V)" if img_bytes else "🎬 영상 생성"
        
        st.write(f"🔍 **'{st.session_state.current_prompt}'**(으)로 작업을 시작할까요?")
        col1, col2 = st.columns(2)
        
        # --- [이미지 생성/변형 (I2I)] ---
        if col1.button(mode_text, use_container_width=True):
            try:
                with st.spinner("이미지 작업 중..."):
                    # 이미지가 있으면 [이미지, 텍스트] 전달, 없으면 [텍스트]만 전달
                    content_list = [img_bytes, st.session_state.current_prompt] if img_bytes else st.session_state.current_prompt
                    
                    response = client.models.generate_content(
                        model="gemini-3.1-flash-image-preview", 
                        contents=content_list
                    )
                    res_img = response.candidates[0].content.parts[0].inline_data.data
                    
                    st.session_state.messages.append({"role": "assistant", "content": f"{mode_text} 완료!", "image": res_img})
                    st.session_state.current_prompt = None
                    st.rerun()
            except Exception as e:
                st.error(f"이미지 오류: {e}")

        # --- [영상 생성/변환 (I2V)] ---
        if col2.button(mode_video, use_container_width=True):
            try:
                with st.spinner("비디오 작업 중... (약 1분 소요)"):
                    # Veo 모델에 이미지와 프롬프트를 함께 전달
                    # (SDK 버전에 따라 파라미터가 다를 수 있으나, 일반적으로 prompt에 포함하거나 전용 필드 사용)
                    video_args = {
                        "model": "veo-3.1-lite-generate-preview",
                        "prompt": st.session_state.current_prompt,
                        "config": {"aspect_ratio": "16:9"}
                    }
                    
                    # 이미지가 있을 경우 input_file 등으로 전달 (2026 SDK 표준)
                    if img_bytes:
                        # 텍스트와 이미지를 리스트로 묶어서 전달하는 방식 시도
                        operation = client.models.generate_videos(
                            **video_args,
                            input_file=img_bytes # 이미지를 참조 영상/이미지로 사용
                        )
                    else:
                        operation = client.models.generate_videos(**video_args)
                    
                    while not operation.done:
                        time.sleep(5)
                        operation = client.operations.get(operation)
                    
                    video_file_ref = operation.result.generated_videos[0].video
                    video_bytes = client.files.download(file=video_file_ref)
                    
                    st.session_state.messages.append({"role": "assistant", "content": f"{mode_video} 완료!", "video": video_bytes})
                    st.session_state.current_prompt = None
                    st.rerun()
            except Exception as e:
                st.error(f"비디오 오류: {e}")
