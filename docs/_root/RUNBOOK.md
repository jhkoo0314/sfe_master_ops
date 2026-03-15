# SFE OPS RUNBOOK

작성일: 2026-03-11

## 1. 기본 원칙

```text
원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder
```

운영 점검 단계에서는 `실행모드`를 고르고 필요한 raw만 넣어 검증합니다.

OPS 역할은 이렇게 이해하면 됩니다.

- 직접 계산 엔진
  - 아님
- 중간 매핑/품질 검증
  - 맞음
- 다음 단계 전달 판단
  - 맞음

즉 OPS는 `중앙 운영 통제실`처럼 동작합니다.

현재 운영 범위 한 줄 요약:
- CRM / Prescription / Sandbox / Territory / Builder는 실행 가능
- Builder는 코드상 보고서 5종 생성 가능
- 실제 저장된 보고서 수는 회사별 마지막 실행 상태에 따라 다를 수 있음

## 2. 실행 전 준비

의존성 설치:

```bash
uv sync
```

API 실행:

```bash
uv run uvicorn ops_core.main:app --reload --host 0.0.0.0 --port 8000
```

운영 콘솔 실행:

```bash
uv run streamlit run ui/ops_console.py --server.port 8501
```

참고:
- 운영 콘솔은 현재 `대시보드 / 데이터 어댑터 / 파이프라인 / 분석 인텔리전스 / 결과물 빌더` 5개 탭으로 동작합니다.

## 3. 운영 콘솔 사용 순서

1. 사이드바에서 `회사 코드` 입력
2. 필요하면 `회사 이름` 입력
3. `실행모드` 선택
4. 데이터 어댑터 탭에서 raw 파일 업로드
5. 파이프라인 탭에서 `실행 전 반영 파일 확인`
6. `파이프라인 실행`
7. 분석 인텔리전스 탭에서 정규화/검증 산출물 확인
8. 결과물 빌더 탭에서 HTML 열기/다운로드

## 4. 실행모드 설명

`CRM -> Sandbox`
- CRM과 실적/목표를 묶어 Sandbox 분석까지 확인

`CRM -> Territory`
- CRM 활동을 Territory 활동 표준으로 바꾸고, 내부 성과 준비 단계를 거쳐 권역 분석까지 바로 확인

`Sandbox -> HTML`
- Sandbox 결과를 기준으로 HTML 보고서 생성 확인

`Sandbox -> Territory`
- Sandbox 결과를 Territory로 넘겨 지도 결과 확인

`CRM -> PDF`
- CRM과 Prescription 흐름 추적 결과 확인

`CRM -> Sandbox -> Territory`
- CRM부터 Territory까지 연결 흐름 점검

`통합 실행`
- CRM
- Prescription
- Sandbox
- Territory
- Builder

를 한 번에 실행합니다.

주의:
- `통합 실행`은 코드상으로 `crm_analysis_preview.html`, `sandbox_report_preview.html`, `territory_map_preview.html`, `prescription_flow_preview.html`, `total_valid_preview.html`까지 연결되는 흐름입니다.
- 다만 실제 저장은 회사별 입력 상태와 마지막 실행 결과에 따라 일부만 남아 있을 수 있습니다.

## 5. 업로드 파일 기준

CRM 패키지:
- `CRM 활동 원본`
- `담당자 / 조직 마스터`
- `거래처 / 병원 담당 배정`
- `CRM 규칙 / KPI 설정`

기타:
- `실적(매출) 데이터`
- `목표 데이터`
- `Prescription 데이터`

중요:
- 같은 파일을 여러 항목에 올려도 허용됩니다.
- 업로드만 했을 때는 세션에만 있고, 실행 시 실제 회사 폴더에 반영됩니다.
- 업로드하지 않았더라도 해당 회사 폴더에 기존 source 파일이 있으면 그 파일을 그대로 사용합니다.
- 화면에서 `권장`으로 보이는 파일도 회사 폴더에 기존 파일이 없으면 실제 실행에는 필요할 수 있습니다.

## 6. 회사별 저장 구조

모든 결과는 회사 코드 기준으로 분리됩니다.

```text
data/company_source/{company_key}/
data/ops_standard/{company_key}/
data/ops_validation/{company_key}/
```

예:

```text
data/company_source/daon_pharma/
data/ops_standard/daon_pharma/
data/ops_validation/daon_pharma/
```

원천 파일 기본 이름도 이제 공통 규칙으로 맞춥니다.

- `crm/crm_activity_raw.xlsx`
- `company/company_assignment_raw.xlsx`
- `company/account_master.xlsx`
- `sales/sales_raw.xlsx`
- `target/target_raw.xlsx`
- `company/fact_ship_raw.csv`
- `company/rep_master.xlsx`

## 6-1. 실행 스크립트 기준

현재 운영에서 먼저 보는 실행 파일은 회사명 없는 공통 스크립트입니다.

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

회사별 raw 파일 위치와 어댑터 설정은 [company_profile.py](/C:/sfe_master_ops/common/company_profile.py)에서 가져옵니다.

참고:
- raw 샘플 데이터가 필요할 때는 `scripts/generate_source_raw.py`를 먼저 보고, 실제 회사별 생성은 profile에 등록된 스크립트가 실행됩니다.
- 회사별 raw 생성 구현 파일은 `scripts/raw_generators/` 아래에 둡니다.

## 7. 주요 산출물

정규화 결과:
- `data/ops_standard/{company_key}/...`

검증 결과:
- `data/ops_validation/{company_key}/crm/...`
- `data/ops_validation/{company_key}/prescription/...`
- `data/ops_validation/{company_key}/sandbox/...`
- `data/ops_validation/{company_key}/territory/...`

모듈별 Builder payload:
- `crm/crm_builder_payload.json`
- `crm/crm_builder_payload_assets/*.js`
- `prescription/prescription_builder_payload.json`
- `territory/territory_builder_payload.json`
- Sandbox는 `sandbox_result_asset.json` 안의 `dashboard_payload.template_payload` 사용
- `sandbox/sandbox_template_payload_assets/*.js`

Territory 정규화 결과:
- `data/ops_standard/{company_key}/territory/ops_territory_activity.xlsx`

Builder 결과:
- `data/ops_validation/{company_key}/builder/crm_analysis_preview.html`
- `data/ops_validation/{company_key}/builder/crm_analysis_preview_assets/*.js`
- `data/ops_validation/{company_key}/builder/sandbox_report_preview.html`
- `data/ops_validation/{company_key}/builder/sandbox_report_preview_assets/*.js`
- `data/ops_validation/{company_key}/builder/territory_map_preview.html`
- `data/ops_validation/{company_key}/builder/territory_map_preview_assets/*.js`
- `data/ops_validation/{company_key}/builder/prescription_flow_preview.html`
- `data/ops_validation/{company_key}/builder/total_valid_preview.html`

추가로 같이 저장되는 것:
- `*_input_standard.json`
- `*_payload_standard.json`
- `*_result_asset.json`

## 8. Builder 운영 메모

- Builder는 raw를 읽지 않습니다.
- Builder는 모듈이 먼저 만든 payload만 읽습니다.
- 그래서 템플릿이 바뀌면 Builder보다 먼저 `모듈 payload`를 같이 맞춰야 합니다.
- Territory 보고서도 이제 Builder 안에서 계산하지 않고 `territory_builder_payload.json`을 읽습니다.
- Sandbox 보고서는 `sandbox_result_asset.json` 안의 payload를 그대로 쓰되, 무거운 지점 상세는 `manifest + branch asset` 구조로 분리됩니다.
- Sandbox 보고서는 첫 화면에 요약만 먼저 열고, 지점을 고를 때만 해당 지점 asset을 읽습니다.
- Territory payload는 `manifest + 분리 asset` 구조입니다.
- 기본 화면은 `담당자 미선택` 상태로 시작하고, 담당자를 고른 뒤 해당 담당자 asset과 선택 월 asset만 읽습니다.
- `total_valid_preview.html`은 개별 HTML을 한 화면에서 묶어 보여주는 허브입니다.
- 통합 보고서도 새 계산을 하지 않고, 이미 만든 HTML을 연결해서 보여주는 역할입니다.

## 9. 처방 보고서 운영 메모

- 미리보기 HTML은 경량화된 버전입니다.
- 전체 원본은 엑셀 다운로드로 확인합니다.
- 빌더 탭에서 처방 보고서를 고르면 원본 다운로드 버튼도 같이 보입니다.

## 10. 실행 이력

운영 콘솔 실행 이력은 여기에 저장됩니다.

```text
data/ops_validation/{company_key}/pipeline/console_run_history.jsonl
```

여기에는 들어갑니다.

- 실행 시각
- 실행모드
- 단계별 결과
- 어떤 업로드 파일을 사용했는지
- 실제 어느 경로에 반영했는지

현재 확인된 예시:
- `daon_pharma`는 Builder 보고서 5종 저장이 확인됩니다.
- `hangyeol_pharma`는 현재 Builder 보고서 5종 저장이 확인됩니다.

## 11. 문제 해결

사이드바 카드가 안 뜰 때:
- 통합 실행을 다시 한 번 돌립니다.
- `total_valid_preview.html`이 최신인지 확인합니다.
- 생성 대상 HTML 자체가 없는 경우에는 카드가 비활성처럼 보일 수 있습니다.

보고서가 비활성일 때:
- 해당 HTML이 아직 생성되지 않은 상태입니다.
- 관련 실행모드를 먼저 돌립니다.
- 회사별 마지막 실행 결과가 달라서 어떤 회사는 5종, 어떤 회사는 일부만 있을 수 있습니다.

Territory가 WARN일 때:
- 현실 raw 데이터에서 일부 연결 누락이나 좌표 품질 이슈가 있을 수 있습니다.
- 전체 파이프라인 실패와는 별도로 해석해야 합니다.
- 현재 Territory는 `Sandbox result asset`을 중심으로 돌고, CRM 날짜 동선은 `ops_territory_activity.xlsx` 표준 파일로 붙는 흐름입니다.

Territory 지도가 다시 무거워졌을 때:
- `territory_builder_payload.json`이 최신인지 먼저 확인합니다.
- `territory_builder_payload_assets/`와 `builder/territory_map_preview_assets/`가 같이 생겼는지 확인합니다.
- Territory와 Builder를 순서대로 다시 실행합니다.

Prescription HTML이 느릴 때:
- 미리보기는 줄였지만 여전히 데이터량이 큽니다.
- 원본 분석은 다운로드 파일로 보는 것이 더 안전합니다.

Builder에서 Territory만 빠질 때:
- 먼저 `data/ops_standard/{company_key}/territory/ops_territory_activity.xlsx`가 생겼는지 확인합니다.
- 먼저 Territory 검증이 돌아서 `territory_builder_payload.json`이 생겼는지 확인합니다.
- 그 다음 Builder를 다시 실행합니다.
