import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io

# 1. 사이트 설정
st.set_page_config(page_title="용인 AI 제작소", layout="wide")
st.title("🎬 용인 미르아이 공유학교 AI 제작소")

# 2. API 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("설정에서 API 키를 넣어주세요")
    st.stop()

client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# 3. 세션 관리
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "img_count" not in st.session_state:
    st.session_state.img_count = 0

MAX_IMG = 10  # 1인당 이미지 최대 횟수

# 4. 운영 시간 체크 (필요시 활성화)
# from datetime import datetime
# import pytz
# kst = pytz.timezone("Asia/Seoul")
# now = datetime.now(kst)
# if now.weekday() >= 5 or now.hour < 9 or now.hour >= 18:
#     st.info("🔒 운영 시간이 아닙니다. (평일 09:00~18:00)")
#     st.stop()

# 5. 좌우 분할 레이아웃
left_col, right_col = st.columns([1, 1])

# ========== 왼쪽: 이미지 생성 ==========
with left_col:
    st.subheader("🖼️ 이미지 생성")
    st.caption(f"남은 횟수: {MAX_IMG - st.session_state.img_count} / {MAX_IMG}")

    # 이미지 업로드
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
    prompt = st.text_input("이미지 설명을 입력하세요", placeholder="예: 용인 처인구의 미래 도시 모습")

    # 생성 버튼
    if st.button("✨ 이미지 생성", use_container_width=True):
        if not prompt:
            st.warning("설명을 입력해주세요!")
        elif st.session_state.img_count >= MAX_IMG:
            st.warning(f"이미지 생성은 최대 {MAX_IMG}회까지 가능합니다.")
        else:
            try:
                with st.spinner("그리는 중..."):
                    contents = [img_for_ai, prompt] if img_for_ai else prompt
                    response = client.models.generate_content(
                        model="gemini-3.1-flash-image-preview",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_modalities=["image", "text"],
                            image_config=types.ImageConfig(
                                aspect_ratio="16:9"
                            )
                        )
                    )
                    res_data = response.candidates[0].content.parts[0].inline_data.data
                    st.session_state.messages.append({
                        "role": "user",
                        "content": prompt,
                        "image": res_data
                    })
                    st.session_state.img_count += 1
                    st.session_state.uploader_key += 1
                    st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")

    # 생성 기록 표시
    st.markdown("---")
    st.subheader("📋 생성 기록")
    if not st.session_state.messages:
        st.info("아직 생성한 이미지가 없어요. 위에서 만들어보세요!")
    else:
        for i, msg in enumerate(reversed(st.session_state.messages)):
            with st.container():
                st.markdown(f"**{len(st.session_state.messages) - i}.** {msg['content']}")
                if "image" in msg:
                    st.image(msg["image"], use_container_width=True)
                st.markdown("---")

# ========== 오른쪽: 패들렛 (영상 주문) ==========
with right_col:
    st.subheader("🎬 영상 주문서")
    st.caption("마음에 드는 이미지를 저장한 뒤, 아래 패들렛에 이미지와 설명을 올려주세요!")
    st.info("💡 왼쪽에서 이미지를 만들고 → 오른쪽 패들렛에 올리면 → 선생님이 영상으로 만들어줄게요!")

    st.components.v1.iframe(
        "https://padlet.com/ludilab001/breakout-room/QgJV4Z6EyzZ84mBk-9od1vjG2akkEbNOy",
        height=800,
        scrolling=True,
    )
