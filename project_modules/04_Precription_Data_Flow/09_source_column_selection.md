# 09_source_column_selection.md

목적:
- `data/raw` 원천 파일에서 어떤 컬럼을 수집할지 확정한다.
- `ingest_merge`, `mastering` 구현과 contract 테스트의 기준으로 사용한다.

기준:
- `AGENTS.md` 비협상 규칙
- `07_source_extraction_sop.md`
- `02_data_dictionary.md`

---

## 1) 원천 파일별 수집 컬럼 확정

### 1.1 병원 원천
파일:
- `data/raw/1.병원정보서비스(2025.12.).xlsx`
시트:
- `hospBasisList`

필수 수집 컬럼(Required):
- `provider_id(...)` -> `provider_id` (암호화요양기호)
- `provider_name(...)` -> `provider_name` (요양기관명)
- `provider_type_code(...)` -> `provider_type_code` (종별코드)
- `provider_type_name(...)` -> `provider_type_name` (종별명)
- `provider_addr(...)` -> `provider_addr` (주소)
- `provider_tel(...)` -> `provider_tel` (전화번호)
- `coord_x(...)` -> `coord_x` (좌표X)
- `coord_y(...)` -> `coord_y` (좌표Y)
- `opened_date(...)` -> `opened_date` (개설일자)

보조 수집 컬럼(Optional):
- `sido_code/sido_name/sigungu_code/sigungu_name/eup_myeon_dong/zip_code`

제외 컬럼(Not used in MVP):
- 의사/치과/한방 인력 수 관련 count 컬럼(`*_count`)
- 홈페이지 컬럼

필터:
- `provider_type_name` in `{의원, 병원, 종합병원, 상급종합병원}`

---

### 1.2 약국 원천
파일:
- `data/raw/2.약국정보서비스(2025.12.).xlsx`
시트:
- `parmacyBasisList`

필수 수집 컬럼(Required):
- `pharmacy_provider_id(...)` -> `pharmacy_provider_id` (암호화요양기호)
- `pharmacy_name(...)` -> `pharmacy_name` (요양기관명)
- `pharmacy_type_code(...)` -> `pharmacy_type_code` (종별코드)
- `pharmacy_type_name(...)` -> `pharmacy_type_name` (종별명)
- `pharmacy_addr(...)` -> `pharmacy_addr` (주소)
- `pharmacy_tel(...)` -> `pharmacy_tel` (전화번호)
- `pharmacy_coord_x(...)` -> `pharmacy_coord_x` (좌표X)
- `pharmacy_coord_y(...)` -> `pharmacy_coord_y` (좌표Y)
- `pharmacy_opened_date(...)` -> `pharmacy_opened_date` (개설일자)

보조 수집 컬럼(Optional):
- `sido_code/sido_name/sigungu_code/sigungu_name/eup_myeon_dong/zip_code`

필터:
- `pharmacy_type_name == 약국`

---

### 1.3 도매 원천
파일:
- `data/raw/전국의약품도매업소표준데이터.csv`

필수 수집 컬럼(Required):
- `facility_name(...)` -> `wholesaler_name` (시설명)
- `business_type(...)` -> `biz_type` (업종명)
- `road_address(...)` -> `wholesaler_addr_road` (도로명주소)
- `jibun_address(...)` -> `wholesaler_addr_jibun` (지번주소)
- `phone(...)` -> `wholesaler_tel` (전화번호)
- `latitude(...)` -> `lat` (위도)
- `longitude(...)` -> `lon` (경도)
- `business_status(...)` -> `business_status` (영업상태)
- `as_of_date(...)` -> `as_of_date` (데이터기준일자)
- `provider_org_code(...)` -> `provider_org_code` (제공기관코드)
- `provider_org_name(...)` -> `provider_org_name` (제공기관명)

보조 수집 컬럼(Optional):
- `has_transport_vehicle`
- `has_storage_facility`
- `supervising_agency`

필터:
- `biz_type` contains `의약품도매`
- `business_status == 영업`이면 `active_flag=True`, 그 외 `False`

---

## 2) 공통 lineage 컬럼 (원천 전부 필수)
- `source_file`
- `source_sheet` (xlsx만)
- `source_row_id`

검증 규칙:
- lineage 컬럼 누락 0건
- `source_row_id` 유일성 기준으로 추적 가능

---

## 3) 캐노니컬 스테이징 출력

### 3.1 병원 스테이징
- 출력: `data/raw/ref_provider_address.parquet`
- 핵심 컬럼:
- `provider_id`, `provider_name`, `provider_type_code`, `provider_type_name`
- `provider_addr`, `provider_tel`, `coord_x`, `coord_y`, `opened_date`
- `addr_norm`, `tel_norm`
- `source_file`, `source_sheet`, `source_row_id`

### 3.2 약국 스테이징
- 출력: `data/raw/ref_pharmacy_address.parquet`
- 핵심 컬럼:
- `pharmacy_provider_id`, `pharmacy_name`, `pharmacy_type_code`, `pharmacy_type_name`
- `pharmacy_addr`, `pharmacy_tel`, `pharmacy_coord_x`, `pharmacy_coord_y`, `pharmacy_opened_date`
- `addr_norm`, `tel_norm`
- `source_file`, `source_sheet`, `source_row_id`

### 3.3 도매 스테이징
- 출력: `data/raw/ref_wholesaler_master.parquet`
- 핵심 컬럼:
- `wholesaler_id`, `wholesaler_name`, `biz_type`
- `wholesaler_addr_road`, `wholesaler_addr_jibun`, `wholesaler_tel`
- `lat`, `lon`, `business_status`, `active_flag`, `is_valid_wholesaler`
- `as_of_date`, `provider_org_code`, `provider_org_name`
- `source_file`, `source_row_id`

---

## 4) 테스트에 바로 연결할 Contract 체크리스트
- [ ] 병원 필수 수집 컬럼 9개 모두 존재
- [ ] 약국 필수 수집 컬럼 9개 모두 존재
- [ ] 도매 필수 수집 컬럼 11개 모두 존재
- [ ] lineage 컬럼 누락 0건
- [ ] 필터 조건 적용 후 row count > 0
- [ ] 스테이징 출력 3종 생성 성공

---

## 5) 컬럼 병행표기 정책(영문+한글)
- 문서/리포트/검토 화면에서 기본 표기는 `column_en (한글명)` 형식 사용
- 내부 물리 컬럼은 영문 snake_case 유지
- 다운로드 2종 운영:
- `*_raw`: 영문 컬럼
- `*_label`: 영문+한글 병행 컬럼
