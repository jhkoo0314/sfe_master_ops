from __future__ import annotations

from typing import Mapping


SANDBOX_KPI_ENGINE_VERSION = "sandbox_kpi_engine_v1"
OFFICIAL_SANDBOX_KPI6_KEYS = (
    "monthly_sales",
    "monthly_target",
    "monthly_attainment_rate",
    "quarterly_sales",
    "quarterly_target",
    "annual_attainment_rate",
)


def compute_sandbox_rep_kpis(
    month_stats: Mapping[str, Mapping[str, float]],
) -> dict[str, float]:
    """
    Sandbox 담당자 단위 공식 KPI 계산.
    주의: CRM KPI는 입력값 평균만 사용하며 Sandbox에서 재산식하지 않는다.
    """
    hir = _avg_from_month_stats(month_stats, "hir")
    rtr = _avg_from_month_stats(month_stats, "rtr")
    bcr = _avg_from_month_stats(month_stats, "bcr")
    phr = _avg_from_month_stats(month_stats, "phr")
    pi = _avg_from_month_stats(month_stats, "pi")
    fgr = _avg_from_month_stats(month_stats, "fgr")

    return {
        "hir": hir,
        "rtr": rtr,
        "bcr": bcr,
        "phr": phr,
        "pi": pi,
        "fgr": fgr,
        "metric_version": SANDBOX_KPI_ENGINE_VERSION,
    }


def compute_sandbox_official_kpi_6(
    sales_by_month: Mapping[str, float],
    target_by_month: Mapping[str, float],
) -> dict[str, float | str]:
    """
    Sandbox 전사 공식 6대지표 계산.
    공식 지표는 리포트 상단 KPI 기준으로 사용한다.
    """
    months = sorted({str(k) for k in sales_by_month.keys()} | {str(k) for k in target_by_month.keys()})
    if not months:
        return {
            "monthly_sales": 0.0,
            "monthly_target": 0.0,
            "monthly_attainment_rate": 0.0,
            "quarterly_sales": 0.0,
            "quarterly_target": 0.0,
            "annual_attainment_rate": 0.0,
            "reference_month": "",
            "reference_quarter": "",
            "reference_year": "",
            "metric_version": SANDBOX_KPI_ENGINE_VERSION,
        }

    reference_month = months[-1]
    year = reference_month[:4]
    month_num = int(reference_month[4:6])
    quarter = ((month_num - 1) // 3) + 1
    quarter_months = [m for m in months if m.startswith(year) and (((int(m[4:6]) - 1) // 3) + 1) == quarter]
    year_months = [m for m in months if m.startswith(year)]

    monthly_sales = float(sales_by_month.get(reference_month, 0.0) or 0.0)
    monthly_target = float(target_by_month.get(reference_month, 0.0) or 0.0)
    monthly_attainment = _rate(monthly_sales, monthly_target)

    quarterly_sales = sum(float(sales_by_month.get(m, 0.0) or 0.0) for m in quarter_months)
    quarterly_target = sum(float(target_by_month.get(m, 0.0) or 0.0) for m in quarter_months)

    annual_sales = sum(float(sales_by_month.get(m, 0.0) or 0.0) for m in year_months)
    annual_target = sum(float(target_by_month.get(m, 0.0) or 0.0) for m in year_months)
    annual_attainment = _rate(annual_sales, annual_target)

    return {
        "monthly_sales": round(monthly_sales, 0),
        "monthly_target": round(monthly_target, 0),
        "monthly_attainment_rate": round(monthly_attainment, 1),
        "quarterly_sales": round(quarterly_sales, 0),
        "quarterly_target": round(quarterly_target, 0),
        "annual_attainment_rate": round(annual_attainment, 1),
        "reference_month": reference_month,
        "reference_quarter": f"{year}-Q{quarter}",
        "reference_year": year,
        "metric_version": SANDBOX_KPI_ENGINE_VERSION,
    }


def validate_official_kpi_6_payload(payload: Mapping[str, float | str]) -> dict[str, float | str]:
    """
    공식 KPI 6대지표 계약 검증.
    서비스 계층은 이 검증을 통과한 값만 공식 KPI로 저장해야 한다.
    """
    missing = [key for key in OFFICIAL_SANDBOX_KPI6_KEYS if key not in payload]
    if missing:
        raise ValueError(f"official_kpi_6 missing keys: {missing}")
    if payload.get("metric_version") != SANDBOX_KPI_ENGINE_VERSION:
        raise ValueError(
            f"official_kpi_6 metric_version mismatch: {payload.get('metric_version')} != {SANDBOX_KPI_ENGINE_VERSION}"
        )
    return dict(payload)


def _avg_from_month_stats(
    month_stats: Mapping[str, Mapping[str, float]],
    metric_name: str,
) -> float:
    sum_key = f"{metric_name}_sum"
    count_key = f"{metric_name}_count"
    total_sum = sum(float((row or {}).get(sum_key, 0.0) or 0.0) for row in month_stats.values())
    total_count = sum(float((row or {}).get(count_key, 0.0) or 0.0) for row in month_stats.values())
    if total_count <= 0:
        return 0.0
    return round(total_sum / total_count, 1)


def _rate(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return (numerator / denominator) * 100.0
