from __future__ import annotations

import sys


SCRIPT_RUNTIME_MODULE_NAMES = [
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
    "modules.kpi",
    "modules.kpi.prescription_engine",
    "modules.prescription.builder_payload",
    "modules.prescription.service",
    "modules.builder.service",
]


def clear_sales_data_os_script_runtime() -> None:
    """
    Clear cached step registry and script modules used by pipeline execution.

    This helper belongs to runtime preparation, not to the validation mode
    definition file.
    """
    from modules.validation.workflow import execution_registry

    execution_registry._get_step_registry.cache_clear()
    for name in SCRIPT_RUNTIME_MODULE_NAMES:
        sys.modules.pop(name, None)
