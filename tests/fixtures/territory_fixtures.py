"""Territory Fixture - Sandbox fixture와 동일한 hospital_id/rep_id 기반"""

# hospital_id → region_key 매핑 (공공 병원 마스터 기반)
HOSPITAL_REGION_MAP = {
    "H001": "서울",
    "H002": "서울",
    "H003": "부산",
    "H004": "부산",
    "H005": "인천",
    "H006": "인천",
}

# Sandbox service 결과를 모사한 HospitalAnalysisRecord 원시 데이터
HOSPITAL_ANALYSIS_RECORDS = [
    # 서울 REP001
    {"hospital_id": "H001", "metric_month": "all", "rep_id": "REP001",
     "total_sales": 7300000.0, "total_target": 8200000.0, "total_visits": 15,
     "attainment_rate": 0.890, "has_sales": True, "has_crm": True, "has_target": True},
    {"hospital_id": "H002", "metric_month": "all", "rep_id": "REP001",
     "total_sales": 2900000.0, "total_target": 3500000.0, "total_visits": 7,
     "attainment_rate": 0.829, "has_sales": True, "has_crm": True, "has_target": True},
    # 부산 REP002
    {"hospital_id": "H003", "metric_month": "all", "rep_id": "REP002",
     "total_sales": 8700000.0, "total_target": 10200000.0, "total_visits": 13,
     "attainment_rate": 0.853, "has_sales": True, "has_crm": True, "has_target": True},
    {"hospital_id": "H004", "metric_month": "all", "rep_id": "REP002",
     "total_sales": 1800000.0, "total_target": 2000000.0, "total_visits": 5,
     "attainment_rate": 0.900, "has_sales": True, "has_crm": True, "has_target": True},
    # 인천 REP003
    {"hospital_id": "H005", "metric_month": "all", "rep_id": "REP003",
     "total_sales": 950000.0, "total_target": 1200000.0, "total_visits": 7,
     "attainment_rate": 0.792, "has_sales": True, "has_crm": True, "has_target": True},
    # 인천 orphan (방문 없음 → gap 테스트용)
    {"hospital_id": "H006", "metric_month": "all", "rep_id": None,
     "total_sales": 500000.0, "total_target": 0.0, "total_visits": 0,
     "attainment_rate": None, "has_sales": True, "has_crm": False, "has_target": False},
]
