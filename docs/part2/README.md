# Part2 Document Hub

작성일: 2026-03-16

## 목적

`docs/part2`는 Part2 문서의 레거시/이력 허브다.  
현재 진행 중인 Part2 활성 문서는 `docs/architecture`를 기준으로 관리한다.

## 현재 활성 문서 (Source of Truth)

- `docs/architecture/12_part2_status_source_of_truth.md`
- KPI 엔진 분리 상세는 현재 `docs/part2/14_Part2_Module_KPI_Engine_Separation_Plan.md`를 기준으로 보되, 신규 업데이트는 `docs/architecture`에 누적한다.
- 역할 고정 기준은 현재 `docs/part2/15_Part2_Module_Role_Definition_Frozen.md`를 참조하고, 신규 업데이트는 `docs/architecture`에 누적한다.

## 이 폴더 문서 상태

- `00_part2_refactor_plan_sales_data_os.md`: 레거시 프롬프트/가이드
- `12_Part2_Execution_Plan.md`: 레거시 실행계획
- `13_Part2_Module_Studio_Planning.md`: 기획안(archive)
- `14_Part2_Module_KPI_Engine_Separation_Plan.md`: 기존 참조본(최신 운영은 architecture 기준)
- `15_Part2_Module_Role_Definition_Frozen.md`: 기존 참조본(최신 운영은 architecture 기준)

## 동기화 규칙

1. 코드 변경 후 먼저 `docs/ai/07_current_phase.md`를 갱신한다.
2. 그 다음 `docs/architecture/12_part2_status_source_of_truth.md`를 갱신한다.
3. `docs/part2/*`는 원칙적으로 새 변경을 반영하지 않고 이력 보존용으로 유지한다.
