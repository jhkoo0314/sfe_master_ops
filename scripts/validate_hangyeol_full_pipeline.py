from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_hangyeol_source_raw import main as generate_source_main
from scripts.normalize_hangyeol_crm_source import main as normalize_crm_main
from scripts.validate_hangyeol_crm_with_ops import main as validate_crm_main
from scripts.normalize_hangyeol_prescription_source import main as normalize_rx_main
from scripts.validate_hangyeol_prescription_with_ops import main as validate_rx_main
from scripts.normalize_hangyeol_sandbox_source import main as normalize_sandbox_main
from scripts.validate_hangyeol_sandbox_with_ops import main as validate_sandbox_main
from scripts.validate_hangyeol_territory_with_ops import main as validate_territory_main
from scripts.validate_hangyeol_builder_with_ops import main as validate_builder_main
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root

COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
OUTPUT_ROOT = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "pipeline"
RAW_ASSIGNMENT_PATH = ROOT / "data" / "sample_data" / "sample_company" / "sample_hospital_assignment_data.xlsx"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    generation_note = None
    if COMPANY_KEY == "hangyeol_pharma" and RAW_ASSIGNMENT_PATH.exists():
        generate_source_main()
    elif COMPANY_KEY != "hangyeol_pharma":
        generation_note = "활성 회사가 한결제약이 아니므로 한결제약 raw 생성 단계는 건너뛰었습니다."
    else:
        generation_note = (
            "sample_hospital_assignment_data.xlsx 가 없어 raw 생성 단계는 건너뛰고 "
            "기존 표준화/검증 산출물을 재사용했습니다."
        )
    normalize_crm_main()
    validate_crm_main()
    normalize_rx_main()
    validate_rx_main()
    normalize_sandbox_main()
    validate_sandbox_main()
    validate_territory_main()
    validate_builder_main()

    validation_root = get_company_root(ROOT, "ops_validation", COMPANY_KEY)
    crm_summary = load_json(validation_root / "crm" / "crm_validation_summary.json")
    rx_summary = load_json(validation_root / "prescription" / "prescription_validation_summary.json")
    sandbox_summary = load_json(validation_root / "sandbox" / "sandbox_validation_summary.json")
    territory_summary = load_json(validation_root / "territory" / "territory_validation_summary.json")
    builder_summary = load_json(validation_root / "builder" / "builder_validation_summary.json")

    pipeline_summary = {
        "company": COMPANY_NAME,
        "stages": {
            "crm": crm_summary,
            "prescription": rx_summary,
            "sandbox": sandbox_summary,
            "territory": territory_summary,
            "builder": builder_summary,
        },
        "generation_note": generation_note,
        "all_passed": all(
            stage.get("quality_status") == "pass"
            for stage in [crm_summary, rx_summary, sandbox_summary, territory_summary]
        ),
    }

    (OUTPUT_ROOT / "pipeline_validation_summary.json").write_text(
        json.dumps(pipeline_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Validated Hangyeol full pipeline:")
    print(json.dumps(pipeline_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
