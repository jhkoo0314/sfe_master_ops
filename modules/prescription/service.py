"""
Prescription Module Service - PrescriptionStandardFlow → PrescriptionResultAsset

흐름 레코드를 집계하여 OPS에 전달할 Result Asset을 생성한다.
"""

from collections import Counter
from typing import Optional

from modules.prescription.schemas import PrescriptionStandardFlow, PrescriptionGapRecord
from result_assets.prescription_result_asset import (
    PrescriptionResultAsset,
    LineageSummary,
    ReconciliationSummary,
    ValidationGapSummary,
    PrescriptionMappingQualitySummary,
)
from common.exceptions import MissingResultAssetError


def build_prescription_result_asset(
    flows: list[PrescriptionStandardFlow],
    gaps: list[PrescriptionGapRecord],
    adapter_failed_count: int = 0,
    total_raw_count: int = 0,
    notes: Optional[str] = None,
) -> PrescriptionResultAsset:
    """
    PrescriptionStandardFlow + GapRecord 목록으로 PrescriptionResultAsset을 생성합니다.

    Args:
        flows: flow_builder 출력 (UNMAPPED 포함)
        gaps: flow_builder 정의한 gap 기록 목록
        adapter_failed_count: Adapter 변환 실패 건수
        total_raw_count: 원본 raw 전체 건수
        notes: 비고

    Returns:
        PrescriptionResultAsset
    """
    if not flows:
        raise MissingResultAssetError(
            "PrescriptionResultAsset을 생성할 흐름 데이터가 없습니다.",
            detail="Adapter 또는 FlowBuilder 실행 결과가 비어 있습니다."
        )

    # ── 1. Lineage Summary ────────────────────────────────────────────────────
    complete = [f for f in flows if f.is_complete]
    incomplete = [f for f in flows if not f.is_complete]
    total = len(flows)

    unique_wholesalers = len({f.wholesaler_id for f in flows})
    unique_pharmacies = len({f.pharmacy_id for f in flows})
    unique_hospitals = len({f.hospital_id for f in complete if f.hospital_id})
    unique_products = len({f.product_id for f in flows})
    months = sorted({f.metric_month for f in flows})

    lineage = LineageSummary(
        total_flow_records=total,
        complete_flow_count=len(complete),
        incomplete_flow_count=len(incomplete),
        flow_completion_rate=round(len(complete) / total, 3) if total > 0 else 0.0,
        unique_wholesalers=unique_wholesalers,
        unique_pharmacies=unique_pharmacies,
        unique_hospitals_connected=unique_hospitals,
        unique_products=unique_products,
        metric_months=months,
    )

    # ── 2. Reconciliation Summary ────────────────────────────────────────────
    ws_qty = sum(f.total_quantity for f in flows if f.source_record_type == "wholesaler_shipment")
    ph_qty = sum(f.total_quantity for f in flows if f.source_record_type == "pharmacy_purchase")
    has_both = ws_qty > 0 and ph_qty > 0

    match_rate = None
    if has_both and ws_qty > 0:
        match_rate = round(min(ws_qty, ph_qty) / max(ws_qty, ph_qty), 3)

    recon_note = None
    if not has_both:
        recon_note = (
            "도매출고 데이터만 있습니다. 약국구입 데이터가 추가되면 대조 가능합니다."
            if ws_qty > 0
            else "약국구입 데이터만 있습니다. 도매출고 데이터가 추가되면 대조 가능합니다."
        )

    reconciliation = ReconciliationSummary(
        wholesaler_shipment_qty=ws_qty,
        pharmacy_purchase_qty=ph_qty,
        qty_match_rate=match_rate,
        has_both_sources=has_both,
        reconciliation_note=recon_note,
    )

    # ── 3. Validation Gap Summary ─────────────────────────────────────────────
    gap_by_reason = dict(Counter(g.gap_reason for g in gaps))
    top_pharmacies = [
        name for name, _ in Counter(g.pharmacy_name for g in gaps).most_common(20)
    ]
    top_products = [
        name for name, _ in Counter(g.product_id for g in gaps).most_common(10)
    ]

    gap_summary = ValidationGapSummary(
        total_gap_records=len(gaps),
        gap_by_reason=gap_by_reason,
        top_unmapped_pharmacies=top_pharmacies,
        top_unmapped_products=top_products,
    )

    # ── 4. Mapping Quality ───────────────────────────────────────────────────
    raw_total = total_raw_count if total_raw_count > 0 else (total + adapter_failed_count)
    hospital_covered = len({f.hospital_id for f in flows if f.hospital_id and f.is_complete})
    hospital_ids_in_flows = len({f.hospital_id for f in flows if f.hospital_id})

    quality = PrescriptionMappingQualitySummary(
        total_records=raw_total,
        adapter_failed_records=adapter_failed_count,
        flow_complete_records=len(complete),
        flow_incomplete_records=len(incomplete),
        flow_completion_rate=lineage.flow_completion_rate,
        hospital_coverage_rate=round(hospital_covered / max(hospital_ids_in_flows, 1), 3),
    )

    return PrescriptionResultAsset(
        lineage_summary=lineage,
        reconciliation_summary=reconciliation,
        validation_gap_summary=gap_summary,
        mapping_quality=quality,
        notes=notes,
    )
