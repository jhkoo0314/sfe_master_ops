from __future__ import annotations

from pathlib import Path

import pandas as pd

from result_assets.territory_result_asset import TerritoryResultAsset


def build_territory_builder_payload(
    asset: TerritoryResultAsset,
    crm_activity_path: str | None = None,
) -> dict:
    markers = _territory_markers_to_payload(asset, crm_activity_path=crm_activity_path)
    routes = _territory_routes_to_payload(asset, crm_activity_path=crm_activity_path)
    return {
        "mode": "routing",
        "auto_render": False,
        "markers": markers,
        "routes": routes,
        "overview": {
            "map_title": asset.map_contract.map_title,
            "period_label": asset.map_contract.period_label,
            "total_regions": asset.coverage_summary.total_regions,
            "coverage_rate": asset.coverage_summary.coverage_rate,
            "total_reps": asset.optimization_summary.total_reps,
            "marker_count": len(markers),
            "route_count": len(routes),
        },
    }


def _territory_markers_to_payload(
    asset: TerritoryResultAsset,
    crm_activity_path: str | None = None,
) -> list[dict]:
    if crm_activity_path:
        crm_markers = _build_markers_from_crm(asset, crm_activity_path)
        if crm_markers:
            return crm_markers

    markers: list[dict] = []
    for row in asset.markers:
        insight_parts = [
            f"권역: {row.region_key}",
            f"세부권역: {row.sub_region_key or '-'}",
            f"방문: {int(row.total_visits or 0)}건",
        ]
        if row.attainment_rate is not None:
            insight_parts.append(f"달성률: {round(float(row.attainment_rate) * 100, 1)}%")
        markers.append(
            {
                "hospital_id": row.hospital_id,
                "hospital": (row.hospital_name or row.hospital_id).strip(),
                "rep": row.rep_id or "미지정",
                "lat": float(row.coord.lat),
                "lon": float(row.coord.lng),
                "sales": round(float(row.total_sales or 0.0), 2),
                "target": round(float(row.total_target or 0.0), 2),
                "insight": " | ".join(insight_parts),
                "region": row.region_key,
                "sub_region": row.sub_region_key,
                "month": None,
                "date": None,
            }
        )
    return markers


def _territory_routes_to_payload(
    asset: TerritoryResultAsset,
    crm_activity_path: str | None = None,
) -> list[dict]:
    if crm_activity_path:
        crm_routes = _build_routes_from_crm(crm_activity_path)
        if crm_routes:
            return crm_routes

    routes: list[dict] = []
    period_label = asset.map_contract.period_label or "AUTO"
    for idx, route in enumerate(asset.routes, start=1):
        coords = [
            {
                "seq": int(point.order),
                "hospital": point.hospital_id,
                "lat": float(point.coord.lat),
                "lon": float(point.coord.lng),
            }
            for point in route.route_points
        ]
        if not coords:
            continue
        routes.append(
            {
                "rep": route.rep_name or route.rep_id,
                "month": period_label,
                "date": f"{period_label}-{idx:02d}",
                "coords": coords,
            }
        )
    return routes


def _build_markers_from_crm(asset: TerritoryResultAsset, crm_activity_path: str) -> list[dict]:
    crm_path = Path(crm_activity_path)
    if not crm_path.exists():
        return []

    crm_df = pd.read_excel(crm_path).reset_index(names="input_order")
    if crm_df.empty:
        return []

    crm_df["실행일"] = pd.to_datetime(crm_df["실행일"], errors="coerce")
    crm_df["기관위도"] = pd.to_numeric(crm_df["기관위도"], errors="coerce")
    crm_df["기관경도"] = pd.to_numeric(crm_df["기관경도"], errors="coerce")
    crm_df = crm_df.dropna(subset=["실행일", "영업사원명", "방문기관", "기관위도", "기관경도"]).copy()
    if crm_df.empty:
        return []

    crm_df["month"] = crm_df["실행일"].dt.strftime("%Y-%m")
    crm_df["date"] = crm_df["실행일"].dt.strftime("%Y-%m-%d")

    totals_by_hospital: dict[str, dict[str, object]] = {}
    for marker in asset.markers:
        name_key = str(marker.hospital_name or marker.hospital_id).strip()
        totals_by_hospital[name_key] = {
            "hospital_id": marker.hospital_id,
            "sales": round(float(marker.total_sales or 0.0), 2),
            "target": round(float(marker.total_target or 0.0), 2),
            "region": marker.region_key,
            "sub_region": marker.sub_region_key,
            "attainment_rate": marker.attainment_rate,
            "visits": int(marker.total_visits or 0),
        }

    markers: list[dict] = []
    for row in crm_df.itertuples(index=False):
        hospital_name = str(row.방문기관).strip()
        marker_meta = totals_by_hospital.get(hospital_name, {})
        attainment = marker_meta.get("attainment_rate")
        insight_parts = [
            f"권역: {marker_meta.get('region') or '-'}",
            f"세부권역: {marker_meta.get('sub_region') or '-'}",
        ]
        if attainment is not None:
            insight_parts.append(f"달성률: {round(float(attainment) * 100, 1)}%")
        markers.append(
            {
                "hospital_id": marker_meta.get("hospital_id") or hospital_name,
                "hospital": hospital_name,
                "rep": str(row.영업사원명).strip(),
                "month": str(row.month),
                "date": str(row.date),
                "lat": float(row.기관위도),
                "lon": float(row.기관경도),
                "sales": marker_meta.get("sales", 0.0),
                "target": marker_meta.get("target", 0.0),
                "insight": " | ".join(insight_parts),
                "region": marker_meta.get("region"),
                "sub_region": marker_meta.get("sub_region"),
                "seq": int(getattr(row, "input_order", 0)) + 1,
            }
        )
    return markers


def _build_routes_from_crm(crm_activity_path: str) -> list[dict]:
    crm_path = Path(crm_activity_path)
    if not crm_path.exists():
        return []

    crm_df = pd.read_excel(crm_path).reset_index(names="input_order")
    if crm_df.empty:
        return []

    crm_df["실행일"] = pd.to_datetime(crm_df["실행일"], errors="coerce")
    crm_df["기관위도"] = pd.to_numeric(crm_df["기관위도"], errors="coerce")
    crm_df["기관경도"] = pd.to_numeric(crm_df["기관경도"], errors="coerce")
    crm_df = crm_df.dropna(subset=["실행일", "영업사원명", "방문기관", "기관위도", "기관경도"]).copy()
    if crm_df.empty:
        return []

    crm_df["month"] = crm_df["실행일"].dt.strftime("%Y-%m")
    crm_df["date"] = crm_df["실행일"].dt.strftime("%Y-%m-%d")

    routes: list[dict] = []
    for (rep_name, month, date), group in crm_df.groupby(["영업사원명", "month", "date"], sort=True):
        ordered = group.sort_values("input_order", kind="stable")
        seen_hospitals: set[str] = set()
        coords: list[dict] = []
        seq = 1
        for row in ordered.itertuples(index=False):
            hospital_name = str(row.방문기관).strip()
            if hospital_name in seen_hospitals:
                continue
            seen_hospitals.add(hospital_name)
            coords.append(
                {
                    "seq": seq,
                    "hospital": hospital_name,
                    "lat": float(row.기관위도),
                    "lon": float(row.기관경도),
                }
            )
            seq += 1
        if coords:
            routes.append(
                {
                    "rep": str(rep_name).strip(),
                    "month": str(month),
                    "date": str(date),
                    "coords": coords,
                }
            )
    return routes
