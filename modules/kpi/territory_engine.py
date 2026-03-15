from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt
from pathlib import Path

import pandas as pd

from result_assets.territory_result_asset import TerritoryResultAsset

ALL_DATES_KEY = "__ALL__"


def build_territory_builder_context(
    asset: TerritoryResultAsset,
    territory_activity_path: str | None = None,
) -> dict:
    marker_meta = _build_marker_meta(asset)
    route_meta = _build_route_meta(asset)
    activity_df = _load_territory_activity_frame(territory_activity_path)
    route_groups = _build_route_groups(asset, activity_df)
    rep_payloads, default_selection, rep_options, selection_count = _build_rep_payloads(
        route_groups=route_groups,
        marker_meta=marker_meta,
        route_meta=route_meta,
    )
    return {
        "marker_meta": marker_meta,
        "route_meta": route_meta,
        "rep_payloads": rep_payloads,
        "default_selection": default_selection,
        "rep_options": rep_options,
        "selection_count": selection_count,
    }


def _build_marker_meta(asset: TerritoryResultAsset) -> dict[str, dict]:
    marker_meta: dict[str, dict] = {}
    for marker in asset.markers:
        insight_parts = [
            f"권역: {marker.region_key}",
            f"세부권역: {marker.sub_region_key or '-'}",
            f"누적 방문: {int(marker.total_visits or 0)}건",
        ]
        if marker.attainment_rate is not None:
            insight_parts.append(f"누적 달성률: {round(float(marker.attainment_rate) * 100, 1)}%")
        marker_meta[marker.hospital_id] = {
            "hospital_id": marker.hospital_id,
            "hospital": (marker.hospital_name or marker.hospital_id).strip(),
            "lat": float(marker.coord.lat),
            "lon": float(marker.coord.lng),
            "sales": round(float(marker.total_sales or 0.0), 2),
            "target": round(float(marker.total_target or 0.0), 2),
            "attainment_rate": (
                round(float(marker.attainment_rate), 4) if marker.attainment_rate is not None else None
            ),
            "visits": int(marker.total_visits or 0),
            "rep_id": marker.rep_id or "",
            "region": marker.region_key,
            "sub_region": marker.sub_region_key,
            "insight": " | ".join(insight_parts),
        }
    return marker_meta


def _build_route_meta(asset: TerritoryResultAsset) -> dict[str, dict]:
    route_meta: dict[str, dict] = {}
    for route in asset.routes:
        route_meta[route.rep_id] = {
            "rep_name": (route.rep_name or route.rep_id).strip(),
            "coverage_score": round(float(route.coverage_score or 0.0), 4),
            "avg_attainment": (
                round(float(route.avg_attainment), 4) if route.avg_attainment is not None else None
            ),
        }
    return route_meta


def _load_territory_activity_frame(territory_activity_path: str | None) -> pd.DataFrame:
    if not territory_activity_path:
        return pd.DataFrame()

    path = Path(territory_activity_path)
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_excel(path)
    if df.empty:
        return df

    required = {
        "hospital_id",
        "hospital_name",
        "rep_id",
        "rep_name",
        "month_key",
        "date_key",
        "latitude",
        "longitude",
        "route_order",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Territory 활동 표준 파일 필수 컬럼 누락: {missing}")

    df = df.copy()
    df["hospital_id"] = df["hospital_id"].astype(str).str.strip()
    df["hospital_name"] = df["hospital_name"].astype(str).str.strip()
    df["rep_id"] = df["rep_id"].astype(str).str.strip()
    df["rep_name"] = df["rep_name"].fillna(df["rep_id"]).astype(str).str.strip()
    df["month_key"] = df["month_key"].astype(str).str.strip()
    df["date_key"] = df["date_key"].astype(str).str.strip()
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["route_order"] = pd.to_numeric(df["route_order"], errors="coerce").fillna(0)
    if "visit_count" in df.columns:
        df["visit_count"] = pd.to_numeric(df["visit_count"], errors="coerce").fillna(1)
    else:
        df["visit_count"] = 1

    return df.dropna(
        subset=["hospital_id", "rep_id", "month_key", "date_key", "latitude", "longitude"]
    ).copy()


def _build_route_groups(asset: TerritoryResultAsset, activity_df: pd.DataFrame) -> list[dict]:
    if not activity_df.empty:
        groups: list[dict] = []
        grouped = activity_df.groupby(["rep_id", "rep_name", "month_key", "date_key"], sort=True)
        for (rep_id, rep_name, month_key, date_key), group in grouped:
            ordered = group.sort_values(["route_order", "hospital_id"], kind="stable")
            seen_hospitals: set[str] = set()
            points: list[dict] = []
            seq = 1
            for row in ordered.itertuples(index=False):
                hospital_id = str(row.hospital_id).strip()
                if hospital_id in seen_hospitals:
                    continue
                seen_hospitals.add(hospital_id)
                points.append(
                    {
                        "seq": seq,
                        "hospital_id": hospital_id,
                        "hospital": str(row.hospital_name).strip(),
                        "lat": float(row.latitude),
                        "lon": float(row.longitude),
                        "visit_count": int(getattr(row, "visit_count", 1) or 1),
                    }
                )
                seq += 1
            if points:
                groups.append(
                    {
                        "rep_id": str(rep_id).strip(),
                        "rep_name": str(rep_name).strip(),
                        "month_key": str(month_key).strip(),
                        "date_key": str(date_key).strip(),
                        "points": points,
                    }
                )
        if groups:
            return groups

    synthetic_groups: list[dict] = []
    period_label = (asset.map_contract.period_label or "AUTO").strip() or "AUTO"
    for idx, route in enumerate(asset.routes, start=1):
        points = [
            {
                "seq": int(point.order) + 1,
                "hospital_id": point.hospital_id,
                "hospital": point.hospital_id,
                "lat": float(point.coord.lat),
                "lon": float(point.coord.lng),
                "visit_count": int(point.visit_count or 0),
            }
            for point in route.route_points
        ]
        if not points:
            continue
        synthetic_groups.append(
            {
                "rep_id": route.rep_id,
                "rep_name": (route.rep_name or route.rep_id).strip(),
                "month_key": period_label,
                "date_key": f"{period_label}-{idx:02d}",
                "points": points,
            }
        )
    return synthetic_groups


def _build_rep_payloads(
    route_groups: list[dict],
    marker_meta: dict[str, dict],
    route_meta: dict[str, dict],
) -> tuple[dict[str, dict], dict[str, str], list[dict], int]:
    rep_groups: dict[str, dict] = {}
    selection_count = 0

    for group in route_groups:
        rep_id = group["rep_id"]
        rep_name = group["rep_name"] or route_meta.get(rep_id, {}).get("rep_name") or rep_id
        month_key = group["month_key"]
        date_key = group["date_key"]
        view_key = f"{month_key}|{date_key}"
        selection = _build_selection_payload(
            rep_id=rep_id,
            rep_name=rep_name,
            month_key=month_key,
            date_key=date_key,
            points=group["points"],
            marker_meta=marker_meta,
            route_meta=route_meta.get(rep_id, {}),
        )

        rep_payload = rep_groups.setdefault(
            rep_id,
            {
                "rep_id": rep_id,
                "rep_name": rep_name,
                "portfolio_summary": _build_portfolio_summary(rep_id, marker_meta, route_meta.get(rep_id, {})),
                "months": [],
                "dates_by_month": {},
                "views": {},
                "_daily_views_by_month": {},
            },
        )
        rep_payload["views"][view_key] = selection
        rep_payload["dates_by_month"].setdefault(month_key, [])
        rep_payload["dates_by_month"][month_key].append(
            {
                "value": date_key,
                "label": date_key,
                "stop_count": selection["summary"]["stop_count"],
            }
        )
        rep_payload["_daily_views_by_month"].setdefault(month_key, []).append(selection)
        selection_count += 1

    rep_options: list[dict] = []
    sorted_rep_ids = sorted(rep_groups, key=lambda rep_id: rep_groups[rep_id]["rep_name"])
    default_selection: dict[str, str] = {}

    for rep_id in sorted_rep_ids:
        rep_payload = rep_groups[rep_id]
        daily_views_by_month = rep_payload.pop("_daily_views_by_month", {})
        months = sorted(rep_payload["dates_by_month"], reverse=True)
        rep_payload["months"] = [
            {
                "value": month_key,
                "label": month_key,
                "day_count": len(rep_payload["dates_by_month"][month_key]),
            }
            for month_key in months
        ]
        for month_key in months:
            day_rows = sorted(
                rep_payload["dates_by_month"][month_key],
                key=lambda row: row["value"],
                reverse=True,
            )
            month_selection = _build_month_selection_payload(
                rep_id=rep_id,
                rep_name=rep_payload["rep_name"],
                month_key=month_key,
                daily_selections=daily_views_by_month.get(month_key, []),
                marker_meta=marker_meta,
                route_meta=route_meta.get(rep_id, {}),
            )
            rep_payload["views"][f"{month_key}|{ALL_DATES_KEY}"] = month_selection
            rep_payload["dates_by_month"][month_key] = [
                {
                    "value": ALL_DATES_KEY,
                    "label": "전체",
                    "day_count": len(day_rows),
                    "stop_count": month_selection["summary"]["selected_hospital_count"],
                }
            ] + day_rows

        portfolio = rep_payload["portfolio_summary"]
        rep_options.append(
            {
                "value": rep_id,
                "label": rep_payload["rep_name"],
                "month_count": len(months),
                "day_count": sum(len(rep_payload["dates_by_month"][month]) - 1 for month in months),
                "hospital_count": portfolio["hospital_count"],
            }
        )

    return rep_groups, default_selection, rep_options, selection_count


def _build_portfolio_summary(rep_id: str, marker_meta: dict[str, dict], route_info: dict) -> dict:
    rep_markers = [row for row in marker_meta.values() if row.get("rep_id") == rep_id]
    total_sales = round(sum(float(row.get("sales") or 0.0) for row in rep_markers), 2)
    total_target = round(sum(float(row.get("target") or 0.0) for row in rep_markers), 2)
    total_visits = int(sum(int(row.get("visits") or 0) for row in rep_markers))
    attainment_rate = round(total_sales / total_target, 4) if total_target > 0 else None
    return {
        "hospital_count": len(rep_markers),
        "total_sales": total_sales,
        "total_target": total_target,
        "total_visits": total_visits,
        "attainment_rate": attainment_rate,
        "coverage_score": round(float(route_info.get("coverage_score") or 0.0), 4),
        "avg_attainment": route_info.get("avg_attainment"),
    }


def _build_selection_payload(
    rep_id: str,
    rep_name: str,
    month_key: str,
    date_key: str,
    points: list[dict],
    marker_meta: dict[str, dict],
    route_meta: dict,
) -> dict:
    enriched_points: list[dict] = []
    selected_hospital_ids: set[str] = set()

    for point in points:
        meta = marker_meta.get(point["hospital_id"], {})
        selected_hospital_ids.add(point["hospital_id"])
        enriched_points.append(
            {
                "seq": int(point["seq"]),
                "hospital_id": point["hospital_id"],
                "hospital": meta.get("hospital") or point["hospital"],
                "lat": float(point["lat"]),
                "lon": float(point["lon"]),
                "visit_count": int(point.get("visit_count") or 1),
                "sales": round(float(meta.get("sales") or 0.0), 2),
                "target": round(float(meta.get("target") or 0.0), 2),
                "region": meta.get("region") or "",
                "sub_region": meta.get("sub_region"),
                "attainment_rate": meta.get("attainment_rate"),
                "insight": meta.get("insight") or "",
                "month_key": month_key,
                "date_key": date_key,
            }
        )

    route_distance_km = round(_calc_route_distance_km(enriched_points), 1)
    radius_km = round(_calc_coverage_radius_km(enriched_points), 1)
    stop_count = len(enriched_points)
    visit_count = int(sum(point["visit_count"] for point in enriched_points))
    km_per_visit = round(route_distance_km / visit_count, 1) if visit_count > 0 else 0.0

    selected_markers = [
        {
            "hospital_id": point["hospital_id"],
            "sales": point["sales"],
            "target": point["target"],
        }
        for point in enriched_points
    ]

    sales_total = round(sum(float(marker.get("sales") or 0.0) for marker in selected_markers), 2)
    target_total = round(sum(float(marker.get("target") or 0.0) for marker in selected_markers), 2)
    attainment_rate = round(sales_total / target_total, 4) if target_total > 0 else None

    summary = {
        "stop_count": stop_count,
        "visit_count": visit_count,
        "distance_km": route_distance_km,
        "radius_km": radius_km,
        "km_per_visit": km_per_visit,
        "sales_total": sales_total,
        "target_total": target_total,
        "attainment_rate": attainment_rate,
        "coverage_score": round(float(route_meta.get("coverage_score") or 0.0), 4),
        "selected_hospital_count": len(selected_hospital_ids),
    }

    return {
        "scope": {
            "rep_id": rep_id,
            "rep_name": rep_name,
            "month_key": month_key,
            "date_key": date_key,
            "date_label": date_key,
            "is_month_aggregate": False,
            "label": f"{rep_name} · {month_key} · {date_key}",
        },
        "summary": summary,
        "points": [
            {
                "seq": point["seq"],
                "hospital_id": point["hospital_id"],
                "visit_count": point["visit_count"],
            }
            for point in enriched_points
        ],
        "insight_text": _build_spatial_insight(summary, rep_name),
        "status_line": (
            f"{rep_name} · {month_key} · {date_key} | "
            f"방문처 {stop_count}곳 | 이동거리 {route_distance_km:.1f}km | "
            f"km/visit {km_per_visit:.1f}"
        ),
    }


def _build_month_selection_payload(
    rep_id: str,
    rep_name: str,
    month_key: str,
    daily_selections: list[dict],
    marker_meta: dict[str, dict],
    route_meta: dict,
) -> dict:
    sorted_daily = sorted(
        daily_selections,
        key=lambda row: row.get("scope", {}).get("date_key", ""),
        reverse=True,
    )
    flattened_points: list[dict] = []
    route_groups: list[dict] = []
    unique_hospital_ids: set[str] = set()
    unique_geo_points: list[dict] = []
    distance_km = 0.0
    visit_count = 0

    for daily in sorted_daily:
        day_scope = daily.get("scope", {})
        day_date_key = str(day_scope.get("date_key") or "").strip()
        day_points = daily.get("points", []) or []
        route_groups.append(
            {
                "date_key": day_date_key,
                "label": day_date_key,
                "points": [
                    {
                        "seq": int(point.get("seq") or 0),
                        "hospital_id": point["hospital_id"],
                        "visit_count": int(point.get("visit_count") or 1),
                    }
                    for point in day_points
                ],
            }
        )

        distance_km += float(daily.get("summary", {}).get("distance_km") or 0.0)
        visit_count += int(daily.get("summary", {}).get("visit_count") or 0)

        for point in day_points:
            hospital_id = point["hospital_id"]
            flattened_points.append({"hospital_id": hospital_id})
            if hospital_id in unique_hospital_ids:
                continue
            meta = marker_meta.get(hospital_id, {})
            unique_hospital_ids.add(hospital_id)
            unique_geo_points.append(
                {
                    "lat": float(meta.get("lat") or 0.0),
                    "lon": float(meta.get("lon") or 0.0),
                }
            )

    sales_total = round(
        sum(float(marker_meta.get(hospital_id, {}).get("sales") or 0.0) for hospital_id in unique_hospital_ids),
        2,
    )
    target_total = round(
        sum(float(marker_meta.get(hospital_id, {}).get("target") or 0.0) for hospital_id in unique_hospital_ids),
        2,
    )
    attainment_rate = round(sales_total / target_total, 4) if target_total > 0 else None
    route_distance_km = round(distance_km, 1)
    radius_km = round(_calc_coverage_radius_km(unique_geo_points), 1)
    stop_count = len(flattened_points)
    km_per_visit = round(route_distance_km / visit_count, 1) if visit_count > 0 else 0.0

    summary = {
        "stop_count": stop_count,
        "visit_count": visit_count,
        "distance_km": route_distance_km,
        "radius_km": radius_km,
        "km_per_visit": km_per_visit,
        "sales_total": sales_total,
        "target_total": target_total,
        "attainment_rate": attainment_rate,
        "coverage_score": round(float(route_meta.get("coverage_score") or 0.0), 4),
        "selected_hospital_count": len(unique_hospital_ids),
    }

    return {
        "scope": {
            "rep_id": rep_id,
            "rep_name": rep_name,
            "month_key": month_key,
            "date_key": ALL_DATES_KEY,
            "date_label": "월 전체",
            "is_month_aggregate": True,
            "label": f"{rep_name} · {month_key} · 월 전체",
        },
        "summary": summary,
        "route_groups": route_groups,
        "insight_text": _build_spatial_insight(summary, rep_name),
        "status_line": (
            f"{rep_name} · {month_key} · 월 전체 | "
            f"일자 {len(sorted_daily)}일 | 방문 스톱 {stop_count}건 | "
            f"고유 병원 {len(unique_hospital_ids)}곳 | 이동거리 {route_distance_km:.1f}km"
        ),
    }


def _build_spatial_insight(summary: dict, rep_name: str) -> str:
    efficiency = float(summary.get("km_per_visit") or 0.0)
    radius = float(summary.get("radius_km") or 0.0)
    stop_count = int(summary.get("stop_count") or 0)
    attainment_rate = summary.get("attainment_rate")

    if efficiency >= 30:
        base = f"{rep_name} 담당 동선은 방문당 이동거리가 길어 이동 손실이 큽니다."
    elif efficiency <= 10:
        base = f"{rep_name} 담당 동선은 방문 밀도가 높아 이동 효율이 좋습니다."
    else:
        base = f"{rep_name} 담당 동선은 보통 수준의 이동 효율을 보입니다."

    radius_note = (
        "권역 반경이 넓어 하루 이동 피로가 커질 수 있습니다."
        if radius >= 150
        else "권역 반경은 과도하게 넓지 않습니다."
    )

    attainment_note = ""
    if attainment_rate is not None:
        percent = round(float(attainment_rate) * 100, 1)
        attainment_note = f" 선택된 방문처 누적 달성률은 {percent:.1f}%입니다."

    return f"{base} 선택된 동선 기준 방문 스톱은 {stop_count}건이며, {radius_note}{attainment_note}"


def _calc_route_distance_km(points: list[dict]) -> float:
    if len(points) < 2:
        return 0.0

    total = 0.0
    for prev_point, current_point in zip(points, points[1:]):
        total += _haversine_km(
            prev_point["lat"],
            prev_point["lon"],
            current_point["lat"],
            current_point["lon"],
        )
    return total


def _calc_coverage_radius_km(points: list[dict]) -> float:
    if len(points) < 2:
        return 0.0

    max_distance = 0.0
    for index, point in enumerate(points):
        for other_point in points[index + 1:]:
            max_distance = max(
                max_distance,
                _haversine_km(point["lat"], point["lon"], other_point["lat"], other_point["lon"]),
            )
    return max_distance / 2.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius * c
