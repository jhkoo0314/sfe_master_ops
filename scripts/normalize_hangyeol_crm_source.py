from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.crm.adapter_config import (
    HospitalAdapterConfig,
    CompanyMasterAdapterConfig,
    CrmActivityAdapterConfig,
)
from adapters.crm.hospital_adapter import load_hospital_master_from_file, build_hospital_index
from adapters.crm.company_master_adapter import load_company_master_from_file, validate_key_integrity
from adapters.crm.crm_activity_adapter import load_crm_activity_from_file


SOURCE_ROOT = ROOT / "data" / "company_source" / "hangyeol_pharma"
OUTPUT_ROOT = ROOT / "data" / "ops_standard" / "hangyeol_pharma" / "crm"


def models_to_frame(models: list) -> pd.DataFrame:
    return pd.DataFrame([m.model_dump(mode="json") for m in models])


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    hospital_file = SOURCE_ROOT / "company" / "hangyeol_account_master.xlsx"
    company_file = SOURCE_ROOT / "company" / "hangyeol_company_assignment_raw.xlsx"
    crm_file = SOURCE_ROOT / "crm" / "hangyeol_crm_activity_raw.xlsx"

    hospitals = load_hospital_master_from_file(
        hospital_file,
        config=HospitalAdapterConfig.hangyeol_account_example(),
    )
    hospital_index = build_hospital_index(hospitals)

    company_master, company_unmapped = load_company_master_from_file(
        company_file,
        config=CompanyMasterAdapterConfig.hangyeol_company_source_example(),
        hospital_index=hospital_index,
    )

    crm_activities, crm_unmapped = load_crm_activity_from_file(
        crm_file,
        config=CrmActivityAdapterConfig.hangyeol_crm_source_example(),
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
        "source_root": str(SOURCE_ROOT),
        "output_root": str(OUTPUT_ROOT),
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

    print("Normalized Hangyeol CRM source data:")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
