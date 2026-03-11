from __future__ import annotations

import json
from pathlib import Path
import shutil
from uuid import uuid4

from modules.builder.schemas import BuilderPayloadStandard
from modules.builder.service import prepare_sandbox_chunk_assets
from modules.sandbox.builder_payload import (
    CHUNKED_SANDBOX_DATA_MODE,
    build_chunked_sandbox_payload,
)


ROOT = Path(__file__).resolve().parents[2]


def _make_temp_dir() -> Path:
    temp_dir = ROOT / "tests" / "_tmp_priority5_sandbox" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def _build_sample_payload() -> dict:
    return {
        "branches": {
            "서울지점": {
                "members": [
                    {
                        "rep_id": "R001",
                        "성명": "김민수",
                        "HIR": 81,
                        "RTR": 74,
                        "BCR": 69,
                        "PHR": 72,
                        "PI": 102,
                        "FGR": 6,
                        "monthly_actual": [12, 11, 13],
                        "monthly_target": [10, 10, 12],
                        "prod_matrix": [{"name": "품목A", "ms": 12.5, "growth": 4.2}],
                    }
                ],
                "avg": {"HIR": 81, "RTR": 74, "BCR": 69, "PHR": 72, "PI": 102, "FGR": 6},
                "achieve": 102.4,
                "monthly_actual": [12, 11, 13],
                "monthly_target": [10, 10, 12],
                "analysis": {"importance": {"PT": 0.5}},
                "prod_analysis": {},
            },
            "부산지점": {
                "members": [
                    {
                        "rep_id": "R002",
                        "성명": "이서연",
                        "HIR": 77,
                        "RTR": 71,
                        "BCR": 65,
                        "PHR": 69,
                        "PI": 98,
                        "FGR": 3,
                        "monthly_actual": [9, 8, 10],
                        "monthly_target": [10, 9, 10],
                        "prod_matrix": [{"name": "품목A", "ms": 10.1, "growth": 2.7}],
                    }
                ],
                "avg": {"HIR": 77, "RTR": 71, "BCR": 65, "PHR": 69, "PI": 98, "FGR": 3},
                "achieve": 98.1,
                "monthly_actual": [9, 8, 10],
                "monthly_target": [10, 9, 10],
                "analysis": {"importance": {"PT": 0.2}},
                "prod_analysis": {},
            },
        },
        "products": ["품목A"],
        "total_prod_analysis": {
            "품목A": {
                "achieve": 100.2,
                "avg": {"HIR": 79, "RTR": 72, "BCR": 67, "PHR": 70, "PI": 100, "FGR": 4},
                "monthly_actual": [21, 19, 23],
                "monthly_target": [20, 19, 22],
            }
        },
        "total": {
            "achieve": 100.2,
            "avg": {"HIR": 79, "RTR": 72, "BCR": 67, "PHR": 70, "PI": 100, "FGR": 4},
            "monthly_actual": [21, 19, 23],
            "monthly_target": [20, 19, 22],
            "analysis": {"importance": {"PT": 0.4}},
        },
        "total_avg": {"HIR": 79, "RTR": 72, "BCR": 67, "PHR": 70, "PI": 100, "FGR": 4},
        "data_health": {"integrity_score": 96.2, "mapped_fields": 12, "missing_fields": 1},
        "missing_data": [{"지점": "OPS", "성명": "UNMAPPED", "품목": "orphan_sales_hospitals"}],
    }


def test_chunked_sandbox_payload_moves_branch_data_out_of_seed():
    payload = _build_sample_payload()

    manifest, asset_chunks = build_chunked_sandbox_payload(payload)

    assert manifest["data_mode"] == CHUNKED_SANDBOX_DATA_MODE
    assert manifest["branches"] == {}
    assert manifest["branch_asset_counts"]["branch_count"] == 2
    assert manifest["branch_asset_counts"]["member_count"] == 2
    assert set(manifest["branch_asset_manifest"]) == {"서울지점", "부산지점"}
    assert len(asset_chunks) == 2

    seoul_chunk_name = manifest["branch_asset_manifest"]["서울지점"]
    assert asset_chunks[seoul_chunk_name]["branch_name"] == "서울지점"
    assert asset_chunks[seoul_chunk_name]["branch_payload"]["members"][0]["성명"] == "김민수"


def test_builder_service_copies_sandbox_branch_assets_for_builder_output():
    temp_dir = _make_temp_dir()
    try:
        payload = _build_sample_payload()
        manifest, asset_chunks = build_chunked_sandbox_payload(payload)

        source_asset_path = temp_dir / "sandbox_result_asset.json"
        source_asset_path.write_text(json.dumps({"asset_type": "sandbox_result_asset"}, ensure_ascii=False), encoding="utf-8")

        source_asset_dir = temp_dir / "sandbox_template_payload_assets"
        source_asset_dir.mkdir(parents=True, exist_ok=True)
        for chunk_name, chunk_payload in asset_chunks.items():
            branch_key_json = json.dumps(str(chunk_payload.get("branch_name") or ""), ensure_ascii=False)
            chunk_script = (
                "window.__SANDBOX_BRANCH_DATA__ = window.__SANDBOX_BRANCH_DATA__ || {};\n"
                f"window.__SANDBOX_BRANCH_DATA__[{branch_key_json}] = "
                f"{json.dumps(chunk_payload.get('branch_payload', {}), ensure_ascii=False)};\n"
            )
            (source_asset_dir / chunk_name).write_text(chunk_script, encoding="utf-8")

        builder_payload = BuilderPayloadStandard(
            template_key="report_template",
            template_path=str(temp_dir / "report_template.html"),
            report_title="Sandbox 성과 보고서",
            payload=manifest,
            source_modules=["sandbox"],
            output_name="sandbox_report_preview.html",
            render_mode="report_data_json",
        )

        prepare_sandbox_chunk_assets(
            builder_payload,
            asset_source_path=str(source_asset_path),
            output_root=str(temp_dir),
        )

        asset_dir = temp_dir / "sandbox_report_preview_assets"
        asset_files = sorted(path.name for path in asset_dir.glob("*.js"))

        assert builder_payload.payload["data_mode"] == CHUNKED_SANDBOX_DATA_MODE
        assert builder_payload.payload["asset_base"] == "sandbox_report_preview_assets"
        assert builder_payload.payload["branches"] == {}
        assert asset_files == sorted(builder_payload.payload["branch_asset_manifest"].values())
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
