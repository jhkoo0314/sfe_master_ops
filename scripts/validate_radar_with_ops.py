from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root
from modules.radar.schemas import (
    RadarInputStandard,
    RadarKpiSummary,
    RadarMeta,
    RadarSandboxSummary,
    RadarScopeSummaries,
    RadarValidationSummary,
)
from modules.radar.service import build_radar_result_asset
from result_assets.crm_result_asset import CrmResultAsset
from result_assets.sandbox_result_asset import SandboxResultAsset


COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
SANDBOX_ROOT = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "sandbox"
SANDBOX_ASSET_PATH = SANDBOX_ROOT / "sandbox_result_asset.json"
SANDBOX_EVAL_PATH = SANDBOX_ROOT / "sandbox_ops_evaluation.json"
CRM_ASSET_PATH = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "crm" / "crm_result_asset.json"
OUTPUT_ROOT = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "radar"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _to_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _calc_pv_change_pct(template_payload: dict) -> float:
    total = template_payload.get("total", {}) if isinstance(template_payload, dict) else {}
    monthly_actual = total.get("monthly_actual", []) if isinstance(total, dict) else []
    if not isinstance(monthly_actual, list):
        return 0.0
    series = [_to_float(v, 0.0) for v in monthly_actual if _to_float(v, 0.0) > 0]
    if len(series) < 2:
        return 0.0
    prev_val = series[-2]
    cur_val = series[-1]
    if prev_val <= 0:
        return 0.0
    return round(((cur_val - prev_val) / prev_val) * 100.0, 1)


def _month_label(metric_month: str) -> str:
    text = str(metric_month or "").strip()
    if len(text) == 6 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}"
    return text or "-"


def _build_scope_summaries(template_payload: dict, block_payload: dict) -> tuple[list[dict], list[dict], list[dict]]:
    branches_obj = template_payload.get("branches", {}) if isinstance(template_payload, dict) else {}
    if not isinstance(branches_obj, dict) or not branches_obj:
        branch_summary = block_payload.get("branch_summary", {}) if isinstance(block_payload, dict) else {}
        branches_obj = branch_summary.get("branches", {}) if isinstance(branch_summary, dict) else {}
    by_branch: list[dict] = []
    by_rep: list[dict] = []
    member_lookup_by_branch = {}
    branch_member_summary = block_payload.get("branch_member_summary", {}) if isinstance(block_payload, dict) else {}
    if isinstance(branch_member_summary, dict):
        member_lookup_by_branch = branch_member_summary.get("members_by_branch", {}) or {}

    if isinstance(branches_obj, dict):
        for branch_name, branch_payload in branches_obj.items():
            if not isinstance(branch_payload, dict):
                continue
            avg = branch_payload.get("avg", {}) if isinstance(branch_payload.get("avg", {}), dict) else {}
            achieve = _to_float(branch_payload.get("achieve"), 0.0)
            by_branch.append(
                {
                    "branch_name": str(branch_name),
                    "attainment_pct": round(achieve, 1),
                    "hir": round(_to_float(avg.get("HIR"), 0.0), 1),
                    "rtr": round(_to_float(avg.get("RTR"), 0.0), 1),
                    "member_count": len(branch_payload.get("members", []) or []),
                }
            )
            member_rows = branch_payload.get("members", []) or member_lookup_by_branch.get(branch_name, []) or []
            for member in member_rows:
                if not isinstance(member, dict):
                    continue
                by_rep.append(
                    {
                        "rep_id": str(member.get("rep_id") or ""),
                        "rep_name": str(member.get("성명") or member.get("rep_name") or ""),
                        "branch_name": str(branch_name),
                        "attainment_pct": round(_to_float(member.get("PI"), 0.0), 1),
                        "hir": round(_to_float(member.get("HIR"), 0.0), 1),
                        "rtr": round(_to_float(member.get("RTR"), 0.0), 1),
                    }
                )

    by_product: list[dict] = []
    prod_obj = template_payload.get("total_prod_analysis", {}) if isinstance(template_payload, dict) else {}
    if (not isinstance(prod_obj, dict) or not prod_obj) and isinstance(block_payload, dict):
        product_analysis = block_payload.get("product_analysis", {}) or {}
        if isinstance(product_analysis, dict):
            prod_obj = product_analysis.get("total_prod_analysis", {}) or {}
    if isinstance(prod_obj, dict):
        for product_name, product_payload in prod_obj.items():
            if not isinstance(product_payload, dict):
                continue
            avg = product_payload.get("avg", {}) if isinstance(product_payload.get("avg", {}), dict) else {}
            by_product.append(
                {
                    "product_name": str(product_name),
                    "attainment_pct": round(_to_float(product_payload.get("achieve"), 0.0), 1),
                    "hir": round(_to_float(avg.get("HIR"), 0.0), 1),
                    "rtr": round(_to_float(avg.get("RTR"), 0.0), 1),
                }
            )

    by_branch = sorted(by_branch, key=lambda row: row.get("attainment_pct", 0.0))
    by_rep = sorted(by_rep, key=lambda row: row.get("attainment_pct", 0.0))
    by_product = sorted(by_product, key=lambda row: row.get("attainment_pct", 0.0))
    return by_branch[:30], by_rep[:100], by_product[:50]


def _build_trend_series(
    template_payload: dict,
    metric_months: list[str],
    crm_asset: CrmResultAsset | None,
) -> dict[str, list]:
    total_payload = template_payload.get("total", {}) if isinstance(template_payload, dict) else {}
    monthly_actual = total_payload.get("monthly_actual", []) if isinstance(total_payload, dict) else []
    monthly_target = total_payload.get("monthly_target", []) if isinstance(total_payload, dict) else []

    labels = [_month_label(month) for month in metric_months]
    goal_attainment: list[float] = []
    for idx, _month in enumerate(metric_months):
        actual = _to_float(monthly_actual[idx] if idx < len(monthly_actual) else 0.0, 0.0)
        target = _to_float(monthly_target[idx] if idx < len(monthly_target) else 0.0, 0.0)
        if target > 0:
            goal_attainment.append(round((actual / target) * 100.0, 1))
        else:
            goal_attainment.append(0.0)

    hir_series: list[float] = []
    rtr_series: list[float] = []
    if crm_asset is not None:
        month_map = {str(row.metric_month): row for row in crm_asset.monthly_kpi_11}
        for month in metric_months:
            row = month_map.get(str(month))
            if row is None:
                hir_series.append(0.0)
                rtr_series.append(0.0)
                continue
            hir_series.append(round(_to_float(row.metric_set.hir, 0.0), 1))
            rtr_series.append(round(_to_float(row.metric_set.rtr, 0.0), 1))

    return {
        "labels": labels,
        "goal_attainment": goal_attainment,
        "hir": hir_series,
        "rtr": rtr_series,
    }


def _build_trend_flags(goal_attainment_pct: float, pv_change_pct: float, hir: float, rtr: float) -> list[str]:
    flags: list[str] = []
    if goal_attainment_pct < 95.0:
        flags.append("goal_attainment_below_95")
    if pv_change_pct < 0.0:
        flags.append("pv_negative_trend")
    if hir < 70.0:
        flags.append("hir_below_70")
    if rtr < 75.0:
        flags.append("rtr_below_75")
    return flags


def _build_validation_summary(eval_payload: dict | None) -> tuple[RadarValidationSummary, str]:
    if not eval_payload:
        return RadarValidationSummary(status="usable", warnings=["sandbox_ops_evaluation_missing"], quality_score=0.7), "validation_usable"

    raw_status = str(eval_payload.get("quality_status", "")).strip().upper()
    status_map = {
        "PASS": "approved",
        "WARN": "usable",
        "FAIL": "rejected",
    }
    mapped_status = status_map.get(raw_status, "usable")
    quality_score = _to_float(eval_payload.get("quality_score"), 70.0) / 100.0
    quality_score = max(0.0, min(1.0, quality_score))
    source_status = "validation_approved" if mapped_status == "approved" else "validation_usable"
    warnings = [] if mapped_status == "approved" else [f"source_quality_status={raw_status or 'UNKNOWN'}"]
    return RadarValidationSummary(status=mapped_status, warnings=warnings, quality_score=quality_score), source_status


def main() -> None:
    if not SANDBOX_ASSET_PATH.exists():
        raise FileNotFoundError(f"Sandbox result asset not found: {SANDBOX_ASSET_PATH}")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    sandbox_asset = SandboxResultAsset.model_validate(_load_json(SANDBOX_ASSET_PATH))
    crm_asset = CrmResultAsset.model_validate(_load_json(CRM_ASSET_PATH)) if CRM_ASSET_PATH.exists() else None
    eval_payload = _load_json(SANDBOX_EVAL_PATH) if SANDBOX_EVAL_PATH.exists() else None
    validation_summary, source_status = _build_validation_summary(eval_payload)

    template_payload = {}
    block_payload = {}
    if sandbox_asset.dashboard_payload and isinstance(sandbox_asset.dashboard_payload.template_payload, dict):
        template_payload = sandbox_asset.dashboard_payload.template_payload
    if sandbox_asset.dashboard_payload and isinstance(sandbox_asset.dashboard_payload.block_payload, dict):
        block_payload = sandbox_asset.dashboard_payload.block_payload

    total_avg = template_payload.get("total_avg", {}) if isinstance(template_payload, dict) else {}
    metrics = sandbox_asset.analysis_summary.custom_metrics or {}
    goal_attainment_pct = _to_float(
        metrics.get("annual_attainment_rate", metrics.get("monthly_attainment_rate", 0.0)),
        0.0,
    )
    pv_change_pct = _calc_pv_change_pct(template_payload)
    hir = _to_float(total_avg.get("HIR"), 0.0)
    rtr = _to_float(total_avg.get("RTR"), 0.0)
    bcr = _to_float(total_avg.get("BCR"), 0.0)
    phr = _to_float(total_avg.get("PHR"), 0.0)

    by_branch, by_rep, by_product = _build_scope_summaries(template_payload, block_payload)
    top_declines = by_branch[:5]
    top_gains = sorted(by_branch, key=lambda row: row.get("attainment_pct", 0.0), reverse=True)[:5]
    trend_flags = _build_trend_flags(goal_attainment_pct, pv_change_pct, hir, rtr)
    trend_series = _build_trend_series(template_payload, sandbox_asset.metric_months, crm_asset)

    period_value = sandbox_asset.metric_months[-1] if sandbox_asset.metric_months else datetime.now().strftime("%Y%m")
    meta = RadarMeta(
        company_key=COMPANY_KEY,
        run_id=f"radar-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        period_type="monthly",
        period_value=period_value,
        source_status=source_status,
    )
    radar_input = RadarInputStandard(
        meta=meta,
        kpi_summary=RadarKpiSummary(
            goal_attainment_pct=round(goal_attainment_pct, 1),
            pv_change_pct=round(pv_change_pct, 1),
            hir=round(hir, 1),
            rtr=round(rtr, 1),
            bcr=round(bcr, 1),
            phr=round(phr, 1),
        ),
        scope_summaries=RadarScopeSummaries(
            by_branch=by_branch,
            by_rep=by_rep,
            by_product=by_product,
        ),
        validation_summary=validation_summary,
        sandbox_summary=RadarSandboxSummary(
            top_declines=top_declines,
            top_gains=top_gains,
            trend_flags=trend_flags,
            trend_series=trend_series,
        ),
    )
    radar_asset = build_radar_result_asset(radar_input)

    (OUTPUT_ROOT / "radar_input_standard.json").write_text(
        json.dumps(radar_input.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "radar_result_asset.json").write_text(
        json.dumps(radar_asset.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "scenario": sandbox_asset.scenario,
        "quality_status": validation_summary.status,
        "quality_score": round(validation_summary.quality_score * 100.0, 1),
        "period_value": period_value,
        "signal_count": radar_asset.summary.signal_count,
        "overall_status": radar_asset.summary.overall_status,
        "top_issue": radar_asset.summary.top_issue,
        "next_modules": ["builder"],
    }
    (OUTPUT_ROOT / "radar_validation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Validated {COMPANY_NAME} radar data with OPS:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
