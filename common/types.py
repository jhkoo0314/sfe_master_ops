"""
SFE OPS 공통 타입 및 상수 정의

이 모듈은 프로젝트 전체에서 공유하는 타입, Enum, 상수를 정의합니다.
모든 모듈이 같은 언어로 통신하기 위한 기반입니다.
"""

from enum import Enum
from typing import Literal


# ────────────────────────────────────────
# 모듈 식별자
# ────────────────────────────────────────

class ModuleName(str, Enum):
    """SFE OPS 5개 모듈의 공식 식별자."""
    CRM = "crm"
    PRESCRIPTION = "prescription"
    SANDBOX = "sandbox"
    TERRITORY = "territory"
    BUILDER = "builder"


# ────────────────────────────────────────
# OPS 품질 게이트 상태
# ────────────────────────────────────────

class QualityGateStatus(str, Enum):
    """OPS가 Result Asset을 평가한 결과 상태."""
    PASS = "pass"       # 정상. 다음 모듈 연결 가능.
    WARN = "warn"       # 경고. 진행 가능하지만 주의 필요.
    FAIL = "fail"       # 실패. 다음 모듈 연결 불가. 수정 필요.


# ────────────────────────────────────────
# Result Asset 타입
# ────────────────────────────────────────

class ResultAssetType(str, Enum):
    """각 모듈이 생산하는 Result Asset의 공식 타입."""
    CRM_RESULT = "crm_result_asset"
    PRESCRIPTION_RESULT = "prescription_result_asset"
    SANDBOX_RESULT = "sandbox_result_asset"
    TERRITORY_RESULT = "territory_result_asset"
    BUILDER_RESULT = "html_builder_result_asset"


# ────────────────────────────────────────
# 공통 키 타입 힌트 (문서화 목적)
# ────────────────────────────────────────

# 병원 공통 식별자 (CRM 기준, 모든 모듈이 재사용)
HospitalId = str

# 지점/지역 담당 식별자
BranchId = str

# 영업담당자 식별자
RepId = str

# 약국 식별자 (Prescription 범용 규칙 기반)
PharmacyId = str

# 도매 식별자 (Prescription 범용 규칙 기반)
WholesalerId = str

# 제품 식별자
ProductId = str

# 성분 코드
IngredientCode = str

# 집계 기준 월 (YYYYMM 형식)
MetricMonth = str

# ────────────────────────────────────────
# 공통 상수
# ────────────────────────────────────────

# 집계 기준 월 포맷
METRIC_MONTH_FORMAT = "%Y%m"

# 날짜 포맷
DATE_FORMAT = "%Y-%m-%d"

# OPS 품질 게이트 최소 기준값
QUALITY_GATE_MIN_MAPPING_RATE = 0.7    # 70% 이상 매핑되어야 PASS
QUALITY_GATE_WARN_MAPPING_RATE = 0.5   # 50% 이상이면 WARN

# ────────────────────────────────────────
# 모듈 간 공식 연결 맵 (OPS handoff 기준)
# ────────────────────────────────────────

# 각 모듈이 Result Asset을 넘길 수 있는 다음 모듈 목록
MODULE_HANDOFF_MAP: dict[ModuleName, list[ModuleName]] = {
    ModuleName.CRM: [ModuleName.PRESCRIPTION, ModuleName.SANDBOX],
    ModuleName.PRESCRIPTION: [ModuleName.SANDBOX],
    ModuleName.SANDBOX: [ModuleName.TERRITORY, ModuleName.BUILDER],
    ModuleName.TERRITORY: [ModuleName.BUILDER],
    ModuleName.BUILDER: [],  # 최종 표현 모듈이므로 후속 없음
}

# ────────────────────────────────────────
# OPS 환경 설정 타입
# ────────────────────────────────────────

OPSEnvironment = Literal["development", "staging", "production"]
