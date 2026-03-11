"""
CRM Result Asset - Pydantic 스키마 정의

CRM 모듈이 최종으로 생산하는 Result Asset.
OPS Core는 이 자산만 보고 품질/연결을 판단한다.

구성:
  - behavior_profile: 담당자별 행동 프로파일
  - kpi_summary: 월별 KPI 요약
  - activity_context_summary: 활동 문맥 요약
  - mapping_quality_summary: 매핑 품질 요약 (OPS 판단 핵심)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from common.asset_versions import CRM_RESULT_SCHEMA_VERSION
from common.types import ResultAssetType


# ────────────────────────────────────────
# 세부 구성 요소 스키마
# ────────────────────────────────────────

class RepBehaviorProfile(BaseModel):
    """담당자 1인의 행동 프로파일."""
    rep_id: str
    rep_name: str
    branch_id: str
    branch_name: str = ""
    total_visits: int = Field(0, description="총 방문 건수")
    unique_hospitals: int = Field(0, description="방문한 고유 병원 수")
    avg_visits_per_hospital: float = Field(0.0, description="병원당 평균 방문 횟수")
    detail_call_rate: float = Field(0.0, ge=0.0, le=1.0, description="상세 설명 비율 (0~1)")
    top_activity_types: list[str] = Field(default_factory=list, description="주요 활동 유형 상위 3개")
    active_months: list[str] = Field(default_factory=list, description="활동이 있는 월 목록 (YYYYMM)")


class MonthlyKpiSummary(BaseModel):
    """월별 KPI 집계 요약."""
    metric_month: str = Field(..., description="집계 기준 월 (YYYYMM)")
    total_visits: int = 0
    total_reps_active: int = 0
    total_hospitals_visited: int = 0
    avg_visits_per_rep: float = 0.0
    detail_call_count: int = 0


class ActivityContextSummary(BaseModel):
    """활동 문맥 요약 - OPS가 후속 재사용 가능성을 판단하는 근거."""
    total_activity_records: int = 0
    date_range_start: Optional[str] = None    # YYYY-MM-DD
    date_range_end: Optional[str] = None      # YYYY-MM-DD
    unique_reps: int = 0
    unique_hospitals: int = 0
    unique_branches: int = 0
    activity_types_found: list[str] = Field(default_factory=list)
    products_mentioned: list[str] = Field(default_factory=list)


class MappingQualitySummary(BaseModel):
    """
    매핑 품질 요약 - OPS 품질 게이트 핵심 판단 항목.

    hospital_id, rep_id, branch_id 매핑 성공률을 포함.
    이 값이 낮으면 OPS가 FAIL 또는 WARN 판정.
    """
    total_raw_records: int = 0
    mapped_hospital_count: int = 0
    unmapped_hospital_count: int = 0
    hospital_mapping_rate: float = Field(0.0, ge=0.0, le=1.0, description="병원 매핑 성공률 (0~1)")
    rep_coverage_rate: float = Field(0.0, ge=0.0, le=1.0, description="담당자 커버리지 (0~1)")
    unmapped_hospital_names: list[str] = Field(default_factory=list, description="매핑 실패 병원명 목록 (최대 20개)")


# ────────────────────────────────────────
# CRM Result Asset 최종 스키마
# ────────────────────────────────────────

class CrmResultAsset(BaseModel):
    """
    CRM 모듈이 생산하는 최종 Result Asset.
    OPS Core는 이 구조만 보고 판단한다. raw는 여기에 없다.

    다음 모듈로의 handoff 대상:
      - Prescription Data Flow (hospital_id 재사용)
      - SFE Sandbox (crm_result_asset 전체 입력)
    """
    schema_version: str = Field(
        default=CRM_RESULT_SCHEMA_VERSION,
        description="Result Asset JSON 규격 버전"
    )
    asset_type: str = Field(
        default=ResultAssetType.CRM_RESULT,
        description="자산 타입 식별자 (고정값)"
    )
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="Result Asset 생성 일시"
    )
    source_module: str = Field(default="crm", description="생산 모듈")

    # 핵심 구성 요소
    behavior_profiles: list[RepBehaviorProfile] = Field(
        default_factory=list,
        description="담당자별 행동 프로파일 목록"
    )
    monthly_kpi: list[MonthlyKpiSummary] = Field(
        default_factory=list,
        description="월별 KPI 집계 목록"
    )
    activity_context: ActivityContextSummary = Field(
        default_factory=ActivityContextSummary,
        description="활동 문맥 요약"
    )
    mapping_quality: MappingQualitySummary = Field(
        default_factory=MappingQualitySummary,
        description="매핑 품질 요약 (OPS 판단 핵심)"
    )

    # OPS와의 연결 메타
    planned_handoff_modules: list[str] = Field(
        default_factory=lambda: ["prescription", "sandbox"],
        description="이 자산을 재사용할 예정인 다음 모듈"
    )
    notes: Optional[str] = Field(None, description="생성 비고 또는 경고 메시지")
