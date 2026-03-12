# Source Extraction SOP (원천 추출 절차서)

본 문서는 `docs/TODO.md`의 **2.5 원천 데이터 계약(컬럼 매핑/보완)** 확정안을 기준으로 작성한 운영 절차서다.  
목적은 병원/약국/도매 원천에서 표준 staging 데이터를 일관되게 추출하는 것이다.

---

## 1) 적용 범위
- 병원 원천: `data/raw/1.병원정보서비스(2025.12.).xlsx` (`hospBasisList`)
- 약국 원천: `data/raw/2.약국정보서비스(2025.12.).xlsx` (`parmacyBasisList`)
- 도매 원천: `data/raw/전국의약품도매업소표준데이터.csv`

---

## 2) 산출물
- `data/raw/ref_provider_address.parquet`
- `data/raw/ref_pharmacy_address.parquet`
- `data/raw/ref_wholesaler_master.parquet`

각 산출물에는 lineage 컬럼을 필수 포함한다.
- `source_file`
- `source_sheet` (xlsx만)
- `source_row_id`

---

## 3) 사전 점검
1. 원천 파일 존재 확인
2. 파일 잠금(`~$...xlsx`) 파일 제외
3. 인코딩/헤더 정상 여부 확인
4. 컬럼명 변경 여부 확인(변경 시 즉시 문서 갱신)

---

## 4) 병원 원천 추출 절차

### 4.1 입력
- 파일: `1.병원정보서비스(2025.12.).xlsx`
- 시트: `hospBasisList`

### 4.2 필터
- `종별코드명` 허용값만 포함:
  - `의원`
  - `병원`
  - `종합병원`
  - `상급종합병원`

### 4.3 컬럼 매핑
- `암호화요양기호` -> `provider_id`
- `요양기관명` -> `provider_name`
- `종별코드` -> `provider_type_code`
- `종별코드명` -> `provider_type_name`
- `주소` -> `provider_addr`
- `전화번호` -> `provider_tel`
- `좌표(X)` -> `coord_x`
- `좌표(Y)` -> `coord_y`
- `개설일자` -> `opened_date`

### 4.4 보완/파생
- `hospital_uid`
- `active_flag` (기본 `true`)
- `addr_norm`, `tel_norm`
- `source_file`, `source_sheet`, `source_row_id`

### 4.5 저장
- `ref_provider_address.parquet`로 저장

---

## 5) 약국 원천 추출 절차

### 5.1 입력
- 파일: `2.약국정보서비스(2025.12.).xlsx`
- 시트: `parmacyBasisList`

### 5.2 컬럼 매핑
- `암호화요양기호` -> `pharmacy_provider_id`
- `요양기관명` -> `pharmacy_name`
- `종별코드` -> `pharmacy_type_code`
- `종별코드명` -> `pharmacy_type_name`
- `주소` -> `pharmacy_addr`
- `전화번호` -> `pharmacy_tel`
- `좌표(X)` -> `pharmacy_coord_x`
- `좌표(Y)` -> `pharmacy_coord_y`
- `개설일자` -> `pharmacy_opened_date`

### 5.3 보완/파생
- `pharmacy_uid`
- `pharmacy_account_id` (nullable)
- `territory_code` (후속 매핑)
- `territory_source` (`A`/`C`)
- `active_flag` (기본 `true`)
- `addr_norm`, `tel_norm`
- `source_file`, `source_sheet`, `source_row_id`

### 5.4 저장
- `ref_pharmacy_address.parquet`로 저장

---

## 6) 도매 원천 추출 절차

### 6.1 입력
- 파일: `전국의약품도매업소표준데이터.csv`

### 6.2 필터
- `업종명 == 일반종합도매`
- `영업상태명 == 영업` 우선 사용
  - 필요 시 비영업은 `active_flag=false`로 별도 보관 가능

### 6.3 컬럼 매핑
- `시설명` -> `wholesaler_name`
- `업종명` -> `biz_type`
- `소재지도로명주소` -> `wholesaler_addr_road`
- `소재지지번주소` -> `wholesaler_addr_jibun`
- `전화번호` -> `wholesaler_tel`
- `위도` -> `lat`
- `경도` -> `lon`
- `영업상태명` -> `business_status`
- `데이터기준일자` -> `as_of_date`
- `제공기관코드` -> `provider_org_code`
- `제공기관명` -> `provider_org_name`

### 6.4 보완/파생
- `wholesaler_id`
- `wholesaler_uid_key` (name+addr+tel 정규화 키)
- `active_flag`
- `is_valid_wholesaler`
- `source_file`, `source_row_id`

### 6.5 중복 제거
- 동일명 + 유사주소 + 전화 동일 기준 dedup
- 대표 row 선택 규칙:
  - 최신 `as_of_date` 우선
  - 동률 시 `source_row_id` 최소값 우선

### 6.6 저장
- `ref_wholesaler_master.parquet`로 저장

---

## 7) 공통 품질검증 체크리스트
1. 필수 컬럼 누락 0건
2. 핵심 키 null 비율 보고
3. `addr_norm`, `tel_norm` 생성률 보고
4. 필터 적용 건수 보고
5. 중복 제거 전/후 건수 보고

검증 실패 시:
- 추출은 중단하지 않고 리포트 생성
- 실패 사유를 `validation_report` 후보 이슈로 기록

---

## 8) 인계(Handoff) 기준
- 산출물 3종 파일 생성 완료
- 원천/필터/건수 요약 로그 작성
- 다음 단계(`mastering`) 입력 경로 확정

---

## 9) 변경 관리
- 원천 컬럼 변경 시 즉시 아래 문서 동시 갱신:
  - `docs/TODO.md` (2.5, 2.6)
  - `docs/02_data_dictionary.md`
  - `docs/PRD.md`
  - `docs/01_business_rules.md`

