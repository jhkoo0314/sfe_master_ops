# Territory Optimizer Independent Build Docs

이 폴더는 Territory를 OPS 내부 부속 기능이 아니라, 독립 실행형 권역 분석 모듈로 다시 세우기 위한 문서 묶음입니다.

핵심 생각은 간단합니다.

- Territory 실험은 밖에서 한다.
- 승인된 결과만 OPS에 넘긴다.
- 지도는 결과를 보여주는 수단이지 본체가 아니다.

## 문서 구성
- `01_map_prd.md`: 독립 실행형 Territory 제품 정의
- `02_map_data_contract.md`: 입력/출력/승인 패키지 데이터 계약
- `03_map_join_grain_policy.md`: 시나리오 기준 grain/조인 정책
- `04_map_payload_schema.md`: result asset / builder payload / handoff 스키마
- `05_map_scenario_spec.md`: Territory 시나리오 YAML 기준
- `06_map_engine_stage_spec.md`: 독립 실행 단계 `M1~M6`
- `07_map_quality_checklist.md`: 실험/승인 품질 체크리스트
- `08_map_runbook_release.md`: 독립 실행/승인/OPS 전달 절차
- `09_map_security_governance.md`: 권한/감사/보안 기준
- `10_map_test_plan.md`: 재현성/승인 패키지/OPS handoff 테스트
- `11_ops_handoff_contract.md`: OPS에 넘기는 공식 패키지 규격
- `12_AGENTS.md`: 작업 규칙

## 추천 읽기 순서
1. `01` + `02`
2. `05` + `06`
3. `03` + `04`
4. `11`
5. `07` + `08` + `09` + `10`
6. `12`

## 한 줄 운영 흐름
`sandbox_result_asset + territory reference -> scenario run -> compare -> approve -> territory_result_asset -> OPS handoff`

## 필수 원칙
- Territory는 독립 실행형이다.
- OPS는 승인된 결과만 읽는다.
- 승인 전 결과는 OPS 공식 결과가 아니다.
- `territory_result_asset.json`이 공식 판단 기준이다.
- `territory_map_preview.html`은 설명용 결과물이다.
