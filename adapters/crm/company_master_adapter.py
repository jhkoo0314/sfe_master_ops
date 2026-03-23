"""
Company Master Adapter - 회사 마스터 파일 → CompanyMasterStandard 변환

핵심 원칙:
  - 컬럼 매핑은 CompanyMasterAdapterConfig로 외부에서 주입한다.
  - 어떤 회사의 담당자-지점-병원 파일이 와도 처리한다.
  - hospital_id 연결: config.hospital_id_col 지정 시 직접 매핑,
    미지정 시 hospital_name으로 HospitalMaster 역매핑.
  - 출력(CompanyMasterStandard)이 계약(Contract)이며, 이 구조는 변하지 않는다.

흐름:
  어떤 회사 마스터 파일 + CompanyMasterAdapterConfig → CompanyMasterStandard (공통 계약)
"""

from pathlib import Path
from typing import Any
try:
    import polars as pl
except ModuleNotFoundError:  # pragma: no cover - 환경 의존 fallback
    pl = None
import pandas as pd

from modules.crm.schemas import HospitalMaster, CompanyMasterStandard
from adapters.crm.adapter_config import CompanyMasterAdapterConfig
from common.exceptions import AdapterInputError, AdapterMappingError


def _normalize_column_name(name: str) -> str:
    return "".join(ch for ch in str(name).strip().lower() if ch.isalnum())


_COMPANY_MASTER_COLUMN_ALIASES = {
    "rep_id": ("rep_id", "담당자id", "담당자코드", "영업사원코드", "사원번호"),
    "rep_name": ("rep_name", "담당자명", "영업사원명", "사원명"),
    "branch_id": ("branch_id", "본부코드", "지점코드", "team_code"),
    "branch_name": ("branch_name", "본부명", "지점명", "조직명", "team_name"),
    "hospital_name": ("hospital_name", "account_name", "거래처명", "병원명", "요양기관명"),
    "hospital_id": ("hospital_id", "account_id", "거래처코드", "병원코드"),
    "channel_type": ("channel_type", "기관구분", "채널구분", "account_type"),
    "is_primary": ("is_primary", "주담당여부", "대표담당여부"),
}


def _resolve_column_name(columns: list[str], preferred: str | None, aliases: tuple[str, ...]) -> str | None:
    if not preferred and not aliases:
        return preferred
    normalized_map = {
        _normalize_column_name(column): str(column)
        for column in columns
    }
    candidates = ((preferred,) if preferred else tuple()) + aliases
    for candidate in candidates:
        matched = normalized_map.get(_normalize_column_name(candidate))
        if matched:
            return matched
    return preferred


def load_company_master_from_file(
    file_path: str | Path,
    config: CompanyMasterAdapterConfig,
    hospital_index: dict[str, HospitalMaster],
) -> tuple[list[CompanyMasterStandard], list[dict]]:
    """
    회사 마스터 파일(Excel/CSV)을 읽어 CompanyMasterStandard 목록을 반환합니다.

    Args:
        file_path: 회사 마스터 파일 경로
        config: 이 파일의 컬럼 매핑 설정 (CompanyMasterAdapterConfig)
        hospital_index: {hospital_id: HospitalMaster} - hospital_adapter에서 생성

    Returns:
        (매핑 성공 목록, 매핑 실패 목록)
    """
    path = Path(file_path)
    if not path.exists():
        raise AdapterInputError(f"회사 마스터 파일을 찾을 수 없습니다: {path}")

    try:
        if path.suffix.lower() in (".xlsx", ".xls"):
            if pl is not None:
                df = pl.read_excel(str(path))
            else:
                df = pd.read_excel(str(path))
        else:
            if pl is not None:
                df = pl.read_csv(str(path), encoding="utf-8-sig")
            else:
                df = pd.read_csv(str(path), encoding="utf-8-sig")
    except Exception as e:
        raise AdapterInputError(f"파일 읽기 실패: {path}", detail=str(e))

    return _convert_dataframe_to_company_master(df, config, hospital_index)


def load_company_master_from_records(
    records: list[dict],
    config: CompanyMasterAdapterConfig,
    hospital_index: dict[str, HospitalMaster],
) -> tuple[list[CompanyMasterStandard], list[dict]]:
    """
    딕셔너리 목록을 CompanyMasterStandard 목록으로 변환합니다.
    fixture 데이터, API 응답, DB 쿼리 결과 등에 사용합니다.

    Args:
        records: 딕셔너리 목록
        config: 이 데이터의 키 매핑 설정
        hospital_index: {hospital_id: HospitalMaster}

    Returns:
        (매핑 성공 목록, 매핑 실패 목록)
    """
    df = pl.DataFrame(records) if pl is not None else pd.DataFrame(records)
    return _convert_dataframe_to_company_master(df, config, hospital_index)


def _convert_dataframe_to_company_master(
    df: Any,
    config: CompanyMasterAdapterConfig,
    hospital_index: dict[str, HospitalMaster],
) -> tuple[list[CompanyMasterStandard], list[dict]]:
    """내부 공통 변환 로직."""
    columns = list(df.columns)
    resolved_cols = {
        "rep_id": _resolve_column_name(columns, config.rep_id_col, _COMPANY_MASTER_COLUMN_ALIASES["rep_id"]),
        "rep_name": _resolve_column_name(columns, config.rep_name_col, _COMPANY_MASTER_COLUMN_ALIASES["rep_name"]),
        "branch_id": _resolve_column_name(columns, config.branch_id_col, _COMPANY_MASTER_COLUMN_ALIASES["branch_id"]),
        "branch_name": _resolve_column_name(columns, config.branch_name_col, _COMPANY_MASTER_COLUMN_ALIASES["branch_name"]),
        "hospital_name": _resolve_column_name(columns, config.hospital_name_col, _COMPANY_MASTER_COLUMN_ALIASES["hospital_name"]),
        "hospital_id": _resolve_column_name(columns, config.hospital_id_col, _COMPANY_MASTER_COLUMN_ALIASES["hospital_id"]),
        "channel_type": _resolve_column_name(columns, config.channel_type_col, _COMPANY_MASTER_COLUMN_ALIASES["channel_type"]),
        "is_primary": _resolve_column_name(columns, config.is_primary_col, _COMPANY_MASTER_COLUMN_ALIASES["is_primary"]),
    }

    # 필수 컬럼 확인
    required_cols = {
        "rep_id": resolved_cols["rep_id"],
        "rep_name": resolved_cols["rep_name"],
        "branch_id": resolved_cols["branch_id"],
        "branch_name": resolved_cols["branch_name"],
        "hospital_name": resolved_cols["hospital_name"],
    }
    missing = [f"{field}({col})" for field, col in required_cols.items() if col not in columns]
    if missing:
        raise AdapterInputError(
            "필수 컬럼이 파일에 없습니다.",
            detail=f"누락 항목: {missing} | 파일 컬럼: {columns}"
        )

    # 병원명 → hospital_id 역매핑 테이블 (config에 hospital_id_col 없는 경우 사용)
    name_to_id: dict[str, str] = {}
    if not config.hospital_id_col:
        for h in hospital_index.values():
            key = h.hospital_name.replace(" ", "").lower()
            name_to_id[key] = h.hospital_id

    result: list[CompanyMasterStandard] = []
    unmapped: list[dict] = []

    rows = df.iter_rows(named=True) if pl is not None and isinstance(df, pl.DataFrame) else df.to_dict(orient="records")
    for row in rows:
        rep_id = str(row.get(resolved_cols["rep_id"], "")).strip()
        raw_hospital_name = str(row.get(resolved_cols["hospital_name"], "")).strip()

        # hospital_id 결정: 직접 컬럼 우선, 없으면 이름으로 역매핑
        if resolved_cols["hospital_id"] and resolved_cols["hospital_id"] in df.columns:
            hospital_id = str(row.get(resolved_cols["hospital_id"], "")).strip()
            if hospital_id not in hospital_index:
                unmapped.append({
                    "rep_id": rep_id,
                    "hospital_name": raw_hospital_name,
                    "hospital_id_tried": hospital_id,
                    "reason": "hospital_index에 hospital_id 없음",
                })
                continue
        else:
            normalized = raw_hospital_name.replace(" ", "").lower()
            hospital_id = name_to_id.get(normalized)
            if not hospital_id:
                unmapped.append({
                    "rep_id": rep_id,
                    "hospital_name": raw_hospital_name,
                    "reason": "hospital_master에 해당 병원명 없음 (이름 역매핑 실패)",
                })
                continue

        # is_primary 파싱 (Y/N, True/False, 1/0 등 범용 처리)
        if resolved_cols["is_primary"] and resolved_cols["is_primary"] in df.columns:
            is_primary_raw = str(row.get(resolved_cols["is_primary"], "Y")).strip().upper()
            is_primary = is_primary_raw in ("TRUE", "Y", "1", "주담당", "주")
        else:
            is_primary = True  # 컬럼 없으면 전부 주담당으로 간주

        # channel_type 파싱
        if resolved_cols["channel_type"] and resolved_cols["channel_type"] in df.columns:
            channel_type = str(row.get(resolved_cols["channel_type"], "미분류")).strip()
        else:
            # 병원 종별로 채널 결정
            hospital = hospital_index.get(hospital_id)
            channel_type = hospital.hospital_type if hospital else "미분류"

        try:
            master = CompanyMasterStandard(
                rep_id=rep_id,
                rep_name=str(row.get(resolved_cols["rep_name"], "")).strip(),
                branch_id=str(row.get(resolved_cols["branch_id"], "")).strip(),
                branch_name=str(row.get(resolved_cols["branch_name"], "")).strip(),
                hospital_id=hospital_id,
                hospital_name=raw_hospital_name,
                channel_type=channel_type,
                is_primary=is_primary,
            )
            result.append(master)
        except Exception as e:
            raise AdapterMappingError(
                f"CompanyMasterStandard 변환 실패: rep_id={rep_id}",
                detail=str(e)
            )

    return result, unmapped


def validate_key_integrity(masters: list[CompanyMasterStandard]) -> dict:
    """
    rep_id ↔ branch_id ↔ hospital_id 정합성을 검증합니다.

    Returns:
        {
          "is_valid": bool,
          "rep_count": int,
          "branch_count": int,
          "hospital_count": int,
          "duplicate_rep_hospital_pairs": list,
        }
    """
    pair_counts: dict[tuple, int] = {}
    for m in masters:
        key = (m.rep_id, m.hospital_id)
        pair_counts[key] = pair_counts.get(key, 0) + 1

    duplicates = [
        {"rep_id": k[0], "hospital_id": k[1], "count": v}
        for k, v in pair_counts.items() if v > 1
    ]

    return {
        "is_valid": len(duplicates) == 0,
        "rep_count": len({m.rep_id for m in masters}),
        "branch_count": len({m.branch_id for m in masters}),
        "hospital_count": len({m.hospital_id for m in masters}),
        "duplicate_rep_hospital_pairs": duplicates,
    }
