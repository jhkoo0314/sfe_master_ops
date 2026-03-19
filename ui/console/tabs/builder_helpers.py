from __future__ import annotations

import json
from pathlib import Path


def build_period_filter_defaults(period_mode: str, selected_year: str, selected_sub_period: str) -> dict:
    defaults = {
        "period_mode": "all",
        "year": selected_year or "",
        "month": "",
        "quarter": "",
    }
    if period_mode == "연간":
        defaults["period_mode"] = "year"
    elif period_mode == "분기별":
        defaults["period_mode"] = "quarter"
        quarter_map = {"1분기": "Q1", "2분기": "Q2", "3분기": "Q3", "4분기": "Q4"}
        defaults["quarter"] = f"{selected_year}-{quarter_map.get(selected_sub_period, 'Q1')}" if selected_year else ""
    elif period_mode == "월별":
        defaults["period_mode"] = "month"
        month_num = selected_sub_period.replace("월", "").zfill(2)
        defaults["month"] = f"{selected_year}-{month_num}" if selected_year else ""
    return defaults


def materialize_periodized_report(report_output_path: str, report_period: str, report_filters: dict) -> str:
    source_path = Path(report_output_path)
    if not source_path.exists():
        return report_output_path
    if report_filters.get("period_mode") == "all":
        return report_output_path

    safe_period = (
        report_period.replace(" ", "_")
        .replace("년", "")
        .replace("월", "")
        .replace("분기", "Q")
        .replace("/", "_")
    )
    target_path = source_path.with_name(f"{source_path.stem}__{safe_period}{source_path.suffix}")
    html = source_path.read_text(encoding="utf-8")
    injected = (
        "<script>"
        f"window.__OPS_DEFAULT_FILTER__ = {json.dumps(report_filters, ensure_ascii=False)};"
        "</script>\n</head>"
    )
    if "window.__OPS_DEFAULT_FILTER__" in html:
        materialized = html
    else:
        materialized = html.replace("</head>", injected, 1)
    target_path.write_text(materialized, encoding="utf-8")
    return str(target_path)


__all__ = ["build_period_filter_defaults", "materialize_periodized_report"]
