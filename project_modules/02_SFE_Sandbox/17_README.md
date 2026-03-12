# Sandbox Independent Build Docs

이 폴더는 Sandbox를 독립 실행형 분석 엔진으로 다시 세우기 위한 문서 묶음입니다.

핵심 생각은 간단합니다.

- Sandbox는 OPS 허브가 아닙니다.
- Sandbox는 분석 엔진입니다.
- 승인된 결과만 OPS에 넘깁니다.

## 문서 구성
- `01_architecture.md`: 독립 실행형 Sandbox 구조
- `02_data_contract.md`: 입력/출력/승인 패키지 계약
- `03_mapping_policy.md`: 컬럼 매핑 정책
- `04_join_grain_policy.md`: 조인/그레인 기준
- `05_scenario_spec_template.md`: 시나리오 YAML 기준
- `06_engine_stage_spec.md`: 실행 단계 명세
- `07_runbook_ops.md`: 독립 실행 runbook
- `08_quality_checklist.md`: 품질 체크리스트
- `09_release_change_log.md`: 변경 이력 관리
- `10_security_governance.md`: 보안/승인/감사 기준
- `11_tech_stack.md`: 기술 스택 표준
- `12_rebuild_improvement_comparison.md`: As-Is vs To-Be 재평가
- `14_PRD.md`: Sandbox 독립 빌드 PRD
- `15_workflow.md`: 독립 실행 워크플로우
- `16_AGENTS.md`: 작업 규칙
- `18_ops_handoff_contract.md`: OPS 전달 규격
- `19_boundary_policy.md`: Sandbox / OPS / Builder 경계

## 추천 읽기 순서
1. `14` + `01`
2. `15`
3. `02` + `04` + `05` + `06`
4. `18` + `19`
5. `07` + `08` + `10`
6. `12` + `16`

## 한 줄 실행 흐름
`approved inputs -> sandbox scenario -> quality gate -> sandbox_result_asset -> approve -> OPS handoff`

## 필수 원칙
- Sandbox는 독립 실행형이다.
- OPS는 승인된 결과만 읽는다.
- Builder는 표현 계층이다.
- Sandbox 범위 밖 내용은 이 문서 묶음에 남기지 않는다.
