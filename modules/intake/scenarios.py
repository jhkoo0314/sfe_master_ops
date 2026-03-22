from __future__ import annotations

from dataclasses import dataclass

from ops_core.workflow.execution_registry import get_mode_required_uploads


@dataclass(frozen=True)
class IntakeScenario:
    key: str
    label: str
    description: str
    source_keys: tuple[str, ...]


_SCENARIOS: dict[str, IntakeScenario] = {
    "crm_sales_target": IntakeScenario(
        key="crm_sales_target",
        label="CRM + Sales + Target",
        description="CRM, 실적, 목표 기반 기본 온보딩 시나리오",
        source_keys=("crm_activity", "crm_rep_master", "crm_account_assignment", "crm_rules", "sales", "target"),
    ),
    "crm_prescription": IntakeScenario(
        key="crm_prescription",
        label="CRM + Prescription",
        description="CRM과 처방 흐름 추적 입력을 함께 보는 시나리오",
        source_keys=("crm_activity", "crm_rep_master", "crm_account_assignment", "crm_rules", "prescription"),
    ),
    "integrated_full": IntakeScenario(
        key="integrated_full",
        label="Integrated Full",
        description="Sales Data OS 전체 입력 묶음을 보는 통합 시나리오",
        source_keys=("crm_activity", "crm_rep_master", "crm_account_assignment", "crm_rules", "sales", "target", "prescription"),
    ),
}

_MODE_TO_SCENARIO = {
    "crm_to_sandbox": "crm_sales_target",
    "crm_to_territory": "crm_sales_target",
    "sandbox_to_html": "crm_sales_target",
    "sandbox_to_territory": "crm_sales_target",
    "crm_to_pdf": "crm_prescription",
    "crm_to_sandbox_to_territory": "crm_sales_target",
    "integrated_full": "integrated_full",
}


def get_intake_scenario(key: str) -> IntakeScenario | None:
    return _SCENARIOS.get(key)


def resolve_intake_scenario(
    *,
    execution_mode: str | None = None,
    source_keys: list[str] | None = None,
) -> IntakeScenario:
    if execution_mode:
        scenario_key = _MODE_TO_SCENARIO.get(execution_mode)
        if scenario_key and scenario_key in _SCENARIOS:
            return _SCENARIOS[scenario_key]

    source_key_set = set(source_keys or [])
    if source_key_set:
        for scenario in _SCENARIOS.values():
            if source_key_set.issubset(set(scenario.source_keys)):
                return scenario

    return _SCENARIOS["integrated_full"]


def get_scenario_required_sources(execution_mode: str) -> list[str]:
    scenario = resolve_intake_scenario(
        execution_mode=execution_mode,
        source_keys=get_mode_required_uploads(execution_mode),
    )
    return list(scenario.source_keys)
