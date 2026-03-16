from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


BlockStatus = Literal["supported", "derived", "unsupported"]
BlockProducer = Literal["official_engine", "sandbox_service", "builder_transform", "unsupported"]


@dataclass(frozen=True)
class SandboxBlockSpec:
    """Sandbox block contract registry item for staged block-based refactor."""

    block_id: str
    label: str
    source_path: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()
    producer: BlockProducer = "sandbox_service"
    supported_slots: tuple[str, ...] = ()
    status: BlockStatus = "supported"
    reusable_by_agent: bool = True


BLOCK_REGISTRY: tuple[SandboxBlockSpec, ...] = (
    SandboxBlockSpec(
        block_id="official_kpi_6",
        label="Official KPI 6",
        source_path="dashboard_payload.template_payload.official_kpi_6",
        required_fields=(
            "monthly_sales",
            "monthly_target",
            "monthly_attainment_rate",
            "quarterly_sales",
            "quarterly_target",
            "annual_attainment_rate",
            "metric_version",
        ),
        optional_fields=("reference_month", "reference_quarter", "reference_year"),
        producer="official_engine",
        supported_slots=("header_kpi_slot", "main_trend_slot"),
        status="supported",
    ),
    SandboxBlockSpec(
        block_id="total_summary",
        label="Total Summary",
        source_path="dashboard_payload.template_payload.total",
        required_fields=("achieve", "avg", "monthly_actual", "monthly_target", "analysis"),
        producer="sandbox_service",
        supported_slots=("header_kpi_slot", "main_trend_slot", "capability_radar_slot", "branch_compare_slot"),
        status="supported",
    ),
    SandboxBlockSpec(
        block_id="total_trend",
        label="Total Trend",
        source_path="dashboard_payload.template_payload.total.[monthly_actual,monthly_target]",
        required_fields=("monthly_actual", "monthly_target"),
        producer="sandbox_service",
        supported_slots=("main_trend_slot",),
        status="supported",
    ),
    SandboxBlockSpec(
        block_id="branch_summary",
        label="Branch Summary",
        source_path="dashboard_payload.template_payload.branches.{branch} | sandbox_template_payload_assets/*.js",
        required_fields=("members", "avg", "monthly_actual", "monthly_target", "analysis", "achieve"),
        optional_fields=("prod_analysis",),
        producer="builder_transform",
        supported_slots=("main_trend_slot", "capability_radar_slot", "branch_compare_slot", "product_analysis_slot"),
        status="supported",
    ),
    SandboxBlockSpec(
        block_id="branch_member_summary",
        label="Branch Member Summary",
        source_path="dashboard_payload.template_payload.branches.{branch}.members[]",
        required_fields=("rep_id", "성명", "지점순위", "monthly_actual", "monthly_target"),
        optional_fields=("coach_scenario", "coach_action"),
        producer="builder_transform",
        supported_slots=("member_rank_slot",),
        status="supported",
    ),
    SandboxBlockSpec(
        block_id="member_performance",
        label="Member Performance",
        source_path="dashboard_payload.template_payload.branches.{branch}.members[]",
        required_fields=("HIR", "RTR", "BCR", "PHR", "PI", "FGR", "efficiency", "sustainability", "gini"),
        optional_fields=("shap", "activity_counts", "coach_scenario", "coach_action"),
        producer="sandbox_service",
        supported_slots=("member_rank_slot", "capability_radar_slot", "product_analysis_slot", "insight_slot"),
        status="supported",
    ),
    SandboxBlockSpec(
        block_id="product_analysis",
        label="Product Analysis",
        source_path="dashboard_payload.template_payload.[products,total_prod_analysis] + members[].prod_*",
        required_fields=("products", "total_prod_analysis"),
        optional_fields=("prod_matrix", "prod_analysis"),
        producer="sandbox_service",
        supported_slots=("product_analysis_slot", "main_trend_slot"),
        status="supported",
    ),
    SandboxBlockSpec(
        block_id="activity_analysis",
        label="Activity Analysis",
        source_path="dashboard_payload.template_payload.*.analysis + members[].activity_counts",
        required_fields=("analysis.importance", "analysis.correlation", "analysis.adj_correlation"),
        optional_fields=("activity_counts", "shap", "analysis.ccf"),
        producer="sandbox_service",
        supported_slots=("branch_compare_slot", "capability_radar_slot"),
        status="supported",
    ),
    SandboxBlockSpec(
        block_id="data_health",
        label="Data Health",
        source_path="dashboard_payload.template_payload.data_health",
        required_fields=("integrity_score", "mapped_fields", "operational_notes"),
        optional_fields=("missing_fields",),
        producer="sandbox_service",
        supported_slots=("data_health_slot", "header_kpi_slot"),
        status="supported",
    ),
    SandboxBlockSpec(
        block_id="missing_data",
        label="Missing Data",
        source_path="dashboard_payload.template_payload.missing_data",
        required_fields=("items",),
        producer="sandbox_service",
        supported_slots=("data_health_slot",),
        status="supported",
    ),
    SandboxBlockSpec(
        block_id="executive_insight",
        label="Executive Insight",
        source_path="dashboard_payload.insight_messages",
        required_fields=("messages",),
        producer="sandbox_service",
        supported_slots=("insight_slot",),
        status="derived",
    ),
    SandboxBlockSpec(
        block_id="template_runtime_manifest",
        label="Template Runtime Manifest",
        source_path="dashboard_payload.template_payload.[data_mode,asset_base,branch_asset_manifest,branch_index,branch_asset_counts]",
        required_fields=("data_mode", "branch_asset_manifest", "branch_index"),
        optional_fields=("asset_base", "branch_asset_counts", "branches"),
        producer="builder_transform",
        supported_slots=("runtime_manifest_slot",),
        status="supported",
    ),
)


def get_block_spec(block_id: str) -> SandboxBlockSpec | None:
    for spec in BLOCK_REGISTRY:
        if spec.block_id == block_id:
            return spec
    return None


def list_block_specs(status: BlockStatus | None = None) -> list[SandboxBlockSpec]:
    if status is None:
        return list(BLOCK_REGISTRY)
    return [spec for spec in BLOCK_REGISTRY if spec.status == status]
