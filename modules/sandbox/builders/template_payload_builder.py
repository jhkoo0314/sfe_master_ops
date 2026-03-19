from __future__ import annotations

from collections import defaultdict

from modules.kpi.sandbox_engine import (
    compute_sandbox_layer1_period_metrics,
    compute_sandbox_rep_kpis,
    validate_layer1_period_metrics_payload,
)
from modules.sandbox.schemas import (
    AnalysisSummary,
    DomainQualitySummary,
    JoinQualitySummary,
    SandboxInputStandard,
)


def build_report_template_payload(
    input_std: SandboxInputStandard,
    analysis_summary: AnalysisSummary,
    domain_quality: DomainQualitySummary,
    join_quality: JoinQualitySummary,
    official_kpi_6: dict[str, float | str],
) -> dict:
    behavior_keys = ["PT", "Demo", "Closing", "Needs", "FaceToFace", "Contact", "Access", "Feedback"]
    months = sorted(input_std.metric_months)
    month_index = {month: idx for idx, month in enumerate(months[:12])}

    rep_meta: dict[str, dict[str, str]] = {}
    rep_month: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: defaultdict(
            lambda: {
                "sales": 0.0,
                "target": 0.0,
                "visits": 0.0,
                "detail_calls": 0.0,
                "active_days": 0.0,
                "next_actions": 0.0,
                "hir_sum": 0.0,
                "hir_count": 0.0,
                "rtr_sum": 0.0,
                "rtr_count": 0.0,
                "bcr_sum": 0.0,
                "bcr_count": 0.0,
                "phr_sum": 0.0,
                "phr_count": 0.0,
                "pi_sum": 0.0,
                "pi_count": 0.0,
                "fgr_sum": 0.0,
                "fgr_count": 0.0,
                "PT": 0.0,
                "Demo": 0.0,
                "Closing": 0.0,
                "Needs": 0.0,
                "FaceToFace": 0.0,
                "Contact": 0.0,
                "Access": 0.0,
                "Feedback": 0.0,
            }
        )
    )
    rep_product: dict[str, dict[str, dict]] = defaultdict(
        lambda: defaultdict(
            lambda: {
                "product_name": None,
                "sales": 0.0,
                "target": 0.0,
                "monthly_sales": defaultdict(float),
                "monthly_target": defaultdict(float),
            }
        )
    )
    rep_hospital_sales: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    rep_activity_counts: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "PT": 0.0,
            "Demo": 0.0,
            "Closing": 0.0,
            "Needs": 0.0,
            "FaceToFace": 0.0,
            "Contact": 0.0,
            "Access": 0.0,
            "Feedback": 0.0,
        }
    )

    def normalize_behavior_key(raw_key: str) -> str:
        mapping = {
            "PT": "PT",
            "제품설명": "PT",
            "Demo": "Demo",
            "시연": "Demo",
            "행사": "Demo",
            "디지털": "Demo",
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
            "이메일": "Contact",
            "화상": "Contact",
            "Access": "Access",
            "접근": "Access",
            "Feedback": "Feedback",
            "피드백": "Feedback",
        }
        return mapping.get(str(raw_key or "").strip(), "FaceToFace")

    def calc_corr(rows: list[dict], left: str, right: str) -> float:
        if len(rows) < 2:
            return 0.0
        xs = [float(row.get(left, 0.0) or 0.0) for row in rows]
        ys = [float(row.get(right, 0.0) or 0.0) for row in rows]
        mean_x = sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        denominator_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
        denominator_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
        if denominator_x == 0 or denominator_y == 0:
            return 0.0
        return round(max(-1.0, min(1.0, numerator / (denominator_x * denominator_y))), 2)

    def build_matrix(rows: list[dict]) -> dict[str, dict[str, float]]:
        metrics = ["PI", "HIR", "RTR", "BCR", "PHR", "FGR"]
        matrix: dict[str, dict[str, float]] = {}
        for left in metrics:
            matrix[left] = {}
            for right in metrics:
                matrix[left][right] = 1.0 if left == right else calc_corr(rows, left, right)
        return matrix

    def amplify_matrix(matrix: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
        tuned: dict[str, dict[str, float]] = {}
        for left, row in matrix.items():
            tuned[left] = {}
            for right, value in row.items():
                if left == right:
                    tuned[left][right] = 1.0
                else:
                    tuned[left][right] = round(max(-1.0, min(1.0, value * 1.18)), 2)
        return tuned

    def average_metric(month_payload: dict[str, float], metric_key: str) -> float:
        sum_key = f"{metric_key.lower()}_sum"
        count_key = f"{metric_key.lower()}_count"
        count = float(month_payload.get(count_key, 0.0) or 0.0)
        if count <= 0:
            return 0.0
        return round(float(month_payload.get(sum_key, 0.0) or 0.0) / count, 2)

    for row in input_std.crm_records:
        rep_meta.setdefault(
            row.rep_id,
            {
                "rep_name": row.rep_name or row.rep_id,
                "branch_name": row.branch_name or row.branch_id or "UNASSIGNED",
                "branch_id": row.branch_id or "UNASSIGNED",
            },
        )
        bucket = rep_month[row.rep_id][row.metric_month]
        bucket["visits"] += row.total_visits
        bucket["detail_calls"] += row.detail_call_count
        bucket["active_days"] += row.active_day_count
        bucket["next_actions"] += row.next_action_count
        if row.hir is not None:
            bucket["hir_sum"] += float(row.hir)
            bucket["hir_count"] += 1
        if row.rtr is not None:
            bucket["rtr_sum"] += float(row.rtr)
            bucket["rtr_count"] += 1
        if row.bcr is not None:
            bucket["bcr_sum"] += float(row.bcr)
            bucket["bcr_count"] += 1
        if row.phr is not None:
            bucket["phr_sum"] += float(row.phr)
            bucket["phr_count"] += 1
        if row.pi is not None:
            bucket["pi_sum"] += float(row.pi)
            bucket["pi_count"] += 1
        if row.fgr is not None:
            bucket["fgr_sum"] += float(row.fgr)
            bucket["fgr_count"] += 1

        if row.behavior_mix_8:
            visit_weight = max(float(row.total_visits), 1.0)
            for behavior_key, mix_value in row.behavior_mix_8.items():
                norm_key = normalize_behavior_key(behavior_key)
                weighted_value = max(float(mix_value), 0.0) * visit_weight
                rep_activity_counts[row.rep_id][norm_key] += weighted_value
                bucket[norm_key] += weighted_value
        elif row.activity_types:
            distributed_count = max(float(row.total_visits) / max(len(row.activity_types), 1), 1.0)
            for activity_type in row.activity_types:
                norm_key = normalize_behavior_key(activity_type)
                rep_activity_counts[row.rep_id][norm_key] += distributed_count
                bucket[norm_key] += distributed_count
        else:
            rep_activity_counts[row.rep_id]["FaceToFace"] += max(float(row.total_visits), 1.0)
            bucket["FaceToFace"] += max(float(row.total_visits), 1.0)

    for row in input_std.sales_records:
        rep_meta.setdefault(
            row.rep_id,
            {
                "rep_name": row.rep_name or row.rep_id,
                "branch_name": row.branch_name or row.branch_id or "UNASSIGNED",
                "branch_id": row.branch_id or "UNASSIGNED",
            },
        )
        rep_month[row.rep_id][row.metric_month]["sales"] += row.sales_amount
        rep_product[row.rep_id][row.product_id]["product_name"] = row.product_name or row.product_id
        rep_product[row.rep_id][row.product_id]["sales"] += row.sales_amount
        rep_product[row.rep_id][row.product_id]["monthly_sales"][row.metric_month] += row.sales_amount
        rep_hospital_sales[row.rep_id][row.hospital_id] += row.sales_amount

    for row in input_std.target_records:
        rep_meta.setdefault(
            row.rep_id,
            {
                "rep_name": row.rep_name or row.rep_id,
                "branch_name": row.branch_name or row.branch_id or "UNASSIGNED",
                "branch_id": row.branch_id or "UNASSIGNED",
            },
        )
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

    def latest_month_slot() -> int:
        if not months:
            return 0
        return max(0, min(len(months) - 1, 11))

    def layer1_point(layer1_payload: dict, period: str, idx: int) -> dict[str, float]:
        series = layer1_payload.get(period, [])
        if not isinstance(series, list) or not series:
            return {
                "actual": 0.0,
                "target": 0.0,
                "attainment_rate": 0.0,
                "gap_amount": 0.0,
                "gap_million": 0.0,
                "pi": 0.0,
                "fgr": 0.0,
                "scale": 1.0,
            }
        safe_idx = max(0, min(idx, len(series) - 1))
        point = series[safe_idx]
        if isinstance(point, dict):
            return {
                "actual": float(point.get("actual", 0.0) or 0.0),
                "target": float(point.get("target", 0.0) or 0.0),
                "attainment_rate": float(point.get("attainment_rate", 0.0) or 0.0),
                "gap_amount": float(point.get("gap_amount", 0.0) or 0.0),
                "gap_million": float(point.get("gap_million", 0.0) or 0.0),
                "pi": float(point.get("pi", 0.0) or 0.0),
                "fgr": float(point.get("fgr", 0.0) or 0.0),
                "scale": float(point.get("scale", 1.0) or 1.0),
            }
        return {
            "actual": 0.0,
            "target": 0.0,
            "attainment_rate": 0.0,
            "gap_amount": 0.0,
            "gap_million": 0.0,
            "pi": 0.0,
            "fgr": 0.0,
            "scale": 1.0,
        }

    def build_layer1_payload(monthly_actual: list[float], monthly_target: list[float]) -> dict:
        return validate_layer1_period_metrics_payload(
            compute_sandbox_layer1_period_metrics(
                monthly_actual=monthly_actual,
                monthly_target=monthly_target,
            )
        )

    def calc_gini(values: list[float]) -> float:
        points = sorted(float(v) for v in values if float(v) > 0)
        if not points:
            return 0.0
        total = sum(points)
        n = len(points)
        weighted = sum((idx + 1) * value for idx, value in enumerate(points))
        return round((2 * weighted) / (n * total) - (n + 1) / n, 4)

    branches: dict[str, dict] = defaultdict(lambda: {"members": []})
    branch_prod_analysis_acc: dict[str, dict[str, dict]] = defaultdict(
        lambda: defaultdict(
            lambda: {
                "monthly_actual": [0.0] * 12,
                "monthly_target": [0.0] * 12,
            }
        )
    )
    total_prod_analysis: dict[str, dict] = {}
    products = set()

    for rep_id, month_stats in rep_month.items():
        meta = rep_meta.get(
            rep_id,
            {
                "rep_name": rep_id,
                "branch_name": "UNASSIGNED",
                "branch_id": "UNASSIGNED",
            },
        )
        monthly_actual = month_series({month: vals["sales"] for month, vals in month_stats.items()})
        monthly_target = month_series({month: vals["target"] for month, vals in month_stats.items()})
        total_actual = sum(monthly_actual)
        total_target = sum(monthly_target)
        total_visits = sum(vals["visits"] for vals in month_stats.values())
        rep_kpis = compute_sandbox_rep_kpis(month_stats)
        hir = float(rep_kpis["hir"])
        rtr = float(rep_kpis["rtr"])
        bcr = float(rep_kpis["bcr"])
        phr = float(rep_kpis["phr"])
        pi = float(rep_kpis["pi"])
        fgr = float(rep_kpis["fgr"])
        efficiency = round(total_actual / max(total_visits, 1), 0)
        sustainability = round(min(100.0, (bcr * 0.4) + (phr * 0.35) + (max(pi, 0.0) * 0.25)), 1)
        gini = calc_gini(list(rep_hospital_sales.get(rep_id, {}).values()))
        activity_counts = {
            key: round(value, 1)
            for key, value in rep_activity_counts.get(rep_id, {}).items()
        }
        activity_total = max(sum(activity_counts.values()), 1.0)
        shap = {
            key: round(float(activity_counts.get(key, 0.0)) / activity_total, 2)
            for key in behavior_keys
        }

        product_rows = []
        member_prod_analysis: dict[str, dict] = {}
        for product_id, prod in sorted(
            rep_product.get(rep_id, {}).items(),
            key=lambda item: float(item[1]["sales"]),
            reverse=True,
        ):
            product_name = str(prod["product_name"] or product_id)
            products.add(product_name)
            prod_monthly_actual = month_series(prod["monthly_sales"])
            prod_monthly_target = month_series(prod["monthly_target"])
            prod_total_actual = sum(prod_monthly_actual)
            prod_total_target = sum(prod_monthly_target)
            prod_layer1 = build_layer1_payload(prod_monthly_actual, prod_monthly_target)
            latest_prod_month = layer1_point(prod_layer1, "monthly", latest_month_slot())
            prod_yearly = layer1_point(prod_layer1, "yearly", 0)
            prod_growth = round(float(latest_prod_month["fgr"]), 1)
            prod_pi = round(float(prod_yearly["attainment_rate"]), 1)
            prod_ms = round((prod_total_actual / max(total_actual, 1)) * 100.0, 1) if total_actual > 0 else 0.0
            product_activity_counts = {key: 0.0 for key in behavior_keys}
            product_analysis_rows: list[dict[str, float]] = []
            for month, month_payload in month_stats.items():
                idx = month_index.get(month)
                if idx is None or idx >= len(prod_monthly_actual):
                    continue
                month_sales = float(month_payload.get("sales", 0.0) or 0.0)
                product_sales = float(prod_monthly_actual[idx] or 0.0)
                sales_share = (product_sales / month_sales) if month_sales > 0 else 0.0
                layer1_month = layer1_point(prod_layer1, "monthly", idx)
                row_metrics = {
                    "HIR": average_metric(month_payload, "hir"),
                    "RTR": average_metric(month_payload, "rtr"),
                    "BCR": average_metric(month_payload, "bcr"),
                    "PHR": average_metric(month_payload, "phr"),
                    "PI": round(float(layer1_month.get("pi", 0.0) or 0.0), 2),
                    "FGR": round(float(layer1_month.get("fgr", 0.0) or 0.0), 2),
                }
                for behavior_key in behavior_keys:
                    scaled_behavior = round(float(month_payload.get(behavior_key, 0.0) or 0.0) * sales_share, 2)
                    row_metrics[behavior_key] = scaled_behavior
                    product_activity_counts[behavior_key] += scaled_behavior
                product_analysis_rows.append(row_metrics)

            product_importance = {
                key: round(calc_corr(product_analysis_rows, key, "PI"), 2)
                for key in behavior_keys
            }
            product_correlation = build_matrix(product_analysis_rows)
            product_rows.append({"name": product_name, "ms": prod_ms, "growth": prod_growth})
            member_prod_analysis[product_name] = {
                "monthly_actual": prod_monthly_actual,
                "monthly_target": prod_monthly_target,
                "layer1": prod_layer1,
                "처방금액": round(prod_total_actual, 0),
                "목표금액": round(prod_total_target, 0),
                "PI": prod_pi,
                "FGR": prod_growth,
                "avg_ms": prod_ms,
                "activity_counts": {key: round(value, 1) for key, value in product_activity_counts.items()},
                "analysis": {
                    "importance": product_importance,
                    "correlation": product_correlation,
                    "adj_correlation": amplify_matrix(product_correlation),
                    "ccf": [],
                },
            }
            total_row = total_prod_analysis.setdefault(
                product_name,
                {
                    "achieve": 0.0,
                    "avg": {},
                    "monthly_actual": [0.0] * 12,
                    "monthly_target": [0.0] * 12,
                },
            )
            for idx in range(12):
                total_row["monthly_actual"][idx] += prod_monthly_actual[idx]
                total_row["monthly_target"][idx] += prod_monthly_target[idx]
                branch_prod_analysis_acc[str(meta["branch_name"])][product_name]["monthly_actual"][idx] += prod_monthly_actual[idx]
                branch_prod_analysis_acc[str(meta["branch_name"])][product_name]["monthly_target"][idx] += prod_monthly_target[idx]

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
            "shap": shap,
            "activity_counts": activity_counts,
            "prod_matrix": product_rows[:8] if product_rows else [{"name": "NO_PRODUCT", "ms": 0.0, "growth": 0.0}],
            "prod_analysis": member_prod_analysis,
            "monthly_actual": monthly_actual,
            "monthly_target": monthly_target,
            "layer1": build_layer1_payload(monthly_actual, monthly_target),
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
        branch_layer1 = build_layer1_payload(branch_actual, branch_target)
        branch["achieve"] = round(float(layer1_point(branch_layer1, "yearly", 0)["attainment_rate"]), 1)
        branch["monthly_actual"] = branch_actual
        branch["monthly_target"] = branch_target
        branch["layer1"] = branch_layer1
        branch_importance = {
            "PT": round(sum(float(member["shap"].get("PT", 0.0)) for member in members) / max(len(members), 1), 2),
            "Demo": round(sum(float(member["shap"].get("Demo", 0.0)) for member in members) / max(len(members), 1), 2),
            "Closing": round(sum(float(member["shap"].get("Closing", 0.0)) for member in members) / max(len(members), 1), 2),
            "Needs": round(sum(float(member["shap"].get("Needs", 0.0)) for member in members) / max(len(members), 1), 2),
            "FaceToFace": round(sum(float(member["shap"].get("FaceToFace", 0.0)) for member in members) / max(len(members), 1), 2),
            "Contact": round(sum(float(member["shap"].get("Contact", 0.0)) for member in members) / max(len(members), 1), 2),
            "Access": round(sum(float(member["shap"].get("Access", 0.0)) for member in members) / max(len(members), 1), 2),
            "Feedback": round(sum(float(member["shap"].get("Feedback", 0.0)) for member in members) / max(len(members), 1), 2),
        }
        branch_correlation = build_matrix(members)
        branch["analysis"] = {
            "importance": branch_importance,
            "correlation": branch_correlation,
            "adj_correlation": amplify_matrix(branch_correlation),
            "ccf": [],
        }
        branch["prod_analysis"] = {}
        for product_name, prod_acc in branch_prod_analysis_acc.get(branch_name, {}).items():
            prod_actual = [round(v, 0) for v in prod_acc["monthly_actual"]]
            prod_target = [round(v, 0) for v in prod_acc["monthly_target"]]
            prod_layer1 = build_layer1_payload(prod_actual, prod_target)
            prod_yearly = layer1_point(prod_layer1, "yearly", 0)
            prod_month_latest = layer1_point(prod_layer1, "monthly", latest_month_slot())
            branch["prod_analysis"][product_name] = {
                "achieve": round(float(prod_yearly["attainment_rate"]), 1),
                "avg": {
                    **branch["avg"],
                    "PI": round(float(prod_yearly["attainment_rate"]), 1),
                    "FGR": round(float(prod_month_latest["fgr"]), 1),
                },
                "monthly_actual": prod_actual,
                "monthly_target": prod_target,
                "layer1": prod_layer1,
                "analysis": branch["analysis"],
            }

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
    total_importance = {
        "PT": round(sum(float(member["shap"].get("PT", 0.0)) for member in all_members) / max(len(all_members), 1), 2),
        "Demo": round(sum(float(member["shap"].get("Demo", 0.0)) for member in all_members) / max(len(all_members), 1), 2),
        "Closing": round(sum(float(member["shap"].get("Closing", 0.0)) for member in all_members) / max(len(all_members), 1), 2),
        "Needs": round(sum(float(member["shap"].get("Needs", 0.0)) for member in all_members) / max(len(all_members), 1), 2),
        "FaceToFace": round(sum(float(member["shap"].get("FaceToFace", 0.0)) for member in all_members) / max(len(all_members), 1), 2),
        "Contact": round(sum(float(member["shap"].get("Contact", 0.0)) for member in all_members) / max(len(all_members), 1), 2),
        "Access": round(sum(float(member["shap"].get("Access", 0.0)) for member in all_members) / max(len(all_members), 1), 2),
        "Feedback": round(sum(float(member["shap"].get("Feedback", 0.0)) for member in all_members) / max(len(all_members), 1), 2),
    }
    total_correlation = build_matrix(all_members)

    for _, total_row in total_prod_analysis.items():
        total_layer1 = build_layer1_payload(total_row["monthly_actual"], total_row["monthly_target"])
        total_row["achieve"] = round(float(layer1_point(total_layer1, "yearly", 0)["attainment_rate"]), 1)
        total_row["avg"] = total_avg
        total_row["monthly_actual"] = [round(v, 0) for v in total_row["monthly_actual"]]
        total_row["monthly_target"] = [round(v, 0) for v in total_row["monthly_target"]]
        total_row["layer1"] = total_layer1
        total_row["analysis"] = {
            "importance": total_importance,
            "correlation": total_correlation,
            "adj_correlation": amplify_matrix(total_correlation),
            "ccf": [],
        }

    missing_data = []
    if join_quality.orphan_crm_hospitals > 0:
        missing_data.append({"지점": "OPS", "성명": "UNMAPPED", "품목": "orphan_crm_hospitals"})

    integrity_score = round(
        float(analysis_summary.custom_metrics.get("sandbox_proxy_integrity_score", 0.0)),
        1,
    )

    total_layer1 = build_layer1_payload(total_monthly_actual, total_monthly_target)

    return {
        "official_kpi_6": official_kpi_6,
        "branches": dict(branches),
        "products": sorted(products),
        "total_prod_analysis": total_prod_analysis,
        "total": {
            "achieve": round(float(layer1_point(total_layer1, "yearly", 0)["attainment_rate"]), 1),
            "avg": total_avg,
            "monthly_actual": total_monthly_actual,
            "monthly_target": total_monthly_target,
            "layer1": total_layer1,
            "analysis": {
                "importance": total_importance,
                "correlation": total_correlation,
                "adj_correlation": amplify_matrix(total_correlation),
                "ccf": [],
            },
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
            "operational_notes": [
                {
                    "label": "sales_only_hospitals",
                    "count": join_quality.orphan_sales_hospitals,
                    "message": "실적은 있으나 CRM 활동이 없는 병원 수",
                },
                {
                    "label": "crm_only_hospitals",
                    "count": join_quality.orphan_crm_hospitals,
                    "message": "CRM 활동은 있으나 실적이 없는 병원 수",
                },
            ],
        },
        "missing_data": missing_data,
    }
