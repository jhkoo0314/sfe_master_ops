from __future__ import annotations

import os
from pathlib import Path


def get_active_company_key(default: str = "hangyeol_pharma") -> str:
    return os.environ.get("OPS_COMPANY_KEY", default).strip() or default


def get_active_company_name(default: str | None = None) -> str:
    name = os.environ.get("OPS_COMPANY_NAME", "").strip()
    if name:
        return name
    if default:
        return default
    return get_active_company_key()


def get_company_root(root: Path, bucket: str, company_key: str | None = None) -> Path:
    active_key = company_key or get_active_company_key()
    return root / "data" / bucket / active_key
