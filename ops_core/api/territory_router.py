"""
OPS Territory 평가 라우터

POST /ops/territory/evaluate

평가 게이트:
  1. 마커 수 ≥ 1 (지도에 그릴 병원 있음)
  2. 커버리지율 ≥ 40% (권역 절반 이상 담당)
  3. 담당자별 동선 존재
  4. 미커버 갭 비율 ≤ 30%
  5. 최적화 불균형 없음 (과부하/미부하 담당자)

다음 모듈: HTML Builder (builder)
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from result_assets.territory_result_asset import TerritoryResultAsset
from common.types import QualityGateStatus

router = APIRouter(prefix="/ops/territory", tags=["OPS - Territory"])


class TerritoryEvaluateRequest(BaseModel):
    asset: TerritoryResultAsset
    run_log_id: Optional[str] = None


class TerritoryEvaluateResponse(BaseModel):
    quality_status: str
    quality_score: float
    reasoning_note: str
    next_modules: list[str]
    gate_details: dict
    evaluated_at: datetime


def evaluate_territory_asset(asset: TerritoryResultAsset) -> TerritoryEvaluateResponse:
    cov = asset.coverage_summary
    opt = asset.optimization_summary
    gates: dict = {}
    reasons: list[str] = []
    warnings: list[str] = []

    # Gate 1: 마커 수
    if len(asset.markers) >= 1:
        gates["marker_exists"] = {"status": "pass", "value": len(asset.markers)}
    else:
        gates["marker_exists"] = {"status": "fail", "value": 0}
        reasons.append("지도에 그릴 병원 데이터가 없습니다.")

    # Gate 2: 커버리지율
    cr = cov.coverage_rate
    if cr >= 0.6:
        gates["coverage_rate"] = {"status": "pass", "value": cr}
    elif cr >= 0.4:
        gates["coverage_rate"] = {"status": "warn", "value": cr}
        warnings.append(f"권역 커버리지 {cr:.0%} (권장 60% 이상).")
    else:
        gates["coverage_rate"] = {"status": "fail", "value": cr}
        reasons.append(f"권역 커버리지 {cr:.0%}. 최소 40% 미달.")

    # Gate 3: 동선 존재
    if len(asset.routes) > 0:
        gates["route_exists"] = {"status": "pass", "value": len(asset.routes)}
    else:
        gates["route_exists"] = {"status": "warn", "value": 0}
        warnings.append("담당자 동선 데이터가 없습니다.")

    # Gate 4: 갭 비율
    gap_rate = cov.gap_hospitals / cov.total_hospitals if cov.total_hospitals else 0
    if gap_rate <= 0.3:
        gates["gap_rate"] = {"status": "pass", "value": round(gap_rate, 3)}
    else:
        gates["gap_rate"] = {"status": "warn", "value": round(gap_rate, 3)}
        warnings.append(f"미커버 병원 {gap_rate:.0%}. 방문 계획 수립 권장.")

    # Gate 5: 불균형
    imbalanced = len(opt.overloaded_reps) + len(opt.underloaded_reps)
    if imbalanced == 0:
        gates["balance"] = {"status": "pass", "value": "균형"}
    else:
        gates["balance"] = {"status": "warn", "value": f"불균형 {imbalanced}명"}
        warnings.append(f"담당자 {imbalanced}명 배치 불균형 감지.")

    # 최종 판정
    next_modules = ["builder"] if not reasons else []

    if reasons:
        quality_status = QualityGateStatus.FAIL
        note = f"❌ Territory 품질 게이트 FAIL. " + " | ".join(reasons)
    elif warnings:
        quality_status = QualityGateStatus.WARN
        note = (
            f"⚠️ Territory WARN. 마커 {len(asset.markers)}개, "
            f"커버리지 {cr:.0%}, 동선 {len(asset.routes)}개. "
            + " | ".join(warnings)
        )
    else:
        quality_status = QualityGateStatus.PASS
        note = (
            f"✅ Territory PASS. 마커 {len(asset.markers)}개, "
            f"커버리지 {cr:.0%}, 담당자 {opt.total_reps}명, "
            f"갭 {cov.gap_hospitals}개. HTML Builder로 handoff 가능."
        )

    score = round(
        (cr * 100) * 0.4
        + (min(len(asset.markers), 50) / 50) * 100 * 0.3
        + ((1 - gap_rate) * 100) * 0.2
        + ((imbalanced == 0) * 100) * 0.1,
        1
    )

    return TerritoryEvaluateResponse(
        quality_status=quality_status,
        quality_score=score,
        reasoning_note=note,
        next_modules=next_modules,
        gate_details=gates,
        evaluated_at=datetime.now(),
    )


@router.post("/evaluate", response_model=TerritoryEvaluateResponse)
async def evaluate_territory(request: TerritoryEvaluateRequest):
    try:
        return evaluate_territory_asset(request.asset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def territory_health():
    return {"status": "ok", "module": "territory", "endpoint": "/ops/territory/evaluate"}
