import streamlit as st
from google import genai
from PIL import Image
import io
import time

st.set_page_config(page_title="용인 AI 제작소", layout="centered")
st.title("🎬 용인 미르아이 공유학교 AI 제작소")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("설정에서 API 키를 넣어줘")
    st.stop()

client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "image" in msg: st.image(msg["image"])
        if "video" in msg: st.video(msg["video"])

st.markdown("---")

preview_container = st.container()

uploaded_file = st.file_uploader(
    "이미지 추가 (+)", 
    type=["png", "jpg", "jpeg", "webp"], 
    key=f"up_{st.session_state.uploader_key}",
    label_visibility="collapsed"
)

img_for_ai = None
if uploaded_file:
    raw_img = Image.open(uploaded_file)
    raw_img.thumbnail((1024, 1024))
    with preview_container:
        st.image(raw_img, width=150, caption="사용될 이미지")
    img_for_ai = raw_img

if prompt := st.chat_input("설명을 입력하고 엔터를 눌러줘"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.current_working_prompt = prompt
    st.session_state.current_working_img = img_for_ai
    st.session_state.uploader_key += 1
    st.rerun()

if "current_working_prompt" in st.session_state:
    with st.chat_message("assistant"):
        p = st.session_state.current_working_prompt
        img = st.session_state.current_working_img
        
        st.write(f"{p} 작업을 시작할까?")
        col1, col2 = st.columns(2)
        
        # 이미지 생성/변형 (이미 성공한 로직)
        if col1.button("🖼️ 이미지 생성/변형"):
            try:
                with st.spinner("이미지 작업 중..."):
                    contents = [img, p] if img else p
                    response = client.models.generate_content(
                        model="gemini-3.1-flash-image-preview", 
                        contents=contents
                    )
                    res_data = response.candidates[0].content.parts[0].inline_data.data
                    st.session_state.messages.append({"role": "assistant", "content": "이미지 완성!", "image": res_data})
                    del st.session_state.current_working_prompt
                    st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")

        # 영상 생성/변환 (에러 수정 지점!)
        if col2.button("🎬 영상 생성/변환"):
            try:
                with st.spinner("영상 제작 중..."):
                    # 기본 인자 설정
                    video_args = {
                        "model": "veo-3.1-lite-generate-preview",
                        "prompt": p,
                        "config": {"aspect_ratio": "16:9"}
                    }
                    
                    if img:
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='PNG')
                        temp_file = client.files.upload(
                            file=io.BytesIO(img_byte_arr.getvalue()), 
                            config={"mime_type": "image/png"}
                        )
                        # [핵심 수정] input_file 대신 image라는 이름을 써야 함!
                        video_args["image"] = temp_file
                    
                    op = client.models.generate_videos(**video_args)
                    while not op.done:
                        time.sleep(5)
                        op = client.operations.get(op)
                    
                    v_data = client.files.download(file=op.result.generated_videos[0].video)
                    st.session_state.messages.append({"role": "assistant", "content": "영상 완성!", "video": v_data})
                    del st.session_state.current_working_prompt
                    st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")
