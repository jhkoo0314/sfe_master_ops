from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class ExecutionStepDefinition:
    module: str
    label: str
    runner: Callable[[], None]


@dataclass(frozen=True)
class ExecutionModeDefinition:
    key: str
    label: str
    description: str
    requirements: str
    modules: tuple[str, ...]
    required_uploads: tuple[str, ...]
    step_builder: Callable[[], list[ExecutionStepDefinition]]


@dataclass(frozen=True)
class ExecutionContext:
    project_root: str
    company_key: str
    company_name: str
    source_targets: Mapping[str, tuple[str, str]]


@dataclass
class ExecutionStepResult:
    step: int
    module: str
    status: str
    score: float = 0.0
    duration_ms: int = 0
    reasoning_note: str = ""
    next_modules: list[str] = field(default_factory=list)
    error: str | None = None
    summary_path: str | None = None
    summary: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionPreparationResult:
    monthly_merge_result: Any | None = None
    staged_paths: list[str] = field(default_factory=list)
    intake_result: Any | None = None
    staged_source_root: str | None = None
    recommended_actions: list[str] = field(default_factory=list)


@dataclass
class ExecutionLoopResult:
    steps: list[ExecutionStepResult] = field(default_factory=list)
    final_eligible_modules: list[str] = field(default_factory=list)
    summary_by_module: dict[str, dict[str, Any]] = field(default_factory=dict)
    recommended_actions: list[str] = field(default_factory=list)


@dataclass
class ExecutionRunResult:
    run_id: str
    execution_mode: str
    execution_mode_label: str
    company_key: str
    company_name: str
    overall_status: str
    overall_score: float = 0.0
    steps: list[ExecutionStepResult] = field(default_factory=list)
    final_eligible_modules: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    total_duration_ms: int = 0
    summary_by_module: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["steps"] = [step.to_dict() for step in self.steps]
        return payload
