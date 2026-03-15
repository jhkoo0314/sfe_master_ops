# Sales Data OS

원천데이터를 넣으면 `정규화 -> 모듈 분석 -> OPS 검증 게이트 -> Builder HTML 생성`까지 이어지는 Sales Data OS 운영 검증 프로젝트입니다.

지금 상태의 핵심은 이것입니다.

- 회사별 raw를 같은 틀로 흡수하고 어디까지 연결되는지 검증
- CRM, Prescription, Sandbox, Territory, Builder를 실제로 실행 가능
- 회사 코드별로 결과 폴더를 분리
- 코드 기준으로 HTML 보고서 6종과 통합 허브까지 생성 가능
- 실제 저장된 보고서 수는 회사별 마지막 실행 상태에 따라 다를 수 있음

## Part 1 상태

2026-03-11 기준으로 이 프로젝트는 `Part 1 완료` 상태로 봅니다.

쉽게 말하면:

- CRM / Prescription / Sandbox / Territory / Builder가 한 흐름으로 실제 실행됩니다.
- 운영 콘솔에서 회사 코드 기준으로 실행과 산출물 확인이 가능합니다.
- 핵심 JSON에는 버전이 붙어 있어 파일 규격 추적이 가능합니다.
- CRM / Prescription / Sandbox / Territory는 무거운 상세를 필요할 때만 읽는 구조로 정리됐습니다.
- 파일 크기 / 로딩 시간 회귀 테스트가 들어 있어 다시 무거워지는 문제를 빨리 잡을 수 있습니다.

즉 지금은 `기초 구조를 만드는 단계`를 넘어서,
`운영 직전 단계까지 안정성을 확보한 상태`로 판단합니다.

## Part 2 실행 가능성

2026-03-11 기준으로 `Part 2 착수 가능` 상태입니다.

이유는 간단합니다.

- 앞단 구조가 크게 흔들리지 않습니다.
- 실행 순서와 산출물 규격이 정리돼 있습니다.
- 콘솔, 모듈, Builder, 문서가 같은 구조를 바라보도록 맞춰졌습니다.

따라서 Part 2는 새 기능을 억지로 많이 붙이는 단계보다,
`Validation Layer(OPS)를 안정화하고 Intelligence Layer를 확장하는 단계`로 가는 것이 맞습니다.

권장 우선순위:

1. `Intake Gate`
2. `Daily Watch`
3. `배치 자동화 / 실패 알림`
4. `Action Queue`
5. `규칙 / 임계치 외부화`

## 2026-03-15 동기화 상태 (CRM KPI 거버넌스)

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
- Sandbox + Builder 최종 HTML 6종 검증도 2개 회사 모두 통과

## 핵심 원칙

```text
원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder
```

- OPS는 raw를 직접 읽지 않습니다.
- Adapter가 먼저 회사별 차이를 정리합니다.
- 모듈은 자기 Result Asset과 Builder용 payload를 만듭니다.
- OPS는 시스템 전체가 아니라 `Validation / Orchestration Layer` 역할에 가깝습니다.
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
- 회사 코드 입력
- 실행모드 선택
- 업로드 파일 반영
- 실제 파이프라인 실행
- 산출물 미리보기/다운로드
- 대시보드 / 데이터 어댑터 / 파이프라인 / 분석 인텔리전스 / 결과물 빌더 5개 탭 사용
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
  - `sandbox_result_asset.json` 안의 `dashboard_payload.template_payload`
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
├── ops_validation/{company_key}/   # 검증 결과 + builder payload + HTML
├── public/                         # 공공 기준 데이터
└── sample_data/                    # 샘플/기획 참고 데이터
```

예:
- `data/company_source/daon_pharma`
- `data/ops_standard/daon_pharma`
- `data/ops_validation/daon_pharma`

현재 확인된 회사 예시:
- `daon_pharma`: Builder 보고서 6종 저장 확인
- `hangyeol_pharma`: Builder 보고서 6종 저장 확인

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
- raw 샘플 생성도 이제 [generate_source_raw.py](/C:/sfe_master_ops/scripts/generate_source_raw.py)를 먼저 보고, 실제 회사별 생성 로직은 profile에 등록된 스크립트가 맡습니다.
- 회사별 raw 생성 구현은 [raw_generators](/C:/sfe_master_ops/scripts/raw_generators) 아래에 둡니다.

## 주요 파일

운영 콘솔:
- [ops_console.py](/C:/sfe_master_ops/ui/ops_console.py)
- [console_state.py](/C:/sfe_master_ops/ui/console_state.py)
- [console_paths.py](/C:/sfe_master_ops/ui/console_paths.py)
- [console_runner.py](/C:/sfe_master_ops/ui/console_runner.py)
- [console_artifacts.py](/C:/sfe_master_ops/ui/console_artifacts.py)
- [console_display.py](/C:/sfe_master_ops/ui/console_display.py)
- [console_shared.py](/C:/sfe_master_ops/ui/console_shared.py)
- [console_sidebar.py](/C:/sfe_master_ops/ui/console_sidebar.py)
- [console_tabs.py](/C:/sfe_master_ops/ui/console_tabs.py)

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
uv run uvicorn ops_core.main:app --reload --host 0.0.0.0 --port 8000
```

운영 콘솔:

```bash
uv run streamlit run ui/ops_console.py --server.port 8501
```

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

## 현재 검증된 회사 예시

- `hangyeol_pharma`
- `daon_pharma`

## 문서

- 문서 허브: [docs/README.md](/C:/sfe_master_ops/docs/README.md)
- 실행 방법: [RUNBOOK.md](/C:/sfe_master_ops/docs/_root/RUNBOOK.md)
- 구조 설명: [STRUCTURE.md](/C:/sfe_master_ops/docs/_root/STRUCTURE.md)
