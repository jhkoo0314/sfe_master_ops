"""
CRM 모듈 내부 Pydantic 스키마 정의

이 파일은 CRM 흐름 안에서 사용하는 데이터 구조를 정의합니다.

흐름:
  hospital_public (공공 파일) -> HospitalMaster
  company_raw (회사 파일) -> CompanyMasterStandard
  crm_raw (CRM 활동 파일) -> CrmStandardActivity
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


# ────────────────────────────────────────
# 1. HospitalMaster - 공공 기준 병원 마스터
# ────────────────────────────────────────

class HospitalMaster(BaseModel):
    """
    공공 기준 병원 마스터.
    모든 모듈이 재사용하는 hospital_id 기준 단위.
    HIRA(건강보험심사평가원) 또는 유사 공공 데이터 기반.
    """
    hospital_id: str = Field(..., description="공공 기준 병원 고유 ID (예: HIRA 요양기관번호)")
    hospital_name: str = Field(..., description="병원명 (공식 명칭)")
    hospital_type: str = Field(..., description="병원 종별 (의원/병원/종합병원/상급종합/치과/한방 등)")
    region_key: str = Field(..., description="시도 코드 (예: 11=서울, 26=부산)")
    sub_region_key: str = Field(..., description="시군구 코드 (예: 11010=서울 종로구)")
    address: Optional[str] = Field(None, description="도로명주소 또는 지번주소")
    phone: Optional[str] = Field(None, description="대표 전화번호")
    is_active: bool = Field(True, description="현재 운영 중 여부")


# ────────────────────────────────────────
# 2. CompanyMasterStandard - 회사 마스터 표준화
# ────────────────────────────────────────

class CompanyMasterStandard(BaseModel):
    """
    회사 마스터 표준화 결과.
    담당자(rep) - 지점(branch) - 병원(hospital) 축을 연결.
    adapter가 회사 raw Excel을 이 구조로 변환.
    """
    rep_id: str = Field(..., description="담당자 고유 ID (회사 내부 기준)")
    rep_name: str = Field(..., description="담당자 이름")
    branch_id: str = Field(..., description="지점/팀 고유 ID")
    branch_name: str = Field(..., description="지점/팀명")
    hospital_id: str = Field(..., description="담당 병원 ID (HospitalMaster.hospital_id 재사용)")
    hospital_name: str = Field(..., description="담당 병원명 (매핑 검증용)")
    channel_type: str = Field(..., description="담당 채널 (의원/병원/종합병원 등)")
    is_primary: bool = Field(True, description="주담당 여부 (True=주담당, False=공동담당)")


# ────────────────────────────────────────
# 3. CrmStandardActivity - CRM 표준 활동 데이터
# ────────────────────────────────────────

class CrmStandardActivity(BaseModel):
    """
    CRM raw 활동 데이터를 표준화한 결과.
    adapter가 회사 CRM 파일을 이 구조로 변환.

    핵심 키: hospital_id, rep_id, activity_date, metric_month
    """
    hospital_id: str = Field(..., description="방문 병원 ID (HospitalMaster 기준)")
    rep_id: str = Field(..., description="활동 담당자 ID")
    branch_id: str = Field(..., description="담당자 소속 지점 ID")
    activity_date: date = Field(..., description="활동 일자")
    metric_month: str = Field(..., description="집계 기준 월 (YYYYMM 형식)")
    activity_type: str = Field(..., description="활동 유형 (방문/전화/이메일/행사/디지털 등)")
    visit_count: int = Field(default=1, ge=0, description="방문 건수")
    products_mentioned: list[str] = Field(default_factory=list, description="언급된 제품 목록")
    has_detail_call: bool = Field(False, description="상세 설명(디테일링) 여부")
    notes: Optional[str] = Field(None, description="활동 비고")
    rep_name: Optional[str] = Field(None, description="담당자 이름")
    branch_name: Optional[str] = Field(None, description="지점 이름")
    trust_level: Optional[str] = Field(None, description="입력 신뢰 등급")
    sentiment_score: Optional[float] = Field(None, description="고객 반응 점수")
    quality_factor: Optional[float] = Field(None, description="활동 품질 계수")
    impact_factor: Optional[float] = Field(None, description="활동 영향 계수")
    activity_weight: Optional[float] = Field(None, description="행동 유형별 가중치")
    weighted_activity_score: Optional[float] = Field(None, description="가중 활동 점수")
    next_action_text: Optional[str] = Field(None, description="차기 액션 텍스트")
    raw_row_index: Optional[int] = Field(None, description="원본 파일 행 번호 (역추적용)")
