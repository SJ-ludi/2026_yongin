import streamlit as st
from google import genai
from PIL import Image
import io
import time

# 1. 사이트 설정
st.set_page_config(page_title="용인 AI 영상 제작소", layout="wide")
st.title("🎨 용인 미르아이 공유학교 멀티모달 제작소")

# 2. API 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Secrets 설정에서 GOOGLE_API_KEY를 입력해주세요.")
    st.stop()

client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# 3. 사이드바 - 이미지 업로드 및 포장
with st.sidebar:
    st.header("📂 이미지 업로드")
    uploaded_file = st.file_uploader("참고할 이미지를 올려주세요 (I2I, I2V용)", type=["png", "jpg", "jpeg"])
    
    img_for_ai = None
    if uploaded_file:
        st.image(uploaded_file, caption="업로드된 이미지", use_container_width=True)
        img_for_ai = Image.open(uploaded_file)

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
if prompt := st.chat_input("설명을 적어주세요! (예: 이 공을 유니콘이 차고 있어)"):
    st.session_state.current_prompt = prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# 7. 작업 버튼
if st.session_state.current_prompt:
    with st.chat_message("assistant"):
        mode_text = "🖼️ 이미지 변형(I2I)" if img_for_ai else "🖼️ 이미지 생성"
        mode_video = "🎬 영상 변환(I2V)" if img_for_ai else "🎬 영상 생성"
        
        st.write(f"{st.session_state.current_prompt} 작업을 시작할까?")
        col1, col2 = st.columns(2)
        
        # 이미지 생성/변형
        if col1.button(mode_text, use_container_width=True):
            try:
                with st.spinner("이미지 작업 중..."):
                    contents = [img_for_ai, st.session_state.current_prompt] if img_for_ai else st.session_state.current_prompt
                    
                    response = client.models.generate_content(
                        model="gemini-3.1-flash-image-preview", 
                        contents=contents
                    )
                    res_img = response.candidates[0].content.parts[0].inline_data.data
                    
                    st.session_state.messages.append({"role": "assistant", "content": f"{mode_text} 완료!", "image": res_img})
                    st.session_state.current_prompt = None
                    st.rerun()
            except Exception as e:
                st.error(f"이미지 오류 발생: {e}")

        # 영상 생성/변환
        if col2.button(mode_video, use_container_width=True):
            try:
                with st.spinner("비디오 작업 중... (약 1분 소요)"):
                    if img_for_ai:
                        img_byte_arr = io.BytesIO()
                        img_for_ai.save(img_byte_arr, format="PNG")
                        
                        # [핵심 수정] mime_type을 명시해서 파일 정체를 알려줌
                        temp_file = client.files.upload(
                            file=io.BytesIO(img_byte_arr.getvalue()),
                            config={"mime_type": "image/png"}
                        )
                        
                        operation = client.models.generate_videos(
                            model="veo-3.1-lite-generate-preview",
                            prompt=st.session_state.current_prompt,
                            input_file=temp_file,
                            config={"aspect_ratio": "16:9"}
                        )
                    else:
                        operation = client.models.generate_videos(
                            model="veo-3.1-lite-generate-preview",
                            prompt=st.session_state.current_prompt,
                            config={"aspect_ratio": "16:9"}
                        )
                    
                    while not operation.done:
                        time.sleep(5)
                        operation = client.operations.get(operation)
                    
                    video_file_ref = operation.result.generated_videos[0].video
                    video_bytes = client.files.download(file=video_file_ref)
                    
                    st.session_state.messages.append({"role": "assistant", "content": f"{mode_video} 완료!", "video": video_bytes})
                    st.session_state.current_prompt = None
                    st.rerun()
            except Exception as e:
                st.error(f"비디오 오류 발생: {e}")
