import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.validate_full_pipeline as validate_full_pipeline
from ops_core.workflow.execution_models import ExecutionContext, ExecutionRunResult, ExecutionStepResult


def _make_temp_dir() -> Path:
    temp_dir = ROOT / "tests" / "_tmp_priority1" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_validate_full_pipeline_uses_shared_execution_service(monkeypatch):
    tmp_path = _make_temp_dir()
    try:
        captured: dict = {}
        fake_context = ExecutionContext(
            project_root=str(tmp_path),
            company_key="demo_company",
            company_name="Demo Company",
            source_targets={},
        )
        fake_result = ExecutionRunResult(
            run_id="run-1",
            execution_mode="integrated_full",
            execution_mode_label="통합 실행",
            company_key="demo_company",
            company_name="Demo Company",
            overall_status="PASS",
            overall_score=94.5,
            total_duration_ms=456,
            steps=[
                ExecutionStepResult(
                    step=1,
                    module="crm",
                    status="PASS",
                    score=94.5,
                    summary={"quality_status": "pass", "quality_score": 94.5},
                ),
                ExecutionStepResult(
                    step=2,
                    module="builder",
                    status="PASS",
                    score=100.0,
                    summary={"total_valid": {"path": "total_valid_preview.html"}},
                ),
            ],
            summary_by_module={
                "crm": {"quality_status": "pass", "quality_score": 94.5},
                "builder": {"total_valid": {"path": "total_valid_preview.html"}},
            },
        )

        monkeypatch.setattr(validate_full_pipeline, "get_active_company_key", lambda: "demo_company")
        monkeypatch.setattr(validate_full_pipeline, "get_active_company_name", lambda company_key: "Demo Company")
        monkeypatch.setattr(
            validate_full_pipeline,
            "get_company_ops_profile",
            lambda company_key: SimpleNamespace(raw_generator_module=None),
        )
        monkeypatch.setattr(
            validate_full_pipeline,
            "get_company_root",
            lambda root, bucket, company_key: tmp_path / "data" / bucket / company_key,
        )
        monkeypatch.setattr(validate_full_pipeline, "get_execution_mode_modules", lambda mode: ["crm", "builder"])

        def fake_build_execution_context(**kwargs):
            captured["context_kwargs"] = kwargs
            return fake_context

        def fake_run_execution_mode(**kwargs):
            captured["run_kwargs"] = kwargs
            return fake_result

        monkeypatch.setattr(validate_full_pipeline, "build_execution_context", fake_build_execution_context)
        monkeypatch.setattr(validate_full_pipeline, "run_execution_mode", fake_run_execution_mode)

        validate_full_pipeline.main()

        summary_path = tmp_path / "data" / "ops_validation" / "demo_company" / "pipeline" / "pipeline_validation_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))

        assert captured["context_kwargs"]["company_key"] == "demo_company"
        assert captured["run_kwargs"]["execution_mode"] == "integrated_full"
        assert summary["overall_status"] == "PASS"
        assert summary["stages"]["crm"]["quality_status"] == "pass"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)
