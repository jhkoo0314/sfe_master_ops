# SFE OPS 전체 구현계획 TODO

작성일: 2026-03-10
기준 문서: `00_SFE_OPS_Master_Document_Index.md` ~ `08_HTML_Builder_Implementation_Plan.md`, `AGENTS.md`

---

## 핵심 원칙 (항상 먼저 확인)

```
원천데이터 -> Adapter -> Module -> Result Asset -> OPS
```

- **중심은 OPS Engine** (Sandbox가 아님)
- **Raw는 OPS로 바로 보내지 않는다**
- **Adapter가 항상 먼저다** (adapter-first)
- **Result Asset 중심으로 연결한다**
- **범용 규칙이 회사 맞춤보다 먼저다**

---

## Phase 0. 기준 문서 통합 (완료)

> 목적: 앞으로 무엇을 기준으로 설명하고 구현해야 하는지 하나로 정리

- [x] `00_SFE_OPS_Master_Document_Index.md` 작성
- [x] `01_SFE_OPS_Master_PRD.md` 작성
- [x] `02_SFE_OPS_Integrated_Plan.md` 작성
- [x] `03_SFE_OPS_Technical_Stack.md` 작성
- [x] `04_Behavior_CRM_Implementation_Plan.md` 작성
- [x] `05_SFE_Sandbox_Implementation_Plan.md` 작성
- [x] `06_Territory_Optimizer_Implementation_Plan.md` 작성
- [x] `07_Prescription_Data_Flow_Implementation_Plan.md` 작성
- [x] `08_HTML_Builder_Implementation_Plan.md` 작성
- [x] `AGENTS.md` 작성

**Phase 0 완료 판단:** 기준 문서 세트가 단일 체계로 정리되어 있고, 충돌 없이 읽힌다.

---

## Phase 1. 프로젝트 기반 환경 구성

> 목적: 코드를 작성하기 전에 프로젝트 골격과 실행 환경을 먼저 잡는다.

### 1-1. 저장소 구조 설계

- [x] 폴더 구조 초안 작성 (`/adapters`, `/modules`, `/ops_core`, `/result_assets`, `/tests`, `/ui`)
- [x] 각 폴더의 역할과 책임 명시 → `STRUCTURE.md`
- [x] 공통 예외 클래스 정의 → `common/exceptions.py`
- [x] 공통 타입/상수 정의 → `common/types.py`

### 1-2. 기술 스택 환경 세팅

- [x] `uv` 기반 프로젝트 초기화 → `pyproject.toml`
- [x] 핵심 의존성 추가 (fastapi, uvicorn, pydantic v2, polars, openpyxl, fastexcel, pytest, streamlit, supabase)
- [x] `.env` 구성 템플릿 → `.env.example`
- [x] `pytest` 기본 설정 → `pyproject.toml` 내 설정
- [x] `RUNBOOK.md` 작성 (로컬 실행 명령 정리)
- [x] `common/config.py` 작성 (pydantic-settings 기반 설정 관리)
- [x] `.gitignore` 작성

### 1-3. Supabase 기반 스키마 초안

- [x] `ops_run_log` 테이블 설계 (실행 이력)
- [x] `ops_asset_meta` 테이블 설계 (Result Asset 메타 저장)
- [x] `ops_connection_log` 테이블 설계 (모듈 간 연결 판단 이력)
- [x] Supabase 초기 마이그레이션 스크립트 → `migrations/001_initial_schema.sql`

---

## Phase 2. Behavior CRM 모듈

> 목적: 병원/지점/담당자 공통축을 먼저 안정화하고, 후속 모듈이 재사용할 출발 자산을 만든다.

### 2-1. hospital_master 설계 및 구현

- [x] 공공 병원 기준 데이터 포맷 확인 (건강보험심사평가원, HIRA 등)
- [x] `hospital_master` 스키마 정의 (Pydantic 모델)
  - 핵심 키: `hospital_id`, `hospital_name`, `hospital_type`, `region_key`
- [x] 공공 병원 raw -> `hospital_master` Adapter 구현
- [x] `hospital_master` 로컬 파일 기반 저장 및 로드 기능 구현
- [x] `hospital_master` Adapter 단위 테스트 작성

### 2-2. company_master_standard 설계 및 구현

- [x] 회사 마스터 데이터 입력 포맷 정의 (Excel 기준)
- [x] `company_master_standard` 스키마 정의 (Pydantic 모델) → `modules/crm/schemas.py`
- [x] 회사 마스터 raw → `company_master_standard` Adapter 구현 → `adapters/crm/company_master_adapter.py`
- [x] `hospital_id` ↔ `branch_id` ↔ `rep_id` 정합성 검증 로직 구현 → `validate_key_integrity()`
- [x] Adapter 단위 테스트 작성 → TestCompanyMasterAdapter

### 2-3. crm_standard_activity 설계 및 구현

- [x] CRM raw 활동 데이터 포맷 정의 (Excel/CSV 기준)
- [x] `crm_standard_activity` 스키마 정의 (Pydantic 모델)
  - 핵심 키: `hospital_id`, `rep_id`, `activity_date`, `activity_type`, `metric_month`
- [x] CRM raw -> `crm_standard_activity` Adapter 구현 (Polars 기반)
- [x] fixture 데이터 작성 (실데이터 없을 때 사용)
- [x] Adapter 단위 테스트 작성

### 2-4. crm_result_asset 생성 및 OPS 연결

- [x] `crm_result_asset` 스키마 정의 (Pydantic 모델) → `result_assets/crm_result_asset.py`
- [x] `crm_standard_activity` → `crm_result_asset` 생성기 구현 → `modules/crm/service.py`
- [x] OPS Core API: CRM Result Asset 평가 엔드포인트 (`POST /ops/crm/evaluate`) → `ops_core/api/crm_router.py`
- [x] OPS 평가 기준: 5개 품질 게이트 (PASS/WARN/FAIL)
- [x] 통합 테스트 작성 → `tests/test_crm/test_crm_flow.py`
- [x] `ops_core/main.py` FastAPI 앱 진입점 작성

**Phase 2 완료 판단:**

- `hospital_id`, `branch_id`, `rep_id` 축이 fixture 기반으로 설명 가능하다.
- `crm_result_asset`이 생성되고 OPS가 평가할 수 있다.
- Prescription과 Sandbox가 재사용할 수 있는 공통 축이 문서로 설명된다.

---

## Phase 3. Prescription Data Flow 모듈

> 목적: 실데이터 없이도 범용 흐름 검증 규칙을 먼저 세운다. (common-key-first, adapter-first)

### 3-1. 범용 키 규칙 설계 (구현 전 필수 선행)

- [x] `pharmacy_id` 범용 규칙 설계 문서 작성
  - 약국 raw를 보고 공통 ID 부여 기준 정리 (약국명 + 지역 + 우편번호 등)
- [x] `wholesaler_id` 범용 규칙 설계 문서 작성
  - 도매 raw를 보고 공통 ID 부여 기준 정리
- [x] `도매 -> 약국 -> 병원` 연결 규칙 설계 문서 작성
  - `lineage_key` 생성 규칙 정의

### 3-2. prescription_master 설계 및 구현

- [x] `prescription_master` 스키마 정의 (Pydantic 모델)
  - 핵심 키: `hospital_id` (CRM 재사용), `pharmacy_id`, `wholesaler_id`, `product_id`, `ingredient_code`
- [x] 기준 데이터 Adapter 구현 (공공 약가/품목 기준 데이터 등)
- [x] fixture 데이터 작성

### 3-3. company_prescription_standard 설계 및 구현

- [x] 회사 Prescription raw 포맷 정의 (도매 출고, 약국 구입 데이터)
- [x] `company_prescription_standard` 스키마 정의
- [x] 회사 raw -> `company_prescription_standard` Adapter 구현 (Polars 기반)

### 3-4. prescription_standard_flow 설계 및 구현

- [x] `prescription_standard_flow` 스키마 정의
  - 핵심: 도매->약국->병원 연결 레코드 구조, `lineage_key` 포함
- [x] `company_prescription_standard` -> `prescription_standard_flow` 변환 로직 구현
- [x] 미매핑 추적 로직 구현 (`gap_summary` 생성)

### 3-5. prescription_result_asset 생성 및 OPS 연결

- [x] `prescription_result_asset` 스키마 정의 (Pydantic 모델)
  - 포함 항목: `lineage_summary`, `reconciliation_summary`, `validation_gap_summary`, `mapping_quality_summary`
- [x] Result Asset 생성기 구현
- [x] OPS Core API: Prescription Result Asset 평가 엔드포인트 구현 (`POST /ops/prescription/evaluate`)
- [x] 통합 테스트 작성

**Phase 3 완료 판단:**

- `pharmacy_id`, `wholesaler_id` 범용 규칙이 fixture 기반으로 검증된다.
- `prescription_result_asset`이 생성되고 OPS가 평가할 수 있다.
- Sandbox 재사용 연결 경로가 문서로 설명된다.

---

## Phase 4. SFE Sandbox 모듈

> 목적: OPS가 허용한 자산 조합을 받아 통합 분석 자산을 만드는 엔진을 정비한다. (허브가 아닌 분석엔진)

### 4-1. sandbox_reference_master 설계

- [x] Sandbox가 수신할 수 있는 자산 목록 및 조합 규칙 정의
  - 기본 조합: `crm_result_asset` + 매출 + 목표
  - 선택 조합: `+ prescription_result_asset`
- [x] `sandbox_reference_master` 스키마 정의 (Pydantic 모델)
- [x] fixture 데이터 작성

### 4-2. sandbox_domain_standard 설계 및 구현

- [x] 도메인별 입력 규격 정리 (CRM 도메인, 실적 도메인, 목표 도메인, Prescription 도메인)
- [x] `sandbox_domain_standard` 스키마 정의
- [x] 각 도메인별 표준화 Adapter 구현 (Polars 기반)

### 4-3. sandbox_input_standard 설계 및 구현

- [x] 시나리오별 입력 조합 규격 정의
- [x] `sandbox_input_standard` 스키마 정의
- [x] 시나리오 검증 로직 구현 (OPS가 허용한 조합인지 확인)

### 4-4. sandbox_result_asset 생성 및 OPS 연결

- [x] `sandbox_result_asset` 스키마 정의 (Pydantic 모델)
  - 포함 항목: `analysis_summary`, `dashboard_summary`, `domain_quality_summary`, `join_quality_summary`, `planned_handoff_candidates`
- [x] 시나리오별 분석 집계 로직 구현 (Polars 기반)
- [x] Result Asset 생성기 구현
- [x] 각 모듈 평가 엔드포인트 통합 (`/ops/{module}/evaluate`)
- [x] 파이프라인 오케스트레이터 구현 (`run_pipeline`)
- [x] `POST /ops/pipeline/run` 엔드포인트 구현
- [x] `GET /ops/pipeline/status` 전체 상태 요약
- [x] `GET /ops/diagram` 파이프라인 다이어그램
- [x] FAIL/WARN/PASS 별 흐름 제어 로직
- [x] 다음 모듈 handoff 자동 결정 로직
- [x] OPS Core API: Sandbox Result Asset 평가 엔드포인트 구현 (`POST /ops/sandbox/evaluate`)
  - 평가 항목: 자산 조합, 조인키 안정성, 후속 재사용 가능성
- [x] 통합 테스트 작성

**Phase 4 완료 판단:**

- 시나리오별 입력 조합이 `sandbox_input_standard`로 정리된다.
- `sandbox_result_asset`이 생성되고 OPS가 후속 연결 후보를 판단할 수 있다.
- Territory와 HTML Builder로의 handoff 경로가 문서로 설명된다.

---

## Phase 5. Territory Optimizer 모듈

> 목적: Sandbox 결과를 공간 실행 관점으로 재해석한다. (Sandbox 안정화 후 시작)

### 5-1. 사전 조건 확인 (Phase 4 완료 후 진행)

- [x] `hospital_id`, `branch_id`, `rep_id` 공통축 안정 확인
- [x] `sandbox_result_asset` 안정 확인
- [x] 권역/좌표 기준 데이터 확보 계획 수립

### 5-2. territory_reference_master 설계 및 구현

- [x] 권역/좌표 기준 정리 (시/군/구 단위, 좌표 체계)
- [x] `territory_reference_master` 스키마 정의 (Pydantic 모델)
  - 핵심 키: `territory_id`, `region_key`, `hospital_id` 연결 기준

### 5-3. territory_entity_standard 및 input_standard 설계

- [x] Sandbox 결과 + 권역 기준 연결 로직 구현
- [x] `territory_entity_standard` 스키마 정의
- [x] `territory_input_standard` 스키마 정의 및 구현

### 5-4. territory_result_asset 생성 및 OPS 연결

- [x] `territory_result_asset` 스키마 정의 (Pydantic 모델)
  - 포함 항목: `territory_summary`, `coverage_summary`, `optimization_summary`, `handoff_quality_summary`
- [x] 커버리지/동선/배치 효율 계산 로직 구현 (Polars 기반)
- [x] OPS Core API: Territory Result Asset 평가 엔드포인트 구현 (`POST /ops/territory/evaluate`)
- [x] 통합 테스트 작성

**Phase 5 완료 판단:**

- 권역 기준표가 정리되고 `territory_result_asset`이 생성된다.
- OPS가 Territory 자산을 평가하여 커버리지와 배치 효율을 판단할 수 있다.

---

## Phase 6. HTML Builder 모듈

> 목적: 모든 앞단 Result Asset을 사람이 읽는 보고 자산으로 변환하는 표현 계층을 완성한다.

### 6-1. builder_input_reference 설계

- [x] Builder가 수신할 수 있는 자산 목록 정의
  - CRM, Sandbox, Territory, Prescription 자산 포함
- [x] `builder_input_reference` 스키마 정의 (Pydantic 모델)
  - 핵심 메타: `source_module`, `asset_type`, `report_title`, `executive_summary`

### 6-2. 모듈별 Builder Input Adapter 구현

- [x] CRM Result Asset -> Builder Input Adapter
- [x] Sandbox Result Asset -> Builder Input Adapter
- [x] Territory Result Asset -> Builder Input Adapter
- [x] Prescription Result Asset -> Builder Input Adapter

### 6-3. builder_input_standard 및 payload_standard 설계

- [x] `builder_input_standard` 스키마 정의
- [x] `builder_payload_standard` 스키마 정의
  - 포함 항목: `report_title`, `executive_summary`, `section_cards`, `source_references`
- [x] 모듈별 Adapter 출력 -> `builder_payload_standard` 변환 로직 구현

### 6-4. HTML 보고 템플릿 및 Result Asset 설계

- [x] 기본 HTML 보고서 템플릿 작성 (모듈별 HTML + 통합 허브 기준)
- [x] 통합 HTML 허브 템플릿 작성 (`total_valid_templates.html`)
- [x] `html_builder_result_asset` 스키마 정의 (Pydantic 모델)
  - 포함 항목: `render_summary`, `report_payload_summary`, `template_reference`, `output_reference`
- [x] Builder 검증 스크립트 및 UI 레이어 연결 (`scripts/validate_builder_with_ops.py`, `ui/ops_console.py`)
- [x] 통합 테스트 작성

**Phase 6 완료 판단:**

- 여러 모듈의 Result Asset이 같은 표현 입력 구조로 변환된다.
- `html_builder_result_asset`이 생성되고 보고 자산이 출력된다.

---

## Phase 7. OPS Core API 완성 및 통합

> 목적: 개별 모듈 평가 API를 통합하고, 모듈 간 연결 판단 체계를 완성한다.

### 7-1. OPS Core API 통합

- [x] 모듈별 평가 API 통합 라우터 구성
- [x] 모듈 상태 조회 API (`GET /ops/status`)
- [x] 파이프라인 상태/흐름 조회 API (`GET /ops/pipeline/status`, `GET /ops/diagram`)
- [x] 콘솔 실행 이력 저장 구조 정리 (`console_run_history.jsonl`)

### 7-2. 품질 게이트 시스템 구현

- [x] 공통 품질 게이트 구조 설계 (pass/warn/fail 3단계)
- [x] 각 모듈별 품질 게이트 기준 구현
- [x] `reasoning_note` 자동 생성 로직 구현 (왜 pass/fail인지 설명)

### 7-3. 실행 이력 / 메타 저장 체계 정리

- [x] 콘솔 실행 이력 로컬 저장 연동 (`console_run_history.jsonl`)
- [x] 모듈별 요약 JSON 저장 경로 표준화
- [x] Result Asset / Builder 산출물 메타 저장 규칙 정리

### 7-4. 통합 시나리오 테스트

- [x] 공용 실행 엔진 기준 전체 파이프라인 검증 테스트 작성
- [x] 품질 게이트 fail / warn 흐름 제어 동작 테스트
- [x] fixture 기반 모듈별 통합 테스트 스위트 작성

---

## Phase 8. Streamlit 운영 콘솔 구현

> 목적: 비개발자 운영자가 파일 업로드/실행/결과 확인/다운로드를 할 수 있는 운영 콘솔을 만든다.

### 8-1. 공통 콘솔 레이아웃

- [x] 사이드바: 모듈 선택 및 현재 OPS 상태 표시
- [x] 메인 영역: 파일 업로드, 실행, 결과 미리보기, 다운로드
- [x] OPS 상태 대시보드 페이지 (모듈별 최종 실행 이력 및 품질 요약)

### 8-2. 모듈별 운영 화면

- [x] CRM 업로드 및 실행 화면
- [x] Prescription 업로드 및 실행 화면
- [x] Sandbox 시나리오 선택 및 실행 화면
- [x] Territory 실행 화면
- [x] HTML Builder 보고서 생성 및 다운로드 화면

### 8-3. 운영 콘솔 검증

- [x] 비개발자 기준 UX 검토 (업로드 -> 실행 -> 결과 확인 -> 다운로드 전 흐름)
- [x] 에러 메시지를 사람이 이해할 수 있는 언어로 출력되는지 확인

---

## 공통 작업 항목 (전 Phase 공통)

### 문서 관리 원칙

- [x] 각 Phase 완료 후 `AGENTS.md` 내용과 충돌 여부 재확인
- [x] 새 설계 결정 사항은 마스터 문서에만 반영 (분산 방지)
- [x] 문서는 현재 상태 보고가 아닌 원칙과 순서 중심으로 작성

### 코드 규칙

- [x] 모든 데이터 흐름에 Pydantic 모델 적용 (타입 계약 명시)
- [x] 모든 Adapter는 독립적으로 테스트 가능하게 작성
- [x] OPS Core는 Result Asset 외의 데이터를 직접 읽지 않는다
- [x] 회사 맞춤 로직은 Adapter 안에서만 처리한다

### 단계 전환 공통 기준

모든 Phase 전환 전 아래 5가지를 확인한다:

1. Adapter가 먼저 존재하는가?
2. 공통 키가 설명 가능한가?
3. Result Asset이 만들어지는가?
4. OPS가 그 자산을 평가하는가?
5. 다음 모듈 handoff가 문서 기준으로 설명 가능한가?

---

## 우선순위 요약

| 순서 | Phase               | 핵심 산출물                        | 상태    |
| ---- | ------------------- | ---------------------------------- | ------- |
| 0    | 기준 문서 통합      | 마스터 문서 세트                   | ✅ 완료 |
| 1    | 환경 구성           | 폴더 구조, 의존성, Supabase 스키마 | ✅ 완료 |
| 2    | Behavior CRM        | `crm_result_asset`                 | ✅ 완료 |
| 3    | Prescription        | `prescription_result_asset`        | ✅ 완료 |
| 4    | SFE Sandbox         | `sandbox_result_asset`             | ✅ 완료 |
| 5    | Territory Optimizer | `territory_result_asset`           | ✅ 완료 |
| 6    | HTML Builder        | `html_builder_result_asset`        | ✅ 완료 |
| 7    | OPS Core 통합       | 품질 게이트 + 연결 판단 체계       | ✅ 완료 |
| 8    | Streamlit 운영 콘솔 | 비개발자 운영 화면                 | ✅ 완료 |

---

## 한 줄 결론

`이 TODO는 adapter-first, Result Asset 중심, OPS 중앙 엔진 원칙을 지키면서 CRM -> Prescription -> Sandbox -> Territory -> HTML Builder 순서로 전체 5모듈을 단계별로 가동하는 전체 구현 로드맵이다.`
