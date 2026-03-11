from __future__ import annotations

import pandas as pd
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
    "coach": 0.75,
}

_COACH_WEIGHTS = [
    ("HIR", 0.30),
    ("RTR", 0.20),
    ("BCR", 0.15),
    ("PHR", 0.15),
    ("NAR", 0.10),
    ("AHS", 0.10),
]


def _clip01(value: float | int | None) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(1.0, float(value)))


def _normalize_trust(raw: str | None) -> str:
    value = str(raw or "").strip().lower()
    if value in {"verified", "assist", "verified_input"}:
        return "verified"
    if value in {"assisted", "assist_only"}:
        return "assisted"
    if value in {"self_only", "self", "manual"}:
        return "self_only"
    return "unknown"


def _month_to_label(metric_month: str) -> str:
    text = str(metric_month or "")
    return f"{text[:4]}-{text[4:6]}"


def _month_to_quarter(month_label: str) -> str:
    year = month_label[:4]
    month = int(month_label[5:7])
    quarter = ((month - 1) // 3) + 1
    return f"{year}-Q{quarter}"


def _safe_mean(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return 0.0
    return float(values.mean())


def _safe_corr(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 3:
        return 0.0
    corr = pd.Series(left, dtype="float64").corr(pd.Series(right, dtype="float64"))
    if pd.isna(corr):
        return 0.0
    return float(corr)


def _tag_tone(status: str) -> str:
    mapping = {
        "PASS": "tag-v",
        "AT RISK": "tag-a",
        "CHECK": "tag-s",
        "IMPROVED": "tag-blue",
    }
    return mapping.get(status, "tag-muted")


def _sanitize_scope_token(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "").strip())
    return safe or "scope"


def _build_scope_chunk_name(scope_key: str) -> str:
    safe_scope = _sanitize_scope_token(scope_key)
    return f"{safe_scope}.js"


def _build_basic_payload(asset: CrmResultAsset, summary: dict, company_name: str) -> dict:
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
        rep_rows.append(
            {
                "rep_id": profile.rep_id,
                "rep_name": profile.rep_name,
                "branch_id": profile.branch_id,
                "branch_name": profile.branch_name or profile.branch_id,
                "hir": round(hir_proxy / 100, 3),
                "rtr": round(min(1.0, (reach_proxy / 100) * 0.7 + (intensity_proxy / 100) * 0.3), 3),
                "bcr": round(bcr_proxy / 100, 3),
                "phr": round(min(1.0, (hir_proxy / 100) * 0.55 + (bcr_proxy / 100) * 0.45), 3),
                "nar": round(min(1.0, (bcr_proxy / 100) * 0.6 + (reach_proxy / 100) * 0.4), 3),
                "ahs": round(min(100.0, (reach_proxy * 0.45) + (intensity_proxy * 0.55)), 1),
                "coach_score": 0.0,
                "total_visits": profile.total_visits,
            }
        )
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
            "note": "Fallback CRM payload. Run CRM validation again to generate the full analysis payload.",
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
                "kpi_banner": {"leading": [], "ops": [], "outcome": []},
                "radar": {"labels": ["HIR", "RTR", "BCR", "PHR", "NAR", "AHS"], "team_avg": [0, 0, 0, 0, 0, 0], "target": [0, 0, 0, 0, 0, 0]},
                "integrity": {"verified_pct": 0, "assisted_pct": 0, "self_only_pct": 0, "verified_count": 0, "assisted_count": 0, "self_only_count": 0, "penalty_count": 0, "unscored_count": 0},
                "coach_summary": {"score": 0, "delta": 0, "delta_display": "+0.000", "weight_rows": [{"label": label, "value": weight} for label, weight in _COACH_WEIGHTS]},
                "behavior_axis": [],
                "behavior_diagnosis": "CRM activity-level payload is not available.",
                "pipeline": {"stages": [], "avg_dwell_days": 0, "conversion_rate": 0},
                "matrix_rows": rep_rows,
                "trend": {"labels": [row["month_label"] for row in monthly_rows], "hir": [], "bcr": [], "fgr": []},
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
    if not activities or not company_master:
        return _build_basic_payload(asset, summary, company_name)

    activity_rows: list[dict] = []
    for act in activities:
        month_label = _month_to_label(act.metric_month)
        quarter_label = _month_to_quarter(month_label)
        activity_rows.append(
            {
                "rep_id": str(act.rep_id),
                "rep_name": str(act.rep_name or act.rep_id),
                "branch_id": str(act.branch_id),
                "branch_name": str(act.branch_name or act.branch_id or "미지정"),
                "hospital_id": str(act.hospital_id),
                "activity_date": pd.to_datetime(act.activity_date),
                "metric_month": str(act.metric_month),
                "month_label": month_label,
                "quarter_label": quarter_label,
                "year_label": month_label[:4],
                "activity_type": str(act.activity_type or ""),
                "visit_count": int(act.visit_count or 0),
                "detail_flag": int(bool(act.has_detail_call)),
                "trust_level": _normalize_trust(act.trust_level),
                "note_flag": int(bool(str(act.notes or "").strip())),
                "next_action_flag": int(bool(str(act.next_action_text or "").strip())),
                "quality_factor": float(act.quality_factor) if act.quality_factor is not None else None,
                "impact_factor": float(act.impact_factor) if act.impact_factor is not None else None,
                "weighted_activity_score": float(act.weighted_activity_score) if act.weighted_activity_score is not None else None,
                "sentiment_score": float(act.sentiment_score) if act.sentiment_score is not None else None,
            }
        )
    activity_df = pd.DataFrame(activity_rows)
    if activity_df.empty:
        return _build_basic_payload(asset, summary, company_name)

    activity_df["trust_weight"] = activity_df["trust_level"].map(
        {"verified": 1.0, "assisted": 0.72, "self_only": 0.42, "unknown": 0.25}
    ).fillna(0.25)
    activity_df["quality_factor_filled"] = pd.to_numeric(activity_df["quality_factor"], errors="coerce")
    activity_df["impact_factor_filled"] = pd.to_numeric(activity_df["impact_factor"], errors="coerce")
    activity_df["weighted_activity_score_filled"] = pd.to_numeric(activity_df["weighted_activity_score"], errors="coerce")
    activity_df["sentiment_score_filled"] = pd.to_numeric(activity_df["sentiment_score"], errors="coerce")

    assignment_rows: list[dict] = []
    for row in company_master:
        assignment_rows.append(
            {
                "rep_id": str(row.rep_id),
                "rep_name": str(row.rep_name),
                "branch_id": str(row.branch_id),
                "branch_name": str(row.branch_name or row.branch_id or "미지정"),
                "hospital_id": str(row.hospital_id),
            }
        )
    assignment_df = pd.DataFrame(assignment_rows).drop_duplicates(subset=["rep_id", "hospital_id"])
    if assignment_df.empty:
        return _build_basic_payload(asset, summary, company_name)

    month_tokens = sorted(activity_df["month_label"].dropna().astype(str).unique().tolist())
    quarter_tokens = sorted(activity_df["quarter_label"].dropna().astype(str).unique().tolist())
    year_tokens = sorted(activity_df["year_label"].dropna().astype(str).unique().tolist())

    period_to_months: dict[str, list[str]] = {"ALL": month_tokens}
    period_kind: dict[str, str] = {"ALL": "all"}
    for year in year_tokens:
        period_to_months[year] = [month for month in month_tokens if month.startswith(year)]
        period_kind[year] = "year"
    for quarter in quarter_tokens:
        period_to_months[quarter] = [month for month in month_tokens if _month_to_quarter(month) == quarter]
        period_kind[quarter] = "quarter"
    for month in month_tokens:
        period_to_months[month] = [month]
        period_kind[month] = "month"

    branch_df = assignment_df[["branch_id", "branch_name"]].drop_duplicates()
    branch_df = branch_df.sort_values(["branch_name", "branch_id"], kind="stable")
    team_options = [{"token": _TEAM_ALL_TOKEN, "label": _TEAM_ALL_LABEL}]
    for row in branch_df.to_dict(orient="records"):
        team_options.append({"token": str(row["branch_id"]), "label": str(row["branch_name"])})

    assigned_hospital_counts = assignment_df.groupby("branch_id")["hospital_id"].nunique().to_dict()
    assigned_hospital_counts[_TEAM_ALL_TOKEN] = int(assignment_df["hospital_id"].nunique())
    rep_assigned_counts = assignment_df.groupby("rep_id")["hospital_id"].nunique().to_dict()
    activity_by_rep = {
        str(rep_id): rep_df.copy()
        for rep_id, rep_df in activity_df.groupby("rep_id", dropna=False)
    }

    def _score_scope(scope_df: pd.DataFrame, prospect_count: int) -> dict:
        if scope_df.empty:
            axis_rows = [
                {"label": "Approach", "score": 0.0, "tone": "blue"},
                {"label": "Contact", "score": 0.0, "tone": "blue"},
                {"label": "Visit", "score": 0.0, "tone": "teal"},
                {"label": "Presentation", "score": 0.0, "tone": "amber"},
                {"label": "Question", "score": 0.0, "tone": "teal"},
                {"label": "Need Creation", "score": 0.0, "tone": "red"},
                {"label": "Demonstration", "score": 0.0, "tone": "amber"},
                {"label": "Follow-up", "score": 0.0, "tone": "green"},
            ]
            return {
                "activity_count": 0,
                "total_visits": 0,
                "unique_reps": 0,
                "unique_hospitals": 0,
                "detail_count": 0,
                "verified_count": 0,
                "assisted_count": 0,
                "self_only_count": 0,
                "verified_pct": 0.0,
                "assisted_pct": 0.0,
                "self_only_pct": 0.0,
                "penalty_count": 0,
                "unscored_count": 0,
                "hir": 0.0,
                "rtr": 0.0,
                "bcr": 0.0,
                "phr": 0.0,
                "nar": 0.0,
                "ahs": 0.0,
                "pv": 0.0,
                "pi": 0.0,
                "swr": 0.0,
                "coach_score": 0.0,
                "target_gap": -_TARGETS["coach"] * 100,
                "axis_rows": axis_rows,
                "behavior_diagnosis": "데이터가 없어 행동축 진단을 만들지 못했습니다.",
                "prospect_count": int(prospect_count),
                "contact_count": 0,
                "presentation_count": 0,
                "negotiation_count": 0,
                "close_count": 0,
                "avg_dwell_days": 0.0,
                "conversion_rate": 0.0,
                "nps_proxy": 0.0,
            }

        activity_count = int(len(scope_df))
        total_visits = int(scope_df["visit_count"].sum())
        unique_reps = int(scope_df["rep_id"].nunique())
        unique_hospitals = int(scope_df["hospital_id"].nunique())
        detail_count = int(scope_df["detail_flag"].sum())
        detail_rate = detail_count / max(activity_count, 1)
        verified_count = int((scope_df["trust_level"] == "verified").sum())
        assisted_count = int((scope_df["trust_level"] == "assisted").sum())
        self_only_count = int((scope_df["trust_level"] == "self_only").sum())
        verified_pct = verified_count / max(activity_count, 1)
        assisted_pct = assisted_count / max(activity_count, 1)
        self_only_pct = self_only_count / max(activity_count, 1)

        trust_score = _safe_mean(scope_df["trust_weight"])
        quality_norm = _clip01(_safe_mean(scope_df["quality_factor_filled"]) / 1.35)
        impact_norm = _clip01(_safe_mean(scope_df["impact_factor_filled"]) / 1.35)
        weighted_norm = _clip01(_safe_mean(scope_df["weighted_activity_score_filled"]) / 2.20)
        sentiment_norm = _clip01(_safe_mean(scope_df["sentiment_score_filled"]))
        next_action_rate = _safe_mean(scope_df["next_action_flag"])
        note_rate = _safe_mean(scope_df["note_flag"])
        diversity_norm = _clip01(scope_df["activity_type"].nunique() / 4)
        repeat_ratio = _clip01(total_visits / max(unique_hospitals, 1) / 8)

        hir = round(_clip01(detail_rate * 0.35 + impact_norm * 0.25 + weighted_norm * 0.20 + trust_score * 0.20), 3)
        rtr = round(_clip01(sentiment_norm * 0.40 + repeat_ratio * 0.25 + trust_score * 0.20 + next_action_rate * 0.15), 3)
        bcr = round(_clip01(repeat_ratio * 0.40 + diversity_norm * 0.25 + trust_score * 0.20 + quality_norm * 0.15), 3)
        phr = round(_clip01(next_action_rate * 0.45 + diversity_norm * 0.25 + quality_norm * 0.15 + sentiment_norm * 0.15), 3)
        nar = round(_clip01(next_action_rate * 0.60 + trust_score * 0.20 + quality_norm * 0.20), 3)
        ahs = round(_clip01(sentiment_norm * 0.35 + detail_rate * 0.25 + trust_score * 0.20 + repeat_ratio * 0.20) * 100, 1)
        coach_score = round(
            hir * 0.30
            + rtr * 0.20
            + bcr * 0.15
            + phr * 0.15
            + nar * 0.10
            + (ahs / 100) * 0.10,
            3,
        )

        hospital_journey = (
            scope_df.groupby("hospital_id", dropna=False)
            .agg(
                has_detail=("detail_flag", "max"),
                has_next=("next_action_flag", "max"),
                max_impact=("impact_factor_filled", "max"),
                avg_sentiment=("sentiment_score_filled", "mean"),
                avg_weighted=("weighted_activity_score_filled", "mean"),
                first_date=("activity_date", "min"),
                last_date=("activity_date", "max"),
            )
            .reset_index()
        )
        contact_count = unique_hospitals
        presentation_count = int((hospital_journey["has_detail"] > 0).sum()) if not hospital_journey.empty else 0
        negotiation_count = int(
            ((hospital_journey["has_next"] > 0) | (hospital_journey["max_impact"].fillna(0) >= 1.10)).sum()
        ) if not hospital_journey.empty else 0
        close_count = int(
            (
                (hospital_journey["has_next"] > 0)
                & (
                    (hospital_journey["avg_sentiment"].fillna(0) >= 0.72)
                    | (hospital_journey["avg_weighted"].fillna(0) >= 1.30)
                )
            ).sum()
        ) if not hospital_journey.empty else 0
        prospect_count = max(int(prospect_count or 0), contact_count)
        conversion_rate = round((close_count / max(prospect_count, 1)) * 100, 1)
        pv = round(
            _clip01(
                (close_count / max(prospect_count, 1)) * 0.45
                + (presentation_count / max(prospect_count, 1)) * 0.25
                + next_action_rate * 0.15
                + trust_score * 0.15
            ) * 100,
            1,
        )
        pi = round(_clip01(weighted_norm * 0.50 + sentiment_norm * 0.30 + trust_score * 0.20) * 100, 1)
        swr = round((close_count / max(presentation_count, 1)) * 100, 1)
        target_gap = round((coach_score - _TARGETS["coach"]) * 100, 1)

        penalty_count = int(((scope_df["note_flag"] == 0) | (scope_df["quality_factor_filled"].fillna(0) < 0.90)).sum())
        unscored_count = int(
            (
                scope_df["weighted_activity_score_filled"].isna()
                | scope_df["sentiment_score_filled"].isna()
            ).sum()
        )

        positive_rate = float((scope_df["sentiment_score_filled"].fillna(-1) >= 0.75).mean())
        negative_rate = float((scope_df["sentiment_score_filled"].fillna(2) < 0.45).mean())
        nps_proxy = round((positive_rate - negative_rate) * 100, 1)

        axis_rows = [
            {"label": "Approach", "score": round(_clip01(trust_score * 0.55 + (1 - self_only_pct) * 0.45), 3), "tone": "blue"},
            {"label": "Contact", "score": round(_clip01(((scope_df["activity_type"].isin(["전화", "디지털"])).mean() * 0.55) + (next_action_rate * 0.45)), 3), "tone": "blue"},
            {"label": "Visit", "score": round(_clip01(((scope_df["activity_type"] == "방문").mean() * 0.70) + (repeat_ratio * 0.30)), 3), "tone": "teal"},
            {"label": "Presentation", "score": round(_clip01(detail_rate * 0.70 + weighted_norm * 0.30), 3), "tone": "amber"},
            {"label": "Question", "score": round(_clip01(note_rate * 0.45 + sentiment_norm * 0.30 + trust_score * 0.25), 3), "tone": "teal"},
            {"label": "Need Creation", "score": round(_clip01(impact_norm * 0.60 + quality_norm * 0.40), 3), "tone": "red"},
            {"label": "Demonstration", "score": round(_clip01(((scope_df["activity_type"].isin(["행사", "디지털"])).mean() * 0.45) + detail_rate * 0.35 + weighted_norm * 0.20), 3), "tone": "amber"},
            {"label": "Follow-up", "score": round(_clip01(next_action_rate * 0.65 + trust_score * 0.15 + sentiment_norm * 0.20), 3), "tone": "green"},
        ]
        weakest = sorted(axis_rows, key=lambda item: item["score"])[:2]
        behavior_diagnosis = (
            f"{weakest[0]['label']}({weakest[0]['score'] * 100:.0f}%), "
            f"{weakest[1]['label']}({weakest[1]['score'] * 100:.0f}%) 축 보강이 우선입니다."
        )
        dwell_days = (hospital_journey["last_date"] - hospital_journey["first_date"]).dt.days if not hospital_journey.empty else pd.Series(dtype="float64")
        dwell_days = dwell_days[dwell_days > 0]
        avg_dwell_days = round(float(dwell_days.mean()), 1) if not dwell_days.empty else 0.0

        return {
            "activity_count": activity_count,
            "total_visits": total_visits,
            "unique_reps": unique_reps,
            "unique_hospitals": unique_hospitals,
            "detail_count": detail_count,
            "verified_count": verified_count,
            "assisted_count": assisted_count,
            "self_only_count": self_only_count,
            "verified_pct": round(verified_pct * 100, 1),
            "assisted_pct": round(assisted_pct * 100, 1),
            "self_only_pct": round(self_only_pct * 100, 1),
            "penalty_count": penalty_count,
            "unscored_count": unscored_count,
            "hir": hir,
            "rtr": rtr,
            "bcr": bcr,
            "phr": phr,
            "nar": nar,
            "ahs": ahs,
            "pv": pv,
            "pi": pi,
            "swr": swr,
            "coach_score": coach_score,
            "target_gap": target_gap,
            "axis_rows": axis_rows,
            "behavior_diagnosis": behavior_diagnosis,
            "prospect_count": prospect_count,
            "contact_count": contact_count,
            "presentation_count": presentation_count,
            "negotiation_count": negotiation_count,
            "close_count": close_count,
            "avg_dwell_days": avg_dwell_days,
            "conversion_rate": conversion_rate,
            "nps_proxy": nps_proxy,
        }

    month_metrics_by_team: dict[str, list[dict]] = {}
    for team_option in team_options:
        team_token = team_option["token"]
        team_df = activity_df if team_token == _TEAM_ALL_TOKEN else activity_df[activity_df["branch_id"] == team_token]
        prospect_count = assigned_hospital_counts.get(team_token, assigned_hospital_counts[_TEAM_ALL_TOKEN])
        rows: list[dict] = []
        for month in month_tokens:
            month_df = team_df[team_df["month_label"] == month]
            metrics = _score_scope(month_df, prospect_count)
            rows.append(
                {
                    "month_label": month,
                    "hir": metrics["hir"],
                    "bcr": metrics["bcr"],
                    "pi": metrics["pi"],
                    "coach_score": metrics["coach_score"],
                    "nar": metrics["nar"],
                    "nps_proxy": metrics["nps_proxy"],
                    "total_visits": metrics["total_visits"],
                }
            )
        month_metrics_by_team[team_token] = rows

    month_metrics_by_rep: dict[str, list[dict]] = {}
    for rep_id, rep_df in activity_by_rep.items():
        rep_prospect = int(rep_assigned_counts.get(rep_id, rep_df["hospital_id"].nunique()))
        rows: list[dict] = []
        for month in month_tokens:
            month_df = rep_df[rep_df["month_label"] == month]
            metrics = _score_scope(month_df, rep_prospect)
            rows.append(
                {
                    "month_label": month,
                    "hir": metrics["hir"],
                    "bcr": metrics["bcr"],
                    "pi": metrics["pi"],
                    "coach_score": metrics["coach_score"],
                    "nar": metrics["nar"],
                    "nps_proxy": metrics["nps_proxy"],
                    "total_visits": metrics["total_visits"],
                }
            )
        month_metrics_by_rep[rep_id] = rows

    quarter_prev = {quarter_tokens[idx]: quarter_tokens[idx - 1] for idx in range(1, len(quarter_tokens))}
    year_prev = {year_tokens[idx]: year_tokens[idx - 1] for idx in range(1, len(year_tokens))}
    month_prev = {month_tokens[idx]: month_tokens[idx - 1] for idx in range(1, len(month_tokens))}

    def _resolve_previous_period(period_token: str) -> str | None:
        kind = period_kind.get(period_token, "all")
        if kind == "month":
            return month_prev.get(period_token)
        if kind == "quarter":
            return quarter_prev.get(period_token)
        if kind == "year":
            return year_prev.get(period_token)
        if len(month_tokens) >= 2:
            return month_prev.get(month_tokens[-1])
        return None

    def _resolve_compare_months(period_token: str) -> tuple[list[str], list[str]]:
        if period_token == "ALL":
            if len(month_tokens) >= 2:
                return [month_tokens[-1]], [month_tokens[-2]]
            return period_to_months["ALL"], []
        previous = _resolve_previous_period(period_token)
        return period_to_months.get(period_token, []), period_to_months.get(previous, []) if previous else []

    def _trend_payload_from_rows(rows: list[dict], period_token: str) -> dict:
        if not rows:
            return {"labels": [], "hir": [], "bcr": [], "fgr": []}
        all_labels = [row["month_label"] for row in rows]
        if period_token in period_to_months and period_to_months[period_token]:
            end_month = period_to_months[period_token][-1]
            end_index = all_labels.index(end_month) if end_month in all_labels else len(all_labels) - 1
        else:
            end_index = len(all_labels) - 1
        start_index = max(0, end_index - 5)
        window_rows = rows[start_index : end_index + 1]
        fgr_values: list[float] = []
        for idx, row in enumerate(window_rows):
            if idx == 0:
                fgr_values.append(0.0)
                continue
            prev_pi = float(window_rows[idx - 1]["pi"] or 0.0)
            curr_pi = float(row["pi"] or 0.0)
            if prev_pi <= 0:
                fgr_values.append(0.0)
            else:
                fgr_values.append(round(((curr_pi - prev_pi) / prev_pi) * 100, 1))
        return {
            "labels": [row["month_label"] for row in window_rows],
            "hir": [row["hir"] for row in window_rows],
            "bcr": [row["bcr"] for row in window_rows],
            "fgr": fgr_values,
        }

    def _effectiveness_from_rows(rows: list[dict]) -> float:
        if len(rows) < 3:
            return 0.0
        hir_values = [row["hir"] for row in rows[:-1]]
        next_pi_values = [row["pi"] / 100 for row in rows[1:]]
        return round(_safe_corr(hir_values, next_pi_values), 2)

    def _compute_fgr(compare_metrics: dict, prev_metrics: dict | None, rows: list[dict]) -> float:
        if prev_metrics and prev_metrics["pi"] > 0:
            return round(((compare_metrics["pi"] - prev_metrics["pi"]) / prev_metrics["pi"]) * 100, 1)
        if len(rows) >= 2 and rows[0]["pi"] > 0:
            return round(((rows[-1]["pi"] - rows[0]["pi"]) / rows[0]["pi"]) * 100, 1)
        return 0.0

    def _metric_tile(code: str, name: str, value: float, tone: str) -> dict:
        if code in {"HIR", "RTR", "BCR", "PHR", "NAR"}:
            return {
                "code": code,
                "name": name,
                "value": value,
                "display": f"{value:.2f}",
                "fill_pct": round(value * 100, 1),
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

    def _build_scope_payload(
        *,
        period_token: str,
        team_token: str,
        team_label: str,
        rep_token: str,
        rep_label: str,
        metrics: dict,
        fgr_value: float,
        coach_delta: float,
        effectiveness_corr: float,
        matrix_rows: list[dict],
        trend_payload: dict,
    ) -> dict:
        reliability_status = "PASS" if metrics["self_only_pct"] <= 20 else "AT RISK" if metrics["self_only_pct"] <= 30 else "CHECK"
        execution_status = "PASS" if metrics["nar"] >= _TARGETS["nar"] else "AT RISK" if metrics["nar"] >= 0.65 else "CHECK"
        effectiveness_status = "PASS" if effectiveness_corr >= 0.55 else "AT RISK" if effectiveness_corr >= 0.35 else "CHECK"
        acceptance_status = "IMPROVED" if metrics["nps_proxy"] >= 30 else "PASS" if metrics["nps_proxy"] >= 15 else "AT RISK" if metrics["nps_proxy"] >= 0 else "CHECK"
        return {
            "period_token": period_token,
            "period_label": "전체 기간" if period_token == "ALL" else period_token,
            "team_token": team_token,
            "team_label": team_label,
            "rep_token": rep_token,
            "rep_label": rep_label,
            "kpi_banner": {
                "leading": [
                    _metric_tile("HIR", "High-Impact Rate", metrics["hir"], "blue"),
                    _metric_tile("RTR", "Relationship Temp.", metrics["rtr"], "teal"),
                    _metric_tile("BCR", "Behavior Consistency", metrics["bcr"], "purple"),
                    _metric_tile("PHR", "Proactive Health", metrics["phr"], "pink"),
                ],
                "ops": [
                    _metric_tile("NAR", "Next Action Reliability", metrics["nar"], "amber"),
                    _metric_tile("AHS", "Account Health Score", metrics["ahs"], "amber"),
                    _metric_tile("PV", "Pipeline Velocity", metrics["pv"], "amber"),
                ],
                "outcome": [
                    _metric_tile("FGR", "Field Growth Rate", fgr_value, "green"),
                    _metric_tile("PI", "Prescription Index", metrics["pi"], "green"),
                    _metric_tile("TRG", "Target Readiness Gap", metrics["target_gap"], "muted"),
                    _metric_tile("SWR", "Share Win Rate", metrics["swr"], "muted"),
                ],
            },
            "radar": {
                "labels": ["HIR", "RTR", "BCR", "PHR", "NAR", "AHS"],
                "team_avg": [metrics["hir"], metrics["rtr"], metrics["bcr"], metrics["phr"], metrics["nar"], round(metrics["ahs"] / 100, 3)],
                "target": [_TARGETS["hir"], _TARGETS["rtr"], _TARGETS["bcr"], _TARGETS["phr"], _TARGETS["nar"], round(_TARGETS["ahs"] / 100, 3)],
            },
            "integrity": {
                "verified_pct": metrics["verified_pct"],
                "assisted_pct": metrics["assisted_pct"],
                "self_only_pct": metrics["self_only_pct"],
                "verified_count": metrics["verified_count"],
                "assisted_count": metrics["assisted_count"],
                "self_only_count": metrics["self_only_count"],
                "penalty_count": metrics["penalty_count"],
                "unscored_count": metrics["unscored_count"],
            },
            "coach_summary": {
                "score": metrics["coach_score"],
                "delta": coach_delta,
                "delta_display": f"{coach_delta:+.3f}",
                "weight_rows": [{"label": label, "value": weight} for label, weight in _COACH_WEIGHTS],
            },
            "behavior_axis": metrics["axis_rows"],
            "behavior_diagnosis": metrics["behavior_diagnosis"],
            "pipeline": {
                "stages": [
                    {"name": "Prospect", "count": metrics["prospect_count"], "pct": 100.0, "tone": "blue"},
                    {"name": "Contact", "count": metrics["contact_count"], "pct": round(metrics["contact_count"] / max(metrics["prospect_count"], 1) * 100, 1), "tone": "teal"},
                    {"name": "Presentation", "count": metrics["presentation_count"], "pct": round(metrics["presentation_count"] / max(metrics["prospect_count"], 1) * 100, 1), "tone": "purple"},
                    {"name": "Negotiation", "count": metrics["negotiation_count"], "pct": round(metrics["negotiation_count"] / max(metrics["prospect_count"], 1) * 100, 1), "tone": "amber"},
                    {"name": "Close", "count": metrics["close_count"], "pct": round(metrics["close_count"] / max(metrics["prospect_count"], 1) * 100, 1), "tone": "green"},
                ],
                "avg_dwell_days": metrics["avg_dwell_days"],
                "conversion_rate": metrics["conversion_rate"],
            },
            "matrix_rows": matrix_rows,
            "trend": trend_payload,
            "quality_flags": [
                {"title": "신뢰성", "metric_label": "Self-only 비중", "display": f"{metrics['self_only_pct']:.1f}%", "note": "목표 20.0% 이하 기준 비교", "status": reliability_status, "tone": _tag_tone(reliability_status)},
                {"title": "실행성", "metric_label": "NAR 달성률", "display": f"{metrics['nar'] * 100:.1f}%", "note": f"목표 {_TARGETS['nar'] * 100:.0f}% 기준", "status": execution_status, "tone": _tag_tone(execution_status)},
                {"title": "효과성", "metric_label": "HIR → PI 시차 상관", "display": f"r={effectiveness_corr:+.2f}", "note": "month HIR vs next-month PI 기준 시차 상관", "status": effectiveness_status, "tone": _tag_tone(effectiveness_status)},
                {"title": "수용성", "metric_label": "현장 수용 프록시", "display": f"{metrics['nps_proxy']:+.1f}", "note": "정서점수 기반 NPS 프록시", "status": acceptance_status, "tone": _tag_tone(acceptance_status)},
            ],
        }

    scope_data: dict[str, dict] = {}
    for team_option in team_options:
        team_token = team_option["token"]
        team_label = team_option["label"]
        team_df = activity_df if team_token == _TEAM_ALL_TOKEN else activity_df[activity_df["branch_id"] == team_token]
        team_prospect = assigned_hospital_counts.get(team_token, assigned_hospital_counts[_TEAM_ALL_TOKEN])
        effectiveness_corr = _effectiveness_from_rows(month_metrics_by_team.get(team_token, []))

        for period_token, selected_months in period_to_months.items():
            scope_df = team_df[team_df["month_label"].isin(selected_months)]
            metrics = _score_scope(scope_df, team_prospect)

            compare_months, prev_months = _resolve_compare_months(period_token)
            compare_df = team_df[team_df["month_label"].isin(compare_months)]
            prev_df = team_df[team_df["month_label"].isin(prev_months)] if prev_months else pd.DataFrame(columns=team_df.columns)
            compare_metrics = _score_scope(compare_df, team_prospect)
            prev_metrics = _score_scope(prev_df, team_prospect) if not prev_df.empty else None

            coach_delta = round(compare_metrics["coach_score"] - (prev_metrics["coach_score"] if prev_metrics else 0.0), 3)
            team_series = month_metrics_by_team.get(team_token, [])
            fgr_value = _compute_fgr(compare_metrics, prev_metrics, team_series)

            rep_rows: list[dict] = []
            rep_options = [{"token": _REP_ALL_TOKEN, "label": _REP_ALL_LABEL}]
            rep_scope_data: dict[str, dict] = {}
            rep_groups = scope_df.groupby(["rep_id", "rep_name", "branch_id", "branch_name"], dropna=False)
            for (rep_id, rep_name, branch_id, branch_name), rep_group in rep_groups:
                rep_metrics = _score_scope(rep_group, int(rep_assigned_counts.get(rep_id, rep_group["hospital_id"].nunique())))
                rep_token = str(rep_id)
                rep_label = str(rep_name or rep_id)
                matrix_row = {
                    "rep_id": rep_token,
                    "rep_name": rep_label,
                    "branch_id": str(branch_id or ""),
                    "branch_name": str(branch_name or branch_id or "미지정"),
                    "hir": rep_metrics["hir"],
                    "rtr": rep_metrics["rtr"],
                    "bcr": rep_metrics["bcr"],
                    "phr": rep_metrics["phr"],
                    "nar": rep_metrics["nar"],
                    "ahs": rep_metrics["ahs"],
                    "coach_score": rep_metrics["coach_score"],
                    "total_visits": rep_metrics["total_visits"],
                }
                rep_rows.append(matrix_row)
                rep_options.append({"token": rep_token, "label": rep_label})

                rep_full_df = activity_by_rep.get(rep_token, rep_group)
                rep_compare_df = rep_full_df[rep_full_df["month_label"].isin(compare_months)]
                rep_prev_df = rep_full_df[rep_full_df["month_label"].isin(prev_months)] if prev_months else pd.DataFrame(columns=rep_full_df.columns)
                rep_compare_metrics = _score_scope(rep_compare_df, int(rep_assigned_counts.get(rep_token, rep_group["hospital_id"].nunique())))
                rep_prev_metrics = _score_scope(rep_prev_df, int(rep_assigned_counts.get(rep_token, rep_group["hospital_id"].nunique()))) if not rep_prev_df.empty else None
                rep_series = month_metrics_by_rep.get(rep_token, [])
                rep_coach_delta = round(rep_compare_metrics["coach_score"] - (rep_prev_metrics["coach_score"] if rep_prev_metrics else 0.0), 3)
                rep_fgr_value = _compute_fgr(rep_compare_metrics, rep_prev_metrics, rep_series)
                rep_effectiveness = _effectiveness_from_rows(rep_series)
                rep_scope_data[rep_token] = _build_scope_payload(
                    period_token=period_token,
                    team_token=team_token,
                    team_label=team_label,
                    rep_token=rep_token,
                    rep_label=rep_label,
                    metrics=rep_metrics,
                    fgr_value=rep_fgr_value,
                    coach_delta=rep_coach_delta,
                    effectiveness_corr=rep_effectiveness,
                    matrix_rows=[matrix_row],
                    trend_payload=_trend_payload_from_rows(rep_series, period_token),
                )
            rep_rows = sorted(rep_rows, key=lambda row: (row["coach_score"], row["hir"], row["total_visits"]), reverse=True)
            rep_options = [rep_options[0], *sorted(rep_options[1:], key=lambda row: row["label"])]
            scope_data[f"{period_token}|{team_token}"] = {
                **_build_scope_payload(
                    period_token=period_token,
                    team_token=team_token,
                    team_label=team_label,
                    rep_token=_REP_ALL_TOKEN,
                    rep_label=_REP_ALL_LABEL,
                    metrics=metrics,
                    fgr_value=fgr_value,
                    coach_delta=coach_delta,
                    effectiveness_corr=effectiveness_corr,
                    matrix_rows=rep_rows,
                    trend_payload=_trend_payload_from_rows(team_series, period_token),
                ),
                "rep_options": rep_options,
                "rep_scope_data": rep_scope_data,
            }

    period_options = [{"token": token, "label": token} for token in reversed(month_tokens)]
    period_options.extend({"token": token, "label": token} for token in reversed(quarter_tokens))
    period_options.extend({"token": token, "label": token} for token in reversed(year_tokens))
    period_options.append({"token": "ALL", "label": "전체 기간"})
    default_period = month_tokens[-1] if month_tokens else "ALL"

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
            "note": "CRM analysis template uses activity-level proxy scoring built from trust, detail, sentiment, quality, impact, and next-action signals.",
        },
        "filters": {
            "period_options": period_options,
            "team_options": team_options,
            "rep_options": [{"token": _REP_ALL_TOKEN, "label": _REP_ALL_LABEL}],
            "default_period": default_period,
            "default_team": _TEAM_ALL_TOKEN,
            "default_rep": _REP_ALL_TOKEN,
        },
        "scope_data": scope_data,
    }


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
