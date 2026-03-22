from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RawGenerationConfig:
    company_key: str
    company_name: str
    template_type: str
    start_month: str
    end_month: str
    branch_count: int
    clinic_rep_count: int
    hospital_rep_count: int
    portfolio_source: str
    output_mode: str


_CONFIGS: dict[str, RawGenerationConfig] = {
    "daon_pharma": RawGenerationConfig(
        company_key="daon_pharma",
        company_name="다온제약",
        template_type="daon_like",
        start_month="2025-01",
        end_month="2025-12",
        branch_count=10,
        clinic_rep_count=75,
        hospital_rep_count=33,
        portfolio_source="hangyeol_portfolio",
        output_mode="merged_only",
    ),
    "hangyeol_pharma": RawGenerationConfig(
        company_key="hangyeol_pharma",
        company_name="한결제약",
        template_type="hangyeol_like",
        start_month="2026-01",
        end_month="2026-06",
        branch_count=10,
        clinic_rep_count=80,
        hospital_rep_count=45,
        portfolio_source="hangyeol_portfolio",
        output_mode="merged_only",
    ),
    "monthly_merge_pharma": RawGenerationConfig(
        company_key="monthly_merge_pharma",
        company_name="월별검증제약",
        template_type="daon_like",
        start_month="2025-01",
        end_month="2025-06",
        branch_count=10,
        clinic_rep_count=50,
        hospital_rep_count=25,
        portfolio_source="hangyeol_portfolio",
        output_mode="monthly_and_merged",
    ),
    "tera_pharma": RawGenerationConfig(
        company_key="tera_pharma",
        company_name="테라제약",
        template_type="daon_like",
        start_month="2025-01",
        end_month="2025-12",
        branch_count=6,
        clinic_rep_count=30,
        hospital_rep_count=30,
        portfolio_source="hangyeol_portfolio",
        output_mode="merged_only",
    ),
}


def get_raw_generation_config(company_key: str) -> RawGenerationConfig | None:
    return _CONFIGS.get(company_key)


def list_raw_generation_configs() -> list[RawGenerationConfig]:
    return list(_CONFIGS.values())


__all__ = [
    "RawGenerationConfig",
    "get_raw_generation_config",
    "list_raw_generation_configs",
]
