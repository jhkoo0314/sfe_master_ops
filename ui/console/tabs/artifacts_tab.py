import os

import pandas as pd
import streamlit as st

from modules.validation.workflow.execution_registry import (
    get_execution_mode_label,
    get_execution_mode_modules,
)
from ui.console.analysis_explainer import explain_module_result
from ui.console.artifacts import collect_artifact_files, get_execution_analysis_doc_path, load_artifact_preview
from ui.console.display import render_page_hero, render_panel_header, render_stage_badge
from ui.console.runner import get_cached_intake_result, has_session_intake_inputs


def render_artifacts_tab() -> None:
    render_page_hero("분석 산출물 미리보기", "정규화 파일, 검증 결과 파일, validation 승인 result asset을 10행 미리보기와 다운로드로 확인합니다.", "INTELLIGENCE")
    result = st.session_state.pipeline_result
    if not result:
        st.info("먼저 파이프라인을 실행하세요.")
        return

    execution_mode = st.session_state.get("execution_mode", "crm_to_sandbox")
    intake_result = get_cached_intake_result(execution_mode, st.session_state.saved_uploaded_data)
    intake_inputs_ready = has_session_intake_inputs(st.session_state.saved_uploaded_data)
    artifacts = collect_artifact_files(execution_mode)
    analysis_doc_path = get_execution_analysis_doc_path()
    render_panel_header("기간 차이 해석", "입력 데이터의 월 범위가 서로 다를 때, 실제 검증이 어느 공통 구간 기준으로 진행됐는지 먼저 설명합니다.")
    if not intake_inputs_ready:
        st.info("이번 세션 업로드 기준 intake 정보는 아직 없습니다. 업로드 후 실행하면 여기서 intake 해석도 함께 보여줍니다.")
    elif intake_result and intake_result.get("analysis_summary_message"):
        if intake_result.get("timing_alerts"):
            st.warning(intake_result["analysis_summary_message"])
        else:
            st.info(intake_result["analysis_summary_message"])
        for coverage in intake_result.get("period_coverages", []):
            st.markdown(
                f"- `{coverage.get('source_key')}`: "
                f"{coverage.get('start_month')} ~ {coverage.get('end_month')} "
                f"({coverage.get('month_count')}개월)"
            )
        for alert in intake_result.get("timing_alerts", []):
            st.markdown(f"- {alert.get('message')}")

    advisory_suggestions = [
        suggestion
        for suggestion in (intake_result or {}).get("suggestions", [])
        if suggestion.get("suggestion_type") == "required_mapping_candidate"
    ]
    if advisory_suggestions:
        render_panel_header("입력 데이터 주의사항", "실행은 진행했지만, 해석 전에 사람이 다시 보면 좋은 항목입니다.")
        st.info("아래 항목은 치명적이지 않아 실행은 진행했지만, 결과 해석 정확도를 위해 분석 전에 한 번 더 확인하는 것이 좋습니다.")
        for suggestion in advisory_suggestions[:8]:
            candidate_text = ", ".join(suggestion.get("candidate_columns", [])) or "후보 없음"
            st.markdown(f"- `{suggestion.get('source_key')}`: {suggestion.get('message')} 후보: {candidate_text}")

    render_panel_header("판정 이유 분석", "각 단계가 왜 PASS, WARN, APPROVED, FAIL로 판정됐는지 reasoning note와 요약 파일 기준으로 확인합니다.")
    if os.path.exists(analysis_doc_path):
        with open(analysis_doc_path, "rb") as f:
            st.download_button(
                label="실행 분석 문서 다운로드",
                data=f.read(),
                file_name="latest_execution_analysis.md",
                mime="text/markdown",
                use_container_width=True,
            )
    for step in result.get("steps", []):
        status = str(step.get("status", ""))
        icon = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL", "APPROVED": "APPROVED", "SKIP": "SKIP"}.get(status, status)
        explanation = explain_module_result(str(step.get("module", "")), step)
        with st.expander(f"STEP {step.get('step')} · {str(step.get('module', '')).upper()} · {icon}", expanded=False):
            st.markdown(f"**판정 이유**: {step.get('reasoning_note', '-')}")
            st.markdown(f"**해석**: {explanation.get('summary', '-')}")
            st.markdown(f"**점수**: `{step.get('score')}` / **실행시간**: `{step.get('duration_ms')}ms`")
            if step.get("next_modules"):
                st.markdown(f"**다음 가능 모듈**: `{', '.join(step.get('next_modules', []))}`")
            if step.get("error"):
                st.error(step.get("error"))
            evidence = explanation.get("evidence", [])
            if evidence:
                st.markdown("**근거 수치**")
                for item in evidence:
                    st.markdown(f"- {item}")
            summary_path = step.get("summary_path")
            if summary_path and os.path.exists(summary_path):
                st.caption(summary_path)
                preview_df, preview_mode = load_artifact_preview(summary_path, os.path.splitext(summary_path)[1].lower(), max_rows=10)
                if preview_mode == "table" and preview_df is not None:
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)
                with open(summary_path, "rb") as f:
                    st.download_button(
                        label=f"요약 파일 다운로드: {os.path.basename(summary_path)}",
                        data=f.read(),
                        file_name=os.path.basename(summary_path),
                        mime="application/octet-stream",
                        key=f"summary_download_{step.get('step')}",
                    )

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
