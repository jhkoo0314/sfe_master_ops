# AGENTS.md (Territory Independent Build)

## 목적
이 파일은 Territory Optimizer를 독립 실행형 시나리오 분석 모듈로 문서화하고 구현할 때 따라야 할 작업 규칙을 정의한다.

## 우선 참조 순서
1. `01_map_prd.md`
2. `02_map_data_contract.md`
3. `05_map_scenario_spec.md`
4. `06_map_engine_stage_spec.md`
5. `03_map_join_grain_policy.md`
6. `04_map_payload_schema.md`
7. `11_ops_handoff_contract.md`
8. `07_map_quality_checklist.md`
9. `08_map_runbook_release.md`
10. `09_map_security_governance.md`
11. `10_map_test_plan.md`

## 핵심 원칙
- Territory는 OPS 안에서 반복 실험하지 않는다.
- Territory는 독립 실행 환경에서 시나리오를 비교하고 승인된 결과만 OPS에 넘긴다.
- 지도 미리보기는 보조 결과물이지 Territory 본체가 아니다.
- 승인 전 결과와 승인 완료 결과를 절대 같은 파일로 취급하지 않는다.

## 구현 규칙
- 엔진 단계는 `M1~M6`를 유지한다.
- 시나리오 ID와 승인 버전이 모든 핵심 산출물에 들어가야 한다.
- 품질 임계치는 config 또는 시나리오 YAML에서 관리한다.
- `territory_result_asset.json`이 공식 결과 기준이다.
- `territory_builder_payload.json`은 표현용이며 OPS 판단 기준을 대신하지 않는다.

## handoff 규칙
- OPS에 넘길 때는 `11_ops_handoff_contract.md`를 따른다.
- handoff 패키지는 승인 완료 상태에서만 생성한다.
- OPS는 Territory 시나리오를 다시 계산하지 않고, 승인 패키지 검증만 수행한다.

## 금지사항
- 승인 전 시나리오를 OPS 공식 결과처럼 취급하는 것
- OPS 폴더를 Territory 실험 공간처럼 사용하는 것
- 지도 HTML만 보고 Territory 완료로 판단하는 것
- 이름 기반 조인을 핵심 기준으로 쓰는 것

## 완료 기준(DoD)
- 동일 입력 + 동일 시나리오 설정이면 결과가 재현된다.
- 승인 패키지 3종이 생성된다.
- OPS가 읽을 수 있는 handoff manifest가 존재한다.
- 문서 `01~11` 사이에 역할 충돌이 없다.
