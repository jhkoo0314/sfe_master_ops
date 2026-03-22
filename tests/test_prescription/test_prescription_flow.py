"""
Prescription 모듈 통합 테스트

OPS 철학 검증:
  - 범용 ID 규칙(id_rules)이 결정론적으로 동작하는지
  - Config 기반 Adapter가 어떤 컬럼명에도 대응하는지
  - Flow Builder가 회사 데이터 없이 지역 기반 병원 매핑을 하는지
  - OPS가 흐름 완결률 기준으로 품질을 판단하는지
"""

import pytest

from tests.fixtures.crm_fixtures import HOSPITAL_FIXTURE_RECORDS
from tests.fixtures.prescription_fixtures import (
    PRESCRIPTION_MASTER_RECORDS,
    WHOLESALER_SHIPMENT_RECORDS,
)
from adapters.crm.adapter_config import HospitalAdapterConfig
from adapters.crm.hospital_adapter import load_hospital_master_from_records, build_hospital_index
from adapters.prescription.adapter_config import (
    CompanyPrescriptionAdapterConfig,
    PrescriptionMasterAdapterConfig,
)
from adapters.prescription.company_prescription_adapter import load_prescription_from_records
from modules.prescription.id_rules import (
    generate_pharmacy_id, generate_wholesaler_id, generate_lineage_key,
    generate_product_id, is_lineage_complete, is_valid_pharmacy_id, is_valid_wholesaler_id,
)
from modules.prescription.flow_builder import (
    build_hospital_region_index,
    build_prescription_standard_flow,
)
from modules.prescription.service import build_prescription_result_asset
from modules.validation.api.prescription_router import evaluate_prescription_asset
from common.types import QualityGateStatus
from common.exceptions import MissingResultAssetError


# ────────────────────────────────────────
# 공유 Fixtures
# ────────────────────────────────────────

@pytest.fixture
def hospitals():
    config = HospitalAdapterConfig.fixture_example()
    return load_hospital_master_from_records(HOSPITAL_FIXTURE_RECORDS, config=config)


@pytest.fixture
def hospital_index(hospitals):
    return build_hospital_index(hospitals)


@pytest.fixture
def region_indexes(hospitals):
    return build_hospital_region_index(hospitals)


@pytest.fixture
def prescription_config():
    return CompanyPrescriptionAdapterConfig.fixture_example()


@pytest.fixture
def standards(prescription_config):
    records, failed = load_prescription_from_records(
        WHOLESALER_SHIPMENT_RECORDS,
        config=prescription_config,
    )
    return records, failed


@pytest.fixture
def flows_and_gaps(standards, region_indexes):
    records, _ = standards
    sub_idx, reg_idx = region_indexes
    return build_prescription_standard_flow(records, sub_idx, reg_idx)


# ────────────────────────────────────────
# 1. 범용 ID 규칙 테스트 (핵심)
# ────────────────────────────────────────

class TestUniversalIdRules:
    """
    id_rules가 결정론적으로 동작하는지 확인.
    어떤 데이터에서 와도 동일한 입력 → 동일한 ID.
    """

    def test_pharmacy_id_is_deterministic(self):
        """같은 입력 → 항상 같은 pharmacy_id."""
        id1 = generate_pharmacy_id("종로중앙약국", "11010", "03001")
        id2 = generate_pharmacy_id("종로중앙약국", "11010", "03001")
        assert id1 == id2

    def test_pharmacy_id_differs_by_name(self):
        """다른 약국명 → 다른 pharmacy_id."""
        id1 = generate_pharmacy_id("종로중앙약국", "11010", "03001")
        id2 = generate_pharmacy_id("강남중앙약국", "11010", "03001")
        assert id1 != id2

    def test_pharmacy_id_normalizes_spaces(self):
        """공백 포함 vs 미포함 → 같은 ID (정규화)."""
        id1 = generate_pharmacy_id("종로 중앙 약국", "11010", "03001")
        id2 = generate_pharmacy_id("종로중앙약국", "11010", "03001")
        assert id1 == id2

    def test_pharmacy_id_starts_with_ph(self):
        """pharmacy_id는 PH_ 접두사로 시작해야 한다."""
        pid = generate_pharmacy_id("테스트약국", "11010", "03001")
        assert is_valid_pharmacy_id(pid)
        assert pid.startswith("PH_")

    def test_wholesaler_id_is_deterministic(self):
        """같은 입력 → 항상 같은 wholesaler_id."""
        id1 = generate_wholesaler_id("서울도매A", "11")
        id2 = generate_wholesaler_id("서울도매A", "11")
        assert id1 == id2

    def test_wholesaler_id_starts_with_ws(self):
        """wholesaler_id는 WS_ 접두사로 시작해야 한다."""
        wid = generate_wholesaler_id("서울도매A", "11")
        assert is_valid_wholesaler_id(wid)

    def test_lineage_key_with_hospital(self):
        """병원 연결된 lineage_key는 UNMAPPED가 없어야 한다."""
        lk = generate_lineage_key("WS_11_서울도매a", "PH_11010_종로중앙약국_030", "202501", "H001")
        assert is_lineage_complete(lk)
        assert "UNMAPPED" not in lk

    def test_lineage_key_without_hospital(self):
        """병원 없는 lineage_key는 UNMAPPED를 포함해야 한다."""
        lk = generate_lineage_key("WS_11_서울도매a", "PH_11010_종로중앙약국_030", "202501", None)
        assert not is_lineage_complete(lk)
        assert "UNMAPPED" in lk

    def test_product_id_uses_ingredient_code(self):
        """ingredient_code가 있으면 product_id에 포함되어야 한다."""
        pid = generate_product_id("제품A정", ingredient_code="A001")
        assert "A001" in pid


# ────────────────────────────────────────
# 2. Prescription Adapter 테스트
# ────────────────────────────────────────

class TestPrescriptionAdapter:

    def test_load_standard_from_records(self, standards):
        """fixture 10건 중 매핑 가능한 건수가 변환되어야 한다 (gap 1건 포함)."""
        records, failed = standards
        # 총 10건 중 '알수없는약국' 1건은 날짜 정상이지만 gap으로 처리됨
        assert len(records) + len(failed) == len(WHOLESALER_SHIPMENT_RECORDS)

    def test_all_pharmacy_ids_valid(self, standards):
        """모든 pharmacy_id가 PH_ 포맷이어야 한다."""
        records, _ = standards
        for r in records:
            assert is_valid_pharmacy_id(r.pharmacy_id), f"비정상 pharmacy_id: {r.pharmacy_id}"

    def test_all_wholesaler_ids_valid(self, standards):
        """모든 wholesaler_id가 WS_ 포맷이어야 한다."""
        records, _ = standards
        for r in records:
            assert is_valid_wholesaler_id(r.wholesaler_id)

    def test_metric_month_generated(self, standards):
        """모든 레코드에 YYYYMM 형식의 metric_month가 있어야 한다."""
        records, _ = standards
        for r in records:
            assert len(r.metric_month) == 6
            assert r.metric_month.isdigit()

    def test_config_required_fields(self):
        """Config 필수 필드 없으면 오류가 발생해야 한다."""
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            CompanyPrescriptionAdapterConfig()


# ────────────────────────────────────────
# 3. Flow Builder 테스트
# ────────────────────────────────────────

class TestFlowBuilder:

    def test_flows_generated(self, flows_and_gaps):
        """흐름 레코드가 생성되어야 한다."""
        flows, gaps = flows_and_gaps
        assert len(flows) > 0

    def test_complete_flows_exist(self, flows_and_gaps):
        """병원 연결된 완전한 흐름이 최소 1개 이상이어야 한다."""
        flows, _ = flows_and_gaps
        complete = [f for f in flows if f.is_complete]
        assert len(complete) > 0, "병원 연결된 흐름이 없습니다"

    def test_gap_records_for_unknown_region(self, flows_and_gaps):
        """알 수 없는 지역(99999)의 약국은 gap에 기록되어야 한다."""
        flows, gaps = flows_and_gaps
        incomplete = [f for f in flows if not f.is_complete]
        assert len(incomplete) > 0

    def test_lineage_key_format(self, flows_and_gaps):
        """모든 lineage_key가 __ 구분자로 4부분이어야 한다."""
        flows, _ = flows_and_gaps
        for f in flows:
            parts = f.lineage_key.split("__")
            assert len(parts) == 4, f"lineage_key 포맷 오류: {f.lineage_key}"

    def test_hospital_ids_from_crm_master(self, flows_and_gaps, hospital_index):
        """매핑된 hospital_id는 CRM hospital_master 기준이어야 한다."""
        flows, _ = flows_and_gaps
        for f in flows:
            if f.hospital_id:
                assert f.hospital_id in hospital_index, \
                    f"hospital_master에 없는 ID: {f.hospital_id}"


# ────────────────────────────────────────
# 4. Prescription Service 테스트
# ────────────────────────────────────────

class TestPrescriptionService:

    def test_result_asset_created(self, flows_and_gaps):
        flows, gaps = flows_and_gaps
        asset = build_prescription_result_asset(flows, gaps)
        assert asset is not None
        assert asset.asset_type == "prescription_result_asset"

    def test_lineage_summary_populated(self, flows_and_gaps):
        flows, gaps = flows_and_gaps
        asset = build_prescription_result_asset(flows, gaps)
        ls = asset.lineage_summary
        assert ls.total_flow_records > 0
        assert ls.unique_wholesalers > 0
        assert ls.unique_pharmacies > 0

    def test_gap_summary_reflects_unmapped(self, flows_and_gaps):
        flows, gaps = flows_and_gaps
        asset = build_prescription_result_asset(flows, gaps)
        # 알수없는약국 1건이 gap에 있어야 함
        assert asset.validation_gap_summary.total_gap_records > 0

    def test_months_captured(self, flows_and_gaps):
        flows, gaps = flows_and_gaps
        asset = build_prescription_result_asset(flows, gaps)
        months = asset.lineage_summary.metric_months
        assert "202501" in months
        assert "202502" in months

    def test_empty_flows_raises_error(self):
        with pytest.raises(MissingResultAssetError):
            build_prescription_result_asset([], [])


# ────────────────────────────────────────
# 5. OPS 평가 테스트
# ────────────────────────────────────────

class TestOPSPrescriptionEvaluation:

    def test_pass_or_warn_with_fixture(self, flows_and_gaps):
        """fixture 데이터는 PASS 또는 WARN이어야 한다 (FAIL은 안 됨)."""
        flows, gaps = flows_and_gaps
        asset = build_prescription_result_asset(flows, gaps)
        result = evaluate_prescription_asset(asset)
        assert result.quality_status in [QualityGateStatus.PASS, QualityGateStatus.WARN]

    def test_next_module_is_sandbox(self, flows_and_gaps):
        """연결 다음 모듈은 sandbox여야 한다."""
        flows, gaps = flows_and_gaps
        asset = build_prescription_result_asset(flows, gaps)
        result = evaluate_prescription_asset(asset)
        if result.quality_status != QualityGateStatus.FAIL:
            assert "sandbox" in result.next_modules

    def test_quality_score_range(self, flows_and_gaps):
        """품질 점수는 0~100 범위여야 한다."""
        flows, gaps = flows_and_gaps
        asset = build_prescription_result_asset(flows, gaps)
        result = evaluate_prescription_asset(asset)
        assert 0 <= result.quality_score <= 100

    def test_reasoning_note_not_empty(self, flows_and_gaps):
        flows, gaps = flows_and_gaps
        asset = build_prescription_result_asset(flows, gaps)
        result = evaluate_prescription_asset(asset)
        assert result.reasoning_note
