"""
Territory Optimizer 스키마

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Template-Driven 설계 (Sandbox와 동일 원칙):

  1. 지도 템플릿에 마커 슬롯(MapMarkerSlot)을 먼저 정의한다.
     예: "이 마커는 달성률 색상, 매출 크기로 표시해줘"
  2. Territory 엔진이 Sandbox 데이터를 읽어
     각 슬롯의 marker_key에 맞는 값을 자동으로 채운다.
  3. HTML Builder가 채워진 마커 데이터로 지도를 렌더링한다.

지도 데이터 구조:
  MapMarker   → 병원 위치 핀 (실적, 달성률, 방문수)
  RepRoute    → 담당자 동선 (방문 순서, 효율)
  RegionZone  → 시도/시군구 단위 권역 히트맵
  TerritoryGap→ 커버 안 되는 지역 (미담당 공백)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field


# ────────────────────────────────────────
# 1. 지도 기본 단위
# ────────────────────────────────────────

class GeoCoord(BaseModel):
    """
    위경도 좌표.
    실제 데이터가 없는 경우 region_key 기반 시도 중심 좌표를 사용한다.
    """
    lat: float
    lng: float
    source: str = "region_centroid"   # "exact" | "region_centroid" | "sigungu_centroid"


# 한국 시도별 중심 좌표 (근사값 - 실제 병원 좌표가 없을 때 사용)
SIDO_CENTROIDS: dict[str, GeoCoord] = {
    "서울":  GeoCoord(lat=37.5665, lng=126.9780),
    "부산":  GeoCoord(lat=35.1796, lng=129.0756),
    "대구":  GeoCoord(lat=35.8714, lng=128.6014),
    "인천":  GeoCoord(lat=37.4563, lng=126.7052),
    "광주":  GeoCoord(lat=35.1595, lng=126.8526),
    "대전":  GeoCoord(lat=36.3504, lng=127.3845),
    "울산":  GeoCoord(lat=35.5384, lng=129.3114),
    "세종":  GeoCoord(lat=36.4800, lng=127.2890),
    "경기":  GeoCoord(lat=37.4138, lng=127.5183),
    "강원":  GeoCoord(lat=37.8228, lng=128.1555),
    "충북":  GeoCoord(lat=36.8000, lng=127.7000),
    "충남":  GeoCoord(lat=36.5184, lng=126.8000),
    "전북":  GeoCoord(lat=35.7175, lng=127.1530),
    "전남":  GeoCoord(lat=34.8679, lng=126.9910),
    "경북":  GeoCoord(lat=36.4919, lng=128.8889),
    "경남":  GeoCoord(lat=35.4606, lng=128.2132),
    "제주":  GeoCoord(lat=33.4996, lng=126.5312),
}


class MapMarker(BaseModel):
    """
    지도 위 병원 핀 하나.
    HTML Builder가 이 객체로 Leaflet/Google Maps 마커를 그린다.
    """
    hospital_id: str
    hospital_name: Optional[str] = None
    coord: GeoCoord
    region_key: str                 # 시도명
    sub_region_key: Optional[str] = None  # 시군구명

    # 실적 데이터 (Sandbox에서 주입)
    total_sales: float = 0.0
    total_target: float = 0.0
    attainment_rate: Optional[float] = None
    total_visits: int = 0
    rep_id: Optional[str] = None

    # 시각화 힌트 (Builder용)
    marker_color: str = "gray"      # "green"|"yellow"|"red"|"gray"
    marker_size: str = "md"         # "sm"|"md"|"lg"|"xl"
    tooltip: str = ""               # 마우스 오버 시 표시할 텍스트


class RoutePoint(BaseModel):
    """동선의 방문 순서 하나."""
    order: int
    hospital_id: str
    coord: GeoCoord
    visit_count: int = 0
    sales_amount: float = 0.0


class RepRoute(BaseModel):
    """
    담당자 한 명의 방문 동선.
    방문 효율(거리 대비 성과)을 계산하여 최적 순서를 제안한다.
    """
    rep_id: str
    rep_name: Optional[str] = None
    region_key: str                 # 주요 담당 시도
    route_points: list[RoutePoint] = Field(default_factory=list)

    total_sales: float = 0.0
    total_visits: int = 0
    avg_attainment: Optional[float] = None

    # 동선 효율 (단순화: 담당 병원 수 / 권역 수)
    coverage_score: float = 0.0     # 0.0 ~ 1.0


class RegionZone(BaseModel):
    """
    시도/시군구 단위 권역 집계.
    히트맵 렌더링용.
    """
    region_key: str
    sub_region_key: Optional[str] = None
    center: GeoCoord

    hospital_count: int = 0
    total_sales: float = 0.0
    total_target: float = 0.0
    avg_attainment: Optional[float] = None
    total_visits: int = 0
    rep_count: int = 0              # 담당 담당자 수

    # 히트맵 강도 (0~1)
    heat_intensity: float = 0.0


class TerritoryGap(BaseModel):
    """미커버 지역 (병원은 있지만 담당자가 없거나 방문 0)."""
    region_key: str
    hospital_id: str
    gap_reason: str               # "no_rep_assigned" | "zero_visits" | "orphan_sales"


# ────────────────────────────────────────
# 2. Territory 분석 요약
# ────────────────────────────────────────

class TerritoryCoverageSummary(BaseModel):
    """커버리지 요약."""
    total_regions: int              # 전체 권역 수
    covered_regions: int            # 담당자가 있는 권역 수
    coverage_rate: float            # covered / total

    total_hospitals: int
    mapped_hospitals: int           # 지도에 마커가 생성된 병원
    gap_hospitals: int              # 미커버 병원


class TerritoryOptimizationSummary(BaseModel):
    """배치 최적화 요약."""
    total_reps: int
    avg_hospitals_per_rep: float
    avg_attainment_per_rep: Optional[float] = None

    # 불균형 지표
    overloaded_reps: list[str] = Field(default_factory=list)   # 담당 병원 수 과다
    underloaded_reps: list[str] = Field(default_factory=list)  # 담당 병원 수 부족
    top_rep_id: Optional[str] = None
    bottom_rep_id: Optional[str] = None
