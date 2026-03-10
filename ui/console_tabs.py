import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from ui.console_shared import (
    add_log,
    collect_artifact_files,
    get_active_company_key,
    get_active_company_name,
    get_crm_package_status,
    get_execution_mode_label,
    get_execution_mode_modules,
    get_source_target_rows,
    get_report_output_path,
    get_report_type_artifacts,
    get_report_type_description,
    get_report_type_options,
    load_artifact_preview,
    render_block_card,
    render_page_hero,
    render_panel_header,
    render_stage_badge,
    render_upload_row,
    run_actual_pipeline,
    save_pipeline_run_history,
)


def _build_period_filter_defaults(period_mode: str, selected_year: str, selected_sub_period: str) -> dict:
    defaults = {
        "period_mode": "all",
        "year": selected_year or "",
        "month": "",
        "quarter": "",
    }
    if period_mode == "연간":
        defaults["period_mode"] = "year"
    elif period_mode == "분기별":
        defaults["period_mode"] = "quarter"
        quarter_map = {"1분기": "Q1", "2분기": "Q2", "3분기": "Q3", "4분기": "Q4"}
        defaults["quarter"] = f"{selected_year}-{quarter_map.get(selected_sub_period, 'Q1')}" if selected_year else ""
    elif period_mode == "월별":
        defaults["period_mode"] = "month"
        month_num = selected_sub_period.replace("월", "").zfill(2)
        defaults["month"] = f"{selected_year}-{month_num}" if selected_year else ""
    return defaults


def _materialize_periodized_report(report_output_path: str, report_period: str, report_filters: dict) -> str:
    source_path = Path(report_output_path)
    if not source_path.exists():
        return report_output_path
    if report_filters.get("period_mode") == "all":
        return report_output_path

    safe_period = (
        report_period.replace(" ", "_")
        .replace("년", "")
        .replace("월", "")
        .replace("분기", "Q")
        .replace("/", "_")
    )
    target_path = source_path.with_name(f"{source_path.stem}__{safe_period}{source_path.suffix}")
    html = source_path.read_text(encoding="utf-8")
    injected = (
        "<script>"
        f"window.__OPS_DEFAULT_FILTER__ = {json.dumps(report_filters, ensure_ascii=False)};"
        "</script>\n</head>"
    )
    if "window.__OPS_DEFAULT_FILTER__" in html:
        materialized = html
    else:
        materialized = html.replace("</head>", injected, 1)
    target_path.write_text(materialized, encoding="utf-8")
    return str(target_path)


def render_dashboard_tab() -> None:
    render_page_hero(
        "SFE OPS 엔진 가동 지표",
        "html_builder의 다크 콘솔 톤을 그대로 가져와, 운영 상태와 전략 흐름이 한눈에 들어오도록 재구성한 메인 대시보드입니다.",
        "LIVE CONSOLE",
    )
    result = st.session_state.pipeline_result

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">전략적 정확성</div><div class="metric-val">{result['overall_score'] if result else '—'}</div><div class="metric-sub">전체 파이프라인 평균 점수</div></div>""", unsafe_allow_html=True)
    with col2:
        status = result["overall_status"] if result else "READY"
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(status, "⬜")
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">엔진 상태</div><div class="metric-val" style="font-size: 28px;">{icon} {status}</div><div class="metric-sub">최신 실행 결과 기준</div></div>""", unsafe_allow_html=True)
    with col3:
        n_pass = sum(1 for s in (result["steps"] if result else []) if s["status"] == "PASS")
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">검증 통과 모듈</div><div class="metric-val">{n_pass}/5</div><div class="metric-sub">핸드오프 가능한 단계 수</div></div>""", unsafe_allow_html=True)
    with col4:
        dur = f"{result['total_duration_ms']}ms" if result else "—"
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">엔진 응답 속도</div><div class="metric-val">{dur}</div><div class="metric-sub">전체 파이프라인 수행 시간</div></div>""", unsafe_allow_html=True)

    render_panel_header("SFE 전략 피드백 루프", "실제 OPS 흐름에 맞춰 입력, 정규화, 샌드박스 판단, 산출물 핸드오프 단계로 다시 구성했습니다.")
    st.markdown(
        """
        <div class="ops-network">
          <div class="ops-world">
            <div class="flow-stage">
              <div class="stage-kicker">Stage 01</div>
              <div class="stage-title">Data Intake</div>
              <div class="stage-copy">현장 데이터와 시스템 데이터를 먼저 어댑터가 수집합니다.</div>
              <div class="flow-list">
                <div class="flow-chip"><div class="chip-name">CRM 활동</div><div class="chip-meta">방문, 디테일링, 담당자 실행 로그</div></div>
                <div class="flow-chip"><div class="chip-name">실적 / 목표</div><div class="chip-meta">매출 기준과 목표 기준을 함께 확보</div></div>
                <div class="flow-chip"><div class="chip-name">Prescription</div><div class="chip-meta">선택 입력, 흐름 연결 검증 강화</div></div>
              </div>
            </div>
            <div class="flow-arrow">→</div>
            <div class="decision-core">
              <div class="core-icon">🔬</div>
              <div class="core-title">Sandbox Decision Engine</div>
              <div class="core-copy">정규화된 데이터를 검증하고, 점수와 이유를 만든 뒤 다음 모듈 핸드오프 여부를 결정합니다.</div>
              <div class="decision-badges"><span>Normalize</span><span>Scoring</span><span>Handoff</span></div>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-stage">
              <div class="stage-kicker">Stage 03</div>
              <div class="stage-title">Operational Outputs</div>
              <div class="stage-copy">판단 결과가 권역 최적화와 최종 결과물 생성으로 이어집니다.</div>
              <div class="flow-list">
                <div class="flow-chip"><div class="chip-name">Territory</div><div class="chip-meta">권역 성과, 미커버 병원, 방문 재배치</div></div>
                <div class="flow-chip"><div class="chip-name">Builder</div><div class="chip-meta">HTML 보고서 결과물 생성</div></div>
                <div class="flow-chip"><div class="chip-name">Feedback Loop</div><div class="chip-meta">결과 확인 후 다시 입력 품질을 보강</div></div>
              </div>
            </div>
          </div>
          <div class="helper-note" style="text-align:center; margin-top:18px;">입력 데이터가 Sandbox를 거쳐 Territory와 Builder로 전달되고, 결과가 다시 입력 품질 개선으로 연결되는 OPS 루프입니다.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if result and result.get("recommended_actions"):
        render_panel_header("AI 기반 운영 최적화 제언")
        for action in result["recommended_actions"]:
            st.markdown(f"""<div class="insight-card"><span>{action}</span></div>""", unsafe_allow_html=True)


def render_upload_tab() -> None:
    company_key = get_active_company_key()
    company_name = get_active_company_name()
    render_page_hero(
        "원천 데이터 투입",
        f"{company_name} 원천 데이터를 회사별 폴더에 연결합니다. 검증 단계에서는 항목명, 짧은 설명, 업로드창을 한 줄에 두고 필요한 예시만 펼쳐서 봅니다.",
        "DATA ADAPTER",
    )
    render_panel_header("업로드 목록", "실행할 흐름에 필요한 원천 파일만 올리면 됩니다. 같은 파일을 여러 항목에 써도 됩니다.")
    crm_status = get_crm_package_status(st.session_state.uploaded_data)
    loaded_count = sum(1 for v in st.session_state.uploaded_data.values() if v is not None)
    st.markdown(
        f"""
        <div class="stat-strip">
          <div class="stat-chip"><div class="label">Loaded Files</div><div class="value">{loaded_count} / 7</div></div>
          <div class="stat-chip"><div class="label">Adapter Mode</div><div class="value">Standard Normalize</div></div>
          <div class="stat-chip"><div class="label">CRM Package</div><div class="value">{crm_status['package_count']} / 4</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="action-note">원본 추출 파일 우선 · 중복 업로드 허용 · 자세한 설명은 각 항목의 예시에서 확인</div>', unsafe_allow_html=True)

    render_panel_header("CRM 패키지", f"필수 2개, 권장 1개, 선택 1개 구조입니다. 현재 상태: {'필수 준비 완료' if crm_status['required_ready'] else '필수 미완성'}")
    render_upload_row("crm_activity", "crm_activity_up", "CRM 활동 원본", "필수", "방문, 디테일, 통화 같은 활동 로그", fr"data\company_source\{company_key}\crm\hangyeol_crm_activity_raw.xlsx", ["방문일, 담당자명 또는 담당자ID", "방문기관명, 기관코드, 주소 중 하나 이상", "활동유형(방문, 디테일, 미팅 등)"], ["월별 합계보다 활동 한 줄 한 줄이 남아 있는 원본이 좋습니다.", "가공 요약표보다 시스템 추출 원본이 더 적합합니다."], "CRM 활동 업로드")
    render_upload_row("crm_rep_master", "crm_rep_master_up", "담당자 / 조직 마스터", "필수", "담당자, 지점, 팀 기준 파일", fr"data\company_source\{company_key}\company\hangyeol_company_assignment_raw.xlsx", ["담당자 ID, 담당자명", "지점명, 팀명, 조직코드", "직무 또는 역할"], ["CRM 활동 파일과 연결하려면 담당자 코드가 살아 있는 편이 좋습니다."], "담당자 마스터 업로드")
    render_upload_row("crm_account_assignment", "crm_assignment_up", "거래처 / 병원 담당 배정", "권장", "병원과 담당자를 연결하는 파일", fr"data\company_source\{company_key}\company\hangyeol_account_master.xlsx", ["병원코드 또는 거래처코드", "병원명 또는 거래처명", "담당자 ID 또는 담당자명"], ["있으면 CRM 연결 정확도가 높아집니다."], "담당 배정 업로드")
    render_upload_row("crm_rules", "crm_rules_up", "CRM 규칙 / KPI 설정", "선택", "방문 인정 기준과 KPI 규칙", fr"data\company_source\{company_key}\company\hangyeol_crm_rules_raw.xlsx", ["방문 점수 규칙", "활동 유형별 가중치", "월별 KPI 기준"], ["없으면 기본 규칙으로도 검증은 가능합니다."], "CRM 규칙 업로드")

    render_panel_header("Sandbox 입력")
    render_upload_row("sales", "sales_up", "실적(매출) 데이터", "필수", "병원/거래처 단위 매출 원본", fr"data\company_source\{company_key}\sales\hangyeol_sales_raw.xlsx", ["거래처코드 또는 병원코드", "품목코드 또는 품목명", "매출금액, 매출월 또는 매출일"], ["지점별 합계보다 거래처 단위 원본이 좋습니다."], "실적 파일 업로드")
    render_upload_row("target", "target_up", "목표 데이터", "필수", "목표 금액이나 목표 수량 파일", fr"data\company_source\{company_key}\target\hangyeol_target_raw.xlsx", ["월 목표 또는 분기 목표", "담당자 ID/이름, 병원코드, 품목 중 일부", "목표금액 또는 목표수량"], ["실적과 비교할 수 있게 기간 컬럼이 있으면 좋습니다."], "목표 파일 업로드")

    render_panel_header("Prescription 입력")
    render_upload_row("prescription", "rx_up", "Prescription 데이터", "선택", "도매 -> 약국 흐름을 추적하는 출고 파일", fr"data\company_source\{company_key}\company\hangyeol_fact_ship_raw.csv", ["출고일, 도매상명, 약국명", "품목명 또는 SKU", "수량, 출고금액, 공급금액"], ["PDF 흐름 추적이 필요할 때만 사용합니다."], "Prescription 파일 업로드")

    render_panel_header("고급 설정", "기본적으로는 어댑터가 자동 정규화를 시도합니다. 이 영역은 정말 예외적인 컬럼명 차이가 있을 때만 사용합니다.")
    with st.expander("고급 설정: 컬럼 매핑", expanded=False):
        st.markdown('<div class="action-note">현재 검증 단계에서는 대부분 입력하지 않아도 됩니다. 실제 회사 파일 컬럼명이 표준과 크게 다를 때만 수동으로 조정하세요.</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.text_input("병원 ID 컬럼", value="hospital_id", key="sales_hosp_col")
            st.text_input("병원명 컬럼 (대체용)", value="hospital_name", key="sales_name_col")
        with c2:
            st.text_input("제품 ID 컬럼", value="product_id", key="sales_prod_col")
            st.text_input("금액 컬럼", value="sales_amount", key="sales_amt_col")
        with c3:
            st.text_input("월 컬럼 (YYYYMM)", value="yyyymm", key="sales_month_col")
            st.text_input("담당자 ID 컬럼", value="rep_id", key="sales_rep_col")

    render_panel_header("투입 현황")
    status_data = {
        "입력 묶음": ["CRM 활동 원본", "담당자/조직 마스터", "거래처 담당 배정", "CRM 규칙/KPI", "실적", "목표", "Prescription"],
        "상태": [
            "✅ 업로드됨" if st.session_state.uploaded_data["crm_activity"] else "⬜ 필수",
            "✅ 업로드됨" if st.session_state.uploaded_data["crm_rep_master"] else "⬜ 필수",
            "✅ 업로드됨" if st.session_state.uploaded_data["crm_account_assignment"] else "⬜ 권장",
            "✅ 업로드됨" if st.session_state.uploaded_data["crm_rules"] else "⬜ 선택",
            "✅ 업로드됨" if st.session_state.uploaded_data["sales"] else "⬜ 대기",
            "✅ 업로드됨" if st.session_state.uploaded_data["target"] else "⬜ 대기",
            "✅ 업로드됨" if st.session_state.uploaded_data["prescription"] else "⬜ 선택사항",
        ],
        "건수": [
            st.session_state.uploaded_data["crm_activity"]["row_count"] if st.session_state.uploaded_data["crm_activity"] else 0,
            st.session_state.uploaded_data["crm_rep_master"]["row_count"] if st.session_state.uploaded_data["crm_rep_master"] else 0,
            st.session_state.uploaded_data["crm_account_assignment"]["row_count"] if st.session_state.uploaded_data["crm_account_assignment"] else 0,
            st.session_state.uploaded_data["crm_rules"]["row_count"] if st.session_state.uploaded_data["crm_rules"] else 0,
            st.session_state.uploaded_data["sales"]["row_count"] if st.session_state.uploaded_data["sales"] else 0,
            st.session_state.uploaded_data["target"]["row_count"] if st.session_state.uploaded_data["target"] else 0,
            st.session_state.uploaded_data["prescription"]["row_count"] if st.session_state.uploaded_data["prescription"] else 0,
        ],
    }
    st.dataframe(pd.DataFrame(status_data), use_container_width=True, hide_index=True)


def render_pipeline_tab() -> None:
    company_name = get_active_company_name()
    render_page_hero("OPS 파이프라인 실행", f"{company_name} 원천 파일을 실제 source 경로에 반영한 뒤, 정규화와 검증 스크립트를 순서대로 실행합니다.", "ENGINE RUN")
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
        render_block_card("실행 준비 상태", f"현재 실행 모드는 {get_execution_mode_label(current_mode)} 입니다. 선택 흐름은 {' -> '.join(get_execution_mode_modules(current_mode)).upper()} 이고, CRM 필수 패키지는 {'준비 완료' if crm_status['required_ready'] else '미완성'} 상태입니다.", "Run Context")

    render_panel_header("실행 전 반영 파일 확인", "실행을 누르면 아래 경로에 업로드 파일이 반영됩니다. 업로드하지 않은 항목은 기존 source 파일을 그대로 사용합니다.")
    target_rows = get_source_target_rows(current_mode, uploaded)
    if target_rows:
        st.dataframe(pd.DataFrame(target_rows), use_container_width=True, hide_index=True)

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
        try:
            with st.spinner("OPS 파이프라인 실행 중..."):
                add_log(f"파이프라인 시작 — 실행 모드: {get_execution_mode_label(current_mode)}")
                result = run_actual_pipeline(execution_mode=current_mode, uploaded=uploaded)
                st.session_state.pipeline_result = result
                for step in result["steps"]:
                    st.session_state.module_status[step["module"]] = step["status"]
                    add_log(f"STEP {step['step']} [{step['module']}] → {step['status']} ({step['score']:.0f}점)")
                history_path = save_pipeline_run_history(result, uploaded)
                add_log(f"실행 이력 저장: {history_path}")
                add_log(f"파이프라인 완료 — 전체: {result['overall_status']}")
            st.success(f"✅ 파이프라인 완료 — 전체 상태: **{result['overall_status']}** (점수: {result['overall_score']})")
        except Exception as exc:
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


def render_artifacts_tab() -> None:
    render_page_hero("분석 산출물 미리보기", "이 탭은 차트보다 산출물 확인에 집중합니다. 정규화 파일, 검증 결과 파일, Builder 결과를 10행 미리보기와 다운로드로 확인합니다.", "ANALYTICS")
    result = st.session_state.pipeline_result
    if not result:
        st.info("먼저 파이프라인을 실행하세요.")
        return

    execution_mode = st.session_state.get("execution_mode", "crm_to_sandbox")
    artifacts = collect_artifact_files(execution_mode)
    render_panel_header("산출물 브라우저", f"선택한 흐름은 {get_execution_mode_label(execution_mode)} 입니다. 아래 파일은 해당 흐름과 관련된 정규화 파일 및 검증 산출물입니다.")
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


def render_builder_tab() -> None:
    render_page_hero("HTML 보고서 생성", "이 탭은 검증이 끝난 결과물을 HTML 보고서로 확인하는 마지막 단계입니다. 슬라이드 자동화는 현재 범위에서 제외했습니다.", "BUILDER HANDOFF")
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

    render_block_card("📊 OPS 분석 보고서", "현재 검증이 끝난 결과물 중 어떤 HTML 보고서를 열고 확인할지 선택하는 블록입니다.", "Output Block 01")
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
    report_filters = _build_period_filter_defaults(period_mode, selected_year, selected_sub_period)
    st.markdown(
        f"""<div class="action-note"><b>{report_type}</b><br>{get_report_type_description(report_type)}<br><br>선택 기간: <b>{report_period}</b><br>{get_report_type_artifacts(report_type)}</div>""",
        unsafe_allow_html=True,
    )

    if report_type == "통합 검증 보고서":
        st.info("통합 검증 보고서는 현재 개별 HTML 1장이 아니라 요약 JSON/검증 산출물 묶음 기준입니다.")
    elif report_output_path and os.path.exists(report_output_path):
        effective_report_path = _materialize_periodized_report(report_output_path, report_period, report_filters)
        base_name, ext = os.path.splitext(os.path.basename(report_output_path))
        safe_period = (
            report_period.replace(" ", "_")
            .replace("년", "")
            .replace("월", "")
            .replace("분기", "Q")
            .replace("전체", "all")
            .replace("/", "_")
        )
        download_name = f"{base_name}_{safe_period}{ext}"
        col_open, col_download = st.columns(2)
        with col_open:
            if st.button("🌐 선택한 보고서 열기", disabled=not builder_eligible, use_container_width=True):
                subprocess.Popen(["start", effective_report_path], shell=True)
                st.info(f"브라우저에서 '{report_type}' 보고서를 엽니다. 선택 기간: {report_period}")
                add_log(f"보고서 열기: {report_type} ({report_period})")
        with col_download:
            with open(effective_report_path, "rb") as f:
                st.download_button(
                    label="⬇️ 생성된 보고서 다운로드",
                    data=f.read(),
                    file_name=download_name,
                    mime="text/html",
                    disabled=not builder_eligible,
                    use_container_width=True,
                )
    else:
        st.warning("선택한 보고서 HTML 파일을 아직 찾지 못했습니다. 먼저 관련 검증을 실행해 주세요.")
