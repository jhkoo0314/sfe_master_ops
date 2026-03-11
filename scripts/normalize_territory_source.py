from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.territory import load_territory_activity_from_file
from common.company_profile import get_company_ops_profile
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root

COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
PROFILE = get_company_ops_profile(COMPANY_KEY)
CRM_STANDARD_ROOT = get_company_root(ROOT, "ops_standard", COMPANY_KEY) / "crm"
SOURCE_ROOT = get_company_root(ROOT, "company_source", COMPANY_KEY)
OUTPUT_ROOT = get_company_root(ROOT, "ops_standard", COMPANY_KEY) / "territory"


def models_to_frame(models: list) -> pd.DataFrame:
    return pd.DataFrame([m.model_dump(mode="json") for m in models])


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    crm_standard_file = CRM_STANDARD_ROOT / "ops_crm_activity.xlsx"
    account_master_file = PROFILE.source_path(SOURCE_ROOT, "crm_account_assignment")

    territory_rows, unmapped = load_territory_activity_from_file(
        crm_standard_file,
        account_master_file,
        config=PROFILE.territory_activity_adapter_factory(),
    )

    territory_df = models_to_frame(territory_rows)
    territory_df.to_excel(OUTPUT_ROOT / "ops_territory_activity.xlsx", index=False)

    if unmapped:
        pd.DataFrame(unmapped).to_excel(OUTPUT_ROOT / "unmapped_territory_activity.xlsx", index=False)

    report = {
        "company": COMPANY_NAME,
        "company_key": COMPANY_KEY,
        "crm_standard_file": str(crm_standard_file),
        "account_master_file": str(account_master_file),
        "output_root": str(OUTPUT_ROOT),
        "territory_activity_count": len(territory_rows),
        "territory_unmapped_count": len(unmapped),
        "rep_count": int(territory_df["rep_id"].nunique()) if not territory_df.empty else 0,
        "date_count": int(territory_df["date_key"].nunique()) if not territory_df.empty else 0,
    }
    (OUTPUT_ROOT / "normalization_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Normalized {COMPANY_NAME} Territory source data:")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
