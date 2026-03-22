from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.company_profile import get_company_ops_profile
from common.asset_versions import (
    TERRITORY_BUILDER_PAYLOAD_VERSION,
    attach_builder_payload_version,
)
from modules.territory.schemas import GeoCoord
from modules.territory.builder_payload import build_chunked_territory_payload
from modules.territory.service import build_territory_builder_payload, build_territory_result_asset
from modules.validation.api.territory_router import evaluate_territory_asset
from modules.sandbox.schemas import HospitalAnalysisRecord
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root

COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
PROFILE = get_company_ops_profile(COMPANY_KEY)
SANDBOX_VALIDATION_ROOT = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "sandbox"
TERRITORY_STANDARD_ROOT = get_company_root(ROOT, "ops_standard", COMPANY_KEY) / "territory"
SOURCE_ROOT = get_company_root(ROOT, "company_source", COMPANY_KEY)
OUTPUT_ROOT = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "territory"
TERRITORY_ACTIVITY_PATH = TERRITORY_STANDARD_ROOT / "ops_territory_activity.xlsx"


def load_hospital_records() -> list[HospitalAnalysisRecord]:
    payload = json.loads((SANDBOX_VALIDATION_ROOT / "sandbox_result_asset.json").read_text(encoding="utf-8"))
    return [HospitalAnalysisRecord(**row) for row in payload["hospital_records"]]


def build_hospital_maps() -> tuple[dict[str, str], dict[str, GeoCoord], dict[str, str], dict[str, str], dict[str, str]]:
    account_df = pd.read_excel(PROFILE.source_path(SOURCE_ROOT, "crm_account_assignment"))
    region_map = {str(r.account_id): str(r.region_key) for r in account_df.itertuples(index=False)}
    coord_map = {
        str(r.account_id): GeoCoord(
            lat=float(r.latitude),
            lng=float(r.longitude),
            source="exact",
        )
        for r in account_df.itertuples(index=False)
    }
    name_map = {str(r.account_id): str(r.account_name) for r in account_df.itertuples(index=False)}
    sub_region_map = {str(r.account_id): str(r.sub_region_key) for r in account_df.itertuples(index=False)}
    rep_map = {str(r.account_id): str(r.rep_id) for r in account_df.itertuples(index=False)}
    return region_map, coord_map, name_map, sub_region_map, rep_map


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    chunk_root = OUTPUT_ROOT / "territory_builder_payload_assets"
    chunk_root.mkdir(parents=True, exist_ok=True)

    hospital_records = load_hospital_records()
    region_map, coord_map, name_map, sub_region_map, rep_map = build_hospital_maps()

    asset = build_territory_result_asset(
        hospital_records=hospital_records,
        hospital_region_map=region_map,
        hospital_coord_map=coord_map,
        hospital_name_map=name_map,
        hospital_sub_region_map=sub_region_map,
        hospital_rep_map=rep_map,
    )
    evaluation = evaluate_territory_asset(asset)
    full_builder_payload = build_territory_builder_payload(
        asset,
        territory_activity_path=str(TERRITORY_ACTIVITY_PATH),
    )
    builder_payload, asset_chunks = build_chunked_territory_payload(full_builder_payload)
    builder_payload = attach_builder_payload_version(
        builder_payload,
        payload_version=TERRITORY_BUILDER_PAYLOAD_VERSION,
        source_asset_schema_version=asset.schema_version,
    )

    (OUTPUT_ROOT / "territory_result_asset.json").write_text(
        json.dumps(asset.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "territory_builder_payload.json").write_text(
        json.dumps(builder_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for existing in chunk_root.glob("*.js"):
        existing.unlink()
    for chunk_name, chunk_payload in asset_chunks.items():
        if "views" in chunk_payload:
            chunk_key = f"{chunk_payload.get('rep_id', '')}|{chunk_payload.get('month_key', '')}"
            chunk_script = (
                "window.__TERRITORY_MONTH_DATA__ = window.__TERRITORY_MONTH_DATA__ || {};\n"
                f"window.__TERRITORY_MONTH_DATA__[{json.dumps(chunk_key, ensure_ascii=False)}] = "
                f"{json.dumps(chunk_payload, ensure_ascii=False)};\n"
            )
        else:
            chunk_key = str(chunk_payload.get("rep_id", "")).strip()
            chunk_script = (
                "window.__TERRITORY_REP_DATA__ = window.__TERRITORY_REP_DATA__ || {};\n"
                f"window.__TERRITORY_REP_DATA__[{json.dumps(chunk_key, ensure_ascii=False)}] = "
                f"{json.dumps(chunk_payload, ensure_ascii=False)};\n"
            )
        (chunk_root / chunk_name).write_text(chunk_script, encoding="utf-8")
    (OUTPUT_ROOT / "territory_ops_evaluation.json").write_text(
        json.dumps(evaluation.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "marker_count": len(asset.markers),
        "route_count": len(asset.routes),
        "region_zone_count": len(asset.region_zones),
        "gap_count": len(asset.gaps),
        "quality_status": evaluation.quality_status,
        "quality_score": evaluation.quality_score,
        "next_modules": evaluation.next_modules,
        "coverage_rate": asset.coverage_summary.coverage_rate,
        "territory_activity_standard_exists": TERRITORY_ACTIVITY_PATH.exists(),
        "rep_filter_count": len(builder_payload.get("filters", {}).get("rep_options", [])),
    }
    (OUTPUT_ROOT / "territory_validation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Validated {COMPANY_NAME} territory data with OPS:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
