from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from tests.performance_regression_utils import collect_directory_stats, ensure_script_outputs


ROOT = Path(__file__).resolve().parents[2]
COMPANY_KEY = "hangyeol_pharma"
COMPANY_NAME = COMPANY_KEY
VALIDATION_ROOT = ROOT / "data" / "ops_validation" / COMPANY_KEY
PRESCRIPTION_ROOT = VALIDATION_ROOT / "prescription"
BUILDER_ROOT = VALIDATION_ROOT / "builder"

FILE_SIZE_BUDGETS = {
    "prescription_builder_payload.json": (
        PRESCRIPTION_ROOT / "prescription_builder_payload.json",
        250_000,
    ),
    "prescription_flow_preview_input_standard.json": (
        BUILDER_ROOT / "prescription_flow_preview_input_standard.json",
        250_000,
    ),
    "prescription_flow_preview_payload_standard.json": (
        BUILDER_ROOT / "prescription_flow_preview_payload_standard.json",
        250_000,
    ),
    "prescription_flow_preview.html": (
        BUILDER_ROOT / "prescription_flow_preview.html",
        200_000,
    ),
}
ASSET_BUDGETS = {
    "count": 20,
    "total_bytes": 18_000_000,
    "max_bytes": 13_000_000,
}
REQUIRED_ARTIFACT_PATHS = [
    *(path for path, _budget in FILE_SIZE_BUDGETS.values()),
    PRESCRIPTION_ROOT / "prescription_builder_payload_assets",
    BUILDER_ROOT / "prescription_flow_preview_assets",
]
REGENERATION_SCRIPTS = [
    "scripts.validate_prescription_with_ops",
    "scripts.validate_builder_with_ops",
]


@lru_cache(maxsize=1)
def _ensure_prescription_regression_artifacts() -> None:
    ensure_script_outputs(
        required_paths=REQUIRED_ARTIFACT_PATHS,
        script_modules=REGENERATION_SCRIPTS,
        company_key=COMPANY_KEY,
        company_name=COMPANY_NAME,
    )


def test_prescription_preview_seed_sizes_within_budget():
    _ensure_prescription_regression_artifacts()

    for name, (path, budget) in FILE_SIZE_BUDGETS.items():
        actual = path.stat().st_size
        assert actual <= budget, (
            f"{name} 크기가 상한을 넘었습니다. "
            f"현재 {actual:,} bytes, 기준 {budget:,} bytes"
        )


def test_prescription_detail_assets_within_budget():
    _ensure_prescription_regression_artifacts()

    for folder in [
        PRESCRIPTION_ROOT / "prescription_builder_payload_assets",
        BUILDER_ROOT / "prescription_flow_preview_assets",
    ]:
        stats = collect_directory_stats(folder)
        assert stats["count"] > 0, f"{folder.name}에 detail asset이 없습니다."
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


def test_prescription_builder_payload_records_chunked_detail_manifest():
    _ensure_prescription_regression_artifacts()
    payload = json.loads((PRESCRIPTION_ROOT / "prescription_builder_payload.json").read_text(encoding="utf-8"))

    assert payload["data_mode"] == "chunked_prescription_detail_assets_v1"
    assert payload["claims"] == []
    assert payload["hospital_traces"] == []
    assert payload["rep_kpis"] == []
    assert payload["detail_asset_counts"]["hospital_traces"] > 0
    assert "ALL" in payload["detail_asset_manifest"]["claims"]
