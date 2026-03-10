# SFE OPS 구조 문서

작성일: 2026-03-10

## 핵심 흐름

```text
원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder
```

이 프로젝트는 `완전 무설정 범용 제품`보다는  
`회사별로 얇게 커스텀 가능한 공통 틀`에 가깝습니다.

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

### `modules/`

실제 분석을 수행하고 Result Asset을 만드는 층입니다.

- `modules/crm/`
- `modules/prescription/`
- `modules/sandbox/`
- `modules/territory/`
- `modules/builder/`

### `ops_core/`

OPS 판단과 파이프라인 실행을 담당합니다.

- `ops_core/main.py`
- `ops_core/api/`
- `ops_core/workflow/`

### `result_assets/`

모듈끼리 주고받는 표준 결과 형식입니다.

- `crm_result_asset.py`
- `prescription_result_asset.py`
- `sandbox_result_asset.py`
- `territory_result_asset.py`
- `html_builder_result_asset.py`

### `ui/`

운영 콘솔입니다.

- [ops_console.py](/C:/sfe_master_ops/ui/ops_console.py)
  - Streamlit 진입점
- [console_shared.py](/C:/sfe_master_ops/ui/console_shared.py)
  - 공통 상태, 공통 유틸, 산출물 처리
- [console_sidebar.py](/C:/sfe_master_ops/ui/console_sidebar.py)
  - 사이드바 렌더링
- [console_tabs.py](/C:/sfe_master_ops/ui/console_tabs.py)
  - 데이터 어댑터 / 파이프라인 / 분석 인텔리전스 / 결과물 빌더 탭

즉 예전처럼 `ops_console.py` 한 파일에 몰아넣지 않고 분리된 상태입니다.

### `templates/`

실제 HTML 보고서 템플릿입니다.

- [report_template.html](/C:/sfe_master_ops/templates/report_template.html)
- [crm_coaching_template.html](/C:/sfe_master_ops/templates/crm_coaching_template.html)
- [Spatial_Preview_260224.html](/C:/sfe_master_ops/templates/Spatial_Preview_260224.html)
- [prescription_flow_template.html](/C:/sfe_master_ops/templates/prescription_flow_template.html)
- [total_valid_templates.html](/C:/sfe_master_ops/templates/total_valid_templates.html)

참고:

- `hh.html`, `hh_builder_template.js`, `hhb.js`는 통합 보고서 디자인 복구 참고용 템플릿 자산입니다.

### `scripts/`

정규화/검증/Builder 생성 스크립트입니다.

대표 파일:

- `normalize_hangyeol_crm_source.py`
- `normalize_hangyeol_sandbox_source.py`
- `normalize_hangyeol_prescription_source.py`
- `validate_hangyeol_crm_with_ops.py`
- `validate_hangyeol_prescription_with_ops.py`
- `validate_hangyeol_sandbox_with_ops.py`
- `validate_hangyeol_territory_with_ops.py`
- `validate_hangyeol_builder_with_ops.py`
- `validate_hangyeol_full_pipeline.py`

이름은 `hangyeol`이 남아 있지만,
현재는 `company_runtime.py`를 통해 회사 코드 기준 동적 경로를 사용합니다.

### `common/`

공통 설정과 회사 런타임 유틸입니다.

- [company_runtime.py](/C:/sfe_master_ops/common/company_runtime.py)
  - 회사 코드 기준 경로 생성
- `config.py`
- `exceptions.py`
- `types.py`

### `data/`

실제 운영 검증 데이터가 쌓이는 곳입니다.

```text
data/
├── company_source/      # 회사별 원천데이터
├── ops_standard/        # 정규화 결과
├── ops_validation/      # 검증 결과 + HTML
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

## 현재 UI 기준 흐름

### 데이터 어댑터 탭

- raw 파일 업로드
- 같은 파일 중복 업로드 허용
- 고급 설정은 접힘 상태

### 파이프라인 탭

- 실행모드 선택
- 실행 전 반영 파일 확인
- 실제 파이프라인 실행

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

## 현재 생성되는 보고서

### 개별 보고서

- CRM 행동 코칭 보고서
- Sandbox 성과 보고서
- Territory 권역 지도 보고서
- PDF 처방흐름 보고서

### 통합 보고서

- `total_valid_preview.html`
- 생성된 개별 HTML을 한 화면에서 묶어 보는 허브
- 사이드바에는 4개 보고서가 항상 보이고
- 생성 안 된 것은 비활성 표시

## 현재 빠진 것

- WebSlide 기능은 제거됨
- 통합 보고서는 슬라이드 생성기가 아니라 HTML 허브 역할만 함
- LLM 자동 인사이트 생성은 아직 연결 안 됨
