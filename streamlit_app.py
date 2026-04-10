import streamlit as st
from google import genai
from PIL import Image
import io
import time
import base64 # 사진을 암호로 바꾸기 위해 필요함

# 1. 페이지 설정
st.set_page_config(page_title="용인 AI 제작소", layout="centered")
st.title("🎬 용인 미르아이 공유학교 AI 제작소")

# 2. API 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("설정에서 API 키를 넣어줘")
    st.stop()

client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# 3. 세션 상태 관리
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# 4. 대화 기록 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "image" in msg: st.image(msg["image"])
        if "video" in msg: st.video(msg["video"])

st.markdown("---")

# 5. 이미지 업로드 구역
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

# 6. 입력창
if prompt := st.chat_input("설명을 입력하고 엔터를 눌러줘"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.current_working_prompt = prompt
    st.session_state.current_working_img = img_for_ai
    st.session_state.uploader_key += 1
    st.rerun()

# 7. 실행 버튼 등장
if "current_working_prompt" in st.session_state:
    with st.chat_message("assistant"):
        p = st.session_state.current_working_prompt
        img = st.session_state.current_working_img
        
        st.write(f"{p} 작업을 시작할까?")
        col1, col2 = st.columns(2)
        
        # 이미지 생성/변형 (검증된 로직)
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

        # 영상 생성/변환 (에러 해결 지점)
        if col2.button("🎬 영상 생성/변환"):
            try:
                with st.spinner("영상 제작 중..."):
                    video_args = {
                        "model": "veo-3.1-lite-generate-preview",
                        "prompt": p,
                        "config": {"aspect_ratio": "16:9"}
                    }
                    
                    if img:
                        # [핵심] 사진을 Base64 데이터 구조로 변환
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        img_bytes = buf.getvalue()
                        encoded_img = base64.b64encode(img_bytes).decode("utf-8")
                        
                        # 서버가 요구하는 정확한 딕셔너리 구조로 전달
                        video_args["image"] = {
                            "bytes_base64_encoded": encoded_img,
                            "mime_type": "image/png"
                        }
                    
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
