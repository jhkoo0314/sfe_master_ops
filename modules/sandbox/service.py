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
    template_payload = _build_report_template_payload(
        input_std=input_std,
        analysis_summary=analysis_summary,
        domain_quality=domain_quality,
        join_quality=join_quality,
    )

    return SandboxResultAsset(
        scenario=input_std.scenario,
        metric_months=months,
        analysis_summary=analysis_summary,
        domain_quality=domain_quality,
        join_quality=join_quality,
        hospital_records=records,
        handoff_candidates=handoff_candidates,
        dashboard_payload=DashboardPayload(
            layout_type="dynamic_dashboard",
            chart_data=report_contract.main_trend_chart.dict() if report_contract.main_trend_chart else {},
            top_performers=[{"name": row[0], "val": row[1]} for row in (report_contract.top_efficiency_hospitals.rows if report_contract.top_efficiency_hospitals else [])],
            insight_messages=report_contract.executive_summary,
            template_payload=template_payload,
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


def _build_report_template_payload(
    input_std: SandboxInputStandard,
    analysis_summary: AnalysisSummary,
    domain_quality: DomainQualitySummary,
    join_quality: JoinQualitySummary,
) -> dict:
    months = sorted(input_std.metric_months)
    month_index = {month: idx for idx, month in enumerate(months[:12])}

    rep_meta: dict[str, dict[str, str]] = {}
    rep_month: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(lambda: {
        "sales": 0.0,
        "target": 0.0,
        "visits": 0.0,
        "detail_calls": 0.0,
        "active_days": 0.0,
        "next_actions": 0.0,
        "weighted_sum": 0.0,
        "weighted_count": 0.0,
        "sentiment_sum": 0.0,
        "sentiment_count": 0.0,
        "quality_sum": 0.0,
        "quality_count": 0.0,
        "impact_sum": 0.0,
        "impact_count": 0.0,
    }))
    rep_product: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {
        "product_name": None,
        "sales": 0.0,
        "target": 0.0,
        "monthly_sales": defaultdict(float),
        "monthly_target": defaultdict(float),
    }))
    rep_hospital_sales: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for row in input_std.crm_records:
        rep_meta.setdefault(row.rep_id, {
            "rep_name": row.rep_name or row.rep_id,
            "branch_name": row.branch_name or row.branch_id or "UNASSIGNED",
            "branch_id": row.branch_id or "UNASSIGNED",
        })
        bucket = rep_month[row.rep_id][row.metric_month]
        bucket["visits"] += row.total_visits
        bucket["detail_calls"] += row.detail_call_count
        bucket["active_days"] += row.active_day_count
        bucket["next_actions"] += row.next_action_count
        if row.avg_weighted_activity_score is not None:
            bucket["weighted_sum"] += row.avg_weighted_activity_score
            bucket["weighted_count"] += 1
        if row.avg_sentiment_score is not None:
            bucket["sentiment_sum"] += row.avg_sentiment_score
            bucket["sentiment_count"] += 1
        if row.avg_quality_factor is not None:
            bucket["quality_sum"] += row.avg_quality_factor
            bucket["quality_count"] += 1
        if row.avg_impact_factor is not None:
            bucket["impact_sum"] += row.avg_impact_factor
            bucket["impact_count"] += 1

    for row in input_std.sales_records:
        rep_meta.setdefault(row.rep_id, {
            "rep_name": row.rep_name or row.rep_id,
            "branch_name": row.branch_name or row.branch_id or "UNASSIGNED",
            "branch_id": row.branch_id or "UNASSIGNED",
        })
        rep_month[row.rep_id][row.metric_month]["sales"] += row.sales_amount
        rep_product[row.rep_id][row.product_id]["product_name"] = row.product_name or row.product_id
        rep_product[row.rep_id][row.product_id]["sales"] += row.sales_amount
        rep_product[row.rep_id][row.product_id]["monthly_sales"][row.metric_month] += row.sales_amount
        rep_hospital_sales[row.rep_id][row.hospital_id] += row.sales_amount

    for row in input_std.target_records:
        rep_meta.setdefault(row.rep_id, {
            "rep_name": row.rep_name or row.rep_id,
            "branch_name": row.branch_name or row.branch_id or "UNASSIGNED",
            "branch_id": row.branch_id or "UNASSIGNED",
        })
        rep_month[row.rep_id][row.metric_month]["target"] += row.target_amount
        rep_product[row.rep_id][row.product_id]["product_name"] = row.product_name or row.product_id
        rep_product[row.rep_id][row.product_id]["target"] += row.target_amount
        rep_product[row.rep_id][row.product_id]["monthly_target"][row.metric_month] += row.target_amount

    def month_series(metric_map: dict[str, float]) -> list[float]:
        values = [0.0] * 12
        for month, value in metric_map.items():
            idx = month_index.get(month)
            if idx is not None:
                values[idx] = round(float(value), 0)
        return values

    def calc_gini(values: list[float]) -> float:
        points = sorted(float(v) for v in values if float(v) > 0)
        if not points:
            return 0.0
        total = sum(points)
        n = len(points)
        weighted = sum((idx + 1) * value for idx, value in enumerate(points))
        return round((2 * weighted) / (n * total) - (n + 1) / n, 4)

    branches: dict[str, dict] = defaultdict(lambda: {"members": []})
    total_prod_analysis: dict[str, dict] = {}
    products = set()

    for rep_id, month_stats in rep_month.items():
        meta = rep_meta.get(rep_id, {
            "rep_name": rep_id,
            "branch_name": "UNASSIGNED",
            "branch_id": "UNASSIGNED",
        })
        monthly_actual = month_series({month: vals["sales"] for month, vals in month_stats.items()})
        monthly_target = month_series({month: vals["target"] for month, vals in month_stats.items()})
        total_actual = sum(monthly_actual)
        total_target = sum(monthly_target)
        total_visits = sum(vals["visits"] for vals in month_stats.values())
        total_detail_calls = sum(vals["detail_calls"] for vals in month_stats.values())
        total_active_days = sum(vals["active_days"] for vals in month_stats.values())
        total_next_actions = sum(vals["next_actions"] for vals in month_stats.values())
        weighted_sum = sum(vals["weighted_sum"] for vals in month_stats.values())
        weighted_count = sum(vals["weighted_count"] for vals in month_stats.values())
        sentiment_sum = sum(vals["sentiment_sum"] for vals in month_stats.values())
        sentiment_count = sum(vals["sentiment_count"] for vals in month_stats.values())
        quality_sum = sum(vals["quality_sum"] for vals in month_stats.values())
        quality_count = sum(vals["quality_count"] for vals in month_stats.values())
        impact_sum = sum(vals["impact_sum"] for vals in month_stats.values())
        impact_count = sum(vals["impact_count"] for vals in month_stats.values())

        hir = round(((weighted_sum / weighted_count) * 55.0) if weighted_count else ((total_detail_calls / max(total_visits, 1)) * 100.0), 1)
        rtr = round(((sentiment_sum / sentiment_count) * 100.0) if sentiment_count else 0.0, 1)
        bcr = round((total_active_days / max(len(months) * 20, 1)) * 100.0, 1)
        phr = round((total_next_actions / max(total_visits, 1)) * 100.0, 1)
        pi = round((total_actual / total_target) * 100.0, 1) if total_target > 0 else 0.0
        prev_sales = monthly_actual[max(len(months) - 2, 0)] if len(months) >= 2 else 0.0
        cur_sales = monthly_actual[max(len(months) - 1, 0)] if months else 0.0
        fgr = round(((cur_sales - prev_sales) / prev_sales) * 100.0, 1) if prev_sales > 0 else 0.0
        efficiency = round(total_actual / max(total_visits, 1), 0)
        sustainability = round(min(100.0, (bcr * 0.4) + (phr * 0.35) + (max(pi, 0.0) * 0.25)), 1)
        gini = calc_gini(list(rep_hospital_sales.get(rep_id, {}).values()))

        product_rows = []
        for product_id, prod in sorted(rep_product.get(rep_id, {}).items(), key=lambda item: float(item[1]["sales"]), reverse=True):
            product_name = str(prod["product_name"] or product_id)
            products.add(product_name)
            prod_monthly_actual = month_series(prod["monthly_sales"])
            prod_monthly_target = month_series(prod["monthly_target"])
            prod_total_actual = sum(prod_monthly_actual)
            prev_prod = prod_monthly_actual[max(len(months) - 2, 0)] if len(months) >= 2 else 0.0
            cur_prod = prod_monthly_actual[max(len(months) - 1, 0)] if months else 0.0
            growth = round(((cur_prod - prev_prod) / prev_prod) * 100.0, 1) if prev_prod > 0 else 0.0
            product_rows.append({
                "name": product_name,
                "ms": round((prod_total_actual / max(total_actual, 1)) * 100.0, 1) if total_actual > 0 else 0.0,
                "growth": growth,
            })
            total_row = total_prod_analysis.setdefault(product_name, {
                "achieve": 0.0,
                "avg": {},
                "monthly_actual": [0.0] * 12,
                "monthly_target": [0.0] * 12,
            })
            for idx in range(12):
                total_row["monthly_actual"][idx] += prod_monthly_actual[idx]
                total_row["monthly_target"][idx] += prod_monthly_target[idx]

        if pi >= 105:
            coach_scenario = "Lead Driver"
            coach_action = "실적 상위 흐름이 확인됩니다. 핵심 품목 확대와 신규 병원 전개를 병행하세요."
        elif pi >= 95:
            coach_scenario = "Growth Builder"
            coach_action = "안정 구간입니다. 방문 주기 유지와 상세콜 전환률 개선으로 초과 달성을 노리세요."
        else:
            coach_scenario = "Recovery Focus"
            coach_action = "목표 미달 병원 중심으로 활동 밀도와 차기액션 이행률을 먼저 끌어올리세요."

        member = {
            "rep_id": rep_id,
            "성명": str(meta["rep_name"]),
            "HIR": round(min(100.0, max(0.0, hir)), 1),
            "RTR": round(min(100.0, max(0.0, rtr)), 1),
            "BCR": round(min(100.0, max(0.0, bcr)), 1),
            "PHR": round(min(100.0, max(0.0, phr)), 1),
            "PI": pi,
            "FGR": fgr,
            "처방금액": round(total_actual, 0),
            "목표금액": round(total_target, 0),
            "efficiency": efficiency,
            "sustainability": sustainability,
            "gini": gini,
            "coach_scenario": coach_scenario,
            "coach_action": coach_action,
            "shap": {
                "PT": round((impact_sum / impact_count), 2) if impact_count else 0.0,
                "시연": round((quality_sum / quality_count), 2) if quality_count else 0.0,
                "클로징": round((total_detail_calls / max(total_visits, 1)), 2),
                "니즈환기": round((total_visits / max(len(months) * 30, 1)), 2),
                "대면": round((total_active_days / max(len(months) * 20, 1)), 2),
                "컨택": round((total_next_actions / max(total_visits, 1)), 2),
                "접근": round((sentiment_sum / sentiment_count), 2) if sentiment_count else 0.0,
                "피드백": round((weighted_sum / weighted_count), 2) if weighted_count else 0.0,
            },
            "prod_matrix": product_rows[:8] if product_rows else [{"name": "NO_PRODUCT", "ms": 0.0, "growth": 0.0}],
            "monthly_actual": monthly_actual,
            "monthly_target": monthly_target,
        }
        branches[str(meta["branch_name"])]["members"].append(member)

    all_members = []
    for branch_name, branch in branches.items():
        members = branch["members"]
        members.sort(key=lambda item: item["처방금액"], reverse=True)
        for idx, member in enumerate(members, start=1):
            member["지점순위"] = idx
            all_members.append(member)
        branch_actual = [sum(member["monthly_actual"][i] for member in members) for i in range(12)]
        branch_target = [sum(member["monthly_target"][i] for member in members) for i in range(12)]
        branch["avg"] = {
            "HIR": round(sum(member["HIR"] for member in members) / len(members), 1) if members else 0.0,
            "RTR": round(sum(member["RTR"] for member in members) / len(members), 1) if members else 0.0,
            "BCR": round(sum(member["BCR"] for member in members) / len(members), 1) if members else 0.0,
            "PHR": round(sum(member["PHR"] for member in members) / len(members), 1) if members else 0.0,
            "PI": round(sum(member["PI"] for member in members) / len(members), 1) if members else 0.0,
            "FGR": round(sum(member["FGR"] for member in members) / len(members), 1) if members else 0.0,
        }
        branch["achieve"] = round((sum(branch_actual) / sum(branch_target)) * 100.0, 1) if sum(branch_target) > 0 else 0.0
        branch["monthly_actual"] = branch_actual
        branch["monthly_target"] = branch_target
        branch["analysis"] = {"importance": {}, "correlation": {}, "adj_correlation": {}, "ccf": []}
        branch["prod_analysis"] = {}

    total_monthly_actual = [sum(member["monthly_actual"][i] for member in all_members) for i in range(12)]
    total_monthly_target = [sum(member["monthly_target"][i] for member in all_members) for i in range(12)]
    total_avg = {
        "HIR": round(sum(member["HIR"] for member in all_members) / len(all_members), 1) if all_members else 0.0,
        "RTR": round(sum(member["RTR"] for member in all_members) / len(all_members), 1) if all_members else 0.0,
        "BCR": round(sum(member["BCR"] for member in all_members) / len(all_members), 1) if all_members else 0.0,
        "PHR": round(sum(member["PHR"] for member in all_members) / len(all_members), 1) if all_members else 0.0,
        "PI": round(sum(member["PI"] for member in all_members) / len(all_members), 1) if all_members else 0.0,
        "FGR": round(sum(member["FGR"] for member in all_members) / len(all_members), 1) if all_members else 0.0,
    }

    for product_id, total_row in total_prod_analysis.items():
        actual_sum = sum(total_row["monthly_actual"])
        target_sum = sum(total_row["monthly_target"])
        total_row["achieve"] = round((actual_sum / target_sum) * 100.0, 1) if target_sum > 0 else 0.0
        total_row["avg"] = total_avg
        total_row["monthly_actual"] = [round(v, 0) for v in total_row["monthly_actual"]]
        total_row["monthly_target"] = [round(v, 0) for v in total_row["monthly_target"]]

    missing_data = []
    if join_quality.orphan_sales_hospitals > 0:
        missing_data.append({"지점": "OPS", "성명": "UNMAPPED", "품목": "orphan_sales_hospitals"})
    if join_quality.orphan_crm_hospitals > 0:
        missing_data.append({"지점": "OPS", "성명": "UNMAPPED", "품목": "orphan_crm_hospitals"})

    integrity_score = round(
        min(
            100.0,
            (join_quality.crm_sales_join_rate * 50.0)
            + (join_quality.full_join_rate * 40.0)
            + (10.0 if domain_quality.target_record_count > 0 else 0.0),
        ),
        1,
    )

    return {
        "branches": dict(branches),
        "products": sorted(products),
        "total_prod_analysis": total_prod_analysis,
        "total": {
            "achieve": round((sum(total_monthly_actual) / sum(total_monthly_target)) * 100.0, 1) if sum(total_monthly_target) > 0 else 0.0,
            "avg": total_avg,
            "monthly_actual": total_monthly_actual,
            "monthly_target": total_monthly_target,
            "analysis": {"importance": {}, "correlation": {}, "adj_correlation": {}, "ccf": []},
        },
        "total_avg": total_avg,
        "data_health": {
            "integrity_score": integrity_score,
            "mapped_fields": {
                "병원ID": "hospital_id",
                "담당자ID": "rep_id",
                "지점ID": "branch_id",
                "품목ID": "product_id",
                "실적금액": "sales_amount",
                "목표금액": "target_amount",
                "방문수": "total_visits",
            },
            "missing_fields": [],
        },
        "missing_data": missing_data,
    }


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
