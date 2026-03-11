from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.sandbox.domain_adapter import load_sales_from_records, load_target_from_records
from common.company_profile import get_company_ops_profile
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root

COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
PROFILE = get_company_ops_profile(COMPANY_KEY)
SOURCE_ROOT = get_company_root(ROOT, "company_source", COMPANY_KEY)
OUTPUT_ROOT = get_company_root(ROOT, "ops_standard", COMPANY_KEY) / "sandbox"


def models_to_frame(models: list) -> pd.DataFrame:
    return pd.DataFrame([m.model_dump(mode="json") for m in models])


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    sales_file = PROFILE.source_path(SOURCE_ROOT, "sales")
    target_file = PROFILE.source_path(SOURCE_ROOT, "target")
    account_file = PROFILE.source_path(SOURCE_ROOT, "crm_account_assignment")

    sales_raw = pd.read_excel(sales_file)
    target_raw = pd.read_excel(target_file)
    account_raw = pd.read_excel(account_file)

    hospital_name_to_id = {
        str(row["account_name"]).strip(): str(row["account_id"]).strip()
        for _, row in account_raw.iterrows()
    }

    sales_records, sales_failed = load_sales_from_records(
        sales_raw.to_dict(orient="records"),
        config=PROFILE.sales_adapter_factory(),
        source_label=f"{COMPANY_KEY}_sales_raw",
        hospital_name_to_id=hospital_name_to_id,
    )

    target_records, target_failed = load_target_from_records(
        target_raw.to_dict(orient="records"),
        config=PROFILE.target_adapter_factory(),
        source_label=f"{COMPANY_KEY}_target_raw",
        hospital_name_to_id=hospital_name_to_id,
    )

    sales_df = models_to_frame(sales_records)
    target_df = models_to_frame(target_records)

    sales_df.to_excel(OUTPUT_ROOT / "ops_sales_records.xlsx", index=False)
    target_df.to_excel(OUTPUT_ROOT / "ops_target_records.xlsx", index=False)

    if sales_failed:
        pd.DataFrame(sales_failed).to_excel(OUTPUT_ROOT / "failed_sales_rows.xlsx", index=False)
    if target_failed:
        pd.DataFrame(target_failed).to_excel(OUTPUT_ROOT / "failed_target_rows.xlsx", index=False)

    report = {
        "company": COMPANY_NAME,
        "company_key": COMPANY_KEY,
        "source_root": str(SOURCE_ROOT),
        "output_root": str(OUTPUT_ROOT),
        "sales_source_file": str(sales_file),
        "target_source_file": str(target_file),
        "sales_record_count": len(sales_records),
        "target_record_count": len(target_records),
        "sales_failed_count": len(sales_failed),
        "target_failed_count": len(target_failed),
        "sales_unique_hospitals": len({r.hospital_id for r in sales_records}),
        "target_unique_hospitals": len({r.hospital_id for r in target_records if r.hospital_id}),
        "sales_months": sorted({r.metric_month for r in sales_records}),
        "target_months": sorted({r.metric_month for r in target_records}),
    }
    (OUTPUT_ROOT / "normalization_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Normalized {COMPANY_NAME} sandbox source data:")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
