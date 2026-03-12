# Territory Independent Build Engine Stage Spec

## 목적
Territory 독립 실행 흐름을 `실험 -> 비교 -> 승인 -> handoff` 기준으로 단계화한다.

## M1 Load
- 입력: 시나리오 YAML, sandbox asset, territory reference, route activity
- 출력: 원천 입력 세트
- 검증: 파일 존재, 필수 컬럼 존재, 시나리오 ID 존재

## M2 Normalize
- 입력: 원천 입력 세트
- 출력: 표준화된 병원/담당자/권역/활동 데이터
- 검증: ID 정합성, 월 포맷, 권역 참조 연결

## M3 Scenario Build
- 입력: 표준화 데이터 + 제약조건
- 출력: 시나리오별 배정 후보
- 검증: 중복 배정, 미배정 병원, 잠금 병원 위반 여부

## M4 Coverage And Optimization
- 입력: 시나리오 배정 후보
- 출력: 커버리지/과부하/공백/배치 효율 요약
- 검증: coverage rate, overload, uncovered hospital 비율

## M5 Preview And Compare
- 입력: 시나리오 결과
- 출력: `territory_result_asset`, `territory_builder_payload`, 지도 미리보기
- 검증: payload 필수 필드, 시나리오별 비교 가능 여부

## M6 Approval And Handoff Export
- 입력: 승인 대상 시나리오
- 출력: `territory_ops_handoff.json`
- 검증: 승인 메타 존재, quality gate 통과, 버전 생성 성공

## 오류 코드 예시
- `TERR_LOAD_FAIL`
- `TERR_SCHEMA_FAIL`
- `TERR_SCENARIO_BUILD_FAIL`
- `TERR_QUALITY_FAIL`
- `TERR_HANDOFF_FAIL`

## 로그 필드 최소 기준
- `run_id`
- `scenario_id`
- `stage`
- `status`
- `elapsed_ms`
- `quality_status`
- `approval_status`
- `error_code`
- `error_message`
