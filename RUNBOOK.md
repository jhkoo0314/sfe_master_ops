# SFE OPS RUNBOOK

작성일: 2026-03-10

## 1. 기본 원칙

```text
원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder
```

운영 점검 단계에서는 `실행모드`를 고르고 필요한 raw만 넣어 검증합니다.

여기서 OPS 역할은:

- 직접 계산
  - 아님
- 중간 매핑/품질 검증
  - 맞음
- 다음 단계 전달 판단
  - 맞음

즉 OPS는 `중앙 운영 통제실`처럼 동작합니다.

## 2. 실행 전 준비

### 2-1. 의존성 설치

```bash
uv sync
```

### 2-2. API 실행

```bash
uv run uvicorn ops_core.main:app --reload --host 0.0.0.0 --port 8000
```

### 2-3. 운영 콘솔 실행

```bash
uv run streamlit run ui/ops_console.py --server.port 8501
```

## 3. 운영 콘솔 사용 순서

1. 사이드바에서 `회사 코드` 입력
2. 필요하면 `회사 이름` 입력
3. `실행모드` 선택
4. 데이터 어댑터 탭에서 raw 파일 업로드
5. 파이프라인 탭에서 `실행 전 반영 파일 확인`
6. `파이프라인 실행`
7. 분석 인텔리전스 탭에서 산출물 확인
8. 결과물 빌더 탭에서 HTML 열기/다운로드

## 4. 실행모드 설명

### `CRM -> Sandbox`

- CRM과 실적/목표를 묶어 Sandbox 분석까지 확인

### `Sandbox -> HTML`

- Sandbox 결과를 기준으로 HTML 보고서 생성 확인

### `Sandbox -> Territory`

- Sandbox 결과를 Territory로 넘겨 지도 결과 확인

### `CRM -> PDF`

- CRM과 Prescription 흐름 추적 결과 확인

### `CRM -> Sandbox -> Territory`

- CRM부터 Territory까지 연결 흐름 점검

### `통합 실행`

- CRM
- Prescription
- Sandbox
- Territory
- Builder

를 한 번에 실행합니다.

## 5. 업로드 파일 기준

### CRM 패키지

- `CRM 활동 원본`
- `담당자 / 조직 마스터`
- `거래처 / 병원 담당 배정`
- `CRM 규칙 / KPI 설정`

### 기타

- `실적(매출) 데이터`
- `목표 데이터`
- `Prescription 데이터`

중요:

- 같은 파일을 여러 항목에 올려도 허용됩니다.
- 업로드만 했을 때는 세션에만 있고, 실행 시 실제 회사 폴더에 반영됩니다.

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

## 7. 주요 산출물

### 정규화 결과

- `data/ops_standard/{company_key}/...`

### 검증 결과

- `data/ops_validation/{company_key}/crm/...`
- `data/ops_validation/{company_key}/prescription/...`
- `data/ops_validation/{company_key}/sandbox/...`
- `data/ops_validation/{company_key}/territory/...`

### Builder 결과

- `crm_coaching_preview.html`
- `sandbox_report_preview.html`
- `territory_map_preview.html`
- `prescription_flow_preview.html`
- `total_valid_preview.html`

## 8. 처방 보고서 운영 메모

- 미리보기 HTML은 경량화된 버전입니다.
- 전체 원본은 엑셀 다운로드로 확인합니다.
- 빌더 탭에서 처방 보고서를 고르면 원본 다운로드 버튼도 같이 보입니다.

## 9. 실행 이력

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

## 10. 문제 해결

### 사이드바 카드가 안 뜰 때

- 통합 실행을 다시 한 번 돌립니다.
- `total_valid_preview.html`이 최신인지 확인합니다.

### 보고서가 비활성일 때

- 해당 HTML이 아직 생성되지 않은 상태입니다.
- 관련 실행모드를 먼저 돌립니다.

### Territory가 WARN일 때

- 현실 raw 데이터에서 일부 연결 누락이나 좌표 품질 이슈가 있을 수 있습니다.
- 전체 파이프라인 실패와는 별도로 해석해야 합니다.

### Prescription HTML이 느릴 때

- 미리보기는 줄였지만 여전히 데이터량이 큽니다.
- 원본 분석은 다운로드 파일로 보는 것이 더 안전합니다.
