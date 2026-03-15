"""
RADAR decision option template engine.

Templates are management-level options only.
Field-level schedule or visit instructions are intentionally excluded.
"""

from __future__ import annotations

from modules.radar.schemas import DecisionOptionTemplate, RadarSignal


def attach_decision_options(signal: RadarSignal) -> RadarSignal:
    signal.decision_options = build_decision_options(signal)
    return signal


def build_decision_options(signal: RadarSignal) -> list[DecisionOptionTemplate]:
    if signal.signal_type == "compound_risk":
        return [
            DecisionOptionTemplate(
                option_code="A",
                style="strategic_escalation",
                label="Strategic Escalation",
                description="Escalate to management review and validate cross-functional resource alignment.",
            ),
            DecisionOptionTemplate(
                option_code="B",
                style="selective_intervention",
                label="Selective Intervention",
                description="Apply focused support to the most affected groups and track stabilization signals.",
            ),
            DecisionOptionTemplate(
                option_code="C",
                style="monitoring_hold",
                label="Monitoring Hold",
                description="Hold structure for one cycle and monitor whether combined risk indicators improve.",
            ),
        ]

    if signal.severity == "critical":
        return [
            DecisionOptionTemplate(
                option_code="A",
                style="coaching_focus",
                label="Coaching Focus",
                description="Intensify manager coaching on KPI interpretation and execution consistency.",
            ),
            DecisionOptionTemplate(
                option_code="B",
                style="selective_intervention",
                label="Selective Intervention",
                description="Review high-risk segments first and apply targeted management support.",
            ),
            DecisionOptionTemplate(
                option_code="C",
                style="strategic_escalation",
                label="Strategic Escalation",
                description="Raise issue to leadership review if the next cycle does not stabilize.",
            ),
        ]

    return [
        DecisionOptionTemplate(
            option_code="A",
            style="coaching_focus",
            label="Coaching Focus",
            description="Run a branch-level coaching review to improve interpretation and consistency.",
        ),
        DecisionOptionTemplate(
            option_code="B",
            style="monitoring_hold",
            label="Monitoring Hold",
            description="Monitor one additional cycle before broad intervention and compare trend movement.",
        ),
        DecisionOptionTemplate(
            option_code="C",
            style="selective_intervention",
            label="Selective Intervention",
            description="Apply limited intervention only to segments with repeated weak indicators.",
        ),
    ]
