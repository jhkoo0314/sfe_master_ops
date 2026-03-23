from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.crm.hospital_adapter import load_hospital_master_from_file, build_hospital_index
from adapters.crm.company_master_adapter import load_company_master_from_file, validate_key_integrity
from adapters.crm.crm_activity_adapter import load_crm_activity_from_file
from common.company_profile import get_company_ops_profile
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root

COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
PROFILE = get_company_ops_profile(COMPANY_KEY)
SOURCE_ROOT = get_company_root(ROOT, "company_source", COMPANY_KEY)
OUTPUT_ROOT = get_company_root(ROOT, "ops_standard", COMPANY_KEY) / "crm"


def _refresh_runtime_context() -> None:
    global COMPANY_KEY, COMPANY_NAME, PROFILE, SOURCE_ROOT, OUTPUT_ROOT
    COMPANY_KEY = get_active_company_key()
    COMPANY_NAME = get_active_company_name(COMPANY_KEY)
    PROFILE = get_company_ops_profile(COMPANY_KEY)
    SOURCE_ROOT = get_company_root(ROOT, "company_source", COMPANY_KEY)
    OUTPUT_ROOT = get_company_root(ROOT, "ops_standard", COMPANY_KEY) / "crm"


def models_to_frame(models: list) -> pd.DataFrame:
    return pd.DataFrame([m.model_dump(mode="json") for m in models])


def main() -> None:
    _refresh_runtime_context()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    hospital_file = PROFILE.source_path(SOURCE_ROOT, "crm_account_assignment")
    company_file = PROFILE.source_path(SOURCE_ROOT, "crm_rep_master")
    crm_file = PROFILE.source_path(SOURCE_ROOT, "crm_activity")

    hospitals = load_hospital_master_from_file(
        hospital_file,
        config=PROFILE.hospital_adapter_factory(),
    )
    hospital_index = build_hospital_index(hospitals)

    company_master, company_unmapped = load_company_master_from_file(
        company_file,
        config=PROFILE.company_master_adapter_factory(),
        hospital_index=hospital_index,
    )

    crm_activities, crm_unmapped = load_crm_activity_from_file(
        crm_file,
        config=PROFILE.crm_activity_adapter_factory(),
        company_master=company_master,
    )

    hospital_df = models_to_frame(hospitals)
    company_df = models_to_frame(company_master)
    crm_df = models_to_frame(crm_activities)

    hospital_df.to_excel(OUTPUT_ROOT / "ops_hospital_master.xlsx", index=False)
    company_df.to_excel(OUTPUT_ROOT / "ops_company_master.xlsx", index=False)
    crm_df.to_excel(OUTPUT_ROOT / "ops_crm_activity.xlsx", index=False)

    if company_unmapped:
        pd.DataFrame(company_unmapped).to_excel(OUTPUT_ROOT / "unmapped_company_master.xlsx", index=False)
    if crm_unmapped:
        pd.DataFrame(crm_unmapped).to_excel(OUTPUT_ROOT / "unmapped_crm_activity.xlsx", index=False)

    report = {
        "company": COMPANY_NAME,
        "company_key": COMPANY_KEY,
        "source_root": str(SOURCE_ROOT),
        "output_root": str(OUTPUT_ROOT),
        "hospital_source_file": str(hospital_file),
        "company_source_file": str(company_file),
        "crm_source_file": str(crm_file),
        "hospital_count": len(hospitals),
        "company_master_count": len(company_master),
        "crm_activity_count": len(crm_activities),
        "company_unmapped_count": len(company_unmapped),
        "crm_unmapped_count": len(crm_unmapped),
        "company_key_integrity": validate_key_integrity(company_master),
    }

    (OUTPUT_ROOT / "normalization_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Normalized {COMPANY_NAME} CRM source data:")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
