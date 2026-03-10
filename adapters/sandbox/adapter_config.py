"""
Sandbox Adapter 컬럼 매핑 설정

원칙:
  - 매출/목표 데이터도 회사마다 컬럼명이 다르다.
  - Config를 주입받아야만 Adapter가 동작한다 (기본값 없음).
  - hospital_id_col 또는 hospital_name_col 중 하나는 반드시 있어야 한다.
    (hospital_name_col만 있으면 HospitalMaster에서 역매핑)
"""

from typing import Optional
from pydantic import BaseModel


# ────────────────────────────────────────
# 1. 매출(Sales) Adapter 설정
# ────────────────────────────────────────

class SalesAdapterConfig(BaseModel):
    """
    회사 매출 실적 파일 컬럼 매핑.

    필수: rep_id_col, metric_month_or_date_col, product_col, amount_col
    병원 연결: hospital_id_col 또는 hospital_name_col 중 하나 필수
    """
    # 병원 연결 (둘 중 하나 필수)
    hospital_id_col: Optional[str] = None       # 병원 ID 직접 있는 경우
    hospital_name_col: Optional[str] = None     # 병원명으로 역매핑

    # 담당자
    rep_id_col: str

    # 날짜/기간
    metric_month_col: Optional[str] = None      # YYYYMM 형태 컬럼
    sales_date_col: Optional[str] = None        # 날짜 컬럼 (metric_month 없으면 변환)
    date_format: str = "%Y-%m-%d"

    # 제품
    product_id_col: Optional[str] = None        # 제품 ID 직접
    product_name_col: Optional[str] = None      # 제품명 (없으면 product_id로 사용)

    # 금액/수량
    amount_col: str
    quantity_col: Optional[str] = None

    # 채널
    channel_col: Optional[str] = None

    @classmethod
    def korean_example(cls) -> "SalesAdapterConfig":
        """한국 제약사 일반 매출 파일 예시."""
        return cls(
            hospital_name_col="병원명",
            rep_id_col="담당자코드",
            sales_date_col="실적일자",
            product_name_col="제품명",
            amount_col="매출금액",
            quantity_col="수량",
            channel_col="채널",
        )

    @classmethod
    def english_col_example(cls) -> "SalesAdapterConfig":
        """영문 컬럼 예시."""
        return cls(
            hospital_id_col="HOSP_ID",
            rep_id_col="REP_ID",
            metric_month_col="MONTH",
            product_id_col="PROD_CD",
            amount_col="SALES_AMT",
            quantity_col="SALES_QTY",
        )

    @classmethod
    def fixture_example(cls) -> "SalesAdapterConfig":
        """테스트 fixture 기준."""
        return cls(
            hospital_id_col="hospital_id",
            rep_id_col="rep_id",
            metric_month_col="metric_month",
            product_id_col="product_id",
            amount_col="sales_amount",
            quantity_col="sales_quantity",
            channel_col="channel",
        )


# ────────────────────────────────────────
# 2. 목표(Target) Adapter 설정
# ────────────────────────────────────────

class TargetAdapterConfig(BaseModel):
    """
    회사 목표 파일 컬럼 매핑.

    목표는 일반적으로 담당자 + 월 + 제품 단위.
    병원 단위 목표인 경우 hospital_id_col 또는 hospital_name_col 추가.
    """
    # 담당자
    rep_id_col: str

    # 날짜/기간
    metric_month_col: Optional[str] = None
    target_date_col: Optional[str] = None
    date_format: str = "%Y-%m-%d"

    # 제품
    product_id_col: Optional[str] = None
    product_name_col: Optional[str] = None

    # 목표액
    target_amount_col: str

    # 병원 연결 (선택 - 병원 단위 목표인 경우)
    hospital_id_col: Optional[str] = None
    hospital_name_col: Optional[str] = None

    @classmethod
    def korean_example(cls) -> "TargetAdapterConfig":
        """한국 제약사 일반 목표 파일 예시."""
        return cls(
            rep_id_col="담당자코드",
            metric_month_col="기준월",
            product_name_col="제품명",
            target_amount_col="목표금액",
        )

    @classmethod
    def fixture_example(cls) -> "TargetAdapterConfig":
        """테스트 fixture 기준."""
        return cls(
            rep_id_col="rep_id",
            metric_month_col="metric_month",
            product_id_col="product_id",
            target_amount_col="target_amount",
            hospital_id_col="hospital_id",
        )
