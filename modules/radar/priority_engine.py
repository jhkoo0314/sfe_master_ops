"""
RADAR priority scoring engine.

Score is deterministic and normalized to 0-100.
"""

from __future__ import annotations

from modules.radar.schemas import PriorityBreakdown, RadarInputStandard, RadarSignal


SEVERITY_WEIGHT = 0.35
IMPACT_WEIGHT = 0.25
PERSISTENCE_WEIGHT = 0.15
SCOPE_WEIGHT = 0.15
CONFIDENCE_WEIGHT = 0.10


def score_signal(signal: RadarSignal, radar_input: RadarInputStandard) -> RadarSignal:
    severity = _severity_score(signal.severity)
    impact = _impact_score(signal, radar_input)
    persistence = _persistence_score(radar_input)
    scope = _scope_score(radar_input)
    confidence = _confidence_score(radar_input)

    weighted = (
        (severity * SEVERITY_WEIGHT)
        + (impact * IMPACT_WEIGHT)
        + (persistence * PERSISTENCE_WEIGHT)
        + (scope * SCOPE_WEIGHT)
        + (confidence * CONFIDENCE_WEIGHT)
    )
    score = int(round(max(0.0, min(100.0, weighted))))
    signal.priority_score = score
    signal.priority_breakdown = PriorityBreakdown(
        severity=round(severity, 2),
        impact=round(impact, 2),
        persistence=round(persistence, 2),
        scope=round(scope, 2),
        confidence=round(confidence, 2),
    )
    return signal


def score_signals(signals: list[RadarSignal], radar_input: RadarInputStandard) -> list[RadarSignal]:
    scored = [score_signal(signal, radar_input) for signal in signals]
    scored.sort(key=lambda s: s.priority_score, reverse=True)
    return scored


def _severity_score(severity: str) -> float:
    return 90.0 if severity == "critical" else 60.0


def _impact_score(signal: RadarSignal, radar_input: RadarInputStandard) -> float:
    k = radar_input.kpi_summary
    if signal.signal_type == "goal_underperformance":
        gap = max(0.0, 100.0 - k.goal_attainment_pct)
        return min(95.0, 45.0 + gap * 2.0)
    if signal.signal_type == "pv_decline":
        drop = abs(min(0.0, k.pv_change_pct))
        return min(95.0, 40.0 + drop * 1.8)
    if signal.signal_type == "hir_weakness":
        gap = max(0.0, 70.0 - k.hir)
        return min(90.0, 38.0 + gap * 1.7)
    if signal.signal_type == "rtr_weakness":
        gap = max(0.0, 75.0 - k.rtr)
        return min(90.0, 38.0 + gap * 1.6)
    if signal.signal_type == "compound_risk":
        return 92.0
    return 50.0


def _persistence_score(radar_input: RadarInputStandard) -> float:
    flags = len(radar_input.sandbox_summary.trend_flags)
    if flags >= 3:
        return 85.0
    if flags == 2:
        return 72.0
    if flags == 1:
        return 60.0
    return 45.0


def _scope_score(radar_input: RadarInputStandard) -> float:
    branch_n = len(radar_input.scope_summaries.by_branch)
    rep_n = len(radar_input.scope_summaries.by_rep)
    raw = (branch_n * 6.0) + (rep_n * 2.5)
    return max(35.0, min(90.0, 35.0 + raw))


def _confidence_score(radar_input: RadarInputStandard) -> float:
    return round(float(radar_input.validation_summary.quality_score) * 100.0, 2)
