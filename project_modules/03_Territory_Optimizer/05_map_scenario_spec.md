# Territory Scenario Spec

## 목적
Territory를 독립 실행형 시나리오 실험 모듈로 운영하기 위한 YAML 기준을 정의한다.

## YAML 예시
```yaml
scenario_name: territory_rebalance_q2
scenario_id: TERR-2026Q2-001

input_sources:
  sandbox_asset: data/inputs/sandbox_result_asset.json
  territory_reference: data/reference/territory_reference_master.xlsx
  route_activity: data/inputs/ops_territory_activity.xlsx
  manual_override: data/inputs/manual_override.xlsx

constraints:
  locked_hospitals: true
  max_hospitals_per_rep: 80
  min_coverage_rate: 0.85
  allow_cross_branch: false

weights:
  sales_weight: 0.4
  visit_weight: 0.2
  coverage_weight: 0.3
  overload_penalty: 0.1

quality_gates:
  duplicate_assignment_max: 0
  territory_unmapped_rate_max: 0.02
  uncovered_hospital_rate_max: 0.15
  handoff_fail_on_warn: false

outputs:
  result_asset: territory_result_asset.json
  builder_payload: territory_builder_payload.json
  handoff_manifest: territory_ops_handoff.json
  preview_html: territory_map_preview.html
```

## 규칙
- 시나리오는 파일 단위로 버전 관리한다.
- 같은 입력으로 여러 시나리오를 비교할 수 있어야 한다.
- OPS에는 승인된 시나리오 하나만 handoff 한다.
- 승인되지 않은 시나리오는 `draft`로 유지한다.
