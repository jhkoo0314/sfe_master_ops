# Sales Data OS 구조 문서

작성일: 2026-03-23

## 핵심 흐름

```text
원천데이터 -> Adapter -> Module/Core Engine -> Result Asset -> Validation Layer(OPS) -> Intelligence(RADAR) -> Builder
```

이 프로젝트는 `완전 무설정 범용 제품`보다는  
`회사별로 얇게 커스텀 가능한 공통 틀`에 가깝습니다.

그리고 현재 구조는 `유기적 양방향 연결`보다는
`단방향 검증 확장`에 더 가깝습니다.

즉 Sales Data OS 관점에서:
- 앞단 결과를 확인하고
- OPS가 중간 검증을 하고
- 통과한 것만 Intelligence와 Builder로 넘깁니다

현재 단계 메모:
- 현재 공식 상태는 `Part2 완료`입니다.
- 단일 기준은 `docs/architecture/12_part2_status_source_of_truth.md`입니다.
- 루트 구조 문서는 위 단일 기준 문서와 같은 세계관으로만 설명합니다.

## 최상위 구조

```text
sfe_master_ops/
├── adapters/
├── modules/
├── ops_core/                  # 호환 유지용 경로
├── result_assets/
├── ui/
├── templates/
├── scripts/
├── common/
├── data/
├── docs/
├── README.md
├── RUNBOOK.md
└── STRUCTURE.md
```

## 폴더별 역할

### `adapters/`

회사 raw를 공통 구조로 바꾸는 층입니다.

- CRM
- Prescription
- Sandbox
- Territory

현재 상태 메모:
- `adapters/territory/`는 이제 CRM 표준 활동과 거래처 좌표를 합쳐 `ops_territory_activity.xlsx`를 만드는 역할을 합니다.
- Territory는 `Sandbox result asset`을 중심으로 돌고, 날짜별 실제 동선은 Territory 표준 활동 파일로 붙습니다.

### `modules/`

실제 계산과 Builder용 재료 생성을 담당하는 층입니다.

- `modules/crm/`
  - CRM Result Asset 생성
  - `modules/kpi/crm_engine.py` 기준으로 CRM 11 KPI 계산
  - `builder_payload.py`는 CRM 자산 주입 전용(재계산 없음)
- `modules/prescription/`
  - Prescription Result Asset 생성
  - `service.py`는 Prescription KPI 엔진 호출 + Result Asset/Builder payload 조립
  - `builder_payload.py`는 계산 없이 처방 보고서용 payload 조립/분할만 수행
- `modules/sandbox/`
  - Sandbox Result Asset 생성
  - CRM KPI는 입력값을 사용하고 Sandbox에서 재계산하지 않음
  - `service.py`는 orchestration만 담당하고 조립 책임은 `builders/`로 분리 완료
  - KPI 계산 1차 분리는 `modules/kpi/sandbox_engine.py` 호출로 수행
  - `builders/`
    - `template_payload_builder.py`: 지점/담당자/품목 분석 payload 조립
    - `block_payload_builder.py`: block resolver용 block payload 조립
  - block architecture 적용
    - `block_registry.py`: block 계약/메타 정의
    - `block_resolver.py`: block/slot/branch 조회 + fallback + 카운터
  - `builder_payload.py`에서 지점 상세 분리용 manifest 생성
  - `dashboard_payload.template_payload` + `dashboard_payload.block_payload` 병행 유지
  - 현재는 `manifest + 지점 asset` 구조로 Sandbox Builder 데이터를 분리 생성
- `modules/territory/`
  - Territory Result Asset 생성
  - `service.py`는 Territory KPI 엔진 호출 + Result Asset/Builder payload 조립
  - `builder_payload.py`는 계산 없이 지도 보고서용 payload 조립/분할만 수행
  - 현재는 `manifest + 담당자/월 asset` 구조로 Territory Builder 데이터를 분리 생성
- `modules/builder/`
  - 모듈이 만든 payload를 읽어 HTML로 주입
  - Territory, Prescription, CRM, Sandbox처럼 큰 payload는 Builder 단계에서도 분리 asset 구조를 유지하도록 보정
  - CRM preview 생성 전에는 최신 `crm_builder_payload.json`을 다시 생성해 예전 필터/범위 payload가 남지 않게 함
  - 직접 계산 엔진 역할은 하지 않음

- `modules/kpi/`
  - 모듈 내부 KPI 계산 엔진 모음
- 현재 CRM KPI 엔진(`crm_engine.py`) 운영 중
- Sandbox KPI 엔진(`sandbox_engine.py`) 운영 중
- Territory KPI 엔진(`territory_engine.py`) 운영 중
- Prescription KPI 엔진(`prescription_engine.py`) 운영 중

### `modules/validation/`

현재 Validation / Orchestration Layer의 기본 패키지입니다.

여기서 OPS는:
- 직접 계산하는 분석 엔진이 아니라
- `검증/전달 판단 게이트` 역할입니다

즉 하는 일은 주로 이것입니다.

- 매핑 상태 확인
- 품질 상태 확인
- 다음 단계 전달 판단
- Result Asset 평가 흐름 관리
- 실제 실행 흐름 조정

주요 위치:
- `modules/validation/main.py`
- `modules/validation/api/`
- `modules/validation/workflow/`

현재 메모:
- `modules/validation/api/`는 Result Asset 평가 API에 가깝습니다.
- `modules/validation/workflow/orchestrator.py`는 평가 오케스트레이션입니다.
- `modules/validation/workflow/execution_service.py`는 실제 실행 조정기입니다.
- raw 정리, staging 준비, monthly merge 본체는 점진적으로 `modules/intake` 쪽으로 이동 완료 상태입니다.

### `ops_core/`

현재는 `modules/validation/`의 호환 유지용 패키지입니다.

쉽게 말하면:
- 새 기본 경로는 `modules/validation/*`
- `ops_core/*`는 예전 import가 갑자기 깨지지 않게 남겨둔 경로입니다.

### `result_assets/`

모듈끼리 주고받는 표준 결과 형식입니다.

- `crm_result_asset.py`
- `prescription_result_asset.py`
- `sandbox_result_asset.py`
- `territory_result_asset.py`

참고:
- Builder 결과 스키마 `HtmlBuilderResultAsset`은 현재 `modules/builder/schemas.py` 안에 있습니다.

### `ui/`

운영 콘솔입니다.

- [ops_console.py](/C:/sfe_master_ops/ui/ops_console.py)
  - Streamlit 진입점
- `ui/console/`
  - 실제 콘솔 구현 패키지
- [app.py](/C:/sfe_master_ops/ui/console/app.py)
  - 콘솔 앱 조립
- [sidebar.py](/C:/sfe_master_ops/ui/console/sidebar.py)
  - 회사 선택/등록, 실행모드 선택
  - 회사 목록은 Supabase + 로컬 registry 병합 방식 사용
- [state.py](/C:/sfe_master_ops/ui/console/state.py)
  - 세션 상태, 업로드 캐시, 실행 로그
  - 월별 raw 업로드 저장 보조 포함
- [paths.py](/C:/sfe_master_ops/ui/console/paths.py)
  - 회사 기준 경로와 source target 계산
- [runner.py](/C:/sfe_master_ops/ui/console/runner.py)
  - 실행 준비 판단, 실행 호출, 실행 이력 저장
  - 실행 분석 문서 저장
- [pipeline_tab.py](/C:/sfe_master_ops/ui/console/tabs/pipeline_tab.py)
  - 실행 중 본문 상태 박스와 완료/실패 표시
  - 월별 raw 감지/자동 병합 안내
- `ui/console/tabs/upload_tab.py`
  - 일반 raw 업로드
  - 월별 raw 일괄 업로드
- [artifacts.py](/C:/sfe_master_ops/ui/console/artifacts.py)
  - 산출물 경로, 미리보기, 보고서 파일 탐색
- `ui/console/analysis_explainer.py`
  - `PASS/WARN/APPROVED`를 사람이 읽는 해석 문장으로 변환
- [display.py](/C:/sfe_master_ops/ui/console/display.py)
  - 공통 화면 블록, 업로드 행 표시
- [shared.py](/C:/sfe_master_ops/ui/console/shared.py)
  - 공통 표시 묶음
- `ui/console/tabs/`
  - 6개 탭 구현
- `ui/console/agent/`
  - Agent run/context/artifact/history/mock/LLM 처리

즉 예전 `console_*` 파일은 삭제됐고, 실제 구현은 `ui/console/` 아래로 정리된 상태입니다.

현재 상태 메모:
- 회사 선택은 `company_registry` 기반 선택을 사용합니다.
- Agent는 `run_report_context`와 `run_artifacts`를 읽습니다.
- 콘솔 리팩토링 1차가 아니라 실제 파일 삭제까지 마친 상태입니다.

### `templates/`

실제 HTML 보고서 템플릿입니다.

- [report_template.html](/C:/sfe_master_ops/templates/report_template.html)
- [crm_analysis_template.html](/C:/sfe_master_ops/templates/crm_analysis_template.html)
- [territory_optimizer_template.html](/C:/sfe_master_ops/templates/territory_optimizer_template.html)
- [prescription_flow_template.html](/C:/sfe_master_ops/templates/prescription_flow_template.html)
- [radar_report_template.html](/C:/sfe_master_ops/templates/radar_report_template.html)
- [total_valid_templates.html](/C:/sfe_master_ops/templates/total_valid_templates.html)

참고:
- 현재 운영 기준 템플릿은 위 6개입니다.
- 예전 문서에 남아 있던 `hh.html`, `hh_builder_template.js`, `hhb.js`는 현재 저장소에 없습니다.
- `report_template.html`은 resolver 기반 렌더 + fallback 유지 구조를 사용합니다.
- `radar_report_template.html`의 `Layer 03 : Decision Options`는 현재 임시 고정 문구를 사용합니다. RADAR signal/decision rule이 확정되면 payload 기반 렌더로 다시 전환합니다.

### `scripts/`

정규화/검증/Builder 생성 스크립트입니다.

원칙:
- 루트 `scripts/`에는 공통 진입점만 둡니다.
- 회사별 raw 생성 구현은 `scripts/raw_generators/` 아래에 둡니다.

대표 파일:

- `generate_source_raw.py`
- `normalize_crm_source.py`
- `normalize_sandbox_source.py`
- `normalize_prescription_source.py`
- `normalize_territory_source.py`
- `validate_crm_with_ops.py`
- `validate_prescription_with_ops.py`
- `validate_sandbox_with_ops.py`
- `validate_territory_with_ops.py`
- `validate_radar_with_ops.py`
- `validate_builder_with_ops.py`
- `validate_full_pipeline.py`

운영 메모:
- 현재 기준 진입점 이름은 위 공통 이름만 사용합니다.
- 실제 경로와 입력 파일 선택은 계속 `company_runtime.py`가 회사 코드 기준으로 처리합니다.
- raw 샘플 생성은 `generate_source_raw.py`가 공통 진입점입니다.
- 현재 테스트용 raw generator는 `config -> engine -> template -> writer` 구조로 정리되기 시작한 상태입니다.
- 현재 템플릿은 `daon_like`, `hangyeol_like` 2개이고, `monthly_merge_pharma`는 `daon_like + monthly_and_merged` 옵션으로 처리됩니다.
- 기존 회사별 생성 함수 본체는 template helper로 이동했고, 공통 진입점은 wrapper 없이 config를 직접 읽습니다.
- 실제 운영에서 더 중요한 공통 입구는 이미 `raw -> intake/onboarding -> adapter` 구조로 정리돼 있습니다.
- 그래서 테스트용 생성기 정리 설계는 `docs/architecture/17_raw_generator_refactor_plan.md`, 실제 운영용 공통 입력 설계는 `docs/architecture/18_real_company_raw_input_flow.md`, `docs/architecture/19_intake_gate_and_onboarding_plan.md`, `docs/architecture/20_common_intake_engine_implementation_plan.md`를 함께 봅니다.

현재 중요한 점:
- CRM 검증 스크립트가 `crm_builder_payload.json` 생성
- CRM 검증 스크립트는 필요 시 `crm_builder_payload_assets/*.js`도 같이 생성
- Builder 검증 스크립트도 CRM preview를 만들기 전에 `crm_builder_payload.json`을 최신 결과자산 기준으로 다시 생성
- Prescription 검증 스크립트가 `prescription_builder_payload.json` 생성
- Prescription 검증 스크립트는 필요 시 `prescription_builder_payload_assets/*.js`도 같이 생성
- Territory 정규화 스크립트가 `ops_territory_activity.xlsx` 생성
- Territory 검증 스크립트가 `territory_builder_payload.json`과 `territory_builder_payload_assets/*.js` 생성
- Builder 검증 스크립트는 이 payload를 읽어 HTML 생성
- CRM Builder 결과에도 `crm_analysis_preview_assets/*.js`가 같이 복사될 수 있음
- Prescription Builder 결과에도 `prescription_flow_preview_assets/*.js`가 같이 복사될 수 있음
- Territory Builder 결과에는 `territory_map_preview_assets/*.js`가 같이 복사됨
- 코드상으로는 CRM / Sandbox / Territory / Prescription / RADAR / Total Valid 6종 생성 가능
- 실제 저장된 HTML은 회사별 마지막 실행 시점에 따라 일부만 있을 수 있음
- RADAR 결과 자산은 `data/ops_validation/{company_key}/radar/radar_result_asset.json`에 저장됨
- 실행 중 `monthly_raw/YYYYMM/`가 감지되면 실행 전에 자동 병합 후 기존 파이프라인이 계속 동작함

### `common/`

공통 설정과 회사 런타임 유틸입니다.

- [company_runtime.py](/C:/sfe_master_ops/common/company_runtime.py)
  - 회사 코드 기준 경로 생성
- [company_profile.py](/C:/sfe_master_ops/common/company_profile.py)
  - 회사별 raw 파일 위치와 adapter 설정을 묶어서 관리
- [company_registry.py](/C:/sfe_master_ops/common/company_registry.py)
  - 회사 등록/선택과 고정 `company_key` 관리
  - Supabase + 로컬 registry 병합 조회
- [run_registry.py](/C:/sfe_master_ops/common/run_registry.py)
  - 기존 호환용 facade 유지
- `ui/console/`
  - 콘솔 실제 구현 패키지
- `common/run_storage/`
  - `runs`, `run_steps`, `run_artifacts`, `run_report_context`, `agent_chat_logs` 저장/조회 분리 완료
- `config.py`
- `exceptions.py`
- `types.py`

### `data/`

실제 운영 검증 데이터가 쌓이는 곳입니다.

```text
data/
├── company_source/      # 회사별 원천데이터
├── ops_standard/        # 정규화 결과
├── ops_validation/      # 검증 결과 + builder payload + HTML
├── public/              # 공공 기준 데이터
├── sample_data/         # 샘플/기획 참고 데이터
└── README.md
```

회사별로 이렇게 분리됩니다.

```text
data/company_source/{company_key}/
data/ops_standard/{company_key}/
data/ops_validation/{company_key}/
```

현재 원천 파일 이름은 회사명 접두사 없이 공통 이름을 씁니다.

```text
crm/crm_activity_raw.xlsx
company/company_assignment_raw.xlsx
company/account_master.xlsx
sales/sales_raw.xlsx
target/target_raw.xlsx
company/fact_ship_raw.csv
company/rep_master.xlsx
```

## 현재 Builder 기준 흐름

Builder는 직접 raw를 읽지 않습니다.

현재 연결은 이렇게 정리됩니다.

- CRM
  - `crm_result_asset.json`
  - `crm_builder_payload.json`
  - `crm_builder_payload_assets/*.js`
  - `crm_analysis_preview.html`
  - 표준 활동유형은 8대 행동(`PT/Demo/Closing/Needs/FaceToFace/Contact/Access/Feedback`)
- Prescription
  - `prescription_result_asset.json`
  - `prescription_builder_payload.json`
  - `prescription_flow_preview.html`
- Territory
  - `territory_result_asset.json`
  - `territory_builder_payload.json`
  - `territory_builder_payload_assets/*.js`
  - `territory_map_preview.html`
- Sandbox
  - `sandbox_result_asset.json` 내부 `dashboard_payload.template_payload`
  - `sandbox_template_payload_assets/*.js`
  - `sandbox_report_preview_assets/*.js`
  - `sandbox_report_preview.html`
- RADAR
  - `radar_result_asset.json`
  - `radar_report_preview.html`

즉 Builder는 `표현 단계`이고, 계산은 앞단 모듈에 둡니다.

추가 메모:
- Territory Builder payload는 기본 화면에서 전체 병원 좌표를 다 싣지 않습니다.
- Sandbox 보고서도 기본 화면에서 전체 지점 상세를 다 싣지 않습니다.
- Sandbox는 요약만 먼저 열고, 지점을 고르면 해당 지점 asset만 읽습니다.
- Sandbox 필터는 `branch_index`로 지점 목록을 먼저 구성하고, 선택된 지점의 `branch asset`을 로딩한 뒤 담당자 필터를 채웁니다.
- 기본값은 `담당자 미선택`이고, 담당자를 고르면 해당 담당자용 `catalog asset`과 선택 월용 `route asset`만 읽습니다.
- `total_valid_preview.html`은 Builder 단계에서 별도로 생성됩니다.
- 회사별 현재 저장 상태는 다릅니다.
- `daon_pharma`는 Builder 6종 저장이 확인됩니다.
- `hangyeol_pharma`는 현재 Builder 6종 저장이 확인됩니다.

## 현재 UI 기준 흐름

### 데이터 어댑터 탭

- raw 파일 업로드
- 같은 파일 중복 업로드 허용
- 고급 설정은 접힘 상태
- 월별 raw 다중 업로드 지원
- 파일명에서 월 정보를 읽어 `monthly_raw/YYYYMM/`에 저장 가능

### 파이프라인 탭

- 실행모드 선택
- 실행 전 반영 파일 확인
- 실제 파이프라인 실행
- `monthly_raw` 감지 시 자동 병합 안내

이 단계에서 OPS는 `무엇을 계산하느냐`보다
`지금 상태에서 다음으로 넘길 수 있느냐`를 보는 역할입니다.

### 분석 인텔리전스 탭

- 차트 중심이 아니라 산출물 검증 탭
- xlsx/csv/json 미리보기
- 단계 배지 표시
- 파일 다운로드
- `판정 이유`
- `해석`
- `근거 수치`
- 실행 분석 문서 다운로드

### 결과물 빌더 탭

- 보고서 유형 선택
- 기간 선택
- HTML 열기/다운로드
- Prescription는 원본 엑셀 다운로드도 제공

## 현재 생성 가능한 보고서

개별 보고서:
- CRM 행동 분석 보고서
- Sandbox 성과 보고서
- Territory 권역 지도 보고서
- PDF 처방흐름 보고서
- RADAR Decision Brief

통합 보고서:
- `total_valid_preview.html`
- 생성된 개별 HTML을 한 화면에서 묶어 보는 허브
- 사이드바에는 5개 보고서가 항상 보이고
- 생성 안 된 것은 비활성 표시

즉 통합 보고서도 OPS가 새 계산을 하는 곳이 아니라,
최종 템플릿 결과를 확인하는 관제 화면에 가깝습니다.

주의:
- 위 목록은 코드 기준 생성 가능 목록입니다.
- 실제 폴더에 저장된 결과는 회사별 마지막 실행 상태를 기준으로 달라질 수 있습니다.

## Sandbox Block 문서/테스트 위치

- 설계 문서
  - [04_sandbox_block_contract.md](/C:/sfe_master_ops/docs/architecture/04_sandbox_block_contract.md)
  - [05_sandbox_template_slots.md](/C:/sfe_master_ops/docs/architecture/05_sandbox_template_slots.md)
  - [06_sandbox_refactor_summary.md](/C:/sfe_master_ops/docs/architecture/06_sandbox_refactor_summary.md)
- 회귀 테스트
  - [test_sandbox_block_resolver_regression.py](/C:/sfe_master_ops/tests/test_sandbox/test_sandbox_block_resolver_regression.py)
  - [test_sandbox_renderer_snapshot.py](/C:/sfe_master_ops/tests/test_sandbox/test_sandbox_renderer_snapshot.py)

## 현재 빠진 것

- WebSlide 기능은 제거됨
- 통합 보고서는 슬라이드 생성기가 아니라 HTML 허브 역할만 함
- LLM 자동 인사이트 생성은 아직 연결 안 됨

