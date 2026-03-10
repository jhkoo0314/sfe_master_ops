"""
OPS 파이프라인 오케스트레이터

각 모듈의 evaluate 함수를 순서대로 호출하여
전체 파이프라인의 흐름을 제어한다.

설계 원칙:
- 각 모듈의 평가 로직은 각자의 router에서 독립적으로 구현
- 오케스트레이터는 '호출'과 '결과 취합'만 담당
- FAIL 발생 시 즉시 중단 (stop_on_fail=True 기본값)
- WARN은 계속 진행하되 권고사항 기록
"""

import time
import uuid
from datetime import datetime
from typing import Optional

from ops_core.workflow.schemas import (
    PipelineRunPayload, PipelineRunResult, StepResult, PipelineStatusSummary,
)
from common.types import QualityGateStatus

# 각 모듈 평가 함수 임포트
from ops_core.api.crm_router import evaluate_crm_asset
from ops_core.api.prescription_router import evaluate_prescription_asset
from ops_core.api.sandbox_router import evaluate_sandbox_asset
from ops_core.api.territory_router import evaluate_territory_asset


# 전역 파이프라인 상태 레지스트리 (실제 서비스에서는 DB 또는 Redis)
_pipeline_registry: PipelineStatusSummary = PipelineStatusSummary()


def get_pipeline_status() -> PipelineStatusSummary:
    return _pipeline_registry


def run_pipeline(
    payload: PipelineRunPayload,
    crm_asset=None,
    prescription_asset=None,
    sandbox_asset=None,
    territory_asset=None,
) -> PipelineRunResult:
    """
    OPS 전체 파이프라인 실행.
    각 단계를 순서대로 평가하고 결과를 취합한다.
    """
    run_id = payload.run_id or str(uuid.uuid4())
    started_at = datetime.now()
    steps: list[StepResult] = []
    overall = QualityGateStatus.PASS
    recommended_actions: list[str] = []
    final_eligible: list[str] = []

    def _make_step(step: int, module: str, fn, asset, previous_eligible: list[str]) -> StepResult:
        """단계 실행 래퍼."""
        t0 = time.time()
        if asset is None:
            return StepResult(
                step=step, module=module,
                status=QualityGateStatus.WARN,
                reasoning_note=f"{module} 자산이 제공되지 않아 이 단계를 건너뜁니다.",
                duration_ms=0,
            )
        try:
            result = fn(asset)
            duration = int((time.time() - t0) * 1000)
            return StepResult(
                step=step, module=module,
                status=result.quality_status,
                score=result.quality_score,
                next_modules=result.next_modules,
                reasoning_note=result.reasoning_note,
                gate_details=result.gate_details if hasattr(result, 'gate_details') else {},
                duration_ms=duration,
            )
        except Exception as e:
            return StepResult(
                step=step, module=module,
                status=QualityGateStatus.FAIL,
                reasoning_note=f"평가 중 오류 발생: {str(e)}",
                error=str(e),
            )

    # ── STEP 1: CRM ──────────────────────────────────────
    if payload.start_from_step <= 1:
        step_r = _make_step(1, "crm", evaluate_crm_asset, crm_asset, [])
        steps.append(step_r)
        _update_registry("crm", step_r.status)

        if step_r.status == QualityGateStatus.FAIL:
            overall = QualityGateStatus.FAIL
            recommended_actions.append("❌ CRM 데이터 품질 개선 후 재실행 필요")
            if payload.stop_on_fail:
                return _finalize(run_id, payload.scenario, steps, overall,
                                 recommended_actions, final_eligible, started_at)
        elif step_r.status == QualityGateStatus.WARN:
            recommended_actions.append("⚠️ CRM 데이터에 경고가 있습니다. 검토 후 진행 권장.")

    # ── STEP 2: Prescription (선택) ───────────────────────
    if payload.start_from_step <= 2:
        step_r = _make_step(2, "prescription", evaluate_prescription_asset, prescription_asset, [])
        steps.append(step_r)
        _update_registry("prescription", step_r.status)

        if step_r.status == QualityGateStatus.FAIL:
            recommended_actions.append("⚠️ Prescription 데이터 없음 — 기본 시나리오로 계속 진행.")
            # Prescription은 선택적 모듈 → FAIL이어도 계속 진행

    # ── STEP 3: Sandbox ───────────────────────────────────
    if payload.start_from_step <= 3:
        step_r = _make_step(3, "sandbox", evaluate_sandbox_asset, sandbox_asset, [])
        steps.append(step_r)
        _update_registry("sandbox", step_r.status)

        if step_r.status == QualityGateStatus.FAIL:
            overall = QualityGateStatus.FAIL
            recommended_actions.append("❌ Sandbox 분석 품질 미달. 실적 데이터 재점검 필요.")
            if payload.stop_on_fail:
                return _finalize(run_id, payload.scenario, steps, overall,
                                 recommended_actions, final_eligible, started_at)
        else:
            final_eligible.extend(step_r.next_modules)
            if step_r.status == QualityGateStatus.WARN:
                recommended_actions.append("⚠️ Sandbox WARN — 조인율 또는 병원 수 부족. 데이터 보강 권장.")

    # ── STEP 4: Territory ─────────────────────────────────
    if payload.start_from_step <= 4 and "territory" in final_eligible:
        step_r = _make_step(4, "territory", evaluate_territory_asset, territory_asset, final_eligible)
        steps.append(step_r)
        _update_registry("territory", step_r.status)

        if step_r.status == QualityGateStatus.FAIL:
            recommended_actions.append("❌ Territory 품질 미달. 권역/담당자 매핑 재검토 필요.")
        else:
            final_eligible.extend([m for m in step_r.next_modules if m not in final_eligible])
            if step_r.status == QualityGateStatus.WARN:
                recommended_actions.append("⚠️ Territory WARN — 커버리지 보강 권장.")
    elif "territory" not in final_eligible and payload.start_from_step <= 4:
        steps.append(StepResult(
            step=4, module="territory",
            status=QualityGateStatus.WARN,
            reasoning_note="이전 단계에서 Territory handoff 조건 미충족 — 건너뜀.",
        ))

    # ── STEP 5: Builder ───────────────────────────────────
    if "builder" in final_eligible:
        steps.append(StepResult(
            step=5, module="builder",
            status=QualityGateStatus.PASS,
            score=100.0,
            reasoning_note="✅ Builder handoff 준비 완료. HTML 보고서 생성 가능.",
            next_modules=[],
        ))
        _update_registry("builder", QualityGateStatus.PASS)
        recommended_actions.append("✅ HTML Builder 실행 가능. 보고서를 생성하세요.")

    # 전체 판정
    all_statuses = [s.status for s in steps]
    if QualityGateStatus.FAIL in all_statuses:
        overall = QualityGateStatus.FAIL
    elif QualityGateStatus.WARN in all_statuses:
        overall = QualityGateStatus.WARN

    return _finalize(run_id, payload.scenario, steps, overall,
                     recommended_actions, final_eligible, started_at)


def _finalize(
    run_id: str, scenario: str,
    steps: list[StepResult], overall: str,
    actions: list[str], eligible: list[str],
    started_at: datetime,
) -> PipelineRunResult:
    completed = datetime.now()
    duration = int((completed - started_at).total_seconds() * 1000)
    scores = [s.score for s in steps if s.score > 0]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    _pipeline_registry.last_run_at = completed
    _pipeline_registry.last_overall_status = overall
    _pipeline_registry.total_runs += 1
    if overall == QualityGateStatus.PASS:
        _pipeline_registry.pass_count += 1
    elif overall == QualityGateStatus.WARN:
        _pipeline_registry.warn_count += 1
    else:
        _pipeline_registry.fail_count += 1

    return PipelineRunResult(
        run_id=run_id,
        scenario=scenario,
        overall_status=overall,
        overall_score=avg_score,
        steps=steps,
        final_eligible_modules=list(set(eligible)),
        recommended_actions=actions,
        started_at=started_at,
        completed_at=completed,
        total_duration_ms=duration,
    )


def _update_registry(module: str, status: str):
    _pipeline_registry.module_statuses[module] = status
