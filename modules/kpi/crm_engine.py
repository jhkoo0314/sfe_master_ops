from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import re
from typing import Iterable

from modules.crm.schemas import CrmStandardActivity
from result_assets.crm_result_asset import CrmKpiMetricSet, MonthlyKpi11Summary, RepMonthlyKpi11


TRUST_FACTOR = {
    "verified": 1.0,
    "assisted": 0.85,
    "self_only": 0.70,
}


BEHAVIOR8_KEYS = (
    "PT",
    "Demo",
    "Closing",
    "Needs",
    "FaceToFace",
    "Contact",
    "Access",
    "Feedback",
)


@dataclass
class RepMonthAggregate:
    rep_id: str
    metric_month: str
    total_rows: int = 0
    total_visits: float = 0.0
    total_detail_calls: float = 0.0
    total_next_actions: float = 0.0
    valid_next_actions: float = 0.0
    total_weighted_score: float = 0.0
    total_weighted_count: float = 0.0
    total_sentiment_score: float = 0.0
    total_sentiment_count: float = 0.0
    total_quality_score: float = 0.0
    total_quality_count: float = 0.0
    total_impact_score: float = 0.0
    total_impact_count: float = 0.0
    activity_days: set[date] | None = None
    unique_hospitals: set[str] | None = None
    behavior_counts: dict[str, float] | None = None

    def __post_init__(self) -> None:
        self.activity_days = set()
        self.unique_hospitals = set()
        self.behavior_counts = {k: 0.0 for k in BEHAVIOR8_KEYS}


def compute_crm_kpi_bundle(
    activities: Iterable[CrmStandardActivity],
    *,
    metric_version: str = "crm_kpi_engine_v1",
) -> tuple[list[RepMonthlyKpi11], list[MonthlyKpi11Summary], str]:
    grouped: dict[tuple[str, str], RepMonthAggregate] = {}
    for act in activities:
        key = (act.rep_id, act.metric_month)
        agg = grouped.get(key)
        if agg is None:
            agg = RepMonthAggregate(rep_id=act.rep_id, metric_month=act.metric_month)
            grouped[key] = agg
        _accumulate(agg, act)

    rep_rows: list[RepMonthlyKpi11] = []
    month_collect: dict[str, list[RepMonthlyKpi11]] = defaultdict(list)

    for key in sorted(grouped.keys()):
        agg = grouped[key]
        metric_set, behavior_mix, unscored_reasons = _finalize_metrics(agg)
        row = RepMonthlyKpi11(
            rep_id=agg.rep_id,
            metric_month=agg.metric_month,
            metric_set=metric_set,
            behavior_mix_8=behavior_mix,
            unscored_reasons=unscored_reasons,
        )
        rep_rows.append(row)
        month_collect[agg.metric_month].append(row)

    month_rows: list[MonthlyKpi11Summary] = []
    for month in sorted(month_collect.keys()):
        rows = month_collect[month]
        metric_set = CrmKpiMetricSet(
            hir=_avg(rows, "hir"),
            rtr=_avg(rows, "rtr"),
            bcr=_avg(rows, "bcr"),
            phr=_avg(rows, "phr"),
            nar=_avg(rows, "nar"),
            ahs=_avg(rows, "ahs"),
            pv=_avg(rows, "pv"),
            fgr=_avg(rows, "fgr"),
            pi=_avg(rows, "pi"),
            trg=_avg(rows, "trg"),
            swr=_avg(rows, "swr"),
            coach_score=_avg(rows, "coach_score"),
        )
        month_rows.append(
            MonthlyKpi11Summary(
                metric_month=month,
                metric_set=metric_set,
                rep_count=len(rows),
                unscored_count=sum(1 for row in rows if row.unscored_reasons),
            )
        )

    return rep_rows, month_rows, metric_version


def _accumulate(agg: RepMonthAggregate, act: CrmStandardActivity) -> None:
    visits = max(float(act.visit_count or 0), 0.0)
    agg.total_rows += 1
    agg.total_visits += visits
    if act.has_detail_call:
        agg.total_detail_calls += 1.0
    agg.activity_days.add(act.activity_date)
    agg.unique_hospitals.add(act.hospital_id)

    trust = _trust_factor(act.trust_level)
    quality = _clip01(act.quality_factor if act.quality_factor is not None else 1.0)
    impact = _clip01(act.impact_factor if act.impact_factor is not None else 1.0)
    weight = _clip01(act.activity_weight if act.activity_weight is not None else 1.0)
    weighted = act.weighted_activity_score
    if weighted is None:
        weighted = weight * quality * impact * trust
    weighted = _clip01(weighted)

    agg.total_weighted_score += weighted * max(visits, 1.0)
    agg.total_weighted_count += max(visits, 1.0)

    if act.sentiment_score is not None:
        agg.total_sentiment_score += _clip01(act.sentiment_score)
        agg.total_sentiment_count += 1.0
    if act.quality_factor is not None:
        agg.total_quality_score += _clip01(act.quality_factor)
        agg.total_quality_count += 1.0
    if act.impact_factor is not None:
        agg.total_impact_score += _clip01(act.impact_factor)
        agg.total_impact_count += 1.0

    next_action = str(act.next_action_text or "").strip()
    if next_action:
        agg.total_next_actions += 1.0
        if len(next_action) >= 5:
            agg.valid_next_actions += 1.0

    behavior_key = _to_behavior8(act.activity_type_raw or act.activity_type_standard or act.activity_type)
    agg.behavior_counts[behavior_key] += max(visits, 1.0)


def _finalize_metrics(agg: RepMonthAggregate) -> tuple[CrmKpiMetricSet, dict[str, float], list[str]]:
    unscored: list[str] = []
    total_visits = max(agg.total_visits, 0.0)
    total_actions = max(agg.total_rows, 0)

    if agg.total_weighted_count <= 0:
        unscored.append("hir_weighted_score_missing")
    hir = _to_pct(agg.total_weighted_score / agg.total_weighted_count) if agg.total_weighted_count > 0 else 0.0

    if agg.total_sentiment_count <= 0:
        unscored.append("rtr_sentiment_missing")
    rtr = _to_pct(agg.total_sentiment_score / agg.total_sentiment_count) if agg.total_sentiment_count > 0 else 0.0

    active_days = len(agg.activity_days)
    volume_score = _clip01(total_visits / 20.0)
    regularity_score = _clip01(active_days / 16.0)
    bcr = _to_pct((0.4 * volume_score) + (0.6 * regularity_score))

    phr = _to_pct(agg.valid_next_actions / total_actions) if total_actions > 0 else 0.0
    nar = _to_pct(agg.valid_next_actions / agg.total_next_actions) if agg.total_next_actions > 0 else 0.0

    recency = _clip01(active_days / 20.0)
    rtr_component = _clip01(rtr / 100.0)
    coverage = _clip01(len(agg.unique_hospitals) / 20.0)
    competitor_risk_inverse = 1.0
    ahs = _to_pct(
        (0.35 * recency)
        + (0.25 * rtr_component)
        + (0.20 * coverage)
        + (0.20 * competitor_risk_inverse)
    )

    pv = _to_pct((0.7 * _clip01(hir / 100.0)) + (0.3 * _clip01(nar / 100.0)))
    pi = _to_pct((0.7 * _clip01(hir / 100.0)) + (0.3 * _clip01(bcr / 100.0)))
    fgr = round(((pi - 50.0) / 50.0) * 100.0, 1)
    trg = round(pi - 100.0, 1)
    swr = _to_pct(sum(1 for _, v in agg.behavior_counts.items() if v > 0) / len(BEHAVIOR8_KEYS))

    coach_score = round(
        (0.30 * hir)
        + (0.20 * rtr)
        + (0.15 * bcr)
        + (0.15 * phr)
        + (0.10 * nar)
        + (0.10 * ahs),
        1,
    )

    behavior_mix = {k: 0.0 for k in BEHAVIOR8_KEYS}
    if total_visits > 0:
        behavior_mix = {
            key: round((value / total_visits), 4)
            for key, value in agg.behavior_counts.items()
        }

    metric_set = CrmKpiMetricSet(
        hir=hir,
        rtr=rtr,
        bcr=bcr,
        phr=phr,
        nar=nar,
        ahs=ahs,
        pv=pv,
        fgr=fgr,
        pi=pi,
        trg=trg,
        swr=swr,
        coach_score=coach_score,
    )
    return metric_set, behavior_mix, unscored


def _avg(rows: list[RepMonthlyKpi11], field_name: str) -> float:
    if not rows:
        return 0.0
    values = [float(getattr(row.metric_set, field_name, 0.0) or 0.0) for row in rows]
    return round(sum(values) / len(values), 1)


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _to_pct(value01: float) -> float:
    return round(_clip01(value01) * 100.0, 1)


def _trust_factor(raw: str | None) -> float:
    key = str(raw or "").strip().lower()
    return TRUST_FACTOR.get(key, 1.0)


def _to_behavior8(raw: str | None) -> str:
    text = _normalize_behavior_text(raw)
    mapping = {
        "pt": "PT",
        "제품설명": "PT",
        "producttalk": "PT",
        "detail": "PT",
        "detailing": "PT",
        "demo": "Demo",
        "시연": "Demo",
        "행사": "Demo",
        "디지털": "Demo",
        "edetail": "Demo",
        "webinar": "Demo",
        "closing": "Closing",
        "클로징": "Closing",
        "close": "Closing",
        "마감": "Closing",
        "needs": "Needs",
        "니즈환기": "Needs",
        "니즈발굴": "Needs",
        "needcreation": "Needs",
        "need": "Needs",
        "facetoface": "FaceToFace",
        "대면": "FaceToFace",
        "방문": "FaceToFace",
        "visit": "FaceToFace",
        "contact": "Contact",
        "컨택": "Contact",
        "전화": "Contact",
        "이메일": "Contact",
        "화상": "Contact",
        "call": "Contact",
        "email": "Contact",
        "video": "Contact",
        "remote": "Contact",
        "access": "Access",
        "접근": "Access",
        "feedback": "Feedback",
        "피드백": "Feedback",
    }
    return mapping.get(text, "FaceToFace")


def _normalize_behavior_text(raw: str | None) -> str:
    text = str(raw or "").strip().lower()
    if not text:
        return ""
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"[\s\-_/]+", "", text)
    return text
