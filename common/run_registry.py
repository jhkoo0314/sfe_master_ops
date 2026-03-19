from common.run_storage import _shared

_ORIGINAL_RESOLVE_REPORT_CONTEXTS = _shared._resolve_report_contexts
_supabase_disabled_until = 0.0
get_supabase_client = _shared.get_supabase_client
_validation_root = _shared._validation_root


def _sync_to_shared() -> None:
    _shared._supabase_disabled_until = _supabase_disabled_until
    _shared.get_supabase_client = get_supabase_client
    _shared._validation_root = _validation_root


def _sync_from_shared() -> None:
    global _supabase_disabled_until
    _supabase_disabled_until = _shared._supabase_disabled_until


def _resolve_report_contexts(company_key: str, run_id: str):
    _sync_to_shared()
    result = _ORIGINAL_RESOLVE_REPORT_CONTEXTS(company_key, run_id)
    _sync_from_shared()
    return result


def list_successful_runs_from_supabase(company_key: str, limit: int = 20) -> list[dict]:
    _sync_to_shared()
    result = _shared.list_successful_runs_from_supabase(company_key, limit=limit)
    _sync_from_shared()
    return result


def list_run_artifacts_from_supabase(run_db_id: str, limit: int = 50) -> list[dict]:
    _sync_to_shared()
    result = _shared.list_run_artifacts_from_supabase(run_db_id, limit=limit)
    _sync_from_shared()
    return result


def load_run_contexts_from_supabase(run_db_id: str):
    _sync_to_shared()
    result = _shared.load_run_contexts_from_supabase(run_db_id)
    _sync_from_shared()
    return result


def list_agent_chat_logs_from_supabase(run_db_id: str, limit: int = 20) -> list[dict]:
    _sync_to_shared()
    result = _shared.list_agent_chat_logs_from_supabase(run_db_id, limit=limit)
    _sync_from_shared()
    return result


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
    _sync_to_shared()
    result = _shared.append_agent_chat_log_to_supabase(
        run_db_id,
        mode=mode,
        user_question=user_question,
        assistant_answer=assistant_answer,
        answer_scope=answer_scope,
        model_name=model_name,
        used_context_version=used_context_version,
        question_type=question_type,
    )
    _sync_from_shared()
    return result


def save_pipeline_run_to_supabase(*, company_key: str, company_name: str, result: dict, uploaded: dict) -> str:
    _sync_to_shared()
    previous_resolver = _shared._resolve_report_contexts
    _shared._resolve_report_contexts = _resolve_report_contexts
    try:
        run_id = _shared.save_pipeline_run_to_supabase(
            company_key=company_key,
            company_name=company_name,
            result=result,
            uploaded=uploaded,
        )
    finally:
        _shared._resolve_report_contexts = previous_resolver
        _sync_from_shared()
    return run_id


__all__ = [
    "_resolve_report_contexts",
    "_supabase_disabled_until",
    "_validation_root",
    "append_agent_chat_log_to_supabase",
    "get_supabase_client",
    "list_agent_chat_logs_from_supabase",
    "list_run_artifacts_from_supabase",
    "list_successful_runs_from_supabase",
    "load_run_contexts_from_supabase",
    "save_pipeline_run_to_supabase",
]
