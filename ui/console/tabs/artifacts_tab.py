import pandas as pd
import streamlit as st

from ops_core.workflow.execution_registry import (
    get_execution_mode_label,
    get_execution_mode_modules,
)
from ui.console.artifacts import collect_artifact_files, load_artifact_preview
from ui.console.display import render_page_hero, render_panel_header, render_stage_badge


def render_artifacts_tab() -> None:
    render_page_hero("분석 산출물 미리보기", "정규화 파일, 검증 결과 파일, validation 승인 result asset을 10행 미리보기와 다운로드로 확인합니다.", "INTELLIGENCE")
    result = st.session_state.pipeline_result
    if not result:
        st.info("먼저 파이프라인을 실행하세요.")
        return

    execution_mode = st.session_state.get("execution_mode", "crm_to_sandbox")
    artifacts = collect_artifact_files(execution_mode)
    render_panel_header("산출물 브라우저", f"선택한 흐름은 {get_execution_mode_label(execution_mode)} 입니다. 아래 파일은 해당 흐름에서 생성된 정규화 파일, 검증 산출물, Builder 결과입니다.")
    st.markdown(f"""<div class="action-note"><b>현재 선택 흐름</b>: {' -> '.join(get_execution_mode_modules(execution_mode)).upper()}<br>표로 읽을 수 있는 파일은 최대 10행까지 미리보기 합니다. HTML 파일은 다운로드 중심으로 확인합니다.</div>""", unsafe_allow_html=True)

    if not artifacts:
        st.warning("선택한 흐름에 해당하는 산출물 파일을 아직 찾지 못했습니다.")
        return

    summary_df = pd.DataFrame(
        [{"모듈": item["module"].upper(), "단계": item["stage_label"], "구분": item["source_label"], "파일명": item["name"], "크기(KB)": item["size_kb"]} for item in artifacts]
    )
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    for idx, item in enumerate(artifacts, start=1):
        with st.expander(f"{idx}. [{item['module'].upper()}] {item['name']}"):
            st.markdown(f"""<div style="margin-bottom:8px">{render_stage_badge(item['stage_label'], item['stage_value'])}{render_stage_badge(item['module'].upper(), item['ext'].replace('.', '').upper())}</div>""", unsafe_allow_html=True)
            st.caption(f"{item['source_label']} | {item['path']}")
            preview_df, preview_mode = load_artifact_preview(item["path"], item["ext"], max_rows=10)
            if preview_mode == "table" and preview_df is not None:
                st.dataframe(preview_df, use_container_width=True, hide_index=True)
            else:
                st.info("이 파일 형식은 화면 표 미리보기 대신 다운로드로 확인하는 것이 더 적합합니다.")
            with open(item["path"], "rb") as f:
                st.download_button(
                    label=f"다운로드: {item['name']}",
                    data=f.read(),
                    file_name=item["name"],
                    mime="application/octet-stream",
                    key=f"artifact_download_{idx}",
                )


__all__ = ["render_artifacts_tab"]
