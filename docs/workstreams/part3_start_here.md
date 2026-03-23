# Part3 Start Here

작성일: 2026-03-23
상태: `draft`

## 목적

이 문서는 Part3를 시작할 때 가장 먼저 보는 시작 문서다.

Part3의 상세 메모는 `docs/workstreams/*`에 누적하고,  
현재 기준으로 확정된 구조/상태 문서는 필요할 때 `docs/architecture/*`로 승격한다.

## 시작 전 확인

1. Part2 완료 상태를 먼저 확인한다.
   - `docs/architecture/12_part2_status_source_of_truth.md`
   - `docs/architecture/23_part2_completion_declaration.md`

2. Sales Data OS 기준 용어를 유지한다.
   - 시스템 전체 이름: `Sales Data OS`
   - `OPS`는 `Validation / Orchestration Layer`
   - KPI 계산 단일 소스: `modules/kpi/*`
   - Builder는 render-only

3. Part3 목표를 먼저 한 줄로 고정한다.
   - 예: `run 중심 저장 구조 고도화`
   - 예: `report context 기반 Agent 정교화`
   - 예: `Validation Layer 운영 자동화`

## Part3 한 줄 정의

`여기에 Part3의 핵심 목적 한 줄을 적는다.`

## 이번 단계에서 풀 문제

- `문제 1`
- `문제 2`
- `문제 3`

## 이번 단계에서 하지 않을 것

- `범위 밖 항목 1`
- `범위 밖 항목 2`

## 성공 기준

- [ ] 실제 사용자 흐름 기준으로 설명 가능
- [ ] 코드 책임이 Sales Data OS 레이어 원칙과 충돌하지 않음
- [ ] KPI 단일 소스 원칙을 깨지 않음
- [ ] Builder render-only 원칙을 깨지 않음
- [ ] 완료 후 architecture 문서로 올릴 수 있을 정도로 정리됨

## 연결 문서

- 작업 메모: `docs/workstreams/part3_execution_notes.md`
- 오픈 이슈: `docs/workstreams/part3_open_items.md`

## 다음 행동

- Part3 목표 한 줄 확정
- 우선순위 3개 선정
- 첫 실행 단위 정의
