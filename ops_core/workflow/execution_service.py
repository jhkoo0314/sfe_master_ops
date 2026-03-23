from __future__ import annotations

"""
Runtime execution service for Sales Data OS.

This module handles the real execution path used by the console and scripts:
- intake preparation
- staged input activation
- adapter/validation script execution
- summary collection

It is separate from ``ops_core.workflow.orchestrator``, which evaluates
already-produced Result Assets through the Validation Layer (OPS) API flow.
"""

import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from common.company_profile import get_company_ops_profile
from ops_core.workflow.execution_models import (
    ExecutionContext,
    ExecutionLoopResult,
    ExecutionPreparationResult,
    ExecutionRunResult,
    ExecutionStepDefinition,
    ExecutionStepResult,
)
from ops_core.workflow.execution_registry import (
    get_execution_mode_label,
    get_mode_pipeline_steps,
    get_mode_required_uploads,
    get_summary_relative_path,
)
from ops_core.workflow.execution_runtime import (
    activate_execution_runtime,
    cleanup_execution_runtime,
    inspect_intake_inputs,
    prepare_execution_inputs,
    stage_uploaded_sources,
)


def build_execution_context(
    *,
    project_root: str | Path,
    company_key: str,
    company_name: str,
    source_targets: Mapping[str, tuple[str, str]] | None = None,
) -> ExecutionContext:
    root = Path(project_root)
    resolved_targets = (
        source_targets
        if source_targets is not None
        else get_company_ops_profile(company_key).resolved_source_targets(root, company_key)
    )
    return ExecutionContext(
        project_root=str(root),
        company_key=company_key,
        company_name=company_name,
        source_targets=resolved_targets,
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_summary_path(context: ExecutionContext, module: str) -> Path | None:
    relative_path = get_summary_relative_path(module)
    if relative_path is None:
        return None
    return Path(context.project_root) / "data" / "ops_validation" / context.company_key / Path(relative_path)


def _build_step_result(
    *,
    context: ExecutionContext,
    step_definition: ExecutionStepDefinition,
    duration_ms: int,
) -> ExecutionStepResult:
    summary_path = get_summary_path(context, step_definition.module)
    summary_payload = None
    if summary_path and summary_path.exists():
        summary_payload = _read_json(summary_path)

    if step_definition.module == "builder":
        if summary_payload is not None:
            built_count = sum(
                1
                for key in ["crm_analysis", "sandbox_report", "territory_map", "prescription_flow", "radar_report", "total_valid"]
                if key in summary_payload
            )
            return ExecutionStepResult(
                step=0,
                module=step_definition.module,
                status="PASS",
                score=100.0,
                duration_ms=duration_ms,
                reasoning_note=f"{step_definition.label} 완료. 생성 보고서 {built_count}건.",
                summary_path=str(summary_path),
                summary=summary_payload,
            )
    elif summary_payload is not None:
        status = str(summary_payload.get("quality_status", "warn")).upper()
        score = float(summary_payload.get("quality_score", 0.0))
        return ExecutionStepResult(
            step=0,
            module=step_definition.module,
            status=status,
            score=score,
            duration_ms=duration_ms,
            reasoning_note=f"{step_definition.label} 완료. 품질 {status} / 점수 {score:.1f}",
            next_modules=list(summary_payload.get("next_modules", [])),
            summary_path=str(summary_path),
            summary=summary_payload,
        )

    return ExecutionStepResult(
        step=0,
        module=step_definition.module,
        status="WARN",
        score=0.0,
        duration_ms=duration_ms,
        reasoning_note=f"{step_definition.label}는 실행됐지만 결과 요약 파일을 찾지 못했습니다.",
        summary_path=str(summary_path) if summary_path else None,
    )


def _run_execution_steps(
    *,
    context: ExecutionContext,
    execution_mode: str,
    initial_actions: list[str] | None = None,
) -> ExecutionLoopResult:
    steps: list[ExecutionStepResult] = []
    final_eligible_modules: list[str] = []
    summary_by_module: dict[str, dict[str, Any]] = {}
    recommended_actions = list(initial_actions or [])

    for index, step_definition in enumerate(get_mode_pipeline_steps(execution_mode), start=1):
        started = time.time()
        try:
            step_definition.runner()
            step_result = _build_step_result(
                context=context,
                step_definition=step_definition,
                duration_ms=int((time.time() - started) * 1000),
            )
        except Exception as exc:
            step_result = ExecutionStepResult(
                step=0,
                module=step_definition.module,
                status="FAIL",
                score=0.0,
                duration_ms=int((time.time() - started) * 1000),
                reasoning_note=f"{step_definition.label} 실패: {exc}",
                error=str(exc),
            )
        step_result.step = index
        steps.append(step_result)
        if step_result.summary is not None:
            summary_by_module[step_result.module] = step_result.summary
        if step_result.status == "FAIL":
            if step_result.error:
                recommended_actions.append(f"{step_definition.module.upper()} 단계 실행 오류를 먼저 해결해야 합니다.")
                break
            recommended_actions.append(
                f"{step_definition.module.upper()} 단계 품질은 FAIL이지만, 다음 단계 진단을 위해 통합 실행을 계속 진행했습니다."
            )
            continue
        for next_module in step_result.next_modules:
            if next_module not in final_eligible_modules:
                final_eligible_modules.append(next_module)

    return ExecutionLoopResult(
        steps=steps,
        final_eligible_modules=final_eligible_modules,
        summary_by_module=summary_by_module,
        recommended_actions=recommended_actions,
    )


def run_runtime_execution_mode(
    *,
    context: ExecutionContext,
    execution_mode: str,
    uploaded: Mapping[str, dict[str, Any] | None] | None = None,
) -> ExecutionRunResult:
    os.environ["OPS_COMPANY_KEY"] = context.company_key
    os.environ["OPS_COMPANY_NAME"] = context.company_name

    preparation = prepare_execution_inputs(
        context=context,
        execution_mode=execution_mode,
        uploaded=uploaded,
    )
    started_at = datetime.now()

    try:
        activate_execution_runtime(preparation)
        loop_result = _run_execution_steps(
            context=context,
            execution_mode=execution_mode,
            initial_actions=preparation.recommended_actions,
        )
    finally:
        cleanup_execution_runtime()

    statuses = [step.status for step in loop_result.steps]
    overall_status = "FAIL" if "FAIL" in statuses else "WARN" if "WARN" in statuses else "PASS"
    scores = [step.score for step in loop_result.steps if step.score > 0]
    total_duration_ms = int((datetime.now() - started_at).total_seconds() * 1000)

    return ExecutionRunResult(
        run_id=str(uuid.uuid4()),
        execution_mode=execution_mode,
        execution_mode_label=get_execution_mode_label(execution_mode),
        company_key=context.company_key,
        company_name=context.company_name,
        overall_status=overall_status,
        overall_score=round(sum(scores) / len(scores), 1) if scores else 0.0,
        steps=loop_result.steps,
        final_eligible_modules=loop_result.final_eligible_modules,
        recommended_actions=loop_result.recommended_actions,
        total_duration_ms=total_duration_ms,
        summary_by_module=loop_result.summary_by_module,
    )


def run_execution_mode(
    *,
    context: ExecutionContext,
    execution_mode: str,
    uploaded: Mapping[str, dict[str, Any] | None] | None = None,
) -> ExecutionRunResult:
    """
    Backward-compatible wrapper.

    Prefer ``run_runtime_execution_mode`` for new code so the role is explicit.
    """
    return run_runtime_execution_mode(
        context=context,
        execution_mode=execution_mode,
        uploaded=uploaded,
    )
