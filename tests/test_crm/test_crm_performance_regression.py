from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from tests.performance_regression_utils import collect_directory_stats, ensure_script_outputs


ROOT = Path(__file__).resolve().parents[2]
COMPANY_KEY = "hangyeol_pharma"
COMPANY_NAME = COMPANY_KEY
VALIDATION_ROOT = ROOT / "data" / "ops_validation" / COMPANY_KEY
CRM_ROOT = VALIDATION_ROOT / "crm"
BUILDER_ROOT = VALIDATION_ROOT / "builder"

FILE_SIZE_BUDGETS = {
    "crm_builder_payload.json": (
        CRM_ROOT / "crm_builder_payload.json",
        60_000,
    ),
    "crm_analysis_preview_input_standard.json": (
        BUILDER_ROOT / "crm_analysis_preview_input_standard.json",
        100_000,
    ),
    "crm_analysis_preview_payload_standard.json": (
        BUILDER_ROOT / "crm_analysis_preview_payload_standard.json",
        100_000,
    ),
    "crm_analysis_preview.html": (
        BUILDER_ROOT / "crm_analysis_preview.html",
        100_000,
    ),
}
ASSET_BUDGETS = {
    "count": 80,
    "total_bytes": 8_500_000,
    "max_bytes": 650_000,
}
REQUIRED_ARTIFACT_PATHS = [
    *(path for path, _budget in FILE_SIZE_BUDGETS.values()),
    CRM_ROOT / "crm_builder_payload_assets",
    BUILDER_ROOT / "crm_analysis_preview_assets",
]
REGENERATION_SCRIPTS = [
    "scripts.validate_crm_with_ops",
    "scripts.validate_builder_with_ops",
]


@lru_cache(maxsize=1)
def _ensure_crm_regression_artifacts() -> None:
    ensure_script_outputs(
        required_paths=REQUIRED_ARTIFACT_PATHS,
        script_modules=REGENERATION_SCRIPTS,
        company_key=COMPANY_KEY,
        company_name=COMPANY_NAME,
    )


def test_crm_preview_seed_sizes_within_budget():
    _ensure_crm_regression_artifacts()

    for name, (path, budget) in FILE_SIZE_BUDGETS.items():
        actual = path.stat().st_size
        assert actual <= budget, (
            f"{name} 크기가 상한을 넘었습니다. "
            f"현재 {actual:,} bytes, 기준 {budget:,} bytes"
        )


def test_crm_scope_assets_within_budget():
    _ensure_crm_regression_artifacts()

    for folder in [
        CRM_ROOT / "crm_builder_payload_assets",
        BUILDER_ROOT / "crm_analysis_preview_assets",
    ]:
        stats = collect_directory_stats(folder)
        assert stats["count"] > 0, f"{folder.name}에 scope asset이 없습니다."
        assert stats["count"] <= ASSET_BUDGETS["count"], (
            f"{folder.name} asset 개수가 너무 많습니다. 현재 {stats['count']}, 기준 {ASSET_BUDGETS['count']}"
        )
        assert stats["total_bytes"] <= ASSET_BUDGETS["total_bytes"], (
            f"{folder.name} 전체 크기가 너무 큽니다. "
            f"현재 {stats['total_bytes']:,} bytes, 기준 {ASSET_BUDGETS['total_bytes']:,} bytes"
        )
        assert stats["max_bytes"] <= ASSET_BUDGETS["max_bytes"], (
            f"{folder.name}의 가장 큰 asset이 너무 큽니다. "
            f"현재 {stats['max_bytes']:,} bytes, 기준 {ASSET_BUDGETS['max_bytes']:,} bytes"
        )


def test_crm_builder_payload_records_chunked_scope_manifest():
    _ensure_crm_regression_artifacts()
    payload = json.loads((CRM_ROOT / "crm_builder_payload.json").read_text(encoding="utf-8"))

    assert payload["data_mode"] == "chunked_crm_scope_assets_v1"
    assert payload["scope_data"] == {}
    assert payload["scope_asset_counts"]["scope_count"] > 0
    assert "ALL|ALL" in payload["scope_asset_manifest"]
