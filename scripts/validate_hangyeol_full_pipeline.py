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
from scripts.render_hangyeol_territory_template import main as render_territory_template_main


OUTPUT_ROOT = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "pipeline"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    generate_source_main()
    normalize_crm_main()
    validate_crm_main()
    normalize_rx_main()
    validate_rx_main()
    normalize_sandbox_main()
    validate_sandbox_main()
    validate_territory_main()
    render_territory_template_main()

    crm_summary = load_json(ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "crm" / "crm_validation_summary.json")
    rx_summary = load_json(ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "prescription" / "prescription_validation_summary.json")
    sandbox_summary = load_json(ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "sandbox" / "sandbox_validation_summary.json")
    territory_summary = load_json(ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "territory" / "territory_validation_summary.json")

    pipeline_summary = {
        "company": "한결제약",
        "stages": {
            "crm": crm_summary,
            "prescription": rx_summary,
            "sandbox": sandbox_summary,
            "territory": territory_summary,
        },
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
