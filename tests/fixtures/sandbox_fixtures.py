"""
Sandbox Fixture 데이터

CRM Phase 2 fixture의 hospital_id / rep_id 축을 기준으로 구성.
실데이터 없이 전체 분석 흐름을 검증하기 위한 최소 데이터.

구성:
  - 담당자 3명 (REP001~REP003)
  - 병원 6개 (H001~H006, CRM fixture와 동일)
  - 제품 3개 (PROD_A001, PROD_B001, PROD_C001)
  - 2개월 (202501, 202502)
"""

# ── CRM 도메인 레코드 (crm_result_asset 기반 파생) ──────────────
CRM_DOMAIN_RECORDS = [
    # REP001 - 서울 종로, 강남
    {"hospital_id": "H001", "rep_id": "REP001", "metric_month": "202501",
     "total_visits": 8, "detail_call_count": 5, "activity_types": ["방문", "전화"]},
    {"hospital_id": "H002", "rep_id": "REP001", "metric_month": "202501",
     "total_visits": 4, "detail_call_count": 2, "activity_types": ["방문"]},
    {"hospital_id": "H001", "rep_id": "REP001", "metric_month": "202502",
     "total_visits": 7, "detail_call_count": 4, "activity_types": ["방문", "이메일"]},
    {"hospital_id": "H002", "rep_id": "REP001", "metric_month": "202502",
     "total_visits": 3, "detail_call_count": 1, "activity_types": ["방문"]},
    # REP002 - 부산
    {"hospital_id": "H003", "rep_id": "REP002", "metric_month": "202501",
     "total_visits": 6, "detail_call_count": 3, "activity_types": ["방문", "전화"]},
    {"hospital_id": "H004", "rep_id": "REP002", "metric_month": "202501",
     "total_visits": 5, "detail_call_count": 4, "activity_types": ["방문"]},
    {"hospital_id": "H003", "rep_id": "REP002", "metric_month": "202502",
     "total_visits": 7, "detail_call_count": 5, "activity_types": ["방문"]},
    # REP003 - 인천
    {"hospital_id": "H005", "rep_id": "REP003", "metric_month": "202501",
     "total_visits": 3, "detail_call_count": 1, "activity_types": ["방문"]},
    {"hospital_id": "H005", "rep_id": "REP003", "metric_month": "202502",
     "total_visits": 4, "detail_call_count": 2, "activity_types": ["전화", "방문"]},
]

# ── 매출 실적 데이터 (fixture, hospital_id 기준) ─────────────────
SALES_RECORDS = [
    # H001 - 제품A, B
    {"hospital_id": "H001", "rep_id": "REP001", "metric_month": "202501",
     "product_id": "PROD_A001", "sales_amount": 3500000.0, "sales_quantity": 350.0, "channel": "직판"},
    {"hospital_id": "H001", "rep_id": "REP001", "metric_month": "202501",
     "product_id": "PROD_B001", "sales_amount": 1200000.0, "sales_quantity": 60.0, "channel": "직판"},
    {"hospital_id": "H001", "rep_id": "REP001", "metric_month": "202502",
     "product_id": "PROD_A001", "sales_amount": 3800000.0, "sales_quantity": 380.0, "channel": "직판"},
    # H002
    {"hospital_id": "H002", "rep_id": "REP001", "metric_month": "202501",
     "product_id": "PROD_A001", "sales_amount": 2100000.0, "sales_quantity": 210.0, "channel": "직판"},
    {"hospital_id": "H002", "rep_id": "REP001", "metric_month": "202502",
     "product_id": "PROD_B001", "sales_amount": 800000.0, "sales_quantity": 40.0, "channel": "직판"},
    # H003 - 부산
    {"hospital_id": "H003", "rep_id": "REP002", "metric_month": "202501",
     "product_id": "PROD_A001", "sales_amount": 4200000.0, "sales_quantity": 420.0, "channel": "직판"},
    {"hospital_id": "H003", "rep_id": "REP002", "metric_month": "202502",
     "product_id": "PROD_A001", "sales_amount": 4500000.0, "sales_quantity": 450.0, "channel": "직판"},
    # H004
    {"hospital_id": "H004", "rep_id": "REP002", "metric_month": "202501",
     "product_id": "PROD_C001", "sales_amount": 1800000.0, "sales_quantity": 90.0, "channel": "직판"},
    # H005 - 인천 (CRM에는 있지만 sales가 1건만)
    {"hospital_id": "H005", "rep_id": "REP003", "metric_month": "202501",
     "product_id": "PROD_B001", "sales_amount": 950000.0, "sales_quantity": 47.0, "channel": "직판"},
    # H006 - sales에만 있고 CRM 없음 (orphan_sales 테스트용)
    {"hospital_id": "H006", "rep_id": "REP003", "metric_month": "202501",
     "product_id": "PROD_A001", "sales_amount": 500000.0, "sales_quantity": 50.0, "channel": "직판"},
]

# ── 목표 데이터 (hospital_id 기준) ──────────────────────────────
TARGET_RECORDS = [
    {"rep_id": "REP001", "metric_month": "202501", "product_id": "PROD_A001",
     "target_amount": 4000000.0, "hospital_id": "H001"},
    {"rep_id": "REP001", "metric_month": "202501", "product_id": "PROD_B001",
     "target_amount": 1500000.0, "hospital_id": "H001"},
    {"rep_id": "REP001", "metric_month": "202501", "product_id": "PROD_A001",
     "target_amount": 2500000.0, "hospital_id": "H002"},
    {"rep_id": "REP001", "metric_month": "202502", "product_id": "PROD_A001",
     "target_amount": 4200000.0, "hospital_id": "H001"},
    {"rep_id": "REP002", "metric_month": "202501", "product_id": "PROD_A001",
     "target_amount": 5000000.0, "hospital_id": "H003"},
    {"rep_id": "REP002", "metric_month": "202501", "product_id": "PROD_C001",
     "target_amount": 2000000.0, "hospital_id": "H004"},
    {"rep_id": "REP002", "metric_month": "202502", "product_id": "PROD_A001",
     "target_amount": 5200000.0, "hospital_id": "H003"},
    {"rep_id": "REP003", "metric_month": "202501", "product_id": "PROD_B001",
     "target_amount": 1200000.0, "hospital_id": "H005"},
]
