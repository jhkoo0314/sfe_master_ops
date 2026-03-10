from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.crm.adapter_config import HospitalAdapterConfig
from adapters.crm.hospital_adapter import load_hospital_master_from_file
from modules.prescription.schemas import CompanyPrescriptionStandard
from modules.prescription.flow_builder import build_hospital_region_index, build_prescription_standard_flow
from modules.prescription.service import build_prescription_result_asset
from ops_core.api.prescription_router import evaluate_prescription_asset


SOURCE_ROOT = ROOT / "data" / "raw" / "company_source" / "hangyeol_pharma"
STANDARD_ROOT = ROOT / "data" / "ops_standard" / "hangyeol_pharma" / "prescription"
OUTPUT_ROOT = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "prescription"


def load_standard_records() -> list[CompanyPrescriptionStandard]:
    df = pd.read_excel(STANDARD_ROOT / "ops_prescription_standard.xlsx")
    records: list[CompanyPrescriptionStandard] = []
    for row in df.to_dict(orient="records"):
        row["record_type"] = str(row["record_type"])
        row["wholesaler_id"] = str(row["wholesaler_id"])
        row["wholesaler_name"] = str(row["wholesaler_name"])
        row["pharmacy_id"] = str(row["pharmacy_id"])
        row["pharmacy_name"] = str(row["pharmacy_name"])
        row["pharmacy_region_key"] = str(row["pharmacy_region_key"])
        row["pharmacy_sub_region_key"] = str(row["pharmacy_sub_region_key"])
        row["product_id"] = str(row["product_id"])
        row["product_name"] = str(row["product_name"])
        row["metric_month"] = str(row["metric_month"])
        if row.get("pharmacy_postal_code") is not None and pd.isna(row["pharmacy_postal_code"]):
            row["pharmacy_postal_code"] = None
        if row.get("ingredient_code") is not None and pd.isna(row["ingredient_code"]):
            row["ingredient_code"] = None
        if row.get("amount") is not None and pd.isna(row["amount"]):
            row["amount"] = None
        if row.get("unit") is not None and pd.isna(row["unit"]):
            row["unit"] = None
        if row.get("hospital_id") is not None and pd.isna(row["hospital_id"]):
            row["hospital_id"] = None
        records.append(CompanyPrescriptionStandard(**row))
    return records


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    hospitals = load_hospital_master_from_file(
        SOURCE_ROOT / "company" / "hangyeol_account_master.xlsx",
        config=HospitalAdapterConfig.hangyeol_account_example(),
    )
    sub_idx, reg_idx = build_hospital_region_index(hospitals)
    standards = load_standard_records()
    flows, gaps = build_prescription_standard_flow(
        standards,
        sub_idx,
        reg_idx,
        prefer_hospital_types=["의원", "종합병원", "상급종합"],
    )
    asset = build_prescription_result_asset(
        flows,
        gaps,
        adapter_failed_count=0,
        total_raw_count=len(standards),
        notes="hangyeol fact_ship source -> adapter normalization -> ops prescription validation",
    )
    evaluation = evaluate_prescription_asset(asset)

    (OUTPUT_ROOT / "prescription_result_asset.json").write_text(
        json.dumps(asset.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "prescription_ops_evaluation.json").write_text(
        json.dumps(evaluation.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "standard_record_count": len(standards),
        "flow_record_count": len(flows),
        "gap_record_count": len(gaps),
        "quality_status": evaluation.quality_status,
        "quality_score": evaluation.quality_score,
        "next_modules": evaluation.next_modules,
        "flow_completion_rate": asset.mapping_quality.flow_completion_rate,
        "connected_hospital_count": asset.lineage_summary.unique_hospitals_connected,
    }
    (OUTPUT_ROOT / "prescription_validation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Validated Hangyeol prescription data with OPS:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
