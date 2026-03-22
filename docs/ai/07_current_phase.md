# Current Phase

## 현재 단계 정의

현재 단계는 `Part2 KPI 엔진 분리 진행` 단계다.  
이 문서는 실행 안내/요약 전용이다.

Part1 기준 구조 고정과 CRM KPI 거버넌스 복구(Phase 1~6)는 완료 상태로 본다.

## 단일 기준 고정

- Part2 진행 상태(Completed / In Progress / Next)의 단일 기준은 `docs/architecture/12_part2_status_source_of_truth.md`다.
- 우선순위가 충돌하면 이 문서가 아니라 위 단일 기준 문서를 따른다.
- 이 문서는 단일 기준 문서를 요약 안내하는 용도로만 유지한다.

## 현재 상태 요약

- CRM 공식 KPI 계산: `modules/kpi/crm_engine.py`
- Sandbox KPI 분리 1차: `modules/kpi/sandbox_engine.py`
- Territory KPI 분리 1차: `modules/kpi/territory_engine.py`
- Prescription KPI 분리 1차: `modules/kpi/prescription_engine.py`
- Builder는 KPI 재계산 없이 payload 주입만 수행
- Sandbox는 CRM KPI 재계산 없이 입력 KPI 사용
- Territory builder payload는 KPI 계산 없이 조립/분할만 수행
- Prescription builder payload는 KPI 계산 없이 조립/분할만 수행
- `hangyeol_pharma`, `daon_pharma` 회귀 검증 통과
- `monthly_merge_pharma` 6개월 월별 raw 생성/병합 검증 통과
- `hangyeol_pharma`, `daon_pharma` 기준 최종 HTML 6종 생성 검증 통과
- `monthly_merge_pharma`는 6개월 월별 raw 생성/병합과 실행모드별 점검 완료
- Sandbox 최종 HTML 지점/담당자 필터 복구 완료
  - `report_template`에 지점 chunk 로더 반영
  - `branch_index` 기반 지점 옵션 + 선택 지점 asset 로딩 방식으로 동작
- Sandbox 기반 실행모드에서 RADAR 단계 자동 실행 반영
  - `scripts/validate_radar_with_ops.py`
  - `data/ops_validation/{company_key}/radar/radar_result_asset.json` 생성
- 운영 콘솔에서 월별 raw 업로드 후 자동 병합 실행 가능
- 분석 인텔리전스 탭에서 판정 해석 문장과 근거 수치 확인 가능
- 다음 구현 우선순위는 테스트용 raw generator 공통화보다 실제 운영용 공통 intake/onboarding engine이다.
- 방향은 `공통엔진 1개 + scenario/mapping/rules 업데이트` 기준으로 고정한다.

## 지금 해야 할 것

- `docs/architecture/12_part2_status_source_of_truth.md`의 현재 `In Progress` 항목을 먼저 수행한다.
- 새 작업을 시작할 때 `Completed / In Progress / Next` 상태를 먼저 확인한다.

## 지금 하지 않을 것

- 단일 기준 문서와 다른 임의 우선순위를 새로 만들지 않는다.
- 상태 변경을 `docs/ai/07_current_phase.md`에 먼저 기록하지 않는다.
- `docs/architecture/12_part2_status_source_of_truth.md` 갱신 없이 진행 상태를 확정하지 않는다.

## Codex 작업 제한

- 세계관을 바꾸지 않는다.
- Builder를 계산 엔진으로 확장하지 않는다.
- Sandbox에서 CRM KPI를 재계산하지 않는다.
- `company_key` 경로 원칙을 무시하지 않는다.

## 결론

Part2 우선순위와 상태는 `docs/architecture/12_part2_status_source_of_truth.md`만 기준으로 본다.

## 문서 기준

- Part2 진행 상태의 단일 기준은 `docs/architecture/12_part2_status_source_of_truth.md`다.
- 이 문서는 실행 안내/요약만 유지하고, 세부 체크리스트는 architecture 문서에만 누적한다.
