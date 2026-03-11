from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.prescription.company_prescription_adapter import load_prescription_from_file
from common.company_profile import get_company_ops_profile
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root

COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
PROFILE = get_company_ops_profile(COMPANY_KEY)
SOURCE_ROOT = get_company_root(ROOT, "company_source", COMPANY_KEY)
OUTPUT_ROOT = get_company_root(ROOT, "ops_standard", COMPANY_KEY) / "prescription"


def models_to_frame(models: list) -> pd.DataFrame:
    return pd.DataFrame([m.model_dump(mode="json") for m in models])


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    source_file = PROFILE.source_path(SOURCE_ROOT, "prescription")
    standards, failed = load_prescription_from_file(
        source_file,
        config=PROFILE.prescription_adapter_factory(),
    )

    standard_df = models_to_frame(standards)
    standard_df.to_excel(OUTPUT_ROOT / "ops_prescription_standard.xlsx", index=False)

    if failed:
        pd.DataFrame(failed).to_excel(OUTPUT_ROOT / "failed_prescription_rows.xlsx", index=False)

    report = {
        "company": COMPANY_NAME,
        "company_key": COMPANY_KEY,
        "source_root": str(SOURCE_ROOT),
        "output_root": str(OUTPUT_ROOT),
        "source_file": str(source_file),
        "standard_record_count": len(standards),
        "failed_record_count": len(failed),
        "unique_wholesalers": len({r.wholesaler_id for r in standards}),
        "unique_pharmacies": len({r.pharmacy_id for r in standards}),
        "unique_products": len({r.product_id for r in standards}),
        "metric_months": sorted({r.metric_month for r in standards}),
    }
    (OUTPUT_ROOT / "normalization_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Normalized {COMPANY_NAME} prescription source data:")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
