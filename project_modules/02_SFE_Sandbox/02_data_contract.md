# 02 Data Contract

## 목적
Sandbox 독립 실행에 필요한 입력 자산, 출력 자산, OPS handoff 최소 규격을 정의한다.

## 입력 자산
- 필수:
  - `crm_result_asset` 또는 동등한 CRM 표준 입력
  - `sales_standard`
  - `target_standard`
- 선택:
  - `prescription_result_asset`
  - `scenario_override`
  - `manual_adjustment`

## 필수 표준 컬럼
- `scenario_id`
- `hospital_id`
- `rep_id`
- `branch_id`
- `product_id`
- `metric_month`
- `sales_amount`
- `target_amount`
- `visit_count`

## 타입/포맷
- ID: string
- 금액/수치: numeric
- 월: `YYYY-MM`
- 텍스트: UTF-8
- 승인 시각: ISO datetime

## 출력 자산
- `sandbox_result_asset.json`
- `sandbox_builder_payload.json`
- `sandbox_ops_handoff.json`

## handoff 필수 메타
- `company_key`
- `scenario_id`
- `approved_version`
- `approved_by`
- `approved_at`
- `quality_status`
- `handoff_ready`

## 결측/중복 정책
- `scenario_id` 누락: 중단
- 필수 ID 결측 허용치 초과: 중단
- 조인키 중복: 기본 불허
- 승인 메타 누락: handoff 금지

## 계약 위반 처리
- 독립 실행 단계에서 Fail-Fast 중단
- 로그에 위반 컬럼, 건수, 샘플, 시나리오 ID 기록
