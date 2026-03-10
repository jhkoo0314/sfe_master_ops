"""
OPS Core 통합 파이프라인 스키마

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPS 전체 워크플로우:

  [원천데이터 투입]
       ↓
  STEP 1: CRM 평가      → crm_result_asset        (PASS/WARN/FAIL)
       ↓ PASS 이상
  STEP 2: Prescription  → prescription_result_asset (선택적)
       ↓
  STEP 3: Sandbox 분석  → sandbox_result_asset     (분석 엔진)
       ↓ PASS 이상
  STEP 4: Territory     → territory_result_asset   (지도 최적화)
       ↓ PASS 이상
  STEP 5: Builder       → html_builder_result_asset (최종 산출물)

각 STEP은 독립적으로 평가되고,
이전 STEP이 FAIL이면 다음 STEP으로 진행 불가.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from common.types import QualityGateStatus


class StepResult(BaseModel):
    """파이프라인 단계별 실행 결과."""
    step: int
    module: str
    status: str                      # QualityGateStatus
    score: float = 0.0
    next_modules: list[str] = Field(default_factory=list)
    reasoning_note: str = ""
    gate_details: dict = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=datetime.now)
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class PipelineRunPayload(BaseModel):
    """파이프라인 실행 요청."""
    run_id: str
    scenario: str = "crm_sales_target"
    start_from_step: int = 1         # 재실행 시 특정 STEP부터 시작 가능
    stop_on_fail: bool = True        # FAIL 시 즉시 중단 여부

    # 각 모듈 Result Asset (JSON 직렬화)
    crm_asset: Optional[dict] = None
    prescription_asset: Optional[dict] = None
    sandbox_asset: Optional[dict] = None
    territory_asset: Optional[dict] = None
    builder_asset: Optional[dict] = None


class PipelineRunResult(BaseModel):
    """전체 파이프라인 실행 결과."""
    run_id: str
    scenario: str
    overall_status: str             # 최종 판정
    overall_score: float = 0.0

    steps: list[StepResult] = Field(default_factory=list)

    # 최종 handoff 가능한 모듈
    final_eligible_modules: list[str] = Field(default_factory=list)

    # 추천 액션
    recommended_actions: list[str] = Field(default_factory=list)

    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_duration_ms: Optional[int] = None


class PipelineStatusSummary(BaseModel):
    """운영 콘솔용 전체 파이프라인 상태 요약."""
    active_run_id: Optional[str] = None
    last_run_at: Optional[datetime] = None
    last_overall_status: Optional[str] = None

    # 모듈별 마지막 상태
    module_statuses: dict[str, str] = Field(default_factory=dict)

    # 누적 통계
    total_runs: int = 0
    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0
