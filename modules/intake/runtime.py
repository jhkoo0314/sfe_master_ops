from __future__ import annotations

import os
from pathlib import Path

from .models import IntakeResult
from .staging import ensure_staged_source_copy, get_intake_staging_root


INTAKE_SOURCE_ROOT_ENV = "OPS_COMPANY_SOURCE_ROOT"


def get_intake_staged_source_root(project_root: str | Path, company_key: str) -> Path:
    return get_intake_staging_root(project_root, company_key)


def prepare_intake_staged_sources(
    *,
    project_root: str | Path,
    company_key: str,
    intake_result: IntakeResult,
) -> Path:
    staged_root = get_intake_staged_source_root(project_root, company_key)
    for package in intake_result.packages:
        staged_path = Path(package.staged_path)
        if staged_path.exists() and staged_root in staged_path.parents:
            continue
        copied_path = ensure_staged_source_copy(
            project_root=project_root,
            company_key=company_key,
            source_key=package.source_key,
            source_target_path=package.original_path,
            original_path=package.original_path,
        )
        if copied_path is not None:
            package.staged_path = str(copied_path)
    return staged_root


def activate_intake_source_root(staged_source_root: str | Path | None) -> None:
    if staged_source_root:
        os.environ[INTAKE_SOURCE_ROOT_ENV] = str(staged_source_root)


def clear_intake_source_root() -> None:
    os.environ.pop(INTAKE_SOURCE_ROOT_ENV, None)
