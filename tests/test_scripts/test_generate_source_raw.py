from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.generate_source_raw as generate_source_raw
from scripts.raw_generators.configs import RawGenerationConfig


def test_generate_source_raw_dispatches_generation_config(monkeypatch):
    called = {"value": False}

    def fake_run_raw_generation(config) -> None:
        assert config.company_key == "daon_pharma"
        called["value"] = True

    monkeypatch.setattr(generate_source_raw, "get_active_company_key", lambda: "daon_pharma")
    monkeypatch.setattr(generate_source_raw, "get_active_company_name", lambda company_key: "다온파마")
    monkeypatch.setattr(
        generate_source_raw,
        "get_raw_generation_config",
        lambda company_key: RawGenerationConfig(
            company_key="daon_pharma",
            company_name="다온파마",
            template_type="daon_like",
            start_month="2025-01",
            end_month="2025-12",
            branch_count=10,
            clinic_rep_count=75,
            hospital_rep_count=33,
            portfolio_source="hangyeol_portfolio",
            output_mode="merged_only",
        ),
    )
    monkeypatch.setattr(generate_source_raw, "run_raw_generation", fake_run_raw_generation)

    generate_source_raw.main()

    assert called["value"] is True


def test_generate_source_raw_rejects_unknown_company(monkeypatch):
    monkeypatch.setattr(generate_source_raw, "get_active_company_key", lambda: "custom_pharma")
    monkeypatch.setattr(generate_source_raw, "get_active_company_name", lambda company_key: "커스텀제약")
    monkeypatch.setattr(
        generate_source_raw,
        "get_raw_generation_config",
        lambda company_key: None,
    )

    try:
        generate_source_raw.main()
    except ValueError as exc:
        assert "등록된 raw generation config가 없습니다" in str(exc)
    else:
        raise AssertionError("ValueError should be raised when raw generator is missing.")
