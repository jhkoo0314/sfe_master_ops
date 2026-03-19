from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
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
