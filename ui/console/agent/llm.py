from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

import httpx

from common.config import settings


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _load_json_file(path: Path) -> dict[str, Any] | list[Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_last_js_assignment_value(path: Path) -> dict[str, Any] | list[Any] | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return None
    for raw_line in reversed(lines):
        line = raw_line.strip()
        if "=" not in line or not line.endswith(";"):
            continue
        _, _, rhs = line.partition("=")
        payload = rhs.strip().rstrip(";").strip()
        if not payload or payload in {"{}", "[]"}:
            continue
        try:
            data = json.loads(payload)
        except Exception:
            continue
        if isinstance(data, (dict, list)):
            return data
    return None


def _load_branch_asset_json(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    match = re.search(r"=\s*(\{.*\})\s*;?\s*$", text, re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def _format_amount(value: Any) -> str:
    return f"{round(_to_float(value)):,}원"


def _format_pct(value: Any, scale_100: bool = False) -> str:
    number = _to_float(value)
    if scale_100:
        number *= 100
    return f"{round(number, 1)}%"


def _format_score(value: Any) -> str:
    return f"{round(_to_float(value), 3)}"


def _sum_period(values: Any, start_idx: int, end_idx: int) -> float:
    if not isinstance(values, list):
        return 0.0
    total = 0.0
    for value in values[start_idx:end_idx]:
        try:
            total += float(value or 0)
        except Exception:
            continue
    return total


def _summarize_sandbox_payload(path: Path) -> str:
    data = _load_json_file(path)
    if not isinstance(data, dict):
        return ""
    payload = data.get("payload", {})
    if not isinstance(payload, dict):
        return ""
    manifest = payload.get("branch_asset_manifest", {})
    assets_dir = path.parent / "sandbox_report_preview_assets"
    ranking_rows: list[dict[str, Any]] = []
    if isinstance(manifest, dict):
        for branch_name, asset_name in manifest.items():
            branch_data = _load_branch_asset_json(assets_dir / str(asset_name))
            if not branch_data:
                continue
            for member in branch_data.get("members", []) or []:
                if not isinstance(member, dict):
                    continue
                q1_actual = round(_sum_period(member.get("monthly_actual"), 0, 3))
                q1_target = round(_sum_period(member.get("monthly_target"), 0, 3))
                attainment = round((q1_actual / q1_target) * 100, 1) if q1_target else 0.0
                ranking_rows.append(
                    {
                        "branch": branch_name,
                        "rep_name": _clean_text(member.get("성명")),
                        "q1_actual": q1_actual,
                        "q1_target": q1_target,
                        "q1_attainment": attainment,
                        "HIR": float(member.get("HIR", 0) or 0),
                        "RTR": float(member.get("RTR", 0) or 0),
                        "BCR": float(member.get("BCR", 0) or 0),
                        "PHR": float(member.get("PHR", 0) or 0),
                        "PI": float(member.get("PI", 0) or 0),
                        "FGR": float(member.get("FGR", 0) or 0),
                    }
                )
    if not ranking_rows:
        return f"[artifact] {path.name}\n- payload keys: {list(payload.keys())[:20]}"

    top5 = sorted(ranking_rows, key=lambda item: item["q1_actual"], reverse=True)[:5]
    bottom5 = sorted(ranking_rows, key=lambda item: item["q1_actual"])[:5]

    def _avg(items: list[dict[str, Any]], key: str) -> float:
        return round(sum(float(item.get(key, 0) or 0) for item in items) / len(items), 1) if items else 0.0

    gap_lines = []
    for key in ["HIR", "RTR", "BCR", "PHR", "PI", "FGR"]:
        gap_lines.append(f"- {key}: top5 평균 {_avg(top5, key)} / bottom5 평균 {_avg(bottom5, key)} / 격차 {round(_avg(top5, key)-_avg(bottom5, key),1)}")

    return (
        f"[artifact] {path.name}\n"
        f"- branch_count: {len(manifest) if isinstance(manifest, dict) else 0}\n"
        "[Q1 top5 reps]\n"
        + "\n".join(
            f"- {idx+1}. {item['branch']} {item['rep_name']} | 실적 {item['q1_actual']:,}원 | 목표 {item['q1_target']:,}원 | 달성률 {item['q1_attainment']}%"
            for idx, item in enumerate(top5)
        )
        + "\n[Q1 bottom5 reps]\n"
        + "\n".join(
            f"- {idx+1}. {item['branch']} {item['rep_name']} | 실적 {item['q1_actual']:,}원 | 목표 {item['q1_target']:,}원 | 달성률 {item['q1_attainment']}%"
            for idx, item in enumerate(bottom5)
        )
        + "\n[metric gaps]\n"
        + "\n".join(gap_lines[:4])
    )


def _summarize_crm_payload(path: Path) -> str:
    data = _load_json_file(path)
    if not isinstance(data, dict):
        return ""
    payload = data.get("payload", {})
    if not isinstance(payload, dict):
        return ""
    overview = payload.get("overview", {})
    activity_context = payload.get("activity_context", {})
    mapping_quality = payload.get("mapping_quality", {})
    filters = payload.get("filters", {})

    period_options = filters.get("period_options", []) if isinstance(filters, dict) else []
    team_options = filters.get("team_options", []) if isinstance(filters, dict) else []
    rep_options = filters.get("rep_options", []) if isinstance(filters, dict) else []
    activity_types = activity_context.get("activity_types_standard_found", []) if isinstance(activity_context, dict) else []
    products = activity_context.get("products_mentioned", []) if isinstance(activity_context, dict) else []
    unmapped_names = mapping_quality.get("unmapped_hospital_names", []) if isinstance(mapping_quality, dict) else []

    period_labels = [str(item.get("label", "")).strip() for item in period_options[:4] if isinstance(item, dict)]
    team_labels = [str(item.get("label", "")).strip() for item in team_options[1:5] if isinstance(item, dict)]
    rep_labels = [str(item.get("label", "")).strip() for item in rep_options[1:6] if isinstance(item, dict)]
    detail_lines: list[str] = []
    assets_dir = path.parent / "crm_analysis_preview_assets"
    all_scope_path = assets_dir / "ALL_ALL.js"
    all_scope = _load_last_js_assignment_value(all_scope_path) if all_scope_path.exists() else None
    if isinstance(all_scope, dict):
        matrix_rows = all_scope.get("matrix_rows", []) if isinstance(all_scope.get("matrix_rows"), list) else []
        ranked_rows = [item for item in matrix_rows if isinstance(item, dict)]
        if ranked_rows:
            top_rows = sorted(ranked_rows, key=lambda item: _to_float(item.get("coach_score")), reverse=True)[:3]
            bottom_rows = sorted(ranked_rows, key=lambda item: _to_float(item.get("coach_score")))[:3]
            detail_lines.append("[detail asset] ALL 기간 상위 담당자")
            detail_lines.extend(
                f"- {item.get('rep_name')} | coach_score {_format_score(item.get('coach_score'))} | visits {round(_to_float(item.get('total_visits'))):,} | branch {_clean_text(item.get('branch_name'))}"
                for item in top_rows
            )
            detail_lines.append("[detail asset] ALL 기간 하위 담당자")
            detail_lines.extend(
                f"- {item.get('rep_name')} | coach_score {_format_score(item.get('coach_score'))} | visits {round(_to_float(item.get('total_visits'))):,} | branch {_clean_text(item.get('branch_name'))}"
                for item in bottom_rows
            )

    monthly_scope_paths = sorted([asset for asset in assets_dir.glob("*_ALL.js") if asset.name != "ALL_ALL.js"], key=lambda item: item.name)
    if monthly_scope_paths:
        monthly_scope = _load_last_js_assignment_value(monthly_scope_paths[0])
        if isinstance(monthly_scope, dict):
            monthly_rows = monthly_scope.get("matrix_rows", []) if isinstance(monthly_scope.get("matrix_rows"), list) else []
            monthly_ranked = [item for item in monthly_rows if isinstance(item, dict)]
            if monthly_ranked:
                top_month_rows = sorted(monthly_ranked, key=lambda item: _to_float(item.get("coach_score")), reverse=True)[:3]
                month_label = _clean_text(monthly_scope.get("period_label")) or monthly_scope_paths[0].stem.split("_")[0]
                detail_lines.append(f"[detail asset] {month_label} 상위 담당자")
                detail_lines.extend(
                    f"- {item.get('rep_name')} | coach_score {_format_score(item.get('coach_score'))} | HIR {_format_score(item.get('hir'))} | RTR {_format_score(item.get('rtr'))}"
                    for item in top_month_rows
                )

    summary = (
        f"[artifact] {path.name}\n"
        f"- report_title: {_clean_text(data.get('report_title'))}\n"
        f"- company_key: {_clean_text(payload.get('company'))}\n"
        f"- quality: {_clean_text(overview.get('quality_status'))} / score {_to_float(overview.get('quality_score'))}\n"
        f"- activities: {round(_to_float(overview.get('crm_activity_count'))):,}건\n"
        f"- reps: {round(_to_float(overview.get('unique_reps'))):,}명 / hospitals: {round(_to_float(overview.get('unique_hospitals'))):,}곳 / branches: {round(_to_float(overview.get('unique_branches'))):,}개\n"
        f"- period: {_clean_text(activity_context.get('date_range_start'))} ~ {_clean_text(activity_context.get('date_range_end'))}\n"
        f"- mapping_rate: {_format_pct(mapping_quality.get('hospital_mapping_rate'), scale_100=True)} / unmapped_count: {round(_to_float(mapping_quality.get('unmapped_hospital_count'))):,}\n"
        f"- activity_types: {', '.join([str(item) for item in activity_types[:8]])}\n"
        f"- sample_products: {', '.join([str(item) for item in products[:8]])}\n"
        f"- period_filters: {', '.join([label for label in period_labels if label])}\n"
        f"- team_filters: {', '.join([label for label in team_labels if label])}\n"
        f"- sample_reps: {', '.join([label for label in rep_labels if label])}\n"
        f"- unmapped_hospital_samples: {', '.join([str(item) for item in unmapped_names[:5]])}"
    )
    if detail_lines:
        summary += "\n" + "\n".join(detail_lines[:10])
    return summary


def _summarize_prescription_payload(path: Path) -> str:
    data = _load_json_file(path)
    if not isinstance(data, dict):
        return ""
    payload = data.get("payload", {})
    if not isinstance(payload, dict):
        return ""
    overview = payload.get("overview", {})
    flow_summary = payload.get("flow_summary", {})
    flow_series = payload.get("flow_series", []) if isinstance(payload.get("flow_series"), list) else []
    flow_series_by_territory = (
        payload.get("flow_series_by_territory", {}) if isinstance(payload.get("flow_series_by_territory"), dict) else {}
    )
    pipeline_steps = payload.get("pipeline_steps", []) if isinstance(payload.get("pipeline_steps"), list) else []

    territory_rows: list[dict[str, Any]] = []
    for territory_name, rows in flow_series_by_territory.items():
        if not isinstance(rows, list):
            continue
        territory_rows.append(
            {
                "territory": str(territory_name),
                "final_amount": sum(_to_float(item.get("final_amount")) for item in rows if isinstance(item, dict)),
                "tracked_amount": sum(_to_float(item.get("tracked_amount")) for item in rows if isinstance(item, dict)),
            }
        )
    top_territories = sorted(territory_rows, key=lambda item: item["final_amount"], reverse=True)[:5]
    step_labels = [
        f"{_clean_text(item.get('step'))} {_clean_text(item.get('title'))}={_clean_text(item.get('status'))}"
        for item in pipeline_steps[:6]
        if isinstance(item, dict)
    ]
    month_labels = [str(item.get("label", "")).strip() for item in flow_series[:6] if isinstance(item, dict)]

    claim_validation = overview.get("claim_validation_summary", {}) if isinstance(overview.get("claim_validation_summary"), dict) else {}
    detail_lines: list[str] = []
    assets_dir = path.parent / "prescription_flow_preview_assets"
    rep_kpis_path = assets_dir / "rep_kpis__all.js"
    rep_kpis_data = _load_last_js_assignment_value(rep_kpis_path) if rep_kpis_path.exists() else None
    if isinstance(rep_kpis_data, list):
        rep_totals: dict[str, dict[str, Any]] = {}
        for row in rep_kpis_data:
            if not isinstance(row, dict):
                continue
            rep_id = _clean_text(row.get("rep_id"))
            rep_name = _clean_text(row.get("rep_name"))
            key = rep_id or rep_name
            if not key:
                continue
            bucket = rep_totals.setdefault(
                key,
                {
                    "rep_name": rep_name,
                    "branch_name": _clean_text(row.get("branch_name")),
                    "total_amount": 0.0,
                    "flow_count": 0.0,
                    "gap_amount": 0.0,
                },
            )
            bucket["total_amount"] += _to_float(row.get("total_amount"))
            bucket["flow_count"] += _to_float(row.get("flow_count"))
            bucket["gap_amount"] += abs(_to_float(row.get("settlement_gap_amount")))
        top_rep_totals = sorted(rep_totals.values(), key=lambda item: item["total_amount"], reverse=True)[:5]
        detail_lines.append("[detail asset] rep_kpis 기준 상위 담당자")
        detail_lines.extend(
            f"- {item['rep_name']} | branch {item['branch_name']} | amount {_format_amount(item['total_amount'])} | flow {round(item['flow_count']):,} | gap_abs {_format_amount(item['gap_amount'])}"
            for item in top_rep_totals
        )

    claim_asset_paths = sorted([asset for asset in assets_dir.glob("claims__*.js") if asset.name != "claims__all.js"], key=lambda item: item.name)
    claim_asset = claim_asset_paths[0] if claim_asset_paths else (assets_dir / "claims__all.js")
    claim_data = _load_last_js_assignment_value(claim_asset) if claim_asset.exists() else None
    if isinstance(claim_data, list) and claim_data:
        verdict_counts: dict[str, int] = {}
        for row in claim_data:
            if not isinstance(row, dict):
                continue
            verdict = _clean_text(row.get("verdict")) or "-"
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        risky_rows = [
            row for row in claim_data
            if isinstance(row, dict) and _clean_text(row.get("verdict")) in {"REVIEW", "SUSPECT"}
        ]
        risky_rows = sorted(risky_rows, key=lambda item: abs(_to_float(item.get("variance_amount"))), reverse=True)[:5]
        period_label = _clean_text(claim_data[0].get("period_label")) if isinstance(claim_data[0], dict) else claim_asset.stem
        detail_lines.append(f"[detail asset] {period_label} claim 판정")
        detail_lines.append("- " + " / ".join(f"{key} {value}" for key, value in sorted(verdict_counts.items(), key=lambda item: item[0])))
        detail_lines.extend(
            f"- {row.get('rep_name')} | {row.get('territory_name')} | {row.get('product_name')} | verdict {_clean_text(row.get('verdict'))} | variance {_format_amount(row.get('variance_amount'))}"
            for row in risky_rows
        )

    summary = (
        f"[artifact] {path.name}\n"
        f"- report_title: {_clean_text(data.get('report_title'))}\n"
        f"- company: {_clean_text(payload.get('company'))}\n"
        f"- quality: {_clean_text(overview.get('quality_status'))} / score {_to_float(overview.get('quality_score'))}\n"
        f"- standard_records: {round(_to_float(overview.get('standard_record_count'))):,}건 / connected_hospitals: {round(_to_float(overview.get('connected_hospital_count'))):,}곳\n"
        f"- flow_completion_rate: {_format_pct(overview.get('flow_completion_rate'), scale_100=True)}\n"
        f"- claim_validation: total {round(_to_float(claim_validation.get('total_cases'))):,} / pass {round(_to_float(claim_validation.get('pass_count'))):,} / review {round(_to_float(claim_validation.get('review_count'))):,} / suspect {round(_to_float(claim_validation.get('suspect_count'))):,}\n"
        f"- wholesale_total: {_format_amount(flow_summary.get('total_wholesale_amount'))}\n"
        f"- tracked_total: {_format_amount(flow_summary.get('tracked_amount'))}\n"
        f"- final_amount_before_kpi_publish: {_format_amount(flow_summary.get('pre_kpi_final_amount'))}\n"
        f"- months: {', '.join([label for label in month_labels if label])}\n"
        "[top territories by final_amount]\n"
        + "\n".join(
            f"- {idx+1}. {item['territory']} | final { _format_amount(item['final_amount']) } | tracked { _format_amount(item['tracked_amount']) }"
            for idx, item in enumerate(top_territories)
        )
        + "\n[pipeline_steps]\n"
        + "\n".join(f"- {label}" for label in step_labels)
    )
    if detail_lines:
        summary += "\n" + "\n".join(detail_lines[:12])
    return summary


def _summarize_territory_payload(path: Path) -> str:
    data = _load_json_file(path)
    if not isinstance(data, dict):
        return ""
    payload = data.get("payload", {})
    if not isinstance(payload, dict):
        return ""
    overview = payload.get("overview", {})
    filters = payload.get("filters", {})
    rep_options = filters.get("rep_options", []) if isinstance(filters, dict) else []
    month_options = filters.get("month_options", []) if isinstance(filters, dict) else []

    rep_rows = []
    for item in rep_options:
        if not isinstance(item, dict):
            continue
        rep_rows.append(
            {
                "label": _clean_text(item.get("label")),
                "hospital_count": round(_to_float(item.get("hospital_count"))),
                "day_count": round(_to_float(item.get("day_count"))),
                "month_count": round(_to_float(item.get("month_count"))),
            }
        )
    top_hospitals = sorted(rep_rows, key=lambda item: item["hospital_count"], reverse=True)[:5]
    top_days = sorted(rep_rows, key=lambda item: item["day_count"], reverse=True)[:5]
    month_labels = [str(item.get("label", "")).strip() for item in month_options[:6] if isinstance(item, dict)]
    detail_lines: list[str] = []
    assets_dir = path.parent / "territory_map_preview_assets"
    for rep in top_hospitals[:2]:
        rep_label = _clean_text(rep.get("label"))
        rep_entry = next((item for item in rep_options if isinstance(item, dict) and _clean_text(item.get("label")) == rep_label), None)
        rep_id = _clean_text(rep_entry.get("value")) if isinstance(rep_entry, dict) else ""
        if not rep_id:
            continue
        catalog_path = assets_dir / f"{rep_id}__catalog.js"
        catalog_data = _load_last_js_assignment_value(catalog_path) if catalog_path.exists() else None
        if isinstance(catalog_data, dict):
            hospital_catalog = catalog_data.get("hospital_catalog", {})
            if isinstance(hospital_catalog, dict):
                top_catalog = sorted(
                    [item for item in hospital_catalog.values() if isinstance(item, dict)],
                    key=lambda item: _to_float(item.get("sales")),
                    reverse=True,
                )[:3]
                detail_lines.append(f"[detail asset] {rep_label} 대표 병원")
                detail_lines.extend(
                    f"- {item.get('hospital')} | sales {_format_amount(item.get('sales'))} | target {_format_amount(item.get('target'))} | visits {round(_to_float(item.get('visits'))):,}"
                    for item in top_catalog
                )

        month_asset_paths = sorted([asset for asset in assets_dir.glob(f"{rep_id}__*.js") if not asset.name.endswith('__catalog.js')], key=lambda item: item.name)
        if not month_asset_paths:
            continue
        month_data = _load_last_js_assignment_value(month_asset_paths[0])
        if isinstance(month_data, dict):
            views = month_data.get("views", {})
            if isinstance(views, dict):
                month_aggregate = next((item for key, item in views.items() if key.endswith("|__ALL__") and isinstance(item, dict)), None)
                day_rows = [item for key, item in views.items() if not key.endswith("|__ALL__") and isinstance(item, dict)]
                busiest_day = max(day_rows, key=lambda item: _to_float(item.get("summary", {}).get("distance_km")), default=None)
                if isinstance(month_aggregate, dict):
                    summary_row = month_aggregate.get("summary", {})
                    scope_row = month_aggregate.get("scope", {})
                    detail_lines.append(
                        f"[detail asset] {_clean_text(scope_row.get('rep_name'))} {_clean_text(scope_row.get('month_key'))} 월 전체 | stops {round(_to_float(summary_row.get('stop_count'))):,} | distance {round(_to_float(summary_row.get('distance_km')),1)}km | attainment {_format_pct(summary_row.get('attainment_rate'), scale_100=True)}"
                    )
                if isinstance(busiest_day, dict):
                    scope_row = busiest_day.get("scope", {})
                    summary_row = busiest_day.get("summary", {})
                    detail_lines.append(
                        f"- 최장 이동일 {_clean_text(scope_row.get('date_label'))} | distance {round(_to_float(summary_row.get('distance_km')),1)}km | visits {round(_to_float(summary_row.get('visit_count'))):,} | hospitals {round(_to_float(summary_row.get('selected_hospital_count'))):,}"
                    )

    summary = (
        f"[artifact] {path.name}\n"
        f"- report_title: {_clean_text(data.get('report_title'))}\n"
        f"- map_title: {_clean_text(overview.get('map_title'))}\n"
        f"- period_label: {_clean_text(overview.get('period_label'))}\n"
        f"- total_regions: {round(_to_float(overview.get('total_regions'))):,} / total_reps: {round(_to_float(overview.get('total_reps'))):,}\n"
        f"- territory_hospitals: {round(_to_float(overview.get('territory_hospital_count'))):,} / route_selections: {round(_to_float(overview.get('route_selection_count'))):,}\n"
        f"- coverage_rate: {_format_pct(overview.get('coverage_rate'), scale_100=True)}\n"
        f"- month_filters: {', '.join([label for label in month_labels if label])}\n"
        "[top reps by hospital_count]\n"
        + "\n".join(
            f"- {idx+1}. {item['label']} | hospitals {item['hospital_count']} | active_days {item['day_count']} | months {item['month_count']}"
            for idx, item in enumerate(top_hospitals)
        )
        + "\n[top reps by day_count]\n"
        + "\n".join(
            f"- {idx+1}. {item['label']} | active_days {item['day_count']} | hospitals {item['hospital_count']}"
            for idx, item in enumerate(top_days)
        )
    )
    if detail_lines:
        summary += "\n" + "\n".join(detail_lines[:12])
    return summary


def _summarize_generic_json(path: Path) -> str:
    data = _load_json_file(path)
    if isinstance(data, dict):
        preview = {key: data[key] for key in list(data.keys())[:15]}
        return f"[artifact] {path.name}\n{json.dumps(preview, ensure_ascii=False, indent=2)[:4000]}"
    if isinstance(data, list):
        return f"[artifact] {path.name}\nlist_length={len(data)}\n{json.dumps(data[:3], ensure_ascii=False, indent=2)[:3000]}"
    return ""


def _summarize_html(path: Path) -> str:
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    text = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return f"[artifact] {path.name}\n{text[:2500]}"


def _summarize_agent_summary_payload(artifact: dict[str, Any]) -> str:
    payload = artifact.get("payload")
    if not isinstance(payload, dict):
        return ""
    agent_summary = payload.get("agent_summary")
    if not isinstance(agent_summary, dict):
        return ""
    headline = _clean_text(agent_summary.get("headline"))
    facts = agent_summary.get("facts", []) if isinstance(agent_summary.get("facts"), list) else []
    report_key = _clean_text(agent_summary.get("report_key")) or _clean_text(payload.get("report_key"))
    lines = [f"[artifact-summary] {report_key or _clean_text(artifact.get('artifact_name'))}"]
    if headline:
        lines.append(f"- {headline}")
    for fact in facts[:5]:
        cleaned = _clean_text(fact)
        if cleaned:
            lines.append(f"- {cleaned}")
    return "\n".join(lines) if len(lines) > 1 else ""


def build_artifact_contexts(artifacts: list[dict[str, Any]], max_items: int = 4) -> tuple[str, list[str]]:
    prioritized = sorted(
        artifacts,
        key=lambda item: (
            0 if item.get("artifact_role") == "sandbox_report" else 1,
            0 if item.get("artifact_type") == "report_payload_standard" else 1,
            0 if item.get("artifact_type") == "report_result_asset" else 1,
            0 if item.get("artifact_type") == "report_html" else 1,
        ),
    )
    chunks: list[str] = []
    evidence_refs: list[str] = []
    for artifact in prioritized:
        path_text = _clean_text(artifact.get("storage_path"))
        if not path_text:
            continue
        summary = _summarize_agent_summary_payload(artifact)
        if summary:
            chunks.append(summary)
            evidence_refs.append(path_text)
            if len(chunks) >= max_items:
                break
        path = Path(path_text)
        if not path.exists():
            continue
        summary = ""
        if path.name == "sandbox_report_preview_payload_standard.json":
            summary = _summarize_sandbox_payload(path)
        elif path.name == "crm_analysis_preview_payload_standard.json":
            summary = _summarize_crm_payload(path)
        elif path.name == "prescription_flow_preview_payload_standard.json":
            summary = _summarize_prescription_payload(path)
        elif path.name == "territory_map_preview_payload_standard.json":
            summary = _summarize_territory_payload(path)
        elif path.suffix.lower() == ".json":
            summary = _summarize_generic_json(path)
        elif path.suffix.lower() in {".html", ".htm"}:
            summary = _summarize_html(path)
        if not summary:
            continue
        chunks.append(summary)
        evidence_refs.append(path_text)
        if len(chunks) >= max_items:
            break
    return "\n\n".join(chunks), evidence_refs


def is_llm_configured() -> bool:
    return bool(_clean_text(settings.llm_provider) and _clean_text(settings.llm_model) and _clean_text(settings.llm_api_key))


def _provider() -> str:
    return _clean_text(settings.llm_provider).lower()


def _system_prompt(answer_scope: str) -> str:
    scope_line = "근거 경로를 우선 설명하라." if answer_scope == "evidence_trace" else "최종 보고서 요약 중심으로 답하라."
    return (
        "You are the Agent tab analyst for Sales Data OS. "
        "Use only the provided run report context. "
        "Do not recalculate KPI. "
        "Do not join raw data. "
        "If evidence is missing, say that it cannot be confirmed. "
        f"{scope_line}"
    )


def _user_prompt(
    question: str,
    prompt_ctx: dict[str, Any] | None,
    full_ctx: dict[str, Any] | None,
    answer_scope: str,
    artifact_contexts: str,
) -> str:
    return (
        "[answer_scope]\n"
        f"{answer_scope}\n\n"
        "[user_question]\n"
        f"{question}\n\n"
        "[prompt_context]\n"
        f"{prompt_ctx or {}}\n\n"
        "[full_context]\n"
        f"{full_ctx or {}}\n\n"
        "[artifact_contexts]\n"
        f"{artifact_contexts}\n\n"
        "[response_rule]\n"
        "Answer in Korean. Be concise. Mention only facts supported by the provided context."
    )


def _extract_openai_text(data: dict[str, Any]) -> str:
    text = _clean_text(data.get("output_text"))
    if text:
        return text
    for item in data.get("output", []) or []:
        for content in item.get("content", []) or []:
            if content.get("type") == "output_text":
                text = _clean_text(content.get("text"))
                if text:
                    return text
    return ""


def _call_openai(system_prompt: str, user_prompt: str) -> str:
    base_url = _clean_text(settings.llm_base_url) or "https://api.openai.com"
    response = httpx.post(
        f"{base_url.rstrip('/')}/v1/responses",
        headers={
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.llm_model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            "temperature": settings.llm_temperature,
            "max_output_tokens": settings.llm_max_tokens,
        },
        timeout=settings.llm_timeout_sec,
    )
    response.raise_for_status()
    return _extract_openai_text(response.json())


def _call_claude(system_prompt: str, user_prompt: str) -> str:
    base_url = _clean_text(settings.llm_base_url) or "https://api.anthropic.com"
    response = httpx.post(
        f"{base_url.rstrip('/')}/v1/messages",
        headers={
            "x-api-key": settings.llm_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": settings.llm_model,
            "max_tokens": settings.llm_max_tokens,
            "temperature": settings.llm_temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=settings.llm_timeout_sec,
    )
    response.raise_for_status()
    data = response.json()
    parts = data.get("content", []) or []
    for part in parts:
        if part.get("type") == "text":
            text = _clean_text(part.get("text"))
            if text:
                return text
    return ""


def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    base_url = _clean_text(settings.llm_base_url) or "https://generativelanguage.googleapis.com"
    model = settings.llm_model
    response = httpx.post(
        f"{base_url.rstrip('/')}/v1beta/models/{model}:generateContent",
        params={"key": settings.llm_api_key},
        headers={"Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": settings.llm_temperature,
                "maxOutputTokens": settings.llm_max_tokens,
            },
        },
        timeout=settings.llm_timeout_sec,
    )
    response.raise_for_status()
    data = response.json()
    for candidate in data.get("candidates", []) or []:
        content = candidate.get("content", {})
        for part in content.get("parts", []) or []:
            text = _clean_text(part.get("text"))
            if text:
                return text
    return ""


def generate_agent_answer(
    *,
    question: str,
    prompt_ctx: dict[str, Any] | None,
    full_ctx: dict[str, Any] | None,
    answer_scope: str,
    evidence_refs: list[str],
    artifact_contexts: str = "",
) -> dict[str, Any]:
    if not is_llm_configured():
        raise RuntimeError("llm_not_configured")

    system_prompt = _system_prompt(answer_scope)
    user_prompt = _user_prompt(question, prompt_ctx, full_ctx, answer_scope, artifact_contexts)
    provider = _provider()

    if provider == "openai":
        answer_text = _call_openai(system_prompt, user_prompt)
    elif provider == "claude":
        answer_text = _call_claude(system_prompt, user_prompt)
    elif provider == "gemini":
        answer_text = _call_gemini(system_prompt, user_prompt)
    else:
        raise RuntimeError(f"unsupported_llm_provider:{provider}")

    answer_text = _clean_text(answer_text)
    if not answer_text:
        raise RuntimeError("empty_llm_response")

    return {
        "answer_text": answer_text,
        "evidence_refs": evidence_refs,
        "provider": provider,
        "model": settings.llm_model,
    }
