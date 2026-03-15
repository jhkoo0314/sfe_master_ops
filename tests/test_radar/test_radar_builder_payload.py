from modules.builder.service import build_radar_template_input, build_template_payload, render_builder_html
from modules.radar.schemas import RadarInputStandard
from modules.radar.service import build_radar_result_asset


def _make_radar_result():
    radar_input = RadarInputStandard(
        meta={
            "company_key": "daon_pharma",
            "run_id": "run-radar-builder-001",
            "period_type": "monthly",
            "period_value": "2026-03",
            "source_status": "validation_approved",
        },
        kpi_summary={
            "goal_attainment_pct": 91.0,
            "pv_change_pct": -19.0,
            "hir": 57.2,
            "rtr": 66.1,
            "bcr": 62.0,
            "phr": 64.5,
        },
        scope_summaries={"by_branch": [{"branch_key": "seoul"}], "by_rep": [], "by_product": []},
        validation_summary={"status": "approved", "warnings": [], "quality_score": 0.91},
        sandbox_summary={"top_declines": [], "top_gains": [], "trend_flags": ["down"]},
    )
    return build_radar_result_asset(radar_input)


def test_radar_template_payload_and_html_injection():
    radar_asset = _make_radar_result()
    builder_input = build_radar_template_input(
        radar_asset,
        template_path="templates/radar_report_template.html",
        source_asset_path="data/ops_validation/demo/radar/radar_result_asset.json",
    )
    builder_payload = build_template_payload(builder_input)
    html = render_builder_html(builder_payload)

    assert builder_input.template_key == "radar_report"
    assert builder_payload.render_mode == "radar_window_vars"
    assert builder_payload.output_name == "radar_report_preview.html"
    assert "window.__RADAR_DATA__" in html
