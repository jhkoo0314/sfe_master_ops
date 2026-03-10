"""
OPS Core API - Prescription Result Asset 평가 엔드포인트

POST /ops/prescription/evaluate

평가 기준:
  - flow_completion_rate >= 0.6 → PASS
  - flow_completion_rate >= 0.4 → WARN
  - flow_completion_rate < 0.4  → FAIL
  - unique_wholesalers > 0      → 필수
  - unique_pharmacies > 0       → 필수
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from result_assets.prescription_result_asset import PrescriptionResultAsset
from common.types import QualityGateStatus, ModuleName

router = APIRouter(prefix="/ops/prescription", tags=["OPS - Prescription"])

PASS_THRESHOLD = 0.6
WARN_THRESHOLD = 0.4


class PrescriptionEvaluateRequest(BaseModel):
    asset: PrescriptionResultAsset
    run_log_id: Optional[str] = None


class PrescriptionEvaluateResponse(BaseModel):
    quality_status: str
    quality_score: float
    reasoning_note: str
    next_modules: list[str]
    gate_details: dict
    evaluated_at: datetime


def evaluate_prescription_asset(asset: PrescriptionResultAsset) -> PrescriptionEvaluateResponse:
    ls = asset.lineage_summary
    mq = asset.mapping_quality
    gates: dict = {}
    reasons: list[str] = []
    warnings: list[str] = []

    # Gate 1: 흐름 완결률
    cr = mq.flow_completion_rate
    if cr >= PASS_THRESHOLD:
        gates["flow_completion_rate"] = {"status": "pass", "value": cr}
    elif cr >= WARN_THRESHOLD:
        gates["flow_completion_rate"] = {"status": "warn", "value": cr}
        warnings.append(f"병원 연결 완결률 {cr:.1%} (권장 60% 이상).")
    else:
        gates["flow_completion_rate"] = {"status": "fail", "value": cr}
        reasons.append(f"병원 연결 완결률 {cr:.1%}. 최소 기준 40% 미달.")

    # Gate 2: 도매상 존재
    if ls.unique_wholesalers > 0:
        gates["wholesaler_exists"] = {"status": "pass", "value": ls.unique_wholesalers}
    else:
        gates["wholesaler_exists"] = {"status": "fail", "value": 0}
        reasons.append("도매상 데이터가 없습니다.")

    # Gate 3: 약국 존재
    if ls.unique_pharmacies > 0:
        gates["pharmacy_exists"] = {"status": "pass", "value": ls.unique_pharmacies}
    else:
        gates["pharmacy_exists"] = {"status": "fail", "value": 0}
        reasons.append("약국 데이터가 없습니다.")

    # Gate 4: 병원 연결 존재
    if ls.unique_hospitals_connected > 0:
        gates["hospital_connected"] = {"status": "pass", "value": ls.unique_hospitals_connected}
    else:
        gates["hospital_connected"] = {"status": "warn", "value": 0}
        warnings.append("병원 연결이 하나도 없습니다. 지역 매핑 설정을 확인하세요.")

    # Gate 5: lineage_key 존재
    if ls.total_flow_records > 0:
        gates["flow_records_exist"] = {"status": "pass", "value": ls.total_flow_records}
    else:
        gates["flow_records_exist"] = {"status": "fail", "value": 0}
        reasons.append("흐름 레코드가 없습니다.")

    # 최종 판정
    if reasons:
        quality_status = QualityGateStatus.FAIL
        next_modules = []
        reasoning = (
            f"❌ Prescription Result Asset 품질 게이트 FAIL. "
            + " | ".join(reasons)
        )
    elif warnings:
        quality_status = QualityGateStatus.WARN
        next_modules = [ModuleName.SANDBOX]
        reasoning = (
            f"⚠️ Prescription Result Asset 품질 게이트 WARN. "
            + " | ".join(warnings)
            + f" 도매 {ls.unique_wholesalers}개, 약국 {ls.unique_pharmacies}개, "
            f"연결 병원 {ls.unique_hospitals_connected}개."
        )
    else:
        quality_status = QualityGateStatus.PASS
        next_modules = [ModuleName.SANDBOX]
        reasoning = (
            f"✅ Prescription Result Asset 품질 게이트 PASS. "
            f"도매→약국→병원 흐름 {ls.total_flow_records}건, "
            f"완결률 {cr:.1%}, 연결 병원 {ls.unique_hospitals_connected}개. "
            f"Sandbox로 연결 가능."
        )

    score = round(
        cr * 100 * 0.5
        + (min(ls.unique_wholesalers, 10) / 10) * 100 * 0.15
        + (min(ls.unique_pharmacies, 50) / 50) * 100 * 0.2
        + (ls.unique_hospitals_connected > 0) * 100 * 0.15,
        1
    )

    return PrescriptionEvaluateResponse(
        quality_status=quality_status,
        quality_score=score,
        reasoning_note=reasoning,
        next_modules=next_modules,
        gate_details=gates,
        evaluated_at=datetime.now(),
    )


@router.post("/evaluate", response_model=PrescriptionEvaluateResponse)
async def evaluate_prescription(request: PrescriptionEvaluateRequest):
    try:
        return evaluate_prescription_asset(request.asset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def prescription_health():
    return {"status": "ok", "module": "prescription", "endpoint": "/ops/prescription/evaluate"}
