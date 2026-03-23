# Sales Data OS

원천데이터를 넣으면 `정규화 -> 모듈 분석/KPI 계산 -> Validation Layer(OPS) 검증 게이트 -> Intelligence -> Builder HTML 생성`까지 이어지는 Sales Data OS 운영 검증 프로젝트입니다.

현재 공식 기준의 핵심은 이것입니다.

- 회사별 raw를 같은 틀로 흡수하고 어디까지 연결되는지 검증
- CRM, Prescription, Sandbox, Territory, RADAR, Builder를 실제로 실행 가능
- 회사 코드별로 결과 폴더를 분리
- run 기준 저장(`runs`, `run_steps`, `run_artifacts`, `run_report_context`)이 로컬/DB에 연결됨
- Agent 탭은 `run_report_context`와 `run_artifacts`를 실제로 읽는 구조로 동작
- CRM Builder preview는 생성 전에 `crm_builder_payload.json`을 최신 결과자산 기준으로 다시 써서 필터/범위가 stale 되지 않게 동작
- RADAR `Layer 03 : Decision Options`는 현재 판단 규칙 확정 전이라 임시 고정 문구로 운영 중
- 운영 콘솔은 월별 raw 업로드 후 자동 병합 실행을 지원
- 패키지 업로드는 파일 업로드 직후가 아니라 `패키지 업로드 저장` 시점에 intake 검증을 시작
- 분석 인텔리전스 탭은 점수뿐 아니라 판정 해석과 근거 수치까지 표시
- 코드 기준으로 HTML 보고서 6종과 통합 허브까지 생성 가능
- 실제 저장된 보고서 수는 회사별 마지막 실행 상태에 따라 다를 수 있음

## 현재 단계

2026-03-23 기준으로 현재 단계는 `Part2 완료`입니다.

이 말의 뜻은 문서만 정리된 상태가 아니라, 실제 운영 흐름 검증까지 끝났다는 뜻입니다.

- KPI 계산 단일 소스가 `modules/kpi/*`로 분리되어 유지됩니다.
- 월별 raw 업로드 -> 자동 병합 -> intake -> staging -> 파이프라인 -> Builder 흐름이 실제로 검증됐습니다.
- `company_000001` 기준으로 월별 raw 운영 흐름 실사용 검증이 끝났습니다.
- `company_000002` 기준으로 지저분한 raw intake 자동보정과 전체 파이프라인 검증이 끝났습니다.
- Builder 6종 산출물과 다운로드 흐름이 실제 생성본 기준으로 확인됐습니다.
- 남아 있는 Territory `WARN`은 실행 차단이 아니라 운영 경고로 해석합니다.

즉 현재는 `Part2 착수 가능` 단계가 아니라 `Part2 완료` 단계입니다.

우선순위 기준:

- 우선순위와 상태(Completed / In Progress / Next)는 `docs/architecture/12_part2_status_source_of_truth.md`만 기준으로 본다.
- README의 설명 텍스트보다 단일 기준 문서가 항상 우선한다.

Part2 문서 운영 기준:
- 활성 상태/실행 문서: `docs/architecture/12_part2_status_source_of_truth.md`
- Part2 레거시 허브: `docs/part2/README.md`
- 앞으로의 새 단계 작업 문서: `docs/workstreams/`
  - `docs/part3` 같은 새 단계 폴더는 만들지 않습니다.

## 최근 동기화 핵심

### 2026-03-15 동기화 상태 (CRM KPI 거버넌스)

이번 동기화에서 반영된 핵심:

- CRM KPI는 `modules/kpi/crm_engine.py`를 공식 계산 소스로 사용
- Sandbox KPI 1차 계산 분리는 `modules/kpi/sandbox_engine.py`로 시작
- Territory KPI 계산 분리는 `modules/kpi/territory_engine.py`로 반영
- Prescription KPI 계산 분리는 `modules/kpi/prescription_engine.py`로 반영
- CRM 표준 활동유형은 8대 행동으로 고정
  - `PT / Demo / Closing / Needs / FaceToFace / Contact / Access / Feedback`
- Adapter는 원본과 표준을 분리 저장
  - `activity_type_raw` (원본)
  - `activity_type_standard` (표준 8대 행동)
- CRM Builder는 KPI를 재계산하지 않고 `crm_result_asset`만 주입
- Sandbox도 CRM KPI를 재계산하지 않고 CRM 공식 KPI 입력값만 사용
- Territory Builder payload는 KPI 계산 없이 엔진 결과를 조립/분할만 수행
- Prescription Builder payload는 KPI 계산 없이 엔진 결과를 조립/분할만 수행
- `hangyeol_pharma`, `daon_pharma` 기준 CRM->Builder->Sandbox KPI 전달 불일치 0건 확인
- `hangyeol_pharma`, `daon_pharma` 기준 Sandbox + Builder 최종 HTML 6종 생성 검증 통과
- `monthly_merge_pharma`는 6개월 월별 raw 생성/병합 검증과 실행모드별 점검 완료

### 2026-03-16 동기화 상태 (Sandbox Block Renderer Stage 4)

이번 동기화에서 Sandbox 보고서 구조 안정화가 반영되었습니다.

- `template_payload`는 유지하고 `block_payload`를 병행 사용
- Sandbox 템플릿은 `resolveBlock / resolveSlot / resolveBranchBlock` 중심으로 점진 전환
- branch lazy-load는 `branchCache`를 둬서 재선택 시 안정적으로 재사용
- resolver fallback 관측값을 콘솔에서 확인 가능
  - `block_missing`
  - `slot_missing`
  - `chunk_pending`
  - `fallback_used`
- 인사이트 슬롯(`executive_insight`)은 데이터가 없으면 숨김 처리
- 회귀 테스트 강화
  - `tests/test_sandbox/test_sandbox_block_resolver_regression.py`
  - `tests/test_sandbox/test_sandbox_renderer_snapshot.py`

검증 결과:
- `scripts/validate_sandbox_with_ops.py` 통과
- `scripts/validate_builder_with_ops.py` 통과

### 2026-03-23 동기화 상태 (Part2 완료 기준 반영)

- Part2 단일 기준 문서 상태는 `completed`입니다.
- Part2 완료 선언 문서 상태는 `official`입니다.
- 운영 콘솔은 `ui/console/` 패키지 기준으로 동작합니다.
- Agent 탭은 `run_report_context`뿐 아니라 `run_artifacts`와 최신 run bundle을 읽는 구조입니다.
- 패키지 업로드는 파일 업로드 직후가 아니라 `패키지 업로드 저장` 시점부터 intake 검증을 시작합니다.
- intake는 느슨한 통과가 아니라 Adapter가 실제로 읽을 수 있는 `_intake_staging` 정리본 생성까지 포함합니다.
- Prescription 월별 필터와 월별 detail asset 로딩은 실제 Builder 생성본 기준으로 정상화됐습니다.
- Territory 보고서는 `Leaflet` 로컬 번들 기준으로 열리도록 안정화됐습니다.

## 핵심 원칙

```text
원천데이터 -> Adapter -> Module -> Result Asset -> Validation Layer (OPS) -> Intelligence (RADAR) -> Builder
```

- OPS는 raw를 직접 읽지 않습니다.
- Adapter가 먼저 회사별 차이를 정리합니다.
- 모듈은 자기 Result Asset과 Builder용 payload를 만듭니다.
- OPS는 시스템 전체가 아니라 `Validation / Orchestration Layer` 역할에 가깝습니다.
- RADAR는 Validation 승인 결과를 받아 해석/우선순위 판단을 돕는 Intelligence 단계입니다.
- Builder는 계산보다는 `payload를 읽어 템플릿에 주입하는 단계`입니다.

## 현재 동작 범위

지원 raw 범위:
- CRM 활동 원본
- 담당자/조직 마스터
- 거래처/병원 담당 배정
- CRM 규칙/KPI 설정
- 실적
- 목표
- Prescription fact_ship

코드 기준 생성 가능한 주요 HTML:
- CRM 행동 분석 보고서
- Sandbox 성과 보고서
- Territory 권역 지도 보고서
- PDF 처방흐름 보고서
- RADAR Decision Brief
- 통합 검증 보고서

운영 콘솔:
- Streamlit 기반
- 회사 등록/선택 기반
- 회사 목록은 Supabase 등록 목록과 로컬 registry를 함께 반영
- 실행모드 선택
- 업로드 파일 반영
- 월별 raw 일괄 업로드 지원
- 실제 파이프라인 실행
- 산출물 미리보기/다운로드
- 대시보드 / 데이터 어댑터 / 파이프라인 / 분석 인텔리전스 / 결과물 빌더 / Agent 6개 탭 사용
- 현재 실행모드:
  - `CRM -> Sandbox`
  - `CRM -> Territory`
  - `Sandbox -> HTML`
  - `Sandbox -> Territory`
  - `CRM -> PDF`
  - `CRM -> Sandbox -> Territory`
  - `통합 실행`

## Builder 입력 방식

현재는 모듈별로 이렇게 연결됩니다.

- CRM
  - `crm_result_asset.json`
  - `crm_builder_payload.json`
  - `crm_builder_payload_assets/*.js`
  - `crm_analysis_preview.html`
- Prescription
  - `prescription_result_asset.json`
  - `prescription_builder_payload.json`
  - `prescription_builder_payload_assets/*.js`
  - `prescription_flow_preview.html`
- Territory
  - `territory_result_asset.json`
  - `territory_builder_payload.json`
  - `territory_builder_payload_assets/*.js`
  - `territory_map_preview.html`
- Sandbox
  - `sandbox_result_asset.json` 안의 `dashboard_payload.template_payload` + `dashboard_payload.block_payload`
  - `sandbox/sandbox_template_payload_assets/*.js`
  - `builder/sandbox_report_preview_assets/*.js`
  - `sandbox_report_preview.html`
- RADAR
  - `radar_result_asset.json`
  - `radar_report_preview.html`

즉 Builder는 `모듈이 먼저 만든 재료`만 받아서 화면을 만듭니다.

## 실제 폴더 구조

```text
data/
├── company_source/{company_key}/   # 회사별 원천데이터
├── ops_standard/{company_key}/     # 정규화 결과
├── ops_validation/{company_key}/   # 검증 결과 + builder payload + HTML + run 저장
├── public/                         # 공공 기준 데이터
└── sample_data/                    # 샘플/기획 참고 데이터
```

예:
- `data/company_source/daon_pharma`
- `data/ops_standard/daon_pharma`
- `data/ops_validation/daon_pharma`

run 저장 예:
- `data/ops_validation/{company_key}/runs/{run_id}/`
- `report_context.full.json`
- `report_context.prompt.json`
- `pipeline_summary.json`
- `artifacts.index.json`
- `chat/agent_chat_history.jsonl`

현재 확인된 회사 예시:
- `daon_pharma`: Builder 보고서 6종 저장 확인
- `hangyeol_pharma`: Builder 보고서 6종 저장 확인
- `monthly_merge_pharma`: 6개월 월별 raw 생성/병합 + 실행모드별 점검 완료

즉:
- 코드 구조는 6종 보고서를 지원
- 실제 저장 산출물은 회사별 마지막 실행 결과에 따라 다름

원천 파일 이름 규칙:
- `crm/crm_activity_raw.xlsx`
- `company/company_assignment_raw.xlsx`
- `company/account_master.xlsx`
- `sales/sales_raw.xlsx`
- `target/target_raw.xlsx`
- `company/fact_ship_raw.csv`
- `company/rep_master.xlsx`

즉 회사 구분은 파일명 앞 접두사가 아니라 `company_key` 폴더가 맡습니다.

## 실행 진입점 정리

현재 실제 실행 진입점은 회사명 없는 공통 스크립트입니다.

- `scripts/generate_source_raw.py`
- `scripts/normalize_crm_source.py`
- `scripts/normalize_sandbox_source.py`
- `scripts/normalize_prescription_source.py`
- `scripts/normalize_territory_source.py`
- `scripts/validate_crm_with_ops.py`
- `scripts/validate_sandbox_with_ops.py`
- `scripts/validate_prescription_with_ops.py`
- `scripts/validate_territory_with_ops.py`
- `scripts/validate_builder_with_ops.py`
- `scripts/validate_full_pipeline.py`

회사별 차이는 파일 이름이 아니라 [company_profile.py](/C:/sfe_master_ops/common/company_profile.py)에서 관리합니다.

참고:
- raw 샘플 생성은 [generate_source_raw.py](/C:/sfe_master_ops/scripts/generate_source_raw.py)가 공통 진입점입니다.
- 현재 테스트용 raw generator는 `config -> engine -> template -> writer` 구조로 정리되기 시작한 상태입니다.
- 현재 템플릿은 `daon_like`, `hangyeol_like` 2개이고, `monthly_merge_pharma`는 `daon_like + monthly_and_merged` 옵션으로 처리됩니다.
- 기존 회사별 생성 함수 본체는 template helper로 이동했고, 공통 진입점은 wrapper 없이 config를 직접 읽습니다.
- 실제 운영/테스트 공통 입구는 이미 `raw -> intake/onboarding -> adapter -> 기존 파이프라인` 기준으로 정리되어 있습니다.
- 테스트용 raw generator 정리 설계 문서는 [17_raw_generator_refactor_plan.md](/C:/sfe_master_ops/docs/architecture/17_raw_generator_refactor_plan.md)입니다.
- 실제 운영용 공통 입력 기준은 [18_real_company_raw_input_flow.md](/C:/sfe_master_ops/docs/architecture/18_real_company_raw_input_flow.md), [19_intake_gate_and_onboarding_plan.md](/C:/sfe_master_ops/docs/architecture/19_intake_gate_and_onboarding_plan.md), [20_common_intake_engine_implementation_plan.md](/C:/sfe_master_ops/docs/architecture/20_common_intake_engine_implementation_plan.md)입니다.

## 주요 파일

운영 콘솔:
- [ops_console.py](/C:/sfe_master_ops/ui/ops_console.py)
  - Streamlit 실행 진입점
- [app.py](/C:/sfe_master_ops/ui/console/app.py)
  - 실제 콘솔 앱 조립
  - 상단 메뉴에서 선택한 화면만 렌더
- [sidebar.py](/C:/sfe_master_ops/ui/console/sidebar.py)
  - 회사 선택/등록, 실행모드 선택
- [state.py](/C:/sfe_master_ops/ui/console/state.py)
  - 세션 상태, 업로드 캐시, 실행 로그
- [paths.py](/C:/sfe_master_ops/ui/console/paths.py)
  - 회사 기준 경로 계산
- [runner.py](/C:/sfe_master_ops/ui/console/runner.py)
  - 실제 실행 호출, run 이력 저장
- [display.py](/C:/sfe_master_ops/ui/console/display.py)
  - 공통 화면 블록
- [artifacts.py](/C:/sfe_master_ops/ui/console/artifacts.py)
  - 산출물 경로/미리보기/다운로드 보조
- [tabs](/C:/sfe_master_ops/ui/console/tabs)
  - 6개 탭 구현
- [agent](/C:/sfe_master_ops/ui/console/agent)
  - Agent run/context/artifact/LLM 처리

회사별 실행 프로필:
- [company_profile.py](/C:/sfe_master_ops/common/company_profile.py)

모듈별 Builder payload:
- [builder_payload.py](/C:/sfe_master_ops/modules/crm/builder_payload.py)
- [builder_payload.py](/C:/sfe_master_ops/modules/prescription/builder_payload.py)
- [builder_payload.py](/C:/sfe_master_ops/modules/sandbox/builder_payload.py)
- [builder_payload.py](/C:/sfe_master_ops/modules/territory/builder_payload.py)

Builder 템플릿:
- [report_template.html](/C:/sfe_master_ops/templates/report_template.html)
- [crm_analysis_template.html](/C:/sfe_master_ops/templates/crm_analysis_template.html)
- [territory_optimizer_template.html](/C:/sfe_master_ops/templates/territory_optimizer_template.html)
- [prescription_flow_template.html](/C:/sfe_master_ops/templates/prescription_flow_template.html)
- [radar_report_template.html](/C:/sfe_master_ops/templates/radar_report_template.html)
- [total_valid_templates.html](/C:/sfe_master_ops/templates/total_valid_templates.html)

참고:
- `templates/`에는 현재 위 6개 템플릿을 운영 기준으로 유지
- 예전 문서에 남아 있던 `hh.html`, `hh_builder_template.js`, `hhb.js`는 현재 저장소에 없음

## 실행 방식

API:

```bash
uv run uvicorn modules.validation.main:app --reload --host 0.0.0.0 --port 8000
```

호환용 기존 진입점:

```bash
uv run uvicorn ops_core.main:app --reload --host 0.0.0.0 --port 8000
```

참고:
- 새 기본 경로는 `modules.validation.main:app`입니다.
- 기존 `ops_core.main:app`는 호환용으로만 함께 지원합니다.

운영 콘솔:

```bash
uv run python -m streamlit run ui/ops_console.py --server.port 8501
```

참고:
- 일부 Windows 환경에서는 `.venv\Scripts\streamlit.exe`가 Code Integrity 정책에 걸릴 수 있습니다.
- 이 경우 `uv run streamlit ...` 대신 `uv run python -m streamlit ...`를 사용합니다.

## 실행모드

- `CRM -> Sandbox`
- `CRM -> Territory`
- `Sandbox -> HTML`
- `Sandbox -> Territory`
- `CRM -> PDF`
- `CRM -> Sandbox -> Territory`
- `통합 실행`

`통합 실행`이면 현재 기준으로 아래가 함께 생성됩니다.

- `crm_analysis_preview.html`
- `sandbox_report_preview.html`
- `territory_map_preview.html`
- `prescription_flow_preview.html`
- `radar_report_preview.html`
- `total_valid_preview.html`

단, 위 6개는 `입력 데이터 + 모듈 산출물 + Builder payload`가 모두 준비됐을 때 기준입니다.
즉 회사별 마지막 실행 상태에 따라 일부만 저장돼 있을 수 있습니다.

## 현재 주의할 점

- 완전 범용 제품이라기보다 `회사별 커스텀 가능한 공통 틀`에 가깝습니다.
- 템플릿이 바뀌면 모듈 쪽 Builder payload도 같이 맞춰야 합니다.
- Prescription HTML은 경량화했지만 다른 보고서보다 여전히 무거운 편입니다.
- 통합 보고서는 개별 HTML을 한 화면에서 묶어 보는 허브입니다.
- WebSlide 기능은 현재 제거된 상태입니다.
- Territory는 이제 `ops_standard/{company_key}/territory/ops_territory_activity.xlsx`를 만들고, Builder는 이 표준 파일 기반 payload를 읽습니다.
- Sandbox 보고서는 이제 전체 지점 상세를 처음부터 싣지 않습니다.
- Sandbox 보고서는 먼저 요약만 열고, 지점을 고르면 `builder/sandbox_report_preview_assets/*.js`에서 해당 지점 상세를 읽습니다.
- Sandbox 필터(지점/담당자)는 `branch_index + branch asset` 기준으로 동작하며, 지점 선택 시 해당 지점 asset을 지연 로딩해 담당자 목록을 채웁니다.
- Territory 지도는 기본값이 `담당자 미선택` 상태입니다.
- Territory 지도는 초기 전체 마커를 한 번에 뿌리지 않고, 담당자를 고른 뒤 해당 담당자의 `catalog asset`과 선택한 `월 asset`만 순차 로딩합니다.
- Territory Builder 출력에는 `builder/territory_map_preview_assets/*.js`가 같이 생기며, 지도는 이 분리 asset을 필요할 때만 읽습니다.
- Territory Builder 출력에는 `builder/territory_map_preview_assets/leaflet/*`도 같이 생기며, 지도 라이브러리는 로컬 파일 기준으로 엽니다.

## 현재 검증된 회사 예시

- `hangyeol_pharma`
- `daon_pharma`
- `monthly_merge_pharma`

## 문서

- 문서 허브: [docs/README.md](/C:/sfe_master_ops/docs/README.md)
- 실행 방법: [RUNBOOK.md](/C:/sfe_master_ops/RUNBOOK.md)
- 구조 설명: [STRUCTURE.md](/C:/sfe_master_ops/STRUCTURE.md)
- Sandbox 리팩토링 요약: [06_sandbox_refactor_summary.md](/C:/sfe_master_ops/docs/architecture/06_sandbox_refactor_summary.md)

