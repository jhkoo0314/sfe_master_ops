"""
Prescription Flow Builder - 도매→약국→병원 흐름 조립

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
공공데이터 실제 구조 반영:

  병원정보서비스 지역 구조:
    region_key     = 시도명 (한글, 예: '서울', '부산', '경남')
    sub_region_key = 시군구명 (한글, 예: '종로구', '해운대구')

  약국정보서비스 지역 구조:
    pharmacy_region_key     = 시도코드명 (한글, 예: '서울', '부산')
                              OR 시도코드 6자리 (예: '110000', '260000')
    pharmacy_sub_region_key = 시군구코드 6자리 (예: '110110', '260402')
                              OR 시군구코드명 (한글)

  매핑 전략:
    약국 pharmacy_region_key (한글 시도명) == 병원 region_key (한글 시도명)
    → 병원 매핑 가능

  도매업소 지역:
    wholesaler_id에 시도명 포함 → 병원 region_key와 직접 비교 가능
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

병원 매핑 규칙 (범용, 회사 데이터 불필요):
  1. record에 hospital_id 있으면 → 직접 사용 (direct)
  2. pharmacy_sub_region_key == hospital.sub_region_key → 시군구 직접 매핑 (direct)
  3. pharmacy_region_key == hospital.region_key → 시도 근접 매핑 (region_proximity)
  4. 모두 실패 → UNMAPPED (gap_record 생성, 도매→약국 구간은 유지)
"""

from collections import defaultdict
from modules.prescription.schemas import (
    CompanyPrescriptionStandard,
    PrescriptionStandardFlow,
    PrescriptionGapRecord,
)
from modules.crm.schemas import HospitalMaster
from modules.prescription.id_rules import generate_lineage_key, is_lineage_complete


# ────────────────────────────────────────
# 병원 매핑 인덱스 생성
# ────────────────────────────────────────

def build_hospital_region_index(
    hospitals: list[HospitalMaster],
) -> tuple[dict[str, list[HospitalMaster]], dict[str, list[HospitalMaster]]]:
    """
    병원을 지역 기준으로 인덱싱합니다.

    Returns:
        (sub_region_index, region_index)
        sub_region_index: {sub_region_key: [HospitalMaster, ...]}
        region_index:     {region_key: [HospitalMaster, ...]}
    """
    sub_region_index: dict[str, list[HospitalMaster]] = defaultdict(list)
    region_index: dict[str, list[HospitalMaster]] = defaultdict(list)

    for h in hospitals:
        sub_region_index[h.sub_region_key].append(h)
        region_index[h.region_key].append(h)

    return dict(sub_region_index), dict(region_index)


def _pick_hospital(
    candidates: list[HospitalMaster],
    prefer_types: list[str] | None = None,
) -> HospitalMaster | None:
    """
    후보 병원 목록에서 1개를 선택합니다.
    prefer_types로 우선 종별을 지정할 수 있습니다.

    우선순위:
      1. prefer_types에 있는 종별 중 첫 번째
      2. 없으면 목록의 첫 번째 (단일 후보이면 그것)
      3. 복수 후보에서 prefer_types도 없으면 None (ambiguous)
    """
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    if prefer_types:
        for ptype in prefer_types:
            for h in candidates:
                if h.hospital_type == ptype:
                    return h
    return None  # 명확한 1:1 매핑 불가 → gap


# ────────────────────────────────────────
# Flow Builder 핵심 함수
# ────────────────────────────────────────

def build_prescription_standard_flow(
    standards: list[CompanyPrescriptionStandard],
    hospital_sub_region_index: dict[str, list[HospitalMaster]],
    hospital_region_index: dict[str, list[HospitalMaster]],
    prefer_hospital_types: list[str] | None = None,
) -> tuple[list[PrescriptionStandardFlow], list[PrescriptionGapRecord]]:
    """
    CompanyPrescriptionStandard 목록을 받아 PrescriptionStandardFlow를 생성합니다.

    병원 매핑 전략 (우선순위):
      1. record에 hospital_id가 이미 있으면 → 직접 사용
      2. pharmacy_sub_region_key == hospital.sub_region_key → 시군구 직접 매핑
      3. pharmacy_region_key == hospital.region_key → 시도 근접 매핑
      4. 모두 실패 → gap_record 생성 (lineage_key에 UNMAPPED)

    Args:
        standards: CompanyPrescriptionAdapter 출력
        hospital_sub_region_index: {sub_region_key: [HospitalMaster]}
        hospital_region_index: {region_key: [HospitalMaster]}
        prefer_hospital_types: 매핑 우선 종별 (예: ["의원", "병원"])

    Returns:
        (흐름 레코드 목록, gap 기록 목록)
    """
    flows: list[PrescriptionStandardFlow] = []
    gaps: list[PrescriptionGapRecord] = []

    for std in standards:
        hospital_id: str | None = None
        hospital_name: str | None = None
        mapping_method: str | None = None
        gap_reason: str | None = None

        # 전략 1: 이미 hospital_id가 있는 경우 (pharmacy_purchase 파일 등)
        if std.hospital_id:
            hospital_id = std.hospital_id
            hospital_name = None  # 이름은 보조 정보
            mapping_method = "direct"

        # 전략 2: 시군구 코드 직접 매핑
        else:
            sub_candidates = hospital_sub_region_index.get(std.pharmacy_sub_region_key, [])
            if sub_candidates:
                chosen = _pick_hospital(sub_candidates, prefer_hospital_types)
                if chosen:
                    hospital_id = chosen.hospital_id
                    hospital_name = chosen.hospital_name
                    mapping_method = "direct"
                else:
                    gap_reason = "ambiguous_match"  # 같은 시군구에 복수 병원, 선택 불가
            else:
                # 전략 3: 시도 코드 근접 매핑
                region_candidates = hospital_region_index.get(std.pharmacy_region_key, [])
                if region_candidates:
                    chosen = _pick_hospital(region_candidates, prefer_hospital_types)
                    if chosen:
                        hospital_id = chosen.hospital_id
                        hospital_name = chosen.hospital_name
                        mapping_method = "region_proximity"
                    else:
                        gap_reason = "ambiguous_match"
                else:
                    gap_reason = "no_hospital_in_region"

        # lineage_key 생성
        lineage_key = generate_lineage_key(
            wholesaler_id=std.wholesaler_id,
            pharmacy_id=std.pharmacy_id,
            metric_month=std.metric_month,
            hospital_id=hospital_id,
        )
        is_complete = is_lineage_complete(lineage_key)

        if is_complete or mapping_method:
            flow = PrescriptionStandardFlow(
                lineage_key=lineage_key,
                is_complete=is_complete,
                wholesaler_id=std.wholesaler_id,
                wholesaler_name=std.wholesaler_name,
                wholesaler_region_key=std.pharmacy_region_key,  # 도매 지역 없으면 약국 지역 활용
                pharmacy_id=std.pharmacy_id,
                pharmacy_name=std.pharmacy_name,
                pharmacy_region_key=std.pharmacy_region_key,
                pharmacy_sub_region_key=std.pharmacy_sub_region_key,
                hospital_id=hospital_id,
                hospital_name=hospital_name,
                hospital_mapping_method=mapping_method,
                product_id=std.product_id,
                product_name=std.product_name,
                ingredient_code=std.ingredient_code,
                total_quantity=std.quantity,
                total_amount=std.amount,
                metric_month=std.metric_month,
                source_record_type=std.record_type,
            )
            flows.append(flow)
        else:
            # gap 기록
            gap = PrescriptionGapRecord(
                pharmacy_id=std.pharmacy_id,
                pharmacy_name=std.pharmacy_name,
                pharmacy_region_key=std.pharmacy_region_key,
                wholesaler_id=std.wholesaler_id,
                product_id=std.product_id,
                metric_month=std.metric_month,
                quantity=std.quantity,
                gap_reason=gap_reason or "unknown",
                raw_row_index=std.raw_row_index,
            )
            gaps.append(gap)

            # gap도 flow로 기록 (UNMAPPED 상태로) - 추적 유지
            flow = PrescriptionStandardFlow(
                lineage_key=lineage_key,
                is_complete=False,
                wholesaler_id=std.wholesaler_id,
                wholesaler_name=std.wholesaler_name,
                wholesaler_region_key=std.pharmacy_region_key,
                pharmacy_id=std.pharmacy_id,
                pharmacy_name=std.pharmacy_name,
                pharmacy_region_key=std.pharmacy_region_key,
                pharmacy_sub_region_key=std.pharmacy_sub_region_key,
                hospital_id=None,
                hospital_name=None,
                hospital_mapping_method=None,
                product_id=std.product_id,
                product_name=std.product_name,
                ingredient_code=std.ingredient_code,
                total_quantity=std.quantity,
                total_amount=std.amount,
                metric_month=std.metric_month,
                source_record_type=std.record_type,
            )
            flows.append(flow)

    return flows, gaps
