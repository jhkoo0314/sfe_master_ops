"""
Territory Service - Sandbox 데이터 → 지도 마커/동선/권역 자동 생성

핵심 흐름:
  1. SandboxResultAsset.hospital_records 수신
  2. TerritoryMapContract 템플릿의 SlotKey를 읽어
     마커 색상, 크기, 툴팁을 자동으로 결정
  3. 담당자(rep_id) 기준으로 동선(Route) 생성
  4. 권역(region_key) 기준으로 히트맵(RegionZone) 집계
  5. TerritoryResultAsset 반환

좌표:
  실제 DB에 위경도가 없는 경우 → SIDO_CENTROIDS 사용
  (Phase 7+ 에서 실좌표 보강 예정)
"""

from collections import defaultdict
from typing import Optional

from modules.territory.schemas import (
    MapMarker, RepRoute, RoutePoint, RegionZone,
    TerritoryGap, TerritoryCoverageSummary, TerritoryOptimizationSummary,
    GeoCoord, SIDO_CENTROIDS,
)
from modules.territory.templates import TerritoryMapContract
from modules.territory.builder_payload import build_territory_builder_payload as _build_territory_builder_payload
from modules.sandbox.schemas import HospitalAnalysisRecord
from result_assets.territory_result_asset import TerritoryResultAsset
from common.exceptions import MissingResultAssetError


# ────────────────────────────────────────
# 마커 스타일 결정 엔진 (SlotKey → 값)
# ────────────────────────────────────────

def _resolve_coord(region_key: str) -> GeoCoord:
    """region_key로 중심 좌표 반환. 없으면 한국 중심."""
    return SIDO_CENTROIDS.get(region_key, GeoCoord(lat=36.5, lng=127.8, source="default"))


def _resolve_marker_color(rec: HospitalAnalysisRecord, color_key: str) -> str:
    """color_key SlotKey에 따라 마커 색상 자동 결정."""
    if color_key == "attainment_color":
        rate = rec.attainment_rate or 0
        if rate >= 1.0:   return "green"
        if rate >= 0.8:   return "yellow"
        if rate > 0:      return "red"
        return "gray"
    elif color_key == "sales_color":
        if rec.total_sales >= 5_000_000: return "green"
        if rec.total_sales >= 2_000_000: return "yellow"
        if rec.total_sales > 0:          return "red"
        return "gray"
    elif color_key == "visit_color":
        if rec.total_visits >= 10: return "green"
        if rec.total_visits >= 5:  return "yellow"
        if rec.total_visits > 0:   return "red"
        return "gray"
    return "gray"


def _resolve_marker_size(rec: HospitalAnalysisRecord, size_key: str) -> str:
    """size_key SlotKey에 따라 마커 크기 자동 결정."""
    if size_key == "sales_size":
        if rec.total_sales >= 10_000_000: return "xl"
        if rec.total_sales >= 5_000_000:  return "lg"
        if rec.total_sales >= 1_000_000:  return "md"
        return "sm"
    elif size_key == "visit_size":
        if rec.total_visits >= 15: return "xl"
        if rec.total_visits >= 8:  return "lg"
        if rec.total_visits >= 3:  return "md"
        return "sm"
    return "md"


def _resolve_tooltip(rec: HospitalAnalysisRecord, tooltip_key: str) -> str:
    """tooltip_key SlotKey에 따라 툴팁 텍스트 자동 생성."""
    name = rec.hospital_id
    if tooltip_key == "full_summary":
        att = f"{(rec.attainment_rate or 0)*100:.0f}%" if rec.attainment_rate is not None else "목표없음"
        return (
            f"🏥 {name}\n"
            f"💰 매출: {rec.total_sales:,.0f}원\n"
            f"🎯 달성률: {att}\n"
            f"🚶 방문: {rec.total_visits}건"
        )
    elif tooltip_key == "sales_focus":
        att = f"{(rec.attainment_rate or 0)*100:.0f}%"
        return f"🏥 {name} | 💰 {rec.total_sales:,.0f}원 | 🎯 {att}"
    elif tooltip_key == "visit_focus":
        return f"🏥 {name} | 🚶 방문 {rec.total_visits}건"
    return name


def _resolve_route_order_key(route_key: str):
    """route_key SlotKey에 따라 정렬 함수 반환."""
    if route_key == "optimal_route":
        return lambda r: -r.visit_count
    elif route_key == "sales_route":
        return lambda r: -r.sales_amount
    return lambda r: r.order


# ────────────────────────────────────────
# 핵심 서비스 함수
# ────────────────────────────────────────

def build_territory_result_asset(
    hospital_records: list[HospitalAnalysisRecord],
    contract: Optional[TerritoryMapContract] = None,
    hospital_region_map: Optional[dict[str, str]] = None,
    hospital_coord_map: Optional[dict[str, GeoCoord]] = None,
    hospital_name_map: Optional[dict[str, str]] = None,
    hospital_sub_region_map: Optional[dict[str, str]] = None,
    hospital_rep_map: Optional[dict[str, str]] = None,
) -> "TerritoryResultAsset":
    """
    Sandbox의 HospitalAnalysisRecord를 받아 Territory 지도 자산을 생성한다.

    Args:
        hospital_records: Sandbox에서 넘어온 병원별 분석 레코드
        contract: 지도 템플릿 (None이면 표준 템플릿 자동 사용)
        hospital_region_map: hospital_id → region_key 매핑
                            (없으면 레코드에서 추론 불가 → "기타" 처리)

    Returns:
        TerritoryResultAsset
    """
    if not hospital_records:
        raise MissingResultAssetError("Territory 생성을 위한 병원 분석 레코드가 없습니다.")

    # 템플릿 자동 선택
    if contract is None:
        contract = TerritoryMapContract.get_standard_template()

    # 병원별로 월 데이터 집계 (같은 병원이 여러 월에 걸쳐 있음)
    hosp_agg: dict[str, dict] = {}
    for rec in hospital_records:
        h = rec.hospital_id
        if h not in hosp_agg:
            hosp_agg[h] = {
                "hospital_id": h,
                # 병원별 담당자 맵이 있으면 우선 사용하고, 없으면 Sandbox 분석 레코드의 rep_id를 그대로 쓴다.
                "rep_id": (hospital_rep_map or {}).get(h) or rec.rep_id,
                "total_sales": 0.0,
                "total_target": 0.0,
                "total_visits": 0,
                "attainment_rates": [],
            }
        hosp_agg[h]["total_sales"] += rec.total_sales
        hosp_agg[h]["total_target"] += rec.total_target
        hosp_agg[h]["total_visits"] += rec.total_visits
        if rec.attainment_rate is not None:
            hosp_agg[h]["attainment_rates"].append(rec.attainment_rate)

    # ── 1. 마커 생성 (SlotKey 자동 주입) ─────────────────
    markers: list[MapMarker] = []
    gaps: list[TerritoryGap] = []

    for h_id, agg in hosp_agg.items():
        region_key = (hospital_region_map or {}).get(h_id, "기타")
        coord = (hospital_coord_map or {}).get(h_id) or _resolve_coord(region_key)

        # 집계 레코드 임시 객체 (마커 스타일 결정용)
        mock_rec = HospitalAnalysisRecord(
            hospital_id=h_id,
            metric_month="all",
            total_sales=agg["total_sales"],
            total_target=agg["total_target"],
            total_visits=agg["total_visits"],
            attainment_rate=(
                sum(agg["attainment_rates"]) / len(agg["attainment_rates"])
                if agg["attainment_rates"] else None
            ),
            has_sales=agg["total_sales"] > 0,
            has_crm=agg["total_visits"] > 0,
        )

        color = _resolve_marker_color(mock_rec, contract.marker_style.color_key)
        size = _resolve_marker_size(mock_rec, contract.marker_style.size_key)
        tooltip = _resolve_tooltip(mock_rec, contract.marker_style.tooltip_key)

        markers.append(MapMarker(
            hospital_id=h_id,
            hospital_name=(hospital_name_map or {}).get(h_id),
            coord=coord,
            region_key=region_key,
            sub_region_key=(hospital_sub_region_map or {}).get(h_id),
            total_sales=agg["total_sales"],
            total_target=agg["total_target"],
            attainment_rate=mock_rec.attainment_rate,
            total_visits=agg["total_visits"],
            rep_id=agg["rep_id"],
            marker_color=color,
            marker_size=size,
            tooltip=tooltip,
        ))

        # 미커버 병원 감지
        if agg["total_visits"] == 0:
            gaps.append(TerritoryGap(
                region_key=region_key,
                hospital_id=h_id,
                gap_reason="zero_visits",
            ))

    # ── 2. 담당자 동선 생성 ───────────────────────────────
    rep_buckets: dict[str, list[MapMarker]] = defaultdict(list)
    for m in markers:
        if m.rep_id:
            rep_buckets[m.rep_id].append(m)

    sort_fn = _resolve_route_order_key(contract.route_style.route_key)
    routes: list[RepRoute] = []

    for rep_id, rep_markers in rep_buckets.items():
        # 동선 정렬 (SlotKey 기반)
        sorted_markers = sorted(
            rep_markers,
            key=lambda m: sort_fn(RoutePoint(
                order=0, hospital_id=m.hospital_id, coord=m.coord,
                visit_count=m.total_visits, sales_amount=m.total_sales,
            ))
        )

        route_points = [
            RoutePoint(
                order=i,
                hospital_id=m.hospital_id,
                coord=m.coord,
                visit_count=m.total_visits,
                sales_amount=m.total_sales,
            )
            for i, m in enumerate(sorted_markers)
        ]

        region_keys = [m.region_key for m in rep_markers if m.region_key != "기타"]
        main_region = max(set(region_keys), key=region_keys.count) if region_keys else "기타"

        total_sales = sum(m.total_sales for m in rep_markers)
        total_visits = sum(m.total_visits for m in rep_markers)
        att_list = [m.attainment_rate for m in rep_markers if m.attainment_rate is not None]
        avg_att = round(sum(att_list) / len(att_list), 4) if att_list else None

        # 커버리지 점수: (방문 있는 병원 수) / (전체 담당 병원 수)
        visited = sum(1 for m in rep_markers if m.total_visits > 0)
        coverage = round(visited / len(rep_markers), 4) if rep_markers else 0.0

        routes.append(RepRoute(
            rep_id=rep_id,
            region_key=main_region,
            route_points=route_points,
            total_sales=total_sales,
            total_visits=total_visits,
            avg_attainment=avg_att,
            coverage_score=coverage,
        ))

    # ── 3. 권역(Region) 집계 ─────────────────────────────
    region_buckets: dict[str, list[MapMarker]] = defaultdict(list)
    for m in markers:
        region_buckets[m.region_key].append(m)

    region_zones: list[RegionZone] = []
    region_sales_totals = [
        sum(marker.total_sales for marker in r_markers)
        for r_markers in region_buckets.values()
        if sum(marker.total_sales for marker in r_markers) > 0
    ]
    max_region_sales = max(region_sales_totals) if region_sales_totals else 1.0

    for region_key, r_markers in region_buckets.items():
        total_s = sum(m.total_sales for m in r_markers)
        total_t = sum(m.total_target for m in r_markers)
        atts = [m.attainment_rate for m in r_markers if m.attainment_rate is not None]
        reps = {m.rep_id for m in r_markers if m.rep_id}

        region_zones.append(RegionZone(
            region_key=region_key,
            center=_resolve_coord(region_key),
            hospital_count=len(r_markers),
            total_sales=total_s,
            total_target=total_t,
            avg_attainment=round(sum(atts)/len(atts), 4) if atts else None,
            total_visits=sum(m.total_visits for m in r_markers),
            rep_count=len(reps),
            heat_intensity=round(total_s / max_region_sales, 4),
        ))

    # ── 4. 커버리지 요약 ──────────────────────────────────
    covered = {z.region_key for z in region_zones if z.rep_count > 0}
    coverage_summary = TerritoryCoverageSummary(
        total_regions=len(region_zones),
        covered_regions=len(covered),
        coverage_rate=round(len(covered) / len(region_zones), 4) if region_zones else 0.0,
        total_hospitals=len(markers),
        mapped_hospitals=len(markers),
        gap_hospitals=len(gaps),
    )

    # ── 5. 최적화 요약 ────────────────────────────────────
    avg_hosp = round(len(markers) / len(routes), 2) if routes else 0.0
    att_per_rep = [r.avg_attainment for r in routes if r.avg_attainment is not None]
    sorted_routes = sorted(routes, key=lambda r: r.total_sales, reverse=True)

    OVERLOAD_THRESHOLD = avg_hosp * 1.5
    UNDERLOAD_THRESHOLD = avg_hosp * 0.5

    opt_summary = TerritoryOptimizationSummary(
        total_reps=len(routes),
        avg_hospitals_per_rep=avg_hosp,
        avg_attainment_per_rep=round(sum(att_per_rep)/len(att_per_rep), 4) if att_per_rep else None,
        overloaded_reps=[r.rep_id for r in routes if len(r.route_points) > OVERLOAD_THRESHOLD],
        underloaded_reps=[r.rep_id for r in routes if len(r.route_points) < UNDERLOAD_THRESHOLD],
        top_rep_id=sorted_routes[0].rep_id if sorted_routes else None,
        bottom_rep_id=sorted_routes[-1].rep_id if sorted_routes else None,
    )

    contract.period_label = f"집계 {len(hospital_records)}건"

    return TerritoryResultAsset(
        map_contract=contract,
        markers=markers,
        routes=routes,
        region_zones=region_zones,
        gaps=gaps,
        coverage_summary=coverage_summary,
        optimization_summary=opt_summary,
    )


def build_territory_builder_payload(
    asset: TerritoryResultAsset,
    territory_activity_path: str | None = None,
) -> dict:
    return _build_territory_builder_payload(
        asset=asset,
        territory_activity_path=territory_activity_path,
    )
