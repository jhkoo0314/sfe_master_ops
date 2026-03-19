from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from common.run_storage import (
    append_agent_chat_log_to_supabase,
    list_agent_chat_logs_from_supabase,
)
from ui.console.paths import get_project_root


def _agent_runs_root(company_key: str) -> Path:
    return Path(get_project_root()) / "data" / "ops_validation" / company_key / "runs"


def _agent_history_path(company_key: str, run_id: str) -> Path:
    return _agent_runs_root(company_key) / run_id / "chat" / "agent_chat_history.jsonl"


def _read_agent_history(company_key: str, run_id: str, limit: int = 20, run_db_id: str = "") -> list[dict[str, Any]]:
    if run_db_id:
        supabase_rows = list_agent_chat_logs_from_supabase(run_db_id, limit=limit)
        if supabase_rows:
            return supabase_rows

    history_path = _agent_history_path(company_key, run_id)
    if not history_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with history_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return rows[-limit:][::-1]


def _append_agent_history(company_key: str, run_id: str, record: dict[str, Any], run_db_id: str = "") -> None:
    if run_db_id:
        append_agent_chat_log_to_supabase(
            run_db_id,
            mode=str(record.get("mode", "")),
            user_question=str(record.get("question", "")),
            assistant_answer=str(record.get("answer", "")),
            answer_scope=str(record.get("answer_scope", "final_report_only")),
            model_name=str(record.get("model", "")),
        )

    history_path = _agent_history_path(company_key, run_id)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


__all__ = ["_read_agent_history", "_append_agent_history"]
