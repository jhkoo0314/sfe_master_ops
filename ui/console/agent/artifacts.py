from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from common.run_storage import list_run_artifacts_from_supabase
from ui.console.paths import get_project_root


def _legacy_pipeline_root(company_key: str) -> Path:
    return Path(get_project_root()) / "data" / "ops_validation" / company_key / "pipeline"


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _load_any_json_if_exists(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _agent_runs_root(company_key: str) -> Path:
    return Path(get_project_root()) / "data" / "ops_validation" / company_key / "runs"


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


def _build_artifacts_from_run_summary(run_summary: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for step in run_summary.get("steps", []):
        summary_path = str(step.get("summary_path") or "").strip()
        if not summary_path:
            continue
        artifacts.append(
            {
                "artifact_type": f"{step.get('module', 'module')}_validation_summary",
                "artifact_role": "validation_summary",
                "artifact_name": Path(summary_path).name,
                "artifact_class": "intermediate",
                "storage_path": summary_path,
                "mime_type": "application/json",
                "payload": {
                    "module": step.get("module"),
                    "reasoning_note": step.get("reasoning_note"),
                },
            }
        )

    builder_stage = (run_summary.get("summary_by_module") or {}).get("builder", {})
    if not builder_stage:
        for step in run_summary.get("steps", []):
            if str(step.get("module") or "") == "builder":
                builder_stage = step.get("summary") or {}
                break

    if isinstance(builder_stage, dict):
        for report_key, artifact_group in builder_stage.items():
            if not isinstance(artifact_group, dict):
                continue
            for file_role, file_path in artifact_group.items():
                if not isinstance(file_path, str) or not file_path.strip():
                    continue
                artifacts.append(
                    {
                        "artifact_type": {
                            "html": "report_html",
                            "input_standard": "report_input_standard",
                            "payload_standard": "report_payload_standard",
                            "result_asset": "report_result_asset",
                        }.get(file_role, f"report_{file_role}"),
                        "artifact_role": report_key,
                        "artifact_name": Path(file_path).name,
                        "artifact_class": "final" if file_role == "html" else "evidence",
                        "storage_path": file_path,
                        "mime_type": "text/html" if file_role == "html" else "application/json",
                        "payload": {"report_key": report_key, "file_role": file_role},
                    }
                )
    return artifacts


def _load_run_artifacts(company_key: str, run_id: str, run_db_id: str = "") -> list[dict[str, Any]]:
    if run_db_id:
        rows = list_run_artifacts_from_supabase(run_db_id, limit=50)
        if rows:
            return rows

    run_dir = _agent_runs_root(company_key) / run_id
    indexed_artifacts = _load_any_json_if_exists(run_dir / "artifacts.index.json")
    if isinstance(indexed_artifacts, list):
        return indexed_artifacts

    run_summary = _load_json_if_exists(run_dir / "pipeline_summary.json")
    if run_summary:
        artifacts = _build_artifacts_from_run_summary(run_summary)
        if artifacts:
            return artifacts

    history_summary = _load_run_summary_from_history(company_key, run_id)
    if history_summary:
        artifacts = _build_artifacts_from_run_summary(history_summary)
        if artifacts:
            return artifacts

    artifacts: list[dict[str, Any]] = []
    legacy_summary = _load_json_if_exists(_legacy_pipeline_root(company_key) / "pipeline_validation_summary.json")
    if not legacy_summary:
        return artifacts
    builder_stage = (legacy_summary.get("stages", {}) or {}).get("builder", {})
    if not isinstance(builder_stage, dict):
        return artifacts
    for report_key, artifact_group in builder_stage.items():
        if not isinstance(artifact_group, dict):
            continue
        for file_role, file_path in artifact_group.items():
            if not isinstance(file_path, str) or not file_path.strip():
                continue
            artifacts.append(
                {
                    "artifact_type": f"report_{file_role}",
                    "artifact_role": report_key,
                    "artifact_name": Path(file_path).name,
                    "artifact_class": "final" if file_role == "html" else "evidence",
                    "storage_path": file_path,
                    "mime_type": "text/html" if file_role == "html" else "application/json",
                    "payload": {"report_key": report_key, "file_role": file_role},
                }
            )
    return artifacts


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


__all__ = ["_load_run_artifacts", "_pick_evidence_items", "_pick_evidence_refs"]
