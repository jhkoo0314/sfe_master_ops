from __future__ import annotations

from typing import Mapping, Sequence


SANDBOX_KPI_ENGINE_VERSION = "sandbox_kpi_engine_v1"
OFFICIAL_SANDBOX_KPI6_KEYS = (
    "monthly_sales",
    "monthly_target",
    "monthly_attainment_rate",
    "quarterly_sales",
    "quarterly_target",
    "annual_attainment_rate",
)
OFFICIAL_SANDBOX_LAYER1_PERIOD_KEYS = ("monthly", "quarterly", "yearly")
OFFICIAL_SANDBOX_LAYER1_POINT_KEYS = (
    "actual",
    "target",
    "attainment_rate",
    "gap_amount",
    "gap_million",
    "pi",
    "fgr",
    "scale",
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


def compute_sandbox_layer1_period_metrics(
    monthly_actual: Sequence[float],
    monthly_target: Sequence[float],
) -> dict[str, object]:
    """
    Sandbox Layer 01 기간별 지표를 공식 KPI 엔진에서 계산한다.
    Builder/Template는 이 결과를 표시만 해야 한다.
    """

    def as_float_list(values: Sequence[float], size: int = 12) -> list[float]:
        result = [0.0] * size
        for idx in range(min(len(values), size)):
            result[idx] = float(values[idx] or 0.0)
        return result

    def summarize_series(actual_series: Sequence[float], target_series: Sequence[float]) -> list[dict[str, float]]:
        actual = [float(v or 0.0) for v in actual_series]
        target = [float(v or 0.0) for v in target_series]
        rows: list[dict[str, float]] = []
        non_zero_actual = [v for v in actual if v > 0]
        avg_actual = (sum(non_zero_actual) / len(non_zero_actual)) if non_zero_actual else 0.0
        for idx, (cur_actual, cur_target) in enumerate(zip(actual, target)):
            prev_actual = actual[idx - 1] if idx > 0 else 0.0
            attainment_rate = _rate(cur_actual, cur_target)
            gap_amount = cur_actual - cur_target
            fgr = ((cur_actual - prev_actual) / prev_actual) * 100.0 if prev_actual > 0 else 0.0
            scale = ((cur_actual / max(avg_actual, 1.0)) * 0.6) + ((attainment_rate / 100.0) * 0.4)
            scale = max(0.7, min(1.3, scale))
            rows.append(
                {
                    "actual": round(cur_actual, 0),
                    "target": round(cur_target, 0),
                    "attainment_rate": round(attainment_rate, 1),
                    "gap_amount": round(gap_amount, 0),
                    "gap_million": round(gap_amount / 1_000_000.0, 1),
                    "pi": round(attainment_rate, 1),
                    "fgr": round(fgr, 1),
                    "scale": round(scale, 4),
                }
            )
        return rows

    monthly_actual_values = as_float_list(monthly_actual, size=12)
    monthly_target_values = as_float_list(monthly_target, size=12)

    quarterly_actual = [
        sum(monthly_actual_values[0:3]),
        sum(monthly_actual_values[3:6]),
        sum(monthly_actual_values[6:9]),
        sum(monthly_actual_values[9:12]),
    ]
    quarterly_target = [
        sum(monthly_target_values[0:3]),
        sum(monthly_target_values[3:6]),
        sum(monthly_target_values[6:9]),
        sum(monthly_target_values[9:12]),
    ]

    yearly_actual = [sum(monthly_actual_values)]
    yearly_target = [sum(monthly_target_values)]

    return {
        "monthly": summarize_series(monthly_actual_values, monthly_target_values),
        "quarterly": summarize_series(quarterly_actual, quarterly_target),
        "yearly": summarize_series(yearly_actual, yearly_target),
        "metric_version": SANDBOX_KPI_ENGINE_VERSION,
    }


def validate_layer1_period_metrics_payload(payload: Mapping[str, object]) -> dict[str, object]:
    """
    Layer 01 기간별 KPI 계약 검증.
    서비스 계층은 이 검증을 통과한 값만 template payload에 저장해야 한다.
    """
    missing_periods = [key for key in OFFICIAL_SANDBOX_LAYER1_PERIOD_KEYS if key not in payload]
    if missing_periods:
        raise ValueError(f"layer1 missing period keys: {missing_periods}")
    if payload.get("metric_version") != SANDBOX_KPI_ENGINE_VERSION:
        raise ValueError(
            f"layer1 metric_version mismatch: {payload.get('metric_version')} != {SANDBOX_KPI_ENGINE_VERSION}"
        )
    for period in OFFICIAL_SANDBOX_LAYER1_PERIOD_KEYS:
        series = payload.get(period)
        if not isinstance(series, list):
            raise ValueError(f"layer1[{period}] must be list")
        for idx, point in enumerate(series):
            if not isinstance(point, Mapping):
                raise ValueError(f"layer1[{period}][{idx}] must be object")
            missing_fields = [field for field in OFFICIAL_SANDBOX_LAYER1_POINT_KEYS if field not in point]
            if missing_fields:
                raise ValueError(f"layer1[{period}][{idx}] missing fields: {missing_fields}")
    return dict(payload)


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
