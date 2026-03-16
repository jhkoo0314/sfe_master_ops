from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modules.builder.service import build_sandbox_template_input, build_template_payload, render_builder_html
from result_assets.sandbox_result_asset import SandboxResultAsset


ROOT = Path(__file__).resolve().parents[2]


def _pick_sandbox_asset_path() -> Path:
    candidates = [
        ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "sandbox" / "sandbox_result_asset.json",
        ROOT / "data" / "ops_validation" / "daon_pharma" / "sandbox" / "sandbox_result_asset.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("sandbox_result_asset.json fixture not found for renderer snapshot tests")


def _load_dashboard_payload() -> dict[str, Any]:
    asset_obj = json.loads(_pick_sandbox_asset_path().read_text(encoding="utf-8"))
    return dict(asset_obj.get("dashboard_payload") or {})


def _render_html() -> str:
    asset_obj = json.loads(_pick_sandbox_asset_path().read_text(encoding="utf-8"))
    asset = SandboxResultAsset.model_validate(asset_obj)
    builder_input = build_sandbox_template_input(
        asset,
        str(ROOT / "templates" / "report_template.html"),
        source_asset_path=str(_pick_sandbox_asset_path()),
    )
    builder_payload = build_template_payload(builder_input)
    return render_builder_html(builder_payload)


def test_group_view_snapshot_contract() -> None:
    dashboard = _load_dashboard_payload()
    block_payload = dashboard.get("block_payload") or {}

    assert "official_kpi_6" in block_payload
    assert "total_summary" in block_payload
    assert "total_trend" in block_payload
    assert "data_health" in block_payload

    html = _render_html()
    assert "id='groupView'" in html
    assert "resolveSlot('group_summary_slot'" in html or "resolveBlock('total_summary')" in html
    assert html.count("id='card_metric_") >= 6


def test_individual_view_snapshot_contract() -> None:
    dashboard = _load_dashboard_payload()
    block_payload = dashboard.get("block_payload") or {}
    member_block = block_payload.get("member_performance") or {}

    assert "total_avg" in member_block
    assert "sample_member" in member_block

    html = _render_html()
    assert "id='indivView'" in html
    assert "id='activity_breakdown'" in html
    assert "resolveBranchBlock(branchKey, 'branch_member_summary')" in html
    assert "renderInsightSlot" in html


def test_product_view_snapshot_contract() -> None:
    dashboard = _load_dashboard_payload()
    block_payload = dashboard.get("block_payload") or {}
    product_block = block_payload.get("product_analysis") or {}

    products = list(product_block.get("products") or [])
    assert len(products) >= 1

    html = _render_html()
    assert "id='pSel'" in html
    assert "resolveBlock('product_analysis')" in html

    assert "const db = {" in html
    assert "\"block_payload\"" in html
