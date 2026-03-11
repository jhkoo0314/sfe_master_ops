"""
Territory Result Asset

OPS에 전달되는 Territory 분석의 최종 출력물.
HTML Builder가 이 자산을 받아 인터랙티브 지도 대시보드를 렌더링한다.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from common.asset_versions import TERRITORY_RESULT_SCHEMA_VERSION

from modules.territory.schemas import (
    MapMarker, RepRoute, RegionZone,
    TerritoryGap, TerritoryCoverageSummary, TerritoryOptimizationSummary,
)
from modules.territory.templates import TerritoryMapContract


class TerritoryResultAsset(BaseModel):
    schema_version: str = Field(default=TERRITORY_RESULT_SCHEMA_VERSION)
    asset_type: str = "territory_result_asset"

    # 지도 템플릿 (렌더링 규격)
    map_contract: TerritoryMapContract

    # 지도 데이터
    markers: list[MapMarker] = Field(default_factory=list)
    routes: list[RepRoute] = Field(default_factory=list)
    region_zones: list[RegionZone] = Field(default_factory=list)
    gaps: list[TerritoryGap] = Field(default_factory=list)

    # 분석 요약
    coverage_summary: TerritoryCoverageSummary
    optimization_summary: TerritoryOptimizationSummary

    # 메타
    generated_at: datetime = Field(default_factory=datetime.now)
    source_sandbox_scenario: Optional[str] = None
