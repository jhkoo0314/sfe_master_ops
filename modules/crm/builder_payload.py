from __future__ import annotations

import re

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


def _build_basic_payload(asset: CrmResultAsset, summary: dict, company_name: str) -> dict:
    monthly_rows: list[dict] = []
    legacy_month_map = {str(row.metric_month): row for row in asset.monthly_kpi}

    if asset.monthly_kpi_11:
        for row in asset.monthly_kpi_11:
            legacy = legacy_month_map.get(str(row.metric_month))
            total_visits = int(getattr(legacy, "total_visits", 0) or 0)
            detail_call_count = int(getattr(legacy, "detail_call_count", 0) or 0)
            detail_rate = round(detail_call_count / max(total_visits, 1), 4)
            monthly_rows.append(
                {
                    "metric_month": str(row.metric_month),
                    "month_label": f"{str(row.metric_month)[:4]}-{str(row.metric_month)[4:6]}",
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
    else:
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
    profile_map = {p.rep_id: p for p in asset.behavior_profiles}
    latest_month = None
    if asset.rep_monthly_kpi_11:
        latest_month = max(str(row.metric_month) for row in asset.rep_monthly_kpi_11)
        for row in asset.rep_monthly_kpi_11:
            if str(row.metric_month) != latest_month:
                continue
            profile = profile_map.get(row.rep_id)
            rep_rows.append(
                {
                    "rep_id": row.rep_id,
                    "rep_name": profile.rep_name if profile else row.rep_id,
                    "branch_id": profile.branch_id if profile else "",
                    "branch_name": (profile.branch_name if profile else "") or (profile.branch_id if profile else ""),
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
                    "behavior_mix_8": row.behavior_mix_8,
                }
            )

    rep_rows = sorted(rep_rows, key=lambda row: (row.get("coach_score", 0.0), row.get("hir", 0.0), row.get("total_visits", 0)), reverse=True)

    team_avg_hir = round(_avg_key(rep_rows, "hir"), 3)
    team_avg_rtr = round(_avg_key(rep_rows, "rtr"), 3)
    team_avg_bcr = round(_avg_key(rep_rows, "bcr"), 3)
    team_avg_phr = round(_avg_key(rep_rows, "phr"), 3)
    team_avg_nar = round(_avg_key(rep_rows, "nar"), 3)
    team_avg_ahs_norm = round(_avg_key(rep_rows, "ahs") / 100.0, 3)
    team_avg_coach = round(_avg_key(rep_rows, "coach_score"), 3)

    trend_labels = [row["month_label"] for row in monthly_rows]
    trend_hir = [round(float(row.get("hir", 0.0) or 0.0) / 100.0, 3) for row in monthly_rows if "hir" in row]
    trend_bcr = [round(float(row.get("bcr", 0.0) or 0.0) / 100.0, 3) for row in monthly_rows if "bcr" in row]
    trend_fgr = [round(float(row.get("fgr", 0.0) or 0.0) - 100.0, 1) for row in monthly_rows if "fgr" in row]

    latest_month_kpi = None
    if monthly_rows:
        latest_month_kpi = monthly_rows[-1]

    leading = []
    ops = []
    outcome = []
    if latest_month_kpi:
        leading = [
            _metric_tile("HIR", "High-Impact Rate", round(float(latest_month_kpi.get("hir", 0.0)) / 100.0, 3), "blue"),
            _metric_tile("RTR", "Relationship Temp.", round(float(latest_month_kpi.get("rtr", 0.0)) / 100.0, 3), "teal"),
            _metric_tile("BCR", "Behavior Consistency", round(float(latest_month_kpi.get("bcr", 0.0)) / 100.0, 3), "purple"),
            _metric_tile("PHR", "Proactive Health", round(float(latest_month_kpi.get("phr", 0.0)) / 100.0, 3), "pink"),
        ]
        ops = [
            _metric_tile("NAR", "Next Action Reliability", round(float(latest_month_kpi.get("nar", 0.0)) / 100.0, 3), "amber"),
            _metric_tile("AHS", "Account Health Score", float(latest_month_kpi.get("ahs", 0.0)), "amber"),
            _metric_tile("PV", "Pipeline Velocity", float(latest_month_kpi.get("pv", 0.0)), "amber"),
        ]
        outcome = [
            _metric_tile("FGR", "Field Growth Rate", float(latest_month_kpi.get("fgr", 0.0)) - 100.0, "green"),
            _metric_tile("PI", "Prescription Index", float(latest_month_kpi.get("pi", 0.0)), "green"),
            _metric_tile("TRG", "Target Readiness Gap", float(latest_month_kpi.get("trg", 0.0)), "muted"),
            _metric_tile("SWR", "Share Win Rate", float(latest_month_kpi.get("swr", 0.0)), "muted"),
        ]

    behavior_keys = ["PT", "Demo", "Closing", "Needs", "FaceToFace", "Contact", "Access", "Feedback"]
    behavior_axis: list[dict] = []
    if rep_rows:
        for key in behavior_keys:
            score = round(_avg_key([row.get("behavior_mix_8", {}) for row in rep_rows], key), 3)
            behavior_axis.append({"label": key, "score": score, "tone": "blue"})

    behavior_diagnosis = "CRM KPI 자산 기준으로 표시됩니다."
    if behavior_axis:
        weakest = sorted(behavior_axis, key=lambda item: item["score"])[:2]
        behavior_diagnosis = f"{weakest[0]['label']}({weakest[0]['score'] * 100:.0f}%), {weakest[1]['label']}({weakest[1]['score'] * 100:.0f}%) 축 보강이 우선입니다."

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
            "period_options": [{"token": "ALL", "label": "전체 기간"}],
            "team_options": [{"token": _TEAM_ALL_TOKEN, "label": _TEAM_ALL_LABEL}],
            "rep_options": [{"token": _REP_ALL_TOKEN, "label": _REP_ALL_LABEL}],
            "default_period": "ALL",
            "default_team": _TEAM_ALL_TOKEN,
            "default_rep": _REP_ALL_TOKEN,
        },
        "scope_data": {
            f"ALL|{_TEAM_ALL_TOKEN}": {
                "period_token": "ALL",
                "period_label": "전체 기간",
                "team_token": _TEAM_ALL_TOKEN,
                "team_label": _TEAM_ALL_LABEL,
                "rep_token": _REP_ALL_TOKEN,
                "rep_label": _REP_ALL_LABEL,
                "kpi_banner": {"leading": leading, "ops": ops, "outcome": outcome},
                "radar": {
                    "labels": ["HIR", "RTR", "BCR", "PHR", "NAR", "AHS"],
                    "team_avg": [team_avg_hir, team_avg_rtr, team_avg_bcr, team_avg_phr, team_avg_nar, team_avg_ahs_norm],
                    "target": [
                        _TARGETS["hir"],
                        _TARGETS["rtr"],
                        _TARGETS["bcr"],
                        _TARGETS["phr"],
                        _TARGETS["nar"],
                        round(_TARGETS["ahs"] / 100.0, 3),
                    ],
                },
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
                "coach_summary": {
                    "score": team_avg_coach,
                    "delta": 0,
                    "delta_display": "+0.000",
                    "weight_rows": [{"label": label, "value": weight} for label, weight in _COACH_WEIGHTS],
                },
                "behavior_axis": behavior_axis,
                "behavior_diagnosis": behavior_diagnosis,
                "pipeline": {"stages": [], "avg_dwell_days": 0, "conversion_rate": 0},
                "matrix_rows": rep_rows,
                "trend": {"labels": trend_labels, "hir": trend_hir, "bcr": trend_bcr, "fgr": trend_fgr},
                "quality_flags": [],
                "rep_options": [{"token": _REP_ALL_TOKEN, "label": _REP_ALL_LABEL}],
                "rep_scope_data": {},
            }
        },
    }


def build_crm_builder_payload(
    asset: CrmResultAsset,
    summary: dict,
    company_name: str,
    activities: list[CrmStandardActivity] | None = None,
    company_master: list[CompanyMasterStandard] | None = None,
) -> dict:
    # Phase 4: Builder는 계산하지 않고 CRM Result Asset만 주입한다.
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
