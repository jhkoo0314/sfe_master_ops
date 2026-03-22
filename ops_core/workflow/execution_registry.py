from __future__ import annotations

import sys
from functools import lru_cache

from ops_core.workflow.execution_models import ExecutionModeDefinition, ExecutionStepDefinition


def _run_territory_pipeline(
    normalize_territory_main,
    validate_territory_main,
) -> None:
    normalize_territory_main()
    validate_territory_main()


def _run_crm_to_territory_pipeline(
    normalize_sandbox_main,
    validate_sandbox_main,
    normalize_territory_main,
    validate_territory_main,
) -> None:
    normalize_sandbox_main()
    validate_sandbox_main()
    _run_territory_pipeline(normalize_territory_main, validate_territory_main)


@lru_cache(maxsize=1)
def _get_step_registry() -> dict[str, list[ExecutionStepDefinition]]:
    from scripts.normalize_crm_source import main as normalize_crm_main
    from scripts.normalize_prescription_source import main as normalize_rx_main
    from scripts.normalize_sandbox_source import main as normalize_sandbox_main
    from scripts.normalize_territory_source import main as normalize_territory_main
    from scripts.validate_builder_with_ops import main as validate_builder_main
    from scripts.validate_crm_with_ops import main as validate_crm_main
    from scripts.validate_prescription_with_ops import main as validate_rx_main
    from scripts.validate_radar_with_ops import main as validate_radar_main
    from scripts.validate_sandbox_with_ops import main as validate_sandbox_main
    from scripts.validate_territory_with_ops import main as validate_territory_main

    return {
        "crm_to_sandbox": [
            ExecutionStepDefinition(
                module="crm",
                label="CRM 정규화 및 검증",
                runner=lambda: (normalize_crm_main(), validate_crm_main()),
            ),
            ExecutionStepDefinition(
                module="sandbox",
                label="Sandbox 정규화 및 검증",
                runner=lambda: (normalize_sandbox_main(), validate_sandbox_main()),
            ),
            ExecutionStepDefinition(
                module="radar",
                label="RADAR 신호 생성",
                runner=validate_radar_main,
            ),
        ],
        "crm_to_territory": [
            ExecutionStepDefinition(
                module="crm",
                label="CRM 정규화 및 검증",
                runner=lambda: (normalize_crm_main(), validate_crm_main()),
            ),
            ExecutionStepDefinition(
                module="territory",
                label="Territory 입력 정규화 및 검증",
                runner=lambda: _run_crm_to_territory_pipeline(
                    normalize_sandbox_main,
                    validate_sandbox_main,
                    normalize_territory_main,
                    validate_territory_main,
                ),
            ),
            ExecutionStepDefinition(
                module="radar",
                label="RADAR 신호 생성",
                runner=validate_radar_main,
            ),
        ],
        "sandbox_to_html": [
            ExecutionStepDefinition(
                module="crm",
                label="CRM 정규화 및 검증",
                runner=lambda: (normalize_crm_main(), validate_crm_main()),
            ),
            ExecutionStepDefinition(
                module="sandbox",
                label="Sandbox 정규화 및 검증",
                runner=lambda: (normalize_sandbox_main(), validate_sandbox_main()),
            ),
            ExecutionStepDefinition(
                module="radar",
                label="RADAR 신호 생성",
                runner=validate_radar_main,
            ),
            ExecutionStepDefinition(
                module="builder",
                label="Builder HTML 생성",
                runner=validate_builder_main,
            ),
        ],
        "sandbox_to_territory": [
            ExecutionStepDefinition(
                module="crm",
                label="CRM 정규화 및 검증",
                runner=lambda: (normalize_crm_main(), validate_crm_main()),
            ),
            ExecutionStepDefinition(
                module="sandbox",
                label="Sandbox 정규화 및 검증",
                runner=lambda: (normalize_sandbox_main(), validate_sandbox_main()),
            ),
            ExecutionStepDefinition(
                module="territory",
                label="Territory 입력 정규화 및 검증",
                runner=lambda: _run_territory_pipeline(normalize_territory_main, validate_territory_main),
            ),
            ExecutionStepDefinition(
                module="radar",
                label="RADAR 신호 생성",
                runner=validate_radar_main,
            ),
        ],
        "crm_to_pdf": [
            ExecutionStepDefinition(
                module="crm",
                label="CRM 정규화 및 검증",
                runner=lambda: (normalize_crm_main(), validate_crm_main()),
            ),
            ExecutionStepDefinition(
                module="prescription",
                label="Prescription 정규화 및 검증",
                runner=lambda: (normalize_rx_main(), validate_rx_main()),
            ),
        ],
        "crm_to_sandbox_to_territory": [
            ExecutionStepDefinition(
                module="crm",
                label="CRM 정규화 및 검증",
                runner=lambda: (normalize_crm_main(), validate_crm_main()),
            ),
            ExecutionStepDefinition(
                module="sandbox",
                label="Sandbox 정규화 및 검증",
                runner=lambda: (normalize_sandbox_main(), validate_sandbox_main()),
            ),
            ExecutionStepDefinition(
                module="territory",
                label="Territory 입력 정규화 및 검증",
                runner=lambda: _run_territory_pipeline(normalize_territory_main, validate_territory_main),
            ),
            ExecutionStepDefinition(
                module="radar",
                label="RADAR 신호 생성",
                runner=validate_radar_main,
            ),
        ],
        "integrated_full": [
            ExecutionStepDefinition(
                module="crm",
                label="CRM 정규화 및 검증",
                runner=lambda: (normalize_crm_main(), validate_crm_main()),
            ),
            ExecutionStepDefinition(
                module="prescription",
                label="Prescription 정규화 및 검증",
                runner=lambda: (normalize_rx_main(), validate_rx_main()),
            ),
            ExecutionStepDefinition(
                module="sandbox",
                label="Sandbox 정규화 및 검증",
                runner=lambda: (normalize_sandbox_main(), validate_sandbox_main()),
            ),
            ExecutionStepDefinition(
                module="territory",
                label="Territory 입력 정규화 및 검증",
                runner=lambda: _run_territory_pipeline(normalize_territory_main, validate_territory_main),
            ),
            ExecutionStepDefinition(
                module="radar",
                label="RADAR 신호 생성",
                runner=validate_radar_main,
            ),
            ExecutionStepDefinition(
                module="builder",
                label="Builder HTML 생성",
                runner=validate_builder_main,
            ),
        ],
    }


def _build_step_builder(mode: str):
    return lambda: list(_get_step_registry().get(mode, []))


_MODE_DEFINITIONS = {
    "crm_to_sandbox": ExecutionModeDefinition(
        key="crm_to_sandbox",
        label="CRM -> Sandbox",
        description="CRM 정리 결과를 시작점으로 샌드박스 분석까지 확인하는 흐름입니다.",
        requirements="필수: CRM 활동 원본, 담당자 마스터 / 권장: 실적, 목표",
        modules=("crm", "sandbox", "radar"),
        required_uploads=("crm_activity", "crm_rep_master", "crm_account_assignment", "sales", "target"),
        step_builder=_build_step_builder("crm_to_sandbox"),
    ),
    "crm_to_territory": ExecutionModeDefinition(
        key="crm_to_territory",
        label="CRM -> Territory",
        description="CRM 활동을 Territory용 활동 표준으로 바꾸고, 내부 성과 준비 단계를 거쳐 권역 분석까지 바로 확인하는 흐름입니다.",
        requirements="필수: CRM 활동 원본, 담당자 마스터, 거래처 담당 배정, 실적, 목표",
        modules=("crm", "territory", "radar"),
        required_uploads=("crm_activity", "crm_rep_master", "crm_account_assignment", "sales", "target"),
        step_builder=_build_step_builder("crm_to_territory"),
    ),
    "sandbox_to_html": ExecutionModeDefinition(
        key="sandbox_to_html",
        label="Sandbox -> HTML",
        description="샌드박스 결과가 이미 있다고 보고 HTML 보고서 생성 단계만 점검하는 흐름입니다.",
        requirements="필수: Sandbox 결과 또는 실적, 목표",
        modules=("sandbox", "radar", "builder"),
        required_uploads=("crm_activity", "crm_rep_master", "crm_account_assignment", "sales", "target"),
        step_builder=_build_step_builder("sandbox_to_html"),
    ),
    "sandbox_to_territory": ExecutionModeDefinition(
        key="sandbox_to_territory",
        label="Sandbox -> Territory",
        description="샌드박스 결과를 권역 분석으로 넘기는 흐름을 점검합니다.",
        requirements="필수: Sandbox 결과 또는 실적, 목표 / 권장: CRM 활동",
        modules=("sandbox", "territory", "radar"),
        required_uploads=("crm_activity", "crm_rep_master", "crm_account_assignment", "sales", "target"),
        step_builder=_build_step_builder("sandbox_to_territory"),
    ),
    "crm_to_pdf": ExecutionModeDefinition(
        key="crm_to_pdf",
        label="CRM -> PDF",
        description="CRM과 Prescription 흐름을 함께 보며 처방 추적 쪽을 점검하는 흐름입니다.",
        requirements="필수: CRM 활동 원본, 담당자 마스터 / 권장: Prescription fact_ship",
        modules=("crm", "prescription"),
        required_uploads=("crm_activity", "crm_rep_master", "crm_account_assignment", "prescription"),
        step_builder=_build_step_builder("crm_to_pdf"),
    ),
    "crm_to_sandbox_to_territory": ExecutionModeDefinition(
        key="crm_to_sandbox_to_territory",
        label="CRM -> Sandbox -> Territory",
        description="CRM에서 시작해 샌드박스와 권역 분석까지 이어지는 대표 검증 흐름입니다.",
        requirements="필수: CRM 활동 원본, 담당자 마스터, 실적, 목표",
        modules=("crm", "sandbox", "territory", "radar"),
        required_uploads=("crm_activity", "crm_rep_master", "crm_account_assignment", "sales", "target"),
        step_builder=_build_step_builder("crm_to_sandbox_to_territory"),
    ),
    "integrated_full": ExecutionModeDefinition(
        key="integrated_full",
        label="통합 실행",
        description="CRM, Prescription, Sandbox, Territory, Builder를 모두 거치는 전체 검증 흐름입니다.",
        requirements="필수: CRM 활동 원본, 담당자 마스터, 실적, 목표 / 권장: Prescription, 담당 배정",
        modules=("crm", "prescription", "sandbox", "territory", "radar", "builder"),
        required_uploads=("crm_activity", "crm_rep_master", "crm_account_assignment", "sales", "target", "prescription"),
        step_builder=_build_step_builder("integrated_full"),
    ),
}


_SUMMARY_RELATIVE_PATHS = {
    "crm": "crm/crm_validation_summary.json",
    "prescription": "prescription/prescription_validation_summary.json",
    "sandbox": "sandbox/sandbox_validation_summary.json",
    "territory": "territory/territory_validation_summary.json",
    "radar": "radar/radar_validation_summary.json",
    "builder": "builder/builder_validation_summary.json",
}


def list_execution_modes() -> list[str]:
    return list(_MODE_DEFINITIONS)


def get_execution_mode_definition(mode: str) -> ExecutionModeDefinition | None:
    return _MODE_DEFINITIONS.get(mode)


def get_execution_mode_label(mode: str) -> str:
    definition = get_execution_mode_definition(mode)
    return definition.label if definition else mode


def get_execution_mode_description(mode: str) -> str:
    definition = get_execution_mode_definition(mode)
    return definition.description if definition else ""


def get_execution_mode_requirements(mode: str) -> str:
    definition = get_execution_mode_definition(mode)
    return definition.requirements if definition else ""


def get_execution_mode_modules(mode: str) -> list[str]:
    definition = get_execution_mode_definition(mode)
    if definition:
        return list(definition.modules)
    return ["crm", "sandbox"]


def get_mode_required_uploads(mode: str) -> list[str]:
    definition = get_execution_mode_definition(mode)
    if definition:
        return list(definition.required_uploads)
    return []


def get_mode_pipeline_steps(mode: str) -> list[ExecutionStepDefinition]:
    definition = get_execution_mode_definition(mode)
    if definition is None:
        return []
    return list(definition.step_builder())


def get_summary_relative_path(module: str) -> str | None:
    return _SUMMARY_RELATIVE_PATHS.get(module)


def clear_execution_step_registry_cache() -> None:
    _get_step_registry.cache_clear()


def clear_execution_runtime_modules() -> None:
    clear_execution_step_registry_cache()
    module_names = [
        "scripts.normalize_crm_source",
        "scripts.normalize_prescription_source",
        "scripts.normalize_sandbox_source",
        "scripts.normalize_territory_source",
        "scripts.validate_builder_with_ops",
        "scripts.validate_crm_with_ops",
        "scripts.validate_prescription_with_ops",
        "scripts.validate_radar_with_ops",
        "scripts.validate_sandbox_with_ops",
        "scripts.validate_territory_with_ops",
    ]
    for name in module_names:
        sys.modules.pop(name, None)
