import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import time
from runwayml import RunwayML

# 1. 사이트 설정
st.set_page_config(page_title="용인 AI 제작소", layout="wide")
st.title("🎬 용인 미르아이 공유학교 AI 제작소")

# 2. API 설정
if "GOOGLE_API_KEY" not in st.secrets or "RUNWAY_API_KEY" not in st.secrets:
    st.error("설정에서 GOOGLE_API_KEY와 RUNWAY_API_KEY를 모두 넣어주세요")
    st.stop()

gemini_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
runway_client = RunwayML(api_key=st.secrets["RUNWAY_API_KEY"])

# 3. 세션 관리
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# 4. 좌우 분할 레이아웃
left_col, right_col = st.columns([1, 1])

# ========== 왼쪽: AI 생성 (이미지 및 영상) ==========
with left_col:
    st.subheader("🎨 AI 생성 도구")
    st.caption("설명을 입력하고 이미지나 영상 버튼을 눌러보세요.")

    # 파일 업로드
    uploaded_file = st.file_uploader(
        "참고 이미지 (선택사항)",
        type=["png", "jpg", "jpeg", "webp"],
        key=f"up_{st.session_state.uploader_key}",
    )

    img_for_ai = None
    if uploaded_file:
        raw_img = Image.open(uploaded_file)
        raw_img.thumbnail((1024, 1024))
        st.image(raw_img, width=150, caption="참고 이미지")
        img_for_ai = raw_img

    # 프롬프트 입력
    prompt = st.text_input("무엇을 만들고 싶나요?", placeholder="예: 우주를 유영하는 고양이")

    btn_col1, btn_col2 = st.columns(2)

    # 이미지 생성 버튼
    if btn_col1.button("✨ 이미지 생성", use_container_width=True):
        if not prompt:
            st.warning("설명을 입력해주세요!")
        else:
            try:
                with st.spinner("이미지를 그리는 중..."):
                    contents = [img_for_ai, prompt] if img_for_ai else prompt
                    response = gemini_client.models.generate_content(
                        model="gemini-3.1-flash-image-preview",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_modalities=["image", "text"],
                            image_config=types.ImageConfig(aspect_ratio="16:9")
                        )
                    )
                    res_data = response.candidates[0].content.parts[0].inline_data.data
                    st.session_state.messages.append({
                        "role": "user",
                        "type": "image",
                        "content": prompt,
                        "data": res_data
                    })
                    st.session_state.uploader_key += 1
                    st.rerun()
            except Exception as e:
                st.error(f"이미지 생성 오류: {e}")

    # 영상 생성 버튼 (Runway API 연동)
    if btn_col2.button("🎥 영상 생성", use_container_width=True):
        if not prompt:
            st.warning("설명을 입력해주세요!")
        else:
            try:
                with st.spinner("영상을 만드는 중 (약 1분 소요)..."):
                    # 실제 환경에서는 이미지를 URL로 변환하여 넘겨야 하지만 
                    # 여기서는 텍스트 기반 생성을 기본으로 구조를 잡았어.
                    # 이미지 투 비디오를 위해서는 이미지를 어딘가 업로드하고 그 URL을 보내야 해.
                    
                    task = runway_client.image_to_video.create(
                        model='gen3a_turbo',
                        prompt_text=prompt
                        # 만약 이미지 투 비디오를 하려면 prompt_image 매개변수에 URL이 들어가야 함
                    )
                    
                    # 작업 완료 대기 (폴링)
                    while task.status not in ['SUCCEEDED', 'FAILED']:
                        time.sleep(3)
                        task = runway_client.tasks.retrieve(task.id)
                    
                    if task.status == 'SUCCEEDED':
                        video_url = task.output[0]
                        st.session_state.messages.append({
                            "role": "user",
                            "type": "video",
                            "content": prompt,
                            "data": video_url
                        })
                        st.session_state.uploader_key += 1
                        st.rerun()
                    else:
                        st.error("영상 생성에 실패했어.")
            except Exception as e:
                st.error(f"영상 생성 오류: {e}")

    # 생성 기록 표시
    st.markdown("---")
    st.subheader("📋 생성 기록")
    if not st.session_state.messages:
        st.info("아직 생성한 결과물이 없어요.")
    else:
        for i, msg in enumerate(reversed(st.session_state.messages)):
            with st.container():
                st.markdown(f"**{len(st.session_state.messages) - i}.** {msg['content']}")
                if msg["type"] == "image":
                    st.image(msg["data"], use_container_width=True)
                elif msg["type"] == "video":
                    st.video(msg["data"])
                st.markdown("---")

# ========== 오른쪽: 패들렛 (산출물 공유) ==========
with right_col:
    st.subheader("🎬 산출물 공유함")
    st.caption("마음에 드는 결과물을 다운로드해서 패들렛에 올려주세요!")
    
    st.components.v1.iframe(
        "https://padlet.com/ludilab001/breakout-room/QgJV4Z6EyzZ84mBk-9od1vjG2akkEbNOy",
        height=800,
        scrolling=True,
    )
