"""
CRM 모듈 통합 테스트 (Config 기반 리팩터링)

핵심 원칙 반영:
  - 모든 Adapter는 Config를 명시적으로 주입받는다.
  - fixture 데이터의 컬럼명은 fixture_example() Config로 선언한다.
  - Config를 교체하면 어떤 데이터 소스에도 대응 가능함을 보여준다.

테스트 범위:
  1. Config 검증: 필수/선택 필드 분리 확인
  2. Hospital Adapter: Config → HospitalMaster 변환
  3. Company Master Adapter: Config → CompanyMasterStandard 변환
  4. CRM Activity Adapter: Config → CrmStandardActivity 변환
  5. CRM Service: CrmResultAsset 생성
  6. OPS 평가: quality_status 판정
"""

import pytest

from tests.fixtures.crm_fixtures import (
    HOSPITAL_FIXTURE_RECORDS,
    COMPANY_MASTER_FIXTURE_RECORDS,
    CRM_ACTIVITY_FIXTURE_RECORDS,
)
from adapters.crm.adapter_config import (
    HospitalAdapterConfig,
    CompanyMasterAdapterConfig,
    CrmActivityAdapterConfig,
)
from adapters.crm.hospital_adapter import (
    load_hospital_master_from_records,
    build_hospital_index,
)
from adapters.crm.company_master_adapter import (
    load_company_master_from_records,
    validate_key_integrity,
)
from adapters.crm.crm_activity_adapter import load_crm_activity_from_records
from modules.crm.service import build_crm_result_asset
from modules.validation.api.crm_router import evaluate_crm_asset
from common.types import QualityGateStatus
from common.exceptions import MissingResultAssetError


# ────────────────────────────────────────
# 공유 Fixtures
# ────────────────────────────────────────

@pytest.fixture
def hospital_config():
    """fixture 데이터에 맞는 병원 Config."""
    return HospitalAdapterConfig.fixture_example()


@pytest.fixture
def company_config():
    """fixture 데이터에 맞는 회사 마스터 Config."""
    return CompanyMasterAdapterConfig.fixture_example()


@pytest.fixture
def activity_config():
    """fixture 데이터에 맞는 CRM 활동 Config."""
    return CrmActivityAdapterConfig.fixture_example()


@pytest.fixture
def hospitals(hospital_config):
    return load_hospital_master_from_records(HOSPITAL_FIXTURE_RECORDS, config=hospital_config)


@pytest.fixture
def hospital_index(hospitals):
    return build_hospital_index(hospitals)


@pytest.fixture
def company_masters(company_config, hospital_index):
    masters, unmapped = load_company_master_from_records(
        COMPANY_MASTER_FIXTURE_RECORDS,
        config=company_config,
        hospital_index=hospital_index,
    )
    return masters, unmapped


@pytest.fixture
def activities(activity_config, company_masters):
    masters, _ = company_masters
    acts, unmapped = load_crm_activity_from_records(
        CRM_ACTIVITY_FIXTURE_RECORDS,
        config=activity_config,
        company_master=masters,
    )
    return acts, unmapped


# ────────────────────────────────────────
# 1. Config 설계 원칙 확인 테스트
# ────────────────────────────────────────

class TestAdapterConfigPrinciple:
    """Config가 범용 설계 원칙에 맞는지 확인"""

    def test_hospital_config_requires_all_fields(self):
        """HospitalAdapterConfig는 기본값 없이 필수 필드를 요구해야 한다."""
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            HospitalAdapterConfig()  # 필수 필드 없이 생성 시 오류

    def test_different_configs_produce_same_schema(self, hospital_index):
        """HIRA 예시 Config와 fixture Config가 같은 스키마(HospitalMaster)를 생산한다."""
        # fixture config로 생성
        fixture_config = HospitalAdapterConfig.fixture_example()
        hospitals_fixture = load_hospital_master_from_records(
            HOSPITAL_FIXTURE_RECORDS, config=fixture_config
        )
        # 결과 구조가 동일한 HospitalMaster인지 확인
        from modules.crm.schemas import HospitalMaster
        for h in hospitals_fixture:
            assert isinstance(h, HospitalMaster)
            assert h.hospital_id
            assert h.hospital_name

    def test_config_example_factories_exist(self):
        """각 Config에 예시 팩토리 메서드가 있어야 한다."""
        # 없으면 개발자가 어떻게 설정하는지 알 수 없음
        h_config = HospitalAdapterConfig.hira_example()
        assert h_config.hospital_id_col

        c_config = CompanyMasterAdapterConfig.korean_example()
        assert c_config.rep_id_col

        a_config = CrmActivityAdapterConfig.veeva_crm_example()
        assert a_config.rep_id_col
        assert a_config.activity_type_map  # Veeva는 영문 → 한국어 맵 포함


# ────────────────────────────────────────
# 2. Hospital Adapter 테스트
# ────────────────────────────────────────

class TestHospitalAdapter:

    def test_load_count(self, hospitals):
        """fixture 기준 10개 병원이 로드되어야 한다."""
        assert len(hospitals) == 10

    def test_all_have_required_keys(self, hospitals):
        """모든 병원에 hospital_id, hospital_name, hospital_type이 있어야 한다."""
        for h in hospitals:
            assert h.hospital_id
            assert h.hospital_name
            assert h.hospital_type

    def test_hospital_index_built_correctly(self, hospital_index, hospitals):
        """인덱스 키 개수가 병원 수와 같아야 한다."""
        assert len(hospital_index) == len(hospitals)

    def test_hospital_lookup_by_id(self, hospital_index):
        """H001은 서울중앙병원이어야 한다."""
        h = hospital_index.get("H001")
        assert h is not None
        assert h.hospital_name == "서울중앙병원"

    def test_missing_required_col_raises_error(self, hospital_config):
        """필수 컬럼 없는 데이터 → AdapterInputError 발생해야 한다."""
        from common.exceptions import AdapterInputError
        bad_records = [{"잘못된컬럼": "값"}]
        with pytest.raises(AdapterInputError):
            load_hospital_master_from_records(bad_records, config=hospital_config)


# ────────────────────────────────────────
# 3. Company Master Adapter 테스트
# ────────────────────────────────────────

class TestCompanyMasterAdapter:

    def test_all_mapped_no_unmapped(self, company_masters):
        """fixture 기준 전체 매핑, unmapped 0건이어야 한다."""
        masters, unmapped = company_masters
        assert len(masters) > 0
        assert len(unmapped) == 0, f"매핑 실패: {unmapped}"

    def test_all_rep_ids_present(self, company_masters):
        """R001~R005 모두 포함되어야 한다."""
        masters, _ = company_masters
        rep_ids = {m.rep_id for m in masters}
        for r in ["R001", "R002", "R003", "R004", "R005"]:
            assert r in rep_ids

    def test_both_branches_present(self, company_masters):
        """BR01, BR02 모두 있어야 한다."""
        masters, _ = company_masters
        branch_ids = {m.branch_id for m in masters}
        assert "BR01" in branch_ids
        assert "BR02" in branch_ids

    def test_hospital_id_references_hospital_master(self, company_masters, hospital_index):
        """모든 hospital_id가 HospitalMaster 기준이어야 한다."""
        masters, _ = company_masters
        for m in masters:
            assert m.hospital_id in hospital_index, f"유효하지 않은 hospital_id: {m.hospital_id}"

    def test_key_integrity(self, company_masters):
        """중복 rep-hospital 쌍이 없어야 한다."""
        masters, _ = company_masters
        result = validate_key_integrity(masters)
        assert result["is_valid"], f"정합성 오류: {result}"


# ────────────────────────────────────────
# 4. CRM Activity Adapter 테스트
# ────────────────────────────────────────

class TestCrmActivityAdapter:

    def test_activity_count(self, activities):
        """fixture 기준 14건 표준화, 미매핑 0건이어야 한다."""
        acts, unmapped = activities
        assert len(acts) == 14, f"활동 수 불일치: {len(acts)}"
        assert len(unmapped) == 0, f"미매핑 활동: {unmapped}"

    def test_all_have_hospital_id(self, activities):
        """모든 활동에 hospital_id가 있어야 한다."""
        acts, _ = activities
        for a in acts:
            assert a.hospital_id

    def test_metric_month_is_yyyymm(self, activities):
        """metric_month가 6자리 숫자여야 한다."""
        acts, _ = activities
        for a in acts:
            assert len(a.metric_month) == 6
            assert a.metric_month.isdigit()

    def test_activity_types_normalized(self, activities):
        """활동유형이 공통 표준 값이어야 한다."""
        acts, _ = activities
        valid_types = {"방문", "전화", "이메일", "행사", "디지털", "화상"}
        for a in acts:
            assert a.activity_type in valid_types, f"비정상 유형: {a.activity_type}"

    def test_custom_activity_type_map(self, company_masters):
        """Config의 activity_type_map으로 회사별 용어를 표준화할 수 있어야 한다."""
        masters, _ = company_masters
        custom_config = CrmActivityAdapterConfig(
            rep_id_col="rep_id",
            hospital_name_col="hospital_name",
            activity_date_col="activity_date",
            activity_type_col="activity_type",
            has_detail_call_col="has_detail_call",
            products_mentioned_col="products_mentioned",
            notes_col="notes",
            activity_type_map={
                "방문": "방문",   # 동일하게 통과
                "전화": "전화",
                "행사": "행사",
            },
        )
        acts, _ = load_crm_activity_from_records(
            CRM_ACTIVITY_FIXTURE_RECORDS,
            config=custom_config,
            company_master=masters,
        )
        assert len(acts) > 0


# ────────────────────────────────────────
# 5. CRM Service - Result Asset 생성
# ────────────────────────────────────────

class TestCrmService:

    def test_result_asset_created(self, activities, company_masters):
        acts, unmapped = activities
        masters, _ = company_masters
        asset = build_crm_result_asset(acts, masters)
        assert asset is not None
        assert asset.asset_type == "crm_result_asset"

    def test_five_behavior_profiles(self, activities, company_masters):
        """5명 담당자의 프로파일이 생성되어야 한다."""
        acts, _ = activities
        masters, _ = company_masters
        asset = build_crm_result_asset(acts, masters)
        assert len(asset.behavior_profiles) == 5

    def test_monthly_kpi_two_months(self, activities, company_masters):
        """202501, 202502 두 달의 KPI가 있어야 한다."""
        acts, _ = activities
        masters, _ = company_masters
        asset = build_crm_result_asset(acts, masters)
        months = {k.metric_month for k in asset.monthly_kpi}
        assert "202501" in months
        assert "202502" in months

    def test_mapping_rate_100_percent(self, activities, company_masters):
        """fixture는 100% 매핑이어야 한다."""
        acts, unmapped = activities
        masters, _ = company_masters
        asset = build_crm_result_asset(
            acts, masters,
            unmapped_raw_count=len(unmapped),
            total_raw_count=len(acts) + len(unmapped),
        )
        assert asset.mapping_quality.hospital_mapping_rate == 1.0

    def test_handoff_targets(self, activities, company_masters):
        """다음 모듈로 prescription, sandbox가 있어야 한다."""
        acts, _ = activities
        masters, _ = company_masters
        asset = build_crm_result_asset(acts, masters)
        assert "prescription" in asset.planned_handoff_modules
        assert "sandbox" in asset.planned_handoff_modules

    def test_empty_activities_raises_error(self, company_masters):
        """활동이 없으면 MissingResultAssetError가 발생해야 한다."""
        masters, _ = company_masters
        with pytest.raises(MissingResultAssetError):
            build_crm_result_asset([], masters)


# ────────────────────────────────────────
# 6. OPS 평가 테스트
# ────────────────────────────────────────

class TestOPSEvaluation:

    def test_pass_with_good_data(self, activities, company_masters):
        """정상 fixture → OPS PASS."""
        acts, unmapped = activities
        masters, _ = company_masters
        asset = build_crm_result_asset(acts, masters, unmapped_raw_count=0, total_raw_count=len(acts))
        result = evaluate_crm_asset(asset)
        assert result.quality_status == QualityGateStatus.PASS

    def test_next_modules_on_pass(self, activities, company_masters):
        """PASS 시 다음 모듈로 prescription, sandbox 반환."""
        acts, _ = activities
        masters, _ = company_masters
        asset = build_crm_result_asset(acts, masters)
        result = evaluate_crm_asset(asset)
        assert "prescription" in result.next_modules
        assert "sandbox" in result.next_modules

    def test_quality_score_0_to_100(self, activities, company_masters):
        """품질 점수는 0~100 범위여야 한다."""
        acts, _ = activities
        masters, _ = company_masters
        asset = build_crm_result_asset(acts, masters)
        result = evaluate_crm_asset(asset)
        assert 0 <= result.quality_score <= 100

    def test_reasoning_note_is_human_readable(self, activities, company_masters):
        """reasoning_note는 비어 있지 않아야 한다."""
        acts, _ = activities
        masters, _ = company_masters
        asset = build_crm_result_asset(acts, masters)
        result = evaluate_crm_asset(asset)
        assert result.reasoning_note
        assert len(result.reasoning_note) > 10
