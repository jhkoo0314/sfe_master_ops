from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from common.company_onboarding_registry import load_company_onboarding_registry
from modules.validation.workflow.execution_registry import get_mode_required_uploads
from .fixers import apply_basic_intake_fixes
from .models import (
    IntakeFinding,
    IntakeFix,
    IntakePeriodCoverage,
    IntakeRequest,
    IntakeResult,
    IntakeSourceInput,
    IntakeSuggestion,
    IntakeTimingAlert,
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


_SOURCE_LABELS = {
    "crm_activity": "CRM 활동",
    "crm_rep_master": "담당자 / 조직 마스터",
    "crm_account_assignment": "거래처 담당 배정",
    "crm_rules": "CRM 규칙",
    "sales": "실적",
    "target": "목표",
    "prescription": "처방",
}


def _normalize_column_name(name: str) -> str:
    return "".join(ch for ch in str(name).strip().lower() if ch.isalnum())


def _format_month_token(month_token: str) -> str:
    if len(month_token) == 6 and month_token.isdigit():
        return f"{month_token[:4]}-{month_token[4:6]}"
    return month_token


def _month_to_index(month_token: str) -> int:
    return int(month_token[:4]) * 12 + int(month_token[4:6])


def _month_gap(from_month: str, to_month: str) -> int:
    return abs(_month_to_index(from_month) - _month_to_index(to_month))


def _read_source_frame(path: str | Path) -> pd.DataFrame | None:
    source_path = Path(path)
    if not source_path.exists():
        return None
    suffix = source_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(source_path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(source_path)
    return None


def _normalize_month_value(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)) or pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    compact = re.sub(r"[^0-9]", "", text)
    if len(compact) >= 6:
        year = compact[:4]
        month = compact[4:6]
        if year.isdigit() and month.isdigit() and 1 <= int(month) <= 12:
            return f"{year}{month}"

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return f"{parsed.year:04d}{parsed.month:02d}"


def _resolve_period_column(
    source_key: str,
    columns: list[str],
    resolved_mapping: dict[str, str],
) -> str | None:
    preferred_fields = {
        "crm_activity": ("activity_date",),
        "sales": ("period",),
        "target": ("period",),
        "prescription": ("ship_date",),
    }.get(source_key, ())
    for field_name in preferred_fields:
        column_name = resolved_mapping.get(field_name)
        if column_name in columns:
            return column_name

    lowered_columns = {str(column).lower(): column for column in columns}
    for token in ("yyyymm", "metric_month", "month", "date", "월", "출고일", "활동일", "방문일"):
        for lowered, original in lowered_columns.items():
            if token in lowered:
                return original
    return None


def _build_period_coverage(
    *,
    source_key: str,
    columns: list[str],
    dataframe: pd.DataFrame | None,
    resolved_mapping: dict[str, str],
) -> IntakePeriodCoverage | None:
    if dataframe is None or dataframe.empty or not columns:
        return None

    period_column = _resolve_period_column(source_key, columns, resolved_mapping)
    if period_column is None or period_column not in dataframe.columns:
        return None

    normalized_months = [
        month_token
        for month_token in dataframe[period_column].map(_normalize_month_value).tolist()
        if month_token is not None
    ]
    distinct_months = sorted(set(normalized_months))
    if not distinct_months:
        return None

    return IntakePeriodCoverage(
        source_key=source_key,
        period_column=str(period_column),
        start_month=distinct_months[0],
        end_month=distinct_months[-1],
        month_count=len(distinct_months),
        distinct_months=distinct_months,
    )


def _build_timing_summary(
    *,
    scenario: Any,
    coverages: dict[str, IntakePeriodCoverage],
) -> tuple[list[IntakeTimingAlert], list[str], str | None, str | None, int | None, str | None, str | None]:
    analysis_source_keys = [source_key for source_key in scenario.analysis_source_keys if source_key in coverages]
    if not analysis_source_keys:
        analysis_source_keys = list(coverages.keys())
    if not analysis_source_keys:
        return [], [], None, None, None, None, None

    common_months: set[str] | None = None
    for source_key in analysis_source_keys:
        source_months = set(coverages[source_key].distinct_months)
        common_months = source_months if common_months is None else common_months & source_months

    sorted_common_months = sorted(common_months or [])
    analysis_start = sorted_common_months[0] if sorted_common_months else None
    analysis_end = sorted_common_months[-1] if sorted_common_months else None
    analysis_month_count = len(sorted_common_months) if sorted_common_months else None

    timing_alerts: list[IntakeTimingAlert] = []
    if analysis_end is not None:
        for source_key, coverage in coverages.items():
            if coverage.end_month == analysis_end:
                continue
            source_label = _SOURCE_LABELS.get(source_key, source_key)
            month_gap = _month_gap(coverage.end_month, analysis_end)
            if _month_to_index(coverage.end_month) > _month_to_index(analysis_end):
                timing_alerts.append(
                    IntakeTimingAlert(
                        level="warn",
                        source_key=source_key,
                        message=(
                            f"{source_label} 데이터는 공통 분석 기준 종료월 {_format_month_token(analysis_end)}보다 "
                            f"{month_gap}개월 앞서 있습니다."
                        ),
                        direction="ahead",
                        month_gap=month_gap,
                        reference_end_month=analysis_end,
                    )
                )
            else:
                timing_alerts.append(
                    IntakeTimingAlert(
                        level="warn",
                        source_key=source_key,
                        message=(
                            f"{source_label} 데이터는 공통 분석 기준 종료월 {_format_month_token(analysis_end)}보다 "
                            f"{month_gap}개월 이전 데이터까지만 있습니다."
                        ),
                        direction="behind",
                        month_gap=month_gap,
                        reference_end_month=analysis_end,
                    )
                )

    if analysis_month_count and analysis_start and analysis_end and timing_alerts:
        analysis_summary_message = (
            f"일부 입력 데이터의 기간이 서로 다르지만, 공통 분석 구간 "
            f"{_format_month_token(analysis_start)} ~ {_format_month_token(analysis_end)} 기준 "
            f"{analysis_month_count}개월 검증은 진행 가능합니다."
        )
        proceed_confirmation_message = (
            f"일부 입력 데이터의 기간이 서로 다릅니다. 그래도 공통 분석 구간 "
            f"{_format_month_token(analysis_start)} ~ {_format_month_token(analysis_end)} 기준 "
            f"{analysis_month_count}개월 검증을 계속 진행할까요?"
        )
    elif analysis_month_count and analysis_start and analysis_end:
        analysis_summary_message = (
            f"현재 공통 분석 구간은 {_format_month_token(analysis_start)} ~ "
            f"{_format_month_token(analysis_end)} 총 {analysis_month_count}개월입니다."
        )
        proceed_confirmation_message = None
    elif timing_alerts:
        analysis_summary_message = "입력 데이터의 기간 차이는 감지됐지만, 공통 분석 구간을 자동으로 확정하지 못했습니다."
        proceed_confirmation_message = "입력 데이터 기간 차이를 먼저 확인한 뒤 계속 진행할지 결정해야 합니다."
    else:
        analysis_summary_message = None
        proceed_confirmation_message = None

    return (
        timing_alerts,
        analysis_source_keys,
        analysis_start,
        analysis_end,
        analysis_month_count,
        analysis_summary_message,
        proceed_confirmation_message,
    )


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
    source_frames: dict[str, Any] = {}
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
            source_frames[source_key] = fixer_result.dataframe
            row_count = fixer_result.row_count
            columns = fixer_result.columns
            preview_rows = fixer_result.preview_rows
            package_fixes = fixer_result.fixes
            upload_present = True
        else:
            existing_frame = _read_source_frame(target_path)
            if existing_frame is not None:
                source_frames[source_key] = existing_frame
                row_count = int(len(existing_frame))
                columns = [str(column) for column in existing_frame.columns]
                preview_rows = existing_frame.head(3).to_dict("records")
                file_name = Path(target_path).name
                file_ext = Path(target_path).suffix.lower()

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
    scenario = resolve_intake_scenario(
        execution_mode=execution_mode,
        source_keys=[package.source_key for package in result.packages],
    )

    coverages: dict[str, IntakePeriodCoverage] = {}

    for package in result.packages:
        dataframe = source_frames.get(package.source_key)
        period_coverage = _build_period_coverage(
            source_key=package.source_key,
            columns=next((source.columns for source in sources if source.source_key == package.source_key), []),
            dataframe=dataframe,
            resolved_mapping=package.resolved_mapping,
        )
        package.period_coverage = period_coverage
        if period_coverage is not None:
            coverages[package.source_key] = period_coverage

        if dataframe is not None:
            if (uploaded or {}).get(package.source_key) is not None:
                staged_path = stage_intake_dataframe(
                    project_root=project_root,
                    company_key=company_key,
                    source_key=package.source_key,
                    source_target_path=package.original_path,
                    dataframe=dataframe,
                )
                package.staged_path = str(staged_path)
        save_onboarding_package(project_root, company_key, package.to_dict())

    (
        result.timing_alerts,
        result.analysis_basis_sources,
        result.analysis_start_month,
        result.analysis_end_month,
        result.analysis_month_count,
        result.analysis_summary_message,
        result.proceed_confirmation_message,
    ) = _build_timing_summary(
        scenario=scenario,
        coverages=coverages,
    )
    result.period_coverages = list(coverages.values())

    save_intake_result_snapshot(project_root, result)
    update_onboarding_registry_from_result(project_root, result)
    return result
