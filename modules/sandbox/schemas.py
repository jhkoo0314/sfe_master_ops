"""
SFE Sandbox 모듈 스키마

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sandbox는 OPS가 허용한 자산 조합을 받아 분석하는 엔진이다.
Sandbox는 데이터를 결정하지 않는다. OPS가 결정한다.

데이터 흐름:
  CRM Result Asset    ─┐
  Sales Domain        ─┼─▶ SandboxInputStandard ─▶ SandboxResultAsset
  Target Domain       ─┤
  Prescription (선택) ─┘

조인 키:
  모든 분석의 기준은 hospital_id (Phase 2 CRM에서 확립)
  company_data는 hospital_id로 조인되어야만 Sandbox에 입력 가능
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations
from datetime import date
from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


# ────────────────────────────────────────
# 1. 도메인 표준 스키마 (각 데이터 소스별)
# ────────────────────────────────────────

class SalesDomainRecord(BaseModel):
    """
    회사 매출 실적 표준 레코드.

    어떤 포맷의 매출 파일이 와도 Adapter를 통해 이 스키마로 변환된다.
    핵심: hospital_id가 반드시 존재해야 Sandbox에 입력 가능.
    """
    hospital_id: str
    rep_id: str
    metric_month: str               # YYYYMM
    product_id: str
    sales_amount: float             # 매출액 (원)
    sales_quantity: Optional[float] = None  # 수량
    channel: Optional[str] = None   # 채널 구분 (직판/병원/약국 등)
    hospital_name: Optional[str] = None
    rep_name: Optional[str] = None
    branch_id: Optional[str] = None
    branch_name: Optional[str] = None
    product_name: Optional[str] = None
    source_label: str = "unknown"   # 어느 파일/회사 데이터인지 (추적용)


class TargetDomainRecord(BaseModel):
    """
    회사 목표 표준 레코드.

    담당자별 + 월별 + 제품별 목표.
    hospital_id 또는 rep_id 기준으로 연결.
    """
    rep_id: str
    metric_month: str               # YYYYMM
    product_id: str
    target_amount: float            # 목표액 (원)
    hospital_id: Optional[str] = None  # 병원 단위 목표인 경우
    hospital_name: Optional[str] = None
    rep_name: Optional[str] = None
    branch_id: Optional[str] = None
    branch_name: Optional[str] = None
    product_name: Optional[str] = None
    source_label: str = "unknown"


class CrmDomainRecord(BaseModel):
    """
    CRM Phase 2에서 파생된 도메인 레코드.
    SandboxInputStandard 구성 시 crm_result_asset의 요약 정보를 담는다.
    """
    hospital_id: str
    rep_id: str
    metric_month: str
    total_visits: int
    detail_call_count: int
    rep_name: Optional[str] = None
    branch_id: Optional[str] = None
    branch_name: Optional[str] = None
    active_day_count: int = 0
    avg_sentiment_score: Optional[float] = None
    avg_quality_factor: Optional[float] = None
    avg_impact_factor: Optional[float] = None
    avg_weighted_activity_score: Optional[float] = None
    next_action_count: int = 0
    activity_types: list[str] = Field(default_factory=list)


class PrescriptionDomainRecord(BaseModel):
    """
    Prescription Phase 3에서 파생된 도메인 레코드.
    선택적 입력 - OPS가 연결 허용 시에만 포함.
    """
    hospital_id: str
    pharmacy_id: str
    wholesaler_id: str
    product_id: str
    metric_month: str
    quantity: float
    amount: float
    lineage_key: str
    is_complete: bool


# ────────────────────────────────────────
# 2. Sandbox Reference Master
# ────────────────────────────────────────

class AllowedAssetCombo(BaseModel):
    """
    OPS가 허용하는 자산 조합 규칙 정의.
    Sandbox는 이 규칙을 벗어나는 입력을 거부한다.
    """
    combo_id: str                      # 조합 식별자
    combo_name: str                    # 조합 이름
    required_domains: list[str]        # 필수 도메인 (예: ["crm", "sales", "target"])
    optional_domains: list[str] = Field(default_factory=list)  # 선택 도메인
    description: str = ""


class SandboxReferenceMaster(BaseModel):
    """
    Sandbox가 수신할 수 있는 자산 조합 마스터.
    OPS가 이 마스터를 기준으로 sandbox_input_standard의 유효성을 판단한다.
    """
    allowed_combos: list[AllowedAssetCombo]
    join_key: str = "hospital_id"      # 모든 도메인의 공통 조인 키
    min_months_required: int = 1       # 최소 분석 기간 (월)
    version: str = "1.0"


# ────────────────────────────────────────
# 3. Sandbox Input Standard
# ────────────────────────────────────────

SandboxScenario = str  # "crm_sales_target" 등 기본값 외에 커스텀 명칭 가능

AggregationLevel = Literal["monthly", "quarterly", "yearly", "total"]


class SandboxInputStandard(BaseModel):
    """
    Sandbox 분석 입력 표준.

    OPS가 허용한 자산 조합에 따라 구성된다.
    """
    scenario: SandboxScenario
    aggregation_level: AggregationLevel = "monthly"  # 분석 집계 단위
    weight_config: dict[str, float] = Field(default_factory=dict) # 지표별 가중치 (커스텀 분석용)

    metric_months: list[str]            # 분석 대상 월 목록 (YYYYMM)
    crm_records: list[CrmDomainRecord] = Field(default_factory=list)
    sales_records: list[SalesDomainRecord] = Field(default_factory=list)
    target_records: list[TargetDomainRecord] = Field(default_factory=list)
    prescription_records: list[PrescriptionDomainRecord] = Field(default_factory=list)

    # 메타
    source_crm_asset_id: Optional[str] = None
    source_rx_asset_id: Optional[str] = None
    created_by: str = "ops_engine"

    @property
    def has_crm(self) -> bool:
        return len(self.crm_records) > 0

    @property
    def has_sales(self) -> bool:
        return len(self.sales_records) > 0

    @property
    def has_target(self) -> bool:
        return len(self.target_records) > 0

    @property
    def has_prescription(self) -> bool:
        return len(self.prescription_records) > 0

    @property
    def unique_hospital_ids(self) -> set[str]:
        ids = set()
        for r in self.crm_records:
            ids.add(r.hospital_id)
        for r in self.sales_records:
            ids.add(r.hospital_id)
        return ids


# ────────────────────────────────────────
# 4. 분석 요약 스키마
# ────────────────────────────────────────

class HospitalAnalysisRecord(BaseModel):
    """병원 단위 통합 분석 레코드 (Sandbox 핵심 산출물)."""
    hospital_id: str
    metric_month: str
    rep_id: Optional[str] = None

    # CRM 지표
    total_visits: int = 0
    detail_call_count: int = 0

    # 매출 지표
    total_sales: float = 0.0
    total_quantity: float = 0.0

    # 목표 지표
    total_target: float = 0.0
    attainment_rate: Optional[float] = None   # 달성률 (sales/target)

    # Prescription 지표 (선택)
    rx_amount: float = 0.0
    rx_complete_flows: int = 0

    # 조인 상태
    has_crm: bool = False
    has_sales: bool = False
    has_target: bool = False
    has_rx: bool = False

    @property
    def is_fully_joined(self) -> bool:
        return self.has_crm and self.has_sales and self.has_target


class AnalysisSummary(BaseModel):
    """전체 분석 집계 요약."""
    total_hospitals: int
    total_months: int
    aggregation_level: str = "monthly"
    total_sales_amount: float
    total_target_amount: float
    avg_attainment_rate: Optional[float] = None
    total_visits: int
    fully_joined_hospitals: int     # crm + sales + target 모두 조인된 병원 수
    rx_linked_hospitals: int = 0    # prescription까지 연결된 병원 수
    metric_months: list[str] = Field(default_factory=list)

    # 커스텀 집계 지표 (사용자 정의 필드)
    custom_metrics: dict[str, float] = Field(default_factory=dict)


class DashboardPayload(BaseModel):
    """
    HTML Builder(Phase 6)를 위한 시각화 전용 데이터 구조.
    회사가 원하는 대시보드 형태를 여기서 결정합니다.
    """
    layout_type: str = "comprehensive"  # "sales_focus", "activity_focus" 등
    chart_data: dict[str, list] = Field(default_factory=dict) # 시계열, 파이차트 등 데이터
    top_performers: list[dict] = Field(default_factory=list)
    bottom_performers: list[dict] = Field(default_factory=list)
    insight_messages: list[str] = Field(default_factory=list)
    template_payload: dict[str, Any] = Field(default_factory=dict)


class DomainQualitySummary(BaseModel):
    """각 도메인별 데이터 품질 요약."""
    crm_record_count: int = 0
    sales_record_count: int = 0
    target_record_count: int = 0
    rx_record_count: int = 0

    crm_unique_hospitals: int = 0
    sales_unique_hospitals: int = 0
    target_unique_reps: int = 0
    rx_unique_hospitals: int = 0

    crm_months: list[str] = Field(default_factory=list)
    sales_months: list[str] = Field(default_factory=list)


class JoinQualitySummary(BaseModel):
    """도메인 간 조인 품질 요약."""
    hospitals_with_crm_and_sales: int = 0
    hospitals_with_all_three: int = 0
    hospitals_with_rx_added: int = 0

    crm_sales_join_rate: float = 0.0
    full_join_rate: float = 0.0

    orphan_sales_hospitals: int = 0
    orphan_crm_hospitals: int = 0

    join_key: str = "hospital_id"


class PlannedHandoffCandidate(BaseModel):
    """Territory/Builder로 넘길 수 있는 후속 모듈 후보."""
    module: str
    condition: str
    is_eligible: bool
    blocking_reason: Optional[str] = None
    payload_hint: Optional[str] = None # Builder에게 줄 템플릿 힌트
