from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from common.runtime_helpers import clear_sales_data_os_script_runtime
from modules.intake import (
    IntakeResult,
    activate_intake_source_root,
    build_intake_result,
    clear_intake_source_root,
    merge_monthly_raw_sources,
    prepare_intake_staged_sources,
)
from ops_core.workflow.execution_models import ExecutionContext, ExecutionPreparationResult


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
    return build_intake_result(
        project_root=context.project_root,
        company_key=context.company_key,
        company_name=context.company_name,
        source_targets=context.source_targets,
        uploaded=uploaded,
        execution_mode=execution_mode,
    )


def collect_intake_blockers(intake_result: IntakeResult) -> list[str]:
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


def build_intake_blocker_message(intake_result: IntakeResult) -> str:
    blocker_messages = collect_intake_blockers(intake_result)
    if blocker_messages:
        return "; ".join(blocker_messages[:5])
    return "intake 결과를 먼저 확인해야 합니다."


def prepare_execution_inputs(
    *,
    context: ExecutionContext,
    execution_mode: str,
    uploaded: Mapping[str, dict[str, Any] | None] | None = None,
) -> ExecutionPreparationResult:
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
        details = build_intake_blocker_message(intake_result)
        raise ValueError(f"Intake Gate에서 Adapter 전달이 보류되었습니다: {details}")

    staged_source_root = prepare_intake_staged_sources(
        project_root=context.project_root,
        company_key=context.company_key,
        intake_result=intake_result,
    )

    recommended_actions: list[str] = []
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
        recommended_actions.append(f"monthly_raw를 감지해 자동 병합했습니다: {merged_labels}.")

    return ExecutionPreparationResult(
        monthly_merge_result=monthly_merge_result,
        staged_paths=staged_paths,
        intake_result=intake_result,
        staged_source_root=str(staged_source_root),
        recommended_actions=recommended_actions,
    )


def activate_execution_runtime(preparation: ExecutionPreparationResult) -> None:
    activate_intake_source_root(preparation.staged_source_root)
    clear_sales_data_os_script_runtime()


def cleanup_execution_runtime() -> None:
    clear_intake_source_root()
    clear_sales_data_os_script_runtime()
