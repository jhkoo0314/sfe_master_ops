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


def _load_run_artifacts(company_key: str, run_id: str, run_db_id: str = "") -> list[dict[str, Any]]:
    if run_db_id:
        rows = list_run_artifacts_from_supabase(run_db_id, limit=50)
        if rows:
            return rows

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
