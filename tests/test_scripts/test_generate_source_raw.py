from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.generate_source_raw as generate_source_raw


def test_generate_source_raw_dispatches_profile_module(monkeypatch):
    called = {"value": False}

    def fake_main() -> None:
        called["value"] = True

    monkeypatch.setattr(generate_source_raw, "get_active_company_key", lambda: "daon_pharma")
    monkeypatch.setattr(generate_source_raw, "get_active_company_name", lambda company_key: "다온파마")
    monkeypatch.setattr(
        generate_source_raw,
        "get_company_ops_profile",
        lambda company_key: SimpleNamespace(raw_generator_module="scripts.raw_generators.generate_daon_source_raw"),
    )
    monkeypatch.setattr(
        generate_source_raw.importlib,
        "import_module",
        lambda module_name: SimpleNamespace(main=fake_main),
    )

    generate_source_raw.main()

    assert called["value"] is True


def test_generate_source_raw_rejects_unknown_company(monkeypatch):
    monkeypatch.setattr(generate_source_raw, "get_active_company_key", lambda: "custom_pharma")
    monkeypatch.setattr(generate_source_raw, "get_active_company_name", lambda company_key: "커스텀제약")
    monkeypatch.setattr(
        generate_source_raw,
        "get_company_ops_profile",
        lambda company_key: SimpleNamespace(raw_generator_module=None),
    )

    try:
        generate_source_raw.main()
    except ValueError as exc:
        assert "등록된 raw 생성 스크립트가 없습니다" in str(exc)
    else:
        raise AssertionError("ValueError should be raised when raw generator is missing.")
