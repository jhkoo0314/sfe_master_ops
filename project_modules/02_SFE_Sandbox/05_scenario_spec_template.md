# 05 Scenario Spec Template

## 목적
Sandbox 독립 실행 시나리오 정의 템플릿을 표준화한다.

## 필수 항목
- `scenario_name`
- `scenario_id`
- `input_assets`
- `grain`
- `join_keys`
- `filters`
- `metrics`
- `quality_gates`
- `approval_status`
- `handoff_export`

## 작성 템플릿
```yaml
scenario_name: quarterly_performance_review
scenario_id: SBOX-2026Q2-001

input_assets:
  crm_asset: data/input/crm_result_asset.json
  sales_standard: data/input/sales_standard.parquet
  target_standard: data/input/target_standard.parquet
  prescription_asset: data/input/prescription_result_asset.json

grain: [hospital_id, metric_month, product_id]

join_keys:
  crm_sales: [hospital_id, metric_month]
  sales_target: [hospital_id, metric_month, product_id]

filters:
  metric_month_from: 2026-01
  metric_month_to: 2026-06

metrics:
  - sales_amount
  - target_amount
  - attainment_rate
  - visit_count
  - rx_link_rate

quality_gates:
  key_null_rate_max: 0.02
  join_row_growth_rate_max: 1.10
  orphan_sales_rate_max: 0.05

approval_status: draft

handoff_export:
  enabled: true
  output_files:
    result_asset: sandbox_result_asset.json
    builder_payload: sandbox_builder_payload.json
    ops_handoff: sandbox_ops_handoff.json
```

## 규칙
- 시나리오는 파일 단위로 버전 관리한다.
- 승인 전 결과와 승인 완료 결과를 구분한다.
- OPS에는 승인된 시나리오 하나만 넘긴다.
- Sandbox 범위 밖 예시는 시나리오 문서에 넣지 않는다.
