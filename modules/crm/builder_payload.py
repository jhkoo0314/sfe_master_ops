from __future__ import annotations

import re
from copy import deepcopy

from modules.crm.schemas import CompanyMasterStandard, CrmStandardActivity
from result_assets.crm_result_asset import CrmResultAsset


CHUNKED_CRM_DATA_MODE = "chunked_crm_scope_assets_v1"
_TEAM_ALL_TOKEN = "ALL"
_TEAM_ALL_LABEL = "전체 팀"
_REP_ALL_TOKEN = "ALL"
_REP_ALL_LABEL = "전체 담당자"

_TARGETS = {
    "hir": 0.80,
    "rtr": 0.75,
    "bcr": 0.75,
    "phr": 0.70,
    "nar": 0.80,
    "ahs": 80.0,
}

_COACH_WEIGHTS = [
    ("HIR", 0.30),
    ("RTR", 0.20),
    ("BCR", 0.15),
    ("PHR", 0.15),
    ("NAR", 0.10),
    ("AHS", 0.10),
]

_BEHAVIOR_KEYS = ["PT", "Demo", "Closing", "Needs", "FaceToFace", "Contact", "Access", "Feedback"]


def _sanitize_scope_token(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "").strip())
    return safe or "scope"


def _build_scope_chunk_name(scope_key: str) -> str:
    safe_scope = _sanitize_scope_token(scope_key)
    return f"{safe_scope}.js"


def _avg_key(rows: list[dict], key: str) -> float:
    values = [float(row.get(key, 0.0) or 0.0) for row in rows]
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _metric_tile(code: str, name: str, value: float, tone: str) -> dict:
    if code in {"HIR", "RTR", "BCR", "PHR", "NAR"}:
        return {
            "code": code,
            "name": name,
            "value": value,
            "display": f"{value:.2f}",
            "fill_pct": round(max(0.0, min(100.0, value * 100)), 1),
            "tone": tone,
        }
    if code in {"AHS", "PV", "PI"}:
        return {
            "code": code,
            "name": name,
            "value": value,
            "display": f"{value:.1f}",
            "fill_pct": round(max(0.0, min(100.0, value)), 1),
            "tone": tone,
        }
    if code == "FGR":
        return {
            "code": code,
            "name": name,
            "value": value,
            "display": f"{value:+.1f}%",
            "fill_pct": round(max(0.0, min(100.0, 50 + (value * 4))), 1),
            "tone": tone,
        }
    if code == "TRG":
        return {
            "code": code,
            "name": name,
            "value": value,
            "display": f"{value:+.1f}pt",
            "fill_pct": round(max(0.0, min(100.0, 100 - abs(value * 4))), 1),
            "tone": tone,
        }
    return {
        "code": code,
        "name": name,
        "value": value,
        "display": f"{value:.1f}%",
        "fill_pct": round(max(0.0, min(100.0, value)), 1),
        "tone": tone,
    }


def _month_label(metric_month: str) -> str:
    text = str(metric_month or "").strip()
    if len(text) == 6 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}"
    return text or "-"


def _build_monthly_rows(asset: CrmResultAsset) -> list[dict]:
    monthly_rows: list[dict] = []
    legacy_month_map = {str(row.metric_month): row for row in asset.monthly_kpi}
    for row in asset.monthly_kpi_11 or []:
        metric_month = str(row.metric_month)
        legacy = legacy_month_map.get(metric_month)
        total_visits = int(getattr(legacy, "total_visits", 0) or 0)
        detail_call_count = int(getattr(legacy, "detail_call_count", 0) or 0)
        detail_rate = round(detail_call_count / max(total_visits, 1), 4)
        monthly_rows.append(
            {
                "metric_month": metric_month,
                "month_label": _month_label(metric_month),
                "total_visits": total_visits,
                "total_reps_active": int(getattr(legacy, "total_reps_active", row.rep_count) or row.rep_count),
                "total_hospitals_visited": int(getattr(legacy, "total_hospitals_visited", 0) or 0),
                "avg_visits_per_rep": float(getattr(legacy, "avg_visits_per_rep", 0.0) or 0.0),
                "detail_call_count": detail_call_count,
                "detail_call_rate": detail_rate,
                "hir": float(row.metric_set.hir),
                "rtr": float(row.metric_set.rtr),
                "bcr": float(row.metric_set.bcr),
                "phr": float(row.metric_set.phr),
                "nar": float(row.metric_set.nar),
                "ahs": float(row.metric_set.ahs),
                "pv": float(row.metric_set.pv),
                "fgr": float(row.metric_set.fgr),
                "pi": float(row.metric_set.pi),
                "trg": float(row.metric_set.trg),
                "swr": float(row.metric_set.swr),
                "coach_score": float(row.metric_set.coach_score),
            }
        )
    if monthly_rows:
        return sorted(monthly_rows, key=lambda row: row["metric_month"])

    for row in asset.monthly_kpi or []:
        detail_rate = round(row.detail_call_count / max(row.total_visits, 1), 4)
        monthly_rows.append(
            {
                "metric_month": str(row.metric_month),
                "month_label": _month_label(str(row.metric_month)),
                "total_visits": row.total_visits,
                "total_reps_active": row.total_reps_active,
                "total_hospitals_visited": row.total_hospitals_visited,
                "avg_visits_per_rep": row.avg_visits_per_rep,
                "detail_call_count": row.detail_call_count,
                "detail_call_rate": detail_rate,
            }
        )
    return sorted(monthly_rows, key=lambda row: row["metric_month"])


def _build_rep_rows_by_month(asset: CrmResultAsset) -> tuple[dict[str, list[dict]], dict[str, str]]:
    profile_map = {p.rep_id: p for p in asset.behavior_profiles}
    branch_labels: dict[str, str] = {}
    rep_rows_by_month: dict[str, list[dict]] = {}

    for row in asset.rep_monthly_kpi_11 or []:
        metric_month = str(row.metric_month)
        profile = profile_map.get(row.rep_id)
        branch_id = (profile.branch_id if profile else "") or "UNASSIGNED"
        branch_name = (profile.branch_name if profile else "") or branch_id or _TEAM_ALL_LABEL
        branch_labels[branch_id] = branch_name
        rep_rows_by_month.setdefault(metric_month, []).append(
            {
                "metric_month": metric_month,
                "rep_id": row.rep_id,
                "rep_name": profile.rep_name if profile else row.rep_id,
                "branch_id": branch_id,
                "branch_name": branch_name,
                "hir": round(float(row.metric_set.hir) / 100.0, 3),
                "rtr": round(float(row.metric_set.rtr) / 100.0, 3),
                "bcr": round(float(row.metric_set.bcr) / 100.0, 3),
                "phr": round(float(row.metric_set.phr) / 100.0, 3),
                "nar": round(float(row.metric_set.nar) / 100.0, 3),
                "ahs": float(row.metric_set.ahs),
                "pv": float(row.metric_set.pv),
                "fgr": float(row.metric_set.fgr),
                "pi": float(row.metric_set.pi),
                "trg": float(row.metric_set.trg),
                "swr": float(row.metric_set.swr),
                "coach_score": round(float(row.metric_set.coach_score) / 100.0, 3),
                "total_visits": int(profile.total_visits) if profile else 0,
                "behavior_mix_8": dict(row.behavior_mix_8 or {}),
            }
        )

    for month, rows in rep_rows_by_month.items():
        rep_rows_by_month[month] = sorted(
            rows,
            key=lambda item: (item.get("coach_score", 0.0), item.get("hir", 0.0), item.get("total_visits", 0)),
            reverse=True,
        )
    return rep_rows_by_month, branch_labels


def _filter_rows(rep_rows_by_month: dict[str, list[dict]], period_token: str, team_token: str) -> tuple[list[dict], list[dict]]:
    selected_months = sorted(rep_rows_by_month.keys()) if period_token == "ALL" else [period_token]
    monthly_rows: list[dict] = []
    latest_rows: list[dict] = []
    for month in selected_months:
        month_rows = list(rep_rows_by_month.get(month, []))
        if team_token != _TEAM_ALL_TOKEN:
            month_rows = [row for row in month_rows if row.get("branch_id") == team_token]
        if month_rows:
            monthly_rows.extend(month_rows)
            latest_rows = month_rows
    return monthly_rows, latest_rows


def _build_trend_rows(monthly_rows: list[dict], period_token: str) -> dict:
    month_order = sorted({str(row.get("metric_month", "")) for row in monthly_rows if str(row.get("metric_month", "")).strip()})
    if period_token != "ALL":
        month_order = [period_token] if period_token in month_order else month_order[:1]
    trend_source: list[dict] = []
    for month in month_order:
        rows = [row for row in monthly_rows if str(row.get("metric_month", "")) == month]
        if not rows:
            continue
        trend_source.append(
            {
                "month_label": _month_label(month),
                "hir": _avg_key(rows, "hir"),
                "bcr": _avg_key(rows, "bcr"),
                "fgr": _avg_key(rows, "fgr"),
            }
        )
    return {
        "labels": [row["month_label"] for row in trend_source],
        "hir": [round(float(row.get("hir", 0.0)), 3) for row in trend_source],
        "bcr": [round(float(row.get("bcr", 0.0)), 3) for row in trend_source],
        "fgr": [round(float(row.get("fgr", 0.0)) - 100.0, 1) for row in trend_source],
    }


def _build_behavior_axis(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    axis: list[dict] = []
    for key in _BEHAVIOR_KEYS:
        score = round(
            sum(float((row.get("behavior_mix_8") or {}).get(key, 0.0) or 0.0) for row in rows) / max(len(rows), 1),
            3,
        )
        axis.append({"label": key, "score": score, "tone": "blue"})
    return axis


def _build_behavior_diagnosis(axis: list[dict]) -> str:
    if not axis:
        return "CRM KPI 자산 기준으로 표시됩니다."
    weakest = sorted(axis, key=lambda item: item["score"])[:2]
    if len(weakest) == 1:
        return f"{weakest[0]['label']}({weakest[0]['score'] * 100:.0f}%) 축 보강이 우선입니다."
    return f"{weakest[0]['label']}({weakest[0]['score'] * 100:.0f}%), {weakest[1]['label']}({weakest[1]['score'] * 100:.0f}%) 축 보강이 우선입니다."


def _build_kpi_banner(rows: list[dict]) -> dict:
    if not rows:
        return {"leading": [], "ops": [], "outcome": []}
    avg_hir = round(_avg_key(rows, "hir"), 3)
    avg_rtr = round(_avg_key(rows, "rtr"), 3)
    avg_bcr = round(_avg_key(rows, "bcr"), 3)
    avg_phr = round(_avg_key(rows, "phr"), 3)
    avg_nar = round(_avg_key(rows, "nar"), 3)
    avg_ahs = round(_avg_key(rows, "ahs"), 1)
    avg_pv = round(_avg_key(rows, "pv"), 1)
    avg_fgr = round(_avg_key(rows, "fgr"), 1) - 100.0
    avg_pi = round(_avg_key(rows, "pi"), 1)
    avg_trg = round(_avg_key(rows, "trg"), 1)
    avg_swr = round(_avg_key(rows, "swr"), 1)
    return {
        "leading": [
            _metric_tile("HIR", "High-Impact Rate", avg_hir, "blue"),
            _metric_tile("RTR", "Relationship Temp.", avg_rtr, "teal"),
            _metric_tile("BCR", "Behavior Consistency", avg_bcr, "purple"),
            _metric_tile("PHR", "Proactive Health", avg_phr, "pink"),
        ],
        "ops": [
            _metric_tile("NAR", "Next Action Reliability", avg_nar, "amber"),
            _metric_tile("AHS", "Account Health Score", avg_ahs, "amber"),
            _metric_tile("PV", "Pipeline Velocity", avg_pv, "amber"),
        ],
        "outcome": [
            _metric_tile("FGR", "Field Growth Rate", avg_fgr, "green"),
            _metric_tile("PI", "Prescription Index", avg_pi, "green"),
            _metric_tile("TRG", "Target Readiness Gap", avg_trg, "muted"),
            _metric_tile("SWR", "Share Win Rate", avg_swr, "muted"),
        ],
    }


def _build_radar(rows: list[dict]) -> dict:
    return {
        "labels": ["HIR", "RTR", "BCR", "PHR", "NAR", "AHS"],
        "team_avg": [
            round(_avg_key(rows, "hir"), 3),
            round(_avg_key(rows, "rtr"), 3),
            round(_avg_key(rows, "bcr"), 3),
            round(_avg_key(rows, "phr"), 3),
            round(_avg_key(rows, "nar"), 3),
            round(_avg_key(rows, "ahs") / 100.0, 3),
        ] if rows else [0, 0, 0, 0, 0, 0],
        "target": [
            _TARGETS["hir"],
            _TARGETS["rtr"],
            _TARGETS["bcr"],
            _TARGETS["phr"],
            _TARGETS["nar"],
            round(_TARGETS["ahs"] / 100.0, 3),
        ],
    }


def _build_coach_summary(rows: list[dict]) -> dict:
    return {
        "score": round(_avg_key(rows, "coach_score"), 3),
        "delta": 0,
        "delta_display": "+0.000",
        "weight_rows": [{"label": label, "value": weight} for label, weight in _COACH_WEIGHTS],
    }


def _build_rep_scope(rep_rows_all_months: list[dict], rep_token: str, period_label: str, team_label: str) -> dict | None:
    rep_rows = [row for row in rep_rows_all_months if row.get("rep_id") == rep_token]
    if not rep_rows:
        return None
    latest_row = sorted(rep_rows, key=lambda row: str(row.get("metric_month", "")))[-1]
    behavior_axis = [
        {"label": key, "score": round(float((latest_row.get("behavior_mix_8") or {}).get(key, 0.0) or 0.0), 3), "tone": "blue"}
        for key in _BEHAVIOR_KEYS
    ]
    return {
        "period_token": latest_row.get("metric_month", "ALL"),
        "period_label": period_label,
        "team_token": latest_row.get("branch_id", _TEAM_ALL_TOKEN),
        "team_label": team_label,
        "rep_token": rep_token,
        "rep_label": latest_row.get("rep_name", rep_token),
        "kpi_banner": _build_kpi_banner([latest_row]),
        "radar": _build_radar([latest_row]),
        "integrity": {
            "verified_pct": 0,
            "assisted_pct": 0,
            "self_only_pct": 0,
            "verified_count": 0,
            "assisted_count": 0,
            "self_only_count": 0,
            "penalty_count": 0,
            "unscored_count": 0,
        },
        "coach_summary": _build_coach_summary([latest_row]),
        "behavior_axis": behavior_axis,
        "behavior_diagnosis": _build_behavior_diagnosis(behavior_axis),
        "pipeline": {"stages": [], "avg_dwell_days": 0, "conversion_rate": 0},
        "matrix_rows": [latest_row],
        "trend": _build_trend_rows(rep_rows, period_token="ALL"),
        "quality_flags": [],
        "rep_options": [{"token": _REP_ALL_TOKEN, "label": _REP_ALL_LABEL}],
        "rep_scope_data": {},
    }


def _build_scope_payload(
    *,
    period_token: str,
    period_label: str,
    team_token: str,
    team_label: str,
    rep_rows_by_month: dict[str, list[dict]],
) -> dict:
    monthly_rows, latest_rows = _filter_rows(rep_rows_by_month, period_token, team_token)
    rep_options = [{"token": _REP_ALL_TOKEN, "label": _REP_ALL_LABEL}]
    rep_scope_data: dict[str, dict] = {}
    rep_pairs = {(row.get("rep_id"), row.get("rep_name")) for row in monthly_rows if row.get("rep_id")}
    for rep_id, rep_name in sorted(rep_pairs, key=lambda item: str(item[1] or item[0])):
        rep_options.append({"token": rep_id, "label": rep_name})
        rep_scope = _build_rep_scope(monthly_rows, rep_id, period_label, team_label)
        if rep_scope:
            rep_scope_data[rep_id] = rep_scope

    behavior_axis = _build_behavior_axis(latest_rows)
    return {
        "period_token": period_token,
        "period_label": period_label,
        "team_token": team_token,
        "team_label": team_label,
        "rep_token": _REP_ALL_TOKEN,
        "rep_label": _REP_ALL_LABEL,
        "kpi_banner": _build_kpi_banner(latest_rows),
        "radar": _build_radar(latest_rows),
        "integrity": {
            "verified_pct": 0,
            "assisted_pct": 0,
            "self_only_pct": 0,
            "verified_count": 0,
            "assisted_count": 0,
            "self_only_count": 0,
            "penalty_count": 0,
            "unscored_count": 0,
        },
        "coach_summary": _build_coach_summary(latest_rows),
        "behavior_axis": behavior_axis,
        "behavior_diagnosis": _build_behavior_diagnosis(behavior_axis),
        "pipeline": {"stages": [], "avg_dwell_days": 0, "conversion_rate": 0},
        "matrix_rows": latest_rows,
        "trend": _build_trend_rows(monthly_rows, period_token=period_token),
        "quality_flags": [],
        "rep_options": rep_options,
        "rep_scope_data": rep_scope_data,
    }


def _build_basic_payload(asset: CrmResultAsset, summary: dict, company_name: str) -> dict:
    monthly_rows = _build_monthly_rows(asset)
    rep_rows_by_month, branch_labels = _build_rep_rows_by_month(asset)

    period_options = [{"token": "ALL", "label": "전체 기간"}]
    for row in monthly_rows:
        period_options.append({"token": row["metric_month"], "label": row["month_label"]})

    team_options = [{"token": _TEAM_ALL_TOKEN, "label": _TEAM_ALL_LABEL}]
    for branch_id, branch_name in sorted(branch_labels.items(), key=lambda item: item[1]):
        team_options.append({"token": branch_id, "label": branch_name})

    default_period = monthly_rows[-1]["metric_month"] if monthly_rows else "ALL"
    default_team = _TEAM_ALL_TOKEN
    default_rep = _REP_ALL_TOKEN

    scope_data: dict[str, dict] = {}
    periods = [("ALL", "전체 기간")] + [(row["metric_month"], row["month_label"]) for row in monthly_rows]
    teams = [(_TEAM_ALL_TOKEN, _TEAM_ALL_LABEL)] + sorted(branch_labels.items(), key=lambda item: item[1])
    for period_token, period_label in periods:
        for team_token, team_label in teams:
            scope_key = f"{period_token}|{team_token}"
            scope_data[scope_key] = _build_scope_payload(
                period_token=period_token,
                period_label=period_label,
                team_token=team_token,
                team_label=team_label,
                rep_rows_by_month=rep_rows_by_month,
            )

    all_scope = scope_data.get(f"ALL|{_TEAM_ALL_TOKEN}", {})

    return {
        "company": company_name,
        "generated_at": asset.generated_at.isoformat(),
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
        "activity_context": asset.activity_context.model_dump(mode="json"),
        "mapping_quality": asset.mapping_quality.model_dump(mode="json"),
        "logic_reference": {
            "core_kpis": ["HIR", "RTR", "BCR", "PHR"],
            "ops_kpis": ["NAR", "AHS", "PV"],
            "result_kpis": ["FGR", "PI", "TRG", "SWR"],
            "weights": [{"label": label, "value": weight} for label, weight in _COACH_WEIGHTS],
            "note": "Builder is rendering-only. KPI source: crm_result_asset (rep_monthly_kpi_11/monthly_kpi_11).",
        },
        "filters": {
            "period_options": period_options,
            "team_options": team_options,
            "rep_options": deepcopy((all_scope.get("rep_options") or [{"token": _REP_ALL_TOKEN, "label": _REP_ALL_LABEL}])),
            "default_period": default_period,
            "default_team": default_team,
            "default_rep": default_rep,
        },
        "scope_data": scope_data,
    }


def build_crm_builder_payload(
    asset: CrmResultAsset,
    summary: dict,
    company_name: str,
    activities: list[CrmStandardActivity] | None = None,
    company_master: list[CompanyMasterStandard] | None = None,
) -> dict:
    # Builder는 KPI를 다시 계산하지 않고 crm_result_asset에 이미 들어 있는 결과를 화면용 구조로 조립한다.
    _ = activities
    _ = company_master
    return _build_basic_payload(asset, summary, company_name)


def build_chunked_crm_payload(payload: dict) -> tuple[dict, dict[str, dict]]:
    scope_data = payload.get("scope_data", {}) or {}
    filters = payload.get("filters", {}) or {}

    manifest = {
        key: value
        for key, value in payload.items()
        if key != "scope_data"
    }
    manifest["data_mode"] = CHUNKED_CRM_DATA_MODE
    manifest["asset_base"] = ""
    manifest["scope_data"] = {}
    manifest["scope_asset_manifest"] = {}

    default_scope_key = f"{filters.get('default_period', 'ALL')}|{filters.get('default_team', 'ALL')}"
    if default_scope_key not in scope_data:
        default_scope_key = next(iter(scope_data), default_scope_key)
    manifest["default_scope_key"] = default_scope_key

    asset_chunks: dict[str, dict] = {}
    rep_scope_count = 0
    for scope_key, scope_payload in scope_data.items():
        scope_token = str(scope_key or "").strip()
        if not scope_token:
            continue
        chunk_name = _build_scope_chunk_name(scope_token)
        manifest["scope_asset_manifest"][scope_token] = chunk_name
        asset_chunks[chunk_name] = {
            "scope_key": scope_token,
            "scope_payload": scope_payload,
        }
        rep_scope_count += len((scope_payload or {}).get("rep_scope_data", {}) or {})

    manifest["scope_asset_counts"] = {
        "scope_count": len(manifest["scope_asset_manifest"]),
        "rep_scope_count": rep_scope_count,
    }
    return manifest, asset_chunks
