import json
from pathlib import Path
import shutil
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.asset_versions import (
    BUILDER_CONTRACT_VERSION,
    BUILDER_INPUT_SCHEMA_VERSION,
    BUILDER_PAYLOAD_VERSION,
    CRM_BUILDER_PAYLOAD_VERSION,
    CRM_RESULT_SCHEMA_VERSION,
    HTML_BUILDER_RESULT_SCHEMA_VERSION,
    PRESCRIPTION_RESULT_SCHEMA_VERSION,
    SANDBOX_INPUT_SCHEMA_VERSION,
    SANDBOX_RESULT_SCHEMA_VERSION,
    SANDBOX_TEMPLATE_PAYLOAD_VERSION,
    TERRITORY_RESULT_SCHEMA_VERSION,
)
from modules.builder.schemas import HtmlBuilderResultAsset
from modules.builder.service import build_crm_template_input, build_template_payload
from modules.sandbox.schemas import (
    AnalysisSummary,
    DashboardPayload,
    DomainQualitySummary,
    JoinQualitySummary,
    SandboxInputStandard,
)
from modules.territory.schemas import TerritoryCoverageSummary, TerritoryOptimizationSummary
from modules.territory.templates import TerritoryMapContract
from result_assets.crm_result_asset import CrmResultAsset
from result_assets.prescription_result_asset import PrescriptionResultAsset
from result_assets.sandbox_result_asset import SandboxResultAsset
from result_assets.territory_result_asset import TerritoryResultAsset


def _make_temp_dir() -> Path:
    temp_dir = ROOT / "tests" / "_tmp_priority2" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_core_assets_and_standards_expose_versions():
    sandbox_input = SandboxInputStandard(
        scenario="demo",
        metric_months=["202501"],
    )
    sandbox_asset = SandboxResultAsset(
        scenario="demo",
        metric_months=["202501"],
        analysis_summary=AnalysisSummary(
            total_hospitals=1,
            total_months=1,
            total_sales_amount=0.0,
            total_target_amount=0.0,
            total_visits=0,
            fully_joined_hospitals=0,
        ),
        domain_quality=DomainQualitySummary(),
        join_quality=JoinQualitySummary(),
    )
    territory_asset = TerritoryResultAsset(
        map_contract=TerritoryMapContract.get_standard_template(),
        coverage_summary=TerritoryCoverageSummary(
            total_regions=0,
            covered_regions=0,
            coverage_rate=0.0,
            total_hospitals=0,
            mapped_hospitals=0,
            gap_hospitals=0,
        ),
        optimization_summary=TerritoryOptimizationSummary(
            total_reps=0,
            avg_hospitals_per_rep=0.0,
        ),
    )

    assert CrmResultAsset().schema_version == CRM_RESULT_SCHEMA_VERSION
    assert PrescriptionResultAsset().schema_version == PRESCRIPTION_RESULT_SCHEMA_VERSION
    assert sandbox_input.schema_version == SANDBOX_INPUT_SCHEMA_VERSION
    assert sandbox_asset.schema_version == SANDBOX_RESULT_SCHEMA_VERSION
    assert territory_asset.schema_version == TERRITORY_RESULT_SCHEMA_VERSION
    assert DashboardPayload().payload_version == SANDBOX_TEMPLATE_PAYLOAD_VERSION
    assert DashboardPayload().builder_contract_version == BUILDER_CONTRACT_VERSION
    assert HtmlBuilderResultAsset().schema_version == HTML_BUILDER_RESULT_SCHEMA_VERSION


def test_builder_standards_record_source_versions():
    temp_dir = _make_temp_dir()
    try:
        payload_path = temp_dir / "crm_builder_payload.json"
        payload_path.write_text(
            json.dumps(
                {
                    "payload_version": CRM_BUILDER_PAYLOAD_VERSION,
                    "builder_contract_version": BUILDER_CONTRACT_VERSION,
                    "source_asset_schema_version": CRM_RESULT_SCHEMA_VERSION,
                    "overview": {"crm_activity_count": 12},
                    "activity_context": {"unique_reps": 2, "unique_hospitals": 5},
                    "mapping_quality": {"hospital_mapping_rate": 0.975},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        builder_input = build_crm_template_input(
            template_path="templates/crm_analysis_template.html",
            builder_payload_path=str(payload_path),
            source_asset_path="data/ops_validation/demo/crm/crm_result_asset.json",
        )
        builder_payload = build_template_payload(builder_input)

        assert builder_input.schema_version == BUILDER_INPUT_SCHEMA_VERSION
        assert builder_input.builder_contract_version == BUILDER_CONTRACT_VERSION
        assert builder_input.source_versions["crm"]["schema_version"] == CRM_RESULT_SCHEMA_VERSION
        assert builder_input.source_versions["crm"]["payload_version"] == CRM_BUILDER_PAYLOAD_VERSION
        assert builder_payload.payload_version == BUILDER_PAYLOAD_VERSION
        assert builder_payload.builder_contract_version == BUILDER_CONTRACT_VERSION
        assert builder_payload.source_versions["crm"]["payload_version"] == CRM_BUILDER_PAYLOAD_VERSION
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
