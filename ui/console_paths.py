from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from common.company_registry import (
    find_company_by_name,
    get_company_by_key,
    list_registered_companies,
)
from common.company_profile import get_company_ops_profile
from common.company_runtime import get_active_company_key as env_company_key, get_active_company_name as env_company_name


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_registered_company_from_state() -> tuple[str, str]:
    project_root = get_project_root()
    session_company_key = str(st.session_state.get("company_key", "")).strip()
    session_company_name = str(st.session_state.get("company_name", "")).strip()

    if session_company_key:
        registered = get_company_by_key(project_root, session_company_key)
        if registered is not None:
            return registered.company_key, registered.company_name

    if session_company_name:
        registered = find_company_by_name(project_root, session_company_name)
        if registered is not None:
            return registered.company_key, registered.company_name

    env_key = str(env_company_key("")).strip()
    if env_key:
        registered = get_company_by_key(project_root, env_key)
        if registered is not None:
            return registered.company_key, registered.company_name

    companies = list_registered_companies(project_root)
    if companies:
        first_company = companies[0]
        return first_company.company_key, first_company.company_name

    if env_key:
        return env_key, str(env_company_name(env_key)).strip()

    return "", ""


def get_active_company_key() -> str:
    company_key, company_name = _get_registered_company_from_state()
    if company_key:
        st.session_state.company_key = company_key
    if company_name:
        st.session_state.company_name = company_name
    return company_key


def get_active_company_name() -> str:
    company_key, company_name = _get_registered_company_from_state()
    if company_key:
        st.session_state.company_key = company_key
    if company_name:
        st.session_state.company_name = company_name
        return company_name
    return env_company_name(company_key)


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
