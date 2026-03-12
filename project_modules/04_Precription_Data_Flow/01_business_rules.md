# Business Rules Spec — Prescription Data Flow (MVP)

## 1. 목적
Prescription Data Flow(PDF)는 **도매→약국 출고(출고일 기준)** 데이터를 기반으로 **담당자 분기 KPI(금액)**를 산출하고, **종합병원–의원 경계 분쟁을 품목+영업권역(territory) 단위 쉐어 정산**으로 해결한다.

## 2. 핵심 정의
- KPI 기준 금액: `amount_ship`(출고가) — MVP 고정
- Raw 보관: `amount_supply`(공급가) 포함(향후 표준화 논의)
- 집계 기준일: `ship_date`(출고일)
- 집계 주기: 분기(Quarter)
- 지역 단위: **영업권역(territory_code)** (행정구역 아님)
- 쉐어 적용 그레인: `year_quarter × territory_code × brand`
- 담당자 귀속 시작: **트래킹 개시 이후만**(소급 없음)

## 2-1. 원천 데이터 정책 (Hybrid)
- 병원/의원 주소 원천: `data/raw/1.병원정보서비스(2025.12.).xlsx`
- 약국 주소 원천: `data/raw/2.약국정보서비스(2025.12.).xlsx`
- 도매 원천: `data/raw/전국의약품도매업소표준데이터.csv`
- 합성 생성 대상: 담당자/품목/출고금액/쉐어룰
- 컬럼 출처는 `source`/`derived`/`synthetic`으로 구분 관리한다.

## 2-2. 원천별 필수 컬럼 규칙
- 병원 원천 최소 컬럼:
  - `암호화요양기호`, `요양기관명`, `종별코드명`, `주소`, `전화번호`
- 병원 필터:
  - `종별코드명 in (의원, 병원, 종합병원, 상급종합병원)`
- 약국 원천 최소 컬럼:
  - `암호화요양기호`, `요양기관명`, `종별코드명`, `주소`, `전화번호`
- 도매 원천 최소 컬럼:
  - `시설명`, `업종명`, `소재지도로명주소`, `영업상태명`, `데이터기준일자`
- 도매 필터:
  - `업종명 == 일반종합도매`
- 필수 보완 컬럼:
  - 병원/약국/도매 모두 `source_file`, `source_row_id`(병원은 `source_sheet` 포함)
  - 도매는 `wholesaler_id`, `active_flag`, `is_valid_wholesaler`를 생성
  - 약국은 `pharmacy_uid`를 생성

## 3. 문전약국 취합/인정 규칙
- 담당자(Rep)는 담당 병원(의원 포함)의 **문전약국 리스트**를 제출한다.
- 제출 리스트는 문전으로 원칙 인정한다.
- 본부는 지도 검증을 통해 “상식적으로 납득 불가한 원거리 약국”은 **취합 단계에서 제외**할 수 있다.
- 운영 원칙: **취합 단계에서 누락된 약국은 실적 산정에 포함되지 않는다**(사전 공지).

## 4. 영업권역 매핑 규칙
약국 `territory_code` 부여 우선순위:
1) 거래처 ID 존재 시: 본부 마스터 territory_code 사용 (source='C')
2) 거래처 ID 없을 시: 제출 주소 기반 수작업 매핑 테이블 적용 (source='A')

## 5. KPI 산출 (Pre-share)
- `BaseAmount(rep, quarter, territory, brand) = Σ amount_ship`
- 입력 Fact는 `FACT_SHIP_PHARMACY_MASTERED`를 기준으로 한다(`RAW` 직접 집계 금지).
- 조건:
  - ship_date가 해당 분기
  - 약국이 territory로 매핑됨
  - 제품이 brand

## 6. 쉐어 정산 (Post-share)
- 적용 대상: `RULE_SHARE_QUARTERLY`에 정의된 `quarter×territory×brand`
- 방식: 풀(pool) 합산 후 배분
  - Pool = 참여자(종병 담당자 1명 + 의원 담당자 n명)의 BaseAmount 합
  - Pool을 본부 비율로 종병 몫/의원 몫 배분
  - 의원 몫은 의원 담당자들 사이에 **의원 BaseAmount 비례**로 재배분
- 정산 주기: 분기
- 룰 누락/합의 미성립: **전분기 룰 자동 연장**
  - 전분기에도 없으면 쉐어 미적용(Pre 유지)
- 룰 변경: 분기마다 본부 조정 가능. 결과 테이블에 룰 버전 기록 필수.

## 7. 미포착(도매 미매핑) 처리
- 케이스: “수요/주장 실적이 있는데 출고 데이터가 안 잡힘”
- 처리:
  1) 담당자 도매명 확인
  2) 본부가 도매에 약국 거래 여부 문의
  3) 확인 결과로 매핑 확정 및 로그 기록
- 상태: `Unverified → Inquired → Confirmed/Rejected`

## 8. 원천 정합성 검증 규칙
- 주소 원천 정합성: `ADDRESS_SOURCE_MISMATCH` 이슈로 관리
- 도매 원천 정합성: `WHOLESALER_SOURCE_MISMATCH` 이슈로 관리
- 도매 업종 필터 미통과: `INVALID_WHOLESALER_TYPE` 이슈로 관리
