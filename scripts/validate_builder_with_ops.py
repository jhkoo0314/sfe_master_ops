from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.builder.service import (
    build_crm_template_input,
    build_html_builder_asset,
    build_prescription_template_input,
    build_radar_template_input,
    prepare_sandbox_chunk_assets,
    prepare_crm_chunk_assets,
    prepare_prescription_chunk_assets,
    prepare_territory_chunk_assets,
    build_sandbox_template_input,
    build_template_payload,
    build_territory_template_input,
    render_builder_html,
)
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root
from modules.crm.service import build_crm_builder_payload
from result_assets.crm_result_asset import CrmResultAsset
from result_assets.sandbox_result_asset import SandboxResultAsset
from result_assets.radar_result_asset import RadarResultAsset


COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
CRM_TEMPLATE_PATH = ROOT / "templates" / "crm_analysis_template.html"
SANDBOX_TEMPLATE_PATH = ROOT / "templates" / "report_template.html"
TERRITORY_TEMPLATE_PATH = ROOT / "templates" / "territory_optimizer_template.html"
PRESCRIPTION_TEMPLATE_PATH = ROOT / "templates" / "prescription_flow_template.html"
RADAR_TEMPLATE_PATH = ROOT / "templates" / "radar_report_template.html"
CRM_ASSET_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "crm" / "crm_result_asset.json"
CRM_BUILDER_PAYLOAD_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "crm" / "crm_builder_payload.json"
SANDBOX_ASSET_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "sandbox" / "sandbox_result_asset.json"
TERRITORY_ASSET_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "territory" / "territory_result_asset.json"
TERRITORY_BUILDER_PAYLOAD_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "territory" / "territory_builder_payload.json"
PRESCRIPTION_ASSET_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "prescription" / "prescription_result_asset.json"
PRESCRIPTION_BUILDER_PAYLOAD_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "prescription" / "prescription_builder_payload.json"
RADAR_ASSET_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "radar" / "radar_result_asset.json"
OUTPUT_ROOT = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "builder"
TOTAL_VALID_TEMPLATE_PATH = ROOT / "templates" / "total_valid_templates.html"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sync_sandbox_chunk_assets() -> None:
    source_dir = SANDBOX_ASSET_PATH.with_name("sandbox_template_payload_assets")
    target_dir = OUTPUT_ROOT / "sandbox_report_preview_assets"
    target_dir.mkdir(parents=True, exist_ok=True)
    for existing in target_dir.glob("*.js"):
        existing.unlink()
    if not source_dir.exists():
        return
    for chunk_file in source_dir.glob("*.js"):
        shutil.copyfile(chunk_file, target_dir / chunk_file.name)


def refresh_crm_builder_payload() -> None:
    if not CRM_ASSET_PATH.exists():
        return
    summary_path = CRM_ASSET_PATH.with_name("crm_validation_summary.json")
    if not summary_path.exists():
        return

    crm_asset = CrmResultAsset.model_validate(load_json(CRM_ASSET_PATH))
    crm_summary = load_json(summary_path)
    builder_payload = build_crm_builder_payload(
        asset=crm_asset,
        summary=crm_summary,
        company_name=COMPANY_NAME,
    )
    CRM_BUILDER_PAYLOAD_PATH.write_text(
        json.dumps(builder_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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


def write_total_valid_output(summary: dict) -> dict | None:
    if not TOTAL_VALID_TEMPLATE_PATH.exists():
        return None

    template_html = TOTAL_VALID_TEMPLATE_PATH.read_text(encoding="utf-8")

    report_map = {
        "sandbox": ("sandbox_report", "Sandbox 성과 보고서", "Sandbox 결과 HTML"),
        "crm": ("crm_analysis", "CRM 행동 분석 보고서", "CRM 행동 분석 HTML"),
        "territory": ("territory_map", "Territory 권역 지도 보고서", "Territory 지도 HTML"),
        "prescription": ("prescription_flow", "PDF 처방흐름 보고서", "Prescription 흐름 HTML"),
        "radar": ("radar_report", "RADAR Decision Brief", "RADAR 신호/우선순위 HTML"),
    }
    reports_payload: dict[str, dict] = {}
    for module_key, (summary_key, title, subtitle) in report_map.items():
        item = summary.get(summary_key)
        if not item:
            continue
        html_path = Path(item["html"])
        if not html_path.exists():
            continue
        reports_payload[module_key] = {
            "title": title,
            "subtitle": subtitle,
            "badge": "TOTAL VALID",
            "src": html_path.name,
        }

    manifest = {
        "company": COMPANY_NAME,
        "generated_at": datetime.now().isoformat(),
        "reports": reports_payload,
    }
    manifest_script = f"<script>window.__OPS_TOTAL_VALID_DATA__ = {json.dumps(manifest, ensure_ascii=False)};</script>"
    if "</head>" in template_html:
        injected_html = template_html.replace("</head>", f"  {manifest_script}\n  </head>", 1)
    elif "</body>" in template_html:
        injected_html = template_html.replace("</body>", f"    {manifest_script}\n  </body>", 1)
    else:
        injected_html = template_html + "\n" + manifest_script
    output_path = OUTPUT_ROOT / "total_valid_preview.html"
    output_path.write_text(injected_html, encoding="utf-8")
    return {
        "html": str(output_path),
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
        prepare_sandbox_chunk_assets(
            sandbox_payload,
            asset_source_path=str(SANDBOX_ASSET_PATH),
            output_root=str(OUTPUT_ROOT),
        )
        sync_sandbox_chunk_assets()
        sandbox_input.payload_seed = sandbox_payload.payload
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

    crm_ready = CRM_ASSET_PATH.exists() and CRM_BUILDER_PAYLOAD_PATH.exists()
    if crm_ready:
        refresh_crm_builder_payload()
        crm_input = build_crm_template_input(
            str(CRM_TEMPLATE_PATH),
            builder_payload_path=str(CRM_BUILDER_PAYLOAD_PATH),
            source_asset_path=str(CRM_ASSET_PATH),
        )
        crm_payload = build_template_payload(crm_input)
        prepare_crm_chunk_assets(
            crm_payload,
            payload_source_path=str(CRM_BUILDER_PAYLOAD_PATH),
            output_root=str(OUTPUT_ROOT),
        )
        crm_input.payload_seed = crm_payload.payload
        crm_html = render_builder_html(crm_payload)
        crm_result_asset = build_html_builder_asset(crm_input, crm_html)
        summary["crm_analysis"] = write_builder_output(
            "crm_analysis_preview",
            crm_input,
            crm_payload,
            crm_html,
            crm_result_asset,
        )
        summary["templates_validated"].append(str(CRM_TEMPLATE_PATH))
    else:
        summary["skipped_reports"].append("crm_analysis")

    territory_ready = TERRITORY_ASSET_PATH.exists() and TERRITORY_BUILDER_PAYLOAD_PATH.exists()
    if territory_ready:
        territory_input = build_territory_template_input(
            str(TERRITORY_TEMPLATE_PATH),
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
            PRESCRIPTION_BUILDER_PAYLOAD_PATH,
        ]
    )
    if prescription_ready:
        prescription_input = build_prescription_template_input(
            str(PRESCRIPTION_TEMPLATE_PATH),
            builder_payload_path=str(PRESCRIPTION_BUILDER_PAYLOAD_PATH),
            source_asset_path=str(PRESCRIPTION_ASSET_PATH),
        )
        prescription_payload = build_template_payload(prescription_input)
        prepare_prescription_chunk_assets(
            prescription_payload,
            payload_source_path=str(PRESCRIPTION_BUILDER_PAYLOAD_PATH),
            output_root=str(OUTPUT_ROOT),
        )
        prescription_input.payload_seed = prescription_payload.payload
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

    if RADAR_ASSET_PATH.exists() and RADAR_TEMPLATE_PATH.exists():
        radar_asset = RadarResultAsset.model_validate(load_json(RADAR_ASSET_PATH))
        radar_input = build_radar_template_input(
            radar_asset,
            str(RADAR_TEMPLATE_PATH),
            source_asset_path=str(RADAR_ASSET_PATH),
        )
        radar_payload = build_template_payload(radar_input)
        radar_html = render_builder_html(radar_payload)
        radar_result_asset = build_html_builder_asset(radar_input, radar_html)
        summary["radar_report"] = write_builder_output(
            "radar_report_preview",
            radar_input,
            radar_payload,
            radar_html,
            radar_result_asset,
        )
        summary["templates_validated"].append(str(RADAR_TEMPLATE_PATH))
    else:
        summary["skipped_reports"].append("radar_report")

    total_valid_output = write_total_valid_output(summary)
    if total_valid_output is not None:
        summary["total_valid"] = total_valid_output
        summary["templates_validated"].append(str(TOTAL_VALID_TEMPLATE_PATH))
    else:
        summary["skipped_reports"].append("total_valid")

    summary["built_report_count"] = sum(
        1
        for key in ["crm_analysis", "sandbox_report", "territory_map", "prescription_flow", "radar_report", "total_valid"]
        if key in summary
    )
    (OUTPUT_ROOT / "builder_validation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Validated {COMPANY_NAME} builder pipeline:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
