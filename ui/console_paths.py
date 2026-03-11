from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from common.company_profile import get_company_ops_profile
from common.company_runtime import get_active_company_key as env_company_key, get_active_company_name as env_company_name


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_active_company_key() -> str:
    return st.session_state.get("company_key", env_company_key())


def get_active_company_name() -> str:
    return st.session_state.get("company_name", env_company_name(get_active_company_key()))


def get_source_target_map() -> dict[str, tuple[str, str]]:
    root = Path(get_project_root())
    company_key = get_active_company_key()
    profile = get_company_ops_profile(company_key)
    return profile.resolved_source_targets(root, company_key)


def get_source_target_display_path(source_key: str) -> str:
    root = Path(get_project_root())
    company_key = get_active_company_key()
    profile = get_company_ops_profile(company_key)
    relative_path, _ = profile.source_targets[source_key]
    return str(Path("data") / "company_source" / company_key / Path(relative_path))
