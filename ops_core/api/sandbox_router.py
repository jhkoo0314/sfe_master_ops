"""
OPS Core API - Sandbox Result Asset 평가 엔드포인트

POST /ops/sandbox/evaluate

평가 게이트 (5개):
  1. 매출 데이터 존재
  2. CRM×Sales 조인율 ≥ 40% (PASS: ≥60%)
  3. 분석 가능 병원 수 ≥ 5
  4. 분석 월 수 ≥ 1
  5. Territory/Builder handoff 후보 존재

다음 모듈:
  - territory: 조인율 ≥ 60% AND 병원 ≥ 10
  - builder:   항상 가능 (분석 결과 있으면)
"""

from datetime import datetime
from typing import Optional
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

from result_assets.sandbox_result_asset import SandboxResultAsset
from common.types import QualityGateStatus, ModuleName

router = APIRouter(prefix="/ops/sandbox", tags=["OPS - Sandbox"])

PASS_JOIN_RATE = 0.6
WARN_JOIN_RATE = 0.4
MIN_HOSPITALS = 5


class SandboxEvaluateRequest(BaseModel):
    asset: SandboxResultAsset
    run_log_id: Optional[str] = None


class SandboxEvaluateResponse(BaseModel):
    quality_status: str
    quality_score: float
    reasoning_note: str
    next_modules: list[str]
    gate_details: dict
    evaluated_at: datetime


def evaluate_sandbox_asset(asset: SandboxResultAsset) -> SandboxEvaluateResponse:
    s = asset.analysis_summary
    jq = asset.join_quality
    gates: dict = {}
    reasons: list[str] = []
    warnings: list[str] = []

    # Gate 1: 매출 데이터 존재
    if asset.domain_quality.sales_record_count > 0:
        gates["sales_exists"] = {"status": "pass", "value": asset.domain_quality.sales_record_count}
    else:
        gates["sales_exists"] = {"status": "fail", "value": 0}
        reasons.append("매출 데이터가 없습니다.")

    # Gate 2: CRM × Sales 조인율
    jr = jq.crm_sales_join_rate
    if jr >= PASS_JOIN_RATE:
        gates["join_rate"] = {"status": "pass", "value": jr}
    elif jr >= WARN_JOIN_RATE:
        gates["join_rate"] = {"status": "warn", "value": jr}
        warnings.append(f"CRM×Sales 조인율 {jr:.1%} (권장 60% 이상).")
    else:
        gates["join_rate"] = {"status": "fail", "value": jr}
        reasons.append(f"CRM×Sales 조인율 {jr:.1%}. 최소 기준 40% 미달.")

    # Gate 3: 병원 수
    if s.total_hospitals >= MIN_HOSPITALS:
        gates["hospital_count"] = {"status": "pass", "value": s.total_hospitals}
    else:
        gates["hospital_count"] = {"status": "warn", "value": s.total_hospitals}
        warnings.append(f"분석 병원 수 {s.total_hospitals}개. 권장 {MIN_HOSPITALS}개 이상.")

    # Gate 4: 분석 기간
    if s.total_months >= 1:
        gates["month_coverage"] = {"status": "pass", "value": s.total_months}
    else:
        gates["month_coverage"] = {"status": "fail", "value": 0}
        reasons.append("분석 가능한 월 데이터가 없습니다.")

    # Gate 5: handoff 후보
    eligible = [h for h in asset.handoff_candidates if h.is_eligible]
    if eligible:
        gates["handoff_eligible"] = {"status": "pass", "value": [h.module for h in eligible]}
    else:
        gates["handoff_eligible"] = {"status": "warn", "value": []}
        warnings.append("Territory/Builder handoff 조건 미충족.")

    # 최종 판정
    next_modules = [h.module for h in asset.handoff_candidates if h.is_eligible]

    if reasons:
        quality_status = QualityGateStatus.FAIL
        next_modules = []
        note = (
            f"❌ Sandbox Result Asset 품질 게이트 FAIL. "
            + " | ".join(reasons)
        )
    elif warnings:
        quality_status = QualityGateStatus.WARN
        note = (
            f"⚠️ Sandbox Result Asset 품질 게이트 WARN. "
            + " | ".join(warnings)
            + f" 분석 병원 {s.total_hospitals}개, "
            f"조인율 {jr:.1%}, 기간 {s.total_months}개월."
        )
    else:
        quality_status = QualityGateStatus.PASS
        att_str = f", 평균달성률 {s.avg_attainment_rate:.1%}" if s.avg_attainment_rate else ""
        note = (
            f"✅ Sandbox Result Asset 품질 게이트 PASS. "
            f"병원 {s.total_hospitals}개, 조인율 {jr:.1%}{att_str}, "
            f"기간 {s.total_months}개월. "
            f"다음 모듈: {', '.join(next_modules) if next_modules else '없음'}."
        )

    score = round(
        jr * 100 * 0.4
        + (min(s.total_hospitals, 50) / 50) * 100 * 0.3
        + (min(s.total_months, 12) / 12) * 100 * 0.2
        + (len(eligible) > 0) * 100 * 0.1,
        1
    )

    return SandboxEvaluateResponse(
        quality_status=quality_status,
        quality_score=score,
        reasoning_note=note,
        next_modules=next_modules,
        gate_details=gates,
        evaluated_at=datetime.now(),
    )


@router.post("/evaluate", response_model=SandboxEvaluateResponse)
async def evaluate_sandbox(request: SandboxEvaluateRequest):
    try:
        return evaluate_sandbox_asset(request.asset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def sandbox_health():
    return {"status": "ok", "module": "sandbox", "endpoint": "/ops/sandbox/evaluate"}
