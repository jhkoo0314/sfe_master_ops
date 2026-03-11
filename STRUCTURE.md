# SFE OPS 구조 문서

작성일: 2026-03-11

## 핵심 흐름

```text
원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder
```

이 프로젝트는 `완전 무설정 범용 제품`보다는  
`회사별로 얇게 커스텀 가능한 공통 틀`에 가깝습니다.

그리고 현재 구조는 `유기적 양방향 연결`보다는
`단방향 검증 확장`에 더 가깝습니다.

즉:
- 앞단 결과를 확인하고
- OPS가 중간 검증을 하고
- 통과한 것만 다음 단계와 템플릿으로 넘깁니다

## 최상위 구조

```text
sfe_master_ops/
├── adapters/
├── modules/
├── ops_core/
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
  - `builder_payload.py`에서 CRM 보고서용 payload 생성
- `modules/prescription/`
  - Prescription Result Asset 생성
  - `builder_payload.py`에서 처방 보고서용 payload 생성
- `modules/sandbox/`
  - Sandbox Result Asset 생성
  - `dashboard_payload.template_payload`를 Builder 입력으로 사용
- `modules/territory/`
  - Territory Result Asset 생성
  - `builder_payload.py`에서 지도 보고서용 payload 생성
  - 현재는 `manifest + 담당자/월 asset` 구조로 Territory Builder 데이터를 분리 생성
- `modules/builder/`
  - 모듈이 만든 payload를 읽어 HTML로 주입
  - Territory처럼 큰 payload는 Builder 단계에서도 분리 asset 구조를 유지하도록 보정
  - 직접 계산 엔진 역할은 하지 않음

### `ops_core/`

OPS 판단과 파이프라인 실행을 담당합니다.

여기서 OPS는:
- 직접 계산하는 분석 엔진이 아니라
- `중앙 관제 게이트` 역할입니다

즉 하는 일은 주로 이것입니다.

- 매핑 상태 확인
- 품질 상태 확인
- 다음 단계 전달 판단
- 실행 흐름 관리

주요 위치:
- `ops_core/main.py`
- `ops_core/api/`
- `ops_core/workflow/`

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
- [console_state.py](/C:/sfe_master_ops/ui/console_state.py)
  - 세션 상태, 업로드 캐시, 실행 로그
- [console_paths.py](/C:/sfe_master_ops/ui/console_paths.py)
  - 회사 코드 기준 경로와 source target 계산
- [console_runner.py](/C:/sfe_master_ops/ui/console_runner.py)
  - 실행 준비 판단, 실행 호출, 실행 이력 저장
- [console_artifacts.py](/C:/sfe_master_ops/ui/console_artifacts.py)
  - 산출물 경로, 미리보기, 보고서 파일 탐색
- [console_display.py](/C:/sfe_master_ops/ui/console_display.py)
  - 공통 화면 블록, 업로드 행 표시
- [console_shared.py](/C:/sfe_master_ops/ui/console_shared.py)
  - 얇게 남겨 둔 공통 표시 헬퍼
- [console_sidebar.py](/C:/sfe_master_ops/ui/console_sidebar.py)
  - 사이드바 렌더링
- [console_tabs.py](/C:/sfe_master_ops/ui/console_tabs.py)
  - 데이터 어댑터 / 파이프라인 / 분석 인텔리전스 / 결과물 빌더 탭

즉 예전처럼 `ops_console.py` 한 파일에 몰아넣지 않고 분리된 상태입니다.

### `templates/`

실제 HTML 보고서 템플릿입니다.

- [report_template.html](/C:/sfe_master_ops/templates/report_template.html)
- [crm_analysis_template.html](/C:/sfe_master_ops/templates/crm_analysis_template.html)
- [territory_optimizer_template.html](/C:/sfe_master_ops/templates/territory_optimizer_template.html)
- [prescription_flow_template.html](/C:/sfe_master_ops/templates/prescription_flow_template.html)
- [total_valid_templates.html](/C:/sfe_master_ops/templates/total_valid_templates.html)

참고:
- 현재 운영 기준 템플릿은 위 5개입니다.
- 예전 문서에 남아 있던 `hh.html`, `hh_builder_template.js`, `hhb.js`는 현재 저장소에 없습니다.

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
- `validate_builder_with_ops.py`
- `validate_full_pipeline.py`

운영 메모:
- 현재 기준 진입점 이름은 위 공통 이름만 사용합니다.
- 실제 경로와 입력 파일 선택은 계속 `company_runtime.py`가 회사 코드 기준으로 처리합니다.
- raw 샘플 생성은 `generate_source_raw.py`가 공통 진입점이고, 실제 회사별 생성 로직은 `company_profile.py`에 연결된 생성 스크립트가 담당합니다.

현재 중요한 점:
- CRM 검증 스크립트가 `crm_builder_payload.json` 생성
- Prescription 검증 스크립트가 `prescription_builder_payload.json` 생성
- Territory 정규화 스크립트가 `ops_territory_activity.xlsx` 생성
- Territory 검증 스크립트가 `territory_builder_payload.json`과 `territory_builder_payload_assets/*.js` 생성
- Builder 검증 스크립트는 이 payload를 읽어 HTML 생성
- Territory Builder 결과에는 `territory_map_preview_assets/*.js`가 같이 복사됨
- 코드상으로는 CRM / Sandbox / Territory / Prescription / Total Valid 5종 생성 가능
- 실제 저장된 HTML은 회사별 마지막 실행 시점에 따라 일부만 있을 수 있음

### `common/`

공통 설정과 회사 런타임 유틸입니다.

- [company_runtime.py](/C:/sfe_master_ops/common/company_runtime.py)
  - 회사 코드 기준 경로 생성
- [company_profile.py](/C:/sfe_master_ops/common/company_profile.py)
  - 회사별 raw 파일 위치와 adapter 설정을 묶어서 관리
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
  - `crm_analysis_preview.html`
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
  - `sandbox_report_preview.html`

즉 Builder는 `표현 단계`이고, 계산은 앞단 모듈에 둡니다.

추가 메모:
- Territory Builder payload는 기본 화면에서 전체 병원 좌표를 다 싣지 않습니다.
- 기본값은 `담당자 미선택`이고, 담당자를 고르면 해당 담당자용 `catalog asset`과 선택 월용 `route asset`만 읽습니다.
- `total_valid_preview.html`은 Builder 단계에서 별도로 생성됩니다.
- 회사별 현재 저장 상태는 다릅니다.
- `daon_pharma`는 Builder 5종 저장이 확인됩니다.
- `hangyeol_pharma`는 현재 Builder 3종 저장이 확인됩니다.

## 현재 UI 기준 흐름

### 데이터 어댑터 탭

- raw 파일 업로드
- 같은 파일 중복 업로드 허용
- 고급 설정은 접힘 상태

### 파이프라인 탭

- 실행모드 선택
- 실행 전 반영 파일 확인
- 실제 파이프라인 실행

이 단계에서 OPS는 `무엇을 계산하느냐`보다
`지금 상태에서 다음으로 넘길 수 있느냐`를 보는 역할입니다.

### 분석 인텔리전스 탭

- 차트 중심이 아니라 산출물 검증 탭
- xlsx/csv/json 미리보기
- 단계 배지 표시
- 파일 다운로드

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

통합 보고서:
- `total_valid_preview.html`
- 생성된 개별 HTML을 한 화면에서 묶어 보는 허브
- 사이드바에는 4개 보고서가 항상 보이고
- 생성 안 된 것은 비활성 표시

즉 통합 보고서도 OPS가 새 계산을 하는 곳이 아니라,
최종 템플릿 결과를 확인하는 관제 화면에 가깝습니다.

주의:
- 위 목록은 코드 기준 생성 가능 목록입니다.
- 실제 폴더에 저장된 결과는 회사별 마지막 실행 상태를 기준으로 달라질 수 있습니다.

## 현재 빠진 것

- WebSlide 기능은 제거됨
- 통합 보고서는 슬라이드 생성기가 아니라 HTML 허브 역할만 함
- LLM 자동 인사이트 생성은 아직 연결 안 됨
