from __future__ import annotations

import io
import os
from datetime import datetime

import pandas as pd
import streamlit as st

UPLOADED_DATA_KEYS = (
    "crm_activity",
    "crm_rep_master",
    "crm_account_assignment",
    "crm_rules",
    "sales",
    "target",
    "prescription",
)
MODULE_STATUS_KEYS = (
    "crm",
    "prescription",
    "sandbox",
    "territory",
    "radar",
    "builder",
)


def init_console_state() -> None:
    if "pipeline_result" not in st.session_state:
        st.session_state.pipeline_result = None
    if "uploaded_data" not in st.session_state:
        st.session_state.uploaded_data = {key: None for key in UPLOADED_DATA_KEYS}
    if "uploaded_tokens" not in st.session_state:
        st.session_state.uploaded_tokens = {key: None for key in UPLOADED_DATA_KEYS}
    if "run_log" not in st.session_state:
        st.session_state.run_log = []
    if "module_status" not in st.session_state:
        st.session_state.module_status = {key: "미실행" for key in MODULE_STATUS_KEYS}
    if "execution_mode" not in st.session_state:
        st.session_state.execution_mode = "crm_to_sandbox"
    if "company_key" not in st.session_state:
        st.session_state.company_key = ""
    if "company_name" not in st.session_state:
        st.session_state.company_name = ""


def add_log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.run_log.append(f"[{ts}] {msg}")


@st.cache_data(show_spinner=False)
def load_uploaded_dataframe(file_name: str, file_bytes: bytes) -> pd.DataFrame:
    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    return pd.read_excel(io.BytesIO(file_bytes))


def get_file_token(uploaded_file) -> str:
    file_size = getattr(uploaded_file, "size", None)
    if file_size is None:
        file_size = len(uploaded_file.getvalue())
    return f"{uploaded_file.name}:{file_size}"


def load_file_once(module_key: str, uploaded_file, label: str) -> dict:
    token = get_file_token(uploaded_file)
    existing = st.session_state.uploaded_data.get(module_key)
    if st.session_state.uploaded_tokens.get(module_key) == token and existing is not None:
        return existing

    file_bytes = uploaded_file.getvalue()
    df = load_uploaded_dataframe(uploaded_file.name, file_bytes)
    info = {
        "name": uploaded_file.name,
        "row_count": int(len(df)),
        "columns": list(df.columns),
        "preview": df.head(3).to_dict("records"),
        "file_bytes": file_bytes,
        "file_ext": os.path.splitext(uploaded_file.name)[1].lower(),
    }
    st.session_state.uploaded_data[module_key] = info
    st.session_state.uploaded_tokens[module_key] = token
    add_log(f"{label} 데이터 {len(df)}건 업로드")
    return info
