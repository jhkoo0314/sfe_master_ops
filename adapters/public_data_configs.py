"""
공공데이터 기반 Adapter 설정 (불변 규칙)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
이 파일은 공공데이터 3종의 실제 컬럼 구조를 기반으로 작성됩니다.
공공데이터는 정부 규격으로 컬럼명이 고정되어 있습니다.
한 번 정의하면 변하지 않으므로 '불변 규칙(Immutable Rules)'입니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

데이터 출처:
  1. 병원정보서비스 (심평원) - xlsx
     컬럼: 암호화된요양기호, 요양기관명, 종별코드, 종별코드명,
            시도명, 시군구명, 읍면동, 우편번호, 주소, 전화번호, ...

  2. 약국정보서비스 (심평원) - xlsx
     컬럼: 암호화요양기호(Base64 불가), 요양기관명, 종별코드,
            종별코드명, 시도코드, 시도코드명, 시군구코드, 시군구코드명,
            읍면동, 우편번호, 주소, 전화번호, 개설일자, 좌표X, 좌표Y

  3. 전국의약품도매업소표준데이터 (data.go.kr) - csv
     컬럼: facility_name(시설명), business_type(업종명),
            road_address(소재지도로명주소), jibun_address(소재지지번주소),
            latitude(위도), longitude(경도), business_status(영업상태명),
            has_transport_vehicle(운반용차량보유여부),
            has_storage_facility(저장시설보유여부), phone(전화번호),
            supervising_agency(관리기관명), as_of_date(데이터기준일자),
            provider_org_code(제공기관코드), provider_org_name(제공기관명)

핵심 발견 사항:
  - 병원: 암호화된요양기호 → 암호화되어 있지만 고유 ID 역할 가능 (변환 필요)
  - 약국: 암호화요양기호 → Base64+인코딩 불가 → pharmacy_id는 범용 규칙으로 생성해야 함
  - 도매: 고유 ID 없음 → wholesaler_id는 범용 규칙(이름+지역)으로 생성해야 함
"""

from adapters.crm.adapter_config import HospitalAdapterConfig
from adapters.prescription.adapter_config import (
    PrescriptionMasterAdapterConfig,
    CompanyPrescriptionAdapterConfig,
)


# ────────────────────────────────────────
# 1. 병원정보서비스 (심평원) - 불변 Config
# ────────────────────────────────────────

class HospitalMasterPublicConfig:
    """
    병원정보서비스 (심평원) 실제 컬럼 기반 불변 Config.

    파일: 1.병원정보서비스(2025.12.).xlsx
    출처: 건강보험심사평가원 (요양기관현황)

    컬럼 매핑 근거:
      A: 암호화된요양기호 → hospital_id (암호화 형태지만 고유값으로 사용)
      B: 요양기관명       → hospital_name
      C: 종별코드         → (내부 코드, 참조용)
      D: 종별코드명       → hospital_type ('의원', '병원', '종합병원' 등)
      E: 시도명           → region_key (시도명 그대로. 코드 없음)
      F: 시군구명         → sub_region_key (시군구명 그대로)
      G: 읍면동           → (참조용)
      H: 우편번호         → postal_code (pharmacy_id 생성 보조)
      I: 주소             → address
      J: 전화번호         → phone
      K: 홈페이지         → (무시)
      L: 개설일자         → (무시)
      ... 의사수 등 인원 관련 컬럼들 ...

    주의:
      시도명/시군구명을 코드가 아닌 한글 이름 그대로 key로 사용.
      → 약국/도매 데이터와 매핑 시 동일 기준 필요 (아래 참조)
    """

    @staticmethod
    def get_adapter_config() -> HospitalAdapterConfig:
        return HospitalAdapterConfig(
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

    # 실제 종별코드명 전체 목록 (참조용)
    ALL_HOSPITAL_TYPES = [
        "의원", "병원", "종합병원", "상급종합",
        "요양병원", "정신병원",
        "한의원", "한방병원",
        "치과의원", "치과병원",
        "보건소", "보건지소", "보건진료소",
        "조산원", "산후조리원",
    ]

    # 영업 활성 종별만 포함할 때 사용하는 필터
    ACTIVE_CLINIC_TYPES = ["의원", "한의원", "치과의원"]
    ACTIVE_HOSPITAL_TYPES = ["병원", "종합병원", "상급종합", "요양병원"]


# ────────────────────────────────────────
# 2. 약국정보서비스 (심평원) - 불변 Config
# ────────────────────────────────────────

class PharmacyMasterPublicConfig:
    """
    약국정보서비스 (심평원) 실제 컬럼 기반 불변 Config.

    파일: 2.약국정보서비스(2025.12.).xlsx
    출처: 건강보험심사평가원

    실제 컬럼 (파일 직접 확인):
      A: 암호화요양기호     → 사용 불가 (Base64 암호화, 재현 불가)
      B: 요양기관명         → pharmacy_name (약국명)
      C: 종별코드           → '81' (모두 약국, 필터 불필요)
      D: 종별코드명         → '약국' (고정)
      E: 시도코드           → sido_code (6자리, 예: 210000=부산, 110000=서울)
      F: 시도코드명         → sido_name (시도명, 예: '부산')
      G: 시군구코드         → sigungu_code (6자리)
      H: 시군구코드명       → sigungu_name (시군구명)
      I: 읍면동             → eup_myeon_dong
      J: 우편번호           → zip_code (5자리)
      K: 주소               → pharmacy_addr
      L: 전화번호           → pharmacy_tel
      M: 개설일자           → 엑셀 날짜 숫자 (변환 필요)
      N: 좌표(X)            → 경도 longitude
      O: 좌표(Y)            → 위도 latitude

    ★ pharmacy_id 생성 전략:
      암호화요양기호는 재현 불가 → id_rules.generate_pharmacy_id() 사용:
      pharmacy_id = PH_{sigungu_code}_{normalized_pharmacy_name}_{zip_3}

    ★ 병원-약국 지역 매핑 시 주의:
      병원파일: 시도명(한글), 시군구명(한글)
      약국파일: 시도코드(6자리 숫자), 시도코드명(한글), 시군구코드(6자리 숫자), 시군구코드명(한글)
      → flow_builder에서 매핑 시 '코드명(한글)' 기준으로 맞춰야 함
    """

    ACTUAL_COLUMNS = {
        "pharmacy_name": "요양기관명",          # B열
        "pharmacy_type_code": "종별코드",        # C열 (항상 '81')
        "pharmacy_type_name": "종별코드명",      # D열 (항상 '약국')
        "sido_code": "시도코드",                 # E열 (6자리 숫자)
        "sido_name": "시도코드명",               # F열 (한글 시도명)
        "sigungu_code": "시군구코드",            # G열 (6자리 숫자)
        "sigungu_name": "시군구코드명",          # H열 (한글 시군구명)
        "eup_myeon_dong": "읍면동",              # I열
        "zip_code": "우편번호",                  # J열
        "pharmacy_addr": "주소",                 # K열
        "pharmacy_tel": "전화번호",              # L열
    }

    # 시도코드 → 시도명 매핑 (약국-병원 지역 연결에 사용)
    SIDO_CODE_TO_NAME = {
        "110000": "서울", "210000": "부산", "220000": "대구",
        "230000": "인천", "240000": "광주", "250000": "대전",
        "260000": "울산", "290000": "세종",
        "310000": "경기", "320000": "강원",
        "330000": "충북", "340000": "충남",
        "350000": "전북", "360000": "전남",
        "370000": "경북", "380000": "경남",
        "390000": "제주",
    }

    @staticmethod
    def get_id_rule_cols() -> dict:
        """pharmacy_id 생성에 필요한 컬럼 이름 반환."""
        return {
            "pharmacy_name_col": "요양기관명",
            "sigungu_code_col": "시군구코드",    # sub_region_key로 사용
            "sido_code_col": "시도코드",          # region_key로 사용
            "zip_code_col": "우편번호",
        }


# ────────────────────────────────────────
# 3. 전국의약품도매업소 (data.go.kr) - 불변 Config
# ────────────────────────────────────────

class WholesaleMasterPublicConfig:
    """
    전국의약품도매업소표준데이터 실제 컬럼 기반 불변 Config.

    파일: 3. 전국의약품도매업소표준데이터.csv
    출처: 공공데이터포털 (data.go.kr)
    인코딩: UTF-8-BOM

    실제 컬럼 (파일 직접 확인):
      [0]  facility_name(시설명)             → wholesaler_name
      [1]  business_type(업종명)             → wholesaler_type ('한약도매', '의약품도매' 등)
      [2]  road_address(소재지도로명주소)     → road_address (도로명주소)
      [3]  jibun_address(소재지지번주소)      → jibun_address
      [4]  latitude(위도)                    → latitude (위도)
      [5]  longitude(경도)                   → longitude (경도)
      [6]  business_status(영업상태명)        → business_status ('영업' 등)
      [7]  has_transport_vehicle(운반용차량보유여부) → Y/N
      [8]  has_storage_facility(저장시설보유여부)   → Y/N
      [9]  phone(전화번호)                   → phone
      [10] supervising_agency(관리기관명)    → supervising_agency (시도 관할청)
      [11] as_of_date(데이터기준일자)         → 데이터 기준일
      [12] provider_org_code(제공기관코드)   → 제공기관 코드
      [13] provider_org_name(제공기관명)     → 제공기관명 (시도명과 동일)

    ★ wholesale_id 생성 전략:
      도매업소 고유 ID 없음 → id_rules.generate_wholesaler_id() 사용:
      wholesaler_id = WS_{region_key}_{normalized_name}

    ★ 지역 추출 방법:
      도로명주소에서 시도명 추출 OR supervising_agency에서 추출
      예: supervising_agency='경상남도 창원시' → region_key='경상남도'
          或 provider_org_name으로 추출

    ★ 업종 필터:
      의약품도매만 사용, 한약도매 제외 여부는 비즈니스 규칙에 따름
    """

    ACTUAL_COLUMNS = {
        "facility_name": "facility_name(시설명)",
        "business_type": "business_type(업종명)",
        "road_address": "road_address(소재지도로명주소)",
        "jibun_address": "jibun_address(소재지지번주소)",
        "latitude": "latitude(위도)",
        "longitude": "longitude(경도)",
        "business_status": "business_status(영업상태명)",
        "phone": "phone(전화번호)",
        "supervising_agency": "supervising_agency(관리기관명)",
        "as_of_date": "as_of_date(데이터기준일자)",
        "provider_org_name": "provider_org_name(제공기관명)",
    }

    # 의약품 도매 업종명 (이 값만 포함)
    PHARMA_WHOLESALE_TYPES = ["의약품도매"]
    # 한약 포함 시: ["의약품도매", "한약도매"]

    @staticmethod
    def extract_region_from_address(road_address: str) -> str:
        """
        도로명주소에서 시도명을 추출합니다.
        예: '경상남도 창원시 진해구 ...' → '경상남도'
        """
        if not road_address:
            return "미확인"
        parts = road_address.strip().split()
        if parts:
            sido = parts[0]
            # 약칭 처리
            if sido in ("서울특별시",): return "서울"
            if sido in ("부산광역시",): return "부산"
            if sido in ("대구광역시",): return "대구"
            if sido in ("인천광역시",): return "인천"
            if sido in ("광주광역시",): return "광주"
            if sido in ("대전광역시",): return "대전"
            if sido in ("울산광역시",): return "울산"
            if sido in ("세종특별자치시",): return "세종"
            if sido in ("경기도",): return "경기"
            if sido in ("강원특별자치도", "강원도"): return "강원"
            if sido in ("충청북도",): return "충북"
            if sido in ("충청남도",): return "충남"
            if sido in ("전라북도", "전북특별자치도"): return "전북"
            if sido in ("전라남도",): return "전남"
            if sido in ("경상북도",): return "경북"
            if sido in ("경상남도",): return "경남"
            if sido in ("제주특별자치도",): return "제주"
            return sido
        return "미확인"
