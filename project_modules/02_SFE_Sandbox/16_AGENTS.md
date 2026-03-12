# AGENTS.md (Sandbox Independent Build)

## 목적
이 파일은 Sandbox를 독립 실행형 분석 엔진으로 문서화하고 구현할 때 따라야 할 작업 규칙을 정의한다.

## 작업 범위
- Sandbox core는 독립 분석 엔진 문서에 집중한다.
- OPS 자체 설명이나 다른 모듈 문서를 Sandbox 안에 섞지 않는다.
- 승인 전 분석과 OPS handoff를 분리해 문서화한다.

## 우선 적용 문서 순서
1. `14_PRD.md`
2. `01_architecture.md`
3. `15_workflow.md`
4. `02_data_contract.md`
5. `04_join_grain_policy.md`
6. `05_scenario_spec_template.md`
7. `06_engine_stage_spec.md`
8. `18_ops_handoff_contract.md`
9. `19_boundary_policy.md`
10. `07_runbook_ops.md`
11. `08_quality_checklist.md`
12. `10_security_governance.md`
13. `12_rebuild_improvement_comparison.md`

## 핵심 원칙
- Sandbox는 OPS를 대신하지 않는다.
- Sandbox는 승인된 입력 자산만 읽는다.
- Sandbox 공식 결과는 `sandbox_result_asset`이다.
- OPS에는 승인된 결과만 넘긴다.
- 다른 모듈 내용은 Sandbox core 문서에 남기지 않는다.

## 구현 규칙
- 단계는 `load -> normalize -> join_validate -> analyze -> summarize -> approve/export`
- `scenario_id`, `approval_status`, `approved_version` 메타를 유지
- Builder는 표현용 payload만 담당
- handoff는 승인 완료 후에만 생성

## 금지사항
- Sandbox를 중앙 허브처럼 설명하는 것
- 승인 전 결과를 OPS 공식 결과처럼 다루는 것
- 범위 밖 spec를 Sandbox 문서에 다시 넣는 것
- Builder를 분석 엔진처럼 설명하는 것

## 완료 기준(DoD)
- 독립 실행 흐름이 문서로 설명된다.
- handoff 규격이 정의된다.
- 승인 전/후 결과가 분리된다.
- Sandbox 범위 밖 내용이 제거된다.
