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
import polars as pl

from modules.crm.schemas import HospitalMaster
from adapters.crm.adapter_config import HospitalAdapterConfig
from common.exceptions import AdapterInputError, AdapterMappingError


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
            df = pl.read_excel(str(path))
        elif path.suffix.lower() == ".csv":
            df = pl.read_csv(str(path), encoding="utf-8-sig")
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
    df = pl.DataFrame(records)
    return _convert_dataframe_to_hospital_master(df, config)


def _convert_dataframe_to_hospital_master(
    df: pl.DataFrame,
    config: HospitalAdapterConfig,
) -> list[HospitalMaster]:
    """
    내부 공통 변환 로직.
    DataFrame + Config → list[HospitalMaster]
    """
    # 필수 컬럼 존재 확인
    required_cols = {
        "hospital_id": config.hospital_id_col,
        "hospital_name": config.hospital_name_col,
        "hospital_type": config.hospital_type_col,
        "region_key": config.region_key_col,
        "sub_region_key": config.sub_region_key_col,
    }
    missing = [
        f"{field}({col})" for field, col in required_cols.items()
        if col not in df.columns
    ]
    if missing:
        raise AdapterInputError(
            "필수 컬럼이 파일에 없습니다.",
            detail=f"누락 항목: {missing} | 파일 컬럼: {list(df.columns)}"
        )

    # 병원 종별 필터 적용
    if config.active_type_values:
        df = df.filter(
            pl.col(config.hospital_type_col).is_in(config.active_type_values)
        )

    # null 행 제거 (ID 없는 행)
    df = df.filter(
        pl.col(config.hospital_id_col).is_not_null() &
        pl.col(config.hospital_id_col).cast(pl.Utf8).str.len_chars().gt(0)
    )

    # HospitalMaster로 변환
    result: list[HospitalMaster] = []
    for row in df.iter_rows(named=True):
        try:
            hospital = HospitalMaster(
                hospital_id=str(row[config.hospital_id_col]).strip(),
                hospital_name=str(row[config.hospital_name_col]).strip(),
                hospital_type=str(row[config.hospital_type_col]).strip(),
                region_key=str(row[config.region_key_col]).strip(),
                sub_region_key=str(row[config.sub_region_key_col]).strip(),
                address=(
                    str(row[config.address_col]).strip()
                    if config.address_col and row.get(config.address_col)
                    else None
                ),
                phone=(
                    str(row[config.phone_col]).strip()
                    if config.phone_col and row.get(config.phone_col)
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
                f"HospitalMaster 변환 실패: {row.get(config.hospital_id_col)}",
                detail=str(e)
            )

    return result


def build_hospital_index(hospitals: list[HospitalMaster]) -> dict[str, HospitalMaster]:
    """
    hospital_id → HospitalMaster 인덱스를 생성합니다.
    다른 Adapter에서 빠른 병원 조회에 사용합니다.
    """
    return {h.hospital_id: h for h in hospitals}
