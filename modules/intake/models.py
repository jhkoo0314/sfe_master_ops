from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

IntakeLevel = Literal["info", "warn", "error"]
IntakeStatus = Literal["ready", "ready_with_fixes", "needs_review", "blocked"]
TimingDirection = Literal["ahead", "behind"]


@dataclass(frozen=True)
class IntakeFinding:
    level: IntakeLevel
    source_key: str
    issue_code: str
    message: str
    column_name: str | None = None
    row_estimate: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntakeFix:
    source_key: str
    fix_type: str
    message: str
    affected_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntakeSuggestion:
    source_key: str
    suggestion_type: str
    message: str
    candidate_columns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntakePeriodCoverage:
    source_key: str
    period_column: str
    start_month: str
    end_month: str
    month_count: int
    distinct_months: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntakeTimingAlert:
    level: IntakeLevel
    source_key: str
    message: str
    direction: TimingDirection
    month_gap: int
    reference_end_month: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntakeSourceInput:
    source_key: str
    original_path: str
    target_path: str
    file_name: str | None = None
    file_ext: str | None = None
    row_count: int | None = None
    columns: list[str] = field(default_factory=list)
    preview_rows: list[dict[str, Any]] = field(default_factory=list)
    fixes: list[IntakeFix] = field(default_factory=list)
    is_required: bool = False
    upload_present: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OnboardingPackage:
    company_key: str
    source_key: str
    original_path: str
    staged_path: str
    status: IntakeStatus
    scenario_key: str | None = None
    scenario_label: str | None = None
    findings: list[IntakeFinding] = field(default_factory=list)
    fixes: list[IntakeFix] = field(default_factory=list)
    suggestions: list[IntakeSuggestion] = field(default_factory=list)
    resolved_mapping: dict[str, str] = field(default_factory=dict)
    period_coverage: IntakePeriodCoverage | None = None
    ready_for_adapter: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["findings"] = [item.to_dict() for item in self.findings]
        payload["fixes"] = [item.to_dict() for item in self.fixes]
        payload["suggestions"] = [item.to_dict() for item in self.suggestions]
        return payload


@dataclass(frozen=True)
class IntakeRequest:
    project_root: str
    company_key: str
    company_name: str
    sources: list[IntakeSourceInput]
    execution_mode: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sources"] = [item.to_dict() for item in self.sources]
        return payload


@dataclass
class IntakeResult:
    company_key: str
    company_name: str
    status: IntakeStatus
    cache_signature: str | None = None
    scenario_key: str | None = None
    scenario_label: str | None = None
    findings: list[IntakeFinding] = field(default_factory=list)
    fixes: list[IntakeFix] = field(default_factory=list)
    suggestions: list[IntakeSuggestion] = field(default_factory=list)
    period_coverages: list[IntakePeriodCoverage] = field(default_factory=list)
    timing_alerts: list[IntakeTimingAlert] = field(default_factory=list)
    analysis_basis_sources: list[str] = field(default_factory=list)
    analysis_start_month: str | None = None
    analysis_end_month: str | None = None
    analysis_month_count: int | None = None
    analysis_summary_message: str | None = None
    proceed_confirmation_message: str | None = None
    packages: list[OnboardingPackage] = field(default_factory=list)

    @property
    def ready_for_adapter(self) -> bool:
        return all(package.ready_for_adapter for package in self.packages)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["findings"] = [item.to_dict() for item in self.findings]
        payload["fixes"] = [item.to_dict() for item in self.fixes]
        payload["suggestions"] = [item.to_dict() for item in self.suggestions]
        payload["period_coverages"] = [item.to_dict() for item in self.period_coverages]
        payload["timing_alerts"] = [item.to_dict() for item in self.timing_alerts]
        payload["packages"] = [item.to_dict() for item in self.packages]
        payload["ready_for_adapter"] = self.ready_for_adapter
        return payload
