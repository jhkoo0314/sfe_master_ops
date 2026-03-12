# Territory OPS Handoff Contract

## 목적
Territory 독립 실행 결과를 OPS에 넘길 때 필요한 최소 패키지와 검증 기준을 정의한다.

## OPS에 넘기는 최소 파일
- `territory_result_asset.json`
- `territory_builder_payload.json`
- `territory_ops_handoff.json`

## handoff 필수 조건
- `approval_status=approved`
- `quality_status` 존재
- `approved_version` 존재
- `approved_by`, `approved_at` 존재
- 재실행 가능한 `scenario_id`와 입력 참조 정보 존재

## OPS가 해야 하는 일
- 파일 규격 검증
- 버전 확인
- 품질 상태 확인
- Builder 전달 가능 여부 판단

## OPS가 하지 않는 일
- Territory 시나리오 재계산
- 권역안 비교 실험
- 담당자/병원 재배치 탐색

## rejection 조건
- 승인 메타 누락
- 필수 파일 누락
- `quality_status=FAIL`
- 버전 또는 schema 불일치

## 한 줄 원칙
`Territory는 밖에서 실험하고, OPS는 승인된 결과만 읽는다.`
