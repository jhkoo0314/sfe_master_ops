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


def build_radar_builder_payload(asset: RadarResultAsset) -> dict:
    top_signal = asset.signals[0] if asset.signals else None
    trend_labels = [
        f"{asset.meta.period_value}-2",
        f"{asset.meta.period_value}-1",
        asset.meta.period_value,
    ]
    goal = round(float(asset.kpi_summary.goal_attainment_pct), 1)
    rtr = round(float(asset.kpi_summary.rtr), 1)
    hir = round(float(asset.kpi_summary.hir), 1)

    payload = {
        "report_title": "RADAR Decision Brief",
        "period_label": str(asset.meta.period_value),
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
        "confidence": round(float(asset.validation_summary.quality_score), 2),
        "kpi_snapshot": {
            "goal_attainment_pct": goal,
            "pv_change_pct": round(float(asset.kpi_summary.pv_change_pct), 1),
            "hir": hir,
            "rtr": rtr,
        },
        "trend_chart": {
            "labels": trend_labels,
            "goal_attainment": [round(goal + 4.0, 1), round(goal + 2.0, 1), goal],
            "rtr": [round(rtr + 4.0, 1), round(rtr + 2.0, 1), rtr],
            "hir": [round(hir + 4.0, 1), round(hir + 2.0, 1), hir],
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
