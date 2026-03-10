"""
OPS Pipeline API Router

POST /ops/pipeline/run       - 전체 파이프라인 실행
GET  /ops/pipeline/status    - 현재 파이프라인 상태 요약
GET  /ops/pipeline/modules   - 활성 모듈 목록
POST /ops/pipeline/step/{n}  - 특정 STEP만 단독 실행
"""

from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ops_core.workflow.orchestrator import run_pipeline, get_pipeline_status
from ops_core.workflow.schemas import PipelineRunPayload, PipelineRunResult, PipelineStatusSummary

router = APIRouter(prefix="/ops/pipeline", tags=["OPS - Pipeline"])


# ────────────────────────────────────────
# 요청/응답 모델
# ────────────────────────────────────────

class PipelineRunRequest(BaseModel):
    """파이프라인 실행 요청."""
    scenario: str = "crm_sales_target"
    start_from_step: int = 1
    stop_on_fail: bool = True

    # 각 Result Asset (실제 서비스에서는 asset_id로 조회)
    crm_asset: Optional[dict] = None
    prescription_asset: Optional[dict] = None
    sandbox_asset: Optional[dict] = None
    territory_asset: Optional[dict] = None


class ModuleInfo(BaseModel):
    module: str
    endpoint: str
    status: str
    description: str


# ────────────────────────────────────────
# 엔드포인트
# ────────────────────────────────────────

@router.post("/run", response_model=PipelineRunResult)
async def run_full_pipeline(request: PipelineRunRequest):
    """
    OPS 전체 파이프라인 실행.

    각 모듈의 Result Asset을 순서대로 평가하고
    전체 흐름의 결과를 반환합니다.

    - FAIL: 해당 단계에서 중단 (stop_on_fail=True)
    - WARN: 계속 진행, 권고사항 기록
    - PASS: 다음 단계 진행
    """
    try:
        payload = PipelineRunPayload(
            run_id=str(uuid.uuid4()),
            scenario=request.scenario,
            start_from_step=request.start_from_step,
            stop_on_fail=request.stop_on_fail,
        )

        # Result Asset 역직렬화 (실제로는 여기서 Pydantic 모델로 파싱)
        # 현재는 orchestrator에 dict 전달 → 각 평가 함수가 처리
        result = run_pipeline(
            payload=payload,
            crm_asset=request.crm_asset,
            prescription_asset=request.prescription_asset,
            sandbox_asset=request.sandbox_asset,
            territory_asset=request.territory_asset,
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파이프라인 실행 오류: {str(e)}")


@router.get("/status", response_model=PipelineStatusSummary)
async def get_status():
    """현재 파이프라인 상태 및 모듈별 마지막 평가 결과 조회."""
    return get_pipeline_status()


@router.get("/modules", response_model=list[ModuleInfo])
async def list_modules():
    """활성화된 모든 OPS 모듈 목록 반환."""
    status = get_pipeline_status()
    modules = [
        ModuleInfo(
            module="crm",
            endpoint="POST /ops/crm/evaluate",
            status=status.module_statuses.get("crm", "미실행"),
            description="병원 행동 CRM 데이터 품질 평가"
        ),
        ModuleInfo(
            module="prescription",
            endpoint="POST /ops/prescription/evaluate",
            status=status.module_statuses.get("prescription", "미실행"),
            description="도매→약국→병원 처방 흐름 분석"
        ),
        ModuleInfo(
            module="sandbox",
            endpoint="POST /ops/sandbox/evaluate",
            status=status.module_statuses.get("sandbox", "미실행"),
            description="CRM+실적+목표 통합 분석 엔진"
        ),
        ModuleInfo(
            module="territory",
            endpoint="POST /ops/territory/evaluate",
            status=status.module_statuses.get("territory", "미실행"),
            description="권역별 마커·동선·히트맵 지도 최적화"
        ),
        ModuleInfo(
            module="builder",
            endpoint="UI: templates/total_valid_templates.html",
            status=status.module_statuses.get("builder", "미실행"),
            description="OPS 보고서 HTML + WebSlide Studio"
        ),
    ]
    return modules


@router.get("/health")
async def pipeline_health():
    status = get_pipeline_status()
    return {
        "status": "ok",
        "total_runs": status.total_runs,
        "last_status": status.last_overall_status,
        "module_count": 5,
        "checked_at": datetime.now().isoformat(),
    }
