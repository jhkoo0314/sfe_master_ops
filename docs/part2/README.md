# Part2 Legacy Archive

작성일: 2026-03-16

## 목적

`docs/part2`는 Part2 문서의 레거시/이력 보관 폴더다.  
현재 활성 기준 문서는 `docs/architecture`를 기준으로 관리한다.

중요:

- 이 폴더는 이제 새 기준 문서를 추가하는 위치가 아니다.
- Part2 완료 상태와 최종 선언은 `docs/architecture` 문서를 본다.
- 앞으로 Part3 이상은 `docs/part3` 같은 새 폴더를 만들지 않고 `docs/workstreams/` 아래에 누적한다.

## 현재 활성 문서 (Source of Truth)

- `docs/architecture/12_part2_status_source_of_truth.md`
- `docs/architecture/23_part2_completion_declaration.md`
- KPI 엔진 분리 상세는 현재 `docs/part2/14_Part2_Module_KPI_Engine_Separation_Plan.md`를 기준으로 보되, 신규 업데이트는 `docs/architecture`에 누적한다.
- 역할 고정 기준은 현재 `docs/part2/15_Part2_Module_Role_Definition_Frozen.md`를 참조하고, 신규 업데이트는 `docs/architecture`에 누적한다.

## 이 폴더 문서 상태

- `00_part2_refactor_plan_sales_data_os.md`: 레거시 프롬프트/가이드
- `12_Part2_Execution_Plan.md`: 레거시 실행계획
- `13_Part2_Module_Studio_Planning.md`: 기획안(archive)
- `14_Part2_Module_KPI_Engine_Separation_Plan.md`: 기존 참조본(최신 운영은 architecture 기준)
- `15_Part2_Module_Role_Definition_Frozen.md`: 기존 참조본(최신 운영은 architecture 기준)

## 동기화 규칙

1. Part2 진행 상태는 `docs/architecture/12_part2_status_source_of_truth.md`만 갱신한다.
2. `docs/ai/07_current_phase.md`는 실행 안내/요약만 유지한다.
3. `docs/part2/*`는 원칙적으로 새 변경을 반영하지 않고 이력 보존용으로 유지한다.
4. 앞으로의 새 단계 작업 문서는 `docs/workstreams/`를 사용한다.
