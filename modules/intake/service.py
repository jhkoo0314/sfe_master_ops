from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from common.company_onboarding_registry import load_company_onboarding_registry
from ops_core.workflow.execution_registry import get_mode_required_uploads
from .fixers import apply_basic_intake_fixes
from .models import (
    IntakeFinding,
    IntakeFix,
    IntakeRequest,
    IntakeResult,
    IntakeSourceInput,
    IntakeSuggestion,
    OnboardingPackage,
)
from .rules import get_intake_rule
from .scenarios import resolve_intake_scenario
from .suggestions import (
    build_mapping_review_suggestion,
    build_missing_required_field_suggestion,
    build_optional_field_suggestion,
    build_optional_source_missing_suggestion,
    build_saved_mapping_fallback_suggestion,
)
from .staging import (
    save_intake_result_snapshot,
    save_onboarding_package,
    stage_intake_dataframe,
    update_onboarding_registry_from_result,
)


def _normalize_column_name(name: str) -> str:
    return "".join(ch for ch in str(name).strip().lower() if ch.isalnum())


def _resolve_mapping(columns: list[str], source_key: str) -> tuple[dict[str, str], list[str], list[str]]:
    rule = get_intake_rule(source_key)
    if rule is None:
        return {}, [], []

    normalized_columns = {
        _normalize_column_name(column): column
        for column in columns
    }
    resolved_mapping: dict[str, str] = {}
    missing_required: list[str] = []
    missing_review: list[str] = []

    for semantic_field, aliases in rule.field_aliases.items():
        matched_column = None
        for alias in aliases:
            matched_column = normalized_columns.get(_normalize_column_name(alias))
            if matched_column:
                break
        if matched_column:
            resolved_mapping[semantic_field] = matched_column
        elif semantic_field in rule.required_fields:
            missing_required.append(semantic_field)
        elif semantic_field in rule.review_fields:
            missing_review.append(semantic_field)

    return resolved_mapping, missing_required, missing_review


class CommonIntakeEngine:
    """
    Common intake entry point for Sales Data OS.

    Phase 1 only fixes the input/output contract.
    Detailed scenario, mapping, rule, auto-fix, and staging logic will be
    added in later phases without changing this public interface.
    """

    def inspect(self, request: IntakeRequest) -> IntakeResult:
        registry = load_company_onboarding_registry(request.project_root, request.company_key)
        scenario = resolve_intake_scenario(
            execution_mode=request.execution_mode,
            source_keys=[source.source_key for source in request.sources],
        )
        active_source_keys = set(scenario.source_keys)
        packages: list[OnboardingPackage] = []
        findings: list[IntakeFinding] = []
        fixes: list[IntakeFix] = []
        suggestions: list[IntakeSuggestion] = []

        for source in request.sources:
            package_findings: list[IntakeFinding] = []
            package_fixes: list[IntakeFix] = list(source.fixes)
            package_suggestions: list[IntakeSuggestion] = []
            status = "ready_with_fixes" if package_fixes else "ready"
            resolved_mapping: dict[str, str] = {}
            source_rule = get_intake_rule(source.source_key)
            stored_mapping = (
                registry.get("source_mappings", {}).get(source.source_key, {})
                if isinstance(registry.get("source_mappings"), dict)
                else {}
            )

            if source.source_key not in active_source_keys and not source.is_required:
                package = OnboardingPackage(
                    company_key=request.company_key,
                    source_key=source.source_key,
                    original_path=source.original_path,
                    staged_path=source.target_path,
                    status=status,
                    scenario_key=scenario.key,
                    scenario_label=scenario.label,
                    findings=package_findings,
                    fixes=package_fixes,
                    suggestions=package_suggestions,
                    resolved_mapping=resolved_mapping,
                    ready_for_adapter=True,
                )
                fixes.extend(package_fixes)
                packages.append(package)
                continue

            if not source.upload_present and not Path(source.original_path).exists():
                if source.is_required:
                    status = "blocked"
                    package_findings.append(
                        IntakeFinding(
                            level="error",
                            source_key=source.source_key,
                            issue_code="missing_source",
                            message="업로드된 파일이 없고 기존 source 경로에도 파일이 없습니다.",
                        )
                    )
                else:
                    package_suggestions.append(build_optional_source_missing_suggestion(source.source_key))
            elif source.columns:
                inferred_mapping, missing_required, missing_review = _resolve_mapping(source.columns, source.source_key)
                resolved_mapping.update(
                    {
                        semantic_field: actual_column
                        for semantic_field, actual_column in stored_mapping.items()
                        if actual_column in source.columns
                    }
                )
                for semantic_field, actual_column in inferred_mapping.items():
                    resolved_mapping.setdefault(semantic_field, actual_column)

                for semantic_field in missing_required:
                    if semantic_field in resolved_mapping:
                        continue
                    status = "needs_review"
                    package_findings.append(
                        IntakeFinding(
                            level="warn",
                            source_key=source.source_key,
                            issue_code="missing_required_semantic_field",
                            message=f"필수 의미 컬럼 `{semantic_field}` 를 아직 확정하지 못했습니다.",
                            column_name=semantic_field,
                        )
                    )
                    if source_rule is not None:
                        package_suggestions.append(
                            build_missing_required_field_suggestion(
                                source_key=source.source_key,
                                semantic_field=semantic_field,
                                columns=source.columns,
                                rule=source_rule,
                            )
                        )

                for semantic_field in missing_review:
                    if semantic_field in resolved_mapping:
                        continue
                    if source_rule is not None:
                        package_suggestions.append(
                            build_optional_field_suggestion(
                                source_key=source.source_key,
                                semantic_field=semantic_field,
                                columns=source.columns,
                                rule=source_rule,
                            )
                        )
                if source_rule is not None and not resolved_mapping and source.columns:
                    package_suggestions.append(
                        build_mapping_review_suggestion(
                            source_key=source.source_key,
                            columns=source.columns,
                            rule=source_rule,
                        )
                    )
            elif source_rule is not None:
                package_suggestions.append(build_saved_mapping_fallback_suggestion(source.source_key))

            blocking_suggestion_types = {"mapping_review_required"}
            if status in ("ready", "ready_with_fixes") and any(
                suggestion.suggestion_type in blocking_suggestion_types
                for suggestion in package_suggestions
            ):
                status = "needs_review"

            package = OnboardingPackage(
                company_key=request.company_key,
                source_key=source.source_key,
                original_path=source.original_path,
                staged_path=source.target_path,
                status=status,
                scenario_key=scenario.key,
                scenario_label=scenario.label,
                findings=package_findings,
                fixes=package_fixes,
                suggestions=package_suggestions,
                resolved_mapping=resolved_mapping,
                ready_for_adapter=(status not in ("blocked", "needs_review")),
            )
            findings.extend(package_findings)
            fixes.extend(package_fixes)
            suggestions.extend(package_suggestions)
            packages.append(package)

        if any(pkg.status == "blocked" for pkg in packages):
            result_status = "blocked"
        elif any(pkg.status == "needs_review" for pkg in packages):
            result_status = "needs_review"
        elif any(pkg.status == "ready_with_fixes" for pkg in packages):
            result_status = "ready_with_fixes"
        else:
            result_status = "ready"
        return IntakeResult(
            company_key=request.company_key,
            company_name=request.company_name,
            status=result_status,
            scenario_key=scenario.key,
            scenario_label=scenario.label,
            findings=findings,
            fixes=fixes,
            suggestions=suggestions,
            packages=packages,
        )


def build_intake_result(
    *,
    project_root: str | Path,
    company_key: str,
    company_name: str,
    source_targets: Mapping[str, tuple[str, str]],
    uploaded: Mapping[str, dict[str, object] | None] | None = None,
    execution_mode: str | None = None,
) -> IntakeResult:
    sources: list[IntakeSourceInput] = []
    staged_frames: dict[str, Any] = {}
    required_source_keys = set(get_mode_required_uploads(execution_mode)) if execution_mode else set()
    for source_key, (target_path, _target_format) in source_targets.items():
        info = (uploaded or {}).get(source_key)
        file_name = None
        file_ext = None
        row_count = None
        columns: list[str] = []
        preview_rows: list[dict[str, Any]] = []
        upload_present = False
        package_fixes = []
        if info is not None:
            file_name = str(info.get("name") or "")
            file_ext = str(info.get("file_ext") or "")
            fixer_result = apply_basic_intake_fixes(source_key, info)
            staged_frames[source_key] = fixer_result.dataframe
            row_count = fixer_result.row_count
            columns = fixer_result.columns
            preview_rows = fixer_result.preview_rows
            package_fixes = fixer_result.fixes
            upload_present = True

        sources.append(
            IntakeSourceInput(
            source_key=source_key,
            original_path=str(target_path),
            target_path=str(target_path),
            file_name=file_name,
            file_ext=file_ext,
                row_count=row_count,
                columns=columns,
                preview_rows=preview_rows,
                fixes=package_fixes,
                is_required=(source_key in required_source_keys),
                upload_present=upload_present,
        )
        )

    request = IntakeRequest(
        project_root=str(project_root),
        company_key=company_key,
        company_name=company_name,
        execution_mode=execution_mode,
        sources=sources,
    )
    result = CommonIntakeEngine().inspect(request)

    for package in result.packages:
        dataframe = staged_frames.get(package.source_key)
        if dataframe is not None:
            staged_path = stage_intake_dataframe(
                project_root=project_root,
                company_key=company_key,
                source_key=package.source_key,
                source_target_path=package.original_path,
                dataframe=dataframe,
            )
            package.staged_path = str(staged_path)
        save_onboarding_package(project_root, company_key, package.to_dict())

    save_intake_result_snapshot(project_root, result)
    update_onboarding_registry_from_result(project_root, result)
    return result
