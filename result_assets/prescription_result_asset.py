"""
Prescription Result Asset - Pydantic 스키마 정의

Prescription 모듈의 최종 출력.
OPS는 이 자산만 보고 품질/연결을 판단한다.

구성:
  - lineage_summary: 도매→약국→병원 흐름 요약
  - reconciliation_summary: 데이터 대조 요약
  - validation_gap_summary: 매핑 실패 분석
  - mapping_quality_summary: 전체 품질 지표 (OPS 판단 핵심)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from common.types import ResultAssetType


class LineageSummary(BaseModel):
    """도매→약국→병원 흐름 요약."""
    total_flow_records: int = 0
    complete_flow_count: int = 0      # hospital까지 연결된 흐름 수
    incomplete_flow_count: int = 0    # UNMAPPED 포함 흐름 수
    flow_completion_rate: float = Field(0.0, ge=0.0, le=1.0)
    unique_wholesalers: int = 0
    unique_pharmacies: int = 0
    unique_hospitals_connected: int = 0
    unique_products: int = 0
    metric_months: list[str] = Field(default_factory=list)


class ReconciliationSummary(BaseModel):
    """
    데이터 대조 요약.
    도매출고 vs 약국구입 데이터가 둘 다 있을 때 비교.
    """
    wholesaler_shipment_qty: float = 0.0
    pharmacy_purchase_qty: float = 0.0
    qty_match_rate: Optional[float] = None
    has_both_sources: bool = False
    reconciliation_note: Optional[str] = None


class ValidationGapSummary(BaseModel):
    """미매핑 분석 요약 - OPS 판단 핵심 근거."""
    total_gap_records: int = 0
    gap_by_reason: dict[str, int] = Field(default_factory=dict)
    """
    gap_reason별 건수:
      "no_hospital_in_region": 해당 지역에 담당 병원 없음
      "ambiguous_match": 복수 병원 후보로 선택 불가
      "region_mismatch": 지역 코드 정보 불충분
    """
    top_unmapped_pharmacies: list[str] = Field(
        default_factory=list,
        description="미매핑 건수 상위 약국명 목록 (최대 20개)"
    )
    top_unmapped_products: list[str] = Field(
        default_factory=list,
        description="미매핑 건수 상위 제품명 목록 (최대 10개)"
    )


class PrescriptionMappingQualitySummary(BaseModel):
    """매핑 품질 요약 - OPS 품질 게이트 핵심 판단 항목."""
    total_records: int = 0
    adapter_failed_records: int = 0   # Adapter 변환 실패 (필수값 누락 등)
    flow_complete_records: int = 0    # 병원까지 연결 성공
    flow_incomplete_records: int = 0  # UNMAPPED
    flow_completion_rate: float = Field(0.0, ge=0.0, le=1.0, description="병원 연결 성공률")
    hospital_coverage_rate: float = Field(0.0, ge=0.0, le=1.0, description="CRM hospital_id 활용률")


class PrescriptionResultAsset(BaseModel):
    """
    Prescription 모듈이 생산하는 최종 Result Asset.
    OPS Core는 이 구조만 보고 판단한다.

    다음 모듈로의 handoff 대상:
      - SFE Sandbox (CRM Result Asset과 함께 조합 분석)
    """
    asset_type: str = Field(default=ResultAssetType.PRESCRIPTION_RESULT)
    generated_at: datetime = Field(default_factory=datetime.now)
    source_module: str = Field(default="prescription")

    lineage_summary: LineageSummary = Field(default_factory=LineageSummary)
    reconciliation_summary: ReconciliationSummary = Field(default_factory=ReconciliationSummary)
    validation_gap_summary: ValidationGapSummary = Field(default_factory=ValidationGapSummary)
    mapping_quality: PrescriptionMappingQualitySummary = Field(
        default_factory=PrescriptionMappingQualitySummary
    )
    planned_handoff_modules: list[str] = Field(default_factory=lambda: ["sandbox"])
    notes: Optional[str] = None
