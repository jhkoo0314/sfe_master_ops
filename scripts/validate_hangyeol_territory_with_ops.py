from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.territory.schemas import GeoCoord
from modules.territory.service import build_territory_result_asset
from ops_core.api.territory_router import evaluate_territory_asset
from modules.sandbox.schemas import HospitalAnalysisRecord


SANDBOX_VALIDATION_ROOT = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "sandbox"
SOURCE_ROOT = ROOT / "data" / "raw" / "company_source" / "hangyeol_pharma"
OUTPUT_ROOT = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "territory"


def load_hospital_records() -> list[HospitalAnalysisRecord]:
    payload = json.loads((SANDBOX_VALIDATION_ROOT / "sandbox_result_asset.json").read_text(encoding="utf-8"))
    return [HospitalAnalysisRecord(**row) for row in payload["hospital_records"]]


def build_hospital_maps() -> tuple[dict[str, str], dict[str, GeoCoord], dict[str, str], dict[str, str], dict[str, str]]:
    account_df = pd.read_excel(SOURCE_ROOT / "company" / "hangyeol_account_master.xlsx")
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

    (OUTPUT_ROOT / "territory_result_asset.json").write_text(
        json.dumps(asset.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
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
    }
    (OUTPUT_ROOT / "territory_validation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Validated Hangyeol territory data with OPS:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
