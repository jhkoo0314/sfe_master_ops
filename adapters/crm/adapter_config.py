"""
CRM Adapter 컬럼 매핑 설정

핵심 원칙:
  - Adapter는 "어떤 데이터가 와도 공통 스키마로 번역하는 번역기"다.
  - 회사마다 컬럼명이 다르므로, 컬럼 매핑은 반드시 외부에서 주입한다.
  - 이 파일은 기본값이 없는 설정 계약(Config Contract)을 정의한다.
  - example_*() 메서드는 "이런 형태로 채우면 된다"는 예시일 뿐, 정답이 아니다.

사용법:
  config = HospitalAdapterConfig(
      hospital_id_col="내회사_병원코드",
      hospital_name_col="내회사_병원명",
      hospital_type_col="내회사_종별",
      region_key_col="내회사_시도",
      sub_region_key_col="내회사_시군구",
  )
  hospitals = load_hospital_master_from_file("path/to/file.xlsx", config=config)
"""

from typing import Optional
from pydantic import BaseModel


# ────────────────────────────────────────
# 1. 병원 마스터 Adapter 설정
# ────────────────────────────────────────

class HospitalAdapterConfig(BaseModel):
    """
    병원 마스터 파일의 컬럼 매핑 설정.

    어떤 병원 기준 파일이 와도 이 Config를 채워서 Adapter에 전달하면
    HospitalMaster(공통 스키마)로 변환됩니다.

    필수 필드: 반드시 실제 파일의 컬럼명을 넣어야 합니다.
    선택 필드: 파일에 없으면 None으로 두어도 됩니다.
    """
    # 필수
    hospital_id_col: str     # 병원 고유 ID 역할을 하는 컬럼명
    hospital_name_col: str   # 병원명 컬럼명
    hospital_type_col: str   # 병원 종별 컬럼명 (의원/병원/종합병원 등)
    region_key_col: str      # 광역 지역 코드 컬럼명 (시도 등)
    sub_region_key_col: str  # 세부 지역 코드 컬럼명 (시군구 등)

    # 선택 (없어도 HospitalMaster 생성 가능)
    address_col: Optional[str] = None     # 주소 컬럼명
    phone_col: Optional[str] = None       # 전화번호 컬럼명
    is_active_col: Optional[str] = None   # 영업 여부 컬럼명 (없으면 전체 True 처리)

    # 필터 옵션
    active_type_values: Optional[list[str]] = None
    """포함할 병원 종별 값 목록. None이면 전체 포함.
    예: ["의원", "병원", "종합병원"] 또는 ["clinic", "hospital"]
    """

    @classmethod
    def hira_example(cls) -> "HospitalAdapterConfig":
        """
        HIRA 병원정보서비스 실제 컬럼 기반 설정 (불변).

        파일: 1.병원정보서비스(2025.12.).xlsx
        실제 컬럼명 (파일 직접 확인):
          A: 암호화된요양기호  → hospital_id (암호화되어 있으나 파일 내 고유값)
          B: 요양기관명        → hospital_name
          D: 종별코드명        → hospital_type ('의원', '병원', '종합병원' 등)
          E: 시도명            → region_key  (한글 시도명, 예: '서울', '경남')
          F: 시군구명          → sub_region_key (한글 시군구명)
          I: 주소              → address
          J: 전화번호          → phone

        약국 데이터와 지역 매핑 시 주의:
          약국파일은 '시도코드명', '시군구코드명'(한글명) 사용
          → flow_builder에서 시도명/시군구명 한글 기준으로 매핑할 것
        """
        return cls(
            hospital_id_col="암호화된요양기호",
            hospital_name_col="요양기관명",
            hospital_type_col="종별코드명",
            region_key_col="시도명",
            sub_region_key_col="시군구명",
            address_col="주소",
            phone_col="전화번호",
            active_type_values=[
                "의원", "병원", "종합병원", "상급종합", "요양병원",
                "한의원", "한방병원", "치과의원", "치과병원",
            ],
        )

    @classmethod
    def english_col_example(cls) -> "HospitalAdapterConfig":
        """
        영문 컬럼 기반 내부 시스템 데이터 예시.
        ERP나 내부 DB에서 내려받은 파일이 이런 형태일 수 있습니다.
        """
        return cls(
            hospital_id_col="HOSP_CD",
            hospital_name_col="HOSP_NM",
            hospital_type_col="HOSP_TYPE",
            region_key_col="REGION_CD",
            sub_region_key_col="SUBREGION_CD",
            address_col="ADDR",
            phone_col="TEL",
        )

    @classmethod
    def fixture_example(cls) -> "HospitalAdapterConfig":
        """
        테스트/개발용 fixture 파일 컬럼 설정.
        tests/fixtures/ 아래 파일과 동일한 컬럼명 기준.
        """
        return cls(
            hospital_id_col="hospital_id",
            hospital_name_col="hospital_name",
            hospital_type_col="hospital_type",
            region_key_col="region_key",
            sub_region_key_col="sub_region_key",
            address_col="address",
            phone_col="phone",
        )

    @classmethod
    def hangyeol_account_example(cls) -> "HospitalAdapterConfig":
        """
        한결제약 회사 원본형 account master 파일 기준 설정.

        파일:
          data/raw/company_source/hangyeol_pharma/company/hangyeol_account_master.xlsx
        """
        return cls(
            hospital_id_col="account_id",
            hospital_name_col="account_name",
            hospital_type_col="account_type",
            region_key_col="region_key",
            sub_region_key_col="sub_region_key",
            address_col="address",
            active_type_values=["의원", "종합병원", "상급종합"],
        )


# ────────────────────────────────────────
# 2. 회사 마스터 Adapter 설정
# ────────────────────────────────────────

class CompanyMasterAdapterConfig(BaseModel):
    """
    회사 마스터 파일의 컬럼 매핑 설정.

    담당자-지점-병원 축을 연결하는 회사 내부 마스터 파일.
    회사마다 이 파일의 컬럼명이 완전히 다릅니다.
    이 Config를 채워서 Adapter에 전달하면 CompanyMasterStandard로 변환됩니다.

    중요: hospital_id는 직접 오는 경우도 있고, 병원명으로 HospitalMaster에서
    매핑해야 하는 경우도 있습니다. hospital_id_col을 지정하면 직접 매핑,
    아니면 hospital_name_col로 역매핑을 시도합니다.
    """
    # 담당자 정보 (필수)
    rep_id_col: str       # 담당자 고유 ID 컬럼명
    rep_name_col: str     # 담당자 이름 컬럼명

    # 지점/팀 정보 (필수)
    branch_id_col: str    # 지점 고유 ID 컬럼명
    branch_name_col: str  # 지점명 컬럼명

    # 병원 연결 (hospital_id_col 또는 hospital_name_col 중 하나 필수)
    hospital_name_col: str            # 병원명 컬럼명 (이름으로 hospital_id 역매핑)
    hospital_id_col: Optional[str] = None  # 병원 ID 컬럼명 (있으면 직접 매핑, 우선)

    # 선택 정보
    channel_type_col: Optional[str] = None  # 채널 구분 컬럼명 (없으면 "미분류")
    is_primary_col: Optional[str] = None    # 주담당 여부 컬럼명 (없으면 True)

    @classmethod
    def korean_example(cls) -> "CompanyMasterAdapterConfig":
        """
        한국 제약사 일반적인 마스터 파일 예시.
        실제 파일 컬럼명이 다르면 수정해서 사용하세요.
        """
        return cls(
            rep_id_col="담당자코드",
            rep_name_col="담당자명",
            branch_id_col="지점코드",
            branch_name_col="지점명",
            hospital_name_col="병원명",
            channel_type_col="채널구분",
            is_primary_col="주담당여부",
        )

    @classmethod
    def english_col_example(cls) -> "CompanyMasterAdapterConfig":
        """영문 컬럼 기반 시스템 예시."""
        return cls(
            rep_id_col="REP_ID",
            rep_name_col="REP_NM",
            branch_id_col="BRANCH_CD",
            branch_name_col="BRANCH_NM",
            hospital_name_col="HOSP_NM",
            hospital_id_col="HOSP_CD",  # 직접 ID 매핑
            channel_type_col="CHANNEL",
        )

    @classmethod
    def fixture_example(cls) -> "CompanyMasterAdapterConfig":
        """테스트/개발용 fixture 파일 기준 (hospital_id 직접 매핑)."""
        return cls(
            rep_id_col="rep_id",
            rep_name_col="rep_name",
            branch_id_col="branch_id",
            branch_name_col="branch_name",
            hospital_name_col="hospital_name",
            hospital_id_col="hospital_id",  # fixture는 ID 직접 제공
            channel_type_col="channel_type",
            is_primary_col="is_primary",
        )

    @classmethod
    def hangyeol_company_source_example(cls) -> "CompanyMasterAdapterConfig":
        """
        한결제약 회사 원본형 배정 파일 기준 설정.

        파일:
          data/raw/company_source/hangyeol_pharma/company/hangyeol_company_assignment_raw.xlsx
        """
        return cls(
            rep_id_col="영업사원코드",
            rep_name_col="영업사원명",
            branch_id_col="본부코드",
            branch_name_col="본부명",
            hospital_name_col="거래처명",
            hospital_id_col="거래처코드",
            channel_type_col="기관구분",
            is_primary_col="주담당여부",
        )


# ────────────────────────────────────────
# 3. CRM 활동 Adapter 설정
# ────────────────────────────────────────

class CrmActivityAdapterConfig(BaseModel):
    """
    CRM 활동 파일의 컬럼 매핑 설정.

    회사 CRM 시스템에서 내려받은 활동 데이터.
    Salesforce, Veeva CRM, 자체 CRM 등 시스템마다 컬럼명이 다릅니다.
    이 Config를 채워서 Adapter에 전달하면 CrmStandardActivity로 변환됩니다.
    """
    # 핵심 키 컬럼 (필수)
    rep_id_col: str           # 활동 담당자 ID 컬럼명
    hospital_name_col: str    # 방문 병원명 컬럼명 (company_master와 연결)
    activity_date_col: str    # 활동 일자 컬럼명

    # 활동 상세 (필수)
    activity_type_col: str    # 활동 유형 컬럼명 (방문/전화 등)

    # 선택 컬럼
    visit_count_col: Optional[str] = None        # 방문 건수 컬럼명 (없으면 1로 처리)
    has_detail_call_col: Optional[str] = None    # 디테일링 여부 컬럼명 (없으면 False)
    products_mentioned_col: Optional[str] = None # 제품 언급 컬럼명 (쉼표 구분)
    notes_col: Optional[str] = None              # 비고 컬럼명
    trust_level_col: Optional[str] = None
    sentiment_score_col: Optional[str] = None
    quality_factor_col: Optional[str] = None
    impact_factor_col: Optional[str] = None
    activity_weight_col: Optional[str] = None
    weighted_activity_score_col: Optional[str] = None
    next_action_text_col: Optional[str] = None

    # 날짜 형식 설정
    date_format: str = "%Y-%m-%d"
    """
    날짜 컬럼 형식. 예:
      - "%Y-%m-%d"  → 2025-01-08
      - "%Y%m%d"    → 20250108
      - "%d/%m/%Y"  → 08/01/2025
    """

    # 활동 유형 표준화 매핑
    activity_type_map: Optional[dict[str, str]] = None
    """
    회사별 활동 유형 표현 → 공통 표현 매핑.
    None이면 기본 매핑 사용.
    예: {"F2F": "방문", "Phone call": "전화", "e-detail": "디지털"}
    """

    @classmethod
    def korean_crm_example(cls) -> "CrmActivityAdapterConfig":
        """
        한국 제약사 일반 CRM 시스템 예시.
        실제 파일 컬럼명이 다르면 수정해서 사용하세요.
        """
        return cls(
            rep_id_col="담당자코드",
            hospital_name_col="방문병원명",
            activity_date_col="활동일자",
            activity_type_col="활동유형",
            visit_count_col="방문건수",
            has_detail_call_col="디테일여부",
            products_mentioned_col="언급제품",
            notes_col="비고",
        )

    @classmethod
    def veeva_crm_example(cls) -> "CrmActivityAdapterConfig":
        """
        Veeva CRM 내려받기 파일 예시.
        """
        return cls(
            rep_id_col="Owner_EMP_ID",
            hospital_name_col="Account_Name",
            activity_date_col="Call_Date",
            activity_type_col="Call_Type",
            has_detail_call_col="Is_Detail_Call",
            products_mentioned_col="Products_Discussed",
            notes_col="Comments",
            date_format="%m/%d/%Y",
            activity_type_map={
                "Face to Face": "방문",
                "Phone": "전화",
                "Email": "이메일",
                "Remote": "화상",
                "Group": "행사",
            },
        )

    @classmethod
    def fixture_example(cls) -> "CrmActivityAdapterConfig":
        """테스트/개발용 fixture 파일 기준."""
        return cls(
            rep_id_col="rep_id",
            hospital_name_col="hospital_name",
            activity_date_col="activity_date",
            activity_type_col="activity_type",
            visit_count_col="visit_count",
            has_detail_call_col="has_detail_call",
            products_mentioned_col="products_mentioned",
            notes_col="notes",
        )

    @classmethod
    def hangyeol_crm_source_example(cls) -> "CrmActivityAdapterConfig":
        """
        한결제약 회사 원본형 CRM 파일 기준 설정.

        파일:
          data/raw/company_source/hangyeol_pharma/crm/hangyeol_crm_activity_raw.xlsx
        """
        return cls(
            rep_id_col="영업사원코드",
            hospital_name_col="방문기관",
            activity_date_col="실행일",
            activity_type_col="액션유형",
            visit_count_col="방문횟수",
            has_detail_call_col="상세콜여부",
            products_mentioned_col="언급브랜드",
            notes_col="활동메모",
            trust_level_col="신뢰등급",
            sentiment_score_col="정서점수",
            quality_factor_col="품질계수",
            impact_factor_col="영향계수",
            activity_weight_col="행동가중치",
            weighted_activity_score_col="가중활동점수",
            next_action_text_col="차기액션",
            activity_type_map={
                "접근": "방문",
                "컨택": "전화",
                "대면": "방문",
                "pt": "행사",
                "시연": "디지털",
                "니즈환기": "방문",
                "클로징": "방문",
                "피드백": "전화",
            },
        )
