"""
CRM Fixture 데이터 - 테스트 및 실데이터 없는 환경에서 사용

실데이터가 없어도 전체 흐름을 검증할 수 있는 최소 데이터 세트.
가상의 제약회사 영업 데이터 (10개 병원, 5명 담당자, 2개 지점)
"""

from datetime import date


# ────────────────────────────────────────
# 병원 마스터 Fixture
# ────────────────────────────────────────

HOSPITAL_FIXTURE_RECORDS = [
    {"hospital_id": "H001", "hospital_name": "서울중앙병원", "hospital_type": "종합병원",
     "region_key": "11", "sub_region_key": "11010", "address": "서울 종로구", "phone": "02-1000-0001"},
    {"hospital_id": "H002", "hospital_name": "강남365의원", "hospital_type": "의원",
     "region_key": "11", "sub_region_key": "11020", "address": "서울 강남구", "phone": "02-1000-0002"},
    {"hospital_id": "H003", "hospital_name": "부산대학병원", "hospital_type": "상급종합",
     "region_key": "26", "sub_region_key": "26010", "address": "부산 서구", "phone": "051-1000-0003"},
    {"hospital_id": "H004", "hospital_name": "해운대내과의원", "hospital_type": "의원",
     "region_key": "26", "sub_region_key": "26040", "address": "부산 해운대구", "phone": "051-1000-0004"},
    {"hospital_id": "H005", "hospital_name": "인천길병원", "hospital_type": "종합병원",
     "region_key": "28", "sub_region_key": "28010", "address": "인천 남동구", "phone": "032-1000-0005"},
    {"hospital_id": "H006", "hospital_name": "마포가정의학과", "hospital_type": "의원",
     "region_key": "11", "sub_region_key": "11030", "address": "서울 마포구", "phone": "02-1000-0006"},
    {"hospital_id": "H007", "hospital_name": "대구파티마병원", "hospital_type": "병원",
     "region_key": "27", "sub_region_key": "27010", "address": "대구 동구", "phone": "053-1000-0007"},
    {"hospital_id": "H008", "hospital_name": "수원아주대병원", "hospital_type": "상급종합",
     "region_key": "41", "sub_region_key": "41110", "address": "경기 수원시", "phone": "031-1000-0008"},
    {"hospital_id": "H009", "hospital_name": "분당서울대병원", "hospital_type": "상급종합",
     "region_key": "41", "sub_region_key": "41130", "address": "경기 성남시", "phone": "031-1000-0009"},
    {"hospital_id": "H010", "hospital_name": "서대문연세내과", "hospital_type": "의원",
     "region_key": "11", "sub_region_key": "11040", "address": "서울 서대문구", "phone": "02-1000-0010"},
]


# ────────────────────────────────────────
# 회사 마스터 Fixture
# ────────────────────────────────────────

COMPANY_MASTER_FIXTURE_RECORDS = [
    # 서울지점 (BR01) - 담당자 3명
    {"rep_id": "R001", "rep_name": "김영업", "branch_id": "BR01", "branch_name": "서울지점",
     "hospital_id": "H001", "hospital_name": "서울중앙병원", "channel_type": "종합병원", "is_primary": True},
    {"rep_id": "R001", "rep_name": "김영업", "branch_id": "BR01", "branch_name": "서울지점",
     "hospital_id": "H002", "hospital_name": "강남365의원", "channel_type": "의원", "is_primary": True},
    {"rep_id": "R001", "rep_name": "김영업", "branch_id": "BR01", "branch_name": "서울지점",
     "hospital_id": "H006", "hospital_name": "마포가정의학과", "channel_type": "의원", "is_primary": True},

    {"rep_id": "R002", "rep_name": "이기획", "branch_id": "BR01", "branch_name": "서울지점",
     "hospital_id": "H009", "hospital_name": "분당서울대병원", "channel_type": "상급종합", "is_primary": True},
    {"rep_id": "R002", "rep_name": "이기획", "branch_id": "BR01", "branch_name": "서울지점",
     "hospital_id": "H010", "hospital_name": "서대문연세내과", "channel_type": "의원", "is_primary": True},

    {"rep_id": "R003", "rep_name": "박전략", "branch_id": "BR01", "branch_name": "서울지점",
     "hospital_id": "H002", "hospital_name": "강남365의원", "channel_type": "의원", "is_primary": False},
    {"rep_id": "R003", "rep_name": "박전략", "branch_id": "BR01", "branch_name": "서울지점",
     "hospital_id": "H008", "hospital_name": "수원아주대병원", "channel_type": "상급종합", "is_primary": True},

    # 부산지점 (BR02) - 담당자 2명
    {"rep_id": "R004", "rep_name": "최현장", "branch_id": "BR02", "branch_name": "부산지점",
     "hospital_id": "H003", "hospital_name": "부산대학병원", "channel_type": "상급종합", "is_primary": True},
    {"rep_id": "R004", "rep_name": "최현장", "branch_id": "BR02", "branch_name": "부산지점",
     "hospital_id": "H004", "hospital_name": "해운대내과의원", "channel_type": "의원", "is_primary": True},

    {"rep_id": "R005", "rep_name": "정분석", "branch_id": "BR02", "branch_name": "부산지점",
     "hospital_id": "H004", "hospital_name": "해운대내과의원", "channel_type": "의원", "is_primary": False},
    {"rep_id": "R005", "rep_name": "정분석", "branch_id": "BR02", "branch_name": "부산지점",
     "hospital_id": "H005", "hospital_name": "인천길병원", "channel_type": "종합병원", "is_primary": True},
    {"rep_id": "R005", "rep_name": "정분석", "branch_id": "BR02", "branch_name": "부산지점",
     "hospital_id": "H007", "hospital_name": "대구파티마병원", "channel_type": "병원", "is_primary": True},
]


# ────────────────────────────────────────
# CRM 활동 Fixture
# ────────────────────────────────────────

CRM_ACTIVITY_FIXTURE_RECORDS = [
    # R001 - 202501
    {"rep_id": "R001", "hospital_id": "H001", "branch_id": "BR01",
     "activity_date": date(2025, 1, 8), "metric_month": "202501",
     "activity_type": "방문", "visit_count": 1, "products_mentioned": ["제품A"],
     "has_detail_call": True, "notes": None},
    {"rep_id": "R001", "hospital_id": "H002", "branch_id": "BR01",
     "activity_date": date(2025, 1, 10), "metric_month": "202501",
     "activity_type": "방문", "visit_count": 2, "products_mentioned": ["제품A", "제품B"],
     "has_detail_call": False, "notes": None},
    {"rep_id": "R001", "hospital_id": "H006", "branch_id": "BR01",
     "activity_date": date(2025, 1, 15), "metric_month": "202501",
     "activity_type": "전화", "visit_count": 1, "products_mentioned": [],
     "has_detail_call": False, "notes": "다음 방문 예약"},
    # R001 - 202502
    {"rep_id": "R001", "hospital_id": "H001", "branch_id": "BR01",
     "activity_date": date(2025, 2, 5), "metric_month": "202502",
     "activity_type": "방문", "visit_count": 1, "products_mentioned": ["제품A"],
     "has_detail_call": True, "notes": None},
    {"rep_id": "R001", "hospital_id": "H002", "branch_id": "BR01",
     "activity_date": date(2025, 2, 12), "metric_month": "202502",
     "activity_type": "방문", "visit_count": 1, "products_mentioned": ["제품B"],
     "has_detail_call": True, "notes": None},

    # R002 - 202501
    {"rep_id": "R002", "hospital_id": "H009", "branch_id": "BR01",
     "activity_date": date(2025, 1, 7), "metric_month": "202501",
     "activity_type": "방문", "visit_count": 1, "products_mentioned": ["제품C"],
     "has_detail_call": True, "notes": None},
    {"rep_id": "R002", "hospital_id": "H010", "branch_id": "BR01",
     "activity_date": date(2025, 1, 20), "metric_month": "202501",
     "activity_type": "행사", "visit_count": 1, "products_mentioned": ["제품C", "제품D"],
     "has_detail_call": False, "notes": "학술 심포지엄"},

    # R003 - 202501
    {"rep_id": "R003", "hospital_id": "H008", "branch_id": "BR01",
     "activity_date": date(2025, 1, 9), "metric_month": "202501",
     "activity_type": "방문", "visit_count": 2, "products_mentioned": ["제품A"],
     "has_detail_call": True, "notes": None},

    # R004 - 202501, 202502
    {"rep_id": "R004", "hospital_id": "H003", "branch_id": "BR02",
     "activity_date": date(2025, 1, 6), "metric_month": "202501",
     "activity_type": "방문", "visit_count": 1, "products_mentioned": ["제품D"],
     "has_detail_call": True, "notes": None},
    {"rep_id": "R004", "hospital_id": "H004", "branch_id": "BR02",
     "activity_date": date(2025, 1, 13), "metric_month": "202501",
     "activity_type": "방문", "visit_count": 1, "products_mentioned": ["제품D"],
     "has_detail_call": False, "notes": None},
    {"rep_id": "R004", "hospital_id": "H003", "branch_id": "BR02",
     "activity_date": date(2025, 2, 3), "metric_month": "202502",
     "activity_type": "방문", "visit_count": 1, "products_mentioned": ["제품D"],
     "has_detail_call": True, "notes": None},

    # R005 - 202501, 202502
    {"rep_id": "R005", "hospital_id": "H005", "branch_id": "BR02",
     "activity_date": date(2025, 1, 14), "metric_month": "202501",
     "activity_type": "방문", "visit_count": 1, "products_mentioned": ["제품A", "제품E"],
     "has_detail_call": True, "notes": None},
    {"rep_id": "R005", "hospital_id": "H007", "branch_id": "BR02",
     "activity_date": date(2025, 1, 21), "metric_month": "202501",
     "activity_type": "전화", "visit_count": 1, "products_mentioned": [],
     "has_detail_call": False, "notes": None},
    {"rep_id": "R005", "hospital_id": "H005", "branch_id": "BR02",
     "activity_date": date(2025, 2, 10), "metric_month": "202502",
     "activity_type": "방문", "visit_count": 1, "products_mentioned": ["제품E"],
     "has_detail_call": True, "notes": None},
]
