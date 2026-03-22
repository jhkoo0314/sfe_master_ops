from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def get_onboarding_root(project_root: str | Path, company_key: str) -> Path:
    return Path(project_root) / "data" / "company_source" / company_key / "_onboarding"


def get_onboarding_registry_path(project_root: str | Path, company_key: str) -> Path:
    return get_onboarding_root(project_root, company_key) / "company_onboarding_registry.json"


def load_company_onboarding_registry(project_root: str | Path, company_key: str) -> dict[str, Any]:
    path = get_onboarding_registry_path(project_root, company_key)
    if not path.exists():
        return {
            "company_key": company_key,
            "source_mappings": {},
            "scenario_overrides": {},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_company_onboarding_registry(
    project_root: str | Path,
    company_key: str,
    payload: dict[str, Any],
) -> Path:
    path = get_onboarding_registry_path(project_root, company_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
