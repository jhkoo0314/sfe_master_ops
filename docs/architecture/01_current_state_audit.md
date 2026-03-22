# Current State Audit (Sales Data OS Alignment)

작성일: 2026-03-16

## 1) 현재 구조 요약

현재 저장소는 기능적으로는 이미 다음 흐름으로 동작합니다.

`raw data -> Adapter -> Module Service/KPI Engine -> Result Asset -> OPS 평가 -> Builder 렌더링`

핵심 폴더 기준:

- `adapters/`: 회사 raw를 표준 스키마로 정규화
- `modules/`: 모듈별 계산/집계와 payload 조립
- `modules/kpi/`: 공식 KPI 계산 엔진
- `modules/validation/`: Validation/Orchestration 기본 패키지
- `ops_core/`: 호환 유지용 Validation/Orchestration 패키지
- `result_assets/`: 모듈 간 전달 계약 포맷
- `modules/builder/`, `templates/`: HTML 렌더링
- `ui/`: Streamlit 운영 콘솔
- `scripts/`: normalize/validate 파이프라인 실행

## 2) 모듈 책임(실제 동작 기준)

### Data Layer
- `data/company_source/*` raw 입력 저장
- `data/public/*` 공통 기준 데이터

### Adapter Layer
- `adapters/crm`, `adapters/sandbox`, `adapters/prescription`, `adapters/territory`
- raw를 표준 필드로 변환

### Core Engine Layer
- `modules/kpi/crm_engine.py`
- `modules/kpi/sandbox_engine.py`
- `modules/kpi/territory_engine.py`
- `modules/kpi/prescription_engine.py`
- `modules/*/service.py`는 엔진 호출 + 결과 조립

### Validation / Orchestration Layer (OPS)
- `modules/validation/api/*_router.py`: Result Asset 품질/매핑 검증
- `modules/validation/workflow/orchestrator.py`: 단계 실행 통제
- `modules/validation/workflow/schemas.py`: 실행 계약 스키마

### Intelligence Layer
- `modules/sandbox`, `modules/territory`, `modules/prescription`
- 현재 RADAR 구현 파일은 없음 (구조 준비 필요)

### Presentation Layer
- `modules/builder/service.py`, `modules/builder/schemas.py`
- `templates/*.html`
- Builder는 payload 주입/렌더링 담당

## 3) KPI 계산 위치 점검

KPI 계산 소스는 `modules/kpi/*`로 수렴되어 있습니다.

- CRM: `modules/crm/service.py` -> `modules.kpi.crm_engine.compute_crm_kpi_bundle`
- Sandbox: `modules/sandbox/service.py` -> `modules.kpi.sandbox_engine.*`
- Territory: `modules/territory/builder_payload.py` -> `modules.kpi.build_territory_builder_context`
- Prescription: `modules/prescription/builder_payload.py` -> `modules.kpi.build_prescription_builder_context`

확인 결과:
- Builder에서 KPI 재계산 로직은 확인되지 않음
- Sandbox에서 CRM KPI 재계산 금지 규칙 관련 주석/스키마 문구 존재

## 4) Validation 위치

- API 단위 평가: `modules/validation/api/crm_router.py`, `prescription_router.py`, `sandbox_router.py`, `territory_router.py`
- 파이프라인 제어: `modules/validation/api/pipeline_router.py`, `modules/validation/workflow/orchestrator.py`
- 실행 스크립트: `scripts/validate_*_with_ops.py`, `scripts/validate_full_pipeline.py`

## 5) Rendering 위치

- Builder 서비스: `modules/builder/service.py`
- Builder 스키마: `modules/builder/schemas.py`
- 템플릿: `templates/report_template.html`, `crm_analysis_template.html`, `territory_optimizer_template.html`, `prescription_flow_template.html`, `total_valid_templates.html`
- 콘솔 결과 탭: `ui/console_tabs.py`

## 6) Sales Data OS 관점 naming 불일치

우선 정렬이 필요한 주요 지점:

- 루트 문서 제목/소개가 `SFE OPS` 중심 표현
  - `README.md`, `RUNBOOK.md`, `STRUCTURE.md`, `docs/README.md`
- UI 라벨의 `SFE MASTER OPS`, `Operation System Engine`, `OPS 파이프라인 실행`, `OPS 분석 보고서`
  - `ui/ops_console.py`, `ui/console_display.py`, `ui/console_sidebar.py`, `ui/console_tabs.py`
- API/주석에서 OPS를 시스템 중심으로 읽히는 문장
  - `modules/validation/main.py`, `modules/validation/workflow/*.py`, `modules/validation/api/pipeline_router.py`
- Builder 스키마/서비스 설명의 OPS 중심 문구
  - `modules/builder/service.py`, `modules/builder/schemas.py`
- 템플릿 라벨의 `SFE OPS`, `LIVE OPS`
  - `templates/total_valid_templates.html`, `templates/crm_analysis_template.html`, `templates/prescription_flow_template.html`

## 7) Rename 위험 구간 vs 안전 구간

### 위험 구간 (이번 작업에서 보류)
- 폴더명/패키지명 변경: `ops_core`, `ops_standard`, `ops_validation`
- API 경로 변경: `/ops/*`
- 스크립트 파일명 변경: `validate_*_with_ops.py`
- 런타임 env key 변경: `OPS_*` 환경변수

이 구간은 import/API/운영 자동화에 직접 영향이 있어 즉시 rename 시 리스크가 큽니다.

### 안전 구간 (이번 작업에서 적용)
- 아키텍처 문서 신설
- README/RUNBOOK/STRUCTURE 개념 설명 정렬
- 주석/docstring 책임 설명 정렬
- 콘솔/템플릿 텍스트 라벨 정렬

## 8) 결론

코드 구조 자체는 이미 `Sales Data OS` 레이어 모델과 상당 부분 맞아 있습니다.
현재 핵심 과제는 대규모 코드 변경이 아니라, 시스템 정의/문서/UI/주석을 `Sales Data OS` 기준으로 일관 정렬하는 것입니다.
