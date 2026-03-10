"""
Territory Map Template Contract

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Template-First 원칙 (Sandbox와 동일):
  1. 지도에 무엇을 표시할지 SlotKey(태그)로 미리 선언
  2. Territory 엔진이 Sandbox 데이터를 읽어 자동 채움
  3. HTML Builder가 채워진 데이터로 지도 렌더링

SlotKey 목록 (엔진이 지원하는 분석 도구):
  마커 색상:
    "attainment_color"   → 달성률 구간에 따라 green/yellow/red
    "sales_color"        → 매출 크기에 따라 색상 분류
  마커 크기:
    "sales_size"         → 매출 크기 비례
    "visit_size"         → 방문 수 비례
  툴팁:
    "full_summary"       → 병원명, 매출, 달성률, 방문수 모두
    "sales_focus"        → 매출과 달성률만
    "visit_focus"        → 방문수와 CRM 지표만
  동선:
    "optimal_route"      → 방문수 기준 내림차순 정렬 동선
    "sales_route"        → 매출 기준 내림차순 정렬 동선

새 회사용 템플릿 추가 방법:
  아래 TerritoryMapContract를 상속하거나 복사하여
  각 슬롯의 slot_key만 변경하면 엔진이 자동 매핑합니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from typing import Optional
from pydantic import BaseModel, Field


class MarkerStyleSlot(BaseModel):
    """
    지도 마커 스타일 슬롯 (태그 기반 자동 주입).

    color_key: 마커 색상을 어떤 지표로 결정할지
    size_key:  마커 크기를 어떤 지표로 결정할지
    tooltip_key: 마우스 오버 시 툴팁 형식
    """
    color_key: str = "attainment_color"   # 기본: 달성률 기반 색상
    size_key: str = "sales_size"          # 기본: 매출 기반 크기
    tooltip_key: str = "full_summary"     # 기본: 모든 정보 표시


class RouteStyleSlot(BaseModel):
    """
    담당자 동선 스타일 슬롯.

    route_key: 동선 정렬 기준
    show_line: 동선을 선으로 연결할지
    """
    route_key: str = "optimal_route"
    show_line: bool = True
    line_color_key: str = "rep_color"     # 담당자마다 다른 색 선


class HeatmapSlot(BaseModel):
    """
    권역 히트맵 슬롯.

    heat_key: 히트맵 강도를 어떤 지표로 결정할지
    """
    heat_key: str = "total_sales"         # 기본: 매출 기준 히트맵


class TerritoryMapContract(BaseModel):
    """
    Territory 지도 대시보드 템플릿 계약.

    이 틀이 먼저 정의되고, 엔진이 Sandbox 데이터로 채운다.
    HTML Builder는 채워진 이 계약을 받아 지도를 렌더링한다.
    """
    map_title: str
    period_label: str = "자동 생성"

    # 시각화 레이어 정의 (무엇을, 어떻게 보여줄지)
    marker_style: MarkerStyleSlot = Field(default_factory=MarkerStyleSlot)
    route_style: RouteStyleSlot = Field(default_factory=RouteStyleSlot)
    heatmap_style: Optional[HeatmapSlot] = None

    # 지도 초기 설정
    map_center: dict = Field(default_factory=lambda: {"lat": 36.5, "lng": 127.8})
    map_zoom: int = 7               # 한국 전체가 보이는 줌 레벨

    # 활성화할 레이어
    show_markers: bool = True
    show_routes: bool = True
    show_heatmap: bool = False
    show_gaps: bool = True          # 미커버 지역 표시

    # 추가 패널 (지도 옆 사이드바용)
    show_rep_ranking: bool = True   # 담당자 순위 패널
    show_region_table: bool = True  # 권역별 실적 테이블

    @classmethod
    def get_standard_template(cls) -> "TerritoryMapContract":
        """
        표준 영업 권역 지도 템플릿.
        달성률 기반 색상, 매출 기반 크기, 방문 동선 포함.
        """
        return cls(
            map_title="SFE 권역별 영업 성과 지도",
            marker_style=MarkerStyleSlot(
                color_key="attainment_color",
                size_key="sales_size",
                tooltip_key="full_summary",
            ),
            route_style=RouteStyleSlot(
                route_key="optimal_route",
                show_line=True,
            ),
            heatmap_style=HeatmapSlot(heat_key="total_sales"),
            show_heatmap=True,
        )

    @classmethod
    def get_activity_focus_template(cls) -> "TerritoryMapContract":
        """
        활동량 중심 영업 권역 지도 (방문 빈도 집중 분석).
        """
        return cls(
            map_title="SFE 방문 활동 커버리지 지도",
            marker_style=MarkerStyleSlot(
                color_key="visit_color",
                size_key="visit_size",
                tooltip_key="visit_focus",
            ),
            route_style=RouteStyleSlot(
                route_key="optimal_route",
                show_line=True,
            ),
            show_heatmap=False,
        )
