from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


TEMPLATE_PATH = ROOT / "templates" / "Spatial_Preview_260224.html"
CRM_RAW_PATH = ROOT / "data" / "raw" / "company_source" / "hangyeol_pharma" / "crm" / "hangyeol_crm_activity_raw.xlsx"
TERRITORY_ASSET_PATH = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "territory" / "territory_result_asset.json"
SANDBOX_ASSET_PATH = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "sandbox" / "sandbox_result_asset.json"
OUTPUT_ROOT = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "territory"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_sales_target_map() -> dict[tuple[str, str], dict[str, float]]:
    sandbox_asset = load_json(SANDBOX_ASSET_PATH)
    month_map: dict[tuple[str, str], dict[str, float]] = {}
    total_map: dict[str, dict[str, float]] = {}

    for row in sandbox_asset["hospital_records"]:
        hospital_id = str(row["hospital_id"])
        month = f"{str(row['metric_month'])[:4]}-{str(row['metric_month'])[4:6]}"
        month_map[(hospital_id, month)] = {
            "sales": float(row.get("total_sales") or 0.0),
            "target": float(row.get("total_target") or 0.0),
        }
        if hospital_id not in total_map:
            total_map[hospital_id] = {"sales": 0.0, "target": 0.0}
        total_map[hospital_id]["sales"] += float(row.get("total_sales") or 0.0)
        total_map[hospital_id]["target"] += float(row.get("total_target") or 0.0)

    return {"month_map": month_map, "total_map": total_map}


def build_rep_name_map(crm_df: pd.DataFrame) -> dict[str, str]:
    pairs = (
        crm_df[["영업사원코드", "영업사원명"]]
        .dropna()
        .drop_duplicates()
        .itertuples(index=False)
    )
    return {str(code): str(name) for code, name in pairs}


def build_markers() -> list[dict]:
    territory_asset = load_json(TERRITORY_ASSET_PATH)
    crm_df = pd.read_excel(CRM_RAW_PATH)
    rep_name_map = build_rep_name_map(crm_df)
    sales_maps = build_sales_target_map()
    total_map = sales_maps["total_map"]

    markers: list[dict] = []
    for row in territory_asset["markers"]:
        hospital_id = str(row["hospital_id"])
        totals = total_map.get(hospital_id, {"sales": 0.0, "target": 0.0})
        attainment = row.get("attainment_rate")
        insight_parts = [
            f"권역: {row.get('region_key')}",
            f"세부권역: {row.get('sub_region_key') or '-'}",
            f"방문: {int(row.get('total_visits') or 0)}건",
        ]
        if attainment is not None:
            insight_parts.append(f"달성률: {round(float(attainment) * 100, 1)}%")
        markers.append(
            {
                "hospital_id": hospital_id,
                "hospital": str(row.get("hospital_name") or hospital_id).strip(),
                "rep": rep_name_map.get(str(row.get("rep_id") or ""), str(row.get("rep_id") or "")),
                "lat": float(row["coord"]["lat"]),
                "lon": float(row["coord"]["lng"]),
                "sales": round(float(totals["sales"]), 2),
                "target": round(float(totals["target"]), 2),
                "insight": " | ".join(insight_parts),
                "region": row.get("region_key"),
                "sub_region": row.get("sub_region_key"),
            }
        )
    return markers


def build_routes() -> list[dict]:
    crm_df = pd.read_excel(CRM_RAW_PATH).reset_index(names="input_order")
    crm_df["실행일"] = pd.to_datetime(crm_df["실행일"], errors="coerce")
    crm_df = crm_df.dropna(subset=["실행일", "영업사원명", "방문기관", "기관위도", "기관경도"]).copy()
    crm_df["month"] = crm_df["실행일"].dt.strftime("%Y-%m")
    crm_df["date"] = crm_df["실행일"].dt.strftime("%Y-%m-%d")
    crm_df["기관위도"] = pd.to_numeric(crm_df["기관위도"], errors="coerce")
    crm_df["기관경도"] = pd.to_numeric(crm_df["기관경도"], errors="coerce")
    crm_df = crm_df.dropna(subset=["기관위도", "기관경도"]).copy()

    routes: list[dict] = []
    group_cols = ["영업사원명", "month", "date"]
    for (rep_name, month, date), group in crm_df.groupby(group_cols, sort=True):
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
        if not coords:
            continue
        routes.append(
            {
                "rep": str(rep_name),
                "month": str(month),
                "date": str(date),
                "coords": coords,
            }
        )
    return routes


def render_html(template_text: str, markers: list[dict], routes: list[dict]) -> str:
    rendered = template_text
    replacements = [
        (
            r'window\.__INITIAL_MODE__ = "[^"]*";',
            'window.__INITIAL_MODE__ = "hospital";',
        ),
        (
            r"window\.__INITIAL_MARKERS__ = [\s\S]*?;",
            f"window.__INITIAL_MARKERS__ = {json.dumps(markers, ensure_ascii=False)};",
        ),
        (
            r"window\.__INITIAL_ROUTES__ = [\s\S]*?;",
            f"window.__INITIAL_ROUTES__ = {json.dumps(routes, ensure_ascii=False)};",
        ),
    ]
    import re

    for pattern, replacement in replacements:
        rendered = re.sub(pattern, replacement, rendered, count=1)
    return rendered


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    markers = build_markers()
    routes = build_routes()
    rendered_html = render_html(template_text, markers, routes)

    output_html_path = OUTPUT_ROOT / "territory_map_preview.html"
    output_payload_path = OUTPUT_ROOT / "territory_template_payload.json"
    summary_path = OUTPUT_ROOT / "territory_template_validation_summary.json"

    output_html_path.write_text(rendered_html, encoding="utf-8")
    output_payload_path.write_text(
        json.dumps(
            {
                "mode": "hospital",
                "markers": markers,
                "routes": routes,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    route_reps = sorted({route["rep"] for route in routes})
    route_months = sorted({route["month"] for route in routes})
    route_dates = sorted({route["date"] for route in routes})
    territory_asset = load_json(TERRITORY_ASSET_PATH)
    summary = {
        "template_file": str(TEMPLATE_PATH),
        "output_html": str(output_html_path),
        "region_count": len(territory_asset.get("region_zones", [])),
        "marker_count": len(markers),
        "route_count": len(routes),
        "rep_filter_count": len(route_reps),
        "month_filter_count": len(route_months),
        "date_filter_count": len(route_dates),
        "sample_rep": route_reps[0] if route_reps else None,
        "sample_month": route_months[0] if route_months else None,
        "sample_date": route_dates[0] if route_dates else None,
        "has_target_in_markers": any(marker.get("target") is not None for marker in markers),
        "initial_mode": "hospital",
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Rendered Hangyeol territory template:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
