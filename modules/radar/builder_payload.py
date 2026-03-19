"""
RADAR builder payload generator.

RADAR creates decision-support payload only.
Builder remains render-only and consumes this payload.
"""

from __future__ import annotations

from common.asset_versions import (
    BUILDER_CONTRACT_VERSION,
    RADAR_BUILDER_PAYLOAD_VERSION,
    attach_builder_payload_version,
)
from modules.radar.schemas import RadarResultAsset


def _format_period_label(period_value: str) -> str:
    text = str(period_value or "").strip()
    if len(text) == 6 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}"
    return text or "-"


def build_radar_builder_payload(asset: RadarResultAsset) -> dict:
    top_signal = asset.signals[0] if asset.signals else None
    branch_options: list[str] = []
    for row in asset.scope_summaries.by_branch:
        branch_name = str(row.get("branch_name") or row.get("branch_key") or "").strip()
        if branch_name and branch_name not in branch_options:
            branch_options.append(branch_name)
    for signal in asset.signals:
        for branch_name in list((signal.scope or {}).get("branch_keys") or []):
            branch_key = str(branch_name).strip()
            if branch_key and branch_key not in branch_options:
                branch_options.append(branch_key)

    trend_series = asset.sandbox_summary.trend_series or {}
    trend_labels = list(trend_series.get("labels") or [])
    goal = round(float(asset.kpi_summary.goal_attainment_pct), 1)
    rtr = round(float(asset.kpi_summary.rtr), 1)
    hir = round(float(asset.kpi_summary.hir), 1)
    if not trend_labels:
        period_label = _format_period_label(asset.meta.period_value)
        trend_labels = [period_label]
    goal_series = list(trend_series.get("goal_attainment") or [])
    rtr_series = list(trend_series.get("rtr") or [])
    hir_series = list(trend_series.get("hir") or [])
    if not goal_series:
        goal_series = [goal]
    if not rtr_series:
        rtr_series = [rtr]
    if not hir_series:
        hir_series = [hir]

    payload = {
        "report_title": "RADAR Decision Brief",
        "period_label": _format_period_label(asset.meta.period_value),
        "overall_status": asset.summary.overall_status,
        "top_issue": asset.summary.top_issue or "No critical issue detected",
        "top_issue_desc": (
            top_signal.message
            if top_signal is not None
            else "No immediate management alert. Continue baseline monitoring."
        ),
        "decision_readiness": int(top_signal.priority_score if top_signal is not None else 40),
        "validation_status": str(asset.validation_summary.status).upper(),
        "signal_count": int(asset.summary.signal_count),
        "branch_options": branch_options,
        "confidence": round(float(asset.validation_summary.quality_score), 2),
        "kpi_snapshot": {
            "goal_attainment_pct": goal,
            "pv_change_pct": round(float(asset.kpi_summary.pv_change_pct), 1),
            "hir": hir,
            "rtr": rtr,
        },
        "trend_chart": {
            "labels": trend_labels,
            "goal_attainment": goal_series,
            "rtr": rtr_series,
            "hir": hir_series,
        },
        "signals": [
            {
                "signal_type": signal.signal_type,
                "severity": signal.severity,
                "priority_score": signal.priority_score,
                "title": signal.title,
                "message": signal.message,
                "scope": signal.scope,
                "evidence": signal.evidence.model_dump(mode="json"),
                "possible_explanations": list(signal.possible_explanations),
                "decision_options": [option.model_dump(mode="json") for option in signal.decision_options],
            }
            for signal in asset.signals
        ],
    }
    return attach_builder_payload_version(
        payload,
        payload_version=RADAR_BUILDER_PAYLOAD_VERSION,
        source_asset_schema_version=asset.schema_version,
        builder_contract_version=BUILDER_CONTRACT_VERSION,
    )
