from __future__ import annotations

import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


TEMPLATE_PATH = ROOT / "templates" / "report_template.html"
SANDBOX_ASSET_PATH = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "sandbox" / "sandbox_result_asset.json"
OUTPUT_ROOT = ROOT / "data" / "ops_validation" / "hangyeol_pharma" / "sandbox"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render_html(template_text: str, payload: dict) -> str:
    return re.sub(
        r"const db = /\*DATA_JSON_PLACEHOLDER\*/[\s\S]*?\n\s*let charts = \{\};",
        f"const db = {json.dumps(payload, ensure_ascii=False, indent=2)};\n        let charts = {{}};",
        template_text,
        count=1,
    )


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    sandbox_asset = load_json(SANDBOX_ASSET_PATH)
    payload = (((sandbox_asset.get("dashboard_payload") or {}).get("template_payload")) or {})
    if not payload:
        raise ValueError("sandbox_result_asset.json 안에 dashboard_payload.template_payload 가 없습니다.")

    rendered_html = render_html(template_text, payload)

    output_html = OUTPUT_ROOT / "sandbox_report_preview.html"
    output_payload = OUTPUT_ROOT / "sandbox_template_payload.json"
    output_summary = OUTPUT_ROOT / "sandbox_template_validation_summary.json"

    output_html.write_text(rendered_html, encoding="utf-8")
    output_payload.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    member_count = sum(len(branch.get("members", [])) for branch in payload.get("branches", {}).values())
    summary = {
        "template_file": str(TEMPLATE_PATH),
        "output_html": str(output_html),
        "branch_count": len(payload.get("branches", {})),
        "member_count": member_count,
        "product_count": len(payload.get("products", [])),
        "total_achieve": payload.get("total", {}).get("achieve"),
        "integrity_score": payload.get("data_health", {}).get("integrity_score"),
        "missing_data_count": len(payload.get("missing_data", [])),
        "uses_actual_sandbox_asset": True,
    }
    output_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Rendered Hangyeol sandbox template:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
