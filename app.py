import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PURPOSE_OPTIONS = {
    "회식 장소 공지": "회식 일정, 장소, 교통편, 비용 등을 안내하는 공지",
    "회식 인원 파악": "회식 참석 여부 및 인원을 취합하는 요청",
    "축의금 취합": "경조사 축의금 납부 안내 및 취합 요청",
    "사내 데이터 취합": "부서·팀별 자료, 설문, 현황 등 사내 데이터 수집 요청",
    "일반 공지": "업무·행사·변경사항 등 일반적인 사내 공지",
    "직접 입력": "",
}

AUDIENCE_OPTIONS = [
    "전체 임직원",
    "특정 부서",
    "특정 팀",
    "관련 담당자",
    "직접 입력",
]

STYLE_OPTIONS = {
    "예의있게": "격식 있고 정중한 어투로, 존댓말을 사용합니다.",
    "간결하게": "핵심만 짧고 명확하게 전달합니다.",
    "친근하게": "부드럽고 따뜻한 톤으로, 협조를 구하는 느낌을 줍니다.",
    "공식적으로": "공문·공지 형식에 맞게 격식 있는 문체를 사용합니다.",
    "직접 입력": "",
}


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("`.env` 파일에 `OPENAI_API_KEY`가 설정되어 있지 않습니다.")
        st.stop()
    return OpenAI(api_key=api_key)


def build_prompt(
    title: str,
    purpose: str,
    purpose_detail: str,
    audience: str,
    audience_detail: str,
    style: str,
    style_detail: str,
    topic: str,
    extra_notes: str,
) -> str:
    audience_text = audience_detail if audience == "직접 입력" else audience
    style_text = style_detail if style == "직접 입력" else STYLE_OPTIONS[style]

    return f"""당신은 사내 에이텍(내부 공지·취합 요청) 보고서 작성 전문가입니다.
아래 조건에 맞는 보고서 초안을 한국어로 작성하세요.

## 작성 조건
- 보고서 제목: {title}
- 보고서 목적: {purpose}
- 목적 설명: {purpose_detail}
- 대상: {audience_text}
- 작성 스타일: {style_text}
- 주제/상세 내용: {topic}
- 추가 참고사항: {extra_notes or "없음"}

## 작성 지침
1. 실무에서 바로 사용할 수 있는 완성도 높은 초안을 작성합니다.
2. 제목, 본문, 마감일·제출 방법·문의처 등 필요한 항목을 목적에 맞게 포함합니다.
3. 플레이스홀더가 필요한 경우 [날짜], [장소], [담당자], [금액] 형식으로 표시합니다.
4. 불필요한 설명 없이 보고서 본문만 출력합니다.
5. 목적이 '취합'인 경우 제출 방법, 마감일, 제출 양식 안내를 반드시 포함합니다.
6. 목적이 '공지'인 경우 핵심 정보를 먼저 제시하고, 참석·확인이 필요하면 명확히 요청합니다.
"""


def generate_draft(client: OpenAI, prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "당신은 한국 기업의 사내 공지·취합 문서 작성 전문가입니다. "
                "명확하고 실무적인 에이텍 초안을 작성합니다.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def main() -> None:
    st.set_page_config(
        page_title="에이텍 보고서 초안 생성기",
        page_icon="📋",
        layout="wide",
    )

    st.title("📋 에이텍 보고서 초안 생성기")
    st.caption("회식 공지, 인원 파악, 축의금·데이터 취합 등 사내 보고서 초안을 빠르게 작성합니다.")

    with st.form("report_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input(
                "보고서 제목 *",
                placeholder="예: 2025년 1분기 팀 회식 안내",
            )

            purpose = st.selectbox(
                "보고서 목적 *",
                options=list(PURPOSE_OPTIONS.keys()),
            )
            purpose_detail = st.text_area(
                "목적 상세 설명",
                value=PURPOSE_OPTIONS[purpose],
                height=80,
                help="선택한 목적에 맞게 수정할 수 있습니다.",
            )

        with col2:
            audience = st.selectbox("대상 *", options=AUDIENCE_OPTIONS)
            audience_detail = ""
            if audience == "직접 입력":
                audience_detail = st.text_input(
                    "대상 직접 입력 *",
                    placeholder="예: 개발팀 전체, 인사팀 담당자",
                )

            style = st.selectbox(
                "작성 스타일 *",
                options=list(STYLE_OPTIONS.keys()),
                index=0,
            )
            style_detail = ""
            if style == "직접 입력":
                style_detail = st.text_input(
                    "스타일 직접 입력 *",
                    placeholder="예: 간결하되 존댓말 유지",
                )

        topic = st.text_area(
            "주제 및 상세 내용 *",
            height=140,
            placeholder=(
                "예: 6월 15일(금) 저녁 7시 강남 OO식당 회식\n"
                "참석 가능 여부를 6월 10일까지 회신해 주세요.\n"
                "1인당 예상 비용 5만원, 대중교통 이용 권장"
            ),
        )

        extra_notes = st.text_area(
            "추가 참고사항 (선택)",
            height=80,
            placeholder="예: 마감일, 담당자, 제출 방법, 금액, 특이사항 등",
        )

        submitted = st.form_submit_button("초안 생성", type="primary", use_container_width=True)

    if submitted:
        audience_value = audience_detail if audience == "직접 입력" else audience
        style_value = style_detail if style == "직접 입력" else style

        if not title.strip():
            st.warning("보고서 제목을 입력해 주세요.")
            return
        if not topic.strip():
            st.warning("주제 및 상세 내용을 입력해 주세요.")
            return
        if audience == "직접 입력" and not audience_detail.strip():
            st.warning("대상을 직접 입력해 주세요.")
            return
        if style == "직접 입력" and not style_detail.strip():
            st.warning("작성 스타일을 직접 입력해 주세요.")
            return

        prompt = build_prompt(
            title=title.strip(),
            purpose=purpose,
            purpose_detail=purpose_detail.strip(),
            audience=audience,
            audience_detail=audience_detail.strip(),
            style=style,
            style_detail=style_detail.strip(),
            topic=topic.strip(),
            extra_notes=extra_notes.strip(),
        )

        with st.spinner("에이텍 초안을 생성하는 중..."):
            try:
                client = get_client()
                draft = generate_draft(client, prompt)
                st.session_state["latest_draft"] = draft
                st.session_state["latest_title"] = title.strip()
                st.session_state["latest_purpose"] = purpose
                st.session_state["latest_audience"] = audience_value
                st.session_state["latest_style"] = style_value
            except Exception as exc:
                st.error(f"초안 생성 중 오류가 발생했습니다: {exc}")
                return

    if "latest_draft" in st.session_state:
        st.divider()
        st.subheader("생성된 초안")
        st.info(
            f"**{st.session_state.get('latest_title', '보고서')}** · "
            f"목적: {st.session_state.get('latest_purpose', '-')} · "
            f"대상: {st.session_state.get('latest_audience', '-')} · "
            f"스타일: {st.session_state.get('latest_style', '-')}"
        )
        st.text_area(
            "결과",
            value=st.session_state["latest_draft"],
            height=420,
            label_visibility="collapsed",
        )

        st.download_button(
            label="초안 다운로드 (.txt)",
            data=st.session_state["latest_draft"],
            file_name=f"{st.session_state.get('latest_title', '에이텍_초안')}.txt",
            mime="text/plain",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
