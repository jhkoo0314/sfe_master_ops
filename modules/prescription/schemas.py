"""
Prescription 모듈 Pydantic 스키마 정의

흐름:
  공공약가데이터 → PrescriptionMaster (제품/성분 기준)
  회사raw → CompanyPrescriptionStandard (도매 또는 약국 단위 기록)
  CompanyPrescriptionStandard → PrescriptionStandardFlow (도매→약국→병원 연결)
  미매핑 기록 → PrescriptionGapRecord (gap 추적)

핵심 원칙:
  - 모든 스키마는 회사 데이터를 가정하지 않는다.
  - pharmacy_id, wholesaler_id는 id_rules.py의 범용 규칙으로 생성.
  - hospital_id는 CRM Phase 2의 HospitalMaster를 재사용한다.
  - lineage_key는 연결의 완결성을 나타내는 핵심 지표다.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


# ────────────────────────────────────────
# 1. PrescriptionMaster - 제품/성분 공통 기준
# ────────────────────────────────────────

class PrescriptionMaster(BaseModel):
    """
    제품/성분 공통 기준 데이터.
    어떤 회사의 처방 데이터가 와도 제품을 이 기준으로 매핑한다.

    공공 데이터 기반:
      - 건강보험 청구 기준 약품 목록 (보건복지부/심평원)
      - 식약처 의약품 허가 정보

    핵심 키: product_id (id_rules.generate_product_id()로 생성)
    """
    product_id: str = Field(..., description="범용 규칙으로 생성된 제품 고유 ID")
    product_name: str = Field(..., description="제품명 (공식 허가명)")
    ingredient_code: Optional[str] = Field(None, description="건강보험 청구 성분코드")
    ingredient_name: Optional[str] = Field(None, description="주성분명")
    dosage_form: Optional[str] = Field(None, description="제형 (정/캡슐/주사/시럽 등)")
    strength: Optional[str] = Field(None, description="함량 (예: 10mg, 5mg/mL)")
    atc_code: Optional[str] = Field(None, description="ATC 분류 코드 (WHO 기준)")
    manufacturer: Optional[str] = Field(None, description="제조사명")
    is_listed: bool = Field(True, description="건보 급여 등재 여부")


# ────────────────────────────────────────
# 2. CompanyPrescriptionStandard - 회사별 처방/출고 표준화
# ────────────────────────────────────────

class CompanyPrescriptionStandard(BaseModel):
    """
    회사 Prescription raw 데이터를 표준화한 단위 기록.

    데이터 유형:
      - "wholesaler_shipment": 도매상 → 약국 출고 기록
      - "pharmacy_purchase": 약국 → 병원 구입 기록 (어떤 회사가 관리 중인 경우)

    두 유형 모두 이 스키마로 표준화되어 flow_builder에서 연결된다.

    핵심 키:
      wholesaler_id + pharmacy_id + metric_month + product_id
    """
    record_type: str = Field(
        ...,
        description="기록 유형: 'wholesaler_shipment' 또는 'pharmacy_purchase'"
    )

    # 도매상 정보
    wholesaler_id: str = Field(..., description="범용 규칙으로 생성된 도매상 ID (WS_...)")
    wholesaler_name: str = Field(..., description="도매상명 (원본)")

    # 약국 정보
    pharmacy_id: str = Field(..., description="범용 규칙으로 생성된 약국 ID (PH_...)")
    pharmacy_name: str = Field(..., description="약국명 (원본)")
    pharmacy_region_key: str = Field(..., description="약국 시도 코드")
    pharmacy_sub_region_key: str = Field(..., description="약국 시군구 코드")
    pharmacy_postal_code: Optional[str] = Field(None, description="약국 우편번호")

    # 제품 정보
    product_id: str = Field(..., description="범용 규칙으로 생성된 제품 ID (PROD_...)")
    product_name: str = Field(..., description="제품명 (원본)")
    ingredient_code: Optional[str] = Field(None, description="성분코드 (있으면 매핑 정확도 향상)")

    # 수량/금액
    quantity: float = Field(..., ge=0, description="출고/구입 수량")
    amount: Optional[float] = Field(None, ge=0, description="출고/구입 금액")
    unit: Optional[str] = Field(None, description="단위 (정/박스/바이알 등)")

    # 시간 기준
    transaction_date: date = Field(..., description="거래 일자")
    metric_month: str = Field(..., description="집계 기준 월 (YYYYMM)")

    # 병원 연결 정보 (약국→병원 매핑 가능한 경우)
    hospital_id: Optional[str] = Field(
        None,
        description="병원 ID (hospital_master 기준, 매핑된 경우 채움)"
    )

    # 추적 메타
    raw_row_index: Optional[int] = Field(None, description="원본 파일 행 번호")


# ────────────────────────────────────────
# 3. PrescriptionStandardFlow - 도매→약국→병원 연결 레코드
# ────────────────────────────────────────

class PrescriptionStandardFlow(BaseModel):
    """
    도매→약국→병원 흐름을 하나의 레코드로 표현.
    lineage_key가 이 흐름의 핵심 추적 단위이다.

    연결 완결성:
      - wholesaler_id + pharmacy_id: 항상 존재 (출고 데이터 기반)
      - hospital_id: 매핑 성공 시 존재, 실패 시 None
      - lineage_key: hospital_id 없으면 "UNMAPPED" 포함

    OPS가 이 레코드의 집계 결과로 흐름 품질을 판단한다.
    """
    lineage_key: str = Field(
        ...,
        description="도매→약국→병원 연결 키 (id_rules.generate_lineage_key())"
    )
    is_complete: bool = Field(
        ...,
        description="병원까지 완전히 연결된 흐름인지 여부"
    )

    # 도매 정보
    wholesaler_id: str
    wholesaler_name: str
    wholesaler_region_key: str

    # 약국 정보
    pharmacy_id: str
    pharmacy_name: str
    pharmacy_region_key: str
    pharmacy_sub_region_key: str

    # 병원 연결 (매핑 성공 시)
    hospital_id: Optional[str] = Field(None, description="CRM hospital_master 기준 병원 ID")
    hospital_name: Optional[str] = Field(None, description="병원명 (매핑 성공 시)")
    hospital_mapping_method: Optional[str] = Field(
        None,
        description="병원 매핑 방법: 'direct' | 'region_proximity' | None"
    )

    # 제품 정보
    product_id: str
    product_name: str
    ingredient_code: Optional[str] = None

    # 집계 수치
    total_quantity: float = Field(0.0, ge=0)
    total_amount: Optional[float] = Field(None, ge=0)
    metric_month: str

    # 소스 추적
    source_record_type: str = Field(
        ...,
        description="원본 기록 유형: 'wholesaler_shipment' | 'pharmacy_purchase'"
    )


# ────────────────────────────────────────
# 4. PrescriptionGapRecord - 미매핑 추적
# ────────────────────────────────────────

class PrescriptionGapRecord(BaseModel):
    """
    병원 매핑에 실패한 흐름 기록.
    gap_summary 생성의 원재료.
    OPS가 이 비율로 데이터 품질을 판단한다.
    """
    pharmacy_id: str
    pharmacy_name: str
    pharmacy_region_key: str
    wholesaler_id: str
    product_id: str
    metric_month: str
    quantity: float
    gap_reason: str = Field(
        ...,
        description="매핑 실패 이유: 'no_hospital_in_region' | 'ambiguous_match' | 'region_mismatch' | 기타"
    )
    raw_row_index: Optional[int] = None
