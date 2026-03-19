from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from common.company_registry import resolve_company_reference
from common.run_storage import list_successful_runs_from_supabase
from ui.console.paths import get_project_root


def _agent_runs_root(company_key: str) -> Path:
    return Path(get_project_root()) / "data" / "ops_validation" / company_key / "runs"


def _legacy_pipeline_root(company_key: str) -> Path:
    return Path(get_project_root()) / "data" / "ops_validation" / company_key / "pipeline"


def _normalize_company_key(company_key: str) -> str:
    return company_key.strip().lower().replace("-", "_").replace(" ", "_")


def _resolve_company_key_for_agent(company_key: str) -> str:
    project_root = get_project_root()
    registered = resolve_company_reference(project_root, company_key)
    if registered is not None:
        return registered.company_key

    normalized = _normalize_company_key(company_key)
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
    supabase_runs = list_successful_runs_from_supabase(company_key, limit=20)
    if supabase_runs:
        return supabase_runs

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


__all__ = [
    "_agent_runs_root",
    "_legacy_pipeline_root",
    "_normalize_company_key",
    "_resolve_company_key_for_agent",
    "_build_legacy_run_entry",
    "_load_json_if_exists",
    "_scan_successful_runs",
]
