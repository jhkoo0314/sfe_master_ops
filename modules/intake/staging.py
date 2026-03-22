from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from common.company_onboarding_registry import (
    load_company_onboarding_registry,
    save_company_onboarding_registry,
)
from .models import IntakeResult


def get_intake_staging_root(project_root: str | Path, company_key: str) -> Path:
    return Path(project_root) / "data" / "company_source" / company_key / "_intake_staging"


def get_intake_source_staging_dir(project_root: str | Path, company_key: str, source_key: str) -> Path:
    return get_intake_staging_root(project_root, company_key) / source_key


def _resolve_staged_target_path(
    project_root: str | Path,
    company_key: str,
    source_target_path: str,
) -> Path:
    source_root = Path(project_root) / "data" / "company_source" / company_key
    target_path = Path(source_target_path)
    try:
        relative_path = target_path.relative_to(source_root)
    except ValueError:
        relative_path = Path(target_path.name)
    return get_intake_staging_root(project_root, company_key) / relative_path


def _write_dataframe(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".csv":
        df.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        df.to_excel(path, index=False)


def stage_intake_dataframe(
    *,
    project_root: str | Path,
    company_key: str,
    source_key: str,
    source_target_path: str,
    dataframe: pd.DataFrame,
) -> Path:
    staged_path = _resolve_staged_target_path(project_root, company_key, source_target_path)
    _write_dataframe(staged_path, dataframe)
    return staged_path


def ensure_staged_source_copy(
    *,
    project_root: str | Path,
    company_key: str,
    source_key: str,
    source_target_path: str,
    original_path: str,
) -> Path | None:
    original = Path(original_path)
    if not original.exists():
        return None
    staged_path = _resolve_staged_target_path(project_root, company_key, source_target_path)
    staged_path.parent.mkdir(parents=True, exist_ok=True)
    if not staged_path.exists():
        shutil.copy2(original, staged_path)
    return staged_path


def save_onboarding_package(project_root: str | Path, company_key: str, package_payload: dict[str, Any]) -> Path:
    onboarding_root = Path(project_root) / "data" / "company_source" / company_key / "_onboarding"
    onboarding_root.mkdir(parents=True, exist_ok=True)
    package_path = onboarding_root / f"{package_payload['source_key']}_onboarding_package.json"
    package_path.write_text(
        json.dumps(package_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return package_path


def save_intake_result_snapshot(project_root: str | Path, result: IntakeResult) -> tuple[Path, Path]:
    onboarding_root = Path(project_root) / "data" / "company_source" / result.company_key / "_onboarding"
    onboarding_root.mkdir(parents=True, exist_ok=True)
    latest_path = onboarding_root / "intake_result.latest.json"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_path = onboarding_root / f"intake_result_{timestamp}.json"
    payload = result.to_dict()
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    latest_path.write_text(serialized, encoding="utf-8")
    history_path.write_text(serialized, encoding="utf-8")
    return latest_path, history_path


def update_onboarding_registry_from_result(project_root: str | Path, result: IntakeResult) -> Path:
    payload = load_company_onboarding_registry(project_root, result.company_key)
    source_mappings = payload.setdefault("source_mappings", {})
    payload["company_key"] = result.company_key
    payload["last_scenario_key"] = result.scenario_key
    for package in result.packages:
        if package.resolved_mapping:
            source_mappings[package.source_key] = package.resolved_mapping
    return save_company_onboarding_registry(project_root, result.company_key, payload)
