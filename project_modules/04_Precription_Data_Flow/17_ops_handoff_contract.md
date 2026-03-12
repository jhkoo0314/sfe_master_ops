# Prescription OPS Handoff Contract

## 목적
Prescription 독립 실행 결과를 OPS에 넘길 때 필요한 최소 파일과 검증 기준을 정의한다.

## OPS에 넘기는 최소 파일
- `prescription_result_asset.json`
- `prescription_builder_payload.json`
- `prescription_ops_handoff.json`

## handoff 필수 조건
- `approval_status=approved`
- `approved_version` 존재
- `approved_by`, `approved_at` 존재
- `quality_status` 존재
- `handoff_ready=true`
- `input_manifest`와 `rule_version` 존재

## OPS가 해야 하는 일
- 파일 규격 검증
- 승인 메타 검증
- 품질 상태 확인
- Builder 전달 가능 여부 판단

## OPS가 하지 않는 일
- Prescription 추적 로직 재계산
- 쉐어 정산 재실행
- 승인 전 상세 테이블 재검토

## rejection 조건
- 승인 메타 누락
- 필수 파일 누락
- `quality_status=FAIL`
- 버전 또는 schema 불일치

## 한 줄 원칙
`Prescription은 밖에서 계산하고, OPS는 승인된 결과만 읽는다.`
