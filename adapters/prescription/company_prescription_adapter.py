"""
Company Prescription Adapter - 회사 처방 파일 → CompanyPrescriptionStandard 변환

핵심 원칙:
  - 이 Adapter는 회사 데이터를 가정하지 않는다.
  - pharmacy_id, wholesaler_id, product_id는 id_rules의 범용 규칙으로 생성한다.
  - 어떤 회사의 도매출고/약국구입 파일이 와도 Config만 맞추면 처리된다.
  - 출력(CompanyPrescriptionStandard)이 계약이며 이 구조는 변하지 않는다.

흐름:
  [어떤 회사 파일] + CompanyPrescriptionAdapterConfig
  → CompanyPrescriptionStandard (공통 계약)
  → flow_builder가 도매→약국→병원 흐름으로 조립
"""

from datetime import date, datetime
from pathlib import Path
import polars as pl

from modules.prescription.schemas import CompanyPrescriptionStandard
from modules.prescription.id_rules import (
    generate_pharmacy_id,
    generate_wholesaler_id,
    generate_product_id,
)
from adapters.prescription.adapter_config import CompanyPrescriptionAdapterConfig
from common.exceptions import AdapterInputError, AdapterMappingError


def load_prescription_from_file(
    file_path: str | Path,
    config: CompanyPrescriptionAdapterConfig,
) -> tuple[list[CompanyPrescriptionStandard], list[dict]]:
    """
    처방/출고 파일(Excel/CSV)을 읽어 CompanyPrescriptionStandard 목록을 반환합니다.

    Args:
        file_path: 파일 경로
        config: 이 파일의 컬럼 매핑 설정

    Returns:
        (표준화 성공 목록, 변환 실패 목록)
    """
    path = Path(file_path)
    if not path.exists():
        raise AdapterInputError(f"처방 데이터 파일을 찾을 수 없습니다: {path}")

    try:
        if path.suffix.lower() in (".xlsx", ".xls"):
            df = pl.read_excel(str(path))
        else:
            df = pl.read_csv(str(path), encoding="utf-8-sig")
    except Exception as e:
        raise AdapterInputError(f"파일 읽기 실패: {path}", detail=str(e))

    return _convert_dataframe_to_standard(df, config)


def load_prescription_from_records(
    records: list[dict],
    config: CompanyPrescriptionAdapterConfig,
) -> tuple[list[CompanyPrescriptionStandard], list[dict]]:
    """
    딕셔너리 목록을 CompanyPrescriptionStandard로 변환합니다.
    fixture, API 응답, DB 쿼리 결과에 사용합니다.
    """
    if not records:
        return [], []

    # 날짜 등 직렬화 처리
    clean_records = []
    for r in records:
        row = {}
        for k, v in r.items():
            row[k] = str(v) if isinstance(v, (date, datetime)) else v
        clean_records.append(row)

    df = pl.DataFrame(clean_records)
    return _convert_dataframe_to_standard(df, config)


def _convert_dataframe_to_standard(
    df: pl.DataFrame,
    config: CompanyPrescriptionAdapterConfig,
) -> tuple[list[CompanyPrescriptionStandard], list[dict]]:
    """내부 공통 변환 로직."""
    # 필수 컬럼 확인
    required = {
        "wholesaler_name": config.wholesaler_name_col,
        "wholesaler_region": config.wholesaler_region_col,
        "pharmacy_name": config.pharmacy_name_col,
        "pharmacy_region": config.pharmacy_region_col,
        "pharmacy_sub_region": config.pharmacy_sub_region_col,
        "product_name": config.product_name_col,
        "quantity": config.quantity_col,
    }
    missing = [
        f"{field}({col})" for field, col in required.items()
        if col not in df.columns
    ]
    if missing:
        raise AdapterInputError(
            "필수 컬럼이 파일에 없습니다.",
            detail=f"누락: {missing} | 파일 컬럼: {list(df.columns)}"
        )

    result: list[CompanyPrescriptionStandard] = []
    failed: list[dict] = []
    row_index = 0

    for row in df.iter_rows(named=True):
        row_index += 1

        # 핵심 정보 추출
        wholesaler_name = str(row.get(config.wholesaler_name_col, "")).strip()
        wholesaler_region = str(row.get(config.wholesaler_region_col, "")).strip()
        pharmacy_name = str(row.get(config.pharmacy_name_col, "")).strip()
        pharmacy_region = str(row.get(config.pharmacy_region_col, "")).strip()
        pharmacy_sub_region = str(row.get(config.pharmacy_sub_region_col, "")).strip()
        product_name = str(row.get(config.product_name_col, "")).strip()

        # 필수값 누락 체크
        if not all([wholesaler_name, pharmacy_name, pharmacy_sub_region, product_name]):
            failed.append({
                "row_index": row_index,
                "reason": "필수 값 누락 (도매상명/약국명/시군구코드/제품명 중 하나 이상)",
            })
            continue

        # 범용 ID 생성 (id_rules 기반)
        postal_code = (
            str(row.get(config.pharmacy_postal_col, "")).strip()
            if config.pharmacy_postal_col and config.pharmacy_postal_col in df.columns
            else None
        )
        pharmacy_id = generate_pharmacy_id(pharmacy_name, pharmacy_sub_region, postal_code)
        wholesaler_id = generate_wholesaler_id(wholesaler_name, wholesaler_region)

        ingredient_code = (
            str(row.get(config.ingredient_code_col, "")).strip()
            if config.ingredient_code_col and config.ingredient_code_col in df.columns
            else None
        ) or None

        dosage_form = (
            str(row.get(config.dosage_form_col, "")).strip()
            if config.dosage_form_col and config.dosage_form_col in df.columns
            else None
        ) or None

        product_id = generate_product_id(product_name, ingredient_code, dosage_form)

        # 수량/금액
        try:
            quantity = float(row.get(config.quantity_col, 0) or 0)
        except (ValueError, TypeError):
            quantity = 0.0

        amount = None
        if config.amount_col and config.amount_col in df.columns:
            try:
                amount = float(row.get(config.amount_col, 0) or 0) or None
            except (ValueError, TypeError):
                amount = None

        # 거래 일자 / metric_month 처리
        if config.metric_month_col and config.metric_month_col in df.columns:
            metric_month_raw = str(row.get(config.metric_month_col, "")).strip()
            metric_month = metric_month_raw if metric_month_raw.isdigit() and len(metric_month_raw) == 6 else "000000"
            txn_date = _first_day_of_month(metric_month)
        elif config.transaction_date_col and config.transaction_date_col in df.columns:
            raw_date_str = str(row.get(config.transaction_date_col, "")).strip()
            try:
                txn_date = _parse_date_flexible(raw_date_str)
                metric_month = txn_date.strftime("%Y%m")
            except Exception:
                failed.append({
                    "row_index": row_index,
                    "reason": f"날짜 파싱 실패: '{raw_date_str}'"
                })
                continue
        else:
            # 날짜/월 컬럼 없는 경우
            failed.append({
                "row_index": row_index,
                "reason": "거래일자 또는 집계월 컬럼이 Config에 설정되지 않았습니다."
            })
            continue

        # 병원명 (있으면 직접 매핑에 활용 가능)
        hospital_id = None  # flow_builder에서 매핑

        unit = (
            str(row.get(config.unit_col, "")).strip()
            if config.unit_col and config.unit_col in df.columns
            else None
        ) or None

        try:
            std = CompanyPrescriptionStandard(
                record_type=config.record_type_value,
                wholesaler_id=wholesaler_id,
                wholesaler_name=wholesaler_name,
                pharmacy_id=pharmacy_id,
                pharmacy_name=pharmacy_name,
                pharmacy_region_key=pharmacy_region,
                pharmacy_sub_region_key=pharmacy_sub_region,
                pharmacy_postal_code=postal_code,
                product_id=product_id,
                product_name=product_name,
                ingredient_code=ingredient_code,
                quantity=quantity,
                amount=amount,
                unit=unit,
                transaction_date=txn_date,
                metric_month=metric_month,
                hospital_id=hospital_id,
                raw_row_index=row_index,
            )
            result.append(std)
        except Exception as e:
            raise AdapterMappingError(
                f"CompanyPrescriptionStandard 변환 실패: row={row_index}",
                detail=str(e)
            )

    return result, failed


def _parse_date_flexible(raw: str) -> date:
    """다양한 날짜 포맷 파싱."""
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            continue
    raise ValueError(f"날짜 파싱 실패: '{raw}'")


def _first_day_of_month(metric_month: str) -> date:
    """YYYYMM → 해당 월 1일."""
    y, m = int(metric_month[:4]), int(metric_month[4:6])
    return date(y, m, 1)
