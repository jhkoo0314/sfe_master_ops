from __future__ import annotations

import io
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from ops_core.workflow.monthly_source_merge import MONTHLY_FILE_NAMES

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
    if "selected_run_id" not in st.session_state:
        st.session_state.selected_run_id = ""
    if "selected_run_db_id" not in st.session_state:
        st.session_state.selected_run_db_id = ""
    if "selected_mode" not in st.session_state:
        st.session_state.selected_mode = ""
    if "report_context_full" not in st.session_state:
        st.session_state.report_context_full = None
    if "report_context_prompt" not in st.session_state:
        st.session_state.report_context_prompt = None
    if "agent_history" not in st.session_state:
        st.session_state.agent_history = []
    if "current_answer_scope" not in st.session_state:
        st.session_state.current_answer_scope = "final_report_only"
    if "monthly_upload_summary" not in st.session_state:
        st.session_state.monthly_upload_summary = None


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


def extract_month_token(file_name: str) -> str:
    name = str(file_name)
    patterns = [
        r"(20\d{2})[-_]?([01]\d)",
        r"(20\d{2})\.([01]\d)",
    ]
    for pattern in patterns:
        match = re.search(pattern, name)
        if not match:
            continue
        year, month = match.group(1), match.group(2)
        if 1 <= int(month) <= 12:
            return f"{year}{month}"
    raise ValueError(f"파일명에서 월을 찾지 못했습니다: {file_name}")


def save_monthly_upload_batch(source_key: str, uploaded_files, monthly_root: str | Path) -> dict:
    if not uploaded_files:
        return {"saved_count": 0, "months": [], "rows": 0}

    target_file_name = MONTHLY_FILE_NAMES[source_key]
    root = Path(monthly_root)
    root.mkdir(parents=True, exist_ok=True)

    saved_months: list[str] = []
    total_rows = 0
    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.getvalue()
        month_token = extract_month_token(uploaded_file.name)
        month_dir = root / month_token
        month_dir.mkdir(parents=True, exist_ok=True)
        target_path = month_dir / target_file_name

        df = load_uploaded_dataframe(uploaded_file.name, file_bytes)
        total_rows += int(len(df))
        if target_path.suffix.lower() == ".csv":
            if str(uploaded_file.name).lower().endswith(".csv"):
                target_path.write_bytes(file_bytes)
            else:
                df.to_csv(target_path, index=False, encoding="utf-8-sig")
        else:
            df.to_excel(target_path, index=False)
        saved_months.append(month_token)

    unique_months = sorted(set(saved_months))
    add_log(f"{source_key} 월별 파일 {len(uploaded_files)}건 저장 ({', '.join(unique_months)})")
    return {
        "saved_count": len(uploaded_files),
        "months": unique_months,
        "rows": total_rows,
    }
