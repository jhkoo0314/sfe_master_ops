"""
RADAR service entrypoint.

RADAR is an Intelligence Layer module in Sales Data OS.
It consumes validation-approved KPI outputs and generates:
signals, priority scores, and decision option templates.
"""

from __future__ import annotations

from modules.radar.option_engine import attach_decision_options
from modules.radar.priority_engine import score_signals
from modules.radar.schemas import RadarInputStandard, RadarResultAsset, RadarSummary
from modules.radar.signal_engine import detect_signals


def build_radar_result_asset(radar_input: RadarInputStandard) -> RadarResultAsset:
    """
    Build RADAR result asset from validation-approved radar input.
    """
    detected = detect_signals(radar_input)
    scored = score_signals(detected, radar_input)
    finalized = [attach_decision_options(signal) for signal in scored]
    summary = _build_summary(finalized)
    return RadarResultAsset(
        meta=radar_input.meta,
        kpi_summary=radar_input.kpi_summary,
        validation_summary=radar_input.validation_summary,
        summary=summary,
        signals=finalized,
    )


def _build_summary(signals) -> RadarSummary:
    if not signals:
        return RadarSummary(
            overall_status="normal",
            signal_count=0,
            top_issue=None,
        )
    has_critical = any(signal.severity == "critical" for signal in signals)
    top = signals[0]
    return RadarSummary(
        overall_status="critical" if has_critical else "warning",
        signal_count=len(signals),
        top_issue=top.title,
    )
