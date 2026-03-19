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
