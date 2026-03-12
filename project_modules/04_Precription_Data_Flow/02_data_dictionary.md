# Data Dictionary — Prescription Data Flow (MVP)

## 0) Data Strategy (Hybrid)
- 병원/의원 주소 원천: `data/raw/1.병원정보서비스(2025.12.).xlsx` (`hospBasisList`)
- 약국 주소 원천: `data/raw/2.약국정보서비스(2025.12.).xlsx` (`parmacyBasisList`)
- 도매 원천: `data/raw/전국의약품도매업소표준데이터.csv`
- 합성 대상: 담당자/품목/출고금액/쉐어룰
- 컬럼 출처 메타: `source`(원천), `derived`(파생), `synthetic`(합성)

## 1) REF_PROVIDER_ADDRESS (원천 정제 스냅샷)
- Grain: provider 1 row
- Key(권장): (`source_file`, `source_sheet`, `source_row_id`)

### Columns
- source_file (string, origin_type: source)
- source_sheet (string, origin_type: source)
- source_row_id (string/int, origin_type: source)
- provider_id (string, origin_type: source) — 암호화요양기호
- provider_name (string, origin_type: source)
- provider_type_code (string, origin_type: source)
- provider_type_name (string, origin_type: source)
- provider_addr (string, origin_type: source)
- provider_tel (string, nullable, origin_type: source)
- coord_x (float, nullable, origin_type: source)
- coord_y (float, nullable, origin_type: source)
- opened_date (date/string, nullable, origin_type: source)
- addr_norm (string, origin_type: derived)
- tel_norm (string, origin_type: derived)

## 2) DIM_WHOLESALER_MASTER (도매 마스터; 원천+정제)
- Grain: wholesaler 1 row
- PK: wholesaler_id

### Columns
- wholesaler_id (string, origin_type: derived)
- wholesaler_name (string, origin_type: source) — 시설명
- biz_type (string, origin_type: source) — 업종명
- wholesaler_addr_road (string, nullable, origin_type: source)
- wholesaler_addr_jibun (string, nullable, origin_type: source)
- wholesaler_tel (string, nullable, origin_type: source)
- lat (float, nullable, origin_type: source)
- lon (float, nullable, origin_type: source)
- business_status (string, origin_type: source)
- active_flag (bool, origin_type: derived)
- is_valid_wholesaler (bool, origin_type: derived; 업종 필터 통과 여부)
- as_of_date (date/string, nullable, origin_type: source)
- provider_org_code (string, nullable, origin_type: source)
- provider_org_name (string, nullable, origin_type: source)
- wholesaler_uid_key (string, origin_type: derived)
- source_file (string, origin_type: source)
- source_row_id (string/int, origin_type: source)

## 3) FACT_SHIP_PHARMACY_RAW (도매→약국 출고 Raw Fact)
- Grain: `ship_date × wholesaler × pharmacy_name/addr/tel × brand (× sku optional)`
- Key(권장): `ship_id` 또는 복합키

### Columns
- ship_id (string, optional, origin_type: derived)
- ship_date (date, origin_type: synthetic) — 집계 기준
- year_month (YYYY-MM, origin_type: derived)
- year_quarter (YYYY-Q, origin_type: derived)
- wholesaler_id (string, origin_type: derived)
- wholesaler_name (string, origin_type: source)
- wholesaler_raw_name (string, nullable, origin_type: source)
- pharmacy_name (string, origin_type: source)
- pharmacy_addr (string, origin_type: source)
- pharmacy_tel (string, origin_type: source)
- pharmacy_account_id (string, nullable, origin_type: derived)
- brand (string, origin_type: synthetic) — 쉐어 단위
- sku (string, nullable, origin_type: derived)
- qty (float/int, origin_type: synthetic)
- amount_ship (float, origin_type: synthetic) — KPI 기준(출고가)
- amount_supply (float, nullable, origin_type: synthetic) — 공급가(보조)
- data_source (string, optional, origin_type: synthetic; 예: `hybrid_simulated`)
- is_unknown_wholesaler_case (bool, optional, origin_type: synthetic)

## 4) FACT_SHIP_PHARMACY_MASTERED (마스터링 완료 Fact)
- Grain: `ship_date × wholesaler × pharmacy_uid × brand (× sku optional)`
- Key(권장): (`ship_id`) 또는 (`ship_date`, `wholesaler_id`, `pharmacy_uid`, `brand`, `sku`)

### Columns
- ship_id (string, optional, origin_type: derived)
- ship_date (date, origin_type: synthetic)
- year_month (YYYY-MM, origin_type: derived)
- year_quarter (YYYY-Q, origin_type: derived)
- wholesaler_id (string, origin_type: derived)
- wholesaler_name (string, origin_type: source)
- pharmacy_uid (string, not null, origin_type: derived)
- pharmacy_name (string, origin_type: source)
- pharmacy_addr (string, origin_type: source)
- pharmacy_tel (string, origin_type: source)
- pharmacy_account_id (string, nullable, origin_type: derived)
- territory_code (string, nullable, origin_type: derived)
- territory_source ('A'/'C', nullable, origin_type: derived)
- brand (string, origin_type: synthetic)
- sku (string, nullable, origin_type: derived)
- qty (float/int, origin_type: synthetic)
- amount_ship (float, origin_type: synthetic)
- amount_supply (float, nullable, origin_type: synthetic)
- mapping_quality_flag (`C`/`A`/`UNMAPPED`, origin_type: derived)
- mastering_run_id (string, optional, origin_type: derived)

## 5) DIM_PHARMACY_MASTER (약국 마스터)
- Grain: pharmacy 1 row
- PK: pharmacy_uid

### Columns
- pharmacy_uid (string, origin_type: derived)
- pharmacy_name (string, origin_type: source)
- pharmacy_addr (string, origin_type: source)
- pharmacy_tel (string, origin_type: source)
- pharmacy_account_id (string, nullable, origin_type: derived)
- territory_code (string, origin_type: derived)
- territory_source ('A' manual / 'C' master, origin_type: derived)
- active_flag (bool, origin_type: derived)
- source_file (string, nullable, origin_type: source)
- source_row_id (string/int, nullable, origin_type: source)
- addr_norm (string, optional, origin_type: derived)
- tel_norm (string, optional, origin_type: derived)
- created_at, updated_at (optional, origin_type: derived)

## 6) DIM_HOSPITAL_MASTER (병원 마스터)
- Grain: hospital 1 row
- PK: hospital_uid

### Columns
- hospital_uid (string, origin_type: derived)
- provider_id (string, nullable, origin_type: source)
- hospital_name (string, origin_type: source)
- hospital_addr (string, origin_type: source)
- hospital_tel (string, nullable, origin_type: source)
- hospital_type (optional, origin_type: source)
- territory_code (string, origin_type: derived)
- active_flag (bool, origin_type: derived)
- coord_x (float, nullable, origin_type: source)
- coord_y (float, nullable, origin_type: source)
- opened_date (date/string, nullable, origin_type: source)
- source_file (string, nullable, origin_type: source)
- source_sheet (string, nullable, origin_type: source)
- source_row_id (string/int, nullable, origin_type: source)

## 7) MAP_FRONT_PHARMACY (병원-문전약국 매핑)
- Grain: `hospital_uid × pharmacy_uid` relationship
- Key(권장): (hospital_uid, pharmacy_uid, valid_from)

### Columns
- hospital_uid (string, origin_type: derived)
- pharmacy_uid (string, origin_type: derived)
- submitted_by_rep_id (string, origin_type: synthetic)
- submitted_quarter (string, origin_type: synthetic)
- status (approved/rejected/pending, origin_type: synthetic)
- hq_review_note (nullable, origin_type: synthetic)
- valid_from (optional, origin_type: synthetic)
- valid_to (nullable, origin_type: synthetic)

## 8) DIM_REP_ASSIGN (담당자-권역 배정)
- Grain: `rep_id × territory_code × 기간`
- Key(권장): (rep_id, territory_code, valid_from)

### Columns
- rep_id (string, origin_type: synthetic)
- rep_name (string, origin_type: synthetic)
- territory_code (string, origin_type: derived)
- valid_from (date, origin_type: synthetic)
- valid_to (nullable, origin_type: synthetic)

## 9) RULE_SHARE_QUARTERLY (분기 쉐어 룰)
- Grain: `year_quarter × territory_code × brand` (+ version)
- Key(권장): (year_quarter, territory_code, brand, version)

### Columns
- year_quarter (string, origin_type: synthetic)
- territory_code (string, origin_type: derived)
- brand (string, origin_type: synthetic)
- ratio_hosp (float 0~1, origin_type: synthetic)
- ratio_clinic (float, origin_type: synthetic)
- version (int, origin_type: synthetic)
- status (draft/confirmed, origin_type: synthetic)
- extend_prev_quarter_flag (bool, origin_type: synthetic)
- notes (nullable, origin_type: synthetic)

### RULE_SHARE_PARTICIPANT (정규화 권장)
- Grain: `year_quarter × territory_code × brand × rep_id`
- Columns:
  - year_quarter (string, origin_type: synthetic)
  - territory_code (string, origin_type: derived)
  - brand (string, origin_type: synthetic)
  - rep_id (string, origin_type: synthetic)
  - role(hosp/clinic) (string, origin_type: synthetic)

## 10) LOG_WHOLESALER_TRACE (미포착 케이스 로그)
- Grain: case 1 row
- PK: case_id

### Columns
- case_id (string, origin_type: derived)
- created_quarter (string, origin_type: derived)
- pharmacy_uid (string, origin_type: derived)
- rep_id (string, origin_type: synthetic)
- brand (string, origin_type: synthetic)
- suspected_wholesaler_name (string, origin_type: source)
- status (Unverified/Inquired/Confirmed/Rejected, origin_type: synthetic)
- hq_result_note (nullable, origin_type: synthetic)
- resolved_date (nullable, origin_type: synthetic)

## 11) PRESCRIPTION_RESULT_ASSET (공식 결과 요약)
- Grain: run 1 row
- Key(권장): `run_id`

### Columns
- run_id (string, origin_type: derived)
- module_name (string, origin_type: derived)
- input_manifest_ref (string, origin_type: derived)
- rule_version (string/int, origin_type: derived)
- tracking_summary (json/object, origin_type: derived)
- reconciliation_summary (json/object, origin_type: derived)
- validation_gap_summary (json/object, origin_type: derived)
- share_summary (json/object, origin_type: derived)
- kpi_summary (json/object, origin_type: derived)
- quality_status (PASS/WARN/FAIL, origin_type: derived)
- approval_status (approved/rejected/pending, origin_type: derived)

## 12) PRESCRIPTION_BUILDER_PAYLOAD (표현용 payload)
- Grain: run 1 row
- Key(권장): `run_id`

### Columns
- run_id (string, origin_type: derived)
- template_name (string, origin_type: derived)
- header_summary (json/object, origin_type: derived)
- tracking_cards (json/array, origin_type: derived)
- share_cards (json/array, origin_type: derived)
- kpi_cards (json/array, origin_type: derived)
- validation_cards (json/array, origin_type: derived)
- download_refs (json/array, origin_type: derived)

## 13) PRESCRIPTION_OPS_HANDOFF (OPS 전달 메타)
- Grain: approved package 1 row
- Key(권장): `approved_version`

### Columns
- module_name (string, origin_type: derived)
- approved_version (string/int, origin_type: derived)
- approved_by (string, origin_type: derived)
- approved_at (datetime/string, origin_type: derived)
- approval_note (nullable, origin_type: derived)
- quality_status (PASS/WARN/FAIL, origin_type: derived)
- handoff_ready (bool, origin_type: derived)
- result_asset_path (string, origin_type: derived)
- builder_payload_path (string, origin_type: derived)
