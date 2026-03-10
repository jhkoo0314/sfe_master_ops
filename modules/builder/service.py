"""
HTML Builder Service
Layer1: OPS Result Asset → 분석 보고 HTML 자동 생성
Layer2: WebSlide Architect 페르소나 세션 관리
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from modules.builder.schemas import (
    BuilderInputReference,
    BuilderInputStandard,
    BuilderPayloadStandard,
    HtmlBuilderResultAsset,
    OpsReportPayload,
    ReportSection,
    WebSlideSession,
    WebSlideSlotContent,
)
from result_assets.sandbox_result_asset import SandboxResultAsset
from result_assets.territory_result_asset import TerritoryResultAsset
import uuid
from datetime import datetime


# ────────────────────────────────────────
# Layer 1: OPS Result Asset → Payload 변환
# ────────────────────────────────────────

def sandbox_to_report_payload(asset: SandboxResultAsset) -> OpsReportPayload:
    s = asset.analysis_summary
    jq = asset.join_quality

    sections = [
        ReportSection(
            section_id="kpi_summary",
            section_title="핵심 KPI 요약",
            section_type="kpi_cards",
            data={
                "cards": [
                    {"label": "총 매출", "value": f"{s.total_sales_amount/10000:,.0f}만원"},
                    {"label": "평균 달성률", "value": f"{(s.avg_attainment_rate or 0)*100:.1f}%"},
                    {"label": "분석 병원", "value": f"{s.total_hospitals}개"},
                    {"label": "CRM×Sales 조인율", "value": f"{jq.crm_sales_join_rate:.0%}"},
                ]
            },
            render_hint="4-column KPI cards row"
        ),
        ReportSection(
            section_id="top_hospitals",
            section_title="달성률 상위 병원",
            section_type="table",
            data={
                "columns": ["병원ID", "매출", "달성률", "방문수"],
                "rows": [
                    [r.hospital_id,
                     f"{r.total_sales:,.0f}",
                     f"{(r.attainment_rate or 0)*100:.1f}%",
                     str(r.total_visits)]
                    for r in sorted(asset.hospital_records,
                                    key=lambda x: x.attainment_rate or 0,
                                    reverse=True)[:10]
                ]
            }
        ),
        ReportSection(
            section_id="insights",
            section_title="전략적 인사이트",
            section_type="text",
            data={"items": asset.dashboard_payload.insight_messages if asset.dashboard_payload else []}
        ),
    ]

    period = f"{s.metric_months[0]}~{s.metric_months[-1]}" if s.metric_months else "N/A"
    return OpsReportPayload(
        report_title=f"SFE 성과 분석 보고서 ({asset.scenario})",
        source_module="sandbox",
        period_label=period,
        sections=sections,
        executive_summary=asset.dashboard_payload.insight_messages if asset.dashboard_payload else [],
    )


def territory_to_report_payload(asset: TerritoryResultAsset) -> OpsReportPayload:
    cov = asset.coverage_summary
    opt = asset.optimization_summary

    sections = [
        ReportSection(
            section_id="coverage_kpi",
            section_title="권역 커버리지 요약",
            section_type="kpi_cards",
            data={
                "cards": [
                    {"label": "전체 권역", "value": f"{cov.total_regions}개"},
                    {"label": "커버리지율", "value": f"{cov.coverage_rate:.0%}"},
                    {"label": "미커버 병원", "value": f"{cov.gap_hospitals}개"},
                    {"label": "담당자 수", "value": f"{opt.total_reps}명"},
                ]
            },
        ),
        ReportSection(
            section_id="region_table",
            section_title="권역별 실적",
            section_type="table",
            data={
                "columns": ["권역", "병원수", "총 매출", "평균 달성률", "방문수"],
                "rows": [
                    [z.region_key, str(z.hospital_count),
                     f"{z.total_sales:,.0f}",
                     f"{(z.avg_attainment or 0)*100:.1f}%",
                     str(z.total_visits)]
                    for z in sorted(asset.region_zones,
                                    key=lambda z: z.total_sales, reverse=True)
                ]
            }
        ),
        ReportSection(
            section_id="map_markers",
            section_title="지도 마커 데이터",
            section_type="map",
            data={
                "markers": [
                    {
                        "hospital_id": m.hospital_id,
                        "lat": m.coord.lat, "lng": m.coord.lng,
                        "color": m.marker_color, "size": m.marker_size,
                        "tooltip": m.tooltip,
                    }
                    for m in asset.markers
                ],
                "routes": [
                    {
                        "rep_id": r.rep_id,
                        "points": [
                            {"lat": p.coord.lat, "lng": p.coord.lng, "hosp": p.hospital_id}
                            for p in r.route_points
                        ]
                    }
                    for r in asset.routes
                ],
                "center": {"lat": 36.5, "lng": 127.8},
                "zoom": 7,
            },
            render_hint="leaflet map with markers and polylines"
        ),
    ]

    return OpsReportPayload(
        report_title="SFE 권역별 영업 성과 지도",
        source_module="territory",
        period_label=asset.map_contract.period_label,
        sections=sections,
    )


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


def build_territory_template_input(
    asset: TerritoryResultAsset,
    template_path: str,
    source_asset_path: str | None = None,
    crm_activity_path: str | None = None,
) -> BuilderInputStandard:
    markers = _territory_markers_to_payload(asset, crm_activity_path=crm_activity_path)
    routes = _territory_routes_to_payload(asset, crm_activity_path=crm_activity_path)
    payload_seed = {
        "mode": "routing",
        "auto_render": False,
        "markers": markers,
        "routes": routes,
    }
    reference = BuilderInputReference(
        template_key="territory_map",
        template_path=template_path,
        source_module="territory",
        asset_type=asset.asset_type,
        source_asset_path=source_asset_path,
        description="Territory result asset -> Spatial_Preview_260224 주입",
    )
    return BuilderInputStandard(
        template_key="territory_map",
        template_path=template_path,
        report_title=asset.map_contract.map_title,
        executive_summary=[
            f"전체 권역 {asset.coverage_summary.total_regions}개",
            f"커버리지율 {asset.coverage_summary.coverage_rate:.1%}",
            f"담당자 {asset.optimization_summary.total_reps}명",
        ],
        source_references=[reference],
        payload_seed=payload_seed,
        source_modules=["territory"],
    )


def build_prescription_template_input(
    template_path: str,
    summary_path: str,
    claim_validation_path: str,
    gap_report_path: str,
    hospital_trace_path: str,
    rep_kpi_path: str,
    source_asset_path: str | None = None,
) -> BuilderInputStandard:
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    claim_df = pd.read_excel(claim_validation_path)
    gap_df = pd.read_excel(gap_report_path)
    hospital_trace_df = pd.read_excel(hospital_trace_path)
    rep_kpi_df = pd.read_excel(rep_kpi_path)

    claim_df = claim_df.sort_values(["year_quarter", "tracked_amount"], ascending=[True, False])
    hospital_trace_df = hospital_trace_df.sort_values(
        ["year_quarter", "total_amount"], ascending=[True, False]
    )
    rep_kpi_df = rep_kpi_df.sort_values(["year_quarter", "total_amount"], ascending=[True, False])

    overview = {
        "standard_record_count": summary.get("standard_record_count", 0),
        "flow_record_count": summary.get("flow_record_count", 0),
        "gap_record_count": summary.get("gap_record_count", 0),
        "connected_hospital_count": summary.get("connected_hospital_count", 0),
        "quality_status": summary.get("quality_status", "unknown"),
        "quality_score": summary.get("quality_score", 0),
        "claim_validation_summary": summary.get("claim_validation_summary", {}),
    }
    payload_seed = {
        "company": "한결제약",
        "overview": overview,
        "claims": claim_df.to_dict(orient="records"),
        "gaps": gap_df.to_dict(orient="records"),
        "hospital_traces": hospital_trace_df.head(100).to_dict(orient="records"),
        "rep_kpis": rep_kpi_df.head(100).to_dict(orient="records"),
    }
    reference = BuilderInputReference(
        template_key="prescription_flow",
        template_path=template_path,
        source_module="prescription",
        asset_type="prescription_result_asset",
        source_asset_path=source_asset_path,
        description="Prescription validation outputs -> prescription_flow_template 주입",
    )
    claim_summary = overview["claim_validation_summary"]
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


def _territory_markers_to_payload(
    asset: TerritoryResultAsset,
    crm_activity_path: str | None = None,
) -> list[dict]:
    if crm_activity_path:
        crm_markers = _build_markers_from_crm(asset, crm_activity_path)
        if crm_markers:
            return crm_markers

    markers: list[dict] = []
    for row in asset.markers:
        insight_parts = [
            f"권역: {row.region_key}",
            f"세부권역: {row.sub_region_key or '-'}",
            f"방문: {int(row.total_visits or 0)}건",
        ]
        if row.attainment_rate is not None:
            insight_parts.append(f"달성률: {round(float(row.attainment_rate) * 100, 1)}%")
        markers.append(
            {
                "hospital_id": row.hospital_id,
                "hospital": (row.hospital_name or row.hospital_id).strip(),
                "rep": row.rep_id or "미지정",
                "lat": float(row.coord.lat),
                "lon": float(row.coord.lng),
                "sales": round(float(row.total_sales or 0.0), 2),
                "target": round(float(row.total_target or 0.0), 2),
                "insight": " | ".join(insight_parts),
                "region": row.region_key,
                "sub_region": row.sub_region_key,
                "month": None,
                "date": None,
            }
        )
    return markers


def _territory_routes_to_payload(
    asset: TerritoryResultAsset,
    crm_activity_path: str | None = None,
) -> list[dict]:
    if crm_activity_path:
        crm_routes = _build_routes_from_crm(crm_activity_path)
        if crm_routes:
            return crm_routes

    routes: list[dict] = []
    period_label = asset.map_contract.period_label or "AUTO"
    for idx, route in enumerate(asset.routes, start=1):
        coords = [
            {
                "seq": int(point.order),
                "hospital": point.hospital_id,
                "lat": float(point.coord.lat),
                "lon": float(point.coord.lng),
            }
            for point in route.route_points
        ]
        if not coords:
            continue
        routes.append(
            {
                "rep": route.rep_name or route.rep_id,
                "month": period_label,
                "date": f"{period_label}-{idx:02d}",
                "coords": coords,
            }
        )
    return routes


def _build_markers_from_crm(asset: TerritoryResultAsset, crm_activity_path: str) -> list[dict]:
    crm_df = pd.read_excel(crm_activity_path).reset_index(names="input_order")
    if crm_df.empty:
        return []

    crm_df["실행일"] = pd.to_datetime(crm_df["실행일"], errors="coerce")
    crm_df["기관위도"] = pd.to_numeric(crm_df["기관위도"], errors="coerce")
    crm_df["기관경도"] = pd.to_numeric(crm_df["기관경도"], errors="coerce")
    crm_df = crm_df.dropna(subset=["실행일", "영업사원명", "방문기관", "기관위도", "기관경도"]).copy()
    if crm_df.empty:
        return []

    crm_df["month"] = crm_df["실행일"].dt.strftime("%Y-%m")
    crm_df["date"] = crm_df["실행일"].dt.strftime("%Y-%m-%d")

    totals_by_hospital: dict[str, dict[str, object]] = {}
    for marker in asset.markers:
        name_key = str(marker.hospital_name or marker.hospital_id).strip()
        totals_by_hospital[name_key] = {
            "hospital_id": marker.hospital_id,
            "sales": round(float(marker.total_sales or 0.0), 2),
            "target": round(float(marker.total_target or 0.0), 2),
            "region": marker.region_key,
            "sub_region": marker.sub_region_key,
            "attainment_rate": marker.attainment_rate,
            "visits": int(marker.total_visits or 0),
        }

    markers: list[dict] = []
    for row in crm_df.itertuples(index=False):
        hospital_name = str(row.방문기관).strip()
        marker_meta = totals_by_hospital.get(hospital_name, {})
        attainment = marker_meta.get("attainment_rate")
        insight_parts = [
            f"권역: {marker_meta.get('region') or '-'}",
            f"세부권역: {marker_meta.get('sub_region') or '-'}",
        ]
        if attainment is not None:
            insight_parts.append(f"달성률: {round(float(attainment) * 100, 1)}%")
        markers.append(
            {
                "hospital_id": marker_meta.get("hospital_id") or hospital_name,
                "hospital": hospital_name,
                "rep": str(row.영업사원명).strip(),
                "month": str(row.month),
                "date": str(row.date),
                "lat": float(row.기관위도),
                "lon": float(row.기관경도),
                "sales": marker_meta.get("sales", 0.0),
                "target": marker_meta.get("target", 0.0),
                "insight": " | ".join(insight_parts),
                "region": marker_meta.get("region"),
                "sub_region": marker_meta.get("sub_region"),
                "seq": int(getattr(row, "input_order", 0)) + 1,
            }
        )
    return markers


def _build_routes_from_crm(crm_activity_path: str) -> list[dict]:
    crm_df = pd.read_excel(crm_activity_path).reset_index(names="input_order")
    if crm_df.empty:
        return []

    crm_df["실행일"] = pd.to_datetime(crm_df["실행일"], errors="coerce")
    crm_df["기관위도"] = pd.to_numeric(crm_df["기관위도"], errors="coerce")
    crm_df["기관경도"] = pd.to_numeric(crm_df["기관경도"], errors="coerce")
    crm_df = crm_df.dropna(subset=["실행일", "영업사원명", "방문기관", "기관위도", "기관경도"]).copy()
    if crm_df.empty:
        return []

    crm_df["month"] = crm_df["실행일"].dt.strftime("%Y-%m")
    crm_df["date"] = crm_df["실행일"].dt.strftime("%Y-%m-%d")

    routes: list[dict] = []
    for (rep_name, month, date), group in crm_df.groupby(["영업사원명", "month", "date"], sort=True):
        ordered = group.sort_values("input_order", kind="stable")
        seen_hospitals: set[str] = set()
        coords: list[dict] = []
        seq = 1
        for row in ordered.itertuples(index=False):
            hospital_name = str(row.방문기관).strip()
            if hospital_name in seen_hospitals:
                continue
            seen_hospitals.add(hospital_name)
            coords.append(
                {
                    "seq": seq,
                    "hospital": hospital_name,
                    "lat": float(row.기관위도),
                    "lon": float(row.기관경도),
                }
            )
            seq += 1
        if coords:
            routes.append(
                {
                    "rep": str(rep_name).strip(),
                    "month": str(month),
                    "date": str(date),
                    "coords": coords,
                }
            )
    return routes


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
    return {}


# ────────────────────────────────────────
# Layer 2: WebSlide Studio 세션
# ────────────────────────────────────────

def create_webslide_session(contents: list[dict]) -> WebSlideSession:
    """새 WebSlide 제작 세션 생성."""
    session = WebSlideSession(session_id=str(uuid.uuid4()))
    for c in contents:
        session.input_contents.append(WebSlideSlotContent(**c))
    return session


def advance_phase(session: WebSlideSession) -> WebSlideSession:
    """세션 단계를 다음으로 진행."""
    order = ["intake", "strategy", "blueprint", "build", "done"]
    idx = order.index(session.current_phase)
    if idx < len(order) - 1:
        session.current_phase = order[idx + 1]
    session.updated_at = datetime.now()
    return session
