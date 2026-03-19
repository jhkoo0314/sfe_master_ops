import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common import run_registry


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, table_name, client):
        self.table_name = table_name
        self.client = client
        self.payload = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def insert(self, payload):
        self.payload = payload
        self.client.insert_calls.append((self.table_name, payload))
        return self

    def upsert(self, payload, **_kwargs):
        self.payload = payload
        self.client.upsert_calls.append((self.table_name, payload))
        return self

    def delete(self):
        self.client.delete_calls.append(self.table_name)
        return self

    def execute(self):
        if self.table_name == "runs" and self.client.run_rows is not None and self.payload is None:
            return FakeResponse(self.client.run_rows)
        if self.table_name == "run_report_context" and self.payload is None:
            return FakeResponse(self.client.context_rows)
        if self.table_name == "agent_chat_logs":
            return FakeResponse(self.client.chat_rows)
        if self.table_name == "runs" and self.payload is not None:
            return FakeResponse([{"id": "db-run-1"}])
        if self.table_name == "run_report_context" and self.payload is not None:
            return FakeResponse([{"id": "ctx-1"}])
        return FakeResponse([])


class FakeSupabaseClient:
    def __init__(self, run_rows=None, context_rows=None, chat_rows=None):
        self.run_rows = run_rows or []
        self.context_rows = context_rows or []
        self.chat_rows = chat_rows or []
        self.insert_calls = []
        self.upsert_calls = []
        self.delete_calls = []

    def table(self, table_name):
        return FakeQuery(table_name, self)


def test_list_successful_runs_from_supabase_maps_fields(monkeypatch):
    fake_client = FakeSupabaseClient(
        run_rows=[
            {
                "id": "db-run-1",
                "run_key": "run_20260319_test",
                "mode": "integrated_full",
                "finished_at": "2026-03-19T17:00:00+09:00",
                "validation_status": "warn",
                "confidence_grade": "verified",
            }
        ]
    )
    monkeypatch.setattr(run_registry, "get_supabase_client", lambda: fake_client)

    runs = run_registry.list_successful_runs_from_supabase("daon_pharma")

    assert len(runs) == 1
    assert runs[0]["run_id"] == "run_20260319_test"
    assert runs[0]["run_db_id"] == "db-run-1"
    assert runs[0]["validation_status"] == "WARN"
    assert runs[0]["confidence_grade"] == "A"
    assert runs[0]["storage_type"] == "supabase"


def test_save_pipeline_run_to_supabase_writes_run_and_steps(monkeypatch):
    fake_client = FakeSupabaseClient()
    monkeypatch.setattr(run_registry, "get_supabase_client", lambda: fake_client)
    monkeypatch.setattr(
        run_registry,
        "_resolve_report_contexts",
        lambda company_key, run_id: (
            {"key_findings": ["finding"], "evidence_index": [{"type": "html", "path": "a.html"}]},
            {"executive_summary": "summary"},
        ),
    )

    run_db_id = run_registry.save_pipeline_run_to_supabase(
        company_key="daon_pharma",
        company_name="다온파마",
        result={
            "run_id": "run_20260319_test",
            "execution_mode": "integrated_full",
            "overall_status": "WARN",
            "overall_score": 92.4,
            "steps": [
                {"step": 1, "module": "crm", "status": "PASS", "score": 98, "reasoning_note": "ok", "duration_ms": 12},
                {"step": 2, "module": "sandbox", "status": "WARN", "score": 86, "reasoning_note": "warn", "duration_ms": 22},
            ],
        },
        uploaded={"sales": {"name": "sales.xlsx", "row_count": 120}},
    )

    assert run_db_id == "db-run-1"
    assert fake_client.upsert_calls
    assert fake_client.upsert_calls[0][0] == "runs"
    assert fake_client.upsert_calls[1][0] == "run_report_context"
    assert fake_client.insert_calls[-1][0] == "run_steps"
    assert len(fake_client.insert_calls[-1][1]) == 2


def test_save_pipeline_run_to_supabase_accepts_empty_uploaded(monkeypatch):
    fake_client = FakeSupabaseClient()
    monkeypatch.setattr(run_registry, "get_supabase_client", lambda: fake_client)
    monkeypatch.setattr(
        run_registry,
        "_resolve_report_contexts",
        lambda company_key, run_id: (
            {"key_findings": [], "evidence_index": []},
            {"executive_summary": "summary"},
        ),
    )

    run_db_id = run_registry.save_pipeline_run_to_supabase(
        company_key="hangyeol_pharma",
        company_name="한결제약",
        result={
            "run_id": "run_20260319_cli",
            "execution_mode": "integrated_full",
            "overall_status": "PASS",
            "overall_score": 96.7,
            "steps": [
                {"step": 1, "module": "crm", "status": "PASS", "score": 98, "reasoning_note": "ok", "duration_ms": 12},
            ],
        },
        uploaded={},
    )

    assert run_db_id == "db-run-1"
    assert fake_client.upsert_calls[0][0] == "runs"
    assert fake_client.upsert_calls[0][1]["input_summary"]["input_files"] == {}


def test_resolve_report_contexts_from_pipeline_summary(monkeypatch):
    company_key = "hangyeol_pharma"
    tmp_path = ROOT / "tests" / "_tmp_run_registry"
    if tmp_path.exists():
        shutil.rmtree(tmp_path)
    validation_root = tmp_path / "data" / "ops_validation" / company_key / "pipeline"
    validation_root.mkdir(parents=True, exist_ok=True)
    (validation_root / "pipeline_validation_summary.json").write_text(
        """
        {
          "execution_mode": "integrated_full",
          "overall_status": "PASS",
          "overall_score": 96.7,
          "stages": {
            "builder": {
              "sandbox_report": {"html": "builder/sandbox_report_preview.html"}
            },
            "radar": {"top_issue": "RTR issue", "period_value": "2026-01"},
            "territory": {"quality_status": "pass"},
            "sandbox": {"metric_month_count": 6}
          }
        }
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(run_registry, "_validation_root", lambda key: tmp_path / "data" / "ops_validation" / key)

    full_ctx, prompt_ctx = run_registry._resolve_report_contexts(company_key, "run_1")

    assert full_ctx is not None
    assert prompt_ctx is not None
    assert full_ctx["mode"] == "integrated_full"
    assert full_ctx["evidence_index"][0]["path"] == "builder/sandbox_report_preview.html"
    assert prompt_ctx["executive_summary"]
    shutil.rmtree(tmp_path)
