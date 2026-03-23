from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any

from common.supabase_client import get_supabase_client


_SUPABASE_DISABLE_SECONDS = 300
_supabase_disabled_until = 0.0


def _normalize_validation_status(value: str) -> str:
    cleaned = str(value or "").strip().lower()
    if cleaned == "pass":
        return "PASS"
    if cleaned == "warn":
        return "WARN"
    if cleaned == "fail":
        return "FAIL"
    return cleaned.upper() or "-"


def _normalize_confidence_grade(value: str) -> str:
    cleaned = str(value or "").strip().lower()
    mapping = {
        "verified": "A",
        "assisted": "B",
        "self_only": "C",
    }
    return mapping.get(cleaned, str(value or "-"))


def _iso_or_blank(value: Any) -> str:
    if not value:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).isoformat(timespec="seconds")
    except ValueError:
        return text


def _debug_log_run_registry(event: str, payload: dict[str, Any]) -> None:
    try:
        log_path = Path(r"C:\sfe_master_ops\data\system\run_registry_debug.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "logged_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "event": event,
            **payload,
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _file_hash_or_blank(path: Path) -> str:
    try:
        if not path.exists() or not path.is_file():
            return ""
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def _load_json_from_branch_asset(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    match = re.search(r"=\s*(\{.*\})\s*;?\s*$", text, re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _sum_period(values: Any, start_idx: int, end_idx: int) -> float:
    if not isinstance(values, list):
        return 0.0
    total = 0.0
    for value in values[start_idx:end_idx]:
        try:
            total += float(value or 0)
        except Exception:
            continue
    return total


def _compute_sandbox_member_insights(company_key: str) -> dict[str, Any]:
    builder_dir = _validation_root(company_key) / "builder"
    payload_path = builder_dir / "sandbox_report_preview_payload_standard.json"
    payload_root = _load_json_if_exists(payload_path)
    if not payload_root:
        return {}
    payload = payload_root.get("payload", {})
    manifest = payload.get("branch_asset_manifest", {})
    if not isinstance(manifest, dict):
        return {}

    rows: list[dict[str, Any]] = []
    assets_dir = builder_dir / "sandbox_report_preview_assets"
    for branch_name, asset_name in manifest.items():
        asset_path = assets_dir / str(asset_name)
        branch_data = _load_json_from_branch_asset(asset_path)
        if not branch_data:
            continue
        members = branch_data.get("members", [])
        if not isinstance(members, list):
            continue
        for member in members:
            if not isinstance(member, dict):
                continue
            q1_actual = _sum_period(member.get("monthly_actual"), 0, 3)
            q1_target = _sum_period(member.get("monthly_target"), 0, 3)
            attainment = round((q1_actual / q1_target) * 100, 1) if q1_target > 0 else 0.0
            activity_counts = member.get("activity_counts", {}) if isinstance(member.get("activity_counts"), dict) else {}
            rows.append(
                {
                    "branch": branch_name,
                    "rep_name": str(member.get("성명", "")).strip(),
                    "rep_id": str(member.get("rep_id", "")).strip(),
                    "q1_actual": round(q1_actual),
                    "q1_target": round(q1_target),
                    "q1_attainment": attainment,
                    "gap_amount": round(q1_actual - q1_target),
                    "HIR": float(member.get("HIR", 0) or 0),
                    "RTR": float(member.get("RTR", 0) or 0),
                    "BCR": float(member.get("BCR", 0) or 0),
                    "PHR": float(member.get("PHR", 0) or 0),
                    "PI": float(member.get("PI", 0) or 0),
                    "FGR": float(member.get("FGR", 0) or 0),
                    "activity_counts": activity_counts,
                    "coach_action": str(member.get("coach_action", "")).strip(),
                }
            )

    if not rows:
        return {}

    ranked = sorted(rows, key=lambda item: (item["q1_actual"], item["q1_attainment"]), reverse=True)
    top5 = ranked[:5]
    bottom5 = sorted(rows, key=lambda item: (item["q1_actual"], item["q1_attainment"]))[:5]

    def _avg(items: list[dict[str, Any]], key: str) -> float:
        return round(sum(float(item.get(key, 0) or 0) for item in items) / len(items), 1) if items else 0.0

    metric_gaps = []
    for key in ["HIR", "RTR", "BCR", "PHR", "PI", "FGR"]:
        metric_gaps.append(
            {
                "metric": key,
                "top5_avg": _avg(top5, key),
                "bottom5_avg": _avg(bottom5, key),
                "gap": round(_avg(top5, key) - _avg(bottom5, key), 1),
            }
        )
    metric_gaps.sort(key=lambda item: abs(item["gap"]), reverse=True)

    activity_keys = sorted(
        {
            activity_key
            for item in rows
            for activity_key in item.get("activity_counts", {}).keys()
        }
    )
    activity_gaps = []
    for key in activity_keys:
        top_avg = round(sum(float(item.get("activity_counts", {}).get(key, 0) or 0) for item in top5) / len(top5), 1) if top5 else 0.0
        bottom_avg = round(sum(float(item.get("activity_counts", {}).get(key, 0) or 0) for item in bottom5) / len(bottom5), 1) if bottom5 else 0.0
        activity_gaps.append({"activity": key, "top5_avg": top_avg, "bottom5_avg": bottom_avg, "gap": round(top_avg - bottom_avg, 1)})
    activity_gaps.sort(key=lambda item: abs(item["gap"]), reverse=True)

    return {
        "period": "Q1",
        "top5_members": [
            {
                "rank": index + 1,
                "branch": item["branch"],
                "rep_name": item["rep_name"],
                "q1_actual": item["q1_actual"],
                "q1_target": item["q1_target"],
                "q1_attainment": item["q1_attainment"],
                "gap_amount": item["gap_amount"],
            }
            for index, item in enumerate(top5)
        ],
        "bottom5_members": [
            {
                "rank": index + 1,
                "branch": item["branch"],
                "rep_name": item["rep_name"],
                "q1_actual": item["q1_actual"],
                "q1_target": item["q1_target"],
                "q1_attainment": item["q1_attainment"],
                "gap_amount": item["gap_amount"],
            }
            for index, item in enumerate(bottom5)
        ],
        "comparison_insights": {
            "metric_gaps": metric_gaps[:3],
            "activity_gaps": activity_gaps[:3],
            "top5_avg_actual": round(sum(item["q1_actual"] for item in top5) / len(top5), 0) if top5 else 0,
            "bottom5_avg_actual": round(sum(item["q1_actual"] for item in bottom5) / len(bottom5), 0) if bottom5 else 0,
        },
    }


def _build_agent_summary_for_builder_artifact(report_key: str, file_role: str, file_path: str) -> dict[str, Any]:
    path = Path(file_path)
    if file_role != "payload_standard" or not path.exists() or path.suffix.lower() != ".json":
        return {}

    root = _load_json_if_exists(path)
    if not root:
        return {}
    payload = root.get("payload", {})
    if not isinstance(payload, dict):
        return {}

    if report_key == "crm_analysis":
        overview = payload.get("overview", {})
        activity_context = payload.get("activity_context", {})
        if not isinstance(overview, dict) or not isinstance(activity_context, dict):
            return {}
        return {
            "report_key": report_key,
            "summary_version": "agent_summary_v1",
            "headline": (
                f"CRM 품질 {overview.get('quality_status', '-')} "
                f"/ score {overview.get('quality_score', '-')} "
                f"/ 활동 {overview.get('crm_activity_count', '-')}건"
            ),
            "facts": [
                f"기간 {activity_context.get('date_range_start', '-')} ~ {activity_context.get('date_range_end', '-')}",
                f"담당자 {overview.get('unique_reps', '-')}명 / 병원 {overview.get('unique_hospitals', '-')}곳 / 지점 {overview.get('unique_branches', '-')}개",
                f"매핑률 {overview.get('hospital_mapping_rate', '-')} / unmapped {overview.get('crm_unmapped_count', '-')}",
            ],
        }

    if report_key == "prescription_flow":
        overview = payload.get("overview", {})
        flow_summary = payload.get("flow_summary", {})
        if not isinstance(overview, dict) or not isinstance(flow_summary, dict):
            return {}
        claim_validation = overview.get("claim_validation_summary", {})
        return {
            "report_key": report_key,
            "summary_version": "agent_summary_v1",
            "headline": (
                f"Prescription 품질 {overview.get('quality_status', '-')} "
                f"/ score {overview.get('quality_score', '-')} "
                f"/ 연결병원 {overview.get('connected_hospital_count', '-')}"
            ),
            "facts": [
                f"표준 {overview.get('standard_record_count', '-')}건 / flow completion {overview.get('flow_completion_rate', '-')}",
                f"claim pass {claim_validation.get('pass_count', '-')} / review {claim_validation.get('review_count', '-')} / suspect {claim_validation.get('suspect_count', '-')}" if isinstance(claim_validation, dict) else "claim summary 없음",
                f"tracked {round(float(flow_summary.get('tracked_amount', 0) or 0)):,} / final {round(float(flow_summary.get('pre_kpi_final_amount', 0) or 0)):,}",
            ],
        }

    if report_key == "territory_map":
        overview = payload.get("overview", {})
        if not isinstance(overview, dict):
            return {}
        return {
            "report_key": report_key,
            "summary_version": "agent_summary_v1",
            "headline": (
                f"Territory coverage {overview.get('coverage_rate', '-')} "
                f"/ 담당자 {overview.get('total_reps', '-')}명 "
                f"/ 병원 {overview.get('territory_hospital_count', '-')}"
            ),
            "facts": [
                f"지역 {overview.get('total_regions', '-')}개 / route 선택 {overview.get('route_selection_count', '-')}",
                f"period {overview.get('period_label', '-')}",
            ],
        }

    if report_key == "sandbox_report":
        root_payload = _load_json_if_exists(path)
        payload_obj = root_payload.get("payload", {}) if isinstance(root_payload, dict) else {}
        if not isinstance(payload_obj, dict):
            return {}
        manifest = payload_obj.get("branch_asset_manifest", {})
        return {
            "report_key": report_key,
            "summary_version": "agent_summary_v1",
            "headline": f"Sandbox branch asset {len(manifest) if isinstance(manifest, dict) else 0}개",
            "facts": [
                f"payload keys: {', '.join(list(payload_obj.keys())[:5])}",
            ],
        }

    if report_key == "radar_report":
        overview = payload.get("overview", {})
        signals = payload.get("signals", [])
        decision_options = payload.get("decision_options", [])
        if not isinstance(overview, dict):
            return {}
        top_signal = ""
        if isinstance(signals, list):
            for item in signals:
                if isinstance(item, dict):
                    top_signal = str(item.get("title") or item.get("signal_title") or item.get("issue") or "").strip()
                    if top_signal:
                        break
        return {
            "report_key": report_key,
            "summary_version": "agent_summary_v1",
            "headline": (
                f"RADAR 상태 {overview.get('overall_status', '-')} "
                f"/ signal {overview.get('signal_count', '-')}"
            ),
            "facts": [
                f"top_signal {top_signal or '-'}",
                f"decision_options {len(decision_options) if isinstance(decision_options, list) else 0}개",
                f"period {overview.get('period_value', '-')}",
            ],
        }

    return {}


def _validation_root(company_key: str) -> Path:
    return Path(r"C:\sfe_master_ops\data\ops_validation") / company_key


def _build_report_contexts_from_pipeline_summary(
    company_key: str,
    run_id: str,
    pipeline_summary: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    stages = pipeline_summary.get("stages", {})
    builder_stage = stages.get("builder", {}) if isinstance(stages, dict) else {}
    radar_stage = stages.get("radar", {}) if isinstance(stages, dict) else {}
    territory_stage = stages.get("territory", {}) if isinstance(stages, dict) else {}
    sandbox_stage = stages.get("sandbox", {}) if isinstance(stages, dict) else {}

    linked_artifacts: list[dict[str, str]] = []
    evidence_index: list[dict[str, str]] = []
    if isinstance(builder_stage, dict):
        for key in ["crm_analysis", "sandbox_report", "territory_map", "prescription_flow", "radar_report", "total_valid"]:
            item = builder_stage.get(key)
            if not isinstance(item, dict):
                continue
            html_path = item.get("html")
            if html_path:
                linked_artifacts.append({"type": key, "path": str(html_path)})
                evidence_index.append({"type": key, "path": str(html_path)})

    overall_status = str(pipeline_summary.get("overall_status", "-"))
    overall_score = float(pipeline_summary.get("overall_score", 0) or 0)
    sandbox_member_insights = _compute_sandbox_member_insights(company_key)
    q1_top5 = sandbox_member_insights.get("top5_members", []) if isinstance(sandbox_member_insights, dict) else []
    q1_bottom5 = sandbox_member_insights.get("bottom5_members", []) if isinstance(sandbox_member_insights, dict) else []
    comparison_insights = sandbox_member_insights.get("comparison_insights", {}) if isinstance(sandbox_member_insights, dict) else {}
    executive_summary = (
        f"{company_key} run 요약입니다. 전체 상태는 {overall_status}, "
        f"점수는 {pipeline_summary.get('overall_score', '-')}, "
        f"주요 RADAR 이슈는 {radar_stage.get('top_issue', '없음')} 입니다."
    )
    key_findings = [
        f"Sandbox metric month count: {sandbox_stage.get('metric_month_count', '-')}",
        f"Territory quality status: {territory_stage.get('quality_status', '-')}",
        f"RADAR top issue: {radar_stage.get('top_issue', '-')}",
    ]
    if q1_top5:
        top_names = ", ".join(f"{item['rep_name']}({item['q1_actual']:,}원)" for item in q1_top5[:3])
        key_findings.append(f"Q1 실적 상위 담당자: {top_names}")
    if comparison_insights:
        metric_gap = (comparison_insights.get("metric_gaps") or [{}])[0]
        if metric_gap.get("metric"):
            key_findings.append(
                f"상하위 담당자 차이의 대표 지표는 {metric_gap['metric']}이며 평균 격차는 {metric_gap['gap']}p 입니다."
            )
    full_ctx = {
        "run_id": run_id,
        "company_key": company_key,
        "mode": pipeline_summary.get("execution_mode", ""),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "period": radar_stage.get("period_value", "-"),
        "comparison_period": "-",
        "validation_summary": {"overall_status": overall_status},
        "confidence_grade": "A" if overall_score >= 95 else "B" if overall_score >= 85 else "C",
        "executive_summary": executive_summary,
        "key_findings": key_findings,
        "priority_issues": [radar_stage.get("top_issue", "priority issue 없음")],
        "sales_rankings": {
            "q1_top5_members": q1_top5,
            "q1_bottom5_members": q1_bottom5,
        },
        "comparison_insights": comparison_insights,
        "evidence_index": evidence_index,
        "linked_artifacts": linked_artifacts,
    }
    prompt_ctx = {
        "run_id": run_id,
        "mode": pipeline_summary.get("execution_mode", ""),
        "generated_at": full_ctx["generated_at"],
        "period": full_ctx["period"],
        "comparison_period": "-",
        "executive_summary": executive_summary,
        "top_findings": full_ctx["key_findings"][:3],
        "priority_issues": full_ctx["priority_issues"][:3],
        "sales_rankings": {"q1_top5_members": q1_top5[:5]},
        "comparison_insights": comparison_insights,
        "answer_scope": "final_report_only",
        "forbidden_actions": ["recalculate_kpi", "raw_rejoin"],
    }
    return full_ctx, prompt_ctx


def _resolve_report_contexts(company_key: str, run_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    run_dir = _validation_root(company_key) / "runs" / run_id
    full_ctx = _load_json_if_exists(run_dir / "report_context.full.json")
    prompt_ctx = _load_json_if_exists(run_dir / "report_context.prompt.json")
    if full_ctx and prompt_ctx:
        return full_ctx, prompt_ctx

    pipeline_summary = _load_json_if_exists(_validation_root(company_key) / "pipeline" / "pipeline_validation_summary.json")
    if not pipeline_summary:
        return None, None
    return _build_report_contexts_from_pipeline_summary(company_key, run_id, pipeline_summary)


def _append_artifact_row(
    rows: list[dict[str, Any]],
    *,
    run_db_id: str,
    artifact_type: str,
    artifact_role: str,
    artifact_name: str,
    artifact_class: str,
    storage_path: str,
    mime_type: str,
    payload: dict[str, Any] | None = None,
    quality_status: str | None = None,
    quality_score: float | None = None,
) -> None:
    path_obj = Path(storage_path)
    rows.append(
        {
            "run_id": run_db_id,
            "step_id": None,
            "artifact_type": artifact_type,
            "artifact_role": artifact_role,
            "artifact_name": artifact_name,
            "artifact_class": artifact_class,
            "storage_path": storage_path,
            "mime_type": mime_type,
            "content_hash": _file_hash_or_blank(path_obj),
            "payload": payload or {},
            "quality_status": quality_status,
            "quality_score": quality_score,
        }
    )


def _build_run_artifact_rows(run_db_id: str, result: dict[str, Any], company_key: str, run_key: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for step in result.get("steps", []):
        summary_path = str(step.get("summary_path", "") or "").strip()
        if summary_path:
            status = str(step.get("status", "")).strip().lower() or None
            score_raw = step.get("score")
            score = float(score_raw) if score_raw is not None else None
            _append_artifact_row(
                rows,
                run_db_id=run_db_id,
                artifact_type=f"{step.get('module', 'module')}_validation_summary",
                artifact_role="validation_summary",
                artifact_name=Path(summary_path).name,
                artifact_class="intermediate",
                storage_path=summary_path,
                mime_type="application/json",
                payload={
                    "module": step.get("module"),
                    "reasoning_note": step.get("reasoning_note"),
                },
                quality_status=status if status in {"pass", "warn", "fail"} else None,
                quality_score=score,
            )

    builder_stage = (result.get("summary_by_module") or {}).get("builder", {})
    if isinstance(builder_stage, dict):
        for report_key, artifact_group in builder_stage.items():
            if not isinstance(artifact_group, dict):
                continue
            for file_role, file_path in artifact_group.items():
                if not isinstance(file_path, str) or not file_path.strip():
                    continue
                artifact_type = {
                    "html": "report_html",
                    "input_standard": "report_input_standard",
                    "payload_standard": "report_payload_standard",
                    "result_asset": "report_result_asset",
                }.get(file_role, f"report_{file_role}")
                mime_type = "text/html" if file_role == "html" else "application/json"
                artifact_class = "final" if file_role == "html" else "evidence"
                _append_artifact_row(
                    rows,
                    run_db_id=run_db_id,
                    artifact_type=artifact_type,
                    artifact_role=report_key,
                    artifact_name=Path(file_path).name,
                    artifact_class=artifact_class,
                    storage_path=file_path,
                    mime_type=mime_type,
                    payload={
                        "report_key": report_key,
                        "file_role": file_role,
                        "agent_summary": _build_agent_summary_for_builder_artifact(report_key, file_role, file_path),
                    },
                )

    full_ctx, prompt_ctx = _resolve_report_contexts(company_key, run_key)
    validation_root = _validation_root(company_key)
    run_dir = validation_root / "runs" / run_key
    for file_name, artifact_type in [
        ("report_context.full.json", "report_context_full"),
        ("report_context.prompt.json", "report_context_prompt"),
    ]:
        file_path = run_dir / file_name
        if file_path.exists():
            _append_artifact_row(
                rows,
                run_db_id=run_db_id,
                artifact_type=artifact_type,
                artifact_role="agent_context",
                artifact_name=file_name,
                artifact_class="agent_context",
                storage_path=str(file_path),
                mime_type="application/json",
            )
    if full_ctx:
        _append_artifact_row(
            rows,
            run_db_id=run_db_id,
            artifact_type="report_context_full_virtual",
            artifact_role="agent_context",
            artifact_name=f"{run_key}.full_context",
            artifact_class="agent_context",
            storage_path=str(run_dir / "report_context.full.json"),
            mime_type="application/json",
            payload={"virtual": True, "source": "pipeline_summary_fallback"},
        )
    if prompt_ctx:
        _append_artifact_row(
            rows,
            run_db_id=run_db_id,
            artifact_type="report_context_prompt_virtual",
            artifact_role="agent_context",
            artifact_name=f"{run_key}.prompt_context",
            artifact_class="agent_context",
            storage_path=str(run_dir / "report_context.prompt.json"),
            mime_type="application/json",
            payload={"virtual": True, "source": "pipeline_summary_fallback"},
        )

    return rows


def _save_run_artifacts_to_supabase(
    *,
    client: Any,
    run_db_id: str,
    company_key: str,
    run_key: str,
    result: dict[str, Any],
) -> bool:
    artifact_rows = _build_run_artifact_rows(run_db_id, result, company_key, run_key)
    if not artifact_rows:
        return False
    try:
        try:
            client.table("run_artifacts").delete().eq("run_id", run_db_id).execute()
        except Exception:
            pass
        client.table("run_artifacts").insert(artifact_rows).execute()
        return True
    except Exception as exc:
        _debug_log_run_registry(
            "save_run_artifacts_to_supabase.exception",
            {
                "company_key": company_key,
                "run_key": run_key,
                "run_db_id": run_db_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        return False


def _save_run_report_context_to_supabase(
    *,
    client: Any,
    run_db_id: str,
    company_key: str,
    run_id: str,
    mode: str,
) -> bool:
    full_ctx, prompt_ctx = _resolve_report_contexts(company_key, run_id)
    if not full_ctx or not prompt_ctx:
        return False

    try:
        client.table("run_report_context").upsert(
            {
                "run_id": run_db_id,
                "mode": mode,
                "context_version": "v1",
                "full_context_json": full_ctx,
                "prompt_context_json": prompt_ctx,
                "executive_summary": str(prompt_ctx.get("executive_summary", "")),
                "key_findings": full_ctx.get("key_findings", []),
                "evidence_index": full_ctx.get("evidence_index", []),
            },
            on_conflict="run_id",
        ).execute()
        return True
    except Exception as exc:
        _debug_log_run_registry(
            "save_run_report_context_to_supabase.exception",
            {
                "company_key": company_key,
                "run_id": run_id,
                "run_db_id": run_db_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        return False


def _is_supabase_disabled() -> bool:
    return _supabase_disabled_until > time.monotonic()


def _disable_supabase_temporarily(reason: str, payload: dict[str, Any] | None = None) -> None:
    global _supabase_disabled_until
    _supabase_disabled_until = time.monotonic() + _SUPABASE_DISABLE_SECONDS
    _debug_log_run_registry(
        "supabase.temporarily_disabled",
        {
            "reason": reason,
            "disabled_seconds": _SUPABASE_DISABLE_SECONDS,
            **(payload or {}),
        },
    )


def list_successful_runs_from_supabase(company_key: str, limit: int = 20) -> list[dict[str, Any]]:
    if _is_supabase_disabled():
        return []
    client = get_supabase_client()
    if client is None or not company_key.strip():
        return []

    try:
        response = (
            client.table("runs")
            .select("id, run_key, mode, finished_at, validation_status, confidence_grade")
            .eq("company_key", company_key)
            .eq("run_status", "success")
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        _disable_supabase_temporarily(
            "list_successful_runs_failed",
            {
                "company_key": company_key,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        return []

    rows = getattr(response, "data", None) or []
    collected: list[dict[str, Any]] = []
    for row in rows:
        collected.append(
            {
                "run_id": str(row.get("run_key") or row.get("id") or ""),
                "run_db_id": str(row.get("id") or ""),
                "mode": str(row.get("mode", "")).strip(),
                "finished_at": _iso_or_blank(row.get("finished_at")),
                "validation_status": _normalize_validation_status(str(row.get("validation_status", ""))),
                "confidence_grade": _normalize_confidence_grade(str(row.get("confidence_grade", ""))),
                "storage_type": "supabase",
            }
        )
    return collected


def list_run_artifacts_from_supabase(run_db_id: str, limit: int = 50) -> list[dict[str, Any]]:
    if _is_supabase_disabled():
        return []
    client = get_supabase_client()
    if client is None or not str(run_db_id).strip():
        return []

    try:
        response = (
            client.table("run_artifacts")
            .select("artifact_type, artifact_role, artifact_name, artifact_class, storage_path, mime_type, payload, quality_status, quality_score, created_at")
            .eq("run_id", run_db_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        _disable_supabase_temporarily(
            "list_run_artifacts_failed",
            {
                "run_db_id": run_db_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        return []

    rows = getattr(response, "data", None) or []
    return [
        {
            "artifact_type": str(row.get("artifact_type", "")).strip(),
            "artifact_role": str(row.get("artifact_role", "")).strip(),
            "artifact_name": str(row.get("artifact_name", "")).strip(),
            "artifact_class": str(row.get("artifact_class", "")).strip(),
            "storage_path": str(row.get("storage_path", "")).strip(),
            "mime_type": str(row.get("mime_type", "")).strip(),
            "payload": row.get("payload") if isinstance(row.get("payload"), dict) else {},
            "quality_status": str(row.get("quality_status", "")).strip(),
            "quality_score": row.get("quality_score"),
        }
        for row in rows
    ]


def load_run_contexts_from_supabase(run_db_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if _is_supabase_disabled():
        return None, None
    client = get_supabase_client()
    if client is None or not str(run_db_id).strip():
        return None, None

    try:
        response = (
            client.table("run_report_context")
            .select("full_context_json, prompt_context_json")
            .eq("run_id", run_db_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        _disable_supabase_temporarily(
            "load_run_contexts_failed",
            {
                "run_db_id": run_db_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        return None, None

    rows = getattr(response, "data", None) or []
    if not rows:
        return None, None
    row = rows[0]
    full_ctx = row.get("full_context_json") if isinstance(row.get("full_context_json"), dict) else None
    prompt_ctx = row.get("prompt_context_json") if isinstance(row.get("prompt_context_json"), dict) else None
    return full_ctx, prompt_ctx


def list_agent_chat_logs_from_supabase(run_db_id: str, limit: int = 20) -> list[dict[str, Any]]:
    if _is_supabase_disabled():
        return []
    client = get_supabase_client()
    if client is None or not str(run_db_id).strip():
        return []

    try:
        response = (
            client.table("agent_chat_logs")
            .select("created_at, mode, user_question, assistant_answer, answer_scope, model_name")
            .eq("run_id", run_db_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        _disable_supabase_temporarily(
            "list_agent_chat_logs_failed",
            {
                "run_db_id": run_db_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        return []

    rows = getattr(response, "data", None) or []
    return [
        {
            "created_at": str(row.get("created_at", "")).strip(),
            "mode": str(row.get("mode", "")).strip(),
            "question": str(row.get("user_question", "")).strip(),
            "answer": str(row.get("assistant_answer", "")).strip(),
            "answer_scope": str(row.get("answer_scope", "")).strip(),
            "model": str(row.get("model_name", "")).strip(),
            "provider": "supabase",
            "evidence_refs": [],
        }
        for row in rows
    ]


def append_agent_chat_log_to_supabase(
    run_db_id: str,
    *,
    mode: str,
    user_question: str,
    assistant_answer: str,
    answer_scope: str,
    model_name: str,
    used_context_version: str = "v1",
    question_type: str = "general",
) -> bool:
    if _is_supabase_disabled():
        return False
    client = get_supabase_client()
    if client is None or not str(run_db_id).strip():
        return False

    try:
        (
            client.table("agent_chat_logs")
            .insert(
                {
                    "run_id": run_db_id,
                    "mode": mode,
                    "user_question": user_question,
                    "assistant_answer": assistant_answer,
                    "used_context_version": used_context_version,
                    "answer_scope": answer_scope,
                    "question_type": question_type,
                    "model_name": model_name,
                }
            )
            .execute()
        )
        return True
    except Exception as exc:
        _disable_supabase_temporarily(
            "append_agent_chat_log_failed",
            {
                "run_db_id": run_db_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        return False


def save_pipeline_run_to_supabase(
    *,
    company_key: str,
    company_name: str,
    result: dict[str, Any],
    uploaded: dict[str, Any],
) -> str:
    if _is_supabase_disabled():
        return ""
    client = get_supabase_client()
    if client is None:
        _debug_log_run_registry("save_pipeline_run_to_supabase.no_client", {"company_key": company_key})
        return ""

    run_key = str(result.get("run_id") or "").strip()
    if not run_key:
        _debug_log_run_registry("save_pipeline_run_to_supabase.no_run_key", {"company_key": company_key})
        return ""

    overall_status = str(result.get("overall_status", "")).strip().upper()
    validation_status = {"PASS": "pass", "WARN": "warn", "FAIL": "fail"}.get(overall_status)
    overall_score = float(result.get("overall_score", 0) or 0)
    confidence_grade = "verified" if overall_score >= 95 else "assisted" if overall_score >= 85 else "self_only"
    input_summary = {
        "company_name": company_name,
        "input_files": {
            key: {
                "uploaded_name": value.get("name"),
                "row_count": value.get("row_count"),
            }
            for key, value in uploaded.items()
            if value is not None
        },
    }

    run_payload = {
        "run_key": run_key,
        "company_key": company_key,
        "mode": str(result.get("execution_mode", "")).strip(),
        "run_status": "success",
        "triggered_by": "streamlit_ui",
        "input_summary": input_summary,
        "validation_status": validation_status,
        "confidence_grade": confidence_grade,
        "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }

    try:
        run_response = client.table("runs").upsert(run_payload, on_conflict="run_key").execute()
        run_rows = getattr(run_response, "data", None) or []
        if not run_rows:
            _debug_log_run_registry(
                "save_pipeline_run_to_supabase.empty_run_rows",
                {"company_key": company_key, "run_key": run_key, "run_payload": run_payload},
            )
            return ""
        run_id = str(run_rows[0].get("id") or "").strip()
        if not run_id:
            _debug_log_run_registry(
                "save_pipeline_run_to_supabase.missing_run_id",
                {"company_key": company_key, "run_key": run_key, "run_rows": run_rows},
            )
            return ""

        try:
            client.table("run_steps").delete().eq("run_id", run_id).execute()
        except Exception:
            pass

        step_rows = []
        for step in result.get("steps", []):
            step_status = str(step.get("status", "")).strip().upper()
            step_rows.append(
                {
                    "run_id": run_id,
                    "step_name": str(step.get("module", "")).strip(),
                    "step_order": int(step.get("step", 0) or 0),
                    "step_status": {
                        "PASS": "success",
                        "WARN": "partial",
                        "FAIL": "failed",
                        "SKIP": "skipped",
                    }.get(step_status, "success"),
                    "quality_status": {
                        "PASS": "pass",
                        "WARN": "warn",
                        "FAIL": "fail",
                    }.get(step_status),
                    "output_summary": {
                        "score": step.get("score"),
                        "reasoning_note": step.get("reasoning_note"),
                        "next_modules": step.get("next_modules", []),
                        "duration_ms": step.get("duration_ms"),
                    },
                    "started_at": None,
                    "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                }
            )
        if step_rows:
            client.table("run_steps").insert(step_rows).execute()
        _save_run_artifacts_to_supabase(
            client=client,
            run_db_id=run_id,
            company_key=company_key,
            run_key=run_key,
            result=result,
        )
        _save_run_report_context_to_supabase(
            client=client,
            run_db_id=run_id,
            company_key=company_key,
            run_id=run_key,
            mode=str(result.get("execution_mode", "")).strip(),
        )
        return run_id
    except Exception as exc:
        _disable_supabase_temporarily(
            "save_pipeline_run_failed",
            {
                "company_key": company_key,
                "run_key": run_key,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        _debug_log_run_registry(
            "save_pipeline_run_to_supabase.exception",
            {
                "company_key": company_key,
                "run_key": run_key,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "run_payload": run_payload,
            },
        )
        return ""
