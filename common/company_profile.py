from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from adapters.crm.adapter_config import (
    CompanyMasterAdapterConfig,
    CrmActivityAdapterConfig,
    HospitalAdapterConfig,
)
from adapters.prescription.adapter_config import CompanyPrescriptionAdapterConfig
from adapters.sandbox.adapter_config import SalesAdapterConfig, TargetAdapterConfig
from adapters.territory.adapter_config import TerritoryActivityAdapterConfig


@dataclass(frozen=True)
class CompanyOpsProfile:
    company_key: str
    source_targets: dict[str, tuple[str, str]]
    raw_generator_module: str | None
    hospital_adapter_factory: Callable[[], HospitalAdapterConfig]
    company_master_adapter_factory: Callable[[], CompanyMasterAdapterConfig]
    crm_activity_adapter_factory: Callable[[], CrmActivityAdapterConfig]
    sales_adapter_factory: Callable[[], SalesAdapterConfig]
    target_adapter_factory: Callable[[], TargetAdapterConfig]
    prescription_adapter_factory: Callable[[], CompanyPrescriptionAdapterConfig]
    territory_activity_adapter_factory: Callable[[], TerritoryActivityAdapterConfig]

    def source_path(self, source_root: Path, source_key: str) -> Path:
        relative_path, _ = self.source_targets[source_key]
        return source_root / Path(relative_path)

    def resolved_source_targets(self, project_root: Path, company_key: str | None = None) -> dict[str, tuple[str, str]]:
        active_key = company_key or self.company_key
        source_root = project_root / "data" / "company_source" / active_key
        return {
            key: (str(source_root / Path(relative_path)), file_format)
            for key, (relative_path, file_format) in self.source_targets.items()
        }


_STANDARD_SOURCE_TARGETS = {
    "crm_activity": ("crm/crm_activity_raw.xlsx", "excel"),
    "crm_rep_master": ("company/company_assignment_raw.xlsx", "excel"),
    "crm_account_assignment": ("company/account_master.xlsx", "excel"),
    "crm_rules": ("company/crm_rules_raw.xlsx", "excel"),
    "sales": ("sales/sales_raw.xlsx", "excel"),
    "target": ("target/target_raw.xlsx", "excel"),
    "prescription": ("company/fact_ship_raw.csv", "csv"),
    "rep_master": ("company/rep_master.xlsx", "excel"),
}


def _build_standard_profile(
    company_key: str,
    raw_generator_module: str | None = None,
) -> CompanyOpsProfile:
    return CompanyOpsProfile(
        company_key=company_key,
        source_targets=dict(_STANDARD_SOURCE_TARGETS),
        raw_generator_module=raw_generator_module,
        hospital_adapter_factory=HospitalAdapterConfig.hangyeol_account_example,
        company_master_adapter_factory=CompanyMasterAdapterConfig.hangyeol_company_source_example,
        crm_activity_adapter_factory=CrmActivityAdapterConfig.hangyeol_crm_source_example,
        sales_adapter_factory=SalesAdapterConfig.hangyeol_sales_source_example,
        target_adapter_factory=TargetAdapterConfig.hangyeol_target_source_example,
        prescription_adapter_factory=CompanyPrescriptionAdapterConfig.hangyeol_fact_ship_example,
        territory_activity_adapter_factory=TerritoryActivityAdapterConfig.hangyeol_account_example,
    )


_PROFILE_MAP = {
    "hangyeol_pharma": _build_standard_profile(
        "hangyeol_pharma",
        raw_generator_module="scripts.raw_generators.generate_hangyeol_source_raw",
    ),
    "daon_pharma": _build_standard_profile(
        "daon_pharma",
        raw_generator_module="scripts.raw_generators.generate_daon_source_raw",
    ),
    "monthly_merge_pharma": _build_standard_profile(
        "monthly_merge_pharma",
        raw_generator_module="scripts.raw_generators.generate_monthly_merge_source_raw",
    ),
}


def get_company_ops_profile(company_key: str) -> CompanyOpsProfile:
    if company_key in _PROFILE_MAP:
        return _PROFILE_MAP[company_key]
    return _build_standard_profile(company_key)
