from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from common.company_onboarding_registry import load_company_onboarding_registry
from modules.validation.workflow.execution_registry import get_mode_required_uploads
from .fixers import apply_basic_intake_fixes, apply_basic_intake_fixes_to_dataframe
from .models import (
    IntakeFinding,
    IntakeFix,
    IntakePeriodCoverage,
    IntakeRequest,
    IntakeResult,
    IntakeSourceInput,
    IntakeSuggestion,
    IntakeTimingAlert,
    OnboardingPackage,
)
from .rules import get_intake_rule
from .scenarios import resolve_intake_scenario
from .suggestions import (
    build_mapping_review_suggestion,
    build_missing_required_field_suggestion,
    build_optional_field_suggestion,
    build_optional_source_missing_suggestion,
    build_saved_mapping_fallback_suggestion,
    infer_best_candidate_column,
)
from .staging import (
    save_intake_result_snapshot,
    save_onboarding_package,
    stage_intake_dataframe,
    update_onboarding_registry_from_result,
)


_SOURCE_LABELS = {
    "crm_activity": "CRM 활동",
    "crm_rep_master": "담당자 / 조직 마스터",
    "crm_account_assignment": "거래처 담당 배정",
    "crm_rules": "CRM 규칙",
    "sales": "실적",
    "target": "목표",
    "prescription": "처방",
}

_ADAPTER_CANONICAL_COLUMN_MAP: dict[str, dict[str, str]] = {
    "crm_activity": {
        "병원명": "방문기관",
        "병원코드": "거래처코드",
        "활동내용": "활동메모",
        "담당자id": "영업사원코드",
        "담당자명": "영업사원명",
        "활동유형": "액션유형",
        "방문일": "실행일",
        "활동일": "실행일",
    },
    "crm_rep_master": {
        "병원코드": "거래처코드",
        "병원명": "거래처명",
        "담당자id": "영업사원코드",
        "담당자명": "영업사원명",
        "지점": "본부명",
        "branch_name": "본부명",
        "rep_name": "영업사원명",
    },
    "crm_account_assignment": {
        "병원코드": "account_id",
        "병원명": "account_name",
        "지점": "branch_name",
        "담당자명": "rep_name",
        "account_id": "거래처코드",
        "account_name": "거래처명",
        "담당자id": "영업사원코드",
        "rep_name": "영업사원명",
        "rep_id": "영업사원코드",
        "branch_name": "본부명",
        "branch_id": "본부코드",
        "기관구분": "account_type",
        "광역시도": "region_key",
        "시군구": "sub_region_key",
        "주소원본": "address",
    },
    "sales": {
        "병원코드": "거래처코드",
        "병원명": "거래처명",
        "매출월": "기준년월",
        "제품명": "브랜드명",
        "담당자id": "영업사원코드",
        "담당자명": "영업사원명",
        "rep_name": "영업사원명",
        "branch_name": "본부명",
        "account_id": "거래처코드",
        "account_name": "거래처명",
    },
    "target": {
        "병원코드": "거래처코드",
        "병원명": "거래처명",
        "목표월": "기준년월",
        "제품명": "브랜드명",
        "목표금액": "계획금액",
        "담당자id": "영업사원코드",
        "담당자명": "영업사원명",
        "rep_name": "영업사원명",
        "branch_name": "본부명",
        "account_id": "거래처코드",
        "account_name": "거래처명",
    },
    "prescription": {
        "출고일": "ship_date (출고일)",
        "약국명": "pharmacy_name (약국명)",
        "brand": "brand (브랜드)",
        "sku": "sku (SKU)",
        "출고수량": "qty (수량)",
        "공급가액": "amount_ship (출고금액)",
    },
}


def _normalize_column_name(name: str) -> str:
    return "".join(ch for ch in str(name).strip().lower() if ch.isalnum())


def _apply_adapter_canonical_columns(
    source_key: str,
    dataframe: pd.DataFrame | None,
) -> tuple[pd.DataFrame | None, list[IntakeFix]]:
    if dataframe is None:
        return None, []

    canonical_map = _ADAPTER_CANONICAL_COLUMN_MAP.get(source_key, {})
    if not canonical_map:
        return dataframe, []

    df = dataframe.copy()
    normalized_columns = {
        _normalize_column_name(column): str(column)
        for column in df.columns
    }
    copied_columns: list[str] = []
    for alias, canonical in canonical_map.items():
        matched_column = normalized_columns.get(_normalize_column_name(alias))
        if matched_column is None or matched_column == canonical or canonical in df.columns:
            continue
        df[canonical] = df[matched_column]
        copied_columns.append(canonical)

    if not copied_columns:
        return df, []

    fixes = [
        IntakeFix(
            source_key=source_key,
            fix_type="canonicalize_adapter_columns",
            message="파이프라인 실행용 컬럼을 원본 옆에 자동 추가했습니다.",
            affected_count=len(copied_columns),
        )
    ]
    return df, fixes


def _has_all_columns(dataframe: pd.DataFrame | None, required_columns: tuple[str, ...]) -> bool:
    if dataframe is None:
        return False
    columns = {str(column) for column in dataframe.columns}
    return all(column in columns for column in required_columns)


def _build_execution_ready_crm_rep_master(
    source_frames: dict[str, pd.DataFrame | None],
) -> tuple[pd.DataFrame | None, list[IntakeFix]]:
    current_df = source_frames.get("crm_rep_master")
    assignment_df = source_frames.get("crm_account_assignment")
    required_columns = ("영업사원코드", "영업사원명", "본부코드", "본부명", "거래처명")

    if _has_all_columns(current_df, required_columns):
        return current_df, []
    if assignment_df is None:
        return current_df, []

    execution_df = assignment_df.copy()
    derived_columns = {
        "영업사원코드": ("영업사원코드", "rep_id"),
        "영업사원명": ("영업사원명", "rep_name"),
        "본부코드": ("본부코드", "branch_id"),
        "본부명": ("본부명", "branch_name"),
        "거래처코드": ("거래처코드", "account_id"),
        "거래처명": ("거래처명", "account_name"),
    }
    for target_column, candidates in derived_columns.items():
        if target_column in execution_df.columns:
            continue
        for candidate in candidates:
            if candidate in execution_df.columns:
                execution_df[target_column] = execution_df[candidate]
                break

    if not _has_all_columns(execution_df, required_columns):
        return current_df, []

    fixes = [
        IntakeFix(
            source_key="crm_rep_master",
            fix_type="hydrate_company_assignment_from_account_mapping",
            message="담당자/조직 마스터만으로는 배정표가 부족해 거래처 담당 배정 파일을 실행용 CRM 마스터로 함께 사용했습니다.",
            affected_count=int(len(execution_df)),
        )
    ]

    if current_df is None or current_df.empty:
        return execution_df, fixes

    if "영업사원코드" not in current_df.columns:
        return execution_df, fixes

    enrichment_columns = [
        column
        for column in current_df.columns
        if column not in execution_df.columns and column != "영업사원코드"
    ]
    if not enrichment_columns:
        return execution_df, fixes

    rep_master_unique = current_df[["영업사원코드", *enrichment_columns]].drop_duplicates(subset=["영업사원코드"])
    execution_df = execution_df.merge(rep_master_unique, how="left", on="영업사원코드")
    return execution_df, fixes


def _first_existing_column(dataframe: pd.DataFrame | None, *candidates: str) -> str | None:
    if dataframe is None:
        return None
    for candidate in candidates:
        if candidate in dataframe.columns:
            return candidate
    return None


def _infer_account_type_from_name(account_name: str) -> str:
    normalized = str(account_name).strip().lower()
    if "상급종합" in normalized:
        return "상급종합"
    if "종합병원" in normalized:
        return "종합병원"
    if "병원" in normalized:
        return "병원"
    if "clinic" in normalized:
        return "의원"
    return "의원"


def _build_execution_ready_crm_account_assignment(
    source_frames: dict[str, pd.DataFrame | None],
) -> tuple[pd.DataFrame | None, list[IntakeFix]]:
    current_df = source_frames.get("crm_account_assignment")
    crm_df = source_frames.get("crm_activity")
    rep_df = source_frames.get("crm_rep_master")
    required_columns = ("account_id", "account_name", "account_type", "region_key", "sub_region_key")

    if _has_all_columns(current_df, required_columns):
        return current_df, []

    if crm_df is None or crm_df.empty:
        return current_df, []

    rep_id_col = _first_existing_column(crm_df, "영업사원코드", "rep_id", "담당자id")
    account_name_col = _first_existing_column(crm_df, "방문기관", "병원명", "hospital_name", "account_name", "거래처명")
    if rep_id_col is None or account_name_col is None:
        return current_df, []

    working = crm_df.copy()
    working["rep_id"] = working[rep_id_col].astype(str).str.strip()
    working["account_name"] = working[account_name_col].astype(str).str.strip()
    working = working[(working["rep_id"] != "") & (working["account_name"] != "")]
    if working.empty:
        return current_df, []

    region_source = _first_existing_column(working, "region_key", "광역시도", "시도", "시도명")
    sub_region_source = _first_existing_column(working, "sub_region_key", "시군구", "시군구명")
    account_type_source = _first_existing_column(working, "account_type", "기관구분", "channel_type")
    address_source = _first_existing_column(working, "address", "주소원본", "주소")
    latitude_source = _first_existing_column(working, "latitude", "기관위도")
    longitude_source = _first_existing_column(working, "longitude", "기관경도")

    normalized_name = (
        working["account_name"]
        .astype(str)
        .str.replace(r"\s+", "", regex=True)
        .str.lower()
    )
    account_codes = {
        name: f"DERIVED_ACC_{index:04d}"
        for index, name in enumerate(sorted(normalized_name.unique()), start=1)
    }
    working["_normalized_account_name"] = normalized_name
    working["account_id"] = working["_normalized_account_name"].map(account_codes)
    working["region_key"] = (
        working[region_source].astype(str).str.strip()
        if region_source
        else "UNKNOWN_REGION"
    )
    working["sub_region_key"] = (
        working[sub_region_source].astype(str).str.strip()
        if sub_region_source
        else "UNKNOWN_SUB_REGION"
    )
    if account_type_source:
        working["account_type"] = working[account_type_source].astype(str).str.strip()
        empty_account_type = working["account_type"].eq("") | working["account_type"].isna()
        if empty_account_type.any():
            working.loc[empty_account_type, "account_type"] = working.loc[empty_account_type, "account_name"].map(_infer_account_type_from_name)
    else:
        working["account_type"] = working["account_name"].map(_infer_account_type_from_name)
    if address_source:
        working["address"] = working[address_source].astype(str).str.strip()

    keep_columns = ["account_id", "account_name", "account_type", "region_key", "sub_region_key", "rep_id"]
    if "address" in working.columns:
        keep_columns.append("address")
    if latitude_source:
        working["latitude"] = working[latitude_source]
        keep_columns.append("latitude")
    if longitude_source:
        working["longitude"] = working[longitude_source]
        keep_columns.append("longitude")

    execution_df = working[keep_columns].drop_duplicates(subset=["account_id", "rep_id"]).copy()

    if current_df is not None and not current_df.empty:
        alias_pairs = {
            "rep_name": ("rep_name", "영업사원명", "담당자명"),
            "branch_id": ("branch_id", "본부코드"),
            "branch_name": ("branch_name", "본부명", "지점"),
        }
        for target_column, candidates in alias_pairs.items():
            source_col = _first_existing_column(current_df, *candidates)
            if source_col and target_column not in current_df.columns:
                current_df = current_df.copy()
                current_df[target_column] = current_df[source_col]

    rep_enrichment = rep_df if rep_df is not None and not rep_df.empty else current_df
    if rep_enrichment is not None and not rep_enrichment.empty:
        rep_lookup = rep_enrichment.copy()
        rep_id_source = _first_existing_column(rep_lookup, "영업사원코드", "rep_id", "담당자id")
        if rep_id_source:
            rep_lookup["rep_id"] = rep_lookup[rep_id_source].astype(str).str.strip()
            enrichment_columns: list[str] = []
            for target_column, candidates in {
                "rep_name": ("영업사원명", "rep_name", "담당자명"),
                "branch_id": ("본부코드", "branch_id"),
                "branch_name": ("본부명", "branch_name", "지점"),
            }.items():
                source_col = _first_existing_column(rep_lookup, *candidates)
                if source_col:
                    rep_lookup[target_column] = rep_lookup[source_col].astype(str).str.strip()
                    enrichment_columns.append(target_column)
            if enrichment_columns:
                rep_lookup = rep_lookup[["rep_id", *enrichment_columns]].drop_duplicates(subset=["rep_id"])
                execution_df = execution_df.merge(rep_lookup, how="left", on="rep_id")

    fixes = [
        IntakeFix(
            source_key="crm_account_assignment",
            fix_type="derive_account_assignment_from_crm_activity",
            message="거래처 담당 배정 파일이 부족해 CRM 활동 원본에서 실행용 거래처/병원 배정표를 자동 생성했습니다.",
            affected_count=int(len(execution_df)),
        )
    ]

    if not _has_all_columns(execution_df, required_columns):
        return current_df, []

    return execution_df, fixes


def _adapter_ready_check(source_key: str, dataframe: pd.DataFrame | None) -> tuple[bool, list[str]]:
    required_by_source = {
        "crm_account_assignment": ("account_id", "account_name", "account_type", "region_key", "sub_region_key"),
        "crm_rep_master": ("영업사원코드", "영업사원명", "본부코드", "본부명", "거래처명"),
        "crm_activity": ("영업사원코드", "실행일", "액션유형"),
        "sales": ("거래처코드", "거래처명", "기준년월"),
        "target": ("기준년월",),
        "prescription": ("ship_date (출고일)", "pharmacy_name (약국명)", "qty (수량)"),
    }
    required_columns = required_by_source.get(source_key)
    if not required_columns:
        return True, []
    if dataframe is None or dataframe.empty:
        return False, ["실행용 데이터가 비어 있습니다."]

    columns = {str(column) for column in dataframe.columns}

    missing = [column for column in required_columns if column not in columns]
    if source_key == "crm_activity":
        has_hospital_link = ("방문기관" in columns) or ("거래처코드" in columns)
        if not has_hospital_link:
            missing.append("방문기관|거래처코드")
    if missing:
        return False, missing
    return True, []


def _format_month_token(month_token: str) -> str:
    if len(month_token) == 6 and month_token.isdigit():
        return f"{month_token[:4]}-{month_token[4:6]}"
    return month_token


def _month_to_index(month_token: str) -> int:
    return int(month_token[:4]) * 12 + int(month_token[4:6])


def _month_gap(from_month: str, to_month: str) -> int:
    return abs(_month_to_index(from_month) - _month_to_index(to_month))


def _read_source_frame(path: str | Path) -> pd.DataFrame | None:
    source_path = Path(path)
    if not source_path.exists():
        return None
    stat = source_path.stat()
    dataframe = _read_source_frame_cached(str(source_path), stat.st_mtime_ns, stat.st_size)
    if dataframe is None:
        return None
    return dataframe.copy()


@lru_cache(maxsize=32)
def _read_source_frame_cached(path_str: str, mtime_ns: int, file_size: int) -> pd.DataFrame | None:
    source_path = Path(path_str)
    suffix = source_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(source_path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(source_path)
    return None


def _normalize_month_value(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)) or pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    compact = re.sub(r"[^0-9]", "", text)
    if len(compact) >= 6:
        year = compact[:4]
        month = compact[4:6]
        if year.isdigit() and month.isdigit() and 1 <= int(month) <= 12:
            return f"{year}{month}"

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return f"{parsed.year:04d}{parsed.month:02d}"


def _resolve_period_column(
    source_key: str,
    columns: list[str],
    resolved_mapping: dict[str, str],
) -> str | None:
    preferred_fields = {
        "crm_activity": ("activity_date",),
        "sales": ("period",),
        "target": ("period",),
        "prescription": ("ship_date",),
    }.get(source_key, ())
    for field_name in preferred_fields:
        column_name = resolved_mapping.get(field_name)
        if column_name in columns:
            return column_name

    lowered_columns = {str(column).lower(): column for column in columns}
    for token in ("yyyymm", "metric_month", "month", "date", "월", "출고일", "활동일", "방문일"):
        for lowered, original in lowered_columns.items():
            if token in lowered:
                return original
    return None


def _build_period_coverage(
    *,
    source_key: str,
    columns: list[str],
    dataframe: pd.DataFrame | None,
    resolved_mapping: dict[str, str],
) -> IntakePeriodCoverage | None:
    if dataframe is None or dataframe.empty or not columns:
        return None

    period_column = _resolve_period_column(source_key, columns, resolved_mapping)
    if period_column is None or period_column not in dataframe.columns:
        return None

    normalized_months = [
        month_token
        for month_token in dataframe[period_column].map(_normalize_month_value).tolist()
        if month_token is not None
    ]
    distinct_months = sorted(set(normalized_months))
    if not distinct_months:
        return None

    return IntakePeriodCoverage(
        source_key=source_key,
        period_column=str(period_column),
        start_month=distinct_months[0],
        end_month=distinct_months[-1],
        month_count=len(distinct_months),
        distinct_months=distinct_months,
    )


def _build_timing_summary(
    *,
    scenario: Any,
    coverages: dict[str, IntakePeriodCoverage],
) -> tuple[list[IntakeTimingAlert], list[str], str | None, str | None, int | None, str | None, str | None]:
    analysis_source_keys = [source_key for source_key in scenario.analysis_source_keys if source_key in coverages]
    if not analysis_source_keys:
        analysis_source_keys = list(coverages.keys())
    if not analysis_source_keys:
        return [], [], None, None, None, None, None

    common_months: set[str] | None = None
    for source_key in analysis_source_keys:
        source_months = set(coverages[source_key].distinct_months)
        common_months = source_months if common_months is None else common_months & source_months

    sorted_common_months = sorted(common_months or [])
    analysis_start = sorted_common_months[0] if sorted_common_months else None
    analysis_end = sorted_common_months[-1] if sorted_common_months else None
    analysis_month_count = len(sorted_common_months) if sorted_common_months else None

    timing_alerts: list[IntakeTimingAlert] = []
    if analysis_end is not None:
        for source_key, coverage in coverages.items():
            if coverage.end_month == analysis_end:
                continue
            source_label = _SOURCE_LABELS.get(source_key, source_key)
            month_gap = _month_gap(coverage.end_month, analysis_end)
            if _month_to_index(coverage.end_month) > _month_to_index(analysis_end):
                timing_alerts.append(
                    IntakeTimingAlert(
                        level="warn",
                        source_key=source_key,
                        message=(
                            f"{source_label} 데이터는 공통 분석 기준 종료월 {_format_month_token(analysis_end)}보다 "
                            f"{month_gap}개월 앞서 있습니다."
                        ),
                        direction="ahead",
                        month_gap=month_gap,
                        reference_end_month=analysis_end,
                    )
                )
            else:
                timing_alerts.append(
                    IntakeTimingAlert(
                        level="warn",
                        source_key=source_key,
                        message=(
                            f"{source_label} 데이터는 공통 분석 기준 종료월 {_format_month_token(analysis_end)}보다 "
                            f"{month_gap}개월 이전 데이터까지만 있습니다."
                        ),
                        direction="behind",
                        month_gap=month_gap,
                        reference_end_month=analysis_end,
                    )
                )

    if analysis_month_count and analysis_start and analysis_end and timing_alerts:
        analysis_summary_message = (
            f"일부 입력 데이터의 기간이 서로 다르지만, 공통 분석 구간 "
            f"{_format_month_token(analysis_start)} ~ {_format_month_token(analysis_end)} 기준 "
            f"{analysis_month_count}개월 검증은 진행 가능합니다."
        )
        proceed_confirmation_message = (
            f"일부 입력 데이터의 기간이 서로 다릅니다. 그래도 공통 분석 구간 "
            f"{_format_month_token(analysis_start)} ~ {_format_month_token(analysis_end)} 기준 "
            f"{analysis_month_count}개월 검증을 계속 진행할까요?"
        )
    elif analysis_month_count and analysis_start and analysis_end:
        analysis_summary_message = (
            f"현재 공통 분석 구간은 {_format_month_token(analysis_start)} ~ "
            f"{_format_month_token(analysis_end)} 총 {analysis_month_count}개월입니다."
        )
        proceed_confirmation_message = None
    elif timing_alerts:
        analysis_summary_message = "입력 데이터의 기간 차이는 감지됐지만, 공통 분석 구간을 자동으로 확정하지 못했습니다."
        proceed_confirmation_message = "입력 데이터 기간 차이를 먼저 확인한 뒤 계속 진행할지 결정해야 합니다."
    else:
        analysis_summary_message = None
        proceed_confirmation_message = None

    return (
        timing_alerts,
        analysis_source_keys,
        analysis_start,
        analysis_end,
        analysis_month_count,
        analysis_summary_message,
        proceed_confirmation_message,
    )


def _resolve_mapping(columns: list[str], source_key: str) -> tuple[dict[str, str], list[str], list[str]]:
    rule = get_intake_rule(source_key)
    if rule is None:
        return {}, [], []

    normalized_columns = {
        _normalize_column_name(column): column
        for column in columns
    }
    resolved_mapping: dict[str, str] = {}
    missing_required: list[str] = []
    missing_review: list[str] = []

    for semantic_field, aliases in rule.field_aliases.items():
        matched_column = None
        for alias in aliases:
            matched_column = normalized_columns.get(_normalize_column_name(alias))
            if matched_column:
                break
        if matched_column is None:
            matched_column = infer_best_candidate_column(
                columns,
                aliases,
                semantic_field=semantic_field,
            )
        if matched_column:
            resolved_mapping[semantic_field] = matched_column
        elif semantic_field in rule.required_fields:
            missing_required.append(semantic_field)
        elif semantic_field in rule.review_fields:
            missing_review.append(semantic_field)

    return resolved_mapping, missing_required, missing_review


def _build_source_input_from_dataframe(
    *,
    source_key: str,
    target_path: str,
    dataframe: pd.DataFrame,
    fixes: list[IntakeFix],
    is_required: bool,
    upload_present: bool,
) -> IntakeSourceInput:
    preview_rows = dataframe.head(3).where(pd.notna(dataframe), None).to_dict("records")
    target = Path(target_path)
    return IntakeSourceInput(
        source_key=source_key,
        original_path=str(target_path),
        target_path=str(target_path),
        file_name=target.name,
        file_ext=target.suffix.lower(),
        row_count=int(len(dataframe)),
        columns=[str(column) for column in dataframe.columns],
        preview_rows=preview_rows,
        fixes=fixes,
        is_required=is_required,
        upload_present=upload_present,
    )


class CommonIntakeEngine:
    """
    Common intake entry point for Sales Data OS.

    Phase 1 only fixes the input/output contract.
    Detailed scenario, mapping, rule, auto-fix, and staging logic will be
    added in later phases without changing this public interface.
    """

    def inspect(self, request: IntakeRequest) -> IntakeResult:
        registry = load_company_onboarding_registry(request.project_root, request.company_key)
        scenario = resolve_intake_scenario(
            execution_mode=request.execution_mode,
            source_keys=[source.source_key for source in request.sources],
        )
        active_source_keys = set(scenario.source_keys)
        packages: list[OnboardingPackage] = []
        findings: list[IntakeFinding] = []
        fixes: list[IntakeFix] = []
        suggestions: list[IntakeSuggestion] = []

        for source in request.sources:
            package_findings: list[IntakeFinding] = []
            package_fixes: list[IntakeFix] = list(source.fixes)
            package_suggestions: list[IntakeSuggestion] = []
            status = "ready_with_fixes" if package_fixes else "ready"
            resolved_mapping: dict[str, str] = {}
            source_rule = get_intake_rule(source.source_key)
            stored_mapping = (
                registry.get("source_mappings", {}).get(source.source_key, {})
                if isinstance(registry.get("source_mappings"), dict)
                else {}
            )

            if source.source_key not in active_source_keys and not source.is_required:
                package = OnboardingPackage(
                    company_key=request.company_key,
                    source_key=source.source_key,
                    original_path=source.original_path,
                    staged_path=source.target_path,
                    status=status,
                    scenario_key=scenario.key,
                    scenario_label=scenario.label,
                    findings=package_findings,
                    fixes=package_fixes,
                    suggestions=package_suggestions,
                    resolved_mapping=resolved_mapping,
                    ready_for_adapter=True,
                )
                fixes.extend(package_fixes)
                packages.append(package)
                continue

            if not source.upload_present and not Path(source.original_path).exists():
                if source.is_required:
                    status = "blocked"
                    package_findings.append(
                        IntakeFinding(
                            level="error",
                            source_key=source.source_key,
                            issue_code="missing_source",
                            message="업로드된 파일이 없고 기존 source 경로에도 파일이 없습니다.",
                        )
                    )
                else:
                    package_suggestions.append(build_optional_source_missing_suggestion(source.source_key))
            elif source.columns:
                inferred_mapping, missing_required, missing_review = _resolve_mapping(source.columns, source.source_key)
                resolved_mapping.update(
                    {
                        semantic_field: actual_column
                        for semantic_field, actual_column in stored_mapping.items()
                        if actual_column in source.columns
                    }
                )
                for semantic_field, actual_column in inferred_mapping.items():
                    resolved_mapping.setdefault(semantic_field, actual_column)

                for semantic_field in missing_required:
                    if semantic_field in resolved_mapping:
                        continue
                    candidate_columns: list[str] = []
                    if source_rule is not None:
                        suggestion = build_missing_required_field_suggestion(
                            source_key=source.source_key,
                            semantic_field=semantic_field,
                            columns=source.columns,
                            rule=source_rule,
                        )
                        candidate_columns = suggestion.candidate_columns
                        package_suggestions.append(suggestion)
                    if candidate_columns:
                        package_findings.append(
                            IntakeFinding(
                                level="warn",
                                source_key=source.source_key,
                                issue_code="candidate_review_recommended",
                                message=f"필수 의미 컬럼 `{semantic_field}` 는 후보가 있어 우선 진행 가능하지만, 분석 해석 전에 한 번 확인하는 것이 안전합니다.",
                                column_name=semantic_field,
                            )
                        )
                    else:
                        status = "needs_review"
                        package_findings.append(
                            IntakeFinding(
                                level="warn",
                                source_key=source.source_key,
                                issue_code="missing_required_semantic_field",
                                message=f"필수 의미 컬럼 `{semantic_field}` 를 아직 확정하지 못했습니다.",
                                column_name=semantic_field,
                            )
                        )
                for semantic_field in missing_review:
                    if semantic_field in resolved_mapping:
                        continue
                    if source_rule is not None:
                        package_suggestions.append(
                            build_optional_field_suggestion(
                                source_key=source.source_key,
                                semantic_field=semantic_field,
                                columns=source.columns,
                                rule=source_rule,
                            )
                        )
                if source_rule is not None and not resolved_mapping and source.columns:
                    package_suggestions.append(
                        build_mapping_review_suggestion(
                            source_key=source.source_key,
                            columns=source.columns,
                            rule=source_rule,
                        )
                    )
            elif source_rule is not None:
                package_suggestions.append(build_saved_mapping_fallback_suggestion(source.source_key))

            blocking_suggestion_types = {"mapping_review_required"}
            if status in ("ready", "ready_with_fixes") and any(
                suggestion.suggestion_type in blocking_suggestion_types
                for suggestion in package_suggestions
            ):
                status = "needs_review"

            package = OnboardingPackage(
                company_key=request.company_key,
                source_key=source.source_key,
                original_path=source.original_path,
                staged_path=source.target_path,
                status=status,
                scenario_key=scenario.key,
                scenario_label=scenario.label,
                findings=package_findings,
                fixes=package_fixes,
                suggestions=package_suggestions,
                resolved_mapping=resolved_mapping,
                ready_for_adapter=(status not in ("blocked", "needs_review")),
            )
            findings.extend(package_findings)
            fixes.extend(package_fixes)
            suggestions.extend(package_suggestions)
            packages.append(package)

        if any(pkg.status == "blocked" for pkg in packages):
            result_status = "blocked"
        elif any(pkg.status == "needs_review" for pkg in packages):
            result_status = "needs_review"
        elif any(pkg.status == "ready_with_fixes" for pkg in packages):
            result_status = "ready_with_fixes"
        else:
            result_status = "ready"
        return IntakeResult(
            company_key=request.company_key,
            company_name=request.company_name,
            status=result_status,
            scenario_key=scenario.key,
            scenario_label=scenario.label,
            findings=findings,
            fixes=fixes,
            suggestions=suggestions,
            packages=packages,
        )


def build_intake_result(
    *,
    project_root: str | Path,
    company_key: str,
    company_name: str,
    source_targets: Mapping[str, tuple[str, str]],
    uploaded: Mapping[str, dict[str, object] | None] | None = None,
    execution_mode: str | None = None,
    cache_signature: str | None = None,
) -> IntakeResult:
    sources: list[IntakeSourceInput] = []
    source_frames: dict[str, Any] = {}
    required_source_keys = set(get_mode_required_uploads(execution_mode)) if execution_mode else set()
    for source_key, (target_path, _target_format) in source_targets.items():
        info = (uploaded or {}).get(source_key)
        if info is not None:
            fixer_result = apply_basic_intake_fixes(source_key, info)
            canonical_df, canonical_fixes = _apply_adapter_canonical_columns(source_key, fixer_result.dataframe)
            source_frames[source_key] = canonical_df
            sources.append(
                _build_source_input_from_dataframe(
                    source_key=source_key,
                    target_path=str(target_path),
                    dataframe=canonical_df if canonical_df is not None else pd.DataFrame(),
                    fixes=[*fixer_result.fixes, *canonical_fixes],
                    is_required=(source_key in required_source_keys),
                    upload_present=True,
                )
            )
            continue

        existing_frame = _read_source_frame(target_path)
        if existing_frame is not None:
            fixer_result = apply_basic_intake_fixes_to_dataframe(source_key, existing_frame)
            canonical_df, canonical_fixes = _apply_adapter_canonical_columns(source_key, fixer_result.dataframe)
            source_frames[source_key] = canonical_df
            sources.append(
                _build_source_input_from_dataframe(
                    source_key=source_key,
                    target_path=str(target_path),
                    dataframe=canonical_df if canonical_df is not None else pd.DataFrame(),
                    fixes=[*fixer_result.fixes, *canonical_fixes],
                    is_required=(source_key in required_source_keys),
                    upload_present=False,
                )
            )
            continue

        target = Path(target_path)
        sources.append(
            IntakeSourceInput(
                source_key=source_key,
                original_path=str(target_path),
                target_path=str(target_path),
                file_name=target.name,
                file_ext=target.suffix.lower(),
                row_count=None,
                columns=[],
                preview_rows=[],
                fixes=[],
                is_required=(source_key in required_source_keys),
                upload_present=False,
            )
        )

    request = IntakeRequest(
        project_root=str(project_root),
        company_key=company_key,
        company_name=company_name,
        execution_mode=execution_mode,
        sources=sources,
    )
    result = CommonIntakeEngine().inspect(request)
    result.cache_signature = cache_signature
    scenario = resolve_intake_scenario(
        execution_mode=execution_mode,
        source_keys=[package.source_key for package in result.packages],
    )

    coverages: dict[str, IntakePeriodCoverage] = {}
    crm_account_assignment_df, crm_account_assignment_fixes = _build_execution_ready_crm_account_assignment(source_frames)
    if crm_account_assignment_df is not None:
        source_frames["crm_account_assignment"] = crm_account_assignment_df

    crm_rep_master_df, crm_rep_master_fixes = _build_execution_ready_crm_rep_master(source_frames)
    if crm_rep_master_df is not None:
        source_frames["crm_rep_master"] = crm_rep_master_df

    for package in result.packages:
        if package.source_key == "crm_account_assignment" and crm_account_assignment_fixes:
            package.fixes.extend(crm_account_assignment_fixes)
            result.fixes.extend(crm_account_assignment_fixes)
        if package.source_key == "crm_rep_master" and crm_rep_master_fixes:
            package.fixes.extend(crm_rep_master_fixes)
            result.fixes.extend(crm_rep_master_fixes)

        dataframe = source_frames.get(package.source_key)
        adapter_ready, missing_execution_columns = _adapter_ready_check(package.source_key, dataframe)
        if not adapter_ready:
            package.ready_for_adapter = False
            package.status = "needs_review"
            package.findings.append(
                IntakeFinding(
                    level="warn",
                    source_key=package.source_key,
                    issue_code="adapter_execution_columns_incomplete",
                    message=(
                        "인테이크 기본 검사는 통과했지만, 실행용 staging에서 아답터 필수 컬럼이 아직 부족합니다. "
                        f"부족 항목: {missing_execution_columns}"
                    ),
                )
            )
            result.findings.append(package.findings[-1])
        elif package.status == "ready":
            package.status = "ready_with_fixes" if package.fixes else "ready"
            package.ready_for_adapter = True

        period_coverage = _build_period_coverage(
            source_key=package.source_key,
            columns=next((source.columns for source in sources if source.source_key == package.source_key), []),
            dataframe=dataframe,
            resolved_mapping=package.resolved_mapping,
        )
        package.period_coverage = period_coverage
        if period_coverage is not None:
            coverages[package.source_key] = period_coverage

        if dataframe is not None:
            staged_path = stage_intake_dataframe(
                project_root=project_root,
                company_key=company_key,
                source_key=package.source_key,
                source_target_path=package.original_path,
                dataframe=dataframe,
            )
            package.staged_path = str(staged_path)
        save_onboarding_package(project_root, company_key, package.to_dict())

    if any(pkg.status == "blocked" for pkg in result.packages):
        result.status = "blocked"
    elif any(pkg.status == "needs_review" for pkg in result.packages):
        result.status = "needs_review"
    elif any(pkg.status == "ready_with_fixes" for pkg in result.packages):
        result.status = "ready_with_fixes"
    else:
        result.status = "ready"

    (
        result.timing_alerts,
        result.analysis_basis_sources,
        result.analysis_start_month,
        result.analysis_end_month,
        result.analysis_month_count,
        result.analysis_summary_message,
        result.proceed_confirmation_message,
    ) = _build_timing_summary(
        scenario=scenario,
        coverages=coverages,
    )
    result.period_coverages = list(coverages.values())

    save_intake_result_snapshot(project_root, result)
    update_onboarding_registry_from_result(project_root, result)
    return result
