from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.raw_generators.configs import get_raw_generation_config
from scripts.raw_generators.engine import run_raw_generation


def test_run_raw_generation_dispatches_template(monkeypatch):
    config = get_raw_generation_config("daon_pharma")
    assert config is not None

    called: dict[str, str] = {}

    class FakeTemplateModule:
        @staticmethod
        def run_template(received_config):
            called["company_key"] = received_config.company_key

    monkeypatch.setattr(
        "scripts.raw_generators.engine.import_module",
        lambda module_path: FakeTemplateModule,
    )

    run_raw_generation(config)

    assert called["company_key"] == "daon_pharma"


def test_run_raw_generation_uses_monthly_template_entry_when_needed(monkeypatch):
    config = get_raw_generation_config("monthly_merge_pharma")
    assert config is not None

    called: dict[str, str] = {}

    class FakeTemplateModule:
        @staticmethod
        def run_template(received_config):
            called["entry"] = f"default:{received_config.company_key}"

        @staticmethod
        def run_monthly_and_merged_template(received_config):
            called["entry"] = f"monthly:{received_config.company_key}"

    monkeypatch.setattr(
        "scripts.raw_generators.engine.import_module",
        lambda module_path: FakeTemplateModule,
    )

    run_raw_generation(config)

    assert called["entry"] == "monthly:monthly_merge_pharma"


def test_run_raw_generation_dispatches_hangyeol_template(monkeypatch):
    config = get_raw_generation_config("hangyeol_pharma")
    assert config is not None

    called: dict[str, str] = {}

    class FakeTemplateModule:
        @staticmethod
        def run_template(received_config):
            called["company_key"] = received_config.company_key

    monkeypatch.setattr(
        "scripts.raw_generators.engine.import_module",
        lambda module_path: FakeTemplateModule,
    )

    run_raw_generation(config)

    assert called["company_key"] == "hangyeol_pharma"


def test_run_raw_generation_rejects_unknown_template():
    from scripts.raw_generators.configs import RawGenerationConfig

    config = RawGenerationConfig(
        company_key="demo",
        company_name="데모제약",
        template_type="unknown_template",
        start_month="2025-01",
        end_month="2025-01",
        branch_count=1,
        clinic_rep_count=1,
        hospital_rep_count=1,
        portfolio_source="hangyeol_portfolio",
        output_mode="merged_only",
    )

    try:
        run_raw_generation(config)
    except ValueError as exc:
        assert "아직 지원되지 않습니다" in str(exc)
    else:
        raise AssertionError("Unknown template should raise ValueError.")
