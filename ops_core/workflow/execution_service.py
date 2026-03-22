from __future__ import annotations

import io
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from modules.intake import ensure_staged_source_copy
from common.company_profile import get_company_ops_profile
from modules.intake import IntakeResult, build_intake_result
from ops_core.workflow.execution_models import (
    ExecutionContext,
    ExecutionRunResult,
    ExecutionStepDefinition,
    ExecutionStepResult,
)
from ops_core.workflow.monthly_source_merge import merge_monthly_raw_sources
from ops_core.workflow.execution_registry import (
    clear_execution_step_registry_cache,
    clear_execution_runtime_modules,
    get_execution_mode_label,
    get_mode_pipeline_steps,
    get_mode_required_uploads,
    get_summary_relative_path,
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


def _load_upload_frame(info: dict[str, Any]) -> pd.DataFrame:
    file_bytes = info["file_bytes"]
    if str(info["name"]).lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    return pd.read_excel(io.BytesIO(file_bytes))


def stage_uploaded_sources(
    *,
    context: ExecutionContext,
    uploaded: Mapping[str, dict[str, Any] | None] | None,
) -> list[str]:
    staged_paths: list[str] = []
    for module_key, info in (uploaded or {}).items():
        if not info or "file_bytes" not in info:
            continue
        target_path, target_format = context.source_targets[module_key]
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target_format == "excel":
            df = _load_upload_frame(info)
            df.to_excel(target, index=False)
        else:
            if info.get("file_ext") == ".csv":
                target.write_bytes(info["file_bytes"])
            else:
                df = _load_upload_frame(info)
                df.to_csv(target, index=False, encoding="utf-8-sig")
        staged_paths.append(str(target))
    return staged_paths


def inspect_intake_inputs(
    *,
    context: ExecutionContext,
    execution_mode: str | None = None,
    uploaded: Mapping[str, dict[str, Any] | None] | None = None,
) -> IntakeResult:
    """
    Phase 1 common intake interface.

    This does not change the existing adapter or pipeline flow yet.
    It only provides one shared contract that later phases can extend with
    scenarios, mapping rules, auto-fixes, and staging outputs.
    """
    return build_intake_result(
        project_root=context.project_root,
        company_key=context.company_key,
        company_name=context.company_name,
        source_targets=context.source_targets,
        uploaded=uploaded,
        execution_mode=execution_mode,
    )


def _collect_intake_blockers(intake_result: IntakeResult) -> list[str]:
    blockers: list[str] = []
    for package in intake_result.packages:
        if package.status not in ("blocked", "needs_review"):
            continue
        for finding in package.findings:
            blockers.append(f"{package.source_key}: {finding.message}")
        for suggestion in package.suggestions:
            if suggestion.suggestion_type == "mapping_review_required":
                blockers.append(f"{package.source_key}: {suggestion.message}")
    return blockers


def _prepare_staged_source_root(
    *,
    context: ExecutionContext,
    intake_result: IntakeResult,
) -> Path:
    staged_root = Path(context.project_root) / "data" / "company_source" / context.company_key / "_intake_staging"
    for package in intake_result.packages:
        staged_path = Path(package.staged_path)
        if staged_path.exists() and staged_root in staged_path.parents:
            continue
        copied_path = ensure_staged_source_copy(
            project_root=context.project_root,
            company_key=context.company_key,
            source_key=package.source_key,
            source_target_path=package.original_path,
            original_path=package.original_path,
        )
        if copied_path is not None:
            package.staged_path = str(copied_path)
    return staged_root


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


def _validate_required_inputs(
    *,
    context: ExecutionContext,
    execution_mode: str,
    uploaded: Mapping[str, dict[str, Any] | None] | None,
) -> None:
    missing_inputs: list[str] = []
    for key in get_mode_required_uploads(execution_mode):
        target_path, _ = context.source_targets[key]
        if (uploaded or {}).get(key) is None and not Path(target_path).exists():
            missing_inputs.append(key)
    if missing_inputs:
        raise ValueError(f"필수 원천 파일이 부족합니다: {', '.join(missing_inputs)}")


def run_execution_mode(
    *,
    context: ExecutionContext,
    execution_mode: str,
    uploaded: Mapping[str, dict[str, Any] | None] | None = None,
) -> ExecutionRunResult:
    os.environ["OPS_COMPANY_KEY"] = context.company_key
    os.environ["OPS_COMPANY_NAME"] = context.company_name

    uploaded_keys = {key for key, value in (uploaded or {}).items() if value is not None}
    monthly_merge_result = merge_monthly_raw_sources(
        source_targets=context.source_targets,
        skip_keys=uploaded_keys,
    )
    staged_paths = stage_uploaded_sources(context=context, uploaded=uploaded)
    intake_result = inspect_intake_inputs(
        context=context,
        execution_mode=execution_mode,
        uploaded=uploaded,
    )
    if not intake_result.ready_for_adapter:
        blocker_messages = _collect_intake_blockers(intake_result)
        details = "; ".join(blocker_messages[:5]) if blocker_messages else "intake 결과를 먼저 확인해야 합니다."
        raise ValueError(f"Intake Gate에서 Adapter 전달이 보류되었습니다: {details}")

    staged_source_root = _prepare_staged_source_root(context=context, intake_result=intake_result)
    os.environ["OPS_COMPANY_SOURCE_ROOT"] = str(staged_source_root)
    clear_execution_runtime_modules()

    started_at = datetime.now()
    steps: list[ExecutionStepResult] = []
    recommended_actions: list[str] = []
    final_eligible_modules: list[str] = []
    summary_by_module: dict[str, dict[str, Any]] = {}

    if staged_paths:
        recommended_actions.append(f"업로드 파일 {len(staged_paths)}건을 실제 소스 경로에 반영했습니다.")
    else:
        recommended_actions.append("새로 업로드한 파일이 없어 기존 company_source 데이터를 사용했습니다.")
    recommended_actions.append(f"Intake staging 경로를 Adapter 입력으로 사용합니다: {staged_source_root}")
    if monthly_merge_result.merged_sources:
        merged_labels = ", ".join(
            f"{source_key}({count}개월)"
            for source_key, count in monthly_merge_result.merged_sources.items()
        )
        recommended_actions.append(
            f"monthly_raw를 감지해 자동 병합했습니다: {merged_labels}."
        )

    try:
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
                recommended_actions.append(f"{step_definition.module.upper()} 단계 오류를 먼저 해결해야 합니다.")
                break
            for next_module in step_result.next_modules:
                if next_module not in final_eligible_modules:
                    final_eligible_modules.append(next_module)
    finally:
        os.environ.pop("OPS_COMPANY_SOURCE_ROOT", None)
        clear_execution_runtime_modules()

    statuses = [step.status for step in steps]
    overall_status = "FAIL" if "FAIL" in statuses else "WARN" if "WARN" in statuses else "PASS"
    scores = [step.score for step in steps if step.score > 0]
    total_duration_ms = int((datetime.now() - started_at).total_seconds() * 1000)

    return ExecutionRunResult(
        run_id=str(uuid.uuid4()),
        execution_mode=execution_mode,
        execution_mode_label=get_execution_mode_label(execution_mode),
        company_key=context.company_key,
        company_name=context.company_name,
        overall_status=overall_status,
        overall_score=round(sum(scores) / len(scores), 1) if scores else 0.0,
        steps=steps,
        final_eligible_modules=final_eligible_modules,
        recommended_actions=recommended_actions,
        total_duration_ms=total_duration_ms,
        summary_by_module=summary_by_module,
    )
