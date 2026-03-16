from __future__ import annotations

from typing import Any, Mapping

from modules.sandbox.block_registry import get_block_spec


SLOT_BLOCK_PRIORITY: dict[str, tuple[str, ...]] = {
    "header_kpi_slot": ("official_kpi_6", "total_summary", "data_health"),
    "main_trend_slot": ("total_trend", "total_summary", "branch_summary"),
    "group_summary_slot": ("total_summary",),
    "data_health_slot": ("data_health", "missing_data"),
}


def resolve_block(
    payload: Mapping[str, Any],
    block_id: str,
    *,
    branch_key: str | None = None,
    branch_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Resolve block data by block_id with graceful fallback.

    payload may be either:
    - dashboard_payload (has template_payload/block_payload)
    - template_payload (flat db payload used by current template)
    """
    template_payload = _to_template_payload(payload)
    block_payload = _to_block_payload(payload, template_payload)

    if block_id in block_payload:
        data = block_payload.get(block_id)
        if isinstance(data, Mapping):
            return {"status": "ok", "block_id": block_id, "data": dict(data)}
        return {"status": "ok", "block_id": block_id, "data": data}

    fallback = _resolve_block_fallback(
        template_payload=template_payload,
        block_id=block_id,
        branch_key=branch_key,
        branch_payload=branch_payload,
    )
    if fallback is not None:
        return {"status": "fallback", "block_id": block_id, "data": fallback}

    return {
        "status": "missing",
        "block_id": block_id,
        "data": {},
        "message": f"block '{block_id}' is not available",
    }


def resolve_slot(
    payload: Mapping[str, Any],
    slot_id: str,
    *,
    branch_key: str | None = None,
    branch_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    priorities = SLOT_BLOCK_PRIORITY.get(slot_id, ())
    if not priorities:
        return {
            "status": "missing",
            "slot_id": slot_id,
            "block_id": None,
            "data": {},
            "message": f"slot '{slot_id}' has no block priorities",
        }

    for block_id in priorities:
        resolved = resolve_block(
            payload,
            block_id,
            branch_key=branch_key,
            branch_payload=branch_payload,
        )
        if resolved.get("status") != "missing":
            return {
                "status": resolved.get("status"),
                "slot_id": slot_id,
                "block_id": block_id,
                "data": resolved.get("data", {}),
            }

    return {
        "status": "missing",
        "slot_id": slot_id,
        "block_id": None,
        "data": {},
        "message": f"slot '{slot_id}' failed to resolve all blocks",
    }


def resolve_branch_block_detail(
    payload: Mapping[str, Any],
    branch_key: str,
    *,
    branch_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Resolve branch-scoped data for chunk mode.
    - If branch is inline in template_payload, return directly.
    - If branch requires lazy-load, return pending_chunk metadata.
    - If branch_payload is passed (already loaded), return it.
    """
    template_payload = _to_template_payload(payload)
    branches = template_payload.get("branches", {})
    if isinstance(branches, Mapping) and isinstance(branches.get(branch_key), Mapping):
        return {"status": "ok", "branch_key": branch_key, "data": dict(branches[branch_key])}

    if isinstance(branch_payload, Mapping):
        return {"status": "ok", "branch_key": branch_key, "data": dict(branch_payload)}

    branch_manifest = template_payload.get("branch_asset_manifest", {})
    if isinstance(branch_manifest, Mapping) and branch_key in branch_manifest:
        return {
            "status": "pending_chunk",
            "branch_key": branch_key,
            "chunk_file": str(branch_manifest.get(branch_key) or ""),
            "asset_base": str(template_payload.get("asset_base") or ""),
        }

    return {
        "status": "missing",
        "branch_key": branch_key,
        "data": {},
        "message": "branch detail not found",
    }


def _to_template_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    template_payload = payload.get("template_payload")
    if isinstance(template_payload, Mapping):
        return dict(template_payload)
    return dict(payload)


def _to_block_payload(payload: Mapping[str, Any], template_payload: Mapping[str, Any]) -> dict[str, Any]:
    block_payload = payload.get("block_payload")
    if isinstance(block_payload, Mapping):
        return dict(block_payload)
    nested_block_payload = template_payload.get("block_payload")
    if isinstance(nested_block_payload, Mapping):
        return dict(nested_block_payload)
    return {}


def _resolve_block_fallback(
    *,
    template_payload: Mapping[str, Any],
    block_id: str,
    branch_key: str | None,
    branch_payload: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    spec = get_block_spec(block_id)
    if spec is None:
        return None

    if block_id == "official_kpi_6":
        return dict(template_payload.get("official_kpi_6", {}) or {})
    if block_id == "total_summary":
        return dict(template_payload.get("total", {}) or {})
    if block_id == "total_trend":
        total = dict(template_payload.get("total", {}) or {})
        return {
            "monthly_actual": list(total.get("monthly_actual", []) or []),
            "monthly_target": list(total.get("monthly_target", []) or []),
            "layer1": dict(total.get("layer1", {}) or {}),
        }
    if block_id == "data_health":
        return dict(template_payload.get("data_health", {}) or {})
    if block_id == "missing_data":
        return {
            "rows": list(template_payload.get("missing_data", []) or []),
            "count": len(list(template_payload.get("missing_data", []) or [])),
        }
    if block_id == "executive_insight":
        return {
            "messages": list(template_payload.get("insight_messages", []) or []),
        }
    if block_id == "template_runtime_manifest":
        return {
            "data_mode": str(template_payload.get("data_mode", "") or ""),
            "asset_base": str(template_payload.get("asset_base", "") or ""),
            "branch_asset_manifest": dict(template_payload.get("branch_asset_manifest", {}) or {}),
            "branch_index": list(template_payload.get("branch_index", []) or []),
            "branch_asset_counts": dict(template_payload.get("branch_asset_counts", {}) or {}),
        }
    if block_id in {"branch_summary", "branch_member_summary", "member_performance"}:
        if not branch_key:
            return {
                "mode": "chunked" if bool(template_payload.get("branch_asset_manifest")) else "inline",
                "branch_index": list(template_payload.get("branch_index", []) or []),
                "source_ref": "template_payload.branches",
            }
        return resolve_branch_block_detail(
            template_payload,
            branch_key,
            branch_payload=branch_payload,
        )
    if block_id == "product_analysis":
        return {
            "products": list(template_payload.get("products", []) or []),
            "total_prod_analysis": dict(template_payload.get("total_prod_analysis", {}) or {}),
        }
    if block_id == "activity_analysis":
        total = dict(template_payload.get("total", {}) or {})
        return dict(total.get("analysis", {}) or {})
    return None
