from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


LEGACY_TO_STANDARD = {
    "crm/hangyeol_crm_activity_raw.xlsx": "crm/crm_activity_raw.xlsx",
    "company/hangyeol_company_assignment_raw.xlsx": "company/company_assignment_raw.xlsx",
    "company/hangyeol_account_master.xlsx": "company/account_master.xlsx",
    "company/hangyeol_crm_rules_raw.xlsx": "company/crm_rules_raw.xlsx",
    "sales/hangyeol_sales_raw.xlsx": "sales/sales_raw.xlsx",
    "target/hangyeol_target_raw.xlsx": "target/target_raw.xlsx",
    "company/hangyeol_fact_ship_raw.csv": "company/fact_ship_raw.csv",
    "company/hangyeol_rep_master.xlsx": "company/rep_master.xlsx",
}


def migrate_company_source(company_root: Path) -> dict:
    summary = {
        "company_root": str(company_root),
        "renamed": [],
        "skipped_missing": [],
        "skipped_existing": [],
    }

    for legacy_relative, standard_relative in LEGACY_TO_STANDARD.items():
        legacy_path = company_root / Path(legacy_relative)
        standard_path = company_root / Path(standard_relative)

        if standard_path.exists():
            summary["skipped_existing"].append(str(standard_path))
            continue
        if not legacy_path.exists():
            summary["skipped_missing"].append(str(legacy_path))
            continue

        standard_path.parent.mkdir(parents=True, exist_ok=True)
        legacy_path.replace(standard_path)
        summary["renamed"].append(
            {
                "from": str(legacy_path),
                "to": str(standard_path),
            }
        )

    return summary


def main() -> None:
    source_root = ROOT / "data" / "company_source"
    results = []
    for company_root in sorted(path for path in source_root.iterdir() if path.is_dir()):
        results.append(migrate_company_source(company_root))

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
