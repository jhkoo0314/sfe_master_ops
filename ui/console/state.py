from __future__ import annotations

import io
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from modules.intake import MONTHLY_FILE_NAMES

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
    if "saved_uploaded_data" not in st.session_state:
        st.session_state.saved_uploaded_data = {key: None for key in UPLOADED_DATA_KEYS}
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
    if "intake_result" not in st.session_state:
        st.session_state.intake_result = None
    if "intake_signature" not in st.session_state:
        st.session_state.intake_signature = ""


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


def save_uploaded_batch() -> dict:
    saved_count = 0
    saved_rows = 0
    saved_keys: list[str] = []

    for key in UPLOADED_DATA_KEYS:
        info = st.session_state.uploaded_data.get(key)
        if info is None:
            continue
        st.session_state.saved_uploaded_data[key] = dict(info)
        saved_count += 1
        saved_rows += int(info.get("row_count") or 0)
        saved_keys.append(key)

    st.session_state.intake_result = None
    st.session_state.intake_signature = ""
    st.session_state.pipeline_result = None

    if saved_keys:
        add_log(f"패키지 업로드 저장 {saved_count}건 반영 ({', '.join(saved_keys)})")

    return {
        "saved_count": saved_count,
        "rows": saved_rows,
        "keys": saved_keys,
    }


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


def _extract_month_from_series(series: pd.Series) -> str | None:
    parsed = pd.to_datetime(series, errors="coerce")
    parsed = parsed.dropna()
    if parsed.empty:
        return None
    months = sorted({value.strftime("%Y%m") for value in parsed})
    if len(months) == 1:
        return months[0]
    raise ValueError(f"날짜 컬럼에 여러 달이 섞여 있습니다: {', '.join(months)}")


def infer_month_token_from_dataframe(source_key: str, df: pd.DataFrame) -> str:
    candidate_columns_by_source = {
        "crm_activity": ["실행일", "활동일", "방문일", "일자", "date", "activity_date", "visit_date"],
        "sales": ["매출월", "매출일", "년월", "일자", "date", "sale_date", "sales_date", "yyyymm"],
        "target": ["목표월", "년월", "일자", "date", "target_month", "yyyymm"],
        "prescription": ["출고일", "처방월", "년월", "일자", "date", "ship_date", "prescription_date", "yyyymm"],
    }
    normalized_map = {str(column).strip().lower(): column for column in df.columns}
    candidates = candidate_columns_by_source.get(source_key, [])

    for candidate in candidates:
        matched_column = normalized_map.get(candidate.strip().lower())
        if matched_column is None:
            continue
        month_token = _extract_month_from_series(df[matched_column])
        if month_token:
            return month_token

    for column in df.columns:
        month_token = _extract_month_from_series(df[column])
        if month_token:
            return month_token

    raise ValueError("파일명과 데이터 내용에서 월 정보를 찾지 못했습니다.")


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
        df = load_uploaded_dataframe(uploaded_file.name, file_bytes)
        try:
            month_token = extract_month_token(uploaded_file.name)
        except ValueError:
            month_token = infer_month_token_from_dataframe(source_key, df)
        month_dir = root / month_token
        month_dir.mkdir(parents=True, exist_ok=True)
        target_path = month_dir / target_file_name

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
