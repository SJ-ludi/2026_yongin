import streamlit as st
from google import genai
from PIL import Image  # 이미지를 예쁘게 포장해줄 도구
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
    
    img_for_ai = None # AI에게 줄 포장된 이미지
    if uploaded_file:
        st.image(uploaded_file, caption="업로드된 이미지", use_container_width=True)
        # [수정포인트] raw bytes가 아니라 PIL Image 객체로 변환
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
        
        st.write(f"🔍 **'{st.session_state.current_prompt}'**(으)로 시작할까요?")
        col1, col2 = st.columns(2)
        
        # --- [이미지 생성/변형 (I2I)] ---
        if col1.button(mode_text, use_container_width=True):
            try:
                with st.spinner("이미지 작업 중..."):
                    # [수정포인트] 이미지가 있으면 [그림, 글자] 순서로 리스트를 만들어 전달
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

        # --- [영상 생성/변환 (I2V)] ---
        if col2.button(mode_video, use_container_width=True):
            try:
                with st.spinner("비디오 작업 중... (약 1~2분 소요)"):
                    if img_for_ai:
                        # [I2V 전용 로직] 이미지를 파일로 먼저 업로드한 후 참조함 (가장 안정적인 방식)
                        # 임시로 이미지 바이트 추출
                        img_byte_arr = io.BytesIO()
                        img_for_ai.save(img_byte_arr, format='PNG')
                        temp_file = client.files.upload(file=io.BytesIO(img_byte_arr.getvalue()))
                        
                        operation = client.models.generate_videos(
                            model="veo-3.1-lite-generate-preview",
                            prompt=st.session_state.current_prompt,
                            input_file=temp_file, # 업로드된 파일 참조
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
