"""
Sandbox Result Asset 스키마

OPS에 전달되는 Sandbox 분석의 최종 출력물.
이 자산을 기반으로 OPS는 Territory / Builder로의 handoff를 결정한다.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from modules.sandbox.schemas import (
    AnalysisSummary,
    DomainQualitySummary,
    JoinQualitySummary,
    PlannedHandoffCandidate,
    HospitalAnalysisRecord,
    DashboardPayload,
)


class SandboxResultAsset(BaseModel):
    """
    Sandbox 분석 결과 자산.

    OPS가 이 자산을 평가하여:
      - 분석 품질이 충분한지 판단
      - Territory / Builder handoff 가능 여부 결정
    """
    asset_type: str = "sandbox_result_asset"
    scenario: str                           # 사용된 시나리오
    metric_months: list[str]                # 분석된 월 목록

    # 핵심 분석 요약
    analysis_summary: AnalysisSummary

    # 도메인별 품질
    domain_quality: DomainQualitySummary

    # 조인 품질
    join_quality: JoinQualitySummary

    # 병원별 상세 분석 (OPS 평가용 샘플 - 전체 아님)
    hospital_records: list[HospitalAnalysisRecord] = Field(default_factory=list)

    # 후속 handoff 후보
    handoff_candidates: list[PlannedHandoffCandidate] = Field(default_factory=list)

    # 시각화 전용 데이터 (Builder용)
    dashboard_payload: Optional[DashboardPayload] = None

    # 메타
    generated_at: datetime = Field(default_factory=datetime.now)
    source_crm_asset_id: Optional[str] = None
    source_rx_asset_id: Optional[str] = None
