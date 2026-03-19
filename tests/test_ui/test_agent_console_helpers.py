from pathlib import Path
import json
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ui.console.agent.context as agent_context
import ui.console.agent.history as agent_history
import ui.console.agent.runs as agent_runs


def _make_sandbox(name: str) -> Path:
    sandbox = ROOT / "tests" / ".tmp_agent_console" / f"{name}_{uuid.uuid4().hex}"
    sandbox.mkdir(parents=True, exist_ok=True)
    return sandbox


def test_resolve_company_key_for_agent_normalizes_known_inputs(monkeypatch):
    sandbox = _make_sandbox("resolve")
    try:
        ops_root = sandbox / "data" / "ops_validation"
        (ops_root / "daon_pharma").mkdir(parents=True)
        (ops_root / "hangyeol_pharma").mkdir(parents=True)
        monkeypatch.setattr(agent_runs, "get_project_root", lambda: str(sandbox))

        assert agent_runs._resolve_company_key_for_agent("daon-pharma") == "daon_pharma"
        assert agent_runs._resolve_company_key_for_agent("DAON PHARMA") == "daon_pharma"
        assert agent_runs._resolve_company_key_for_agent("다온파마") == "daon_pharma"
        assert agent_runs._resolve_company_key_for_agent("한결제약") == "hangyeol_pharma"
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_scan_successful_runs_falls_back_to_legacy_summary(monkeypatch):
    sandbox = _make_sandbox("scan")
    try:
        summary_path = sandbox / "data" / "ops_validation" / "daon_pharma" / "pipeline" / "pipeline_validation_summary.json"
        summary_path.parent.mkdir(parents=True)
        summary_path.write_text(
            json.dumps(
                {
                    "execution_mode": "integrated_full",
                    "overall_status": "WARN",
                    "overall_score": 97.9,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(agent_runs, "get_project_root", lambda: str(sandbox))

        runs = agent_runs._scan_successful_runs("daon_pharma")

        assert len(runs) == 1
        assert runs[0]["run_id"] == "legacy-latest"
        assert runs[0]["mode"] == "integrated_full"
        assert runs[0]["validation_status"] == "WARN"
        assert runs[0]["confidence_grade"] == "A"
        assert runs[0]["storage_type"] == "legacy"
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_load_run_contexts_builds_legacy_context(monkeypatch):
    sandbox = _make_sandbox("context")
    try:
        summary_path = sandbox / "data" / "ops_validation" / "hangyeol_pharma" / "pipeline" / "pipeline_validation_summary.json"
        summary_path.parent.mkdir(parents=True)
        summary_path.write_text(
            json.dumps(
                {
                    "execution_mode": "integrated_full",
                    "overall_status": "PASS",
                    "overall_score": 96.7,
                    "stages": {
                        "builder": {
                            "crm_analysis": {"html": "C:/tmp/crm_analysis_preview.html"},
                            "sandbox_report": {"html": "C:/tmp/sandbox_report_preview.html"},
                        },
                        "sandbox": {"metric_month_count": 6},
                        "territory": {"quality_status": "pass"},
                        "radar": {"top_issue": None, "period_value": "202606"},
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(agent_context, "get_project_root", lambda: str(sandbox))

        full_ctx, prompt_ctx = agent_context._load_run_contexts("hangyeol_pharma", "legacy-latest")

        assert full_ctx is not None
        assert prompt_ctx is not None
        assert full_ctx["mode"] == "integrated_full"
        assert full_ctx["confidence_grade"] == "A"
        assert len(full_ctx["evidence_index"]) == 2
        assert prompt_ctx["top_findings"][0] == "Sandbox metric month count: 6"
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_read_agent_history_ignores_bad_json(monkeypatch):
    sandbox = _make_sandbox("history")
    try:
        monkeypatch.setattr(agent_history, "get_project_root", lambda: str(sandbox))
        history_path = sandbox / "data" / "ops_validation" / "daon_pharma" / "runs" / "run-1" / "chat" / "agent_chat_history.jsonl"
        history_path.parent.mkdir(parents=True)
        history_path.write_text(
            "\n".join(
                [
                    json.dumps({"question": "q1", "answer": "a1"}, ensure_ascii=False),
                    "{bad json",
                    json.dumps({"question": "q2", "answer": "a2"}, ensure_ascii=False),
                ]
            ),
            encoding="utf-8",
        )

        rows = agent_history._read_agent_history("daon_pharma", "run-1")

        assert len(rows) == 2
        assert rows[0]["question"] == "q2"
        assert rows[1]["question"] == "q1"
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
