from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.builder.service import (
    build_html_builder_asset,
    build_prescription_template_input,
    build_sandbox_template_input,
    build_template_payload,
    build_territory_template_input,
    render_builder_html,
)
from result_assets.sandbox_result_asset import SandboxResultAsset
from result_assets.territory_result_asset import TerritoryResultAsset


SANDBOX_TEMPLATE_PATH = ROOT / "templates" / "report_template.html"
TERRITORY_TEMPLATE_PATH = ROOT / "templates" / "Spatial_Preview_260224.html"
PRESCRIPTION_TEMPLATE_PATH = ROOT / "templates" / "prescription_flow_template.html"
SANDBOX_ASSET_PATH = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "sandbox" / "sandbox_result_asset.json"
TERRITORY_ASSET_PATH = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "territory" / "territory_result_asset.json"
PRESCRIPTION_ASSET_PATH = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "prescription" / "prescription_result_asset.json"
PRESCRIPTION_SUMMARY_PATH = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "prescription" / "prescription_validation_summary.json"
PRESCRIPTION_CLAIM_PATH = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "prescription" / "prescription_claim_validation.xlsx"
PRESCRIPTION_GAP_PATH = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "prescription" / "prescription_gap_records.xlsx"
PRESCRIPTION_TRACE_PATH = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "prescription" / "prescription_hospital_trace_quarter.xlsx"
PRESCRIPTION_REP_KPI_PATH = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "prescription" / "prescription_rep_kpi_quarter.xlsx"
CRM_ACTIVITY_PATH = ROOT / "data" / "company_source" / "hangyeol_pharma" / "crm" / "hangyeol_crm_activity_raw.xlsx"
OUTPUT_ROOT = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "builder"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_builder_output(name: str, builder_input, builder_payload, html: str, asset) -> dict:
    html_path = OUTPUT_ROOT / f"{name}.html"
    input_path = OUTPUT_ROOT / f"{name}_input_standard.json"
    payload_path = OUTPUT_ROOT / f"{name}_payload_standard.json"
    asset_path = OUTPUT_ROOT / f"{name}_result_asset.json"

    html_path.write_text(html, encoding="utf-8")
    input_path.write_text(json.dumps(builder_input.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
    payload_path.write_text(json.dumps(builder_payload.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
    asset_path.write_text(json.dumps(asset.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "html": str(html_path),
        "input_standard": str(input_path),
        "payload_standard": str(payload_path),
        "result_asset": str(asset_path),
    }


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    sandbox_asset = SandboxResultAsset.model_validate(load_json(SANDBOX_ASSET_PATH))
    sandbox_input = build_sandbox_template_input(
        sandbox_asset,
        str(SANDBOX_TEMPLATE_PATH),
        source_asset_path=str(SANDBOX_ASSET_PATH),
    )
    sandbox_payload = build_template_payload(sandbox_input)
    sandbox_html = render_builder_html(sandbox_payload)
    sandbox_result_asset = build_html_builder_asset(sandbox_input, sandbox_html)
    sandbox_outputs = write_builder_output(
        "sandbox_report_preview",
        sandbox_input,
        sandbox_payload,
        sandbox_html,
        sandbox_result_asset,
    )

    territory_asset = TerritoryResultAsset.model_validate(load_json(TERRITORY_ASSET_PATH))
    territory_input = build_territory_template_input(
        territory_asset,
        str(TERRITORY_TEMPLATE_PATH),
        source_asset_path=str(TERRITORY_ASSET_PATH),
        crm_activity_path=str(CRM_ACTIVITY_PATH),
    )
    territory_payload = build_template_payload(territory_input)
    territory_html = render_builder_html(territory_payload)
    territory_result_asset = build_html_builder_asset(territory_input, territory_html)
    territory_outputs = write_builder_output(
        "territory_map_preview",
        territory_input,
        territory_payload,
        territory_html,
        territory_result_asset,
    )

    prescription_input = build_prescription_template_input(
        str(PRESCRIPTION_TEMPLATE_PATH),
        summary_path=str(PRESCRIPTION_SUMMARY_PATH),
        claim_validation_path=str(PRESCRIPTION_CLAIM_PATH),
        gap_report_path=str(PRESCRIPTION_GAP_PATH),
        hospital_trace_path=str(PRESCRIPTION_TRACE_PATH),
        rep_kpi_path=str(PRESCRIPTION_REP_KPI_PATH),
        source_asset_path=str(PRESCRIPTION_ASSET_PATH),
    )
    prescription_payload = build_template_payload(prescription_input)
    prescription_html = render_builder_html(prescription_payload)
    prescription_result_asset = build_html_builder_asset(prescription_input, prescription_html)
    prescription_outputs = write_builder_output(
        "prescription_flow_preview",
        prescription_input,
        prescription_payload,
        prescription_html,
        prescription_result_asset,
    )

    summary = {
        "company": "한결제약",
        "sandbox_report": sandbox_outputs,
        "territory_map": territory_outputs,
        "prescription_flow": prescription_outputs,
        "templates_validated": [
            str(SANDBOX_TEMPLATE_PATH),
            str(TERRITORY_TEMPLATE_PATH),
            str(PRESCRIPTION_TEMPLATE_PATH),
        ],
    }
    (OUTPUT_ROOT / "builder_validation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Validated Hangyeol builder pipeline:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
