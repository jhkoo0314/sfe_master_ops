from __future__ import annotations


def _build_official_kpi_6_block(template_payload: dict) -> dict:
    return {
        "metrics": dict(template_payload.get("official_kpi_6", {}) or {}),
    }


def _build_total_summary_block(template_payload: dict) -> dict:
    total = dict(template_payload.get("total", {}) or {})
    return {
        "achieve": float(total.get("achieve", 0.0) or 0.0),
        "avg": dict(total.get("avg", {}) or {}),
        "analysis": dict(total.get("analysis", {}) or {}),
        "layer1": dict(total.get("layer1", {}) or {}),
    }


def _build_total_trend_block(template_payload: dict) -> dict:
    total = dict(template_payload.get("total", {}) or {})
    return {
        "monthly_actual": list(total.get("monthly_actual", []) or []),
        "monthly_target": list(total.get("monthly_target", []) or []),
        "layer1": dict(total.get("layer1", {}) or {}),
    }


def _build_data_health_block(template_payload: dict) -> dict:
    return dict(template_payload.get("data_health", {}) or {})


def _build_branch_summary_block(template_payload: dict) -> dict:
    branch_index = list(template_payload.get("branch_index", []) or [])
    branch_manifest = dict(template_payload.get("branch_asset_manifest", {}) or {})
    branches = dict(template_payload.get("branches", {}) or {})
    if branch_index:
        branch_keys = [str(item.get("key") or item.get("label") or "") for item in branch_index if isinstance(item, dict)]
    else:
        branch_keys = list(branches.keys())
    return {
        "mode": "chunked" if bool(branch_manifest) else "inline",
        "branch_keys": [key for key in branch_keys if key],
        "branch_count": int((template_payload.get("branch_asset_counts", {}) or {}).get("branch_count", len(branches)) or 0),
        "branches": branches if not bool(branch_manifest) else {},
        "source_ref": "template_payload.branches",
    }


def _build_branch_member_summary_block(template_payload: dict) -> dict:
    branch_manifest = dict(template_payload.get("branch_asset_manifest", {}) or {})
    branch_index = list(template_payload.get("branch_index", []) or [])
    branches = dict(template_payload.get("branches", {}) or {})
    members_by_branch: dict[str, list[dict]] = {}
    if not branch_manifest:
        for branch_name, branch_payload in branches.items():
            if isinstance(branch_payload, dict):
                members = list(branch_payload.get("members", []) or [])
                members_by_branch[str(branch_name)] = members
    return {
        "mode": "chunked" if bool(branch_manifest) else "inline",
        "branch_index": branch_index,
        "members_by_branch": members_by_branch,
        "source_ref": "template_payload.branches.*.members",
    }


def _build_member_performance_block(template_payload: dict) -> dict:
    branches = dict(template_payload.get("branches", {}) or {})
    sample_member: dict = {}
    for branch_payload in branches.values():
        if isinstance(branch_payload, dict):
            members = list(branch_payload.get("members", []) or [])
            if members:
                sample_member = dict(members[0])
                break
    return {
        "kpi_keys": ["HIR", "RTR", "BCR", "PHR", "PI", "FGR", "efficiency", "sustainability", "gini"],
        "total_avg": dict((template_payload.get("total", {}) or {}).get("avg", {}) or {}),
        "sample_member": sample_member,
        "source_ref": "template_payload.branches.*.members",
    }


def _build_product_analysis_block(template_payload: dict) -> dict:
    products = list(template_payload.get("products", []) or [])
    total_prod = dict(template_payload.get("total_prod_analysis", {}) or {})
    return {
        "products": products,
        "product_count": len(products),
        "total_product_keys": sorted(total_prod.keys()),
        "total_prod_analysis": total_prod,
        "source_ref": "template_payload.total_prod_analysis",
    }


def _build_activity_analysis_block(template_payload: dict) -> dict:
    total = dict(template_payload.get("total", {}) or {})
    analysis = dict(total.get("analysis", {}) or {})
    return {
        "importance": dict(analysis.get("importance", {}) or {}),
        "correlation": dict(analysis.get("correlation", {}) or {}),
        "adj_correlation": dict(analysis.get("adj_correlation", {}) or {}),
        "ccf": list(analysis.get("ccf", []) or []),
        "importance_keys": sorted((analysis.get("importance", {}) or {}).keys()),
        "matrix_keys": sorted((analysis.get("correlation", {}) or {}).keys()),
        "source_ref": "template_payload.total.analysis",
    }


def _build_missing_data_block(template_payload: dict) -> dict:
    rows = list(template_payload.get("missing_data", []) or [])
    return {
        "rows": rows,
        "count": len(rows),
    }


def _build_executive_insight_block(insight_messages: list[str]) -> dict:
    return {
        "messages": list(insight_messages or []),
        "count": len(insight_messages or []),
    }


def _build_template_runtime_manifest_block(template_payload: dict) -> dict:
    return {
        "data_mode": str(template_payload.get("data_mode", "") or ""),
        "asset_base": str(template_payload.get("asset_base", "") or ""),
        "branch_asset_manifest": dict(template_payload.get("branch_asset_manifest", {}) or {}),
        "branch_index": list(template_payload.get("branch_index", []) or []),
        "branch_asset_counts": dict(template_payload.get("branch_asset_counts", {}) or {}),
    }


def build_dashboard_block_payload(template_payload: dict, insight_messages: list[str]) -> dict:
    return {
        "official_kpi_6": _build_official_kpi_6_block(template_payload),
        "total_summary": _build_total_summary_block(template_payload),
        "total_trend": _build_total_trend_block(template_payload),
        "branch_summary": _build_branch_summary_block(template_payload),
        "branch_member_summary": _build_branch_member_summary_block(template_payload),
        "member_performance": _build_member_performance_block(template_payload),
        "product_analysis": _build_product_analysis_block(template_payload),
        "activity_analysis": _build_activity_analysis_block(template_payload),
        "data_health": _build_data_health_block(template_payload),
        "missing_data": _build_missing_data_block(template_payload),
        "executive_insight": _build_executive_insight_block(insight_messages),
        "template_runtime_manifest": _build_template_runtime_manifest_block(template_payload),
    }
