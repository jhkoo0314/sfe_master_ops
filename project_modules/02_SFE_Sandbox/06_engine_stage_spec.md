# 06 Engine Stage Spec

## 목적
Sandbox 독립 실행 흐름을 `입력 -> 분석 -> 승인 -> handoff` 기준으로 정의한다.

## Stage 1: Load
- 입력: 시나리오 config, 승인된 입력 자산 경로
- 출력: 입력 자산 세트
- 검증: 파일 존재, 필수 필드 존재, `scenario_id` 존재

## Stage 2: Normalize
- 입력: 입력 자산 세트
- 출력: 분석 표준 DataFrame / JSON
- 검증: 표준 컬럼, 타입, 날짜/월 포맷

## Stage 3: Join Validate
- 입력: 표준 입력
- 출력: 통합 분석용 마스터
- 검증: null/중복/행증가율/orphan rate

## Stage 4: Analyze
- 입력: 통합 분석용 마스터
- 출력: 시나리오별 분석 결과
- 검증: 지표 결측률, 값 범위 sanity check

## Stage 5: Summarize
- 입력: 분석 결과
- 출력: `sandbox_result_asset`, `sandbox_builder_payload`
- 검증: 요약 필드 누락 여부, 품질 상태 결정

## Stage 6: Approve / Export
- 입력: 승인 대상 시나리오
- 출력: `sandbox_ops_handoff.json`
- 검증: 승인 메타 존재, 버전 생성, handoff 준비 완료

## 로그 포맷 최소 기준
- `run_id`
- `scenario_id`
- `stage`
- `status`
- `elapsed_ms`
- `quality_status`
- `approval_status`
- `error_code`
- `error_message`
