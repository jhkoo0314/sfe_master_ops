"""
SFE OPS 공통 예외 클래스

이 모듈은 프로젝트 전체에서 사용하는 예외를 정의합니다.
각 예외는 OPS 세계관 안에서 어떤 레이어에서 발생했는지를 명확히 합니다.

흐름: 원천데이터 -> Adapter -> Module -> Result Asset -> OPS
"""


class SFEOPSBaseError(Exception):
    """SFE OPS 기본 예외. 모든 커스텀 예외의 부모."""

    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(message)

    def __str__(self) -> str:
        if self.detail:
            return f"{self.message} | 상세: {self.detail}"
        return self.message


# ────────────────────────────────────────
# Adapter 레이어 예외
# ────────────────────────────────────────

class AdapterError(SFEOPSBaseError):
    """Adapter 레이어에서 발생하는 기본 예외."""


class AdapterInputError(AdapterError):
    """Adapter 입력 데이터가 잘못된 경우. (파일 포맷 불일치, 필수 컬럼 누락 등)"""


class AdapterMappingError(AdapterError):
    """Adapter에서 키 매핑에 실패한 경우. (hospital_id 매핑 실패 등)"""


class AdapterFileNotFoundError(AdapterError):
    """Adapter가 처리할 입력 파일을 찾을 수 없는 경우."""


# ────────────────────────────────────────
# Module 레이어 예외
# ────────────────────────────────────────

class ModuleError(SFEOPSBaseError):
    """Module 레이어에서 발생하는 기본 예외."""


class ModuleProcessingError(ModuleError):
    """Module 내부 처리 중 오류가 발생한 경우."""


class ModuleKeyIntegrityError(ModuleError):
    """공통 키 정합성 오류. (hospital_id, branch_id, rep_id 불일치 등)"""


class MissingResultAssetError(ModuleError):
    """Result Asset을 생성할 수 없는 경우. (필수 데이터 부족 등)"""


# ────────────────────────────────────────
# OPS Core 레이어 예외
# ────────────────────────────────────────

class OPSCoreError(SFEOPSBaseError):
    """OPS Core 레이어에서 발생하는 기본 예외."""


class OPSEvaluationError(OPSCoreError):
    """OPS가 Result Asset을 평가하는 중 오류가 발생한 경우."""


class OPSQualityGateError(OPSCoreError):
    """Result Asset이 OPS 품질 게이트를 통과하지 못한 경우."""

    def __init__(self, message: str, gate_result: dict | None = None):
        self.gate_result = gate_result
        super().__init__(message)


class OPSConnectionError(OPSCoreError):
    """모듈 간 연결 판단 중 오류가 발생한 경우."""


# ────────────────────────────────────────
# Result Asset 예외
# ────────────────────────────────────────

class ResultAssetValidationError(SFEOPSBaseError):
    """Result Asset 스키마 검증 실패."""


class ResultAssetNotFoundError(SFEOPSBaseError):
    """참조한 Result Asset을 찾을 수 없는 경우."""


# ────────────────────────────────────────
# Supabase / 저장소 예외
# ────────────────────────────────────────

class StorageError(SFEOPSBaseError):
    """Supabase 또는 로컬 저장소 관련 예외."""


class StorageWriteError(StorageError):
    """저장소 쓰기 실패."""


class StorageReadError(StorageError):
    """저장소 읽기 실패."""
