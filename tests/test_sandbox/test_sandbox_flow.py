"""
Sandbox 통합 테스트

OPS 철학 검증:
  - Config 기반 Adapter가 어떤 컬럼명에도 대응하는지
  - hospital_id 기준 도메인 조인이 정확한지
  - 달성률/조인율 계산이 올바른지
  - OPS 평가가 데이터 품질에 따라 PASS/WARN/FAIL을 정확히 내리는지
  - Territory/Builder handoff 조건이 올바르게 판단되는지
"""

import pytest

from tests.fixtures.sandbox_fixtures import (
    CRM_DOMAIN_RECORDS, SALES_RECORDS, TARGET_RECORDS,
)
from adapters.sandbox.adapter_config import SalesAdapterConfig, TargetAdapterConfig
from adapters.sandbox.domain_adapter import load_sales_from_records, load_target_from_records
from modules.sandbox.schemas import (
    SandboxInputStandard, CrmDomainRecord,
)
from modules.sandbox.service import build_sandbox_result_asset
from modules.validation.api.sandbox_router import evaluate_sandbox_asset
from common.types import QualityGateStatus
from common.exceptions import MissingResultAssetError


# ────────────────────────────────────────
# 공유 Fixtures
# ────────────────────────────────────────

@pytest.fixture
def sales_config():
    return SalesAdapterConfig.fixture_example()


@pytest.fixture
def target_config():
    return TargetAdapterConfig.fixture_example()


@pytest.fixture
def sales_records(sales_config):
    records, failed = load_sales_from_records(SALES_RECORDS, config=sales_config)
    return records, failed


@pytest.fixture
def target_records(target_config):
    records, failed = load_target_from_records(TARGET_RECORDS, config=target_config)
    return records, failed


@pytest.fixture
def crm_records():
    return [CrmDomainRecord(**r) for r in CRM_DOMAIN_RECORDS]


@pytest.fixture
def sandbox_input(crm_records, sales_records, target_records):
    sales, _ = sales_records
    targets, _ = target_records
    return SandboxInputStandard(
        scenario="crm_sales_target",
        metric_months=["202501", "202502"],
        crm_records=crm_records,
        sales_records=sales,
        target_records=targets,
    )


@pytest.fixture
def sandbox_asset(sandbox_input):
    return build_sandbox_result_asset(sandbox_input)


# ────────────────────────────────────────
# 1. Sales Adapter 테스트
# ────────────────────────────────────────

class TestSalesAdapter:

    def test_all_records_converted(self, sales_records):
        records, failed = sales_records
        assert len(records) + len(failed) == len(SALES_RECORDS)

    def test_hospital_ids_present(self, sales_records):
        records, _ = sales_records
        for r in records:
            assert r.hospital_id, "hospital_id가 비어있음"

    def test_metric_month_format(self, sales_records):
        records, _ = sales_records
        for r in records:
            assert len(r.metric_month) == 6 and r.metric_month.isdigit()

    def test_config_required_fields(self):
        """Config 필수 필드 없으면 오류."""
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            SalesAdapterConfig()  # amount_col, rep_id_col 없음

    def test_column_mapping_flexibility(self):
        """다른 컬럼명으로도 동일한 결과."""
        custom_config = SalesAdapterConfig(
            hospital_id_col="hosp_id",    # 다른 컬럼명
            rep_id_col="sales_rep",
            metric_month_col="month",
            amount_col="revenue",
        )
        custom_records = [
            {"hosp_id": "H001", "sales_rep": "REP001", "month": "202501",
             "revenue": 1000000.0}
        ]
        results, failed = load_sales_from_records(custom_records, config=custom_config)
        assert len(results) == 1
        assert results[0].hospital_id == "H001"
        assert results[0].sales_amount == 1000000.0


# ────────────────────────────────────────
# 2. Target Adapter 테스트
# ────────────────────────────────────────

class TestTargetAdapter:

    def test_target_records_converted(self, target_records):
        records, failed = target_records
        assert len(records) > 0

    def test_rep_ids_present(self, target_records):
        records, _ = target_records
        for r in records:
            assert r.rep_id

    def test_target_amounts_positive(self, target_records):
        records, _ = target_records
        for r in records:
            assert r.target_amount > 0


# ────────────────────────────────────────
# 3. SandboxInputStandard 테스트
# ────────────────────────────────────────

class TestSandboxInput:

    def test_has_all_domains(self, sandbox_input):
        assert sandbox_input.has_crm
        assert sandbox_input.has_sales
        assert sandbox_input.has_target

    def test_unique_hospitals(self, sandbox_input):
        """CRM + Sales에서 고유 병원 집합이 생성되어야 한다."""
        hosps = sandbox_input.unique_hospital_ids
        assert "H001" in hosps
        assert "H003" in hosps

    def test_months_coverage(self, sandbox_input):
        months = {r.metric_month for r in sandbox_input.sales_records}
        assert "202501" in months
        assert "202502" in months


# ────────────────────────────────────────
# 4. Sandbox Service 테스트
# ────────────────────────────────────────

class TestSandboxService:

    def test_asset_created(self, sandbox_asset):
        assert sandbox_asset is not None
        assert sandbox_asset.asset_type == "sandbox_result_asset"

    def test_analysis_summary_populated(self, sandbox_asset):
        s = sandbox_asset.analysis_summary
        assert s.total_hospitals > 0
        assert s.total_sales_amount > 0
        assert s.total_months >= 1

    def test_sales_amount_correct(self, sandbox_asset):
        """fixture 총 매출이 집계되어야 한다."""
        expected_total = sum(r["sales_amount"] for r in SALES_RECORDS)
        assert sandbox_asset.analysis_summary.total_sales_amount == pytest.approx(expected_total, rel=0.01)

    def test_attainment_rate_calculated(self, sandbox_asset):
        """달성률이 계산된 병원이 있어야 한다."""
        rated = [r for r in sandbox_asset.hospital_records if r.attainment_rate is not None]
        assert len(rated) > 0

    def test_h001_attainment(self, sandbox_asset):
        """H001의 202501 달성률: 매출 4700000 / 목표 5500000 ≈ 0.8545."""
        h001 = next(
            (r for r in sandbox_asset.hospital_records
             if r.hospital_id == "H001" and r.metric_month == "202501"),
            None
        )
        assert h001 is not None
        assert h001.total_sales == pytest.approx(4700000.0)
        assert h001.total_target == pytest.approx(5500000.0)

    def test_join_quality_calculated(self, sandbox_asset):
        jq = sandbox_asset.join_quality
        assert jq.hospitals_with_crm_and_sales > 0
        assert 0.0 <= jq.crm_sales_join_rate <= 1.0

    def test_orphan_sales_detected(self, sandbox_asset):
        """H006은 CRM 없이 sales만 있는 orphan."""
        assert sandbox_asset.join_quality.orphan_sales_hospitals >= 1

    def test_handoff_candidates_exist(self, sandbox_asset):
        assert len(sandbox_asset.handoff_candidates) > 0

    def test_builder_always_eligible(self, sandbox_asset):
        """분석 결과가 있으면 builder는 항상 eligible."""
        builder = next(
            (h for h in sandbox_asset.handoff_candidates if h.module == "builder"),
            None
        )
        assert builder is not None
        assert builder.is_eligible

    def test_empty_input_raises_error(self):
        empty_input = SandboxInputStandard(
            scenario="crm_sales_target",
            metric_months=["202501"],
        )
        with pytest.raises(MissingResultAssetError):
            build_sandbox_result_asset(empty_input)


# ────────────────────────────────────────
# 5. OPS 평가 테스트
# ────────────────────────────────────────

class TestOPSSandboxEvaluation:

    def test_pass_or_warn_with_fixture(self, sandbox_asset):
        """fixture 데이터는 PASS 또는 WARN이어야 한다."""
        result = evaluate_sandbox_asset(sandbox_asset)
        assert result.quality_status in [QualityGateStatus.PASS, QualityGateStatus.WARN]

    def test_builder_in_next_modules(self, sandbox_asset):
        """분석 결과가 있으면 builder는 next_modules에 포함."""
        result = evaluate_sandbox_asset(sandbox_asset)
        if result.quality_status != QualityGateStatus.FAIL:
            assert "builder" in result.next_modules

    def test_quality_score_range(self, sandbox_asset):
        result = evaluate_sandbox_asset(sandbox_asset)
        assert 0 <= result.quality_score <= 100

    def test_reasoning_note_not_empty(self, sandbox_asset):
        result = evaluate_sandbox_asset(sandbox_asset)
        assert result.reasoning_note

    def test_fail_on_no_sales(self, crm_records):
        """매출 없으면 FAIL."""
        no_sales_input = SandboxInputStandard(
            scenario="crm_sales_target",
            metric_months=["202501"],
            crm_records=crm_records,
        )
        asset = build_sandbox_result_asset(no_sales_input)
        result = evaluate_sandbox_asset(asset)
        assert result.quality_status == QualityGateStatus.FAIL
