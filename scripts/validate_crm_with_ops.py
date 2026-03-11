from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.crm.hospital_adapter import load_hospital_master_from_file, build_hospital_index
from common.asset_versions import (
    CRM_BUILDER_PAYLOAD_VERSION,
    attach_builder_payload_version,
)
from adapters.crm.company_master_adapter import load_company_master_from_file
from adapters.crm.crm_activity_adapter import load_crm_activity_from_file
from common.company_profile import get_company_ops_profile
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root
from modules.crm.service import build_crm_builder_payload, build_crm_result_asset
from ops_core.api.crm_router import evaluate_crm_asset

COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
PROFILE = get_company_ops_profile(COMPANY_KEY)
SOURCE_ROOT = get_company_root(ROOT, "company_source", COMPANY_KEY)
OUTPUT_ROOT = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "crm"


def main() -> None:
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

    total_raw_count = len(crm_activities) + len(crm_unmapped)
    result_asset = build_crm_result_asset(
        crm_activities,
        company_master,
        unmapped_raw_count=len(crm_unmapped),
        total_raw_count=total_raw_count,
        unmapped_hospital_names=[
            str(item.get("hospital_name", "")) for item in crm_unmapped[:20]
        ],
        notes=f"{COMPANY_KEY} company source -> adapter normalization -> ops crm validation",
    )
    evaluation = evaluate_crm_asset(result_asset)

    asset_payload = result_asset.model_dump(mode="json")
    evaluation_payload = evaluation.model_dump(mode="json")
    run_summary = {
        "source_root": str(SOURCE_ROOT),
        "hospital_count": len(hospitals),
        "company_master_count": len(company_master),
        "crm_activity_count": len(crm_activities),
        "company_unmapped_count": len(company_unmapped),
        "crm_unmapped_count": len(crm_unmapped),
        "quality_status": evaluation.quality_status,
        "quality_score": evaluation.quality_score,
        "next_modules": evaluation.next_modules,
    }
    builder_payload = build_crm_builder_payload(
        result_asset,
        run_summary,
        COMPANY_NAME,
        activities=crm_activities,
        company_master=company_master,
    )
    builder_payload = attach_builder_payload_version(
        builder_payload,
        payload_version=CRM_BUILDER_PAYLOAD_VERSION,
        source_asset_schema_version=result_asset.schema_version,
    )

    (OUTPUT_ROOT / "crm_result_asset.json").write_text(
        json.dumps(asset_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "crm_ops_evaluation.json").write_text(
        json.dumps(evaluation_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "crm_validation_summary.json").write_text(
        json.dumps(run_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "crm_builder_payload.json").write_text(
        json.dumps(builder_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Validated {COMPANY_NAME} CRM data with OPS:")
    print(json.dumps(run_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
