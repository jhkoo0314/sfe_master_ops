import pandas as pd
import streamlit as st

from ops_core.workflow.execution_registry import (
    get_execution_mode_label,
    get_execution_mode_modules,
)
from ui.console.display import render_block_card, render_page_hero, render_panel_header
from ui.console.paths import get_active_company_name
from ui.console.state import add_log
from ui.console.runner import (
    get_crm_package_status,
    get_source_target_rows,
    run_actual_pipeline,
    save_pipeline_run_history,
)


def render_pipeline_tab() -> None:
    company_name = get_active_company_name()
    render_page_hero(
        "Sales Data OS 실행",
        f"{company_name} 데이터로 Adapter 정규화, Core Engine 계산, Validation Layer (OPS) 검증을 순서대로 실행합니다.",
        "ORCHESTRATION",
    )
    uploaded = st.session_state.uploaded_data
    crm_status = get_crm_package_status(uploaded)
    ready = [k for k, v in uploaded.items() if v is not None]
    current_mode = st.session_state.get("execution_mode", "crm_to_sandbox")
    st.markdown(
        f"""
        <div class="stat-strip">
          <div class="stat-chip"><div class="label">Execution Mode</div><div class="value">{get_execution_mode_label(current_mode)}</div></div>
          <div class="stat-chip"><div class="label">Loaded Files</div><div class="value">{len(ready)} active</div></div>
          <div class="stat-chip"><div class="label">CRM Required</div><div class="value">{'Ready' if crm_status['required_ready'] else 'Need 2 files'}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_run, col_opt = st.columns([2, 1])
    with col_opt:
        render_block_card("실행 옵션", "실패 시 중단 여부와 시작 스텝을 먼저 정합니다.", "Control")
        st.checkbox("FAIL 시 즉시 중단", value=True)
        st.selectbox("시작 STEP", [1, 2, 3, 4, 5], index=0)
    with col_run:
        render_block_card(
            "실행 준비 상태",
            f"현재 실행 모드: {get_execution_mode_label(current_mode)} · 단계: {' -> '.join(get_execution_mode_modules(current_mode)).upper()} · CRM 필수 패키지: {'준비 완료' if crm_status['required_ready'] else '미완성'}",
            "Run Context",
        )

    render_panel_header("실행 전 반영 파일 확인", "업로드한 파일은 source 경로에 반영되고, 없는 항목은 기존 파일을 사용합니다.")
    target_rows = get_source_target_rows(current_mode, uploaded)
    if target_rows:
        st.dataframe(pd.DataFrame(target_rows), use_container_width=True, hide_index=True)

    st.info("실행 버튼을 누르면 상단에 Stop가 보이는 것이 정상입니다. 아래 본문에도 실행 상태를 바로 표시합니다.")

    col_btn1, col_btn2, _ = st.columns([1, 1, 2])
    with col_btn1:
        run_btn = st.button("🚀 파이프라인 실행", type="primary", use_container_width=True)
    with col_btn2:
        reset_btn = st.button("🔄 초기화", use_container_width=True)

    if reset_btn:
        st.session_state.pipeline_result = None
        st.session_state.run_log = []
        for key in st.session_state.module_status:
            st.session_state.module_status[key] = "미실행"
        for key in st.session_state.uploaded_data:
            st.session_state.uploaded_data[key] = None
            st.session_state.uploaded_tokens[key] = None
        st.rerun()

    if run_btn:
        run_status = st.status("Sales Data OS 실행 중", expanded=True)
        run_status.write(f"실행 모드: {get_execution_mode_label(current_mode)}")
        run_status.write("1. 회사별 source 반영 상태를 확인합니다.")
        run_status.write("2. Adapter → Core Engine → Validation Layer 순서로 실행합니다.")
        run_status.write("3. 완료 후 run 저장과 결과 화면 갱신을 수행합니다.")
        try:
            with st.spinner("Sales Data OS 실행 중... (Adapter → Core Engine → Validation Layer)"):
                add_log(f"파이프라인 시작 — 실행 모드: {get_execution_mode_label(current_mode)}")
                result = run_actual_pipeline(execution_mode=current_mode, uploaded=uploaded)
                st.session_state.pipeline_result = result
                for step in result["steps"]:
                    st.session_state.module_status[step["module"]] = step["status"]
                    add_log(f"STEP {step['step']} [{step['module']}] → {step['status']} ({step['score']:.0f}점)")
                history_path = save_pipeline_run_history(result, uploaded)
                add_log(f"실행 이력 저장: {history_path}")
                add_log(f"파이프라인 완료 — 전체: {result['overall_status']}")
            run_status.update(label="Sales Data OS 실행 완료", state="complete", expanded=False)
            st.success(f"✅ 파이프라인 완료 — 전체 상태: **{result['overall_status']}** (점수: {result['overall_score']})")
        except Exception as exc:
            run_status.update(label="Sales Data OS 실행 실패", state="error", expanded=True)
            add_log(f"파이프라인 실패 — {exc}")
            st.error(f"실행 중 오류가 발생했습니다: {exc}")

    result = st.session_state.pipeline_result
    if result:
        render_panel_header("단계별 평가 결과")
        st.markdown('<div class="action-note">각 단계 카드는 html_builder의 리포트 카드처럼 상태가 분리되어 보이도록 간격과 경계선을 더 강하게 주었습니다.</div>', unsafe_allow_html=True)
        for step in result["steps"]:
            s = step["status"]
            css = {"PASS": "step-pass", "WARN": "step-warn", "FAIL": "step-fail", "SKIP": "step-skip"}.get(s, "step-skip")
            icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "⏭️"}.get(s, "⬜")
            dur = step.get("duration_ms", 0)
            st.markdown(f"""<div class="step-card {css}"><strong>STEP {step['step']} — {step['module'].upper()}</strong><span style="float:right;color:#6e7681;font-size:12px">{dur}ms</span><br><small>{icon} {step['reasoning_note']}</small></div>""", unsafe_allow_html=True)
        if result.get("recommended_actions"):
            render_panel_header("권고사항")
            for action in result["recommended_actions"]:
                st.info(action)
        if result.get("final_eligible_modules"):
            render_panel_header("Handoff 가능한 모듈")
            st.markdown(" · ".join([f"**{m}**" for m in result["final_eligible_modules"]]))

    render_panel_header("실행 로그", "최근 로그 30개를 접어서 볼 수 있게 유지했습니다.")
    with st.expander("📋 실행 로그"):
        for log in reversed(st.session_state.run_log[-30:]):
            st.markdown(f"`{log}`")


__all__ = ["render_pipeline_tab"]
