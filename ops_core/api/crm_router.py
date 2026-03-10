"""
OPS Core API - CRM Result Asset 평가 엔드포인트

POST /ops/crm/evaluate

OPS가 CrmResultAsset을 받아 품질을 평가하고
다음 연결 가능한 모듈과 판단 근거를 반환한다.

평가 기준:
  - hospital_mapping_rate >= 0.7 -> PASS
  - hospital_mapping_rate >= 0.5 -> WARN
  - hospital_mapping_rate < 0.5 -> FAIL
  - unique_reps > 0 -> 필수
  - unique_hospitals > 0 -> 필수
"""

try:
    from fastapi import APIRouter, HTTPException
except ModuleNotFoundError:  # pragma: no cover - 로컬 스크립트 실행 fallback
    class APIRouter:  # type: ignore[override]
        def __init__(self, *args, **kwargs):
            pass

        def post(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

        def get(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from result_assets.crm_result_asset import CrmResultAsset
from common.types import QualityGateStatus, ModuleName, QUALITY_GATE_MIN_MAPPING_RATE, QUALITY_GATE_WARN_MAPPING_RATE


router = APIRouter(prefix="/ops/crm", tags=["OPS - CRM"])


# ────────────────────────────────────────
# 요청/응답 스키마
# ────────────────────────────────────────

class CrmEvaluateRequest(BaseModel):
    """CRM Result Asset 평가 요청."""
    asset: CrmResultAsset
    run_log_id: Optional[str] = None   # ops_run_log ID (있으면 Supabase에 저장)


class CrmEvaluateResponse(BaseModel):
    """OPS CRM 평가 결과."""
    quality_status: str                 # pass | warn | fail
    quality_score: float                # 0.0 ~ 100.0
    reasoning_note: str                 # OPS 판단 근거 (사람이 읽는 설명)
    next_modules: list[str]             # 연결 가능한 다음 모듈
    gate_details: dict                  # 각 게이트별 통과 여부 상세
    evaluated_at: datetime


# ────────────────────────────────────────
# OPS 품질 게이트 평가 로직
# ────────────────────────────────────────

def evaluate_crm_asset(asset: CrmResultAsset) -> CrmEvaluateResponse:
    """
    CrmResultAsset을 평가하여 OPS 판단 결과를 반환합니다.

    평가 항목:
      1. hospital_id 축 완결성 (매핑률)
      2. 담당자 존재 여부
      3. 병원 수 충분성
      4. 행동 프로파일 완결성
      5. 월별 KPI 존재 여부
    """
    mq = asset.mapping_quality
    ctx = asset.activity_context
    gates: dict[str, dict] = {}
    reasons: list[str] = []
    warnings: list[str] = []

    # Gate 1: 병원 매핑률
    mapping_rate = mq.hospital_mapping_rate
    if mapping_rate >= QUALITY_GATE_MIN_MAPPING_RATE:
        gates["hospital_mapping_rate"] = {"status": "pass", "value": mapping_rate}
    elif mapping_rate >= QUALITY_GATE_WARN_MAPPING_RATE:
        gates["hospital_mapping_rate"] = {"status": "warn", "value": mapping_rate}
        warnings.append(f"병원 매핑률 {mapping_rate:.1%}. 70% 미만 (경고 기준 50% 이상).")
    else:
        gates["hospital_mapping_rate"] = {"status": "fail", "value": mapping_rate}
        reasons.append(f"병원 매핑률 {mapping_rate:.1%}. 최소 기준 50% 미달.")

    # Gate 2: 담당자 수
    if ctx.unique_reps > 0:
        gates["rep_exists"] = {"status": "pass", "value": ctx.unique_reps}
    else:
        gates["rep_exists"] = {"status": "fail", "value": 0}
        reasons.append("활동 담당자가 없습니다.")

    # Gate 3: 병원 수
    if ctx.unique_hospitals >= 1:
        gates["hospital_exists"] = {"status": "pass", "value": ctx.unique_hospitals}
    else:
        gates["hospital_exists"] = {"status": "fail", "value": 0}
        reasons.append("방문 병원이 없습니다.")

    # Gate 4: 행동 프로파일 생성 여부
    if len(asset.behavior_profiles) > 0:
        gates["behavior_profiles"] = {"status": "pass", "value": len(asset.behavior_profiles)}
    else:
        gates["behavior_profiles"] = {"status": "warn", "value": 0}
        warnings.append("행동 프로파일이 생성되지 않았습니다.")

    # Gate 5: 월별 KPI 존재
    if len(asset.monthly_kpi) > 0:
        gates["monthly_kpi"] = {"status": "pass", "value": len(asset.monthly_kpi)}
    else:
        gates["monthly_kpi"] = {"status": "warn", "value": 0}
        warnings.append("월별 KPI 집계 결과가 없습니다.")

    # ── 최종 상태 결정 ───────────────────────────────────────────────────────
    if reasons:
        quality_status = QualityGateStatus.FAIL
        next_modules = []
        reasoning = (
            "❌ CRM Result Asset 품질 게이트 FAIL. "
            + " | ".join(reasons)
            + " 원천 데이터와 Adapter 설정을 확인하세요."
        )
    elif warnings:
        quality_status = QualityGateStatus.WARN
        next_modules = [ModuleName.PRESCRIPTION, ModuleName.SANDBOX]
        reasoning = (
            "⚠️ CRM Result Asset 품질 게이트 WARN. 진행 가능하지만 주의 필요. "
            + " | ".join(warnings)
        )
    else:
        quality_status = QualityGateStatus.PASS
        next_modules = [ModuleName.PRESCRIPTION, ModuleName.SANDBOX]
        reasoning = (
            f"✅ CRM Result Asset 품질 게이트 PASS. "
            f"담당자 {ctx.unique_reps}명, 병원 {ctx.unique_hospitals}개, "
            f"활동 {ctx.total_activity_records}건, 매핑률 {mapping_rate:.1%}. "
            f"Prescription 및 Sandbox로 연결 가능."
        )

    # 품질 점수 계산 (0~100)
    score_parts = [
        min(mapping_rate * 100, 100) * 0.5,                           # 매핑률 50% 비중
        (min(ctx.unique_reps, 10) / 10) * 100 * 0.2,                  # 담당자 수 20%
        (min(ctx.unique_hospitals, 50) / 50) * 100 * 0.2,             # 병원 수 20%
        (len(asset.monthly_kpi) > 0) * 100 * 0.1,                     # KPI 존재 10%
    ]
    quality_score = round(sum(score_parts), 1)

    return CrmEvaluateResponse(
        quality_status=quality_status,
        quality_score=quality_score,
        reasoning_note=reasoning,
        next_modules=next_modules,
        gate_details=gates,
        evaluated_at=datetime.now(),
    )


# ────────────────────────────────────────
# FastAPI 라우터 엔드포인트
# ────────────────────────────────────────

@router.post("/evaluate", response_model=CrmEvaluateResponse, summary="CRM Result Asset OPS 평가")
async def evaluate_crm(request: CrmEvaluateRequest) -> CrmEvaluateResponse:
    """
    CRM Result Asset을 OPS 품질 게이트로 평가합니다.

    - **PASS**: hospital 매핑률 ≥ 70%, 담당자/병원 존재
    - **WARN**: hospital 매핑률 50~70% 또는 일부 게이트 미달
    - **FAIL**: 필수 게이트 통과 실패 (다음 모듈 연결 불가)
    """
    try:
        return evaluate_crm_asset(request.asset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OPS 평가 중 오류: {str(e)}")


@router.get("/health", summary="CRM OPS 라우터 상태 확인")
async def crm_health():
    return {"status": "ok", "module": "crm", "endpoint": "/ops/crm/evaluate"}
