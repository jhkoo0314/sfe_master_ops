"""
Hospital Adapter - 공공/기준 병원 데이터 → HospitalMaster 변환

핵심 원칙:
  - 컬럼 매핑은 HospitalAdapterConfig로 외부에서 주입한다.
  - 이 Adapter는 어떤 병원 기준 파일이 와도 처리한다.
  - 출력(HospitalMaster)이 곧 계약(Contract)이며, 이 구조는 변하지 않는다.

지원 데이터소스 예시:
  - HIRA 요양기관 현황 (요양기관기호, 요양기관명 ...)
  - 내부 ERP 병원 마스터 (HOSP_CD, HOSP_NM ...)
  - 기타 어떤 형식이든 HospitalAdapterConfig를 채워서 전달

흐름:
  어떤 병원 파일 + HospitalAdapterConfig → HospitalMaster (공통 계약)
"""

from pathlib import Path
from typing import Any
try:
    import polars as pl
except ModuleNotFoundError:  # pragma: no cover - 환경 의존 fallback
    pl = None
import pandas as pd

from modules.crm.schemas import HospitalMaster
from adapters.crm.adapter_config import HospitalAdapterConfig
from common.exceptions import AdapterInputError, AdapterMappingError


def _normalize_column_name(name: str) -> str:
    return "".join(ch for ch in str(name).strip().lower() if ch.isalnum())


_HOSPITAL_COLUMN_ALIASES = {
    "hospital_id": ("hospital_id", "account_id", "거래처코드", "병원코드", "accountcode"),
    "hospital_name": ("hospital_name", "account_name", "거래처명", "병원명", "요양기관명"),
    "hospital_type": ("hospital_type", "account_type", "기관구분", "종별코드명", "병원종별"),
    "region_key": ("region_key", "광역시도", "시도", "시도명", "sido"),
    "sub_region_key": ("sub_region_key", "시군구", "시군구명", "sigungu"),
    "address": ("address", "주소", "주소원본"),
    "phone": ("phone", "전화번호", "tel"),
}


def _resolve_column_name(columns: list[str], preferred: str, aliases: tuple[str, ...]) -> str:
    normalized_map = {
        _normalize_column_name(column): str(column)
        for column in columns
    }
    for candidate in (preferred, *aliases):
        matched = normalized_map.get(_normalize_column_name(candidate))
        if matched:
            return matched
    return preferred


def load_hospital_master_from_file(
    file_path: str | Path,
    config: HospitalAdapterConfig,
) -> list[HospitalMaster]:
    """
    병원 기준 파일을 읽어 HospitalMaster 목록을 반환합니다.

    Args:
        file_path: 병원 기준 파일 경로 (Excel 또는 CSV)
        config: 이 파일의 컬럼 매핑 설정 (HospitalAdapterConfig)
                → config = HospitalAdapterConfig.hira_example()  # HIRA 기준
                → config = HospitalAdapterConfig(hospital_id_col="내컬럼명", ...)  # 직접 설정

    Returns:
        list[HospitalMaster]

    Raises:
        AdapterInputError: 파일 없음 또는 필수 컬럼 없음
        AdapterMappingError: 데이터 변환 실패
    """
    path = Path(file_path)
    if not path.exists():
        raise AdapterInputError(
            f"병원 기준 파일을 찾을 수 없습니다: {path}",
            detail="data/hospital_master/ 폴더에 파일을 넣어주세요."
        )

    # 파일 로드
    try:
        if path.suffix.lower() in (".xlsx", ".xls"):
            if pl is not None:
                df = pl.read_excel(str(path))
            else:
                df = pd.read_excel(str(path))
        elif path.suffix.lower() == ".csv":
            if pl is not None:
                df = pl.read_csv(str(path), encoding="utf-8-sig")
            else:
                df = pd.read_csv(str(path), encoding="utf-8-sig")
        else:
            raise AdapterInputError(f"지원하지 않는 파일 형식: {path.suffix}")
    except AdapterInputError:
        raise
    except Exception as e:
        raise AdapterInputError(f"파일 읽기 실패: {path}", detail=str(e))

    return _convert_dataframe_to_hospital_master(df, config)


def load_hospital_master_from_records(
    records: list[dict],
    config: HospitalAdapterConfig,
) -> list[HospitalMaster]:
    """
    딕셔너리 목록을 HospitalMaster 목록으로 변환합니다.
    fixture 데이터, API 응답, DB 쿼리 결과 등에 사용합니다.

    Args:
        records: 딕셔너리 목록
        config: 이 데이터의 키 매핑 설정

    Returns:
        list[HospitalMaster]
    """
    df = pl.DataFrame(records) if pl is not None else pd.DataFrame(records)
    return _convert_dataframe_to_hospital_master(df, config)


def _convert_dataframe_to_hospital_master(
    df: Any,
    config: HospitalAdapterConfig,
) -> list[HospitalMaster]:
    """
    내부 공통 변환 로직.
    DataFrame + Config → list[HospitalMaster]
    """
    # 필수 컬럼 존재 확인
    columns = list(df.columns)
    resolved_cols = {
        "hospital_id": _resolve_column_name(columns, config.hospital_id_col, _HOSPITAL_COLUMN_ALIASES["hospital_id"]),
        "hospital_name": _resolve_column_name(columns, config.hospital_name_col, _HOSPITAL_COLUMN_ALIASES["hospital_name"]),
        "hospital_type": _resolve_column_name(columns, config.hospital_type_col, _HOSPITAL_COLUMN_ALIASES["hospital_type"]),
        "region_key": _resolve_column_name(columns, config.region_key_col, _HOSPITAL_COLUMN_ALIASES["region_key"]),
        "sub_region_key": _resolve_column_name(columns, config.sub_region_key_col, _HOSPITAL_COLUMN_ALIASES["sub_region_key"]),
        "address": _resolve_column_name(columns, config.address_col, _HOSPITAL_COLUMN_ALIASES["address"]) if config.address_col else _resolve_column_name(columns, "", _HOSPITAL_COLUMN_ALIASES["address"]),
        "phone": _resolve_column_name(columns, config.phone_col, _HOSPITAL_COLUMN_ALIASES["phone"]) if config.phone_col else _resolve_column_name(columns, "", _HOSPITAL_COLUMN_ALIASES["phone"]),
    }
    required_cols = {
        "hospital_id": resolved_cols["hospital_id"],
        "hospital_name": resolved_cols["hospital_name"],
        "hospital_type": resolved_cols["hospital_type"],
        "region_key": resolved_cols["region_key"],
        "sub_region_key": resolved_cols["sub_region_key"],
    }
    missing = [f"{field}({col})" for field, col in required_cols.items() if col not in columns]
    if missing:
        raise AdapterInputError(
            "필수 컬럼이 파일에 없습니다.",
            detail=f"누락 항목: {missing} | 파일 컬럼: {columns}"
        )

    # 병원 종별 필터 적용
    if config.active_type_values:
        if pl is not None and isinstance(df, pl.DataFrame):
            df = df.filter(pl.col(resolved_cols["hospital_type"]).is_in(config.active_type_values))
        else:
            df = df[df[resolved_cols["hospital_type"]].isin(config.active_type_values)]

    # null 행 제거 (ID 없는 행)
    if pl is not None and isinstance(df, pl.DataFrame):
        df = df.filter(
            pl.col(resolved_cols["hospital_id"]).is_not_null() &
            pl.col(resolved_cols["hospital_id"]).cast(pl.Utf8).str.len_chars().gt(0)
        )
        rows = df.iter_rows(named=True)
    else:
        df = df[df[resolved_cols["hospital_id"]].notna()]
        df = df[df[resolved_cols["hospital_id"]].astype(str).str.len() > 0]
        rows = df.to_dict(orient="records")

    # HospitalMaster로 변환
    result: list[HospitalMaster] = []
    for row in rows:
        try:
            hospital = HospitalMaster(
                hospital_id=str(row[resolved_cols["hospital_id"]]).strip(),
                hospital_name=str(row[resolved_cols["hospital_name"]]).strip(),
                hospital_type=str(row[resolved_cols["hospital_type"]]).strip(),
                region_key=str(row[resolved_cols["region_key"]]).strip(),
                sub_region_key=str(row[resolved_cols["sub_region_key"]]).strip(),
                address=(
                    str(row[resolved_cols["address"]]).strip()
                    if resolved_cols["address"] in row and row.get(resolved_cols["address"])
                    else None
                ),
                phone=(
                    str(row[resolved_cols["phone"]]).strip()
                    if resolved_cols["phone"] in row and row.get(resolved_cols["phone"])
                    else None
                ),
                is_active=(
                    str(row.get(config.is_active_col, "Y")).strip().upper()
                    in ("Y", "TRUE", "1", "운영", "활성")
                    if config.is_active_col
                    else True
                ),
            )
            result.append(hospital)
        except Exception as e:
            raise AdapterMappingError(
                f"HospitalMaster 변환 실패: {row.get(resolved_cols['hospital_id'])}",
                detail=str(e)
            )

    return result


def build_hospital_index(hospitals: list[HospitalMaster]) -> dict[str, HospitalMaster]:
    """
    hospital_id → HospitalMaster 인덱스를 생성합니다.
    다른 Adapter에서 빠른 병원 조회에 사용합니다.
    """
    return {h.hospital_id: h for h in hospitals}
