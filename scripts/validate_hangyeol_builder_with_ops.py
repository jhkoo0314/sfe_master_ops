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
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root
from result_assets.sandbox_result_asset import SandboxResultAsset
from result_assets.territory_result_asset import TerritoryResultAsset


COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
SANDBOX_TEMPLATE_PATH = ROOT / "templates" / "report_template.html"
TERRITORY_TEMPLATE_PATH = ROOT / "templates" / "Spatial_Preview_260224.html"
PRESCRIPTION_TEMPLATE_PATH = ROOT / "templates" / "prescription_flow_template.html"
SANDBOX_ASSET_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "sandbox" / "sandbox_result_asset.json"
TERRITORY_ASSET_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "territory" / "territory_result_asset.json"
PRESCRIPTION_ASSET_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "prescription" / "prescription_result_asset.json"
PRESCRIPTION_SUMMARY_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "prescription" / "prescription_validation_summary.json"
PRESCRIPTION_CLAIM_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "prescription" / "prescription_claim_validation.xlsx"
PRESCRIPTION_GAP_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "prescription" / "prescription_gap_records.xlsx"
PRESCRIPTION_TRACE_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "prescription" / "prescription_hospital_trace_quarter.xlsx"
PRESCRIPTION_REP_KPI_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "prescription" / "prescription_rep_kpi_quarter.xlsx"
CRM_ACTIVITY_PATH = get_company_root(ROOT, "company_source", COMPANY_KEY) / "crm" / "hangyeol_crm_activity_raw.xlsx"
OUTPUT_ROOT = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "builder"


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
    summary = {
        "company": COMPANY_NAME,
        "templates_validated": [],
        "skipped_reports": [],
    }

    if SANDBOX_ASSET_PATH.exists():
        sandbox_asset = SandboxResultAsset.model_validate(load_json(SANDBOX_ASSET_PATH))
        sandbox_input = build_sandbox_template_input(
            sandbox_asset,
            str(SANDBOX_TEMPLATE_PATH),
            source_asset_path=str(SANDBOX_ASSET_PATH),
        )
        sandbox_payload = build_template_payload(sandbox_input)
        sandbox_html = render_builder_html(sandbox_payload)
        sandbox_result_asset = build_html_builder_asset(sandbox_input, sandbox_html)
        summary["sandbox_report"] = write_builder_output(
            "sandbox_report_preview",
            sandbox_input,
            sandbox_payload,
            sandbox_html,
            sandbox_result_asset,
        )
        summary["templates_validated"].append(str(SANDBOX_TEMPLATE_PATH))
    else:
        summary["skipped_reports"].append("sandbox_report")

    if TERRITORY_ASSET_PATH.exists():
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
        summary["territory_map"] = write_builder_output(
            "territory_map_preview",
            territory_input,
            territory_payload,
            territory_html,
            territory_result_asset,
        )
        summary["templates_validated"].append(str(TERRITORY_TEMPLATE_PATH))
    else:
        summary["skipped_reports"].append("territory_map")

    prescription_ready = all(
        path.exists()
        for path in [
            PRESCRIPTION_ASSET_PATH,
            PRESCRIPTION_SUMMARY_PATH,
            PRESCRIPTION_CLAIM_PATH,
            PRESCRIPTION_GAP_PATH,
            PRESCRIPTION_TRACE_PATH,
            PRESCRIPTION_REP_KPI_PATH,
        ]
    )
    if prescription_ready:
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
        summary["prescription_flow"] = write_builder_output(
            "prescription_flow_preview",
            prescription_input,
            prescription_payload,
            prescription_html,
            prescription_result_asset,
        )
        summary["templates_validated"].append(str(PRESCRIPTION_TEMPLATE_PATH))
    else:
        summary["skipped_reports"].append("prescription_flow")

    summary["built_report_count"] = sum(
        1 for key in ["sandbox_report", "territory_map", "prescription_flow"] if key in summary
    )
    (OUTPUT_ROOT / "builder_validation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Validated {COMPANY_NAME} builder pipeline:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
