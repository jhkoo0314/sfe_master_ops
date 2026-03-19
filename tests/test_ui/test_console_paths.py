from pathlib import Path
import shutil
import sys
import uuid

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.company_registry import register_company
from ui import console_paths


def _make_sandbox(name: str) -> Path:
    sandbox = ROOT / "tests" / ".tmp_console_paths" / f"{name}_{uuid.uuid4().hex}"
    sandbox.mkdir(parents=True, exist_ok=True)
    return sandbox


def test_get_active_company_key_prefers_registered_session_key(monkeypatch):
    sandbox = _make_sandbox("session_key")
    try:
        monkeypatch.setattr(console_paths, "get_project_root", lambda: str(sandbox))
        st.session_state.clear()
        st.session_state.company_key = "daon_pharma"

        assert console_paths.get_active_company_key() == "daon_pharma"
        assert console_paths.get_active_company_name() == "다온파마"
    finally:
        st.session_state.clear()
        shutil.rmtree(sandbox, ignore_errors=True)


def test_get_active_company_key_resolves_registered_name_without_free_text_key(monkeypatch):
    sandbox = _make_sandbox("session_name")
    try:
        monkeypatch.setattr(console_paths, "get_project_root", lambda: str(sandbox))
        st.session_state.clear()
        st.session_state.company_name = "지원제약"
        register_company(sandbox, "지원제약", company_code_external="1234")

        assert console_paths.get_active_company_key().startswith("company_")
        assert console_paths.get_active_company_name() == "지원제약"
    finally:
        st.session_state.clear()
        shutil.rmtree(sandbox, ignore_errors=True)


def test_get_active_company_key_falls_back_to_first_registered_company(monkeypatch):
    sandbox = _make_sandbox("first_company")
    try:
        monkeypatch.setattr(console_paths, "get_project_root", lambda: str(sandbox))
        st.session_state.clear()

        assert console_paths.get_active_company_key() == "daon_pharma"
        assert console_paths.get_active_company_name() == "다온파마"
    finally:
        st.session_state.clear()
        shutil.rmtree(sandbox, ignore_errors=True)
