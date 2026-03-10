"""
Prescription Adapter 컬럼 매핑 설정

핵심 원칙:
  - 회사 데이터 없는 가정 하에 설계된다.
  - 컬럼 매핑은 기본값이 없다 (필수 주입).
  - example_*() 메서드는 "이런 형태로 채우면 된다"는 참고용 예시.
  - 이 Config를 바꾸면 어떤 회사의 도매출고/약국구입 파일에도 대응 가능.

핵심 차이점 (CRM과의 비교):
  - CRM: 담당자가 병원을 방문한 기록 (명시적 연결)
  - Prescription: 약이 도매→약국→(추론)→병원으로 흐른 기록 (연결 추론 필요)
  → 따라서 pharmacy 위치(지역, 우편번호) 컬럼이 Prescription Config에서 중요
"""

from typing import Optional
from pydantic import BaseModel


# ────────────────────────────────────────
# 1. 제품 마스터 Adapter 설정
# ────────────────────────────────────────

class PrescriptionMasterAdapterConfig(BaseModel):
    """
    제품/성분 기준 파일(공공 약가 데이터 등)의 컬럼 매핑 설정.

    어떤 제품 기준 파일이 와도 이 Config를 채워서
    PrescriptionMaster (공통 계약)로 변환합니다.
    """
    # 필수
    product_name_col: str      # 제품명 컬럼
    dosage_form_col: str       # 제형 컬럼

    # 선택 (있을수록 product_id 정확도 상승)
    ingredient_code_col: Optional[str] = None   # 성분코드 컬럼
    ingredient_name_col: Optional[str] = None   # 성분명 컬럼
    strength_col: Optional[str] = None          # 함량 컬럼
    atc_code_col: Optional[str] = None          # ATC코드 컬럼
    manufacturer_col: Optional[str] = None      # 제조사 컬럼
    is_listed_col: Optional[str] = None         # 급여등재여부 컬럼

    @classmethod
    def hira_drug_list_example(cls) -> "PrescriptionMasterAdapterConfig":
        """
        심평원 의약품 목록 파일 예시.
        """
        return cls(
            product_name_col="제품명",
            dosage_form_col="제형",
            ingredient_code_col="성분코드",
            ingredient_name_col="성분명",
            strength_col="함량",
            manufacturer_col="제조사",
            is_listed_col="급여구분",
        )

    @classmethod
    def english_col_example(cls) -> "PrescriptionMasterAdapterConfig":
        """영문 컬럼 기반 내부 시스템 예시."""
        return cls(
            product_name_col="PROD_NM",
            dosage_form_col="FORM",
            ingredient_code_col="INGR_CD",
            ingredient_name_col="INGR_NM",
            strength_col="STRENGTH",
            atc_code_col="ATC_CD",
            manufacturer_col="MFR_NM",
        )

    @classmethod
    def fixture_example(cls) -> "PrescriptionMasterAdapterConfig":
        """테스트/개발용 fixture 기준."""
        return cls(
            product_name_col="product_name",
            dosage_form_col="dosage_form",
            ingredient_code_col="ingredient_code",
            ingredient_name_col="ingredient_name",
            strength_col="strength",
            manufacturer_col="manufacturer",
        )


# ────────────────────────────────────────
# 2. 회사 처방/출고 Adapter 설정
# ────────────────────────────────────────

class CompanyPrescriptionAdapterConfig(BaseModel):
    """
    회사 처방 데이터 파일의 컬럼 매핑 설정.

    도매출고 파일(도매→약국)과 약국구입 파일(약국→병원)을 모두 지원.
    record_type_value로 유형을 명시하면 하나의 Config로 처리 가능.

    가장 중요한 컬럼:
      - pharmacy_name_col + pharmacy_sub_region_col + pharmacy_postal_col
        → pharmacy_id 생성의 재료 (id_rules.generate_pharmacy_id)
      - wholesaler_name_col + wholesaler_region_col
        → wholesaler_id 생성의 재료 (id_rules.generate_wholesaler_id)
    """
    # 기록 유형 설정
    record_type_value: str = "wholesaler_shipment"
    """
    이 파일의 기록 유형:
      - "wholesaler_shipment": 도매→약국 출고 데이터
      - "pharmacy_purchase": 약국→병원 구입 데이터
    """

    # 도매상 정보 (필수)
    wholesaler_name_col: str    # 도매상명 컬럼
    wholesaler_region_col: str  # 도매상 시도코드 컬럼 (wholesaler_id 생성용)

    # 약국 정보 (필수 - pharmacy_id 생성 재료)
    pharmacy_name_col: str           # 약국명 컬럼
    pharmacy_sub_region_col: str     # 약국 시군구코드 컬럼 (pharmacy_id 생성 필수)
    pharmacy_region_col: str         # 약국 시도코드 컬럼

    # 약국 보조 정보 (선택 - pharmacy_id 정확도 향상)
    pharmacy_postal_col: Optional[str] = None   # 약국 우편번호 컬럼

    # 제품 정보 (필수)
    product_name_col: str       # 제품명 컬럼

    # 제품 보조 정보 (선택 - product_id 정확도 향상)
    ingredient_code_col: Optional[str] = None  # 성분코드 컬럼
    dosage_form_col: Optional[str] = None      # 제형 컬럼

    # 수량/금액 (필수)
    quantity_col: str           # 수량 컬럼

    # 선택 컬럼
    amount_col: Optional[str] = None           # 금액 컬럼
    unit_col: Optional[str] = None             # 단위 컬럼
    transaction_date_col: Optional[str] = None # 거래일자 컬럼
    metric_month_col: Optional[str] = None     # 집계월 컬럼 (YYYYMM)
    hospital_name_col: Optional[str] = None    # 병원명 컬럼 (있으면 직접 매핑 가능)

    # 날짜 형식
    date_format: str = "%Y-%m-%d"

    @classmethod
    def wholesaler_shipment_korean_example(cls) -> "CompanyPrescriptionAdapterConfig":
        """
        도매회사 출고 데이터 한국어 컬럼 예시 (도매→약국).
        """
        return cls(
            record_type_value="wholesaler_shipment",
            wholesaler_name_col="도매상명",
            wholesaler_region_col="도매시도코드",
            pharmacy_name_col="약국명",
            pharmacy_region_col="약국시도코드",
            pharmacy_sub_region_col="약국시군구코드",
            pharmacy_postal_col="약국우편번호",
            product_name_col="제품명",
            ingredient_code_col="성분코드",
            dosage_form_col="제형",
            quantity_col="출고수량",
            amount_col="출고금액",
            unit_col="단위",
            transaction_date_col="출고일자",
        )

    @classmethod
    def pharmacy_purchase_korean_example(cls) -> "CompanyPrescriptionAdapterConfig":
        """
        약국 구입 데이터 한국어 컬럼 예시 (약국→병원).
        """
        return cls(
            record_type_value="pharmacy_purchase",
            wholesaler_name_col="공급도매상명",
            wholesaler_region_col="도매상지역코드",
            pharmacy_name_col="구입약국명",
            pharmacy_region_col="약국시도",
            pharmacy_sub_region_col="약국시군구",
            pharmacy_postal_col="약국우편번호",
            product_name_col="품목명",
            ingredient_code_col="성분코드",
            quantity_col="구입수량",
            amount_col="구입금액",
            transaction_date_col="구입일자",
            hospital_name_col="처방병원명",
        )

    @classmethod
    def english_col_example(cls) -> "CompanyPrescriptionAdapterConfig":
        """영문 컬럼 기반 ERP/BI 시스템 예시."""
        return cls(
            record_type_value="wholesaler_shipment",
            wholesaler_name_col="WS_NAME",
            wholesaler_region_col="WS_REGION",
            pharmacy_name_col="PH_NAME",
            pharmacy_region_col="PH_REGION",
            pharmacy_sub_region_col="PH_SUBREGION",
            pharmacy_postal_col="PH_POSTAL",
            product_name_col="PROD_NM",
            ingredient_code_col="INGR_CD",
            quantity_col="QTY",
            amount_col="AMT",
            transaction_date_col="TRX_DATE",
            date_format="%Y%m%d",
        )

    @classmethod
    def fixture_example(cls) -> "CompanyPrescriptionAdapterConfig":
        """테스트/개발용 fixture 기준."""
        return cls(
            record_type_value="wholesaler_shipment",
            wholesaler_name_col="wholesaler_name",
            wholesaler_region_col="wholesaler_region_key",
            pharmacy_name_col="pharmacy_name",
            pharmacy_region_col="pharmacy_region_key",
            pharmacy_sub_region_col="pharmacy_sub_region_key",
            pharmacy_postal_col="pharmacy_postal_code",
            product_name_col="product_name",
            ingredient_code_col="ingredient_code",
            dosage_form_col="dosage_form",
            quantity_col="quantity",
            amount_col="amount",
            transaction_date_col="transaction_date",
            hospital_name_col="hospital_name",
        )

    @classmethod
    def hangyeol_fact_ship_example(cls) -> "CompanyPrescriptionAdapterConfig":
        """
        한결제약 회사 원본형 fact_ship 파일 기준 설정.

        파일:
          data/raw/company_source/hangyeol_pharma/company/hangyeol_fact_ship_raw.csv
        """
        return cls(
            record_type_value="wholesaler_shipment",
            wholesaler_name_col="wholesaler_name (도매상명)",
            wholesaler_region_col="wholesaler_region_key (도매시도)",
            pharmacy_name_col="pharmacy_name (약국명)",
            pharmacy_region_col="pharmacy_region_key (약국시도)",
            pharmacy_sub_region_col="pharmacy_sub_region_key (약국시군구)",
            pharmacy_postal_col="pharmacy_account_id (약국거래처ID)",
            product_name_col="brand (브랜드)",
            ingredient_code_col="sku (SKU)",
            dosage_form_col="formulation (제형)",
            quantity_col="qty (수량)",
            amount_col="amount_ship (출고금액)",
            unit_col="pack_size (포장단위)",
            transaction_date_col="ship_date (출고일)",
        )
