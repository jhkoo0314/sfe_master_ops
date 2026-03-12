# Prescription Phase Gate Report Template

프로젝트: Prescription Data Flow  
작성일: YYYY-MM-DD  
작성자:  
검토자:

## 0) Gate 판정 기준
- `PASS`: 필수 테스트 100% 통과, 필수 실패 0건, 필수 산출물 누락 0건
- `CONDITIONAL_PASS`: 경미 이슈만 존재, 시정 계획 명시
- `FAIL`: 필수 테스트 실패, 산출물 누락, 승인 메타 누락 중 하나라도 존재

## 1) 공통 실행 정보
### 1.1 환경 정보
- python:
- pip:
- os:
- run_id:
- seed:

### 1.2 입력 기준
- source snapshot date:
- input manifest path:
- share rule version:
- claim input version:

### 1.3 공통 테스트 실행 결과
- [ ] `pytest -m unit`
- [ ] `pytest -m contract`
- [ ] `pytest -m integration`
- [ ] `pytest -m regression`
- [ ] `pytest -m e2e`
- [ ] 선택: `pytest -m local_workbench_smoke`

### 1.4 필수 상세 산출물 확인
- [ ] `tracking_report.*`
- [ ] `share_settlement.*`
- [ ] `rep_kpi_month.*`
- [ ] `rep_kpi_quarter.*`
- [ ] `rep_kpi_year.*`
- [ ] `kpi_summary_month.*`
- [ ] `kpi_summary_quarter.*`
- [ ] `kpi_summary_year.*`
- [ ] `validation_report.*`
- [ ] `trace_log.*`

### 1.5 공식 패키지 확인
- [ ] `prescription_result_asset.json`
- [ ] `prescription_builder_payload.json`
- [ ] `prescription_ops_handoff.json`

## 2) Phase별 Gate 기록

## Phase 1 - Input Contract
목표:
- 입력 파일, 컬럼, lineage 계약 고정

핵심 검증 항목:
- [ ] 필수 컬럼 존재
- [ ] 인코딩 이상 없음
- [ ] input manifest 생성 성공

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`
이슈/조치:

---

## Phase 2 - Mastering & Tracking
목표:
- `mastering`, `tracking_validation` 안정화

핵심 검증 항목:
- [ ] `pharmacy_uid` 누락 0건
- [ ] `territory_code` 매핑 품질 기준 충족
- [ ] `tracking_report.*` 생성 성공
- [ ] `coverage_ratio`, `gap_ratio` 계산 정확성

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`
이슈/조치:

---

## Phase 3 - Share Settlement
목표:
- 정산 로직과 전분기 연장 안정화

핵심 검증 항목:
- [ ] 보전성 유지
- [ ] `share_rule_source` 정확성
- [ ] `extended` 경로 검증

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`
이슈/조치:

---

## Phase 4 - KPI & Validation
목표:
- KPI 발행과 validation/trace 안정화

핵심 검증 항목:
- [ ] KPI 출력 6종 생성
- [ ] 요약 출력 3종 생성
- [ ] `validation_report.*` 생성
- [ ] `trace_log.*` 생성

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`
이슈/조치:

---

## Phase 5 - Approval Package
목표:
- 공식 패키지 3종 생성과 승인 메타 고정

핵심 검증 항목:
- [ ] `quality_status` 존재
- [ ] `approval_status` 존재
- [ ] `approved_version`, `approved_by`, `approved_at` 존재
- [ ] `handoff_ready` 존재

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`
이슈/조치:

---

## Phase 6 - Optional Local Workbench
목표:
- 로컬 화면이 있더라도 핵심 파이프라인과 충돌하지 않음

핵심 검증 항목:
- [ ] 화면 없이도 end-to-end 실행 가능
- [ ] 화면이 결과 패키지를 대체하지 않음
- [ ] 화면은 조회/다운로드 중심으로 제한

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`
이슈/조치:

## 3) 최종 Gate 요약
| Phase | 판정 | 필수 실패 건수 | 필수 산출물 누락 | 비고 |
|---|---|---:|---:|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |
| 6 |  |  |  |  |

최종 판정: `PASS | CONDITIONAL_PASS | FAIL`

## 4) 승인
- 작성자:
- 검토자:
- 승인일:
