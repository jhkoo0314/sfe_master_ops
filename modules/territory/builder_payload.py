from __future__ import annotations

import re

from modules.kpi import build_territory_builder_context
from result_assets.territory_result_asset import TerritoryResultAsset

ALL_DATES_KEY = "__ALL__"
CHUNKED_TERRITORY_DATA_MODE = "chunked_rep_month_payloads_v1"


def build_territory_builder_payload(
    asset: TerritoryResultAsset,
    territory_activity_path: str | None = None,
) -> dict:
    context = build_territory_builder_context(
        asset=asset,
        territory_activity_path=territory_activity_path,
    )

    return {
        "mode": "routing",
        "auto_render": False,
        "overview": {
            "map_title": asset.map_contract.map_title,
            "period_label": asset.map_contract.period_label,
            "total_regions": asset.coverage_summary.total_regions,
            "coverage_rate": asset.coverage_summary.coverage_rate,
            "total_reps": asset.optimization_summary.total_reps,
            "territory_hospital_count": len(asset.markers),
            "route_selection_count": context["selection_count"],
            "default_rep_name": "",
        },
        "hospital_catalog": context["marker_meta"],
        "filters": {
            "rep_options": context["rep_options"],
        },
        "default_selection": context["default_selection"],
        "rep_payloads": context["rep_payloads"],
    }


def build_chunked_territory_payload(payload: dict) -> tuple[dict, dict[str, dict]]:
    rep_payloads = payload.get("rep_payloads", {}) or {}
    hospital_catalog = payload.get("hospital_catalog", {}) or {}
    manifest = {
        key: value
        for key, value in payload.items()
        if key not in {"rep_payloads", "hospital_catalog"}
    }
    manifest["data_mode"] = CHUNKED_TERRITORY_DATA_MODE
    manifest["asset_base"] = ""
    manifest["hospital_catalog"] = {}
    manifest["rep_payloads"] = {}
    manifest["rep_index"] = {}

    asset_chunks: dict[str, dict] = {}

    for rep_id, rep_payload in rep_payloads.items():
        rep_hospital_ids = _collect_rep_hospital_ids(rep_payload.get("views", {}))
        rep_index = {
            "rep_id": rep_payload.get("rep_id", rep_id),
            "rep_name": rep_payload.get("rep_name", rep_id),
            "portfolio_summary": rep_payload.get("portfolio_summary", {}),
            "months": rep_payload.get("months", []),
            "dates_by_month": rep_payload.get("dates_by_month", {}),
            "rep_asset": _build_rep_chunk_name(rep_id),
            "month_assets": {},
        }
        asset_chunks[rep_index["rep_asset"]] = {
            "rep_id": rep_id,
            "hospital_catalog": {
                hospital_id: hospital_catalog[hospital_id]
                for hospital_id in rep_hospital_ids
                if hospital_id in hospital_catalog
            },
        }

        all_views = rep_payload.get("views", {}) or {}
        for month in rep_index["months"]:
            month_key = str(month.get("value") or "").strip()
            if not month_key:
                continue
            month_views = {
                view_key: view
                for view_key, view in all_views.items()
                if view_key.startswith(f"{month_key}|")
            }
            chunk_name = _build_month_chunk_name(rep_id, month_key)
            rep_index["month_assets"][month_key] = chunk_name
            asset_chunks[chunk_name] = {
                "rep_id": rep_id,
                "month_key": month_key,
                "views": month_views,
            }

        manifest["rep_index"][rep_id] = rep_index

    return manifest, asset_chunks


def _collect_rep_hospital_ids(views: dict[str, dict]) -> list[str]:
    hospital_ids: set[str] = set()
    for selection in (views or {}).values():
        for point in selection.get("points", []) or []:
            hospital_id = str(point.get("hospital_id") or "").strip()
            if hospital_id:
                hospital_ids.add(hospital_id)
        for group in selection.get("route_groups", []) or []:
            for point in group.get("points", []) or []:
                hospital_id = str(point.get("hospital_id") or "").strip()
                if hospital_id:
                    hospital_ids.add(hospital_id)
    return sorted(hospital_ids)


def _build_rep_chunk_name(rep_id: str) -> str:
    safe_rep_id = re.sub(r"[^A-Za-z0-9_-]+", "_", str(rep_id).strip()) or "rep"
    return f"{safe_rep_id}__catalog.js"


def _build_month_chunk_name(rep_id: str, month_key: str) -> str:
    safe_rep_id = re.sub(r"[^A-Za-z0-9_-]+", "_", str(rep_id).strip()) or "rep"
    safe_month_key = re.sub(r"[^A-Za-z0-9_-]+", "_", str(month_key).strip()) or "month"
    return f"{safe_rep_id}__{safe_month_key}.js"
