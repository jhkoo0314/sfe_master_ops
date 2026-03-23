import os
import subprocess
from datetime import datetime

import streamlit as st

from ui.console.state import add_log
from ui.console.display import render_block_card, render_page_hero
from ui.console.artifacts import (
    get_report_download_paths,
    get_report_output_path,
    get_report_type_artifacts,
    get_report_type_description,
    get_report_type_options,
)
from ui.console.tabs.builder_helpers import build_period_filter_defaults, build_report_download_artifact


def render_builder_tab() -> None:
    render_page_hero("HTML 보고서 생성", "Builder는 render-only 레이어입니다. 검증 승인된 payload를 받아 HTML 결과물만 생성/확인합니다.", "PRESENTATION")
    result = st.session_state.pipeline_result
    builder_eligible = result and "builder" in result.get("final_eligible_modules", [])
    if not builder_eligible:
        st.warning("파이프라인 실행 후 Builder Handoff 조건을 충족해야 합니다.")
    else:
        st.markdown(
            """
            <div class="stat-strip">
              <div class="stat-chip"><div class="label">Builder Handoff</div><div class="value">Enabled</div></div>
              <div class="stat-chip"><div class="label">Output Modes</div><div class="value">HTML Report</div></div>
              <div class="stat-chip"><div class="label">Design Link</div><div class="value">Synced with html_builder</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_block_card("📊 Validation Approved Result Asset", "검증이 끝난 결과물 중 어떤 HTML 보고서를 열고 확인할지 선택하는 블록입니다.", "Output Block 01")
    report_type = st.selectbox("보고서 유형", get_report_type_options())
    period_col1, period_col2, period_col3 = st.columns(3)
    current_year = datetime.now().year
    year_options = [str(year) for year in range(current_year - 3, current_year + 1)]
    default_year = "2025" if "2025" in year_options else year_options[-1]

    with period_col1:
        period_mode = st.selectbox("출력 범위", ["전체 출력", "연간", "분기별", "월별"], index=0)

    selected_year = ""
    selected_sub_period = ""
    with period_col2:
        if period_mode == "전체 출력":
            st.selectbox("기준 연도", ["전체"], index=0, disabled=True)
        else:
            selected_year = st.selectbox(
                "기준 연도",
                year_options,
                index=year_options.index(default_year),
            )

    with period_col3:
        if period_mode == "분기별":
            selected_sub_period = st.selectbox("분기", ["1분기", "2분기", "3분기", "4분기"], index=0)
        elif period_mode == "월별":
            selected_sub_period = st.selectbox(
                "월",
                [f"{month:02d}월" for month in range(1, 13)],
                index=0,
            )
        else:
            st.selectbox("세부 기간", ["전체"], index=0, disabled=True)

    if period_mode == "전체 출력":
        report_period = "전체 기간"
    elif period_mode == "연간":
        report_period = f"{selected_year}년 전체"
    elif period_mode == "분기별":
        report_period = f"{selected_year}년 {selected_sub_period}"
    else:
        report_period = f"{selected_year}년 {selected_sub_period}"

    report_output_path = get_report_output_path(report_type)
    report_filters = build_period_filter_defaults(period_mode, selected_year, selected_sub_period)
    st.markdown(
        f"""<div class="action-note"><b>{report_type}</b><br>{get_report_type_description(report_type)}<br><br>선택 기간: <b>{report_period}</b><br>{get_report_type_artifacts(report_type)}</div>""",
        unsafe_allow_html=True,
    )

    if report_output_path and os.path.exists(report_output_path):
        download_data, download_name, download_mime, download_label, effective_report_path = build_report_download_artifact(
            report_output_path,
            report_type,
            report_period,
            report_filters,
        )
        col_open, col_download = st.columns(2)
        with col_open:
            if st.button("🌐 선택한 보고서 열기", disabled=not builder_eligible, use_container_width=True):
                subprocess.Popen(["start", effective_report_path], shell=True)
                st.info(f"브라우저에서 '{report_type}' 보고서를 엽니다. 선택 기간: {report_period}")
                add_log(f"보고서 열기: {report_type} ({report_period})")
        with col_download:
            st.download_button(
                label=download_label,
                data=download_data,
                file_name=download_name,
                mime=download_mime,
                disabled=not builder_eligible,
                use_container_width=True,
            )

        raw_downloads = [(label, path) for label, path in get_report_download_paths(report_type) if os.path.exists(path)]
        if raw_downloads:
            st.markdown(
                "<div class='action-note'><b>원본 다운로드</b><br>미리보기는 가볍게 보고, 전체 처방 원본은 아래 엑셀로 확인합니다.</div>",
                unsafe_allow_html=True,
            )
            raw_cols = st.columns(min(3, len(raw_downloads)))
            for idx, (label, path) in enumerate(raw_downloads):
                with raw_cols[idx % len(raw_cols)]:
                    with open(path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ {label}",
                            data=f.read(),
                            file_name=os.path.basename(path),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key=f"raw_download_{report_type}_{idx}",
                        )
    else:
        st.warning("선택한 보고서 HTML 파일을 아직 찾지 못했습니다. 먼저 관련 검증을 실행해 주세요.")


__all__ = ["render_builder_tab"]
