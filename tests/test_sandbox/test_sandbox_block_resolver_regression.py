from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modules.sandbox.block_resolver import (
    get_fallback_counter,
    reset_fallback_counter,
    resolve_block,
    resolve_branch_block,
    resolve_slot,
)


def _pick_sandbox_asset_path() -> Path:
    candidates = [
        Path(r"C:\sfe_master_ops\data\ops_validation\hangyeol_pharma\sandbox\sandbox_result_asset.json"),
        Path(r"C:\sfe_master_ops\data\ops_validation\daon_pharma\sandbox\sandbox_result_asset.json"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("sandbox_result_asset.json fixture not found for regression tests")


def _load_asset() -> dict[str, Any]:
    path = _pick_sandbox_asset_path()
    return json.loads(path.read_text(encoding="utf-8"))


def _load_chunk_branch_payload(asset_obj: dict[str, Any], branch_key: str) -> dict[str, Any]:
    asset_path = _pick_sandbox_asset_path()
    template_payload = ((asset_obj.get("dashboard_payload") or {}).get("template_payload") or {})
    branch_manifest = template_payload.get("branch_asset_manifest", {}) or {}
    chunk_name = str(branch_manifest.get(branch_key) or "")
    if not chunk_name:
        return {}
    chunk_path = asset_path.parent / "sandbox_template_payload_assets" / chunk_name
    if not chunk_path.exists():
        return {}
    lines = chunk_path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2:
        return {}
    second = lines[1]
    token = " = "
    pos = second.find(token)
    if pos < 0:
        return {}
    json_part = second[pos + len(token):].rstrip(";")
    return json.loads(json_part)


def test_kpi_value_equivalence_template_vs_block_payload() -> None:
    asset = _load_asset()
    dashboard = asset.get("dashboard_payload") or {}
    template_payload = dashboard.get("template_payload") or {}
    block_payload = dashboard.get("block_payload") or {}

    official_t = template_payload.get("official_kpi_6") or {}
    official_b = (block_payload.get("official_kpi_6") or {}).get("metrics") or {}
    assert official_t.get("monthly_attainment_rate") == official_b.get("monthly_attainment_rate")
    assert official_t.get("annual_attainment_rate") == official_b.get("annual_attainment_rate")

    total_t = template_payload.get("total") or {}
    total_b = block_payload.get("total_summary") or {}
    assert float(total_t.get("achieve", 0.0) or 0.0) == float(total_b.get("achieve", 0.0) or 0.0)
    assert float((total_t.get("avg") or {}).get("PI", 0.0) or 0.0) == float((total_b.get("avg") or {}).get("PI", 0.0) or 0.0)

    sample_b = (block_payload.get("member_performance") or {}).get("sample_member") or {}
    if sample_b:
        first_member = None
        for branch_payload in (template_payload.get("branches") or {}).values():
            members = (branch_payload or {}).get("members") or []
            if members:
                first_member = members[0]
                break
        if first_member:
            assert float(first_member.get("PI", 0.0) or 0.0) == float(sample_b.get("PI", 0.0) or 0.0)
            assert float(first_member.get("FGR", 0.0) or 0.0) == float(sample_b.get("FGR", 0.0) or 0.0)


def test_chunk_branch_resolve_pending_then_ok() -> None:
    asset = _load_asset()
    dashboard = asset.get("dashboard_payload") or {}
    template_payload = dashboard.get("template_payload") or {}

    branch_index = template_payload.get("branch_index") or []
    if not branch_index:
        return
    branch_key = str((branch_index[0] or {}).get("key") or "")
    if not branch_key:
        return

    pending = resolve_branch_block(dashboard, branch_key, "branch_summary")
    assert pending.get("status") in {"pending_chunk", "ok"}

    loaded = _load_chunk_branch_payload(asset, branch_key)
    if loaded:
        ok = resolve_branch_block(dashboard, branch_key, "branch_summary", branch_payload=loaded)
        assert ok.get("status") == "ok"
        assert isinstance(ok.get("data"), dict)


def test_resolver_fallback_when_block_payload_missing() -> None:
    asset = _load_asset()
    dashboard = asset.get("dashboard_payload") or {}
    template_payload = dict(dashboard.get("template_payload") or {})
    template_payload.pop("block_payload", None)

    payload_without_blocks = {
        "template_payload": template_payload,
    }
    resolved = resolve_block(payload_without_blocks, "official_kpi_6")
    assert resolved.get("status") == "fallback"
    assert float((resolved.get("data") or {}).get("monthly_attainment_rate", 0.0) or 0.0) >= 0.0


def test_resolver_counter_tracks_fallback_and_missing() -> None:
    asset = _load_asset()
    dashboard = asset.get("dashboard_payload") or {}
    template_payload = dict(dashboard.get("template_payload") or {})
    template_payload.pop("block_payload", None)
    payload_without_blocks = {"template_payload": template_payload}

    reset_fallback_counter()
    _ = resolve_block(payload_without_blocks, "official_kpi_6")
    _ = resolve_block(payload_without_blocks, "no_such_block")
    _ = resolve_slot(payload_without_blocks, "unknown_slot")
    _ = resolve_branch_block(payload_without_blocks, "unknown_branch", "branch_summary")
    counter = get_fallback_counter()

    assert int(counter.get("fallback_used", 0)) >= 1
    assert int(counter.get("slot_missing", 0)) >= 1
    assert int(counter.get("block_missing", 0)) >= 1
