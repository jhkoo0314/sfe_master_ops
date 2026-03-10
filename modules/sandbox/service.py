"""
Sandbox Service - SandboxInputStandard → SandboxResultAsset 생성

핵심 로직:
  1. 도메인별 레코드를 hospital_id 기준으로 집계
  2. CRM × Sales × Target 조인 품질 계산
  3. 달성률(attainment_rate) 계산
  4. Territory/Builder handoff 후보 판단
  5. SandboxResultAsset 반환
"""

from collections import defaultdict
from typing import Optional

from modules.sandbox.schemas import (
    SandboxInputStandard,
    HospitalAnalysisRecord,
    AnalysisSummary,
    DomainQualitySummary,
    JoinQualitySummary,
    PlannedHandoffCandidate,
)
from modules.sandbox.templates import (
    PerformanceDashboardContract,
    SummaryCard,
    ChartSlot,
    TableSlot,
)
from result_assets.sandbox_result_asset import SandboxResultAsset, DashboardPayload
from common.exceptions import MissingResultAssetError


def build_sandbox_result_asset(
    input_std: SandboxInputStandard,
) -> SandboxResultAsset:
    """
    SandboxInputStandard를 받아 SandboxResultAsset을 생성한다.

    Args:
        input_std: OPS가 허용하고 도메인 Adapter가 변환한 표준 입력

    Returns:
        SandboxResultAsset

    Raises:
        MissingResultAssetError: 입력 데이터가 전혀 없는 경우
    """
    if not input_std.has_sales and not input_std.has_crm:
        raise MissingResultAssetError(
            "SandboxInputStandard에 CRM 또는 Sales 데이터가 없습니다."
        )

    # ── 1. hospital_id 기준 집계 버킷 ──────────────────
    # key: (hospital_id, metric_month)
    bucket: dict[tuple[str, str], HospitalAnalysisRecord] = {}

    def get_or_create(hosp_id: str, month: str) -> HospitalAnalysisRecord:
        key = (hosp_id, month)
        if key not in bucket:
            bucket[key] = HospitalAnalysisRecord(
                hospital_id=hosp_id,
                metric_month=month,
            )
        return bucket[key]

    # ── 2. CRM 집계 ────────────────────────────────────
    for r in input_std.crm_records:
        rec = get_or_create(r.hospital_id, r.metric_month)
        rec.total_visits += r.total_visits
        rec.detail_call_count += r.detail_call_count
        rec.has_crm = True

    # ── 3. Sales 집계 ──────────────────────────────────
    for r in input_std.sales_records:
        rec = get_or_create(r.hospital_id, r.metric_month)
        rec.total_sales += r.sales_amount
        rec.total_quantity += (r.sales_quantity or 0.0)
        rec.has_sales = True

    # ── 4. Target 집계 ─────────────────────────────────
    for r in input_std.target_records:
        hosp_id = r.hospital_id
        if not hosp_id:
            # 병원 단위 목표 아닌 경우 → rep 기준으로 배분 생략, metric_month만 집계
            # 단순히 월 수준에서 합산 (병원 단위 목표가 없으면 hospital 레코드에 붙이지 않음)
            continue
        rec = get_or_create(hosp_id, r.metric_month)
        rec.total_target += r.target_amount
        rec.has_target = True

    # ── 5. Prescription 집계 ──────────────────────────
    for r in input_std.prescription_records:
        rec = get_or_create(r.hospital_id, r.metric_month)
        rec.rx_amount += r.amount
        if r.is_complete:
            rec.rx_complete_flows += 1
        rec.has_rx = True

    # ── 6. 달성률 계산 ────────────────────────────────
    for rec in bucket.values():
        if rec.has_target and rec.total_target > 0:
            rec.attainment_rate = round(rec.total_sales / rec.total_target, 4)

    records = list(bucket.values())

    # ── 7. AnalysisSummary ────────────────────────────
    total_sales = sum(r.total_sales for r in records)
    total_target = sum(r.total_target for r in records)
    avg_attainment = None
    rated = [r.attainment_rate for r in records if r.attainment_rate is not None]
    if rated:
        avg_attainment = round(sum(rated) / len(rated), 4)

    unique_hospitals = {r.hospital_id for r in records}
    fully_joined = sum(1 for r in records if r.is_fully_joined)
    rx_linked = sum(1 for r in records if r.has_rx)
    months = sorted({r.metric_month for r in records})

    analysis_summary = AnalysisSummary(
        total_hospitals=len(unique_hospitals),
        total_months=len(months),
        total_sales_amount=round(total_sales, 0),
        total_target_amount=round(total_target, 0),
        avg_attainment_rate=avg_attainment,
        total_visits=sum(r.total_visits for r in records),
        fully_joined_hospitals=fully_joined,
        rx_linked_hospitals=rx_linked,
        metric_months=months,
    )

    # ── 8. DomainQualitySummary ───────────────────────
    crm_months = sorted({r.metric_month for r in input_std.crm_records})
    sales_months = sorted({r.metric_month for r in input_std.sales_records})
    domain_quality = DomainQualitySummary(
        crm_record_count=len(input_std.crm_records),
        sales_record_count=len(input_std.sales_records),
        target_record_count=len(input_std.target_records),
        rx_record_count=len(input_std.prescription_records),
        crm_unique_hospitals=len({r.hospital_id for r in input_std.crm_records}),
        sales_unique_hospitals=len({r.hospital_id for r in input_std.sales_records}),
        target_unique_reps=len({r.rep_id for r in input_std.target_records}),
        rx_unique_hospitals=len({r.hospital_id for r in input_std.prescription_records}),
        crm_months=crm_months,
        sales_months=sales_months,
    )

    # ── 9. JoinQualitySummary ─────────────────────────
    crm_hosps = {r.hospital_id for r in input_std.crm_records}
    sales_hosps = {r.hospital_id for r in input_std.sales_records}
    crm_and_sales = crm_hosps & sales_hosps
    all_three = {r.hospital_id for r in records if r.is_fully_joined}
    rx_hosps = {r.hospital_id for r in input_std.prescription_records}

    crm_sales_rate = round(len(crm_and_sales) / len(crm_hosps), 4) if crm_hosps else 0.0
    full_join_rate = round(len(all_three) / len(crm_hosps), 4) if crm_hosps else 0.0

    join_quality = JoinQualitySummary(
        hospitals_with_crm_and_sales=len(crm_and_sales),
        hospitals_with_all_three=len(all_three),
        hospitals_with_rx_added=len(rx_hosps & crm_hosps),
        crm_sales_join_rate=crm_sales_rate,
        full_join_rate=full_join_rate,
        orphan_sales_hospitals=len(sales_hosps - crm_hosps),
        orphan_crm_hospitals=len(crm_hosps - sales_hosps),
    )

    # ── 10. Handoff 후보 판단 ─────────────────────────
    handoff_candidates = _evaluate_handoff_candidates(
        join_quality=join_quality,
        analysis_summary=analysis_summary,
        has_rx=input_std.has_prescription,
    )

    # ── 11. 리포트 템플릿 계약 충족 (Template Injection) ──
    # [Template-Driven Analysis]
    # 템플릿 규격에 명시된 metric_key를 읽어 자동으로 데이터를 주입한다.
    template = PerformanceDashboardContract.get_standard_template()
    template.period_label = f"{analysis_summary.metric_months[0]}~{analysis_summary.metric_months[-1]}" if analysis_summary.metric_months else "N/A"
    
    report_contract = _inject_data_to_template(template, analysis_summary, records)

    return SandboxResultAsset(
        scenario=input_std.scenario,
        metric_months=months,
        analysis_summary=analysis_summary,
        domain_quality=domain_quality,
        join_quality=join_quality,
        hospital_records=records[:200],
        handoff_candidates=handoff_candidates,
        dashboard_payload=DashboardPayload(
            layout_type="dynamic_dashboard",
            chart_data=report_contract.main_trend_chart.dict() if report_contract.main_trend_chart else {},
            top_performers=[{"name": row[0], "val": row[1]} for row in (report_contract.top_efficiency_hospitals.rows if report_contract.top_efficiency_hospitals else [])],
            insight_messages=report_contract.executive_summary
        ),
        source_crm_asset_id=input_std.source_crm_asset_id,
        source_rx_asset_id=input_std.source_rx_asset_id,
    )


def _inject_data_to_template(
    contract: PerformanceDashboardContract,
    summary: AnalysisSummary,
    records: list[HospitalAnalysisRecord]
) -> PerformanceDashboardContract:
    """
    고도화된 동적 주입기:
    템플릿 객체의 각 카드를 순회하며 metric_key에 맞는 데이터를 자동으로 찾아 채움.
    이제 새로운 템플릿(py)만 추가하면 이 로직이 자동으로 분석툴을 찾아 매핑함.
    """
    
    # 1. Summary Cards 자동 채우기
    for card in contract.summary_cards:
        if not card.metric_key:
            continue
            
        # AnalysisSummary에서 해당 키의 값을 추출
        raw_val = getattr(summary, card.metric_key, None)
        
        # 값의 성격에 따른 자동 포맷팅
        if raw_val is None:
            card.value = "N/A"
        elif "amount" in card.metric_key:
            card.value = f"{raw_val / 10000:,.0f}만원"
        elif "rate" in card.metric_key:
            card.value = f"{raw_val * 100:.1f}%"
            card.status = "good" if raw_val >= 0.9 else "warning"
        else:
            card.value = f"{raw_val:,}"

    # 2. 인사이트 자동 생성 (조건별)
    if (summary.avg_attainment_rate or 0) < 0.8:
        contract.executive_summary.append("⚠️ 전체 달성률 80% 미달로 타겟팅 재검토 권장.")
    if summary.rx_linked_hospitals > 0:
        contract.executive_summary.append(f"🔗 {summary.rx_linked_hospitals}개 병원의 처방-출고 연결성 확인됨.")

    # 3. 테이블 자동 채우기 (고정 로직 - 추후 고도화 가능)
    sorted_recs = sorted(records, key=lambda x: (x.attainment_rate or 0), reverse=True)
    contract.top_efficiency_hospitals = TableSlot(
        title="최고 달성률 병원 TOP 5",
        columns=["ID", "달성률", "매출"],
        rows=[[r.hospital_id, f"{(r.attainment_rate or 0)*100:.1f}%", f"{r.total_sales:,.0f}"] for r in sorted_recs[:5]]
    )

    return contract


def _evaluate_handoff_candidates(
    join_quality: JoinQualitySummary,
    analysis_summary: AnalysisSummary,
    has_rx: bool,
) -> list[PlannedHandoffCandidate]:
    """Territory와 Builder로의 handoff 가능 여부 판단."""
    candidates = []

    # Territory handoff 조건:
    # - CRM × Sales 조인율 60% 이상
    # - 병원 수 10개 이상
    territory_eligible = (
        join_quality.crm_sales_join_rate >= 0.6
        and analysis_summary.total_hospitals >= 10
    )
    candidates.append(PlannedHandoffCandidate(
        module="territory",
        condition="CRM×Sales 조인율 ≥ 60% AND 병원 수 ≥ 10",
        is_eligible=territory_eligible,
        blocking_reason=None if territory_eligible else (
            f"조인율 {join_quality.crm_sales_join_rate:.0%} "
            f"또는 병원 수 {analysis_summary.total_hospitals}개 부족"
        ),
    ))

    # Builder handoff 조건:
    # - analysis_summary 존재 (매출/CRM 중 하나라도)
    # - 1개 월 이상 분석
    builder_eligible = analysis_summary.total_months >= 1
    candidates.append(PlannedHandoffCandidate(
        module="builder",
        condition="분석 월 ≥ 1개월",
        is_eligible=builder_eligible,
        blocking_reason=None if builder_eligible else "분석 가능한 월 데이터 없음",
    ))

    return candidates
