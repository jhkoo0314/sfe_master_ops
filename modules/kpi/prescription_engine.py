from __future__ import annotations

import pandas as pd


def _pick_primary_text(series: pd.Series, fallback: str = "") -> str:
    values = [str(v).strip() for v in series if pd.notna(v) and str(v).strip()]
    if not values:
        return fallback
    return pd.Series(values, dtype="string").value_counts().idxmax()


def _safe_percent(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def _build_flow_series_from_maps(
    labels: list[str],
    wholesale_map: dict[str, float],
    mastered_map: dict[str, float],
    pre_share_map: dict[str, float],
    post_share_map: dict[str, float],
) -> list[dict]:
    return [
        {
            "label": month,
            "wholesale_amount": float(wholesale_map.get(month, 0.0)),
            "mastered_amount": float(mastered_map.get(month, 0.0)),
            "tracked_amount": float(post_share_map.get(month, mastered_map.get(month, 0.0))),
            "final_amount": float(pre_share_map.get(month, post_share_map.get(month, mastered_map.get(month, 0.0)))),
        }
        for month in labels
    ]


def build_prescription_builder_context(
    *,
    company_name: str,
    summary: dict,
    claim_df: pd.DataFrame,
    flow_df: pd.DataFrame,
    gap_df: pd.DataFrame,
    rep_kpi_df: pd.DataFrame,
    download_files: dict[str, str] | None = None,
) -> dict:
    flow_df = flow_df.copy()
    claim_df = claim_df.copy()
    gap_df = gap_df.copy()
    rep_kpi_df = rep_kpi_df.copy()

    flow_df["metric_month"] = flow_df["metric_month"].astype(str)
    flow_df["year"] = flow_df["metric_month"].str[:4]
    flow_df["month"] = flow_df["metric_month"].str[:4] + "-" + flow_df["metric_month"].str[4:6]
    flow_df["total_amount"] = pd.to_numeric(flow_df.get("total_amount"), errors="coerce").fillna(0.0)

    if not gap_df.empty and "metric_month" in gap_df.columns:
        gap_df["metric_month"] = gap_df["metric_month"].astype(str)

    claim_defaults = {
        "territory_group": "",
        "territory_name": "",
        "severity": "low",
        "trace_case": "CLAIM_CONFIRMED",
    }
    for col, default in claim_defaults.items():
        if col not in claim_df.columns:
            claim_df[col] = default
        else:
            claim_df[col] = claim_df[col].fillna(default)

    rep_kpi_defaults = {
        "territory_group": rep_kpi_df["branch_name"] if "branch_name" in rep_kpi_df.columns else "",
        "territory_name": rep_kpi_df["branch_name"] if "branch_name" in rep_kpi_df.columns else "",
        "pre_share_amount": rep_kpi_df["total_amount"] if "total_amount" in rep_kpi_df.columns else 0.0,
        "post_share_amount": rep_kpi_df["total_amount"] if "total_amount" in rep_kpi_df.columns else 0.0,
        "settlement_gap_amount": 0.0,
        "settlement_gap_rate": 0.0,
        "status": "No Rule",
        "rule_version": "-",
        "rule_applied": False,
    }
    for col, default in rep_kpi_defaults.items():
        if col not in rep_kpi_df.columns:
            rep_kpi_df[col] = default
        else:
            rep_kpi_df[col] = rep_kpi_df[col].fillna(default)

    for numeric_col in [
        "total_amount",
        "total_quantity",
        "pre_share_amount",
        "post_share_amount",
        "settlement_gap_amount",
        "settlement_gap_rate",
    ]:
        if numeric_col in rep_kpi_df.columns:
            rep_kpi_df[numeric_col] = pd.to_numeric(rep_kpi_df[numeric_col], errors="coerce").fillna(0.0)

    claim_df = claim_df.sort_values(["year_quarter", "tracked_amount"], ascending=[True, False])
    rep_kpi_df = rep_kpi_df.sort_values(["year_quarter", "post_share_amount"], ascending=[True, False])

    flow_month_map_quarter: dict[tuple[str, str, str, str], list[str]] = (
        flow_df.groupby(["year_quarter", "rep_name", "hospital_id", "product_name"])["month"]
        .agg(lambda s: sorted(set(str(v) for v in s if pd.notna(v))))
        .to_dict()
    )
    flow_month_map_year: dict[tuple[str, str, str, str], list[str]] = (
        flow_df.groupby(["year", "rep_name", "hospital_id", "product_name"])["month"]
        .agg(lambda s: sorted(set(str(v) for v in s if pd.notna(v))))
        .to_dict()
    )

    claim_records = claim_df.to_dict(orient="records")
    for row in claim_records:
        period_type = str(row.get("period_type", "quarter"))
        year = str(row.get("year") or "")
        row["year"] = year
        if period_type == "month":
            year_month = str(row.get("year_month") or row.get("period_value") or "")
            months = [year_month] if year_month else []
        elif period_type == "year":
            months = flow_month_map_year.get(
                (year, str(row["rep_name"]), str(row["hospital_id"]), str(row["product_name"])),
                [],
            )
        else:
            year_quarter = str(row.get("year_quarter") or row.get("period_value") or "")
            months = flow_month_map_quarter.get(
                (year_quarter, str(row["rep_name"]), str(row["hospital_id"]), str(row["product_name"])),
                [],
            )
        row["active_months"] = months
        if not row.get("year"):
            row["year"] = str(row.get("year_quarter", "")).split("-")[0]

    rep_kpi_records = rep_kpi_df.to_dict(orient="records")
    for row in rep_kpi_records:
        quarter = str(row.get("year_quarter", ""))
        row["year"] = quarter.split("-")[0] if "-" in quarter else str(row.get("year") or "")
        row["territory"] = row.get("territory_name") or row.get("territory_group") or row.get("branch_name") or "미지정"
        row["brand"] = row.get("product_name")

    connected_flow_df = flow_df[flow_df["flow_status"] == "connected"].copy()
    connected_flow_df["month"] = connected_flow_df["month"].astype(str)
    connected_flow_df["year"] = connected_flow_df["year"].astype(str)
    trace_group_keys = [
        col for col in [
            "rep_name",
            "branch_name",
            "territory_group",
            "territory_name",
            "hospital_id",
            "hospital_name",
            "product_name",
        ]
        if col in connected_flow_df.columns
    ]

    def _build_trace_summary(period_type: str, period_column: str) -> list[dict]:
        grouped = (
            connected_flow_df.groupby([period_column, *trace_group_keys], dropna=False)
            .agg(
                total_amount=("total_amount", "sum"),
                pharmacy_count=("pharmacy_id", "nunique"),
                wholesaler_count=("wholesaler_id", "nunique"),
            )
            .reset_index()
        )
        if grouped.empty:
            return []
        grouped = grouped.rename(columns={period_column: "period_value"})
        grouped["period_type"] = period_type
        grouped["year"] = grouped["period_value"].astype(str).str[:4]
        grouped["period_label"] = grouped["period_value"].astype(str)
        return grouped.to_dict(orient="records")

    trace_summary_records = []
    trace_summary_records.extend(_build_trace_summary("month", "month"))
    trace_summary_records.extend(_build_trace_summary("quarter", "year_quarter"))
    trace_summary_records.extend(_build_trace_summary("year", "year"))

    overview = {
        "standard_record_count": summary.get("standard_record_count", 0),
        "flow_record_count": summary.get("flow_record_count", 0),
        "gap_record_count": summary.get("gap_record_count", 0),
        "connected_hospital_count": summary.get("connected_hospital_count", 0),
        "flow_completion_rate": summary.get("flow_completion_rate", 0),
        "quality_status": summary.get("quality_status", "unknown"),
        "quality_score": summary.get("quality_score", 0),
        "claim_validation_summary": summary.get("claim_validation_summary", {}),
    }

    month_claim_df = claim_df[claim_df["period_type"].astype(str) == "month"].copy()
    month_claim_df["month_key"] = month_claim_df["year_month"].fillna(month_claim_df["period_value"]).astype(str)
    monthly_wholesale = flow_df.groupby("month", dropna=False)["total_amount"].sum().to_dict()
    monthly_mastered = connected_flow_df.groupby("month", dropna=False)["total_amount"].sum().to_dict()
    monthly_pre_share = month_claim_df.groupby("month_key", dropna=False)["claimed_amount"].sum().to_dict()
    monthly_post_share = month_claim_df.groupby("month_key", dropna=False)["tracked_amount"].sum().to_dict()
    month_labels = sorted(
        {
            *[str(key) for key in monthly_wholesale.keys()],
            *[str(key) for key in monthly_pre_share.keys()],
            *[str(key) for key in monthly_post_share.keys()],
        }
    )
    flow_series = _build_flow_series_from_maps(
        month_labels,
        monthly_wholesale,
        monthly_mastered,
        monthly_pre_share,
        monthly_post_share,
    )
    flow_summary = {
        "total_wholesale_amount": round(sum(item["wholesale_amount"] for item in flow_series), 2),
        "mastered_amount": round(sum(item["mastered_amount"] for item in flow_series), 2),
        "tracked_amount": round(sum(item["tracked_amount"] for item in flow_series), 2),
        "pre_kpi_final_amount": round(sum(item["final_amount"] for item in flow_series), 2),
    }
    territory_flow_series: dict[str, list[dict]] = {}
    territory_keys = sorted(
        {
            str(value).strip()
            for value in pd.concat(
                [
                    flow_df.get("territory_group", pd.Series(dtype="string")).dropna().astype(str),
                    month_claim_df.get("territory_group", pd.Series(dtype="string")).dropna().astype(str),
                ],
                ignore_index=True,
            ).tolist()
            if str(value).strip()
        }
    )
    for territory in territory_keys:
        territory_wholesale = (
            flow_df[flow_df.get("territory_group", "").astype(str) == territory]
            .groupby("month", dropna=False)["total_amount"]
            .sum()
            .to_dict()
        )
        territory_mastered = (
            connected_flow_df[connected_flow_df.get("territory_group", "").astype(str) == territory]
            .groupby("month", dropna=False)["total_amount"]
            .sum()
            .to_dict()
        )
        territory_month_claim_df = month_claim_df[month_claim_df.get("territory_group", "").astype(str) == territory]
        territory_pre_share = territory_month_claim_df.groupby("month_key", dropna=False)["claimed_amount"].sum().to_dict()
        territory_post_share = territory_month_claim_df.groupby("month_key", dropna=False)["tracked_amount"].sum().to_dict()
        territory_flow_series[territory] = _build_flow_series_from_maps(
            month_labels,
            territory_wholesale,
            territory_mastered,
            territory_pre_share,
            territory_post_share,
        )

    rule_applied_count = int(pd.Series(rep_kpi_df["rule_applied"]).fillna(False).astype(bool).sum()) if not rep_kpi_df.empty else 0
    rule_coverage = _safe_percent(rule_applied_count, len(rep_kpi_df))
    mastering_ratio = float(overview["flow_completion_rate"] or 0)
    tracking_coverage = _safe_percent(len(connected_flow_df), len(flow_df))
    quality_status = str(overview["quality_status"] or "unknown").lower()
    quality_score = float(overview["quality_score"] or 0)
    validation_badge = (
        "Validated"
        if quality_status == "pass"
        else "Review"
        if quality_status == "warn"
        else "Check"
    )
    pipeline_steps = [
        {
            "step": "STEP 01",
            "title": "Ingest Merge",
            "metric": f"{int(overview['standard_record_count']):,} Rows",
            "status": "complete" if overview["standard_record_count"] else "error",
        },
        {
            "step": "STEP 02",
            "title": "Mastering",
            "metric": f"Mapping: {mastering_ratio * 100:.1f}%",
            "status": "complete" if mastering_ratio >= 0.95 else "active",
        },
        {
            "step": "STEP 03",
            "title": "Tracking Val.",
            "metric": f"Coverage: {tracking_coverage * 100:.1f}%",
            "status": "complete" if tracking_coverage >= 0.9 else "active",
        },
        {
            "step": "STEP 04",
            "title": "Share Settlement",
            "metric": f"{rule_applied_count:,} Rules Applied",
            "status": "complete" if rule_applied_count else "active",
        },
        {
            "step": "STEP 05",
            "title": "KPI Publish",
            "metric": f"Ready ({100 if len(rep_kpi_df) else 0}%)",
            "status": "complete" if len(rep_kpi_df) else "active",
        },
        {
            "step": "STEP 06",
            "title": "Validation",
            "metric": f"{validation_badge} ({quality_score:.1f})",
            "status": "complete" if quality_status == "pass" else "active" if quality_status == "warn" else "error",
        },
    ]

    diagnostics = {
        "mastering_ratio": mastering_ratio,
        "tracking_coverage": tracking_coverage,
        "rule_coverage": rule_coverage,
        "high_severity": int(overview["claim_validation_summary"].get("suspect_count", 0)),
        "warnings": int(overview["claim_validation_summary"].get("review_count", 0)),
        "quality_status": quality_status,
        "quality_score": quality_score,
        "rule_applied_count": rule_applied_count,
    }

    filters = {
        "quarters": sorted(rep_kpi_df["year_quarter"].dropna().astype(str).unique().tolist()) if "year_quarter" in rep_kpi_df.columns else [],
        "territories": sorted(
            {
                str(v).strip()
                for v in rep_kpi_df.get("territory_group", pd.Series(dtype="string")).dropna().tolist()
                if str(v).strip()
            }
        ),
    }
    filters["default_quarter"] = filters["quarters"][-1] if filters["quarters"] else ""
    filters["default_territory"] = ""

    trace_logs: list[dict] = []
    suspect_claims = claim_df[claim_df["verdict"].isin(["SUSPECT", "REVIEW"])].copy()
    if not suspect_claims.empty:
        suspect_claims["abs_variance_rate"] = suspect_claims["variance_rate"].abs()
        suspect_claims = suspect_claims.sort_values(["abs_variance_rate", "tracked_amount"], ascending=[False, False])
        for row in suspect_claims.head(18).to_dict(orient="records"):
            trace_logs.append(
                {
                    "time": str(row.get("period_label") or row.get("year_quarter") or row.get("year_month") or ""),
                    "case": str(row.get("trace_case") or "CLAIM_REVIEW"),
                    "detail": (
                        f"{row.get('rep_name', '미지정')} / {row.get('product_name', '품목없음')} / "
                        f"{row.get('hospital_name', '병원없음')} : 차이율 {abs(float(row.get('variance_rate') or 0)) * 100:.1f}%"
                    ),
                    "sev": str(row.get("severity") or "med"),
                }
            )
    if not gap_df.empty:
        for row in gap_df.head(10).to_dict(orient="records"):
            trace_logs.append(
                {
                    "time": str(row.get("year_quarter") or row.get("metric_month") or ""),
                    "case": "UNMAPPED_PHARMACY",
                    "detail": f"{row.get('pharmacy_name', '약국없음')} / {row.get('product_name', row.get('product_id', '품목없음'))} : {row.get('gap_reason', '미확인')}",
                    "sev": "high",
                }
            )
    no_rule_rows = rep_kpi_df[~pd.Series(rep_kpi_df["rule_applied"]).fillna(False).astype(bool)] if not rep_kpi_df.empty else pd.DataFrame()
    if not no_rule_rows.empty:
        for row in no_rule_rows.sort_values("total_amount", ascending=False).head(10).to_dict(orient="records"):
            trace_logs.append(
                {
                    "time": str(row.get("year_quarter") or ""),
                    "case": "NO_SETTLEMENT_RULE",
                    "detail": f"{row.get('rep_name', '미지정')} / {row.get('product_name', '품목없음')} : 규칙 미적용",
                    "sev": "low",
                }
            )
    if not trace_logs:
        trace_logs.append(
            {
                "time": "SYSTEM",
                "case": "QUALITY_GATE",
                "detail": f"Prescription 품질 상태 {quality_status.upper()} / 점수 {quality_score:.1f}",
                "sev": "low",
            }
        )

    console_rows = []
    for row in claim_records:
        if str(row.get("period_type") or "") != "quarter":
            continue
        verdict = str(row.get("verdict") or "PASS").upper()
        status = "WARNING" if verdict == "REVIEW" else verdict
        console_rows.append(
            {
                "year_quarter": str(row.get("year_quarter") or row.get("period_value") or ""),
                "rep_name": row.get("rep_name") or "미지정",
                "rep_id": row.get("rep_id") or "",
                "territory": row.get("territory_name") or row.get("territory_group") or row.get("branch_name") or "미지정",
                "territory_group": row.get("territory_group") or row.get("branch_name") or "",
                "branch_name": row.get("branch_name") or "",
                "brand": row.get("product_name") or "품목없음",
                "claimed_amount": float(row.get("claimed_amount") or 0.0),
                "tracked_amount": float(row.get("tracked_amount") or 0.0),
                "status": status,
                "variance_amount": float(row.get("variance_amount") or 0.0),
                "variance_rate": float(row.get("variance_rate") or 0.0),
            }
        )

    return {
        "company": company_name,
        "overview": overview,
        "claims": claim_records,
        "gaps": gap_df.to_dict(orient="records"),
        "hospital_traces": trace_summary_records,
        "rep_kpis": rep_kpi_records,
        "pipeline_steps": pipeline_steps,
        "flow_summary": flow_summary,
        "flow_series": flow_series,
        "flow_series_by_territory": territory_flow_series,
        "diagnostics": diagnostics,
        "filters": filters,
        "console_rows": console_rows,
        "trace_logs": trace_logs,
        "logic_reference": {
            "settlement_basis": "quarter claim_validation이 있는 행은 claim/tracked 금액을 사용하고, 없는 행은 total_amount를 그대로 유지합니다.",
            "rule_version_note": "현재 rule_version은 데모용 claim 기반 계산에만 부여됩니다.",
        },
        "download_files": download_files or {},
    }
