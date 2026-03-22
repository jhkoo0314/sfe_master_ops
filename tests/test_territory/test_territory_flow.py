"""
Territory 통합 테스트

검증 항목:
  - 템플릿 SlotKey가 자동으로 마커 색상/크기/툴팁을 결정하는지
  - Sandbox 데이터에서 담당자 동선이 생성되는지
  - 권역 히트맵 집계가 올바른지
  - 갭 감지 (방문 0 병원) 동작하는지
  - OPS 평가가 PASS/WARN/FAIL 올바르게 내리는지
"""

import pytest
from modules.sandbox.schemas import HospitalAnalysisRecord
from modules.territory.schemas import SIDO_CENTROIDS
from modules.territory.templates import TerritoryMapContract
from modules.territory.service import build_territory_result_asset
from modules.validation.api.territory_router import evaluate_territory_asset
from common.types import QualityGateStatus
from common.exceptions import MissingResultAssetError
from tests.fixtures.territory_fixtures import (
    HOSPITAL_REGION_MAP, HOSPITAL_ANALYSIS_RECORDS,
)


# ────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────

@pytest.fixture
def hospital_records():
    return [HospitalAnalysisRecord(**r) for r in HOSPITAL_ANALYSIS_RECORDS]


@pytest.fixture
def standard_contract():
    return TerritoryMapContract.get_standard_template()


@pytest.fixture
def territory_asset(hospital_records, standard_contract):
    return build_territory_result_asset(
        hospital_records=hospital_records,
        contract=standard_contract,
        hospital_region_map=HOSPITAL_REGION_MAP,
    )


# ────────────────────────────────────────
# 1. 템플릿 SlotKey 자동 주입 테스트
# ────────────────────────────────────────

class TestTemplateSlotInjection:

    def test_standard_template_created(self, standard_contract):
        assert standard_contract.marker_style.color_key == "attainment_color"
        assert standard_contract.marker_style.size_key == "sales_size"
        assert standard_contract.marker_style.tooltip_key == "full_summary"

    def test_activity_template_different_keys(self):
        tmpl = TerritoryMapContract.get_activity_focus_template()
        assert tmpl.marker_style.color_key == "visit_color"
        assert tmpl.marker_style.size_key == "visit_size"

    def test_markers_use_correct_color_key(self, territory_asset):
        """달성률 기반 색상: ≥1.0 green, ≥0.8 yellow, >0 red"""
        # H004: attainment=0.9 → yellow
        h4 = next(m for m in territory_asset.markers if m.hospital_id == "H004")
        assert h4.marker_color == "yellow"

    def test_gap_hospital_marker_color_gray(self, territory_asset):
        """방문 0, 목표 없는 H006 → gray"""
        h6 = next(m for m in territory_asset.markers if m.hospital_id == "H006")
        assert h6.marker_color == "gray"

    def test_tooltip_full_summary_format(self, territory_asset):
        """full_summary 툴팁에 매출, 달성률, 방문 포함"""
        h1 = next(m for m in territory_asset.markers if m.hospital_id == "H001")
        assert "매출" in h1.tooltip
        assert "달성률" in h1.tooltip
        assert "방문" in h1.tooltip


# ────────────────────────────────────────
# 2. 좌표 자동 결정 테스트
# ────────────────────────────────────────

class TestGeoCoord:

    def test_seoul_hospitals_get_seoul_coord(self, territory_asset):
        seoul_markers = [m for m in territory_asset.markers if m.region_key == "서울"]
        for m in seoul_markers:
            assert abs(m.coord.lat - SIDO_CENTROIDS["서울"].lat) < 0.001

    def test_unknown_region_gets_default_coord(self):
        """매핑 없는 병원은 한국 중심 좌표"""
        from modules.territory.service import _resolve_coord
        coord = _resolve_coord("알수없음")
        assert abs(coord.lat - 36.5) < 0.01


# ────────────────────────────────────────
# 3. 담당자 동선 테스트
# ────────────────────────────────────────

class TestRepRoute:

    def test_routes_created_per_rep(self, territory_asset):
        rep_ids = {r.rep_id for r in territory_asset.routes}
        assert "REP001" in rep_ids
        assert "REP002" in rep_ids
        assert "REP003" in rep_ids

    def test_h006_no_route(self, territory_asset):
        """rep_id=None인 H006은 어떤 동선에도 없어야 함"""
        all_hosp_in_routes = {
            p.hospital_id
            for r in territory_asset.routes
            for p in r.route_points
        }
        assert "H006" not in all_hosp_in_routes

    def test_optimal_route_sorted_by_visits(self, territory_asset):
        """optimal_route → 방문 수 내림차순 정렬"""
        rep1_route = next(r for r in territory_asset.routes if r.rep_id == "REP001")
        visits = [p.visit_count for p in rep1_route.route_points]
        assert visits == sorted(visits, reverse=True)

    def test_coverage_score_calculated(self, territory_asset):
        for route in territory_asset.routes:
            assert 0.0 <= route.coverage_score <= 1.0


# ────────────────────────────────────────
# 4. 권역 집계 테스트
# ────────────────────────────────────────

class TestRegionZone:

    def test_region_zones_created(self, territory_asset):
        regions = {z.region_key for z in territory_asset.region_zones}
        assert "서울" in regions
        assert "부산" in regions
        assert "인천" in regions

    def test_seoul_zone_aggregation(self, territory_asset):
        seoul = next(z for z in territory_asset.region_zones if z.region_key == "서울")
        assert seoul.hospital_count == 2
        assert seoul.total_sales == pytest.approx(7300000 + 2900000)

    def test_heat_intensity_range(self, territory_asset):
        for z in territory_asset.region_zones:
            assert 0.0 <= z.heat_intensity <= 1.0


# ────────────────────────────────────────
# 5. 갭 감지 테스트
# ────────────────────────────────────────

class TestTerritoryGap:

    def test_h006_detected_as_gap(self, territory_asset):
        gap_ids = {g.hospital_id for g in territory_asset.gaps}
        assert "H006" in gap_ids

    def test_gap_reason_zero_visits(self, territory_asset):
        h6_gap = next(g for g in territory_asset.gaps if g.hospital_id == "H006")
        assert h6_gap.gap_reason == "zero_visits"


# ────────────────────────────────────────
# 6. OPS 평가 테스트
# ────────────────────────────────────────

class TestOPSTerritoryEvaluation:

    def test_pass_or_warn_with_fixture(self, territory_asset):
        result = evaluate_territory_asset(territory_asset)
        assert result.quality_status in [QualityGateStatus.PASS, QualityGateStatus.WARN]

    def test_builder_in_next_modules_when_not_fail(self, territory_asset):
        result = evaluate_territory_asset(territory_asset)
        if result.quality_status != QualityGateStatus.FAIL:
            assert "builder" in result.next_modules

    def test_quality_score_range(self, territory_asset):
        result = evaluate_territory_asset(territory_asset)
        assert 0 <= result.quality_score <= 100

    def test_fail_on_empty_records(self):
        with pytest.raises(MissingResultAssetError):
            build_territory_result_asset(hospital_records=[])
