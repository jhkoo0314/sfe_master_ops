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

## 문서 위치

- `docs/_root/`: 루트 운영 문서 원본 세트
  - `AGENTS.md`
  - `SKILL.md`
  - `README.md`
  - `RUNBOOK.md`
  - `STRUCTURE.md`
- `docs/ai/`: Codex 작업용 축약 문서 세트
- `docs/architecture/`: Sales Data OS 아키텍처 감사/목표/리팩토링 계획
- `docs/runbook/`: Sales Data OS 기준 운영 런북

## 문서 동기화 기준

- 운영 기준 문서(항상 최신 유지)
  - `docs/README.md`
  - `docs/_root/README.md`
  - `docs/_root/RUNBOOK.md`
  - `docs/_root/STRUCTURE.md`
  - `docs/ai/*`
  - `docs/runbook/*`
- 아카이브 성격 문서(이력 보존 우선)
  - `docs/part1/*`
  - `docs/part2/*`

## 권장 읽기 순서

1. `docs/_root/AGENTS.md`
2. `docs/ai/00_start_here.md`
3. `docs/ai/01_worldview.md`
4. `docs/ai/03_execution_rules.md`
5. `docs/ai/04_module_map.md`
6. `docs/ai/05_crm_rules.md`
7. `docs/ai/06_builder_and_outputs.md`
8. `docs/ai/02_repo_map.md`
9. `docs/ai/07_current_phase.md`
10. `docs/_root/README.md`
11. `docs/_root/RUNBOOK.md`
12. `docs/_root/STRUCTURE.md`
