"""
HTML Builder Service
Layer1: OPS Result Asset → 분석 보고 HTML 자동 생성
Layer2: WebSlide Architect 페르소나 세션 관리
"""

from modules.builder.schemas import (
    OpsReportPayload, ReportSection, WebSlideSession,
    WebSlideSlotContent, HtmlBuilderResultAsset,
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
