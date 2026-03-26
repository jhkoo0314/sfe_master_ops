# Sales Data OS 프로젝트 폴더 구조 인덱스

비개발자도 빠르게 이해할 수 있도록, 프로젝트 폴더를 역할 중심으로 정리한 문서입니다.

## 1) 이 문서의 목적
- 전체 폴더에서 `어디에 무엇이 있는지` 빠르게 찾기
- 시스템 책임(데이터/계산/검증/분석/표현) 구분해서 이해하기
- 작업할 때 기준 문서를 먼저 찾을 수 있게 돕기

## 2) 핵심 원칙
- 시스템 전체 이름은 `Sales Data OS`
- `OPS`는 전체 시스템이 아니라 `Validation / Orchestration Layer`
- KPI 계산 단일 소스는 `modules/kpi/*`
- Builder는 `render-only` (KPI 재계산 금지)

## 3) 루트(최상위) 폴더 한눈에 보기
```text
C:\sfe_master_ops
├─ AGENTS.md
├─ README.md
├─ RUNBOOK.md
├─ STRUCTURE.md
├─ SKILL.md
├─ pyproject.toml
├─ uv.lock
├─ adapters/
├─ common/
├─ data/
├─ docs/
├─ migrations/
├─ modules/
├─ ops_core/
├─ result_assets/
├─ scripts/
├─ templates/
├─ tests/
└─ ui/
```

## 4) 폴더별 상세 설명

### `adapters/` (원천(raw) -> 표준 스키마 변환)
- `adapters/crm/`
  - `adapter_config.py`
  - `company_master_adapter.py`
  - `crm_activity_adapter.py`
  - `hospital_adapter.py`
- `adapters/prescription/`
  - `adapter_config.py`
  - `company_prescription_adapter.py`
- `adapters/sandbox/`
  - `adapter_config.py`
  - `domain_adapter.py`
- `adapters/territory/`
  - `adapter_config.py`
  - `crm_route_adapter.py`
- `adapters/public_data_configs.py`

### `common/` (공통 설정/타입/런 저장 유틸)
- 주요 파일
  - `asset_versions.py`
  - `company_onboarding_registry.py`
  - `company_profile.py`
  - `company_registry.py`
  - `company_runtime.py`
  - `config.py`
  - `exceptions.py`
  - `run_registry.py`
  - `supabase_client.py`
  - `types.py`
- `common/run_storage/`
  - `_shared.py`
  - `artifacts.py`
  - `chat_logs.py`
  - `report_context.py`
  - `runs.py`
- `common/runtime_helpers/`
  - `import_cache.py`

### `data/` (회사별 입력/표준화/검증 데이터)
- `data/company_source/`: 회사별 원천(raw) 입력
- `data/ops_standard/`: 표준화 결과
- `data/ops_validation/`: 검증 결과
- `data/public/`: 외부 공공데이터
- `data/sample_data/`: 샘플 데이터
- `data/system/`: 시스템 레지스트리/로그
- `data/README.md`: 데이터 폴더 가이드

### `docs/` (문서 모음)
- `docs/README.md`
- `docs/SALES_DATA_OS_DETAIL.md`
- `docs/index.md` (현재 문서)
- `docs/ai/`
  - `00_start_here.md`
  - `01_worldview.md`
  - `02_repo_map.md`
  - `03_execution_rules.md`
  - `04_module_map.md`
  - `05_crm_rules.md`
  - `06_builder_and_outputs.md`
  - `07_current_phase.md`
- `docs/architecture/`
  - `01_current_state_audit.md`
  - `02_refactor_plan_sales_data_os.md`
  - `03_radar_module_design.md`
  - `04_sandbox_block_contract.md`
  - `05_sandbox_template_slots.md`
  - `06_sandbox_refactor_summary.md`
  - `07_sales_data_os_architecture.md`
  - `08_sales_data_os_diagram.md`
  - `09_sales_data_os_agent_run_architecture.md`
  - `10_agent_tab_mvp.md`
  - `11_run_based_storage.md`
  - `12_part2_status_source_of_truth.md`
  - `13_agent_tab_implementation_plan.md`
  - `14_company_registry_and_fixed_key_plan.md`
  - `15_company_selection_ui_plan.md`
  - `16_responsibility_based_refactor_structure.md`
  - `17_raw_generator_refactor_plan.md`
  - `18_real_company_raw_input_flow.md`
  - `19_intake_gate_and_onboarding_plan.md`
  - `20_common_intake_engine_implementation_plan.md`
  - `21_ops_core_refactor_plan.md`
  - `22_ops_core_location_migration_review.md`
  - `23_part2_completion_declaration.md`
- `docs/part1/`: Part1 관련 문서 묶음
- `docs/part2/`: Part2 관련 문서 묶음
- `docs/runbook/sales_data_os_runbook.md`
- `docs/workstreams/`
  - `README.md`
  - `part3_start_here.md`
  - `part3_open_items.md`
  - `part3_execution_notes.md`

### `migrations/` (DB 스키마 변경 SQL)
- `001_initial_schema.sql`
- `002_run_based_schema.sql`
- `003_company_registry_schema.sql`

### `modules/` (핵심 비즈니스 모듈)
- `modules/kpi/` (KPI 계산 단일 소스)
  - `crm_engine.py`
  - `prescription_engine.py`
  - `sandbox_engine.py`
  - `territory_engine.py`
- `modules/crm/`
  - `builder_payload.py`
  - `schemas.py`
  - `service.py`
- `modules/prescription/`
  - `builder_payload.py`
  - `flow_builder.py`
  - `id_rules.py`
  - `schemas.py`
  - `service.py`
- `modules/sandbox/`
  - `block_registry.py`
  - `block_resolver.py`
  - `builder_payload.py`
  - `schemas.py`
  - `service.py`
  - `templates.py`
  - `builders/block_payload_builder.py`
  - `builders/template_payload_builder.py`
- `modules/territory/`
  - `builder_payload.py`
  - `schemas.py`
  - `service.py`
  - `templates.py`
- `modules/radar/`
  - `README.md`
  - `builder_payload.py`
  - `option_engine.py`
  - `priority_engine.py`
  - `schemas.py`
  - `service.py`
  - `signal_engine.py`
- `modules/intake/`
  - `fixers.py`
  - `merge.py`
  - `models.py`
  - `rules.py`
  - `runtime.py`
  - `scenarios.py`
  - `service.py`
  - `staging.py`
  - `suggestions.py`
- `modules/builder/`
  - `schemas.py`
  - `service.py`
- `modules/validation/`
  - `main.py`
  - `api/`
    - `crm_router.py`
    - `pipeline_router.py`
    - `prescription_router.py`
    - `sandbox_router.py`
    - `territory_router.py`
  - `workflow/`
    - `execution_models.py`
    - `execution_registry.py`
    - `execution_runtime.py`
    - `execution_service.py`
    - `monthly_source_merge.py`
    - `orchestrator.py`
    - `schemas.py`

### `ops_core/` (Validation / Orchestration API + 워크플로)
- `ops_core/main.py`
- `ops_core/api/`
  - `crm_router.py`
  - `pipeline_router.py`
  - `prescription_router.py`
  - `sandbox_router.py`
  - `territory_router.py`
- `ops_core/workflow/`
  - `execution_models.py`
  - `execution_registry.py`
  - `execution_runtime.py`
  - `execution_service.py`
  - `monthly_source_merge.py`
  - `orchestrator.py`
  - `schemas.py`

### `result_assets/` (다음 단계 전달용 표준 산출물)
- `crm_result_asset.py`
- `prescription_result_asset.py`
- `sandbox_result_asset.py`
- `territory_result_asset.py`
- `radar_result_asset.py`

### `scripts/` (실행 스크립트)
- 데이터 생성/정규화
  - `generate_source_raw.py`
  - `normalize_crm_source.py`
  - `normalize_prescription_source.py`
  - `normalize_sandbox_source.py`
  - `normalize_territory_source.py`
  - `migrate_company_source_filenames.py`
- 템플릿 렌더
  - `render_sandbox_template.py`
  - `render_territory_template.py`
- 검증 실행
  - `validate_crm_with_ops.py`
  - `validate_prescription_with_ops.py`
  - `validate_sandbox_with_ops.py`
  - `validate_territory_with_ops.py`
  - `validate_radar_with_ops.py`
  - `validate_builder_with_ops.py`
  - `validate_full_pipeline.py`
- `scripts/raw_generators/`
  - `configs.py`
  - `engine.py`
  - `writers.py`
  - `templates/daon_like.py`
  - `templates/daon_like_helpers.py`
  - `templates/hangyeol_like.py`
  - `templates/hangyeol_like_helpers.py`

### `templates/` (Builder HTML 템플릿)
- `crm_analysis_template.html`
- `prescription_flow_template.html`
- `radar_report_template.html`
- `report_template.html`
- `territory_optimizer_template.html`
- `total_valid_templates.html`
- `templates/vendor/leaflet/` (지도 렌더용 정적 리소스)

### `tests/` (자동 테스트)
- 공통
  - `performance_regression_utils.py`
- `tests/fixtures/`
  - `crm_fixtures.py`
  - `prescription_fixtures.py`
  - `sandbox_fixtures.py`
  - `territory_fixtures.py`
- `tests/test_builder/`
  - `test_version_contracts.py`
- `tests/test_common/`
  - `test_company_profile.py`
  - `test_company_registry.py`
  - `test_run_registry.py`
- `tests/test_crm/`
  - `test_crm_builder_payload_chunks.py`
  - `test_crm_flow.py`
  - `test_crm_performance_regression.py`
- `tests/test_intake/`
  - `test_intake_auto_mapping.py`
  - `test_intake_period_alignment.py`
  - `test_intake_relaxed_gate.py`
  - `test_intake_suggestions.py`
- `tests/test_prescription/`
  - `test_prescription_builder_payload_chunks.py`
  - `test_prescription_flow.py`
  - `test_prescription_performance_regression.py`
- `tests/test_radar/`
  - `test_radar_builder_payload.py`
  - `test_radar_flow.py`
- `tests/test_sandbox/`
  - `test_sandbox_block_resolver_regression.py`
  - `test_sandbox_flow.py`
  - `test_sandbox_performance_regression.py`
  - `test_sandbox_renderer_snapshot.py`
  - `test_sandbox_template_payload_chunks.py`
- `tests/test_scripts/`
  - `test_generate_source_raw.py`
  - `test_migrate_company_source_filenames.py`
  - `test_raw_generator_configs.py`
  - `test_raw_generator_engine.py`
  - `test_raw_generator_writers.py`
  - `test_validate_full_pipeline.py`
- `tests/test_territory/`
  - `test_territory_adapter_payload.py`
  - `test_territory_flow.py`
  - `test_territory_performance_regression.py`
- `tests/test_ui/`
  - `test_agent_console_helpers.py`
  - `test_console_execution_modes.py`
  - `test_console_paths.py`
- `tests/test_workflow/`
  - `test_execution_service.py`
  - `test_validation_bridge.py`

### `ui/` (콘솔 화면)
- `ui/ops_console.py`
- `ui/console/`
  - 화면/동작 핵심 파일
    - `analysis_explainer.py`
    - `app.py`
    - `artifacts.py`
    - `display.py`
    - `paths.py`
    - `runner.py`
    - `shared.py`
    - `sidebar.py`
    - `state.py`
  - `ui/console/agent/`
    - `artifacts.py`
    - `context.py`
    - `history.py`
    - `llm.py`
    - `mock.py`
    - `runs.py`
    - `service.py`
  - `ui/console/tabs/`
    - `agent_tab.py`
    - `artifacts_tab.py`
    - `builder_helpers.py`
    - `builder_tab.py`
    - `dashboard_tab.py`
    - `pipeline_tab.py`
    - `upload_tab.py`

## 5) 공식 흐름 요약 (1줄)
`raw -> adapter -> core engine/module -> result asset -> validation layer(OPS) -> intelligence(RADAR) -> builder`

## 6) 참고
- 이 문서는 실무용 빠른 인덱스입니다.
- 임시 폴더(`.tmp`), 가상환경(`.venv`), 캐시(`__pycache__`)는 의도적으로 제외했습니다.
- 실제 수정 전에는 `AGENTS.md`와 `docs/ai/*`를 먼저 확인하세요.
