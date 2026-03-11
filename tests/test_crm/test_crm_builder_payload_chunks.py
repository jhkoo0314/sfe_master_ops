from __future__ import annotations

import json
from pathlib import Path
import shutil
from uuid import uuid4

from modules.builder.service import (
    build_crm_template_input,
    build_template_payload,
    prepare_crm_chunk_assets,
)
from modules.crm.builder_payload import CHUNKED_CRM_DATA_MODE, build_chunked_crm_payload


ROOT = Path(__file__).resolve().parents[2]


def _make_temp_dir() -> Path:
    temp_dir = ROOT / "tests" / "_tmp_priority5_crm" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def _scope_payload(period_label: str, team_label: str, rep_label: str, rep_token: str) -> dict:
    rep_scope = {
        rep_token: {
            "period_label": period_label,
            "team_label": team_label,
            "rep_label": rep_label,
            "kpi_banner": {"leading": [], "ops": [], "outcome": []},
            "radar": {"labels": ["HIR"], "team_avg": [0.7], "target": [0.8]},
            "integrity": {"verified_pct": 70.0, "assisted_pct": 20.0, "self_only_pct": 10.0},
            "coach_summary": {"score": 0.712, "delta_display": "+0.100", "weight_rows": []},
            "behavior_axis": [{"label": "디테일", "score": 0.8, "tone": "blue"}],
            "behavior_diagnosis": "상세 콜 비중이 높습니다.",
            "pipeline": {
                "stages": [{"name": "Prospect", "count": 10, "pct": 100.0, "tone": "blue"}],
                "avg_dwell_days": 4.2,
                "conversion_rate": 61.5,
            },
            "matrix_rows": [
                {
                    "rep_id": rep_token,
                    "rep_name": rep_label,
                    "branch_name": team_label,
                    "hir": 0.8,
                    "rtr": 0.74,
                    "bcr": 0.69,
                    "phr": 0.77,
                    "nar": 0.82,
                    "ahs": 83.5,
                    "coach_score": 0.712,
                    "total_visits": 24,
                }
            ],
            "trend": {"labels": ["2026-03"], "hir": [0.8], "bcr": [0.69], "fgr": [2.4]},
            "quality_flags": [],
            "rep_options": [{"token": "ALL", "label": "전체 담당자"}],
            "rep_scope_data": {},
        }
    }
    return {
        "period_label": period_label,
        "team_label": team_label,
        "rep_label": "전체 담당자",
        "kpi_banner": {"leading": [], "ops": [], "outcome": []},
        "radar": {"labels": ["HIR"], "team_avg": [0.72], "target": [0.8]},
        "integrity": {"verified_pct": 72.0, "assisted_pct": 18.0, "self_only_pct": 10.0},
        "coach_summary": {"score": 0.723, "delta_display": "+0.080", "weight_rows": []},
        "behavior_axis": [{"label": "디테일", "score": 0.82, "tone": "blue"}],
        "behavior_diagnosis": "선행 행동이 안정적으로 유지됩니다.",
        "pipeline": {
            "stages": [{"name": "Prospect", "count": 10, "pct": 100.0, "tone": "blue"}],
            "avg_dwell_days": 4.0,
            "conversion_rate": 63.0,
        },
        "matrix_rows": [
            {
                "rep_id": rep_token,
                "rep_name": rep_label,
                "branch_name": team_label,
                "hir": 0.8,
                "rtr": 0.74,
                "bcr": 0.69,
                "phr": 0.77,
                "nar": 0.82,
                "ahs": 83.5,
                "coach_score": 0.712,
                "total_visits": 24,
            }
        ],
        "trend": {"labels": ["2026-03"], "hir": [0.8], "bcr": [0.69], "fgr": [2.4]},
        "quality_flags": [],
        "rep_options": [
            {"token": "ALL", "label": "전체 담당자"},
            {"token": rep_token, "label": rep_label},
        ],
        "rep_scope_data": rep_scope,
    }


def _build_sample_payload() -> dict:
    return {
        "overview": {"crm_activity_count": 12, "quality_status": "pass", "quality_score": 94.2},
        "activity_context": {"unique_reps": 2, "unique_hospitals": 6},
        "mapping_quality": {"hospital_mapping_rate": 0.975},
        "logic_reference": {"weights": [{"label": "HIR", "value": 0.3}]},
        "filters": {
            "period_options": [
                {"token": "2026-03", "label": "2026-03"},
                {"token": "ALL", "label": "전체 기간"},
            ],
            "team_options": [
                {"token": "ALL", "label": "전체 팀"},
                {"token": "SEOUL", "label": "서울지점"},
            ],
            "rep_options": [{"token": "ALL", "label": "전체 담당자"}],
            "default_period": "2026-03",
            "default_team": "ALL",
            "default_rep": "ALL",
        },
        "scope_data": {
            "2026-03|ALL": _scope_payload("2026-03", "전체 팀", "김민수", "R001"),
            "ALL|ALL": _scope_payload("전체 기간", "전체 팀", "김민수", "R001"),
        },
    }


def test_chunked_crm_payload_moves_scope_data_out_of_seed():
    payload = _build_sample_payload()

    manifest, asset_chunks = build_chunked_crm_payload(payload)

    assert manifest["data_mode"] == CHUNKED_CRM_DATA_MODE
    assert manifest["scope_data"] == {}
    assert manifest["default_scope_key"] == "2026-03|ALL"
    assert manifest["scope_asset_counts"]["scope_count"] == 2
    assert manifest["scope_asset_counts"]["rep_scope_count"] == 2

    default_chunk = manifest["scope_asset_manifest"]["2026-03|ALL"]
    assert asset_chunks[default_chunk]["scope_key"] == "2026-03|ALL"
    assert "R001" in asset_chunks[default_chunk]["scope_payload"]["rep_scope_data"]


def test_builder_service_prepares_crm_chunk_assets_before_render():
    temp_dir = _make_temp_dir()
    try:
        payload = _build_sample_payload()
        payload_path = temp_dir / "crm_builder_payload.json"
        payload_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        template_path = temp_dir / "crm_analysis_template.html"
        template_path.write_text("<script>window.__CRM_DATA__ = {};</script>", encoding="utf-8")

        builder_input = build_crm_template_input(
            str(template_path),
            builder_payload_path=str(payload_path),
        )
        builder_payload = build_template_payload(builder_input)

        prepare_crm_chunk_assets(
            builder_payload,
            payload_source_path=str(payload_path),
            output_root=str(temp_dir),
        )

        asset_dir = temp_dir / "crm_analysis_preview_assets"
        asset_files = sorted(path.name for path in asset_dir.glob("*.js"))

        assert builder_payload.payload["data_mode"] == CHUNKED_CRM_DATA_MODE
        assert builder_payload.payload["asset_base"] == "crm_analysis_preview_assets"
        assert builder_payload.payload["scope_data"] == {}
        assert asset_files == sorted(builder_payload.payload["scope_asset_manifest"].values())
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
