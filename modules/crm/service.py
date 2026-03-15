"""
CRM Module Service - CrmStandardActivity -> CrmResultAsset 생성기

CRM 모듈의 핵심 처리기.
adapter가 만든 CrmStandardActivity 목록을 집계하여
Validation Layer(OPS)에 전달할 CrmResultAsset을 생성한다.

흐름:
  list[CrmStandardActivity] + list[CompanyMasterStandard]
  -> CrmResultAsset
"""

from collections import Counter
from typing import Optional

from modules.crm.schemas import CrmStandardActivity, CompanyMasterStandard
from modules.kpi.crm_engine import compute_crm_kpi_bundle
from result_assets.crm_result_asset import (
    CrmResultAsset,
    RepBehaviorProfile,
    MonthlyKpiSummary,
    ActivityContextSummary,
    MappingQualitySummary,
)
from common.exceptions import MissingResultAssetError
from modules.crm.builder_payload import build_crm_builder_payload as _build_crm_builder_payload


def build_crm_result_asset(
    activities: list[CrmStandardActivity],
    company_master: list[CompanyMasterStandard],
    unmapped_raw_count: int = 0,
    total_raw_count: int = 0,
    unmapped_hospital_names: Optional[list[str]] = None,
    notes: Optional[str] = None,
) -> CrmResultAsset:
    """
    CrmStandardActivity 목록을 받아 CrmResultAsset을 생성합니다.

    Args:
        activities: Adapter가 생성한 CrmStandardActivity 목록
        company_master: 담당자-지점 정보 참조용
        unmapped_raw_count: 매핑 실패한 raw 활동 건수 (Adapter에서 전달)
        total_raw_count: 원본 raw 전체 건수 (매핑률 계산용)
        unmapped_hospital_names: 매핑 실패 병원명 목록
        notes: 생성 비고

    Returns:
        CrmResultAsset
    """
    if not activities:
        raise MissingResultAssetError(
            "CrmResultAsset을 생성할 활동 데이터가 없습니다.",
            detail="Adapter 실행 결과가 비어 있습니다. 입력 파일을 확인하세요."
        )

    # ── 1. 담당자 메타 인덱스 구성 ──────────────────────────────────────────
    rep_meta: dict[str, CompanyMasterStandard] = {}
    for m in company_master:
        if m.rep_id not in rep_meta:
            rep_meta[m.rep_id] = m

    # ── 2. 담당자별 행동 프로파일 집계 ────────────────────────────────────────
    rep_visits: dict[str, int] = Counter()
    rep_hospitals: dict[str, set] = {}
    rep_detail_counts: dict[str, int] = Counter()
    rep_activity_types_raw: dict[str, list] = {}
    rep_activity_types_standard: dict[str, list] = {}
    rep_months: dict[str, set] = {}

    for act in activities:
        rep_id = act.rep_id
        rep_visits[rep_id] += act.visit_count
        rep_hospitals.setdefault(rep_id, set()).add(act.hospital_id)
        if act.has_detail_call:
            rep_detail_counts[rep_id] += 1
        raw_type = str(act.activity_type_raw or "").strip()
        std_type = str(act.activity_type_standard or act.activity_type or "").strip()
        if raw_type:
            rep_activity_types_raw.setdefault(rep_id, []).append(raw_type)
        if std_type:
            rep_activity_types_standard.setdefault(rep_id, []).append(std_type)
        rep_months.setdefault(rep_id, set()).add(act.metric_month)

    behavior_profiles = []
    all_rep_ids = set(act.rep_id for act in activities)

    for rep_id in all_rep_ids:
        total_v = rep_visits.get(rep_id, 0)
        unique_h = len(rep_hospitals.get(rep_id, set()))
        detail_c = rep_detail_counts.get(rep_id, 0)
        type_counter_raw = Counter(rep_activity_types_raw.get(rep_id, []))
        type_counter_standard = Counter(rep_activity_types_standard.get(rep_id, []))
        top_types_raw = [t for t, _ in type_counter_raw.most_common(3)]
        top_types_standard = [t for t, _ in type_counter_standard.most_common(3)]
        months = sorted(rep_months.get(rep_id, set()))

        meta = rep_meta.get(rep_id)
        profile = RepBehaviorProfile(
            rep_id=rep_id,
            rep_name=meta.rep_name if meta else rep_id,
            branch_id=meta.branch_id if meta else "",
            branch_name=meta.branch_name if meta else "",
            total_visits=total_v,
            unique_hospitals=unique_h,
            avg_visits_per_hospital=round(total_v / unique_h, 2) if unique_h > 0 else 0.0,
            detail_call_rate=round(detail_c / max(total_v, 1), 3),
            top_activity_types=top_types_standard,
            top_activity_types_raw=top_types_raw,
            top_activity_types_standard=top_types_standard,
            active_months=months,
        )
        behavior_profiles.append(profile)

    # ── 3. 월별 KPI 집계 ──────────────────────────────────────────────────────
    month_visits: dict[str, int] = Counter()
    month_reps: dict[str, set] = {}
    month_hospitals: dict[str, set] = {}
    month_details: dict[str, int] = Counter()

    for act in activities:
        m = act.metric_month
        month_visits[m] += act.visit_count
        month_reps.setdefault(m, set()).add(act.rep_id)
        month_hospitals.setdefault(m, set()).add(act.hospital_id)
        if act.has_detail_call:
            month_details[m] += 1

    monthly_kpi = []
    for month in sorted(month_visits.keys()):
        active_reps = len(month_reps.get(month, set()))
        total_v = month_visits[month]
        kpi = MonthlyKpiSummary(
            metric_month=month,
            total_visits=total_v,
            total_reps_active=active_reps,
            total_hospitals_visited=len(month_hospitals.get(month, set())),
            avg_visits_per_rep=round(total_v / active_reps, 2) if active_reps > 0 else 0.0,
            detail_call_count=month_details.get(month, 0),
        )
        monthly_kpi.append(kpi)

    # ── 4. 활동 문맥 요약 ─────────────────────────────────────────────────────
    all_dates = [act.activity_date for act in activities]
    all_products: set[str] = set()
    all_activity_types_raw: set[str] = set()
    all_activity_types_standard: set[str] = set()
    for act in activities:
        all_products.update(act.products_mentioned)
        raw_type = str(act.activity_type_raw or "").strip()
        std_type = str(act.activity_type_standard or act.activity_type or "").strip()
        if raw_type:
            all_activity_types_raw.add(raw_type)
        if std_type:
            all_activity_types_standard.add(std_type)

    activity_context = ActivityContextSummary(
        total_activity_records=len(activities),
        date_range_start=str(min(all_dates)) if all_dates else None,
        date_range_end=str(max(all_dates)) if all_dates else None,
        unique_reps=len(all_rep_ids),
        unique_hospitals=len(set(act.hospital_id for act in activities)),
        unique_branches=len(set(act.branch_id for act in activities)),
        activity_types_found=sorted(all_activity_types_standard),
        activity_types_raw_found=sorted(all_activity_types_raw),
        activity_types_standard_found=sorted(all_activity_types_standard),
        products_mentioned=sorted(all_products),
    )

    # ── 5. 매핑 품질 요약 ─────────────────────────────────────────────────────
    mapped_hospital_count = len(set(act.hospital_id for act in activities))
    unmapped_count = unmapped_raw_count
    mapped_count_for_rate = len(activities)
    raw_total = total_raw_count if total_raw_count > 0 else (len(activities) + unmapped_count)

    mapping_quality = MappingQualitySummary(
        total_raw_records=raw_total,
        mapped_hospital_count=mapped_hospital_count,
        unmapped_hospital_count=unmapped_count,
        hospital_mapping_rate=round(mapped_count_for_rate / raw_total, 3) if raw_total > 0 else 0.0,
        rep_coverage_rate=round(len(all_rep_ids) / max(len(rep_meta), 1), 3),
        unmapped_hospital_names=(unmapped_hospital_names or [])[:20],
    )

    # ── 6. Result Asset 조립 ──────────────────────────────────────────────────
    rep_monthly_kpi_11, monthly_kpi_11, metric_version = compute_crm_kpi_bundle(activities)

    return CrmResultAsset(
        behavior_profiles=behavior_profiles,
        monthly_kpi=monthly_kpi,
        activity_context=activity_context,
        mapping_quality=mapping_quality,
        metric_version=metric_version,
        rep_monthly_kpi_11=rep_monthly_kpi_11,
        monthly_kpi_11=monthly_kpi_11,
        notes=notes,
    )


def build_crm_builder_payload(
    asset: CrmResultAsset,
    summary: dict,
    company_name: str,
    activities: list[CrmStandardActivity] | None = None,
    company_master: list[CompanyMasterStandard] | None = None,
) -> dict:
    return _build_crm_builder_payload(
        asset=asset,
        summary=summary,
        company_name=company_name,
        activities=activities,
        company_master=company_master,
    )
