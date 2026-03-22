# Documentation Hub

이 폴더는 Sales Data OS 문서 허브다.

## 용어 기준

- 시스템 전체 명칭: `Sales Data OS`
- `OPS`는 `Validation / Orchestration Layer` 의미로만 사용
- KPI 계산 단일 소스: `modules/kpi/*`
- Builder는 render-only 레이어이며 KPI를 재계산하지 않음

## 현재 구현 상태 (2026-03 기준)

- UI 메인 콘솔은 `Sales Data OS` 6개 레이어 흐름으로 표시됨
  - Data → Adapter → Core Engine(KPI) → Validation Layer(OPS) → Intelligence(RADAR 포함) → Presentation(Builder)
- 파이프라인 실행 시 KPI 계산은 각 모듈 엔진에서 처리됨
  - CRM KPI: `modules/kpi/crm_engine.py`
  - Sandbox KPI: `modules/kpi/sandbox_engine.py`
- Sandbox 기반 실행 모드에서는 RADAR가 파이프라인 단계에 포함됨
  - 실행 후 `data/ops_validation/{company}/radar/`에 결과 생성
  - `radar_input_standard.json`
  - `radar_result_asset.json`
  - `radar_validation_summary.json`
- Builder 단계는 RADAR 결과를 포함한 HTML 결과를 렌더링함
  - `radar_report_preview.html` (자산이 준비된 경우)
- 회사 코드/회사 이름 입력 기본값은 빈값으로 시작하도록 UI 반영됨
- 다음 핵심 구현 우선순위는 실제 회사 raw를 받는 공통 intake/onboarding engine이다.
- 테스트용 raw generator 문서는 보조 설계로 두고, 실제 운영 기준은 `18`, `19`, `20` 문서를 먼저 본다.

## 문서 위치

- 루트 문서: 전역 문서이자 운영 문서 원본 세트
  - `AGENTS.md`
  - `SKILL.md`
  - `README.md`
  - `RUNBOOK.md`
  - `STRUCTURE.md`
- `docs/ai/`: Codex 작업용 축약 문서 세트
- `docs/architecture/`: Sales Data OS 아키텍처 감사/목표/리팩토링 계획
  - `docs/architecture/12_part2_status_source_of_truth.md` (Part2 진행 상태 단일 기준)
  - `docs/architecture/18_real_company_raw_input_flow.md` (실제 회사 raw 입력 운영 흐름 기준)
  - `docs/architecture/19_intake_gate_and_onboarding_plan.md` (실제 회사 raw intake/onboarding 운영 설계)
  - `docs/architecture/20_common_intake_engine_implementation_plan.md` (공통 intake engine 구현 계획)
  - `docs/architecture/09_sales_data_os_agent_run_architecture.md`
  - `docs/architecture/10_agent_tab_mvp.md`
  - `docs/architecture/11_run_based_storage.md`
  - `docs/architecture/04_sandbox_block_contract.md`
  - `docs/architecture/05_sandbox_template_slots.md`
  - `docs/architecture/06_sandbox_refactor_summary.md`
- `docs/part2/`: 레거시/이력 허브 (활성 기준 문서는 `docs/architecture` 사용)
  - `docs/part2/README.md`
- `docs/runbook/`: Sales Data OS 기준 운영 런북

## 문서 동기화 기준

- 운영 기준 문서(항상 최신 유지)
  - `docs/README.md`
  - 루트 `README.md`
  - 루트 `RUNBOOK.md`
  - 루트 `STRUCTURE.md`
  - `docs/ai/*` (요약/안내 문서)
  - `docs/runbook/*`
- 아카이브 성격 문서(이력 보존 우선)
  - `docs/part1/*`
  - `docs/part2/*`

정리:

- 루트 = 전역 원본
- 수정은 항상 루트 문서에서 먼저 한다

## 2026-03-16 Sandbox 동기화 요약

- Stage 4 기준으로 Sandbox는 block renderer 안정화 상태
- `template_payload` 유지 + `block_payload` 병행 구조
- resolver 기반 슬롯 렌더, branch cache, fallback 관측값(counter) 반영
- 회귀 테스트:
  - `tests/test_sandbox/test_sandbox_block_resolver_regression.py`
  - `tests/test_sandbox/test_sandbox_renderer_snapshot.py`

## 권장 읽기 순서

1. `AGENTS.md`
2. `docs/ai/00_start_here.md`
3. `docs/ai/01_worldview.md`
4. `docs/ai/03_execution_rules.md`
5. `docs/ai/04_module_map.md`
6. `docs/ai/05_crm_rules.md`
7. `docs/ai/06_builder_and_outputs.md`
8. `docs/ai/02_repo_map.md`
9. `docs/ai/07_current_phase.md`
10. `README.md`
11. `RUNBOOK.md`
12. `STRUCTURE.md`

