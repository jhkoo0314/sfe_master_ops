from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
import shutil
from uuid import uuid4

from tests.performance_regression_utils import (
    collect_directory_stats,
    ensure_script_outputs,
    measure_json_parse_seconds,
    run_script_main,
)


ROOT = Path(__file__).resolve().parents[2]
COMPANY_KEY = "hangyeol_pharma"
COMPANY_NAME = COMPANY_KEY
VALIDATION_ROOT = ROOT / "data" / "ops_validation" / COMPANY_KEY
SANDBOX_ROOT = VALIDATION_ROOT / "sandbox"
BUILDER_ROOT = VALIDATION_ROOT / "builder"
TEMP_ROOT = ROOT / "tests" / "_tmp_priority5_sandbox_perf"

FILE_SIZE_BUDGETS = {
    "sandbox_result_asset.json": (
        SANDBOX_ROOT / "sandbox_result_asset.json",
        4_500_000,
    ),
    "sandbox_report_preview_input_standard.json": (
        BUILDER_ROOT / "sandbox_report_preview_input_standard.json",
        150_000,
    ),
    "sandbox_report_preview_payload_standard.json": (
        BUILDER_ROOT / "sandbox_report_preview_payload_standard.json",
        150_000,
    ),
    "sandbox_report_preview.html": (
        BUILDER_ROOT / "sandbox_report_preview.html",
        200_000,
    ),
}
ASSET_BUDGETS = {
    "count": 20,
    "total_bytes": 1_800_000,
    "max_bytes": 250_000,
}
TIME_BUDGETS = {
    "payload_parse_seconds": 0.02,
    "validate_sandbox_seconds": 45.0,
}
REQUIRED_ARTIFACT_PATHS = [
    *(path for path, _budget in FILE_SIZE_BUDGETS.values()),
    SANDBOX_ROOT / "sandbox_template_payload_assets",
    BUILDER_ROOT / "sandbox_report_preview_assets",
]
REGENERATION_SCRIPTS = [
    "scripts.validate_sandbox_with_ops",
    "scripts.validate_builder_with_ops",
]


@lru_cache(maxsize=1)
def _ensure_sandbox_regression_artifacts() -> None:
    ensure_script_outputs(
        required_paths=REQUIRED_ARTIFACT_PATHS,
        script_modules=REGENERATION_SCRIPTS,
        company_key=COMPANY_KEY,
        company_name=COMPANY_NAME,
    )


@lru_cache(maxsize=1)
def _payload_parse_seconds() -> float:
    _ensure_sandbox_regression_artifacts()
    return measure_json_parse_seconds(
        BUILDER_ROOT / "sandbox_report_preview_payload_standard.json",
        repeats=7,
    )


@lru_cache(maxsize=1)
def _validate_sandbox_seconds() -> float:
    temp_dir = TEMP_ROOT / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        return run_script_main(
            "scripts.validate_sandbox_with_ops",
            company_key=COMPANY_KEY,
            company_name=COMPANY_NAME,
            attribute_overrides={
                "OUTPUT_ROOT": temp_dir,
            },
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_sandbox_preview_seed_sizes_within_budget():
    _ensure_sandbox_regression_artifacts()

    for name, (path, budget) in FILE_SIZE_BUDGETS.items():
        actual = path.stat().st_size
        assert actual <= budget, (
            f"{name} 크기가 상한을 넘었습니다. "
            f"현재 {actual:,} bytes, 기준 {budget:,} bytes"
        )


def test_sandbox_branch_assets_within_budget():
    _ensure_sandbox_regression_artifacts()

    for folder in [
        SANDBOX_ROOT / "sandbox_template_payload_assets",
        BUILDER_ROOT / "sandbox_report_preview_assets",
    ]:
        stats = collect_directory_stats(folder)
        assert stats["count"] > 0, f"{folder.name}에 branch asset이 없습니다."
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


def test_sandbox_builder_payload_records_chunked_branch_manifest():
    _ensure_sandbox_regression_artifacts()
    result_asset = json.loads((SANDBOX_ROOT / "sandbox_result_asset.json").read_text(encoding="utf-8"))
    payload = json.loads((BUILDER_ROOT / "sandbox_report_preview_payload_standard.json").read_text(encoding="utf-8"))
    source_seed = result_asset["dashboard_payload"]["template_payload"]
    seed = payload["payload"]

    assert source_seed["data_mode"] == "chunked_sandbox_branch_assets_v1"
    assert source_seed["branches"] == {}
    assert source_seed["branch_asset_counts"]["branch_count"] > 0
    assert seed["data_mode"] == "chunked_sandbox_branch_assets_v1"
    assert seed["branches"] == {}
    assert seed["branch_asset_counts"]["branch_count"] > 0
    assert len(seed["branch_index"]) == seed["branch_asset_counts"]["branch_count"]
    assert len(seed["branch_asset_manifest"]) == seed["branch_asset_counts"]["branch_count"]


def test_sandbox_seed_payload_parse_time_within_budget():
    parse_seconds = _payload_parse_seconds()
    assert parse_seconds <= TIME_BUDGETS["payload_parse_seconds"], (
        "Sandbox 첫 화면 seed payload JSON 파싱이 느려졌습니다. "
        f"현재 {parse_seconds:.4f}초, 기준 {TIME_BUDGETS['payload_parse_seconds']:.4f}초"
    )


def test_validate_sandbox_runtime_within_budget():
    runtime_seconds = _validate_sandbox_seconds()
    assert runtime_seconds <= TIME_BUDGETS["validate_sandbox_seconds"], (
        "Sandbox 검증 스크립트 실행 시간이 느려졌습니다. "
        f"현재 {runtime_seconds:.2f}초, 기준 {TIME_BUDGETS['validate_sandbox_seconds']:.2f}초"
    )
