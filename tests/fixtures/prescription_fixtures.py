"""
Prescription Fixture 데이터

실데이터 없이 전체 흐름을 검증하기 위한 최소 데이터 세트.
데이터 구조:
  - 3개 도매상 (서울 2, 부산 1)
  - 6개 약국 (서울 3, 부산 2, 인천 1)
  - CRM Phase 2의 hospital_master와 지역 기반 연결
  - 5개 제품
  - 2개월(202501, 202502) 데이터
"""

PRESCRIPTION_MASTER_RECORDS = [
    {"product_name": "제품A정", "dosage_form": "정", "ingredient_code": "A001",
     "ingredient_name": "성분알파", "strength": "10mg", "manufacturer": "한국제약"},
    {"product_name": "제품B캡슐", "dosage_form": "캡슐", "ingredient_code": "B001",
     "ingredient_name": "성분베타", "strength": "20mg", "manufacturer": "대웅제약"},
    {"product_name": "제품C주사", "dosage_form": "주사", "ingredient_code": "C001",
     "ingredient_name": "성분감마", "strength": "5mg/mL", "manufacturer": "동아제약"},
    {"product_name": "제품D정", "dosage_form": "정", "ingredient_code": "D001",
     "ingredient_name": "성분델타", "strength": "5mg", "manufacturer": "유한양행"},
    {"product_name": "제품E시럽", "dosage_form": "시럽", "ingredient_code": "E001",
     "ingredient_name": "성분엡실론", "strength": "100mg/5mL", "manufacturer": "종근당"},
]

# 도매출고 데이터 (도매→약국)
# 약국 시군구 코드는 CRM fixture의 병원 지역과 겹치게 설계하여 연결 가능하도록 함
WHOLESALER_SHIPMENT_RECORDS = [
    # 서울도매A → 서울 약국들 (서울 종로구 병원 H001과 매핑 가능)
    {"wholesaler_name": "서울도매A", "wholesaler_region_key": "11",
     "pharmacy_name": "종로중앙약국", "pharmacy_region_key": "11",
     "pharmacy_sub_region_key": "11010", "pharmacy_postal_code": "03001",
     "product_name": "제품A정", "ingredient_code": "A001", "dosage_form": "정",
     "quantity": 500.0, "amount": 1500000.0, "transaction_date": "2025-01-05",
     "hospital_name": None},
    {"wholesaler_name": "서울도매A", "wholesaler_region_key": "11",
     "pharmacy_name": "강남한마음약국", "pharmacy_region_key": "11",
     "pharmacy_sub_region_key": "11020", "pharmacy_postal_code": "06001",
     "product_name": "제품B캡슐", "ingredient_code": "B001", "dosage_form": "캡슐",
     "quantity": 300.0, "amount": 900000.0, "transaction_date": "2025-01-07",
     "hospital_name": None},
    {"wholesaler_name": "서울도매B", "wholesaler_region_key": "11",
     "pharmacy_name": "마포행복약국", "pharmacy_region_key": "11",
     "pharmacy_sub_region_key": "11030", "pharmacy_postal_code": "04001",
     "product_name": "제품A정", "ingredient_code": "A001", "dosage_form": "정",
     "quantity": 200.0, "amount": 600000.0, "transaction_date": "2025-01-10",
     "hospital_name": None},
    {"wholesaler_name": "서울도매A", "wholesaler_region_key": "11",
     "pharmacy_name": "종로중앙약국", "pharmacy_region_key": "11",
     "pharmacy_sub_region_key": "11010", "pharmacy_postal_code": "03001",
     "product_name": "제품C주사", "ingredient_code": "C001", "dosage_form": "주사",
     "quantity": 100.0, "amount": 800000.0, "transaction_date": "2025-01-15",
     "hospital_name": None},
    # 부산도매 → 부산 약국들 (부산 서구 병원 H003, 해운대 H004와 매핑 가능)
    {"wholesaler_name": "부산도매C", "wholesaler_region_key": "26",
     "pharmacy_name": "서구건강약국", "pharmacy_region_key": "26",
     "pharmacy_sub_region_key": "26010", "pharmacy_postal_code": "49001",
     "product_name": "제품D정", "ingredient_code": "D001", "dosage_form": "정",
     "quantity": 400.0, "amount": 1200000.0, "transaction_date": "2025-01-08",
     "hospital_name": None},
    {"wholesaler_name": "부산도매C", "wholesaler_region_key": "26",
     "pharmacy_name": "해운대바다약국", "pharmacy_region_key": "26",
     "pharmacy_sub_region_key": "26040", "pharmacy_postal_code": "48001",
     "product_name": "제품E시럽", "ingredient_code": "E001", "dosage_form": "시럽",
     "quantity": 150.0, "amount": 450000.0, "transaction_date": "2025-01-12",
     "hospital_name": None},
    # 인천 (H005 인천길병원 지역 - 28010)
    {"wholesaler_name": "서울도매B", "wholesaler_region_key": "11",
     "pharmacy_name": "남동인천약국", "pharmacy_region_key": "28",
     "pharmacy_sub_region_key": "28010", "pharmacy_postal_code": "21001",
     "product_name": "제품A정", "ingredient_code": "A001", "dosage_form": "정",
     "quantity": 250.0, "amount": 750000.0, "transaction_date": "2025-01-20",
     "hospital_name": None},
    # 2월 데이터
    {"wholesaler_name": "서울도매A", "wholesaler_region_key": "11",
     "pharmacy_name": "종로중앙약국", "pharmacy_region_key": "11",
     "pharmacy_sub_region_key": "11010", "pharmacy_postal_code": "03001",
     "product_name": "제품A정", "ingredient_code": "A001", "dosage_form": "정",
     "quantity": 450.0, "amount": 1350000.0, "transaction_date": "2025-02-05",
     "hospital_name": None},
    {"wholesaler_name": "부산도매C", "wholesaler_region_key": "26",
     "pharmacy_name": "서구건강약국", "pharmacy_region_key": "26",
     "pharmacy_sub_region_key": "26010", "pharmacy_postal_code": "49001",
     "product_name": "제품D정", "ingredient_code": "D001", "dosage_form": "정",
     "quantity": 380.0, "amount": 1140000.0, "transaction_date": "2025-02-10",
     "hospital_name": None},
    # 매핑 실패 예상 (존재하지 않는 시군구코드 - gap test용)
    {"wholesaler_name": "서울도매A", "wholesaler_region_key": "11",
     "pharmacy_name": "알수없는약국", "pharmacy_region_key": "99",
     "pharmacy_sub_region_key": "99999", "pharmacy_postal_code": None,
     "product_name": "제품B캡슐", "ingredient_code": "B001", "dosage_form": "캡슐",
     "quantity": 100.0, "amount": 300000.0, "transaction_date": "2025-01-25",
     "hospital_name": None},
]
