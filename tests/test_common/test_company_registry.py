from pathlib import Path
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.company_registry import (
    find_company_by_name,
    get_company_by_key,
    list_registered_companies,
    register_company,
    resolve_company_reference,
)


def _make_sandbox(name: str) -> Path:
    sandbox = ROOT / "tests" / ".tmp_company_registry" / f"{name}_{uuid.uuid4().hex}"
    sandbox.mkdir(parents=True, exist_ok=True)
    return sandbox


def test_list_registered_companies_seeds_defaults():
    sandbox = _make_sandbox("seed")
    try:
        companies = list_registered_companies(sandbox)

        keys = {item.company_key for item in companies}
        assert "daon_pharma" in keys
        assert "hangyeol_pharma" in keys
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_register_company_creates_fixed_generated_key():
    sandbox = _make_sandbox("register")
    try:
        entry = register_company(sandbox, "지원제약", company_code_external="1234")

        assert entry.company_key.startswith("company_")
        assert entry.company_name == "지원제약"
        assert entry.company_code_external == "1234"

        loaded = get_company_by_key(sandbox, entry.company_key)
        assert loaded is not None
        assert loaded.company_name == "지원제약"
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_register_company_returns_existing_entry_on_duplicate_name():
    sandbox = _make_sandbox("duplicate")
    try:
        first = register_company(sandbox, "지원제약")
        second = register_company(sandbox, " 지원제약 ")

        assert first.company_key == second.company_key
        found = find_company_by_name(sandbox, "지원제약")
        assert found is not None
        assert found.company_key == first.company_key
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_resolve_company_reference_matches_external_code_and_alias():
    sandbox = _make_sandbox("resolve")
    try:
        entry = resolve_company_reference(sandbox, "daon_pharma")
        assert entry is not None
        assert entry.company_key == "daon_pharma"

        alias_entry = resolve_company_reference(sandbox, "다온제약")
        assert alias_entry is not None
        assert alias_entry.company_key == "daon_pharma"
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
