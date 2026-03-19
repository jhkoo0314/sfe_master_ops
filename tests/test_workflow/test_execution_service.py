import json
from pathlib import Path
import shutil
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ops_core.workflow.execution_service as execution_service
import ui.console.runner as console_runner
from ops_core.workflow.execution_models import (
    ExecutionContext,
    ExecutionRunResult,
    ExecutionStepDefinition,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _make_temp_dir() -> Path:
    temp_dir = ROOT / "tests" / "_tmp_priority1" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_run_execution_mode_reads_shared_summaries(monkeypatch):
    tmp_path = _make_temp_dir()
    try:
        company_key = "demo_company"
        raw_path = tmp_path / "data" / "company_source" / company_key / "crm" / "crm_activity_raw.xlsx"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(b"existing")

        crm_summary = {
            "quality_status": "pass",
            "quality_score": 92.5,
            "next_modules": ["builder"],
        }
        builder_summary = {
            "crm_analysis": {"path": "crm_analysis_preview.html"},
            "total_valid": {"path": "total_valid_preview.html"},
        }
        _write_json(
            tmp_path / "data" / "ops_validation" / company_key / "crm" / "crm_validation_summary.json",
            crm_summary,
        )
        _write_json(
            tmp_path / "data" / "ops_validation" / company_key / "builder" / "builder_validation_summary.json",
            builder_summary,
        )

        steps = [
            ExecutionStepDefinition(module="crm", label="CRM 정규화 및 검증", runner=lambda: None),
            ExecutionStepDefinition(module="builder", label="Builder HTML 생성", runner=lambda: None),
        ]
        monkeypatch.setattr(execution_service, "get_mode_required_uploads", lambda mode: ["crm_activity"])
        monkeypatch.setattr(execution_service, "get_mode_pipeline_steps", lambda mode: steps)
        monkeypatch.setattr(execution_service, "get_execution_mode_label", lambda mode: "통합 실행")

        context = ExecutionContext(
            project_root=str(tmp_path),
            company_key=company_key,
            company_name="Demo Company",
            source_targets={"crm_activity": (str(raw_path), "excel")},
        )
        result = execution_service.run_execution_mode(
            context=context,
            execution_mode="integrated_full",
        )

        assert result.overall_status == "PASS"
        assert result.final_eligible_modules == ["builder"]
        assert result.summary_by_module["crm"]["quality_score"] == 92.5
        assert result.steps[1].summary == builder_summary
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_console_runner_run_actual_pipeline_delegates_to_execution_service(monkeypatch):
    captured: dict = {}
    fake_context = ExecutionContext(
        project_root=str(ROOT),
        company_key="demo_company",
        company_name="Demo Company",
        source_targets={},
    )
    fake_result = ExecutionRunResult(
        run_id="run-1",
        execution_mode="crm_to_sandbox",
        execution_mode_label="CRM -> Sandbox",
        company_key="demo_company",
        company_name="Demo Company",
        overall_status="PASS",
        overall_score=99.0,
        total_duration_ms=123,
    )

    monkeypatch.setattr(console_runner, "get_project_root", lambda: str(ROOT))
    monkeypatch.setattr(console_runner, "get_active_company_key", lambda: "demo_company")
    monkeypatch.setattr(console_runner, "get_active_company_name", lambda: "Demo Company")
    monkeypatch.setattr(
        console_runner,
        "get_source_target_map",
        lambda: {"crm_activity": (str(ROOT / "data" / "company_source" / "demo_company" / "crm" / "crm_activity_raw.xlsx"), "excel")},
    )

    def fake_build_execution_context(**kwargs):
        captured["context_kwargs"] = kwargs
        return fake_context

    def fake_run_execution_mode(**kwargs):
        captured["run_kwargs"] = kwargs
        return fake_result

    monkeypatch.setattr(console_runner, "build_execution_context", fake_build_execution_context)
    monkeypatch.setattr(console_runner, "run_execution_mode", fake_run_execution_mode)

    result = console_runner.run_actual_pipeline("crm_to_sandbox", {"crm_activity": None})

    assert captured["context_kwargs"]["company_key"] == "demo_company"
    assert captured["run_kwargs"]["execution_mode"] == "crm_to_sandbox"
    assert result["run_id"] == "run-1"
