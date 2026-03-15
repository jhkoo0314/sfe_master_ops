"""
RADAR signal engine.

Deterministic threshold-based signal detection only.
No KPI recalculation is performed in this module.
"""

from __future__ import annotations

from modules.radar.schemas import RadarInputStandard, RadarSignal, SignalEvidence


GOAL_WARNING = 95.0
GOAL_CRITICAL = 90.0
PV_WARNING = -15.0
PV_CRITICAL = -25.0
HIR_WARNING = 60.0
HIR_CRITICAL = 50.0
RTR_WARNING = 70.0
RTR_CRITICAL = 60.0


def detect_signals(radar_input: RadarInputStandard) -> list[RadarSignal]:
    signals: list[RadarSignal] = []
    kpi = radar_input.kpi_summary
    scope = _build_scope(radar_input)

    if kpi.goal_attainment_pct < GOAL_CRITICAL:
        signals.append(
            _build_goal_signal(
                severity="critical",
                current_value=kpi.goal_attainment_pct,
                scope=scope,
            )
        )
    elif kpi.goal_attainment_pct < GOAL_WARNING:
        signals.append(
            _build_goal_signal(
                severity="warning",
                current_value=kpi.goal_attainment_pct,
                scope=scope,
            )
        )

    if kpi.pv_change_pct <= PV_CRITICAL:
        signals.append(
            _build_pv_signal(
                severity="critical",
                current_value=kpi.pv_change_pct,
                scope=scope,
                goal_attainment=kpi.goal_attainment_pct,
            )
        )
    elif kpi.pv_change_pct <= PV_WARNING:
        signals.append(
            _build_pv_signal(
                severity="warning",
                current_value=kpi.pv_change_pct,
                scope=scope,
                goal_attainment=kpi.goal_attainment_pct,
            )
        )

    if kpi.hir < HIR_CRITICAL:
        signals.append(
            _build_hir_signal(
                severity="critical",
                current_value=kpi.hir,
                scope=scope,
                goal_attainment=kpi.goal_attainment_pct,
            )
        )
    elif kpi.hir < HIR_WARNING:
        signals.append(
            _build_hir_signal(
                severity="warning",
                current_value=kpi.hir,
                scope=scope,
                goal_attainment=kpi.goal_attainment_pct,
            )
        )

    if kpi.rtr < RTR_CRITICAL:
        signals.append(
            _build_rtr_signal(
                severity="critical",
                current_value=kpi.rtr,
                scope=scope,
                goal_attainment=kpi.goal_attainment_pct,
            )
        )
    elif kpi.rtr < RTR_WARNING:
        signals.append(
            _build_rtr_signal(
                severity="warning",
                current_value=kpi.rtr,
                scope=scope,
                goal_attainment=kpi.goal_attainment_pct,
            )
        )

    compound_signal = _build_compound_risk_if_needed(signals, scope, kpi)
    if compound_signal is not None:
        signals.append(compound_signal)

    return signals


def _build_scope(radar_input: RadarInputStandard) -> dict[str, object]:
    branches = []
    for row in radar_input.scope_summaries.by_branch[:3]:
        branch_key = str(row.get("branch_key") or row.get("branch") or "").strip()
        if branch_key:
            branches.append(branch_key)
    return {
        "level": "company",
        "branch_keys": branches,
    }


def _build_goal_signal(severity: str, current_value: float, scope: dict[str, object]) -> RadarSignal:
    threshold = GOAL_CRITICAL if severity == "critical" else GOAL_WARNING
    return RadarSignal(
        signal_id="SIG-GOAL-001",
        signal_type="goal_underperformance",
        severity=severity,  # type: ignore[arg-type]
        title="Goal attainment below expected range",
        message="Goal attainment is below the management threshold and requires review.",
        scope=scope,
        evidence=SignalEvidence(
            metric="goal_attainment_pct",
            current_value=round(current_value, 2),
            threshold=threshold,
        ),
        possible_explanations=[
            "execution consistency may be uneven across units",
            "performance momentum may be soft in recent cycles",
            "coverage quality may need additional review",
        ],
    )


def _build_pv_signal(
    severity: str,
    current_value: float,
    scope: dict[str, object],
    goal_attainment: float,
) -> RadarSignal:
    threshold = PV_CRITICAL if severity == "critical" else PV_WARNING
    return RadarSignal(
        signal_id="SIG-PV-001",
        signal_type="pv_decline",
        severity=severity,  # type: ignore[arg-type]
        title="PV trend decline detected",
        message="PV change is below tolerance and indicates a weakening trend.",
        scope=scope,
        evidence=SignalEvidence(
            metric="pv_change_pct",
            current_value=round(current_value, 2),
            threshold=threshold,
            related_metrics={"goal_attainment_pct": round(goal_attainment, 2)},
        ),
        possible_explanations=[
            "growth pace may be slowing in key segments",
            "demand progression may be weaker than expected",
            "short-term conversion velocity may be reduced",
        ],
    )


def _build_hir_signal(
    severity: str,
    current_value: float,
    scope: dict[str, object],
    goal_attainment: float,
) -> RadarSignal:
    threshold = HIR_CRITICAL if severity == "critical" else HIR_WARNING
    return RadarSignal(
        signal_id="SIG-HIR-001",
        signal_type="hir_weakness",
        severity=severity,  # type: ignore[arg-type]
        title="HIR weakness detected",
        message="HIR is below threshold and may limit target engagement quality.",
        scope=scope,
        evidence=SignalEvidence(
            metric="hir",
            current_value=round(current_value, 2),
            threshold=threshold,
            related_metrics={"goal_attainment_pct": round(goal_attainment, 2)},
        ),
        possible_explanations=[
            "high-value target contact quality may be uneven",
            "focus allocation may be diluted across priorities",
            "execution cadence may need reinforcement",
        ],
    )


def _build_rtr_signal(
    severity: str,
    current_value: float,
    scope: dict[str, object],
    goal_attainment: float,
) -> RadarSignal:
    threshold = RTR_CRITICAL if severity == "critical" else RTR_WARNING
    return RadarSignal(
        signal_id="SIG-RTR-001",
        signal_type="rtr_weakness",
        severity=severity,  # type: ignore[arg-type]
        title="RTR weakness detected",
        message="RTR is below threshold and relationship stability may require attention.",
        scope=scope,
        evidence=SignalEvidence(
            metric="rtr",
            current_value=round(current_value, 2),
            threshold=threshold,
            related_metrics={"goal_attainment_pct": round(goal_attainment, 2)},
        ),
        possible_explanations=[
            "relationship maintenance intensity may be soft",
            "continuity of account coverage may vary by unit",
            "follow-through quality may need reinforcement",
        ],
    )


def _build_compound_risk_if_needed(
    signals: list[RadarSignal],
    scope: dict[str, object],
    kpi_summary,
) -> RadarSignal | None:
    weak_signals = [
        s
        for s in signals
        if s.signal_type in {"goal_underperformance", "pv_decline", "hir_weakness", "rtr_weakness"}
    ]
    if len(weak_signals) < 2:
        return None

    critical_count = sum(1 for s in weak_signals if s.severity == "critical")
    severity = "critical" if critical_count >= 2 or len(weak_signals) >= 3 else "warning"
    return RadarSignal(
        signal_id="SIG-COMPOUND-001",
        signal_type="compound_risk",
        severity=severity,  # type: ignore[arg-type]
        title="Compound risk detected",
        message="Multiple weak signals are co-occurring and overall risk priority should be elevated.",
        scope=scope,
        evidence=SignalEvidence(
            metric="compound_signal_count",
            current_value=float(len(weak_signals)),
            threshold=2.0,
            related_metrics={
                "goal_attainment_pct": round(float(kpi_summary.goal_attainment_pct), 2),
                "pv_change_pct": round(float(kpi_summary.pv_change_pct), 2),
                "hir": round(float(kpi_summary.hir), 2),
                "rtr": round(float(kpi_summary.rtr), 2),
            },
        ),
        possible_explanations=[
            "multiple performance dimensions may be weakening at the same time",
            "cross-functional coordination pressure may be increasing",
            "risk concentration may require staged management attention",
        ],
    )
