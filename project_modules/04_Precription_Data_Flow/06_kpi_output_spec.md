# KPI Output Spec - Prescription Data Flow Independent Build

## 1) 핵심 상세 산출물
### 1.1 `rep_kpi_quarter`
- Grain: `year_quarter x rep_id x territory_code x brand`
- 주요 컬럼:
  - `year_quarter`
  - `rep_id`, `rep_name`
  - `territory_code`
  - `brand`
  - `amount_pre_share`
  - `amount_post_share`
  - `share_applied_flag`
  - `share_rule_version`
  - `share_rule_source`
  - `pool_amount`
  - `role_in_rule`
  - `clinic_realloc_weight`
  - `tracking_quality_flag`

### 1.2 `kpi_summary_quarter`
- Grain: `year_quarter`
- 주요 컬럼:
  - `total_pre_share`
  - `total_post_share`
  - `share_rules_applied_count`
  - `extended_rules_count`
  - `unknown_wholesaler_cases_count`
  - `high_risk_issue_count`

### 1.3 `tracking_report`
- Grain: `year_quarter x hospital_uid x brand`
- 주요 컬럼:
  - `tracked_amount`
  - `tracked_qty`
  - `claim_amount`
  - `coverage_ratio`
  - `gap_amount`
  - `gap_ratio`
  - `tracking_quality_flag`

### 1.4 `validation_report`
- Grain: issue 1 row
- 주요 컬럼:
  - `issue_type`
  - `severity`
  - `entity_id`
  - `year_quarter`
  - `details`
  - `resolution_status`

## 2) 공식 결과 자산
### 2.1 `prescription_result_asset.json`
이 파일은 Prescription의 공식 결과 요약본이다.

필수 키:
- `module_name`
- `run_id`
- `input_manifest`
- `rule_version`
- `tracking_summary`
- `reconciliation_summary`
- `validation_gap_summary`
- `share_summary`
- `kpi_summary`
- `quality_status`
- `approval_status`

### 2.2 `prescription_builder_payload.json`
이 파일은 사람이 보는 화면을 만들기 위한 가벼운 payload다.

필수 키:
- `template_name`
- `header_summary`
- `tracking_cards`
- `share_cards`
- `kpi_cards`
- `validation_cards`
- `download_refs`

## 3) OPS 전달 파일
### 3.1 `prescription_ops_handoff.json`
이 파일은 OPS가 읽는 최종 전달 메타다.

필수 키:
- `module_name`
- `approved_version`
- `approved_by`
- `approved_at`
- `quality_status`
- `handoff_ready`
- `result_asset_path`
- `builder_payload_path`

## 4) 승인 메타 규칙
- `approval_status`: `approved` / `rejected` / `pending`
- `approved_version`: 승인된 결과 버전
- `approved_by`: 승인자
- `approved_at`: 승인 시각
- `approval_note`: 승인 또는 반려 사유

## 5) 원칙
`상세 테이블은 내부 검토용, result_asset은 공식 요약용, ops_handoff는 외부 전달용으로 분리한다.`
