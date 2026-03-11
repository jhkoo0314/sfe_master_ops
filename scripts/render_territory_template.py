from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.company_runtime import get_active_company_key, get_company_root
from modules.builder.service import (
    prepare_territory_chunk_assets,
    build_template_payload,
    build_territory_template_input,
    render_builder_html,
)


COMPANY_KEY = get_active_company_key()
TEMPLATE_PATH = ROOT / "templates" / "territory_optimizer_template.html"
TERRITORY_ASSET_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "territory" / "territory_result_asset.json"
TERRITORY_BUILDER_PAYLOAD_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "territory" / "territory_builder_payload.json"
OUTPUT_ROOT = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "territory"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    territory_input = build_territory_template_input(
        str(TEMPLATE_PATH),
        builder_payload_path=str(TERRITORY_BUILDER_PAYLOAD_PATH),
        source_asset_path=str(TERRITORY_ASSET_PATH),
    )
    territory_payload = build_template_payload(territory_input)
    prepare_territory_chunk_assets(
        territory_payload,
        payload_source_path=str(TERRITORY_BUILDER_PAYLOAD_PATH),
        output_root=str(OUTPUT_ROOT),
    )
    territory_input.payload_seed = territory_payload.payload
    rendered_html = render_builder_html(territory_payload)

    output_html_path = OUTPUT_ROOT / "territory_map_preview.html"
    output_payload_path = OUTPUT_ROOT / "territory_template_payload.json"
    summary_path = OUTPUT_ROOT / "territory_template_validation_summary.json"

    output_html_path.write_text(rendered_html, encoding="utf-8")
    output_payload_path.write_text(
        json.dumps(territory_payload.payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    payload = territory_payload.payload
    summary = {
        "template_file": str(TEMPLATE_PATH),
        "output_html": str(output_html_path),
        "rep_filter_count": len(payload.get("filters", {}).get("rep_options", [])),
        "selection_count": int(payload.get("overview", {}).get("route_selection_count", 0) or 0),
        "default_selection": payload.get("default_selection", {}),
        "territory_hospital_count": payload.get("overview", {}).get("territory_hospital_count", 0),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Rendered {COMPANY_KEY} Territory template:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
