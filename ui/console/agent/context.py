from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from common.run_storage import load_run_contexts_from_supabase
from ui.console.paths import get_project_root


def _agent_runs_root(company_key: str) -> Path:
    return Path(get_project_root()) / "data" / "ops_validation" / company_key / "runs"


def _legacy_pipeline_root(company_key: str) -> Path:
    return Path(get_project_root()) / "data" / "ops_validation" / company_key / "pipeline"


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _load_run_summary_from_history(company_key: str, run_id: str) -> dict[str, Any] | None:
    history_path = _legacy_pipeline_root(company_key) / "console_run_history.jsonl"
    if not history_path.exists():
        return None
    try:
        lines = [line for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return None
    for line in reversed(lines):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(payload.get("run_id") or "").strip() == run_id:
            return payload if isinstance(payload, dict) else None
    return None


def _build_contexts_from_run_summary(company_key: str, run_summary: dict[str, Any], run_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    step_map = {
        str(step.get("module") or ""): (step.get("summary") or {})
        for step in run_summary.get("steps", [])
        if isinstance(step, dict)
    }
    crm_summary = step_map.get("crm", {})
    rx_summary = step_map.get("prescription", {})
    sandbox_summary = step_map.get("sandbox", {})
    territory_summary = step_map.get("territory", {})
    radar_summary = step_map.get("radar", {})
    builder_summary = step_map.get("builder", {})

    evidence_index: list[dict[str, str]] = []
    linked_artifacts: list[dict[str, str]] = []
    if isinstance(builder_summary, dict):
        for report_key in ["crm_analysis", "sandbox_report", "territory_map", "prescription_flow", "radar_report", "total_valid"]:
            item = builder_summary.get(report_key)
            if not isinstance(item, dict):
                continue
            html_path = str(item.get("html") or "").strip()
            if html_path:
                evidence_index.append({"type": report_key, "path": html_path})
                linked_artifacts.append({"type": report_key, "path": html_path})

    overall_status = str(run_summary.get("overall_status", "-")).upper()
    overall_score = float(run_summary.get("overall_score", 0) or 0)
    priority_issues: list[str] = []
    radar_issue = str(radar_summary.get("top_issue") or "").strip()
    if radar_issue:
        priority_issues.append(radar_issue)
    if int(rx_summary.get("connected_hospital_count", 0) or 0) == 0 and int(rx_summary.get("flow_record_count", 0) or 0) > 0:
        priority_issues.append("Prescription 병원 연결 0건")

    key_findings = [
        f"CRM 품질 {crm_summary.get('quality_status', '-')}",
        f"Prescription completion {rx_summary.get('flow_completion_rate', '-')}",
        f"Sandbox 품질 {sandbox_summary.get('quality_status', '-')}",
        f"Territory 품질 {territory_summary.get('quality_status', '-')}",
        f"RADAR top issue: {radar_issue or '-'}",
    ]
    executive_summary = (
        f"{company_key} 최신 run 요약입니다. 전체 상태는 {overall_status}, 점수는 {overall_score:.1f}, "
        f"Prescription 상태는 {str(rx_summary.get('quality_status', '-')).upper()}, "
        f"Sandbox 상태는 {str(sandbox_summary.get('quality_status', '-')).upper()} 입니다."
    )
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    full_ctx = {
        "run_id": run_id,
        "company_key": company_key,
        "mode": run_summary.get("execution_mode", ""),
        "generated_at": generated_at,
        "period": radar_summary.get("period_value", "-"),
        "comparison_period": "-",
        "validation_summary": {
            "overall_status": overall_status,
            "overall_score": overall_score,
        },
        "confidence_grade": "A" if overall_score >= 95 else "B" if overall_score >= 85 else "C",
        "executive_summary": executive_summary,
        "key_findings": key_findings,
        "priority_issues": priority_issues,
        "evidence_index": evidence_index,
        "linked_artifacts": linked_artifacts,
    }
    prompt_ctx = {
        "run_id": run_id,
        "mode": run_summary.get("execution_mode", ""),
        "generated_at": generated_at,
        "period": full_ctx["period"],
        "comparison_period": "-",
        "executive_summary": executive_summary,
        "top_findings": key_findings[:5],
        "priority_issues": priority_issues[:5],
        "answer_scope": "final_report_only",
        "forbidden_actions": ["recalculate_kpi", "raw_rejoin"],
    }
    return full_ctx, prompt_ctx


def _load_run_contexts(company_key: str, run_id: str, run_db_id: str = "") -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if run_db_id:
        full_ctx, prompt_ctx = load_run_contexts_from_supabase(run_db_id)
        if full_ctx or prompt_ctx:
            return full_ctx, prompt_ctx

    run_dir = _agent_runs_root(company_key) / run_id
    full_ctx = _load_json_if_exists(run_dir / "report_context.full.json")
    prompt_ctx = _load_json_if_exists(run_dir / "report_context.prompt.json")
    if full_ctx or prompt_ctx:
        return full_ctx, prompt_ctx

    run_summary = _load_json_if_exists(run_dir / "pipeline_summary.json")
    if run_summary:
        return _build_contexts_from_run_summary(company_key, run_summary, run_id)

    history_summary = _load_run_summary_from_history(company_key, run_id)
    if history_summary:
        return _build_contexts_from_run_summary(company_key, history_summary, run_id)

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


__all__ = ["_load_run_contexts"]
