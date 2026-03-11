from __future__ import annotations

import json
from pathlib import Path
import shutil
from uuid import uuid4

import pandas as pd

from modules.builder.service import (
    build_prescription_template_input,
    build_template_payload,
    prepare_prescription_chunk_assets,
)
from modules.prescription.builder_payload import (
    CHUNKED_PRESCRIPTION_DATA_MODE,
    build_chunked_prescription_payload,
    build_prescription_builder_payload,
)


ROOT = Path(__file__).resolve().parents[2]


def _make_temp_dir() -> Path:
    temp_dir = ROOT / "tests" / "_tmp_priority5" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def _build_sample_payload() -> dict:
    summary = {
        "standard_record_count": 12,
        "flow_record_count": 8,
        "gap_record_count": 1,
        "connected_hospital_count": 2,
        "flow_completion_rate": 0.92,
        "quality_status": "pass",
        "quality_score": 96.5,
        "claim_validation_summary": {
            "pass_count": 1,
            "review_count": 1,
            "suspect_count": 0,
        },
    }
    claim_df = pd.DataFrame(
        [
            {
                "period_type": "quarter",
                "period_value": "2026-Q1",
                "period_label": "2026-Q1",
                "year": "2026",
                "year_quarter": "2026-Q1",
                "year_month": "",
                "rep_id": "R001",
                "rep_name": "김민수",
                "branch_name": "서울지점",
                "territory_group": "서울",
                "territory_name": "강남",
                "hospital_id": "H001",
                "hospital_name": "서울A병원",
                "hospital_type": "의원",
                "product_name": "품목A",
                "claimed_amount": 1_200_000.0,
                "tracked_amount": 1_100_000.0,
                "variance_amount": 100_000.0,
                "variance_rate": 0.0909,
                "verdict": "REVIEW",
                "pharmacy_count": 1,
                "wholesaler_count": 1,
                "active_month_count": 2,
                "flow_count": 2,
                "claim_source": "demo",
                "review_note": "추가 확인 필요",
                "severity": "med",
                "trace_case": "CLAIM_REVIEW",
            },
            {
                "period_type": "quarter",
                "period_value": "2026-Q2",
                "period_label": "2026-Q2",
                "year": "2026",
                "year_quarter": "2026-Q2",
                "year_month": "",
                "rep_id": "R001",
                "rep_name": "김민수",
                "branch_name": "서울지점",
                "territory_group": "서울",
                "territory_name": "강남",
                "hospital_id": "H001",
                "hospital_name": "서울A병원",
                "hospital_type": "의원",
                "product_name": "품목A",
                "claimed_amount": 900_000.0,
                "tracked_amount": 900_000.0,
                "variance_amount": 0.0,
                "variance_rate": 0.0,
                "verdict": "PASS",
                "pharmacy_count": 1,
                "wholesaler_count": 1,
                "active_month_count": 1,
                "flow_count": 1,
                "claim_source": "demo",
                "review_note": "정상",
                "severity": "low",
                "trace_case": "CLAIM_CONFIRMED",
            },
        ]
    )
    flow_df = pd.DataFrame(
        [
            {
                "metric_month": "202601",
                "year_quarter": "2026-Q1",
                "flow_status": "connected",
                "total_amount": 550_000.0,
                "territory_group": "서울",
                "territory_name": "강남",
                "rep_name": "김민수",
                "branch_name": "서울지점",
                "hospital_id": "H001",
                "hospital_name": "서울A병원",
                "product_name": "품목A",
                "pharmacy_id": "P001",
                "wholesaler_id": "W001",
            },
            {
                "metric_month": "202602",
                "year_quarter": "2026-Q1",
                "flow_status": "connected",
                "total_amount": 550_000.0,
                "territory_group": "서울",
                "territory_name": "강남",
                "rep_name": "김민수",
                "branch_name": "서울지점",
                "hospital_id": "H001",
                "hospital_name": "서울A병원",
                "product_name": "품목A",
                "pharmacy_id": "P001",
                "wholesaler_id": "W001",
            },
            {
                "metric_month": "202604",
                "year_quarter": "2026-Q2",
                "flow_status": "connected",
                "total_amount": 900_000.0,
                "territory_group": "서울",
                "territory_name": "강남",
                "rep_name": "김민수",
                "branch_name": "서울지점",
                "hospital_id": "H001",
                "hospital_name": "서울A병원",
                "product_name": "품목A",
                "pharmacy_id": "P001",
                "wholesaler_id": "W001",
            },
        ]
    )
    gap_df = pd.DataFrame(
        [
            {
                "year_quarter": "2026-Q1",
                "metric_month": "202601",
                "pharmacy_id": "P002",
                "pharmacy_name": "강남약국",
                "pharmacy_region_key": "서울",
                "wholesaler_id": "W001",
                "product_id": "PRD001",
                "product_name": "품목A",
                "quantity": 5,
                "gap_reason": "hospital_unmapped",
            }
        ]
    )
    rep_kpi_df = pd.DataFrame(
        [
            {
                "year_quarter": "2026-Q1",
                "rep_id": "R001",
                "rep_name": "김민수",
                "branch_name": "서울지점",
                "territory_group": "서울",
                "territory_name": "강남",
                "product_name": "품목A",
                "total_amount": 1_100_000.0,
                "pre_share_amount": 1_200_000.0,
                "post_share_amount": 1_100_000.0,
                "settlement_gap_amount": -100_000.0,
                "settlement_gap_rate": -0.0833,
                "status": "Settled",
                "rule_version": "SIM-CLAIM-v1",
                "rule_applied": True,
            },
            {
                "year_quarter": "2026-Q2",
                "rep_id": "R001",
                "rep_name": "김민수",
                "branch_name": "서울지점",
                "territory_group": "서울",
                "territory_name": "강남",
                "product_name": "품목A",
                "total_amount": 900_000.0,
                "pre_share_amount": 900_000.0,
                "post_share_amount": 900_000.0,
                "settlement_gap_amount": 0.0,
                "settlement_gap_rate": 0.0,
                "status": "Confirmed",
                "rule_version": "SIM-CLAIM-v1",
                "rule_applied": True,
            },
        ]
    )

    return build_prescription_builder_payload(
        company_name="테스트제약",
        summary=summary,
        claim_df=claim_df,
        flow_df=flow_df,
        gap_df=gap_df,
        rep_kpi_df=rep_kpi_df,
        download_files={"claim_validation": "prescription_claim_validation.xlsx"},
    )


def test_chunked_prescription_payload_moves_heavy_detail_rows_out_of_seed():
    payload = _build_sample_payload()

    manifest, asset_chunks = build_chunked_prescription_payload(payload)

    assert manifest["data_mode"] == CHUNKED_PRESCRIPTION_DATA_MODE
    assert manifest["claims"] == []
    assert manifest["gaps"] == []
    assert manifest["hospital_traces"] == []
    assert manifest["rep_kpis"] == []
    assert manifest["detail_asset_counts"]["claims"] == 2
    assert manifest["detail_asset_counts"]["hospital_traces"] > 0
    assert "ALL" in manifest["detail_asset_manifest"]["rep_kpis"]
    assert "2026-Q1" in manifest["detail_asset_manifest"]["claims"]

    q1_claim_asset = manifest["detail_asset_manifest"]["claims"]["2026-Q1"]
    assert asset_chunks[q1_claim_asset]["rows"][0]["year_quarter"] == "2026-Q1"


def test_builder_service_prepares_prescription_chunk_assets_before_render():
    tmp_path = _make_temp_dir()
    try:
        payload = _build_sample_payload()
        payload_path = tmp_path / "prescription_builder_payload.json"
        payload_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        template_path = tmp_path / "prescription_flow_template.html"
        template_path.write_text("<script>window.__PRESCRIPTION_DATA__ = {};</script>", encoding="utf-8")

        builder_input = build_prescription_template_input(
            str(template_path),
            builder_payload_path=str(payload_path),
        )
        builder_payload = build_template_payload(builder_input)

        prepare_prescription_chunk_assets(
            builder_payload,
            payload_source_path=str(payload_path),
            output_root=str(tmp_path),
        )

        assert builder_payload.payload["data_mode"] == CHUNKED_PRESCRIPTION_DATA_MODE
        assert builder_payload.payload["claims"] == []
        assert builder_payload.payload["rep_kpis"] == []
        assert builder_payload.payload["asset_base"] == "prescription_flow_preview_assets"
        assert (tmp_path / "prescription_flow_preview_assets").exists()
        assert any((tmp_path / "prescription_flow_preview_assets").glob("*.js"))
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)
