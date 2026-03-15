"""
RADAR schema definitions.

RADAR belongs to the Intelligence Layer in Sales Data OS.
RADAR consumes validation-approved KPI outputs and summary signals only.
RADAR does not recalculate KPI.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from common.asset_versions import RADAR_INPUT_SCHEMA_VERSION, RADAR_RESULT_SCHEMA_VERSION


SignalType = Literal[
    "goal_underperformance",
    "pv_decline",
    "hir_weakness",
    "rtr_weakness",
    "compound_risk",
]
SignalSeverity = Literal["warning", "critical"]
OptionStyle = Literal[
    "coaching_focus",
    "monitoring_hold",
    "selective_intervention",
    "strategic_escalation",
]
OverallStatus = Literal["normal", "warning", "critical"]


class RadarMeta(BaseModel):
    company_key: str
    run_id: str
    period_type: str = "monthly"
    period_value: str
    source_status: str = "validation_approved"


class RadarKpiSummary(BaseModel):
    goal_attainment_pct: float
    pv_change_pct: float
    hir: float
    rtr: float
    bcr: Optional[float] = None
    phr: Optional[float] = None


class RadarValidationSummary(BaseModel):
    status: Literal["approved", "usable", "rejected", "failed", "pending"]
    warnings: list[str] = Field(default_factory=list)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @property
    def is_approved_or_usable(self) -> bool:
        return self.status in {"approved", "usable"}


class RadarSandboxSummary(BaseModel):
    top_declines: list[dict] = Field(default_factory=list)
    top_gains: list[dict] = Field(default_factory=list)
    trend_flags: list[str] = Field(default_factory=list)


class RadarScopeSummaries(BaseModel):
    by_branch: list[dict] = Field(default_factory=list)
    by_rep: list[dict] = Field(default_factory=list)
    by_product: list[dict] = Field(default_factory=list)


class RadarInputStandard(BaseModel):
    """
    Validation-approved RADAR input contract.
    """

    schema_version: str = Field(default=RADAR_INPUT_SCHEMA_VERSION)
    meta: RadarMeta
    kpi_summary: RadarKpiSummary
    scope_summaries: RadarScopeSummaries = Field(default_factory=RadarScopeSummaries)
    validation_summary: RadarValidationSummary
    sandbox_summary: RadarSandboxSummary = Field(default_factory=RadarSandboxSummary)

    @model_validator(mode="after")
    def _validate_approved_status(self) -> "RadarInputStandard":
        if not self.validation_summary.is_approved_or_usable:
            raise ValueError(
                "RADAR requires validation-approved or usable input "
                f"(current: {self.validation_summary.status})."
            )
        if self.meta.source_status not in {"validation_approved", "validation_usable"}:
            raise ValueError(
                "RADAR meta.source_status must be validation_approved or validation_usable."
            )
        return self


class SignalEvidence(BaseModel):
    metric: str
    current_value: float
    threshold: float
    related_metrics: dict[str, float] = Field(default_factory=dict)


class PriorityBreakdown(BaseModel):
    severity: float
    impact: float
    persistence: float
    scope: float
    confidence: float


class DecisionOptionTemplate(BaseModel):
    option_code: str
    style: OptionStyle
    label: str
    description: str


class RadarSignal(BaseModel):
    signal_id: str
    signal_type: SignalType
    severity: SignalSeverity
    priority_score: int = 0
    title: str
    message: str
    scope: dict[str, object] = Field(default_factory=dict)
    evidence: SignalEvidence
    possible_explanations: list[str] = Field(default_factory=list)
    decision_options: list[DecisionOptionTemplate] = Field(default_factory=list)
    priority_breakdown: Optional[PriorityBreakdown] = None


class RadarSummary(BaseModel):
    overall_status: OverallStatus
    signal_count: int
    top_issue: Optional[str] = None


class RadarResultAsset(BaseModel):
    """
    RADAR output asset for downstream Builder consumption.
    """

    schema_version: str = Field(default=RADAR_RESULT_SCHEMA_VERSION)
    asset_type: str = "radar_result_asset"
    meta: RadarMeta
    kpi_summary: RadarKpiSummary
    validation_summary: RadarValidationSummary
    summary: RadarSummary
    signals: list[RadarSignal] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)
