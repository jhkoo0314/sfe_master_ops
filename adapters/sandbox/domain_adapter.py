"""
Sales & Target Adapter - 회사 매출/목표 데이터 → SandboxDomainRecord 변환

원칙:
  - SalesAdapterConfig / TargetAdapterConfig를 주입받아 동작
  - hospital_id가 없으면 hospital_name으로 HospitalMaster에서 역매핑 시도
  - 변환 실패 레코드는 failed 목록에 수집
"""

from datetime import datetime
from typing import Optional
from modules.sandbox.schemas import SalesDomainRecord, TargetDomainRecord
from adapters.sandbox.adapter_config import SalesAdapterConfig, TargetAdapterConfig


# ────────────────────────────────────────
# 내부 유틸
# ────────────────────────────────────────

def _to_metric_month(date_str: str, fmt: str) -> str:
    """날짜 문자열 → YYYYMM."""
    try:
        return datetime.strptime(str(date_str).strip(), fmt).strftime("%Y%m")
    except Exception:
        digits = "".join(ch for ch in str(date_str).strip() if ch.isdigit())
        return digits[:6]


def _normalize_metric_month(raw: object) -> str:
    """YYYY-MM / YYYYMM / Timestamp 등을 YYYYMM으로 표준화."""
    text = str(raw).strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 6:
        return digits[:6]
    return text[:6]


def _resolve_hospital_id(
    row: dict,
    hospital_id_col: Optional[str],
    hospital_name_col: Optional[str],
    name_to_id: Optional[dict[str, str]] = None,
) -> Optional[str]:
    """
    병원 ID 결정 로직.
    1. hospital_id_col 있으면 직접 사용
    2. hospital_name_col + name_to_id 역매핑
    3. 둘 다 실패 시 None
    """
    if hospital_id_col and hospital_id_col in row:
        val = str(row[hospital_id_col] or "").strip()
        if val:
            return val

    if hospital_name_col and hospital_name_col in row and name_to_id:
        name = str(row[hospital_name_col] or "").strip()
        return name_to_id.get(name)

    return None


# ────────────────────────────────────────
# 1. Sales Adapter
# ────────────────────────────────────────

def load_sales_from_records(
    records: list[dict],
    config: SalesAdapterConfig,
    source_label: str = "unknown",
    hospital_name_to_id: Optional[dict[str, str]] = None,
) -> tuple[list[SalesDomainRecord], list[dict]]:
    """
    딕셔너리 목록을 SalesDomainRecord 목록으로 변환.

    Args:
        records: 매출 원천 데이터 행 목록
        config: SalesAdapterConfig (컬럼 매핑)
        source_label: 어느 회사/파일 데이터인지 레이블
        hospital_name_to_id: 병원명 → hospital_id 역매핑 딕셔너리
                             (hospital_name_col 사용 시 필요)

    Returns:
        (성공 레코드 목록, 실패 행 목록)
    """
    success: list[SalesDomainRecord] = []
    failed: list[dict] = []

    for row in records:
        try:
            hospital_id = _resolve_hospital_id(
                row,
                config.hospital_id_col,
                config.hospital_name_col,
                hospital_name_to_id,
            )
            if not hospital_id:
                failed.append({**row, "_fail_reason": "hospital_id 결정 불가"})
                continue

            rep_id = str(row.get(config.rep_id_col, "") or "").strip()
            if not rep_id:
                failed.append({**row, "_fail_reason": "rep_id 없음"})
                continue

            # metric_month 결정
            if config.metric_month_col and config.metric_month_col in row:
                metric_month = _normalize_metric_month(row[config.metric_month_col])
            elif config.sales_date_col and config.sales_date_col in row:
                metric_month = _to_metric_month(
                    row[config.sales_date_col], config.date_format
                )
            else:
                failed.append({**row, "_fail_reason": "날짜/기간 컬럼 없음"})
                continue

            # 제품
            if config.product_id_col and config.product_id_col in row:
                product_id = str(row[config.product_id_col] or "").strip()
            elif config.product_name_col and config.product_name_col in row:
                product_id = str(row[config.product_name_col] or "").strip()
            else:
                product_id = "PROD_UNKNOWN"

            amount = float(row.get(config.amount_col, 0) or 0)
            quantity = float(row.get(config.quantity_col, 0) or 0) if config.quantity_col else None
            channel = str(row.get(config.channel_col, "") or "") if config.channel_col else None

            success.append(SalesDomainRecord(
                hospital_id=hospital_id,
                hospital_name=str(row.get(config.hospital_name_col, "") or "").strip() if config.hospital_name_col else None,
                rep_id=rep_id,
                rep_name=str(row.get(config.rep_name_col, "") or "").strip() if config.rep_name_col else None,
                branch_id=str(row.get(config.branch_id_col, "") or "").strip() if config.branch_id_col else None,
                branch_name=str(row.get(config.branch_name_col, "") or "").strip() if config.branch_name_col else None,
                metric_month=metric_month,
                product_id=product_id,
                product_name=str(row.get(config.product_name_col, "") or "").strip() if config.product_name_col else None,
                sales_amount=amount,
                sales_quantity=quantity,
                channel=channel or None,
                source_label=source_label,
            ))
        except Exception as e:
            failed.append({**row, "_fail_reason": str(e)})

    return success, failed


# ────────────────────────────────────────
# 2. Target Adapter
# ────────────────────────────────────────

def load_target_from_records(
    records: list[dict],
    config: TargetAdapterConfig,
    source_label: str = "unknown",
    hospital_name_to_id: Optional[dict[str, str]] = None,
) -> tuple[list[TargetDomainRecord], list[dict]]:
    """
    딕셔너리 목록을 TargetDomainRecord 목록으로 변환.

    Args:
        records: 목표 원천 데이터 행 목록
        config: TargetAdapterConfig (컬럼 매핑)
        source_label: 출처 레이블
        hospital_name_to_id: 병원명 역매핑 (선택)

    Returns:
        (성공 레코드 목록, 실패 행 목록)
    """
    success: list[TargetDomainRecord] = []
    failed: list[dict] = []

    for row in records:
        try:
            rep_id = str(row.get(config.rep_id_col, "") or "").strip()
            if not rep_id:
                failed.append({**row, "_fail_reason": "rep_id 없음"})
                continue

            # metric_month
            if config.metric_month_col and config.metric_month_col in row:
                metric_month = _normalize_metric_month(row[config.metric_month_col])
            elif config.target_date_col and config.target_date_col in row:
                metric_month = _to_metric_month(
                    row[config.target_date_col], config.date_format
                )
            else:
                failed.append({**row, "_fail_reason": "날짜/기간 컬럼 없음"})
                continue

            # 제품
            if config.product_id_col and config.product_id_col in row:
                product_id = str(row[config.product_id_col] or "").strip()
            elif config.product_name_col and config.product_name_col in row:
                product_id = str(row[config.product_name_col] or "").strip()
            else:
                product_id = "PROD_UNKNOWN"

            target_amount = float(row.get(config.target_amount_col, 0) or 0)

            # 병원 연결 (선택)
            hospital_id = _resolve_hospital_id(
                row,
                config.hospital_id_col,
                config.hospital_name_col,
                hospital_name_to_id,
            )

            success.append(TargetDomainRecord(
                rep_id=rep_id,
                rep_name=str(row.get(config.rep_name_col, "") or "").strip() if config.rep_name_col else None,
                branch_id=str(row.get(config.branch_id_col, "") or "").strip() if config.branch_id_col else None,
                branch_name=str(row.get(config.branch_name_col, "") or "").strip() if config.branch_name_col else None,
                metric_month=metric_month,
                product_id=product_id,
                product_name=str(row.get(config.product_name_col, "") or "").strip() if config.product_name_col else None,
                target_amount=target_amount,
                hospital_id=hospital_id,
                hospital_name=str(row.get(config.hospital_name_col, "") or "").strip() if config.hospital_name_col else None,
                source_label=source_label,
            ))
        except Exception as e:
            failed.append({**row, "_fail_reason": str(e)})

    return success, failed
