import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import base64
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


def pil_to_data_uri(img: Image.Image) -> str:
    """PIL 이미지를 base64 data URI로 변환 (Runway API용)"""
    img_rgb = img.convert("RGB")
    buf = io.BytesIO()
    img_rgb.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


# 4. 좌우 분할 레이아웃
left_col, right_col = st.columns([1, 1])

# ========== 왼쪽: AI 생성 (이미지 및 영상) ==========
with left_col:
    st.subheader("🎨 AI 생성 도구")
    st.caption("설명을 입력하고 이미지나 영상 버튼을 눌러보세요.")

    # 파일 업로드 (AVIF 포함)
    uploaded_file = st.file_uploader(
        "참고 이미지 (선택사항)",
        type=["png", "jpg", "jpeg", "webp", "avif"],
        key=f"up_{st.session_state.uploader_key}",
    )

    img_for_ai = None
    if uploaded_file:
        try:
            raw_img = Image.open(uploaded_file)
            raw_img = raw_img.convert("RGB")  # AVIF·WebP 등 → RGB 변환
            raw_img.thumbnail((1024, 1024))
            st.image(raw_img, width=150, caption="참고 이미지")
            img_for_ai = raw_img
        except Exception as e:
            st.error(f"이미지를 열 수 없습니다: {e}")

    # 프롬프트 입력
    prompt = st.text_input("무엇을 만들고 싶나요?", placeholder="예: 우주를 유영하는 고양이")

    # 참고 이미지 유무에 따른 모드 안내
    if img_for_ai:
        st.info("📎 참고 이미지 있음 → **이미지→이미지** 또는 **이미지→영상** 가능")
    else:
        st.info("✏️ 텍스트만 입력 → **텍스트→이미지** 가능")

    btn_col1, btn_col2 = st.columns(2)

    # ===== 이미지 생성 버튼 (Gemini) =====
    if btn_col1.button("✨ 이미지 생성", use_container_width=True):
        if not prompt:
            st.warning("설명을 입력해주세요!")
        else:
            try:
                mode = "이미지→이미지" if img_for_ai else "텍스트→이미지"
                with st.spinner(f"[{mode}] 이미지를 그리는 중..."):
                    contents = [img_for_ai, prompt] if img_for_ai else prompt
                    response = gemini_client.models.generate_content(
                        model="gemini-3.1-flash-image-preview",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_modalities=["image", "text"],
                            image_config=types.ImageConfig(aspect_ratio="16:9"),
                        ),
                    )
                    res_data = response.candidates[0].content.parts[0].inline_data.data
                    st.session_state.messages.append(
                        {
                            "role": "user",
                            "type": "image",
                            "content": f"[{mode}] {prompt}",
                            "data": res_data,
                        }
                    )
                    st.session_state.uploader_key += 1
                    st.rerun()
            except Exception as e:
                st.error(f"이미지 생성 오류: {e}")

    # ===== 영상 생성 버튼 (Runway) — 이미지 필수 =====
    if btn_col2.button("🎥 영상 생성", use_container_width=True):
        if not prompt:
            st.warning("설명을 입력해주세요!")
        elif not img_for_ai:
            st.warning("영상 생성에는 참고 이미지가 필요합니다! 이미지를 먼저 업로드해주세요.")
        else:
            try:
                with st.spinner("[이미지→영상] 영상을 만드는 중 (1~2분 소요)..."):
                    data_uri = pil_to_data_uri(img_for_ai)
                    task = runway_client.image_to_video.create(
                        model="gen4.5",
                        prompt_image=data_uri,
                        prompt_text=prompt,
                        ratio="1280:720",
                        duration=5,
                    )
                    task = task.wait_for_task_output()

                video_url = task.output[0]
                st.session_state.messages.append(
                    {
                        "role": "user",
                        "type": "video",
                        "content": f"[이미지→영상] {prompt}",
                        "data": video_url,
                    }
                )
                st.session_state.uploader_key += 1
                st.rerun()

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
