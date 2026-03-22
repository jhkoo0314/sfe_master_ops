# Sales Data OS Startup Skill

## 목적

이 스킬의 목적은 새 세션이 시작될 때 Codex가
Sales Data OS 프로젝트의 공식 문서 기준과 현재 작업 범위를 먼저 동기화한 뒤,
잘못된 가정 없이 작업하도록 만드는 것이다.

이 스킬은 구현보다 먼저 실행한다.

---

## 언제 사용하는가

다음 상황에서 이 스킬을 먼저 사용한다.

1. 새 Codex 세션을 시작할 때
2. 오랜만에 프로젝트에 다시 들어왔을 때
3. `AGENTS.md` 또는 `ai/` 문서가 변경된 뒤
4. 큰 작업(리팩토링, 구조 변경, 새 phase 시작) 전에
5. 현재 문맥이 흔들린다고 느껴질 때

---

## 문서 위치

- 루트에는 빠른 진입 문서를 둔다.
- 상세 AI 기준 문서는 `docs/ai/`에 둔다.
- 운영 문서 원본 세트는 `docs/_root/`에 둔다.

---

## 읽기 순서

아래 순서대로 문서를 읽는다.

1. `AGENTS.md`
2. `docs/ai/00_start_here.md`
3. `docs/ai/01_worldview.md`
4. `docs/ai/03_execution_rules.md`
5. `docs/ai/04_module_map.md`
6. `docs/ai/05_crm_rules.md`
7. `docs/ai/06_builder_and_outputs.md`
8. `docs/ai/02_repo_map.md`
9. `docs/architecture/12_part2_status_source_of_truth.md`
10. `docs/ai/07_current_phase.md`
11. `docs/_root/README.md`
12. `docs/_root/RUNBOOK.md`
13. `docs/_root/STRUCTURE.md`
14. `docs/architecture/16_responsibility_based_refactor_structure.md`
15. `ui/console/` 실제 구조는 wrapper가 아니라 현재 구현 기준으로 해석한다.

---

## 해석 원칙

항상 아래 원칙을 유지한다.

1. 시스템 전체 이름은 반드시 `Sales Data OS`로 해석한다.
2. OPS는 시스템 전체가 아니라 `Validation / Orchestration Layer`로만 해석한다.
3. 공식 흐름은 `raw -> adapter -> core engine/module -> result asset -> validation layer(OPS) -> intelligence(RADAR) -> builder` 이다.
4. 공식 모듈 순서는 `CRM -> Prescription -> Sandbox -> Territory -> RADAR -> HTML Builder` 이다.
5. Builder는 계산 엔진이 아니라 최종 표현 모듈이다.
6. 모든 실행/저장 경로는 `company_key` 기준이다.
7. Part2 진행 상태와 우선순위의 단일 기준은 `docs/architecture/12_part2_status_source_of_truth.md`다.
8. `docs/ai/07_current_phase.md`는 실행 안내/요약 문서로만 해석한다.
9. 현재는 Part2 KPI 엔진 분리 진행 단계다.
10. run 저장은 `runs`, `run_steps`, `run_artifacts`, `run_report_context` 기준으로 본다.
11. Agent는 `run_report_context`만이 아니라 `run_artifacts`를 읽는 방향으로 해석한다.
12. 콘솔 구조는 `ui/console/` 패키지 기준으로 본다.
13. 문서는 짧고 명확한 규칙 우선으로 해석한다.
14. 저장소 실제 구조와 다른 이상적 구조를 상상하지 않는다.

---

## 충돌 시 우선순위

문서가 충돌하면 아래 순서를 따른다.

1. 마스터 문서와 루트 문서
2. `AGENTS.md`
3. `docs/ai/` 폴더
4. 구현 코드와 보조 설명

---

## 시작 절차

세션 시작 시 아래 절차를 수행한다.

1. 지정된 문서를 순서대로 읽는다.
2. 현재 프로젝트를 10줄 이내로 요약한다.
3. 핵심 시스템 흐름을 1줄로 요약한다.
4. 지금 해야 할 것과 하지 말아야 할 것을 구분한다.
5. 이번 세션의 금지사항 5개를 정리한다.
6. 불명확한 점이 있으면 목록화한다.
7. 아직 구현은 시작하지 않는다.

---

## 출력 형식

초기 동기화 결과는 아래 형식을 따른다.

## Understanding
- ...

## Core Flow
- ...

## Do Now
- ...

## Do Not Do Now
- ...

## Guardrails
- ...

## Ambiguities
- ...

마지막 줄은 반드시 아래로 끝낸다.

`READY FOR TASK`

---

## 짧은 재동기화 절차

이미 같은 세션 안에서 작업 중이지만 문서가 일부 바뀌었거나 기준을 다시 맞춰야 할 때는
전체 읽기 대신 아래만 다시 확인한다.

1. `AGENTS.md`
2. `docs/ai/00_start_here.md`
3. `docs/architecture/12_part2_status_source_of_truth.md`
4. `docs/ai/07_current_phase.md`

필요 시 관련 문서만 추가로 읽는다.

---

## 금지사항

1. raw를 OPS로 직접 넘기지 않는다.
2. Builder를 계산 엔진처럼 확장하지 않는다.
3. OPS를 시스템 전체 중심 엔진처럼 설명하지 않는다.
4. `company_key` 구조를 무시하고 경로를 하드코딩하지 않는다.
5. KPI를 `modules/kpi/*` 밖에서 중복 계산하지 않는다.

---

## 한 줄 요약

이 스킬은 새 세션에서 Codex가 Sales Data OS 프로젝트의 공식 기준을 먼저 읽고,
같은 세계관과 같은 우선순위로 작업하도록 만드는 시작 절차다.
