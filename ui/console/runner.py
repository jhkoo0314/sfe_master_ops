from __future__ import annotations

import json
import random
import time
import uuid
from datetime import datetime
from pathlib import Path

from common.run_storage.runs import save_pipeline_run_to_supabase
from modules.intake import inspect_monthly_raw
from modules.validation.workflow.execution_registry import (
    get_execution_mode_label,
    get_execution_mode_modules,
    get_mode_pipeline_steps as workflow_get_mode_pipeline_steps,
    get_mode_required_uploads,
)
from modules.validation.workflow.execution_service import (
    build_execution_context,
    inspect_intake_inputs,
    run_execution_mode,
)
from ui.console.analysis_explainer import explain_module_result
import streamlit as st
from ui.console.paths import (
    get_active_company_key,
    get_active_company_name,
    get_project_root,
    get_source_target_map,
)


def _confidence_grade_from_score(score: float) -> str:
    if score >= 95:
        return "A"
    if score >= 85:
        return "B"
    return "C"


def _build_local_run_artifacts_index(result: dict) -> list[dict]:
    artifacts: list[dict] = []
    for step in result.get("steps", []):
        summary_path = str(step.get("summary_path") or "").strip()
        if not summary_path:
            continue
        artifacts.append(
            {
                "artifact_type": f"{step.get('module', 'module')}_validation_summary",
                "artifact_role": "validation_summary",
                "artifact_name": Path(summary_path).name,
                "artifact_class": "intermediate",
                "storage_path": summary_path,
                "mime_type": "application/json",
                "payload": {
                    "module": step.get("module"),
                    "reasoning_note": step.get("reasoning_note"),
                },
            }
        )

    builder_stage = (result.get("summary_by_module") or {}).get("builder", {})
    if isinstance(builder_stage, dict):
        for report_key, artifact_group in builder_stage.items():
            if not isinstance(artifact_group, dict):
                continue
            for file_role, file_path in artifact_group.items():
                if not isinstance(file_path, str) or not file_path.strip():
                    continue
                artifacts.append(
                    {
                        "artifact_type": {
                            "html": "report_html",
                            "input_standard": "report_input_standard",
                            "payload_standard": "report_payload_standard",
                            "result_asset": "report_result_asset",
                        }.get(file_role, f"report_{file_role}"),
                        "artifact_role": report_key,
                        "artifact_name": Path(file_path).name,
                        "artifact_class": "final" if file_role == "html" else "evidence",
                        "storage_path": file_path,
                        "mime_type": "text/html" if file_role == "html" else "application/json",
                        "payload": {
                            "report_key": report_key,
                            "file_role": file_role,
                        },
                    }
                )
    return artifacts


def _build_local_run_contexts(result: dict) -> tuple[dict, dict]:
    company_key = str(result.get("company_key") or "").strip() or get_active_company_key()
    run_id = str(result.get("run_id") or "").strip()
    overall_status = str(result.get("overall_status", "-")).upper()
    overall_score = float(result.get("overall_score", 0) or 0)
    mode = str(result.get("execution_mode", "") or "")
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")

    step_map = {
        str(step.get("module") or ""): (step.get("summary") or {})
        for step in result.get("steps", [])
        if isinstance(step, dict)
    }
    crm_summary = step_map.get("crm", {})
    rx_summary = step_map.get("prescription", {})
    sandbox_summary = step_map.get("sandbox", {})
    territory_summary = step_map.get("territory", {})
    radar_summary = step_map.get("radar", {})
    builder_summary = step_map.get("builder", {})

    evidence_index: list[dict[str, str]] = []
    linked_artifacts: list[dict[str, str]] = []
    if isinstance(builder_summary, dict):
        for report_key in ["crm_analysis", "sandbox_report", "territory_map", "prescription_flow", "radar_report", "total_valid"]:
            item = builder_summary.get(report_key)
            if not isinstance(item, dict):
                continue
            html_path = str(item.get("html") or "").strip()
            if html_path:
                evidence_index.append({"type": report_key, "path": html_path})
                linked_artifacts.append({"type": report_key, "path": html_path})

    priority_issues: list[str] = []
    radar_issue = str(radar_summary.get("top_issue") or "").strip()
    if radar_issue:
        priority_issues.append(radar_issue)
    if int(rx_summary.get("connected_hospital_count", 0) or 0) == 0 and int(rx_summary.get("flow_record_count", 0) or 0) > 0:
        priority_issues.append("Prescription 병원 연결 0건")

    key_findings: list[str] = []
    if crm_summary:
        key_findings.append(
            f"CRM 품질 {crm_summary.get('quality_status', '-')} / unmapped company {crm_summary.get('company_unmapped_count', '-')}"
        )
    if rx_summary:
        key_findings.append(
            f"Prescription completion {rx_summary.get('flow_completion_rate', '-')} / connected hospitals {rx_summary.get('connected_hospital_count', '-')}"
        )
    if sandbox_summary:
        key_findings.append(
            f"Sandbox 품질 {sandbox_summary.get('quality_status', '-')} / month count {sandbox_summary.get('metric_month_count', '-')}"
        )
    if territory_summary:
        key_findings.append(
            f"Territory 품질 {territory_summary.get('quality_status', '-')} / coverage {territory_summary.get('coverage_rate', '-')}"
        )
    if radar_issue:
        key_findings.append(f"RADAR top issue: {radar_issue}")

    executive_summary = (
        f"{company_key} 최신 run 요약입니다. 전체 상태는 {overall_status}, 점수는 {overall_score:.1f}, "
        f"Prescription 상태는 {str(rx_summary.get('quality_status', '-')).upper()}, "
        f"Sandbox 상태는 {str(sandbox_summary.get('quality_status', '-')).upper()} 입니다."
    )

    full_ctx = {
        "run_id": run_id,
        "company_key": company_key,
        "mode": mode,
        "generated_at": generated_at,
        "period": str(radar_summary.get("period_value") or "-"),
        "comparison_period": "-",
        "validation_summary": {
            "overall_status": overall_status,
            "overall_score": overall_score,
        },
        "confidence_grade": _confidence_grade_from_score(overall_score),
        "executive_summary": executive_summary,
        "key_findings": key_findings,
        "priority_issues": priority_issues,
        "evidence_index": evidence_index,
        "linked_artifacts": linked_artifacts,
        "step_status_map": {
            str(step.get("module") or ""): {
                "status": step.get("status"),
                "score": step.get("score"),
                "reasoning_note": step.get("reasoning_note"),
            }
            for step in result.get("steps", [])
            if isinstance(step, dict)
        },
    }
    prompt_ctx = {
        "run_id": run_id,
        "mode": mode,
        "generated_at": generated_at,
        "period": full_ctx["period"],
        "comparison_period": "-",
        "executive_summary": executive_summary,
        "top_findings": key_findings[:5],
        "priority_issues": priority_issues[:5],
        "answer_scope": "final_report_only",
        "forbidden_actions": ["recalculate_kpi", "raw_rejoin"],
    }
    return full_ctx, prompt_ctx


def _write_local_run_bundle(result: dict, uploaded: dict, analysis_markdown: str) -> None:
    run_id = str(result.get("run_id") or "").strip()
    if not run_id:
        return

    root = Path(get_project_root())
    company_key = str(result.get("company_key") or "").strip() or get_active_company_key()
    company_name = str(result.get("company_name") or "").strip() or get_active_company_name()
    run_dir = root / "data" / "ops_validation" / company_key / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "chat").mkdir(parents=True, exist_ok=True)

    full_ctx, prompt_ctx = _build_local_run_contexts(result)
    artifacts_index = _build_local_run_artifacts_index(result)
    finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
    overall_status = str(result.get("overall_status", "-")).upper()
    overall_score = float(result.get("overall_score", 0) or 0)

    run_meta = {
        "run_id": run_id,
        "mode": str(result.get("execution_mode", "") or ""),
        "finished_at": finished_at,
        "status": "success",
        "validation_status": overall_status,
        "confidence_grade": _confidence_grade_from_score(overall_score),
        "company_key": company_key,
        "company_name": company_name,
        "supabase_run_db_id": str(result.get("supabase_run_db_id") or "").strip(),
    }

    (run_dir / "run_meta.json").write_text(json.dumps(run_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "pipeline_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "report_context.full.json").write_text(json.dumps(full_ctx, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "report_context.prompt.json").write_text(json.dumps(prompt_ctx, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "artifacts.index.json").write_text(json.dumps(artifacts_index, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "execution_analysis.md").write_text(analysis_markdown, encoding="utf-8")


def _build_execution_analysis_markdown(result: dict, uploaded: dict) -> str:
    lines: list[str] = []
    lines.append(f"# Execution Analysis")
    lines.append("")
    lines.append(f"- company_key: `{get_active_company_key()}`")
    lines.append(f"- company_name: `{get_active_company_name()}`")
    lines.append(f"- execution_mode: `{result.get('execution_mode')}`")
    lines.append(f"- execution_mode_label: `{result.get('execution_mode_label')}`")
    lines.append(f"- overall_status: `{result.get('overall_status')}`")
    lines.append(f"- overall_score: `{result.get('overall_score')}`")
    lines.append(f"- total_duration_ms: `{result.get('total_duration_ms')}`")
    lines.append("")
    lines.append("## Steps")
    lines.append("")
    for step in result.get("steps", []):
        explanation = explain_module_result(str(step.get("module", "")), step)
        lines.append(f"### STEP {step.get('step')} - {str(step.get('module', '')).upper()}")
        lines.append(f"- status: `{step.get('status')}`")
        lines.append(f"- score: `{step.get('score')}`")
        lines.append(f"- duration_ms: `{step.get('duration_ms')}`")
        lines.append(f"- reasoning_note: {step.get('reasoning_note', '')}")
        lines.append(f"- interpreted_reason: {explanation.get('summary', '')}")
        if step.get("summary_path"):
            lines.append(f"- summary_path: `{step.get('summary_path')}`")
        if step.get("next_modules"):
            lines.append(f"- next_modules: `{', '.join(step.get('next_modules', []))}`")
        if step.get("error"):
            lines.append(f"- error: `{step.get('error')}`")
        evidence = explanation.get("evidence", [])
        if evidence:
            lines.append("- evidence:")
            for item in evidence:
                lines.append(f"  - {item}")
        lines.append("")
    if result.get("recommended_actions"):
        lines.append("## Recommended Actions")
        lines.append("")
        for action in result["recommended_actions"]:
            lines.append(f"- {action}")
        lines.append("")
    if uploaded:
        lines.append("## Uploaded Inputs")
        lines.append("")
        for key, value in uploaded.items():
            if value is None:
                continue
            lines.append(f"- `{key}`: `{value.get('name')}` / rows={value.get('row_count')}")
        lines.append("")
    return "\n".join(lines)


def get_crm_package_status(uploaded: dict) -> dict:
    activity = uploaded.get("crm_activity") is not None
    rep_master = uploaded.get("crm_rep_master") is not None
    assignment = uploaded.get("crm_account_assignment") is not None
    rules = uploaded.get("crm_rules") is not None
    required_ready = activity and rep_master
    package_count = sum([activity, rep_master, assignment, rules])
    return {
        "activity": activity,
        "rep_master": rep_master,
        "assignment": assignment,
        "rules": rules,
        "required_ready": required_ready,
        "package_count": package_count,
    }


def get_source_target_rows(execution_mode: str, uploaded: dict) -> list[dict]:
    label_map = {
        "crm_activity": "CRM 활동 원본",
        "crm_rep_master": "담당자 / 조직 마스터",
        "crm_account_assignment": "거래처 / 병원 담당 배정",
        "crm_rules": "CRM 규칙 / KPI 설정",
        "sales": "실적(매출) 데이터",
        "target": "목표 데이터",
        "prescription": "Prescription 데이터",
    }
    rows = []
    source_targets = get_source_target_map()
    required_keys = set(get_mode_required_uploads(execution_mode))
    for key, (target_path, _file_format) in source_targets.items():
        info = uploaded.get(key)
        if key not in required_keys and info is None:
            continue
        target_name = Path(target_path).name
        if info and info.get("source_kind") == "existing_company_source":
            apply_mode = "data 폴더 자동 선택"
        elif info:
            apply_mode = "업로드 파일 덮어쓰기"
        else:
            apply_mode = "기존 source 유지"
        rows.append(
            {
                "업로드 슬롯": label_map.get(key, key),
                "슬롯 key": key,
                "실행 필요": "필수" if key in required_keys else "선택",
                "현재 소스": info["name"] if info else "기존 파일 사용",
                "내부 저장 파일명": target_name,
                "실제 반영 경로": target_path,
                "반영 방식": apply_mode,
            }
        )
    return rows


def get_monthly_raw_status() -> dict:
    inspected = inspect_monthly_raw(get_source_target_map())
    return {
        "monthly_root": inspected.monthly_root,
        "months_detected": inspected.months_detected,
        "merged_sources": inspected.merged_sources,
        "has_data": inspected.has_data,
    }


def has_session_intake_inputs(uploaded: dict) -> bool:
    has_direct_upload = any(value is not None for value in uploaded.values())
    has_monthly_upload = bool(st.session_state.get("monthly_upload_summary"))
    return has_direct_upload or has_monthly_upload


def _build_intake_signature(execution_mode: str, uploaded: dict) -> str:
    parts = [get_active_company_key(), execution_mode]
    source_targets = get_source_target_map()
    for key in sorted(uploaded):
        value = uploaded.get(key)
        if value is None:
            target_path = Path(source_targets[key][0])
            if target_path.exists():
                stat = target_path.stat()
                parts.append(f"{key}:file:{target_path.name}:{stat.st_mtime_ns}:{stat.st_size}")
            else:
                parts.append(f"{key}:none")
            continue
        parts.append(
            f"{key}:{value.get('name','')}:{value.get('row_count','')}:{len(value.get('columns', []))}"
        )
    return "|".join(parts)


def run_intake_inspection(execution_mode: str, uploaded: dict) -> dict:
    signature = _build_intake_signature(execution_mode, uploaded)
    context = build_execution_context(
        project_root=get_project_root(),
        company_key=get_active_company_key(),
        company_name=get_active_company_name(),
        source_targets=get_source_target_map(),
    )
    return inspect_intake_inputs(
        context=context,
        execution_mode=execution_mode,
        uploaded=uploaded,
        cache_signature=signature,
    ).to_dict()


def get_cached_intake_result(execution_mode: str, uploaded: dict) -> dict | None:
    if not has_session_intake_inputs(uploaded):
        st.session_state.intake_signature = ""
        st.session_state.intake_result = None
        return None
    signature = _build_intake_signature(execution_mode, uploaded)
    if st.session_state.get("intake_signature", "") != signature:
        return None
    return st.session_state.get("intake_result")


def run_intake_and_cache(execution_mode: str, uploaded: dict) -> dict | None:
    if not has_session_intake_inputs(uploaded):
        st.session_state.intake_signature = ""
        st.session_state.intake_result = None
        return None
    result = run_intake_inspection(execution_mode, uploaded)
    st.session_state.intake_signature = _build_intake_signature(execution_mode, uploaded)
    st.session_state.intake_result = result
    return result


def ensure_intake_result(execution_mode: str, uploaded: dict) -> dict | None:
    if not has_session_intake_inputs(uploaded):
        st.session_state.intake_signature = ""
        st.session_state.intake_result = None
        return None
    signature = _build_intake_signature(execution_mode, uploaded)
    cached_signature = st.session_state.get("intake_signature", "")
    cached_result = st.session_state.get("intake_result")
    if cached_result is not None and cached_signature == signature:
        return cached_result
    result = run_intake_inspection(execution_mode, uploaded)
    st.session_state.intake_signature = signature
    st.session_state.intake_result = result
    return result


def summarize_intake_result(intake_result: dict | None) -> dict:
    if not intake_result:
        return {
            "status": "not_run",
            "ready_for_adapter": False,
            "package_count": 0,
            "blocked_count": 0,
            "review_count": 0,
            "fix_count": 0,
            "timing_alert_count": 0,
            "analysis_month_count": 0,
            "prescription_mapping_risk_score": 0,
            "prescription_mapping_risk_reason": "",
        }
    packages = intake_result.get("packages", [])
    findings = intake_result.get("findings", [])
    suggestions = intake_result.get("suggestions", [])
    risk_score = 0
    risk_reason = ""
    for package in packages:
        if str(package.get("source_key") or "") != "crm_account_assignment":
            continue
        fix_types = {
            str(item.get("fix_type") or "")
            for item in package.get("fixes", [])
        }
        if "derive_account_assignment_from_crm_activity" in fix_types:
            risk_score = 85
            risk_reason = "거래처/병원 배정표를 CRM 활동 기준 임시 생성"
        elif "hydrate_company_assignment_from_account_mapping" in fix_types:
            risk_score = max(risk_score, 55)
            risk_reason = "담당자/조직과 배정표를 조합해 실행용 staging 생성"
    return {
        "status": intake_result.get("status", "unknown"),
        "ready_for_adapter": bool(intake_result.get("ready_for_adapter")),
        "package_count": len(packages),
        "blocked_count": sum(1 for package in packages if package.get("status") == "blocked"),
        "review_count": sum(1 for package in packages if package.get("status") == "needs_review"),
        "advisory_count": sum(
            1
            for finding in findings
            if finding.get("issue_code") == "candidate_review_recommended"
        ),
        "suggestion_count": len(suggestions),
        "fix_count": len(intake_result.get("fixes", [])),
        "timing_alert_count": len(intake_result.get("timing_alerts", [])),
        "analysis_month_count": int(intake_result.get("analysis_month_count") or 0),
        "prescription_mapping_risk_score": risk_score,
        "prescription_mapping_risk_reason": risk_reason,
    }


def save_pipeline_run_history(result: dict, uploaded: dict) -> str:
    root = get_project_root()
    history_dir = Path(root) / "data" / "ops_validation" / get_active_company_key() / "pipeline"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_path = history_dir / "console_run_history.jsonl"
    latest_summary_path = history_dir / "pipeline_validation_summary.json"

    analysis_markdown = _build_execution_analysis_markdown(result, uploaded)
    analysis_latest_path = history_dir / "latest_execution_analysis.md"
    analysis_latest_path.write_text(analysis_markdown, encoding="utf-8")
    run_id = str(result.get("run_id", "")).strip()
    if run_id:
        (history_dir / f"execution_analysis_{run_id}.md").write_text(analysis_markdown, encoding="utf-8")

    supabase_run_db_id = save_pipeline_run_to_supabase(
        company_key=get_active_company_key(),
        company_name=get_active_company_name(),
        result=result,
        uploaded=uploaded,
    )
    if supabase_run_db_id:
        result["supabase_run_db_id"] = supabase_run_db_id
    _write_local_run_bundle(result, uploaded, analysis_markdown)
    latest_summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    record = {
        "saved_at": datetime.now().isoformat(),
        "run_id": result.get("run_id"),
        "supabase_run_db_id": result.get("supabase_run_db_id"),
        "execution_mode": result.get("execution_mode"),
        "execution_mode_label": result.get("execution_mode_label"),
        "company_key": get_active_company_key(),
        "company_name": get_active_company_name(),
        "overall_status": result.get("overall_status"),
        "overall_score": result.get("overall_score"),
        "total_duration_ms": result.get("total_duration_ms"),
        "steps": result.get("steps", []),
        "input_files": {
            key: {
                "uploaded_name": value.get("name"),
                "row_count": value.get("row_count"),
            }
            for key, value in uploaded.items()
            if value is not None
        },
        "source_targets": get_source_target_rows(result.get("execution_mode", "crm_to_sandbox"), uploaded),
    }
    with open(history_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return str(history_path)


def get_mode_pipeline_steps(execution_mode: str) -> list[dict]:
    return [
        {"module": step.module, "label": step.label, "fn": step.runner}
        for step in workflow_get_mode_pipeline_steps(execution_mode)
    ]


def run_actual_pipeline(execution_mode: str, uploaded: dict) -> dict:
    context = build_execution_context(
        project_root=get_project_root(),
        company_key=get_active_company_key(),
        company_name=get_active_company_name(),
        source_targets=get_source_target_map(),
    )
    # Keep the long-lived public entrypoint here so existing console tests
    # and callers can still intercept the runtime execution boundary.
    return run_execution_mode(
        context=context,
        execution_mode=execution_mode,
        uploaded=uploaded,
    ).to_dict()


def run_mock_pipeline(execution_mode: str, uploaded: dict) -> dict:
    steps = []
    modules = ["crm", "prescription", "sandbox", "territory", "radar", "builder"]
    mode_label = get_execution_mode_label(execution_mode)
    crm_status = get_crm_package_status(uploaded)
    active_modules = get_execution_mode_modules(execution_mode)

    for index, module in enumerate(modules):
        time.sleep(0.1)
        status = "PASS"
        note = f"✅ {module} 평가 완료."

        if module not in active_modules:
            status = "SKIP"
            note = f"⏭️ 선택한 흐름에 {module} 단계가 없어 이번 실행에서는 건너뜁니다."
        elif module == "crm":
            if not crm_status["required_ready"]:
                status = "WARN"
                note = "⚠️ CRM 활동 원본 + 담당자 마스터가 모두 있어야 CRM 분석이 안정적으로 시작됩니다."
            elif not crm_status["assignment"] or not crm_status["rules"]:
                note = "✅ CRM 필수 패키지는 준비됨. 배정표/규칙표가 없어서 기본 규칙으로 진행합니다."
        elif module == "prescription":
            if uploaded.get("prescription") is None:
                status = "WARN"
                note = "⚠️ Prescription 흐름을 선택했지만 fact_ship 같은 원천데이터가 없어 분석이 제한됩니다."
        elif module == "sandbox":
            has_core = uploaded.get("sales") is not None or uploaded.get("target") is not None
            if not has_core:
                status = "WARN"
                note = "⚠️ 실적/목표 핵심 입력이 부족해서 샘플 기준의 Sandbox 판단만 가능합니다."
        elif module == "territory":
            if uploaded.get("crm_activity") is None:
                status = "WARN"
                note = "⚠️ Territory는 CRM 활동 데이터가 있어야 이동 흐름을 더 자연스럽게 볼 수 있습니다."
        elif module == "radar":
            note = "✅ Validation 승인 KPI 기반 RADAR 신호 생성 준비 완료."
        elif module == "builder":
            note = "✅ 최종 결과물 생성 준비 완료."

        steps.append(
            {
                "step": index + 1,
                "module": module,
                "status": status,
                "score": round(random.uniform(70, 98), 1) if status != "SKIP" else 0,
                "reasoning_note": note,
                "next_modules": ["territory"] if module == "sandbox" and status == "PASS" else ["builder"] if module == "territory" and status == "PASS" else [],
                "duration_ms": random.randint(20, 150),
            }
        )

    active_scores = [step["score"] for step in steps if step["status"] != "SKIP"]
    overall = "WARN" if any(step["status"] == "WARN" for step in steps) else "PASS"
    return {
        "run_id": str(uuid.uuid4())[:8],
        "execution_mode": execution_mode,
        "execution_mode_label": mode_label,
        "overall_status": overall,
        "overall_score": round(sum(active_scores) / len(active_scores), 1) if active_scores else 0,
        "steps": steps,
        "final_eligible_modules": [module for module in ["territory", "builder"] if module in active_modules],
        "recommended_actions": [
            f"선택 흐름: {' -> '.join(get_execution_mode_modules(execution_mode)).upper()}",
            "현재는 검증 단계라 선택한 흐름만 순차적으로 점검합니다.",
        ],
        "total_duration_ms": sum(step["duration_ms"] for step in steps),
    }
