import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st

from ops_core.workflow.execution_registry import (
    get_execution_mode_label,
    get_execution_mode_modules,
)
from ui.console_artifacts import (
    collect_artifact_files,
    get_report_download_paths,
    get_report_output_path,
    get_report_type_artifacts,
    get_report_type_description,
    get_report_type_options,
    load_artifact_preview,
)
from ui.console_display import (
    render_block_card,
    render_page_hero,
    render_panel_header,
    render_stage_badge,
    render_upload_row,
)
from ui.console_paths import (
    get_active_company_key,
    get_active_company_name,
    get_project_root,
    get_source_target_display_path,
)
from ui.console_runner import (
    get_crm_package_status,
    get_source_target_rows,
    run_actual_pipeline,
    save_pipeline_run_history,
)
from ui.console_state import add_log


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


def _agent_runs_root(company_key: str) -> Path:
    return Path(get_project_root()) / "data" / "ops_validation" / company_key / "runs"


def _legacy_pipeline_root(company_key: str) -> Path:
    return Path(get_project_root()) / "data" / "ops_validation" / company_key / "pipeline"


def _normalize_company_key(company_key: str) -> str:
    return company_key.strip().lower().replace("-", "_").replace(" ", "_")


def _resolve_company_key_for_agent(company_key: str) -> str:
    normalized = _normalize_company_key(company_key)
    alias_map = {
        "다온파마": "daon_pharma",
        "다온제약": "daon_pharma",
        "한결파마": "hangyeol_pharma",
        "한결제약": "hangyeol_pharma",
        "daonpharma": "daon_pharma",
        "hangyeolpharma": "hangyeol_pharma",
    }
    if company_key in alias_map:
        normalized = alias_map[company_key]
    elif normalized in alias_map:
        normalized = alias_map[normalized]
    ops_root = Path(get_project_root()) / "data" / "ops_validation"
    if not normalized or not ops_root.exists():
        return normalized

    if (ops_root / normalized).exists():
        return normalized

    for entry in ops_root.iterdir():
        if not entry.is_dir():
            continue
        if _normalize_company_key(entry.name) == normalized:
            return entry.name
    return normalized


def _build_legacy_run_entry(company_key: str, legacy_summary: dict[str, Any], summary_path: Path) -> dict[str, str]:
    overall_score = float(legacy_summary.get("overall_score", 0) or 0)
    overall_status = str(legacy_summary.get("overall_status", "")).upper()
    finished_at = ""
    try:
        finished_at = datetime.fromtimestamp(summary_path.stat().st_mtime).astimezone().isoformat(timespec="seconds")
    except OSError:
        finished_at = ""
    return {
        "run_id": str(legacy_summary.get("run_id") or "legacy-latest"),
        "mode": str(legacy_summary.get("execution_mode", "")),
        "finished_at": finished_at,
        "validation_status": "PASS" if overall_status == "PASS" else "WARN" if overall_status == "WARN" else overall_status or "-",
        "confidence_grade": "A" if overall_score >= 95 else "B" if overall_score >= 85 else "C",
        "storage_type": "legacy",
    }


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _scan_successful_runs(company_key: str) -> list[dict[str, Any]]:
    runs_root = _agent_runs_root(company_key)
    collected: list[dict[str, Any]] = []
    if runs_root.exists():
        for run_dir in runs_root.iterdir():
            if not run_dir.is_dir():
                continue
            run_meta = _load_json_if_exists(run_dir / "run_meta.json")
            if not run_meta:
                continue
            if str(run_meta.get("status", "")).lower() != "success":
                continue
            run_id = str(run_meta.get("run_id") or run_dir.name)
            collected.append(
                {
                    "run_id": run_id,
                    "mode": str(run_meta.get("mode", "")),
                    "finished_at": str(run_meta.get("finished_at", "")),
                    "validation_status": str(run_meta.get("validation_status", "")),
                    "confidence_grade": str(run_meta.get("confidence_grade", "")),
                    "storage_type": "run",
                }
            )

    if collected:
        return sorted(collected, key=lambda item: (item.get("finished_at") or "", item["run_id"]), reverse=True)

    legacy_summary = _load_json_if_exists(_legacy_pipeline_root(company_key) / "pipeline_validation_summary.json")
    if not legacy_summary:
        return []
    summary_path = _legacy_pipeline_root(company_key) / "pipeline_validation_summary.json"
    return [_build_legacy_run_entry(company_key, legacy_summary, summary_path)]


def _agent_history_path(company_key: str, run_id: str) -> Path:
    return _agent_runs_root(company_key) / run_id / "chat" / "agent_chat_history.jsonl"


def _read_agent_history(company_key: str, run_id: str, limit: int = 20) -> list[dict[str, Any]]:
    history_path = _agent_history_path(company_key, run_id)
    if not history_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with history_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return rows[-limit:][::-1]


def _append_agent_history(company_key: str, run_id: str, record: dict[str, Any]) -> None:
    history_path = _agent_history_path(company_key, run_id)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_run_contexts(company_key: str, run_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    run_dir = _agent_runs_root(company_key) / run_id
    full_ctx = _load_json_if_exists(run_dir / "report_context.full.json")
    prompt_ctx = _load_json_if_exists(run_dir / "report_context.prompt.json")
    if full_ctx or prompt_ctx:
        return full_ctx, prompt_ctx

    legacy_summary = _load_json_if_exists(_legacy_pipeline_root(company_key) / "pipeline_validation_summary.json")
    if not legacy_summary:
        return None, None

    stages = legacy_summary.get("stages", {})
    builder_stage = stages.get("builder", {}) if isinstance(stages, dict) else {}
    radar_stage = stages.get("radar", {}) if isinstance(stages, dict) else {}
    territory_stage = stages.get("territory", {}) if isinstance(stages, dict) else {}
    sandbox_stage = stages.get("sandbox", {}) if isinstance(stages, dict) else {}

    linked_artifacts: list[dict[str, str]] = []
    evidence_index: list[dict[str, str]] = []
    if isinstance(builder_stage, dict):
        for key in ["crm_analysis", "sandbox_report", "territory_map", "prescription_flow", "radar_report", "total_valid"]:
            item = builder_stage.get(key)
            if not isinstance(item, dict):
                continue
            html_path = item.get("html")
            if html_path:
                linked_artifacts.append({"type": key, "path": str(html_path)})
                evidence_index.append({"type": key, "path": str(html_path)})

    executive_summary = (
        f"{company_key} run 요약입니다. 전체 상태는 {legacy_summary.get('overall_status', '-')}, "
        f"점수는 {legacy_summary.get('overall_score', '-')}, "
        f"주요 RADAR 이슈는 {radar_stage.get('top_issue', '없음')} 입니다."
    )
    full_ctx = {
        "run_id": run_id,
        "company_key": company_key,
        "mode": legacy_summary.get("execution_mode", ""),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "period": radar_stage.get("period_value", "-"),
        "comparison_period": "-",
        "validation_summary": {"overall_status": legacy_summary.get("overall_status", "-")},
        "confidence_grade": "A" if float(legacy_summary.get("overall_score", 0) or 0) >= 95 else "B",
        "executive_summary": executive_summary,
        "key_findings": [
            f"Sandbox metric month count: {sandbox_stage.get('metric_month_count', '-')}",
            f"Territory quality status: {territory_stage.get('quality_status', '-')}",
            f"RADAR top issue: {radar_stage.get('top_issue', '-')}",
        ],
        "priority_issues": [radar_stage.get("top_issue", "priority issue 없음")],
        "evidence_index": evidence_index,
        "linked_artifacts": linked_artifacts,
    }
    prompt_ctx = {
        "run_id": run_id,
        "mode": legacy_summary.get("execution_mode", ""),
        "generated_at": full_ctx["generated_at"],
        "period": full_ctx["period"],
        "comparison_period": "-",
        "executive_summary": executive_summary,
        "top_findings": full_ctx["key_findings"][:3],
        "priority_issues": full_ctx["priority_issues"][:3],
        "answer_scope": "final_report_only",
        "forbidden_actions": ["recalculate_kpi", "raw_rejoin"],
    }
    return full_ctx, prompt_ctx


def _pick_evidence_items(full_ctx: dict[str, Any] | None, limit: int = 3) -> list[dict[str, str]]:
    if not full_ctx:
        return []
    evidence_index = full_ctx.get("evidence_index", [])
    refs: list[dict[str, str]] = []
    if isinstance(evidence_index, list):
        for item in evidence_index:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            if path:
                refs.append(
                    {
                        "type": str(item.get("type", "evidence")),
                        "path": str(path),
                    }
                )
            if len(refs) >= limit:
                break
    return refs


def _pick_evidence_refs(full_ctx: dict[str, Any] | None, limit: int = 3) -> list[str]:
    return [item["path"] for item in _pick_evidence_items(full_ctx, limit=limit)]


def _build_mock_agent_answer(
    question: str,
    prompt_ctx: dict[str, Any] | None,
    full_ctx: dict[str, Any] | None,
    answer_scope: str,
) -> dict[str, Any]:
    executive_summary = ""
    if isinstance(prompt_ctx, dict):
        executive_summary = str(prompt_ctx.get("executive_summary", "")).strip()
    if not executive_summary and isinstance(full_ctx, dict):
        executive_summary = str(full_ctx.get("executive_summary", "")).strip()
    if not executive_summary:
        executive_summary = "현재 run 문맥에서 요약 본문을 찾지 못했습니다."

    evidence_refs = _pick_evidence_refs(full_ctx, limit=3)
    caution = "이 답변은 report_context 범위 내 mock 해석이며 KPI를 재계산하지 않습니다."
    if answer_scope == "evidence_trace":
        follow_up = "근거 파일 경로를 열어 수치 원문을 확인하세요."
    else:
        follow_up = "필요하면 answer scope를 evidence_trace로 바꿔 근거 중심으로 다시 질문하세요."

    answer_text = (
        "[핵심 답변]\n"
        f"- 질문: {question}\n"
        f"- 요약: {executive_summary}\n\n"
        "[근거]\n"
        + ("\n".join([f"- {ref}" for ref in evidence_refs]) if evidence_refs else "- 근거 인덱스 없음")
        + "\n\n[주의사항]\n"
        f"- {caution}\n\n[추가로 볼 포인트]\n- {follow_up}"
    )
    return {"answer_text": answer_text, "evidence_refs": evidence_refs}


def render_dashboard_tab() -> None:
    render_page_hero(
        "Sales Data OS Console",
        "입력부터 KPI 계산, 검증, 인텔리전스, 렌더링까지 이어지는 전체 흐름을 한 화면에서 점검합니다.",
    )
    result = st.session_state.pipeline_result

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">전체 품질 점수</div><div class="metric-val">{result['overall_score'] if result else '—'}</div><div class="metric-sub">현재 실행 흐름의 평균 평가</div></div>""", unsafe_allow_html=True)
    with col2:
        status = result["overall_status"] if result else "READY"
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(status, "⬜")
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">플랫폼 상태</div><div class="metric-val" style="font-size: 28px;">{icon} {status}</div><div class="metric-sub">최근 실행 결과 기준</div></div>""", unsafe_allow_html=True)
    with col3:
        steps = result["steps"] if result else []
        active_steps = [s for s in steps if s.get("status") != "SKIP"]
        n_pass = sum(1 for s in active_steps if s.get("status") == "PASS")
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">통과 단계</div><div class="metric-val">{n_pass}/{len(active_steps) if active_steps else '—'}</div><div class="metric-sub">실행 대상 단계 기준</div></div>""", unsafe_allow_html=True)
    with col4:
        dur = f"{result['total_duration_ms']}ms" if result else "—"
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">총 실행 시간</div><div class="metric-val">{dur}</div><div class="metric-sub">현재 선택 흐름 전체 시간</div></div>""", unsafe_allow_html=True)

    render_panel_header(
        "Sales Data OS 레이어 흐름",
        "Data Layer → Adapter Layer → Core Engine Layer → Validation Layer → Intelligence Layer → Presentation Layer 흐름을 한 화면에서 확인합니다.",
    )
    flow_html = dedent(
        """
        <div class="os-flow-shell">
          <div class="os-flow-grid">
            <div class="os-flow-row row-top">
              <div class="os-layer-card layer-data">
                <div class="os-layer-step">L1</div>
                <div class="os-layer-title">Data Layer</div>
                <div class="os-layer-copy">CRM / Sales / Target / Prescription 원천 데이터 집합</div>
                <div class="os-layer-tags"><span>Raw</span><span>Source</span></div>
              </div>
              <div class="os-layer-link">&rarr;</div>
              <div class="os-layer-card layer-adapter">
                <div class="os-layer-step">L2</div>
                <div class="os-layer-title">Adapter Layer</div>
                <div class="os-layer-copy">원천 컬럼을 표준 스키마로 정렬하고 의미를 보존</div>
                <div class="os-layer-tags"><span>Normalize</span><span>Standard</span></div>
              </div>
              <div class="os-layer-link">&rarr;</div>
              <div class="os-layer-card layer-kpi">
                <div class="os-layer-step">L3</div>
                <div class="os-layer-title">Core Engine Layer</div>
                <div class="os-layer-copy">KPI Module이 공식 지표를 단일 소스로 계산</div>
                <div class="os-layer-tags"><span>KPI</span><span>Single Source</span></div>
              </div>
            </div>

            <div class="os-flow-turn">&darr;</div>

            <div class="os-flow-row row-bottom">
              <div class="os-layer-card layer-builder">
                <div class="os-layer-step">L6</div>
                <div class="os-layer-title">Presentation Layer</div>
                <div class="os-layer-copy">Builder가 승인된 payload를 HTML로 렌더링</div>
                <div class="os-layer-tags"><span>Render-only</span><span>Preview</span></div>
              </div>
              <div class="os-layer-link">&larr;</div>
              <div class="os-layer-card layer-intel">
                <div class="os-layer-step">L5</div>
                <div class="os-layer-title">Intelligence Layer</div>
                <div class="os-layer-copy">Sandbox / Territory / Prescription / RADAR 분석</div>
                <div class="os-layer-tags"><span>Insight</span><span>Signal</span></div>
              </div>
              <div class="os-layer-link">&larr;</div>
              <div class="os-layer-card layer-ops">
                <div class="os-layer-step">L4</div>
                <div class="os-layer-title">Validation Layer</div>
                <div class="os-layer-copy">품질 검증, 매핑 검증, 전달 가능 여부 판단</div>
                <div class="os-layer-tags"><span>Quality Gate</span><span>Handoff</span></div>
              </div>
            </div>
          </div>
          <div class="os-flow-note">KPI는 Core Engine에서 1회 계산되고, OPS는 검증/오케스트레이션만 수행합니다. 이후 Intelligence와 Builder가 승인 결과를 소비합니다.</div>
        </div>
        """
    )
    if hasattr(st, "html"):
        st.html(flow_html)
    else:
        st.markdown(flow_html, unsafe_allow_html=True)

    if result and result.get("recommended_actions"):
        render_panel_header("AI 기반 운영 최적화 제언")
        for action in result["recommended_actions"]:
            st.markdown(f"""<div class="insight-card"><span>{action}</span></div>""", unsafe_allow_html=True)


def render_upload_tab() -> None:
    company_name = get_active_company_name()
    render_page_hero(
        "RAW 데이터 투입",
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
    render_upload_row("crm_activity", "crm_activity_up", "CRM 활동 원본", "필수", "방문, 디테일, 통화 같은 활동 로그", get_source_target_display_path("crm_activity"), ["방문일, 담당자명 또는 담당자ID", "방문기관명, 기관코드, 주소 중 하나 이상", "활동유형(방문, 디테일, 미팅 등)"], ["월별 합계보다 활동 한 줄 한 줄이 남아 있는 원본이 좋습니다.", "가공 요약표보다 시스템 추출 원본이 더 적합합니다."], "CRM 활동 업로드")
    render_upload_row("crm_rep_master", "crm_rep_master_up", "담당자 / 조직 마스터", "필수", "담당자, 지점, 팀 기준 파일", get_source_target_display_path("crm_rep_master"), ["담당자 ID, 담당자명", "지점명, 팀명, 조직코드", "직무 또는 역할"], ["CRM 활동 파일과 연결하려면 담당자 코드가 살아 있는 편이 좋습니다."], "담당자 마스터 업로드")
    render_upload_row("crm_account_assignment", "crm_assignment_up", "거래처 / 병원 담당 배정", "권장", "병원과 담당자를 연결하는 파일", get_source_target_display_path("crm_account_assignment"), ["병원코드 또는 거래처코드", "병원명 또는 거래처명", "담당자 ID 또는 담당자명"], ["있으면 CRM 연결 정확도가 높아집니다."], "담당 배정 업로드")
    render_upload_row("crm_rules", "crm_rules_up", "CRM 규칙 / KPI 설정", "선택", "방문 인정 기준과 KPI 규칙", get_source_target_display_path("crm_rules"), ["방문 점수 규칙", "활동 유형별 가중치", "월별 KPI 기준"], ["없으면 기본 규칙으로도 검증은 가능합니다."], "CRM 규칙 업로드")

    render_panel_header("Sandbox 입력")
    render_upload_row("sales", "sales_up", "실적(매출) 데이터", "필수", "병원/거래처 단위 매출 원본", get_source_target_display_path("sales"), ["거래처코드 또는 병원코드", "품목코드 또는 품목명", "매출금액, 매출월 또는 매출일"], ["지점별 합계보다 거래처 단위 원본이 좋습니다."], "실적 파일 업로드")
    render_upload_row("target", "target_up", "목표 데이터", "필수", "목표 금액이나 목표 수량 파일", get_source_target_display_path("target"), ["월 목표 또는 분기 목표", "담당자 ID/이름, 병원코드, 품목 중 일부", "목표금액 또는 목표수량"], ["실적과 비교할 수 있게 기간 컬럼이 있으면 좋습니다."], "목표 파일 업로드")

    render_panel_header("Prescription 입력")
    render_upload_row("prescription", "rx_up", "Prescription 데이터", "선택", "도매 -> 약국 흐름을 추적하는 출고 파일", get_source_target_display_path("prescription"), ["출고일, 도매상명, 약국명", "품목명 또는 SKU", "수량, 출고금액, 공급금액"], ["PDF 흐름 추적이 필요할 때만 사용합니다."], "Prescription 파일 업로드")

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
    report_filters = _build_period_filter_defaults(period_mode, selected_year, selected_sub_period)
    st.markdown(
        f"""<div class="action-note"><b>{report_type}</b><br>{get_report_type_description(report_type)}<br><br>선택 기간: <b>{report_period}</b><br>{get_report_type_artifacts(report_type)}</div>""",
        unsafe_allow_html=True,
    )

    if report_output_path and os.path.exists(report_output_path):
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


def render_agent_tab() -> None:
    company_name = get_active_company_name()
    raw_company_key = get_active_company_key().strip()
    company_key = _resolve_company_key_for_agent(raw_company_key)
    render_page_hero(
        "Agent (Final Report 해석)",
        f"{company_name} 실행(run) 단위 결과를 기준으로 질문/답변을 확인합니다. Agent는 계산이 아니라 해석 레이어입니다.",
        "AGENT",
    )

    render_panel_header("Agent Context")
    st.caption(f"입력 회사 코드: `{raw_company_key or '-'}` | 해석된 회사 코드: `{company_key or '-'}` | 기준: `회사 코드`")
    legacy_summary_path = _legacy_pipeline_root(company_key) / "pipeline_validation_summary.json" if company_key else None
    runs_root_path = _agent_runs_root(company_key) if company_key else None
    st.caption(
        f"runs 경로: `{runs_root_path if runs_root_path else '-'}` | "
        f"legacy 요약: `{legacy_summary_path if legacy_summary_path else '-'}` | "
        f"legacy 존재: `{legacy_summary_path.exists() if legacy_summary_path else False}`"
    )

    runs = _scan_successful_runs(company_key) if company_key else []
    if not runs and legacy_summary_path and legacy_summary_path.exists():
        legacy_summary = _load_json_if_exists(legacy_summary_path)
        if legacy_summary:
            forced_entry = _build_legacy_run_entry(company_key, legacy_summary, legacy_summary_path)
            forced_entry["storage_type"] = "legacy-forced"
            runs = [forced_entry]
    run_ids = [item["run_id"] for item in runs]
    saved_run_id = st.session_state.get("selected_run_id", "")
    default_index = run_ids.index(saved_run_id) if saved_run_id in run_ids else 0
    has_ready_run = bool(company_key and runs)

    def _run_label(run_id: str) -> str:
        row = next((item for item in runs if item["run_id"] == run_id), None)
        if not row:
            return run_id
        return f"{run_id} | {row.get('mode', '-') or '-'} | {row.get('finished_at', '-') or '-'}"

    render_panel_header("Run Selection")
    if has_ready_run:
        st.markdown(
            f"""<div class="run-selector-note"><b>선택 가능한 run:</b> {len(run_ids)}건<br>현재는 {'단일 run이 자동 선택된 상태입니다.' if len(run_ids) == 1 else '드롭다운에서 run을 바꿀 수 있습니다.'}</div>""",
            unsafe_allow_html=True,
        )
        selected_run_id = st.selectbox("Run 선택", options=run_ids, index=default_index, format_func=_run_label)
        selected_run = next((item for item in runs if item["run_id"] == selected_run_id), runs[0])
        needs_reload = (
            st.session_state.get("selected_run_id") != selected_run_id
            or st.session_state.get("report_context_prompt") is None
        )
        if needs_reload:
            full_ctx, prompt_ctx = _load_run_contexts(company_key, selected_run_id)
            st.session_state.selected_run_id = selected_run_id
            st.session_state.selected_mode = str(selected_run.get("mode", ""))
            st.session_state.report_context_full = full_ctx
            st.session_state.report_context_prompt = prompt_ctx
            st.session_state.agent_history = _read_agent_history(company_key, selected_run_id, limit=20)
    else:
        st.markdown(
            """<div class="run-selector-note"><b>선택 가능한 run:</b> 0건<br>run 기반 저장 또는 legacy 요약 파일이 아직 없습니다.</div>""",
            unsafe_allow_html=True,
        )
        st.selectbox("Run 선택", options=["(선택 가능한 run 없음)"], index=0, disabled=True)
        selected_run = {"mode": "-", "validation_status": "-", "confidence_grade": "-"}
        st.session_state.selected_run_id = ""
        st.session_state.selected_mode = ""
        st.session_state.report_context_full = None
        st.session_state.report_context_prompt = None
        st.session_state.agent_history = []

    full_ctx = st.session_state.get("report_context_full")
    prompt_ctx = st.session_state.get("report_context_prompt")
    mode_text = st.session_state.get("selected_mode") or "-"
    period_text = "-"
    comparison_text = "-"
    if isinstance(full_ctx, dict):
        period_text = str(full_ctx.get("period") or "-")
        comparison_text = str(full_ctx.get("comparison_period") or "-")
    elif isinstance(prompt_ctx, dict):
        period_text = str(prompt_ctx.get("period") or "-")
        comparison_text = str(prompt_ctx.get("comparison_period") or "-")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">Run Mode</div><div class="metric-val" style="font-size:20px">{mode_text}</div><div class="metric-sub">선택된 실행 모드</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">Period</div><div class="metric-val" style="font-size:20px">{period_text}</div><div class="metric-sub">보고 기준 기간</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">Comparison</div><div class="metric-val" style="font-size:20px">{comparison_text}</div><div class="metric-sub">비교 기간</div></div>""", unsafe_allow_html=True)
    with col4:
        validation_text = selected_run.get("validation_status") or "-"
        confidence_text = selected_run.get("confidence_grade") or "-"
        st.markdown(f"""<div class="metric-card"><div class="metric-lbl">Validation / Confidence</div><div class="metric-val" style="font-size:20px">{validation_text} / {confidence_text}</div><div class="metric-sub">run_meta 기준</div></div>""", unsafe_allow_html=True)

    render_panel_header("Step5 안정화 상태")
    st.info("run 선택, 컨텍스트 로딩, 질문/응답(mock), run별 jsonl 저장이 연결되어 있고 손상/누락 케이스에서도 화면이 유지되도록 방어하고 있습니다.")

    if not company_key:
        st.warning("먼저 사이드바에서 회사 코드(company_key)를 입력해 주세요.")
    elif not runs:
        st.warning("성공한 run을 찾지 못했습니다. 먼저 파이프라인을 실행해 주세요.")
    if has_ready_run and not isinstance(prompt_ctx, dict):
        st.warning("report_context.prompt.json을 읽지 못했습니다. 해당 run의 Builder 산출물을 확인해 주세요.")
    if has_ready_run and not isinstance(full_ctx, dict):
        st.info("report_context.full.json이 없거나 읽기 실패했습니다. Step2에서는 prompt 기준 최소 표시만 유지합니다.")

    scope = st.selectbox(
        "답변 범위 (scope)",
        options=["final_report_only", "evidence_trace"],
        index=0 if st.session_state.get("current_answer_scope") != "evidence_trace" else 1,
        disabled=not has_ready_run,
    )
    st.session_state.current_answer_scope = scope
    context_ready = has_ready_run and isinstance(prompt_ctx, dict)
    question = st.text_area(
        "질문 입력",
        height=100,
        placeholder="예: 이번 run에서 가장 우선순위가 높은 이슈를 쉽게 설명해줘",
        disabled=not context_ready,
    )
    ask = st.button("질문하기", type="primary", disabled=not context_ready)
    if ask:
        if not question.strip():
            st.warning("질문을 먼저 입력해 주세요.")
        else:
            answer = _build_mock_agent_answer(question.strip(), prompt_ctx, full_ctx, scope)
            record = {
                "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "run_id": st.session_state.get("selected_run_id", ""),
                "mode": mode_text,
                "question": question.strip(),
                "answer": answer["answer_text"],
                "answer_scope": scope,
                "evidence_refs": answer["evidence_refs"],
                "provider": "mock",
                "model": "local-context-only",
            }
            if company_key and st.session_state.get("selected_run_id"):
                _append_agent_history(company_key, st.session_state["selected_run_id"], record)
            st.session_state.agent_history = [record] + st.session_state.get("agent_history", [])
            st.session_state.agent_history = st.session_state.agent_history[:20]
            st.success("답변을 생성했고 run 이력(jsonl)에 저장했습니다.")

    render_panel_header("근거 요약 (상위 3개)")
    evidence_items = _pick_evidence_items(full_ctx, limit=3)
    if evidence_items:
        for item in evidence_items:
            st.markdown(
                f"""<div class="evidence-pill"><b>{item['type']}</b><br>{item['path']}</div>""",
                unsafe_allow_html=True,
            )
    else:
        st.info("evidence_index를 찾지 못했습니다. Step4에서 표시 고도화 예정입니다.")

    render_panel_header("대화 이력 (최신 20개)")
    history = st.session_state.get("agent_history", [])
    if not history:
        st.info("아직 저장된 대화가 없습니다.")
        return
    for idx, item in enumerate(history, start=1):
        created_at = item.get("created_at", "-")
        with st.expander(f"{idx}. {created_at} | {item.get('answer_scope', '-')}", expanded=(idx == 1)):
            st.markdown(f"**질문**\n\n{item.get('question', '')}")
            st.markdown(f"**답변**\n\n{item.get('answer', '')}")
            refs = item.get("evidence_refs", [])
            if refs:
                st.markdown("**근거 파일**")
                for ref in refs:
                    st.markdown(f"""<div class="evidence-pill"><b>evidence</b><br>{ref}</div>""", unsafe_allow_html=True)
