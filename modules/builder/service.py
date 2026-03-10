"""
HTML Builder Service
OPS Result Asset / Builder Payload → 분석 보고 HTML 자동 생성
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from modules.builder.schemas import (
    BuilderInputReference,
    BuilderInputStandard,
    BuilderPayloadStandard,
    HtmlBuilderResultAsset,
)
from result_assets.sandbox_result_asset import SandboxResultAsset


def build_sandbox_template_input(
    asset: SandboxResultAsset,
    template_path: str,
    source_asset_path: str | None = None,
) -> BuilderInputStandard:
    dashboard_payload = asset.dashboard_payload
    payload_seed = (dashboard_payload.template_payload if dashboard_payload is not None else {}) or {}
    reference = BuilderInputReference(
        template_key="report_template",
        template_path=template_path,
        source_module="sandbox",
        asset_type=asset.asset_type,
        source_asset_path=source_asset_path,
        description="Sandbox result asset -> report_template 주입",
    )
    return BuilderInputStandard(
        template_key="report_template",
        template_path=template_path,
        report_title=f"SFE 성과 분석 보고서 ({asset.scenario})",
        executive_summary=dashboard_payload.insight_messages if dashboard_payload is not None else [],
        source_references=[reference],
        payload_seed=payload_seed,
        source_modules=["sandbox"],
    )


def _load_payload_seed(payload_path: str) -> dict:
    return json.loads(Path(payload_path).read_text(encoding="utf-8"))


def build_territory_template_input(
    template_path: str,
    builder_payload_path: str,
    source_asset_path: str | None = None,
) -> BuilderInputStandard:
    payload_seed = _load_payload_seed(builder_payload_path)
    overview = payload_seed.get("overview", {})
    reference = BuilderInputReference(
        template_key="territory_map",
        template_path=template_path,
        source_module="territory",
        asset_type="territory_result_asset",
        source_asset_path=source_asset_path,
        description="Territory builder payload -> Spatial_Preview_260224 주입",
    )
    return BuilderInputStandard(
        template_key="territory_map",
        template_path=template_path,
        report_title=str(overview.get("map_title") or "SFE 권역별 영업 성과 지도"),
        executive_summary=[
            f"전체 권역 {int(overview.get('total_regions', 0))}개",
            f"커버리지율 {float(overview.get('coverage_rate', 0.0) or 0.0):.1%}",
            f"담당자 {int(overview.get('total_reps', 0))}명",
        ],
        source_references=[reference],
        payload_seed=payload_seed,
        source_modules=["territory"],
    )


def build_prescription_template_input(
    template_path: str,
    builder_payload_path: str,
    source_asset_path: str | None = None,
) -> BuilderInputStandard:
    payload_seed = _load_payload_seed(builder_payload_path)
    overview = payload_seed.get("overview", {})
    reference = BuilderInputReference(
        template_key="prescription_flow",
        template_path=template_path,
        source_module="prescription",
        asset_type="prescription_result_asset",
        source_asset_path=source_asset_path,
        description="Prescription validation outputs -> prescription_flow_template 주입",
    )
    claim_summary = overview.get("claim_validation_summary", {})
    return BuilderInputStandard(
        template_key="prescription_flow",
        template_path=template_path,
        report_title="Prescription Data Flow 검증 리포트",
        executive_summary=[
            f"처방 흐름 {overview['flow_record_count']:,}건 추적",
            f"연결 병원 {overview['connected_hospital_count']}개",
            f"비교표 PASS {claim_summary.get('pass_count', 0)}건 / REVIEW {claim_summary.get('review_count', 0)}건 / SUSPECT {claim_summary.get('suspect_count', 0)}건",
        ],
        source_references=[reference],
        payload_seed=payload_seed,
        source_modules=["prescription"],
    )


def build_crm_template_input(
    template_path: str,
    builder_payload_path: str,
    source_asset_path: str | None = None,
) -> BuilderInputStandard:
    payload_seed = _load_payload_seed(builder_payload_path)
    overview = payload_seed.get("overview", {})
    activity_context = payload_seed.get("activity_context", {})
    mapping_quality = payload_seed.get("mapping_quality", {})
    reference = BuilderInputReference(
        template_key="crm_analysis",
        template_path=template_path,
        source_module="crm",
        asset_type="crm_result_asset",
        source_asset_path=source_asset_path,
        description="CRM result asset -> crm analysis template 주입",
    )
    return BuilderInputStandard(
        template_key="crm_analysis",
        template_path=template_path,
        report_title="CRM 행동 분석 리포트",
        executive_summary=[
            f"CRM 활동 {int(overview.get('crm_activity_count', 0)):,}건",
            f"담당자 {int(activity_context.get('unique_reps', 0))}명 / 병원 {int(activity_context.get('unique_hospitals', 0))}개",
            f"병원 매핑률 {float(mapping_quality.get('hospital_mapping_rate', 0) or 0):.1%}",
        ],
        source_references=[reference],
        payload_seed=payload_seed,
        source_modules=["crm"],
    )


def build_template_payload(builder_input: BuilderInputStandard) -> BuilderPayloadStandard:
    if builder_input.template_key == "report_template":
        return BuilderPayloadStandard(
            template_key="report_template",
            template_path=builder_input.template_path,
            report_title=builder_input.report_title,
            payload=builder_input.payload_seed,
            source_modules=builder_input.source_modules,
            output_name="ops_report_preview.html",
            render_mode="report_data_json",
        )

    if builder_input.template_key == "territory_map":
        return BuilderPayloadStandard(
            template_key="territory_map",
            template_path=builder_input.template_path,
            report_title=builder_input.report_title,
            payload=builder_input.payload_seed,
            source_modules=builder_input.source_modules,
            output_name="territory_map_preview.html",
            render_mode="territory_window_vars",
        )

    if builder_input.template_key == "prescription_flow":
        return BuilderPayloadStandard(
            template_key="prescription_flow",
            template_path=builder_input.template_path,
            report_title=builder_input.report_title,
            payload=builder_input.payload_seed,
            source_modules=builder_input.source_modules,
            output_name="prescription_flow_preview.html",
            render_mode="prescription_window_vars",
        )

    if builder_input.template_key == "crm_analysis":
        return BuilderPayloadStandard(
            template_key="crm_analysis",
            template_path=builder_input.template_path,
            report_title=builder_input.report_title,
            payload=builder_input.payload_seed,
            source_modules=builder_input.source_modules,
            output_name="crm_analysis_preview.html",
            render_mode="crm_window_vars",
        )

    raise ValueError(f"지원하지 않는 template_key: {builder_input.template_key}")


def render_builder_html(builder_payload: BuilderPayloadStandard) -> str:
    template_text = Path(builder_payload.template_path).read_text(encoding="utf-8")

    if builder_payload.render_mode == "report_data_json":
        return re.sub(
            r"const db = /\*DATA_JSON_PLACEHOLDER\*/[\s\S]*?\n\s*let charts = \{\};",
            f"const db = {json.dumps(builder_payload.payload, ensure_ascii=False, indent=2)};\n        let charts = {{}};",
            template_text,
            count=1,
        )

    if builder_payload.render_mode == "territory_window_vars":
        rendered = template_text
        replacements = [
            (
                r'window\.__INITIAL_MODE__ = "[^"]*";',
                f'window.__INITIAL_MODE__ = "{builder_payload.payload.get("mode", "hospital")}";',
            ),
            (
                r"window\.__INITIAL_MARKERS__ = [\s\S]*?;",
                f"window.__INITIAL_MARKERS__ = {json.dumps(builder_payload.payload.get('markers', []), ensure_ascii=False)};",
            ),
            (
                r"window\.__INITIAL_ROUTES__ = [\s\S]*?;",
                f"window.__INITIAL_ROUTES__ = {json.dumps(builder_payload.payload.get('routes', []), ensure_ascii=False)};",
            ),
        ]
        for pattern, replacement in replacements:
            rendered = re.sub(pattern, replacement, rendered, count=1)
        return rendered

    if builder_payload.render_mode == "prescription_window_vars":
        rendered = re.sub(
            r"window\.__PRESCRIPTION_DATA__ = [\s\S]*?;",
            f"window.__PRESCRIPTION_DATA__ = {json.dumps(builder_payload.payload, ensure_ascii=False)};",
            template_text,
            count=1,
        )
        return rendered

    if builder_payload.render_mode == "crm_window_vars":
        rendered = re.sub(
            r"window\.__CRM_DATA__ = [\s\S]*?;",
            f"window.__CRM_DATA__ = {json.dumps(builder_payload.payload, ensure_ascii=False)};",
            template_text,
            count=1,
        )
        return rendered

    raise ValueError(f"지원하지 않는 render_mode: {builder_payload.render_mode}")


def build_html_builder_asset(
    builder_input: BuilderInputStandard,
    output_html: str,
    ) -> HtmlBuilderResultAsset:
    builder_payload = build_template_payload(builder_input)
    return HtmlBuilderResultAsset(
        template_reference=builder_input.source_references[0] if builder_input.source_references else None,
        render_summary={
            "template_key": builder_payload.template_key,
            "render_mode": builder_payload.render_mode,
            "source_count": len(builder_input.source_references),
        },
        report_payload_summary=_summarize_payload(builder_payload),
        output_reference={
            "output_name": builder_payload.output_name,
            "report_title": builder_payload.report_title,
        },
        ops_report_html=output_html,
        builder_input=builder_input,
        builder_payload=builder_payload,
        source_modules=builder_input.source_modules,
    )


def _summarize_payload(builder_payload: BuilderPayloadStandard) -> dict:
    payload = builder_payload.payload
    if builder_payload.template_key == "report_template":
        return {
            "branch_count": len(payload.get("branches", {})),
            "product_count": len(payload.get("products", [])),
            "missing_data_count": len(payload.get("missing_data", [])),
        }
    if builder_payload.template_key == "territory_map":
        return {
            "marker_count": len(payload.get("markers", [])),
            "route_count": len(payload.get("routes", [])),
            "mode": payload.get("mode"),
        }
    if builder_payload.template_key == "prescription_flow":
        return {
            "claim_count": len(payload.get("claims", [])),
            "gap_count": len(payload.get("gaps", [])),
            "hospital_trace_count": len(payload.get("hospital_traces", [])),
        }
    if builder_payload.template_key == "crm_analysis":
        default_scope = payload.get("scope_data", {}).get("ALL|ALL", {})
        return {
            "scope_count": len(payload.get("scope_data", {})),
            "team_option_count": len(payload.get("filters", {}).get("team_options", [])),
            "matrix_row_count": len(default_scope.get("matrix_rows", [])),
        }
    return {}
