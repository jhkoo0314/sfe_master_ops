# Sandbox OPS Handoff Contract

## 목적
Sandbox 독립 실행 결과를 OPS에 넘길 때 필요한 최소 파일과 검증 기준을 정의한다.

## OPS에 넘기는 최소 파일
- `sandbox_result_asset.json`
- `sandbox_builder_payload.json`
- `sandbox_ops_handoff.json`

## handoff 필수 조건
- `approval_status=approved`
- `approved_version` 존재
- `approved_by`, `approved_at` 존재
- `quality_status` 존재
- `handoff_ready=true`

## OPS가 해야 하는 일
- 파일 규격 검증
- 승인 메타 검증
- 품질 상태 확인
- 다음 연결 판단

## OPS가 하지 않는 일
- Sandbox 시나리오 재계산
- 승인 전 시나리오 비교
- 입력 자산 재가공

## rejection 조건
- 승인 메타 누락
- 필수 파일 누락
- `quality_status=FAIL`
- 버전 또는 schema 불일치

## 한 줄 원칙
`Sandbox는 밖에서 분석하고, OPS는 승인된 결과만 읽는다.`
