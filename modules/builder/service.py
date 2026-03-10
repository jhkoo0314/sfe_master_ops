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

from common.company_runtime import get_active_company_name
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
from result_assets.crm_result_asset import CrmResultAsset
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


def _normalize_behavior_key(raw_key: str) -> str:
    key = str(raw_key or "").strip()
    mapping = {
        "PT": "PT",
        "제품설명": "PT",
        "Demo": "Demo",
        "시연": "Demo",
        "Closing": "Closing",
        "클로징": "Closing",
        "Needs": "Needs",
        "니즈환기": "Needs",
        "FaceToFace": "FaceToFace",
        "대면": "FaceToFace",
        "방문": "FaceToFace",
        "Contact": "Contact",
        "컨택": "Contact",
        "전화": "Contact",
        "Access": "Access",
        "접근": "Access",
        "Feedback": "Feedback",
        "피드백": "Feedback",
    }
    return mapping.get(key, key)


def _empty_behavior_map() -> dict[str, float]:
    return {
        "PT": 0.0,
        "Demo": 0.0,
        "Closing": 0.0,
        "Needs": 0.0,
        "FaceToFace": 0.0,
        "Contact": 0.0,
        "Access": 0.0,
        "Feedback": 0.0,
    }


def _calc_pearson(values_x: list[float], values_y: list[float]) -> float:
    if len(values_x) != len(values_y) or len(values_x) < 2:
        return 0.0
    mean_x = sum(values_x) / len(values_x)
    mean_y = sum(values_y) / len(values_y)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(values_x, values_y))
    den_x = sum((x - mean_x) ** 2 for x in values_x) ** 0.5
    den_y = sum((y - mean_y) ** 2 for y in values_y) ** 0.5
    if den_x == 0 or den_y == 0:
        return 0.0
    return round(max(-1.0, min(1.0, num / (den_x * den_y))), 2)


def _build_corr_matrix(rows: list[dict], metrics: list[str]) -> dict[str, dict[str, float]]:
    matrix: dict[str, dict[str, float]] = {}
    for left in metrics:
        matrix[left] = {}
        left_values = [float(row.get(left, 0.0) or 0.0) for row in rows]
        for right in metrics:
            if left == right:
                matrix[left][right] = 1.0
                continue
            right_values = [float(row.get(right, 0.0) or 0.0) for row in rows]
            matrix[left][right] = _calc_pearson(left_values, right_values)
    return matrix


def _amplify_matrix(
    matrix: dict[str, dict[str, float]],
    factor: float = 1.18,
) -> dict[str, dict[str, float]]:
    tuned: dict[str, dict[str, float]] = {}
    for left, row in matrix.items():
        tuned[left] = {}
        for right, value in row.items():
            if left == right:
                tuned[left][right] = 1.0
            else:
                tuned[left][right] = round(max(-1.0, min(1.0, value * factor)), 2)
    return tuned


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
    flow_records_path: str,
    gap_report_path: str,
    hospital_trace_path: str,
    rep_kpi_path: str,
    source_asset_path: str | None = None,
) -> BuilderInputStandard:
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    claim_df = pd.read_excel(claim_validation_path)
    flow_df = pd.read_excel(flow_records_path)
    gap_df = pd.read_excel(gap_report_path)
    hospital_trace_df = pd.read_excel(hospital_trace_path)
    rep_kpi_df = pd.read_excel(rep_kpi_path)

    flow_df["metric_month"] = flow_df["metric_month"].astype(str)
    flow_df["year"] = flow_df["metric_month"].str[:4]
    flow_df["month"] = flow_df["metric_month"].str[:4] + "-" + flow_df["metric_month"].str[4:6]

    claim_df = claim_df.sort_values(["year_quarter", "tracked_amount"], ascending=[True, False])
    hospital_trace_df = hospital_trace_df.sort_values(
        ["year_quarter", "total_amount"], ascending=[True, False]
    )
    rep_kpi_df = rep_kpi_df.sort_values(["year_quarter", "total_amount"], ascending=[True, False])

    flow_month_map_quarter: dict[tuple[str, str, str, str], list[str]] = (
        flow_df.groupby(["year_quarter", "rep_name", "hospital_id", "product_name"])["month"]
        .agg(lambda s: sorted(set(str(v) for v in s if pd.notna(v))))
        .to_dict()
    )
    flow_month_map_year: dict[tuple[str, str, str, str], list[str]] = (
        flow_df.groupby(["year", "rep_name", "hospital_id", "product_name"])["month"]
        .agg(lambda s: sorted(set(str(v) for v in s if pd.notna(v))))
        .to_dict()
    )
    claim_records = claim_df.to_dict(orient="records")
    for row in claim_records:
        period_type = str(row.get("period_type", "quarter"))
        year = str(row.get("year") or "")
        row["year"] = year
        if period_type == "month":
            year_month = str(row.get("year_month") or row.get("period_value") or "")
            months = [year_month] if year_month else []
        elif period_type == "year":
            months = flow_month_map_year.get(
                (year, str(row["rep_name"]), str(row["hospital_id"]), str(row["product_name"])),
                [],
            )
        else:
            year_quarter = str(row.get("year_quarter") or row.get("period_value") or "")
            months = flow_month_map_quarter.get(
                (year_quarter, str(row["rep_name"]), str(row["hospital_id"]), str(row["product_name"])),
                [],
            )
        row["active_months"] = months
        if not row.get("year"):
            row["year"] = str(row.get("year_quarter", "")).split("-")[0]
    trace_records = hospital_trace_df.to_dict(orient="records")
    for row in trace_records:
        quarter = str(row.get("year_quarter", ""))
        row["year"] = quarter.split("-")[0] if "-" in quarter else str(row.get("year") or "")
    rep_kpi_records = rep_kpi_df.to_dict(orient="records")
    for row in rep_kpi_records:
        quarter = str(row.get("year_quarter", ""))
        row["year"] = quarter.split("-")[0] if "-" in quarter else str(row.get("year") or "")

    connected_flow_df = flow_df[flow_df["flow_status"] == "connected"].copy()
    connected_flow_df["month"] = connected_flow_df["month"].astype(str)
    connected_flow_df["year"] = connected_flow_df["year"].astype(str)
    trace_group_keys = ["rep_name", "hospital_id", "hospital_name", "product_name"]

    def _build_trace_summary(period_type: str, period_column: str) -> list[dict]:
        grouped = (
            connected_flow_df.groupby([period_column, *trace_group_keys], dropna=False)
            .agg(
                total_amount=("total_amount", "sum"),
                pharmacy_count=("pharmacy_id", "nunique"),
                wholesaler_count=("wholesaler_id", "nunique"),
            )
            .reset_index()
        )
        if grouped.empty:
            return []
        grouped = grouped.rename(columns={period_column: "period_value"})
        grouped["period_type"] = period_type
        grouped["year"] = grouped["period_value"].astype(str).str[:4]
        grouped["period_label"] = grouped["period_value"].astype(str)
        return grouped.to_dict(orient="records")

    trace_summary_records = []
    trace_summary_records.extend(_build_trace_summary("month", "month"))
    trace_summary_records.extend(_build_trace_summary("quarter", "year_quarter"))
    trace_summary_records.extend(_build_trace_summary("year", "year"))

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
        "company": get_active_company_name(),
        "overview": overview,
        "claims": claim_records,
        "gaps": gap_df.to_dict(orient="records"),
        "hospital_traces": trace_summary_records,
        "rep_kpis": rep_kpi_records,
        "download_files": {
            "claim_validation": Path(claim_validation_path).name,
            "flow_records": Path(flow_records_path).name,
            "gap_records": Path(gap_report_path).name,
            "hospital_traces": Path(hospital_trace_path).name,
            "rep_kpis": Path(rep_kpi_path).name,
        },
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


def build_crm_template_input(
    asset: CrmResultAsset,
    template_path: str,
    summary_path: str,
    company_master_path: str | None = None,
    source_asset_path: str | None = None,
) -> BuilderInputStandard:
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))

    branch_name_map: dict[str, str] = {}
    if company_master_path and Path(company_master_path).exists():
        company_df = pd.read_excel(company_master_path)
        branch_id_col = "branch_id" if "branch_id" in company_df.columns else None
        branch_name_col = "branch_name" if "branch_name" in company_df.columns else None
        rep_id_col = "rep_id" if "rep_id" in company_df.columns else None
        if branch_id_col and branch_name_col:
            branch_name_map = (
                company_df[[branch_id_col, branch_name_col]]
                .dropna()
                .drop_duplicates(subset=[branch_id_col])
                .set_index(branch_id_col)[branch_name_col]
                .astype(str)
                .to_dict()
            )
        elif rep_id_col and branch_name_col:
            branch_name_map = (
                company_df[[rep_id_col, branch_name_col]]
                .dropna()
                .drop_duplicates(subset=[rep_id_col])
                .set_index(rep_id_col)[branch_name_col]
                .astype(str)
                .to_dict()
            )

    monthly_rows = []
    for row in asset.monthly_kpi:
        detail_rate = round(row.detail_call_count / max(row.total_visits, 1), 4)
        monthly_rows.append(
            {
                "metric_month": row.metric_month,
                "month_label": f"{str(row.metric_month)[:4]}-{str(row.metric_month)[4:6]}",
                "total_visits": row.total_visits,
                "total_reps_active": row.total_reps_active,
                "total_hospitals_visited": row.total_hospitals_visited,
                "avg_visits_per_rep": row.avg_visits_per_rep,
                "detail_call_count": row.detail_call_count,
                "detail_call_rate": detail_rate,
            }
        )

    rep_rows: list[dict] = []
    for profile in asset.behavior_profiles:
        active_month_count = len(profile.active_months)
        activity_diversity = len(profile.top_activity_types)
        hir_proxy = round(
            min(
                100.0,
                profile.detail_call_rate * 55
                + min(profile.avg_visits_per_hospital, 80) * 0.35
                + activity_diversity * 8
                + active_month_count * 1.1,
            ),
            1,
        )
        bcr_proxy = round(min(100.0, (active_month_count / 12) * 100), 1)
        reach_proxy = round(min(100.0, profile.unique_hospitals * 4.5), 1)
        intensity_proxy = round(min(100.0, profile.avg_visits_per_hospital * 1.4), 1)
        branch_name = branch_name_map.get(profile.branch_id) or profile.branch_id
        rep_rows.append(
            {
                "rep_id": profile.rep_id,
                "rep_name": profile.rep_name,
                "branch_id": profile.branch_id,
                "branch_name": branch_name,
                "total_visits": profile.total_visits,
                "unique_hospitals": profile.unique_hospitals,
                "avg_visits_per_hospital": profile.avg_visits_per_hospital,
                "detail_call_rate": round(profile.detail_call_rate * 100, 1),
                "top_activity_types": profile.top_activity_types,
                "active_month_count": active_month_count,
                "hir_proxy": hir_proxy,
                "bcr_proxy": bcr_proxy,
                "reach_proxy": reach_proxy,
                "intensity_proxy": intensity_proxy,
            }
        )

    rep_df = pd.DataFrame(rep_rows)
    branch_rows: list[dict] = []
    if not rep_df.empty:
        branch_summary = rep_df.groupby(["branch_id", "branch_name"], as_index=False).agg(
            rep_count=("rep_id", "nunique"),
            total_visits=("total_visits", "sum"),
            unique_hospitals=("unique_hospitals", "sum"),
            avg_detail_call_rate=("detail_call_rate", "mean"),
            avg_hir_proxy=("hir_proxy", "mean"),
            avg_bcr_proxy=("bcr_proxy", "mean"),
        )
        branch_rows = branch_summary.sort_values("total_visits", ascending=False).to_dict(orient="records")

    top_reps = sorted(rep_rows, key=lambda row: row["hir_proxy"], reverse=True)[:12]
    coaching_watchlist = sorted(
        rep_rows,
        key=lambda row: (row["hir_proxy"], row["bcr_proxy"], -row["total_visits"]),
    )[:12]

    payload_seed = {
        "company": get_active_company_name(),
        "overview": {
            "quality_status": summary.get("quality_status", "unknown"),
            "quality_score": summary.get("quality_score", 0),
            "crm_activity_count": summary.get("crm_activity_count", 0),
            "unique_reps": asset.activity_context.unique_reps,
            "unique_hospitals": asset.activity_context.unique_hospitals,
            "unique_branches": asset.activity_context.unique_branches,
            "hospital_mapping_rate": round(asset.mapping_quality.hospital_mapping_rate * 100, 1),
            "crm_unmapped_count": summary.get("crm_unmapped_count", 0),
        },
        "logic_reference": {
            "core_kpis": ["HIR", "RTR", "BCR", "PHR"],
            "ops_kpis": ["NAR", "AHS", "PV"],
            "result_kpis": ["FGR", "PI", "TRG", "SWR"],
            "note": "현재 CRM 자산에는 완성 KPI가 없어서, 본 보고서는 raw 기반 프록시 지표와 실제 집계 지표를 함께 보여줍니다.",
        },
        "activity_context": asset.activity_context.model_dump(mode="json"),
        "mapping_quality": asset.mapping_quality.model_dump(mode="json"),
        "monthly_kpi": monthly_rows,
        "rep_profiles": rep_rows,
        "branch_summary": branch_rows,
        "top_reps": top_reps,
        "coaching_watchlist": coaching_watchlist,
    }
    reference = BuilderInputReference(
        template_key="crm_coaching",
        template_path=template_path,
        source_module="crm",
        asset_type=asset.asset_type,
        source_asset_path=source_asset_path,
        description="CRM result asset -> crm coaching template 주입",
    )
    return BuilderInputStandard(
        template_key="crm_coaching",
        template_path=template_path,
        report_title="CRM 행동 코칭 리포트",
        executive_summary=[
            f"CRM 활동 {summary.get('crm_activity_count', 0):,}건",
            f"담당자 {asset.activity_context.unique_reps}명 / 병원 {asset.activity_context.unique_hospitals}개",
            f"병원 매핑률 {asset.mapping_quality.hospital_mapping_rate:.1%}",
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

    if builder_input.template_key == "crm_coaching":
        return BuilderPayloadStandard(
            template_key="crm_coaching",
            template_path=builder_input.template_path,
            report_title=builder_input.report_title,
            payload=builder_input.payload_seed,
            source_modules=builder_input.source_modules,
            output_name="crm_coaching_preview.html",
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
    if builder_payload.template_key == "crm_coaching":
        return {
            "monthly_kpi_count": len(payload.get("monthly_kpi", [])),
            "rep_profile_count": len(payload.get("rep_profiles", [])),
            "watchlist_count": len(payload.get("coaching_watchlist", [])),
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
