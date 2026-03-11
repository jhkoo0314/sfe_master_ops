from __future__ import annotations

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
TERRITORY_ROOT = VALIDATION_ROOT / "territory"
BUILDER_ROOT = VALIDATION_ROOT / "builder"
TEMP_ROOT = ROOT / "tests" / "_tmp_priority3"

FILE_SIZE_BUDGETS = {
    "territory_builder_payload.json": (
        TERRITORY_ROOT / "territory_builder_payload.json",
        1_500_000,
    ),
    "territory_map_preview_input_standard.json": (
        BUILDER_ROOT / "territory_map_preview_input_standard.json",
        1_600_000,
    ),
    "territory_map_preview_payload_standard.json": (
        BUILDER_ROOT / "territory_map_preview_payload_standard.json",
        1_600_000,
    ),
    "territory_map_preview.html": (
        BUILDER_ROOT / "territory_map_preview.html",
        900_000,
    ),
}
CHUNK_BUDGETS = {
    "count": 650,
    "total_bytes": 13_000_000,
    "max_bytes": 40_000,
}
TIME_BUDGETS = {
    "payload_parse_seconds": 0.10,
    "validate_territory_seconds": 25.0,
}
REQUIRED_ARTIFACT_PATHS = [
    *(path for path, _budget in FILE_SIZE_BUDGETS.values()),
    BUILDER_ROOT / "territory_map_preview_assets",
]
REGENERATION_SCRIPTS = [
    "scripts.validate_sandbox_with_ops",
    "scripts.validate_territory_with_ops",
    "scripts.validate_builder_with_ops",
]


@lru_cache(maxsize=1)
def _ensure_territory_regression_artifacts() -> None:
    ensure_script_outputs(
        required_paths=REQUIRED_ARTIFACT_PATHS,
        script_modules=REGENERATION_SCRIPTS,
        company_key=COMPANY_KEY,
        company_name=COMPANY_NAME,
    )


def _artifact_sizes() -> dict[str, int]:
    _ensure_territory_regression_artifacts()
    return {
        name: path.stat().st_size
        for name, (path, _budget) in FILE_SIZE_BUDGETS.items()
    }


def _chunk_stats() -> dict[str, int]:
    _ensure_territory_regression_artifacts()
    return collect_directory_stats(BUILDER_ROOT / "territory_map_preview_assets")


@lru_cache(maxsize=1)
def _payload_parse_seconds() -> float:
    _ensure_territory_regression_artifacts()
    return measure_json_parse_seconds(
        BUILDER_ROOT / "territory_map_preview_payload_standard.json",
        repeats=7,
    )


@lru_cache(maxsize=1)
def _validate_territory_seconds() -> float:
    # 실제 로직 시간은 재되, 저장 위치는 임시 폴더로 바꿔서 작업 흔적을 줄인다.
    temp_dir = TEMP_ROOT / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        return run_script_main(
            "scripts.validate_territory_with_ops",
            company_key=COMPANY_KEY,
            company_name=COMPANY_NAME,
            attribute_overrides={
                "OUTPUT_ROOT": temp_dir,
            },
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_territory_artifact_sizes_within_budget():
    sizes = _artifact_sizes()

    for name, (path, budget) in FILE_SIZE_BUDGETS.items():
        actual = sizes[name]
        assert actual <= budget, (
            f"{name} 크기가 상한을 넘었습니다. "
            f"현재 {actual:,} bytes, 기준 {budget:,} bytes, 경로: {path}"
        )


def test_territory_chunk_assets_within_budget():
    stats = _chunk_stats()

    assert stats["count"] > 0, "territory_map_preview_assets에 chunk 파일이 없습니다."
    assert stats["count"] <= CHUNK_BUDGETS["count"], (
        f"chunk 개수가 너무 많습니다. 현재 {stats['count']}, 기준 {CHUNK_BUDGETS['count']}"
    )
    assert stats["total_bytes"] <= CHUNK_BUDGETS["total_bytes"], (
        "chunk 전체 크기가 너무 큽니다. "
        f"현재 {stats['total_bytes']:,} bytes, 기준 {CHUNK_BUDGETS['total_bytes']:,} bytes"
    )
    assert stats["max_bytes"] <= CHUNK_BUDGETS["max_bytes"], (
        "가장 큰 chunk 파일이 너무 큽니다. "
        f"현재 {stats['max_bytes']:,} bytes, 기준 {CHUNK_BUDGETS['max_bytes']:,} bytes"
    )


def test_territory_seed_payload_parse_time_within_budget():
    parse_seconds = _payload_parse_seconds()
    assert parse_seconds <= TIME_BUDGETS["payload_parse_seconds"], (
        "첫 화면 seed payload JSON 파싱이 느려졌습니다. "
        f"현재 {parse_seconds:.4f}초, 기준 {TIME_BUDGETS['payload_parse_seconds']:.4f}초"
    )


def test_validate_territory_runtime_within_budget():
    runtime_seconds = _validate_territory_seconds()
    assert runtime_seconds <= TIME_BUDGETS["validate_territory_seconds"], (
        "Territory 검증 스크립트 실행 시간이 느려졌습니다. "
        f"현재 {runtime_seconds:.2f}초, 기준 {TIME_BUDGETS['validate_territory_seconds']:.2f}초"
    )
