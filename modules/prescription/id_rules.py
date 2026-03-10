"""
Prescription/공공마스터 범용 ID 생성 규칙 (Universal Key Rules)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
공공데이터 3종 실제 구조 분석 결과를 반영한 ID 생성 규칙:

  병원  : 암호화된요양기호 → 고유값이므로 hospital_id로 직접 사용
  약국  : 암호화요양기호 → Base64 재현 불가 → 이름+시군구코드+우편번호로 생성
  도매  : 고유 ID 없음 → 이름+주소에서 추출한 시도명으로 생성

rule이 고정되면:
  - A회사 도매출고 파일의 '서울도매A' + '서울' → WS_서울_서울도매a
  - B회사 약국구입 파일의 '서울도매A' + '서울' → WS_서울_서울도매a  (동일!)
  - 회사가 달라도 같은 약국/도매를 일관되게 식별 가능
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import re
import unicodedata


# ────────────────────────────────────────
# 내부 유틸: 이름 정규화
# ────────────────────────────────────────

def _normalize_name(name: str) -> str:
    """
    이름 문자열을 ID 생성에 적합하게 정규화합니다.

    규칙:
      - 유니코드 NFC 정규화
      - 공백 제거
      - 괄호/특수문자 제거
      - 소문자 변환 (영문)
      - 한글은 그대로 유지

    예:
      "서울 중앙 약국(직영)" → "서울중앙약국직영"
      "지오영(주)"           → "지오영주"
    """
    if not name:
        return "unknown"
    name = unicodedata.normalize("NFC", str(name).strip())
    name = re.sub(r"[\s\W]+", "", name)
    return name.lower()


def _extract_sido_from_address(road_address: str) -> str:
    """
    도로명주소 또는 지번주소 첫 단어에서 시도명을 추출합니다.
    공공데이터 도매파일에서 활용.

    예:
      '경상남도 창원시 진해구 ...' → '경남'
      '서울특별시 종로구 ...'     → '서울'
    """
    SIDO_MAP = {
        "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
        "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
        "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
        "강원특별자치도": "강원", "강원도": "강원",
        "충청북도": "충북", "충청남도": "충남",
        "전라북도": "전북", "전북특별자치도": "전북", "전라남도": "전남",
        "경상북도": "경북", "경상남도": "경남",
        "제주특별자치도": "제주",
    }
    if not road_address:
        return "미확인"
    parts = str(road_address).strip().split()
    sido_raw = parts[0] if parts else ""
    return SIDO_MAP.get(sido_raw, sido_raw)


# ────────────────────────────────────────
# 1. hospital_id 처리
# ────────────────────────────────────────

def normalize_hospital_id(raw_id: str) -> str:
    """
    병원정보서비스의 '암호화된요양기호'를 hospital_id로 정규화합니다.

    공공데이터 구조:
      - 암호화된요양기호: 고유값 (암호화되어 있지만 반복 가능한 고유값)
      - 파일마다 동일한 병원은 동일한 암호화요양기호를 가짐
      → 그대로 hospital_id로 사용 가능

    Args:
        raw_id: 암호화된요양기호 원본값

    Returns:
        str: 정규화된 hospital_id (앞뒤 공백 제거, 빈 값 처리)
    """
    if not raw_id:
        return "HOSP_UNKNOWN"
    return str(raw_id).strip()


# ────────────────────────────────────────
# 2. pharmacy_id 범용 생성 규칙
# ────────────────────────────────────────

def generate_pharmacy_id(
    pharmacy_name: str,
    sigungu_code: str,
    zip_code: str | None = None,
) -> str:
    """
    약국정보서비스 기반 pharmacy_id 범용 생성.

    왜 암호화요양기호를 쓰지 않는가:
      - 약국정보서비스의 암호화요양기호는 Base64+추가암호화로 재현 불가
      - 회사 CRM/처방 파일에는 이 값이 없음
      - 따라서 '약국명 + 시군구코드 + 우편번호' 조합으로 재현 가능한 ID를 만든다

    규칙:
      PH_{sigungu_code}_{normalized_pharmacy_name}_{zip_prefix}

    구성:
      - PH_: 약국(Pharmacy) 식별 접두사
      - sigungu_code: 시군구코드 6자리 (공공데이터 기준, 예: 110110)
      - normalized_pharmacy_name: 약국명 정규화 (공백/특수문자 제거, 소문자)
      - zip_prefix: 우편번호 앞 3자리 (동명 약국 구분)

    결정론적 보장:
      동일 약국명 + 시군구코드 + 우편번호 → 항상 동일한 ID
      공공데이터 약국 마스터 OR 회사 처방 파일 어디서든 동일하게 생성

    Args:
        pharmacy_name: 약국명 ('요양기관명' 컬럼)
        sigungu_code: 시군구코드 6자리 ('시군구코드' 컬럼)
        zip_code: 우편번호 5자리 ('우편번호' 컬럼, 없으면 '000')

    Returns:
        str: "PH_110110_서울중앙약국_040" 형태

    예:
        generate_pharmacy_id("서울중앙약국", "110110", "04001")
        → "PH_110110_서울중앙약국_040"
    """
    normalized = _normalize_name(pharmacy_name)
    code = str(sigungu_code or "000000").strip()
    zip_prefix = str(zip_code or "000").strip()[:3]
    return f"PH_{code}_{normalized}_{zip_prefix}"


def generate_pharmacy_id_from_public_row(row: dict) -> str:
    """
    약국정보서비스 한 행(dict)에서 pharmacy_id를 바로 생성합니다.

    Args:
        row: 약국정보서비스 행 데이터
             필수 키: '요양기관명', '시군구코드', '우편번호'

    Returns:
        str: pharmacy_id
    """
    return generate_pharmacy_id(
        pharmacy_name=str(row.get("요양기관명", "") or ""),
        sigungu_code=str(row.get("시군구코드", "") or ""),
        zip_code=str(row.get("우편번호", "") or ""),
    )


# ────────────────────────────────────────
# 3. wholesaler_id 범용 생성 규칙
# ────────────────────────────────────────

def generate_wholesaler_id(
    wholesaler_name: str,
    region_key: str,
) -> str:
    """
    도매업소 범용 wholesaler_id 생성.

    공공데이터 도매파일 구조:
      - facility_name(시설명): 도매상 이름
      - road_address: 주소 → 시도명 추출
      - 고유 ID 없음

    규칙:
      WS_{region_key}_{normalized_wholesaler_name}

    구성:
      - WS_: 도매(Wholesaler) 식별 접두사
      - region_key: 시도명 약칭 (공공데이터 주소에서 추출, 예: '서울', '경남')
      - normalized_wholesaler_name: 이름 정규화

    결정론적 보장:
      동일 도매상명 + 시도명 → 항상 동일한 ID
      회사 처방 데이터에서도 동일하게 생성 가능

    Args:
        wholesaler_name: 도매상명 ('facility_name(시설명)' 컬럼)
        region_key: 시도명 약칭 (예: '서울', '부산', '경남')

    Returns:
        str: "WS_경남_지오영주" 형태

    예:
        generate_wholesaler_id("지오영(주)", "경남")
        → "WS_경남_지오영주"
    """
    normalized = _normalize_name(wholesaler_name)
    region = str(region_key or "미확인").strip()
    return f"WS_{region}_{normalized}"


def generate_wholesaler_id_from_public_row(row: dict) -> str:
    """
    도매업소 공공데이터 한 행(dict)에서 wholesaler_id를 바로 생성합니다.
    도로명주소에서 시도명을 자동 추출합니다.

    Args:
        row: 도매업소 행 데이터
             필수 키: 'facility_name(시설명)', 'road_address(소재지도로명주소)'

    Returns:
        str: wholesaler_id
    """
    name = str(row.get("facility_name(시설명)", "") or "")
    address = str(row.get("road_address(소재지도로명주소)", "") or "")
    region = _extract_sido_from_address(address)
    return generate_wholesaler_id(name, region)


# ────────────────────────────────────────
# 4. product_id 범용 생성 규칙
# ────────────────────────────────────────

def generate_product_id(
    product_name: str,
    ingredient_code: str | None = None,
    dosage_form: str | None = None,
) -> str:
    """
    제품 범용 ID 생성.

    우선순위:
      1. ingredient_code 있으면 → PROD_{ingredient_code}_{normalized_name}
         (건강보험 성분코드는 표준이므로 가장 안정적)
      2. 없으면 → PROD_{normalized_name}_{dosage_form}

    공공데이터 약가 파일의 '성분코드' 컬럼이 있으면 product_id 정확도 향상.

    Args:
        product_name: 제품명
        ingredient_code: 건강보험 성분코드 (없으면 None)
        dosage_form: 제형 (정/캡슐/주사 등, 없으면 'na')

    Returns:
        str: "PROD_A001_리피토정" 또는 "PROD_리피토정_정" 형태
    """
    normalized = _normalize_name(product_name)
    if ingredient_code and str(ingredient_code).strip():
        code = str(ingredient_code).strip()
        return f"PROD_{code}_{normalized}"
    else:
        form = _normalize_name(dosage_form) if dosage_form else "na"
        return f"PROD_{normalized}_{form}"


# ────────────────────────────────────────
# 5. lineage_key 생성 규칙
# ────────────────────────────────────────

def generate_lineage_key(
    wholesaler_id: str,
    pharmacy_id: str,
    metric_month: str,
    hospital_id: str | None = None,
) -> str:
    """
    도매→약국→병원 흐름 추적 키 생성.

    규칙:
      {wholesaler_id}__{pharmacy_id}__{hospital_segment}__{metric_month}

    hospital_segment:
      - 병원 매핑 성공: hospital_id (공공데이터 암호화된요양기호)
      - 병원 매핑 실패: 'UNMAPPED' (도매→약국 구간은 유지, 병원 연결만 미완)

    Args:
        wholesaler_id: generate_wholesaler_id() 생성값
        pharmacy_id: generate_pharmacy_id() 생성값
        metric_month: 집계 기준월 YYYYMM
        hospital_id: normalize_hospital_id() 생성값 (없으면 None)

    Returns:
        str: 예) "WS_서울_지오영주__PH_110110_서울중앙약국_040__HOSP_01__202501"
    """
    hospital_part = hospital_id if hospital_id else "UNMAPPED"
    return f"{wholesaler_id}__{pharmacy_id}__{hospital_part}__{metric_month}"


# ────────────────────────────────────────
# 6. 유효성 검증 헬퍼
# ────────────────────────────────────────

def is_valid_pharmacy_id(pharmacy_id: str) -> bool:
    return isinstance(pharmacy_id, str) and pharmacy_id.startswith("PH_")


def is_valid_wholesaler_id(wholesaler_id: str) -> bool:
    return isinstance(wholesaler_id, str) and wholesaler_id.startswith("WS_")


def is_valid_hospital_id(hospital_id: str) -> bool:
    """hospital_id가 비어 있지 않으면 유효."""
    return isinstance(hospital_id, str) and bool(hospital_id.strip())


def is_lineage_complete(lineage_key: str) -> bool:
    """병원까지 완전히 연결된 lineage_key인지 확인."""
    return isinstance(lineage_key, str) and "UNMAPPED" not in lineage_key


def extract_month_from_lineage(lineage_key: str) -> str | None:
    """lineage_key에서 metric_month(YYYYMM) 추출."""
    if not lineage_key:
        return None
    parts = lineage_key.split("__")
    if len(parts) >= 4:
        month = parts[-1]
        if len(month) == 6 and month.isdigit():
            return month
    return None


# ────────────────────────────────────────
# 7. 공공 약국 마스터 인덱스 생성
# ────────────────────────────────────────

def build_pharmacy_index_from_public(
    pharmacy_records: list[dict],
) -> dict[str, dict]:
    """
    약국정보서비스 데이터로 pharmacy_id → 약국정보 인덱스를 생성합니다.
    flow_builder에서 약국 지역 정보 조회에 사용합니다.

    Args:
        pharmacy_records: 약국정보서비스 행 목록
                          필수 컬럼: '요양기관명', '시군구코드', '우편번호',
                                     '시도코드명', '시군구코드명'

    Returns:
        dict: {pharmacy_id: {'pharmacy_name', 'sido_name', 'sigungu_name', ...}}
    """
    index = {}
    for row in pharmacy_records:
        try:
            pid = generate_pharmacy_id_from_public_row(row)
            index[pid] = {
                "pharmacy_id": pid,
                "pharmacy_name": str(row.get("요양기관명", "")),
                "sido_name": str(row.get("시도코드명", "")),
                "sigungu_code": str(row.get("시군구코드", "")),
                "sigungu_name": str(row.get("시군구코드명", "")),
                "zip_code": str(row.get("우편번호", "")),
                "address": str(row.get("주소", "")),
            }
        except Exception:
            continue
    return index


def build_wholesaler_index_from_public(
    wholesaler_records: list[dict],
    active_types: list[str] | None = None,
) -> dict[str, dict]:
    """
    도매업소 공공데이터로 wholesaler_id → 도매정보 인덱스를 생성합니다.

    Args:
        wholesaler_records: 도매업소 행 목록
        active_types: 포함할 업종명 목록 (None이면 전체)
                      예: ['의약품도매'] → 한약도매 제외

    Returns:
        dict: {wholesaler_id: {'wholesaler_name', 'region_key', 'address', ...}}
    """
    index = {}
    for row in wholesaler_records:
        try:
            btype = str(row.get("business_type(업종명)", ""))
            if active_types and btype not in active_types:
                continue
            wid = generate_wholesaler_id_from_public_row(row)
            address = str(row.get("road_address(소재지도로명주소)", ""))
            index[wid] = {
                "wholesaler_id": wid,
                "wholesaler_name": str(row.get("facility_name(시설명)", "")),
                "business_type": btype,
                "region_key": _extract_sido_from_address(address),
                "address": address,
                "phone": str(row.get("phone(전화번호)", "")),
            }
        except Exception:
            continue
    return index
