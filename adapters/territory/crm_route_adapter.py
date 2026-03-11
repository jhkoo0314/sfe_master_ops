from __future__ import annotations

from pathlib import Path

import pandas as pd

from adapters.territory.adapter_config import TerritoryActivityAdapterConfig
from common.exceptions import AdapterInputError, AdapterMappingError
from modules.territory.schemas import TerritoryActivityStandard


def load_territory_activity_from_file(
    crm_standard_path: str | Path,
    account_master_path: str | Path,
    config: TerritoryActivityAdapterConfig,
) -> tuple[list[TerritoryActivityStandard], list[dict]]:
    crm_path = Path(crm_standard_path)
    account_path = Path(account_master_path)
    if not crm_path.exists():
        raise AdapterInputError(f"Territory용 CRM 표준 파일을 찾을 수 없습니다: {crm_path}")
    if not account_path.exists():
        raise AdapterInputError(f"Territory용 거래처 마스터 파일을 찾을 수 없습니다: {account_path}")

    try:
        crm_df = pd.read_excel(crm_path)
        account_df = pd.read_excel(account_path)
    except Exception as exc:
        raise AdapterInputError("Territory 어댑터 입력 파일을 읽지 못했습니다.", detail=str(exc))

    return load_territory_activity_from_frames(crm_df, account_df, config)


def load_territory_activity_from_frames(
    crm_df: pd.DataFrame,
    account_df: pd.DataFrame,
    config: TerritoryActivityAdapterConfig,
) -> tuple[list[TerritoryActivityStandard], list[dict]]:
    crm_required = ["hospital_id", "rep_id", "activity_date", "metric_month"]
    crm_missing = [col for col in crm_required if col not in crm_df.columns]
    if crm_missing:
        raise AdapterInputError(
            "CRM 표준 파일에 Territory 필수 컬럼이 없습니다.",
            detail=f"누락 컬럼: {crm_missing}",
        )

    account_required = [
        config.hospital_id_col,
        config.hospital_name_col,
        config.rep_id_col,
        config.rep_name_col,
        config.latitude_col,
        config.longitude_col,
    ]
    account_missing = [col for col in account_required if col not in account_df.columns]
    if account_missing:
        raise AdapterInputError(
            "거래처 마스터 파일에 Territory 필수 컬럼이 없습니다.",
            detail=f"누락 컬럼: {account_missing}",
        )

    account_rows = account_df.copy()
    account_rows[config.hospital_id_col] = account_rows[config.hospital_id_col].astype(str).str.strip()
    account_rows[config.rep_id_col] = account_rows[config.rep_id_col].astype(str).str.strip()
    account_rows[config.latitude_col] = pd.to_numeric(account_rows[config.latitude_col], errors="coerce")
    account_rows[config.longitude_col] = pd.to_numeric(account_rows[config.longitude_col], errors="coerce")

    account_index_by_pair: dict[tuple[str, str], dict] = {}
    account_index_by_hospital: dict[str, dict] = {}
    for row in account_rows.to_dict(orient="records"):
        hospital_id = str(row.get(config.hospital_id_col, "")).strip()
        rep_id = str(row.get(config.rep_id_col, "")).strip()
        if not hospital_id:
            continue
        account_index_by_hospital[hospital_id] = row
        if rep_id:
            account_index_by_pair[(hospital_id, rep_id)] = row

    crm_rows = crm_df.copy()
    crm_rows["hospital_id"] = crm_rows["hospital_id"].astype(str).str.strip()
    crm_rows["rep_id"] = crm_rows["rep_id"].astype(str).str.strip()
    crm_rows["activity_date"] = pd.to_datetime(crm_rows["activity_date"], errors="coerce")
    if "visit_count" in crm_rows.columns:
        crm_rows["visit_count"] = pd.to_numeric(crm_rows["visit_count"], errors="coerce").fillna(1)
    else:
        crm_rows["visit_count"] = 1
    if "raw_row_index" in crm_rows.columns:
        crm_rows["raw_row_index"] = pd.to_numeric(crm_rows["raw_row_index"], errors="coerce")
    else:
        crm_rows["raw_row_index"] = range(1, len(crm_rows) + 1)

    result: list[TerritoryActivityStandard] = []
    unmapped: list[dict] = []

    for row_index, row in enumerate(crm_rows.to_dict(orient="records"), start=1):
        hospital_id = str(row.get("hospital_id", "")).strip()
        rep_id = str(row.get("rep_id", "")).strip()
        activity_date = row.get("activity_date")
        if not hospital_id or not rep_id or pd.isna(activity_date):
            unmapped.append(
                {
                    "row_index": row_index,
                    "hospital_id": hospital_id,
                    "rep_id": rep_id,
                    "reason": "hospital_id / rep_id / activity_date 중 하나가 비어 있습니다.",
                }
            )
            continue

        account_row = account_index_by_pair.get((hospital_id, rep_id)) or account_index_by_hospital.get(hospital_id)
        if account_row is None:
            unmapped.append(
                {
                    "row_index": row_index,
                    "hospital_id": hospital_id,
                    "rep_id": rep_id,
                    "reason": "거래처 마스터에서 hospital_id 매핑을 찾지 못했습니다.",
                }
            )
            continue

        latitude = account_row.get(config.latitude_col)
        longitude = account_row.get(config.longitude_col)
        if pd.isna(latitude) or pd.isna(longitude):
            unmapped.append(
                {
                    "row_index": row_index,
                    "hospital_id": hospital_id,
                    "rep_id": rep_id,
                    "reason": "거래처 마스터에 위도/경도가 없습니다.",
                }
            )
            continue

        metric_month = str(row.get("metric_month") or "").strip()
        month_key = _normalize_month(metric_month, activity_date)
        date_key = activity_date.strftime("%Y-%m-%d")

        try:
            result.append(
                TerritoryActivityStandard(
                    hospital_id=hospital_id,
                    hospital_name=str(account_row.get(config.hospital_name_col, "") or hospital_id).strip(),
                    rep_id=rep_id,
                    rep_name=str(row.get("rep_name") or account_row.get(config.rep_name_col) or rep_id).strip(),
                    branch_id=str(row.get("branch_id") or account_row.get(config.branch_id_col or "") or "").strip(),
                    branch_name=str(row.get("branch_name") or account_row.get(config.branch_name_col or "") or "").strip(),
                    activity_date=activity_date.date(),
                    month_key=month_key,
                    date_key=date_key,
                    latitude=float(latitude),
                    longitude=float(longitude),
                    region_key=str(account_row.get(config.region_key_col or "", "") or "").strip(),
                    sub_region_key=str(account_row.get(config.sub_region_key_col or "", "") or "").strip() or None,
                    activity_type=str(row.get("activity_type") or "방문").strip(),
                    visit_count=max(int(row.get("visit_count") or 1), 1),
                    route_order=int(row.get("raw_row_index") or row_index),
                )
            )
        except Exception as exc:
            raise AdapterMappingError(
                f"TerritoryActivityStandard 변환 실패: row={row_index}",
                detail=str(exc),
            )

    return result, unmapped


def _normalize_month(metric_month: str, activity_date: pd.Timestamp) -> str:
    raw = metric_month.replace("-", "").strip()
    if len(raw) == 6 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}"
    return activity_date.strftime("%Y-%m")
