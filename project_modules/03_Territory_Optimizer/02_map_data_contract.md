# Territory Independent Build Data Contract

## 목적
Territory 독립 실행에 필요한 입력/출력 데이터 계약과 OPS handoff 최소 규격을 정의한다.

## 입력 도메인
- 필수:
  - `sandbox_result_asset` 또는 동등한 병원 성과 요약 자산
  - `territory_reference_master` (권역/담당자/병원 기준표)
- 선택:
  - `crm_route_activity` 또는 `ops_territory_activity`
  - `manual_override`
  - `scenario_constraints`

## 필수 표준 컬럼
- `scenario_id`
- `hospital_id`
- `rep_id`
- `branch_id`
- `territory_id`
- `region_key`
- `metric_month`
- `sales_amount`
- `visit_count`
- `coverage_flag`

## 타입/포맷
- ID: string
- 수치: numeric
- 월: `YYYY-MM`
- 승인시간: ISO datetime
- 텍스트/한글: UTF-8

## 승인 전 실험 출력
- `territory_result_asset.json`
- `territory_builder_payload.json`
- `territory_map_preview.html` (선택)
- `territory_run_manifest.json`

## OPS handoff 출력
- `territory_result_asset.json`
- `territory_builder_payload.json`
- `territory_ops_handoff.json`

## 필수 handoff 메타
- `company_key`
- `scenario_id`
- `approved_version`
- `approved_by`
- `approved_at`
- `quality_status`
- `handoff_ready`

## 결측/중복 정책
- `scenario_id`, `hospital_id`, `rep_id` 결측: 중단
- 동일 `scenario_id + hospital_id`에 복수 기본 배정: 중단
- 승인 패키지에 승인 메타 누락: handoff 금지

## 계약 위반 처리
- 독립 실행 단계에서는 Fail-Fast 중단
- 위반 컬럼, 건수, 샘플키, 시나리오 ID를 로그에 기록
