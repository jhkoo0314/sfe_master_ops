# Part2 Status Source Of Truth

작성일: 2026-03-20  
상태: `active`

## 문서 목적

이 문서는 Part2 진행 상태의 단일 기준 문서다.  
Part2의 완료/진행/대기 상태는 이 문서를 기준으로 본다.

## 현재 기준

- 현재 단계: `Part2 KPI 엔진 분리 진행`
- 완료된 축:
  - CRM KPI 엔진 운영 (`modules/kpi/crm_engine.py`)
  - Sandbox KPI 엔진 1차 분리 (`modules/kpi/sandbox_engine.py`)
  - Territory KPI 엔진 1차 분리 (`modules/kpi/territory_engine.py`)
  - Prescription KPI 엔진 1차 분리 (`modules/kpi/prescription_engine.py`)
  - Builder KPI 재계산 금지 원칙 유지
  - Sandbox에서 CRM KPI 재계산 금지 원칙 유지
  - 운영 콘솔은 `ui/console/` 패키지 기준으로 동작
  - Agent 탭이 콘솔에 연결되어 실행됨 (`ui/console/tabs/agent_tab.py`)
  - Agent 탭은 run 결과물과 문맥을 읽는 구조로 연결됨
    - run 저장: `common/run_storage/*`
    - Agent 로직: `ui/console/agent/*`

## 완료(Completed)

- KPI 엔진 모듈 체계 생성
- 모듈별 KPI 엔진 분리 완료 (CRM/Sandbox/Territory/Prescription)
- `hangyeol_pharma`, `daon_pharma` 회귀 검증 통과
- `monthly_merge_pharma` 6개월 월별 raw 생성/병합 검증 통과
  - 월별 raw 생성
  - 월별 파일 병합
  - 실행모드별 점검 완료
  - Territory 포함 모드는 의도된 품질 경고(`담당자 배치 불균형`) 확인
- Builder 최종 HTML 6종 생성 검증 통과
- Sandbox 보고서 지점/담당자 필터 복구 반영
- 콘솔 상단 탭에 Agent 화면이 정상 렌더링되도록 연결 완료
- Prescription 분리 회귀/문서 동기화 마감
  - KPI 계산 단일 소스: `modules/kpi/prescription_engine.py` 존재 확인
  - `modules/prescription/service.py`는 Result Asset 조립만 수행 (KPI 계산 없음)
  - `modules/prescription/builder_payload.py`는 KPI 재계산 없이 payload 조립만 수행
  - `scripts/validate_prescription_with_ops.py` 통과 결과 최신 생성 확인
    - `daon_pharma`: `prescription_validation_summary.json` (2026-03-19 17:50)
    - `hangyeol_pharma`: `prescription_validation_summary.json` (2026-03-19 23:11)
  - Builder 생성 결과(`prescription_flow_preview.html`) 최신 생성 확인
    - `daon_pharma`: `2026-03-20 01:15`
    - `hangyeol_pharma`: `2026-03-20 00:23`
- 운영 콘솔 월별 raw 업로드/자동 병합 연결 완료
  - 업로드 탭에서 월별 파일 다중 업로드 가능
  - `monthly_raw/YYYYMM/` 저장 지원
  - 실행 전 자동 병합 후 기존 파이프라인 실행
- 운영 콘솔 분석 인텔리전스 탭 해석 문장/근거 수치 표시 완료
  - 점수만이 아니라 `왜 PASS/WARN/APPROVED인지` 문장으로 표시
  - 실행 분석 문서(`latest_execution_analysis.md`) 저장
- 회사 등록 목록을 Supabase + 로컬 registry 병합 방식으로 보강
  - Supabase에 없는 테스트 회사도 로컬 목록에서 유지 가능
- 공통 intake/onboarding engine Phase 1~7 연결 완료
  - `modules/intake/` 공통엔진 뼈대 추가
  - `scenario + mapping + rules` 구조 연결
  - 기본 자동 수정(컬럼명 trim, 월/날짜 형식 정리, 중복 제거) 반영
  - 제안 문장/컬럼 후보 추천 반영
  - candidate가 있는 비치명적 매핑 애매함은 실행을 막지 않고 advisory로 남기도록 완화
  - source별 기간 범위 감지와 기간 차이 경고 반영
  - 공통 분석 구간(예: 6개월) 자동 계산 반영
  - 실행 전 “기간 차이가 있어도 계속 진행할지” 확인 UI 반영
  - 분석 인텔리전스 탭에 “기간 차이는 있지만 공통 구간 기준 검증 완료” 설명 문구와 intake 주의사항 섹션 반영
  - `_intake_staging`, `_onboarding` 저장 연결
  - 운영 콘솔 업로드/파이프라인 탭에 intake 결과 표시 연결
  - execution service가 `_intake_staging` 정리본을 실제 Adapter 입력으로 사용하도록 연결
- 다온제약 intake 인식 품질 보강 완료 (`2026-03-22`)
  - CRM 활동 파일의 `실행일`, `액션유형` 인식 보강
  - 처방 파일의 `brand (브랜드)`, `sku (SKU)` 인식 보강
  - 현재 다온제약 기준 intake 결과
    - `crm_to_sandbox`: `ready`, `ready_for_adapter=True`, advisory `0`
    - `integrated_full`: `ready`, `ready_for_adapter=True`, advisory `0`
  - 즉 다온제약은 현재 “실행 막힘 없는 intake” 상태로 정리됨
- `monthly_merge_pharma` 통합 실행 재검증 통과 (`2026-03-22`)
  - 실행 엔진 입력이 `company_source` 원본이 아니라 `_intake_staging` 기준으로 전환된 상태에서 재검증
  - `scripts/validate_full_pipeline.py` 기준 전체 파이프라인 완료
  - 전체 상태 `WARN`, 전체 점수 `94.7`
  - CRM `PASS` / Prescription `PASS` / Sandbox `PASS` / Territory `WARN` / RADAR `APPROVED` / Builder `PASS`
  - Builder HTML 6종 생성 확인
- `hangyeol_pharma` 통합 실행 재검증 통과 (`2026-03-22`)
  - `_intake_staging` 입력 기준으로 `scripts/validate_full_pipeline.py` 재실행
  - 전체 상태 `PASS`, 전체 점수 `96.7`
  - CRM `PASS` / Prescription `PASS` / Sandbox `PASS` / Territory `PASS` / RADAR `APPROVED` / Builder `PASS`
  - Builder HTML 6종 생성 확인
  - 현재 raw 기간 확인:
    - `sales`, `target`: `202601 ~ 202606` (6개월)
    - `prescription`: `202501 ~ 202512` (12개월)
  - 따라서 `hangyeol_pharma`는 “raw generator 기준 6개월 월별 검증 데이터셋”으로 분류하지 않는다.
  - source별 기간 구성이 다르다는 점을 기준 문서에 고정한다.
  - 현재 intake/콘솔은 이 차이를 감지해
    - 실행 전에는 “기간 차이가 있어도 공통 분석 구간 기준으로 계속 진행할지” 확인하고
    - 분석 탭에서는 “기간 차이는 있지만 2026-01 ~ 2026-06 기준 6개월 검증은 완료됐다” 식으로 설명한다.
- `ops_core` 구조 리팩토링 Step 1~7 완료 (`2026-03-22`)
  - `execution_service.py` 내부 책임 분해 완료
  - monthly merge 본체를 `modules/intake/merge.py`로 이동
  - staged source runtime helper를 `modules/intake/runtime.py`로 이동
  - script import/cache reset을 `common/runtime_helpers/import_cache.py`로 이동
  - `orchestrator.py`와 `execution_service.py` 경계를 평가/실행 기준으로 정리
  - 문서/주석/README에서 `ops_core`를 `Validation / Orchestration Layer 구현 패키지`로 재정의
  - 위치 이동 검토 결과: `modules/validation` 방향은 맞지만 `지금 즉시 hard rename`은 보류
  - `modules/validation` bridge 패키지 추가 완료
  - 일부 운영 코드가 `modules.validation...` bridge import로 전환 시작
  - API 실행 진입점 이중 지원 완료
    - 권장: `modules.validation.main:app`
    - 호환: `ops_core.main:app`
  - 기본 경로 정리 완료
    - 운영 스크립트 기본 import는 `modules.validation...` 기준
    - `ops_core`는 thin compatibility package로 유지
  - 상세 문서:
    - `docs/architecture/21_ops_core_refactor_plan.md`
    - `docs/architecture/22_ops_core_location_migration_review.md`
- 현재 기준 레거시 문서/테스트 import 정리 완료 (`2026-03-22`)
  - 저장소 지도/런북/구조 문서는 `modules.validation`을 기본 경로로 설명
  - `ops_core`는 호환 경로로만 남김
  - 테스트는 호환성 확인용 bridge 테스트만 `ops_core` import를 의도적으로 유지
- raw generator 공통화 2차 정리 완료 (`2026-03-22`)
  - 실제 실행 경로는 `config -> engine -> template -> helper -> writer` 기준으로 정리
  - 회사별 legacy generator 파일 3개 삭제 완료
    - `generate_daon_source_raw.py`
    - `generate_hangyeol_source_raw.py`
    - `generate_monthly_merge_source_raw.py`
  - raw generator는 이제 `company_profile.py`와 분리되어 동작
  - 즉 테스트용 raw 생성기는 운영 profile과 분리된 공통 생성기 구조로 정리됨
- `tera_pharma` 테스트 회사 생성 및 raw 생성 완료 (`2026-03-22`)
  - 회사명: `테라제약`
  - 템플릿: `daon_like`
  - 생성 기간: `2025-01-01 ~ 2025-12-31`
  - 지점 수: `6개`
  - 담당자 수: 의원 `30명`, 종합병원 `30명`
  - 생성 결과 확인:
    - 매출 월 범위 `202501 ~ 202512`
    - 목표 월 범위 `202501 ~ 202512`
    - CRM 활동일 범위 `2025-01-01 ~ 2025-12-31`
  - 생성 산출물은 `data/company_source/tera_pharma/` 아래에 저장
  - 현재 raw generator는 제품명/SKU/제형/포장단위/채널 적합성/전략 비중을 맞추기 위해 `docs/part1/hangyeol-pharma-portfolio-draft.csv`를 공통 제품 기준표로 사용

## 진행중(In Progress)

- Part2 진행 문서의 최신 구조 반영(Agent 탭/Run storage 포함)
  - [x] Agent 탭 연결 상태와 경로 반영
  - [x] run_storage 경로 반영
- 실제 회사 raw intake/onboarding 공통화 설계 고정
  - [x] intake gate 운영 설계 문서 작성
  - [x] 공통 intake engine 구현 계획 문서 작성
  - [x] 공통엔진 1개 + `scenario + mapping + rules` 업데이트 구조로 방향 고정
  - [x] intake/onboarding 공통엔진 구현
  - [x] 비치명적 intake 제안은 advisory로 완화
  - [x] 다온제약 실제 컬럼 인식 보강
- raw generator 구조 단순화 설계 고정
  - [x] 공통 생성기 구조 설계 문서 초안 작성
  - [x] 설정 기반 공통 generation engine 구현
  - [x] 회사별 generator thin wrapper 전환 후 legacy 파일 정리 완료
- `ops_core -> modules/validation` 점진 전환 준비
  - [x] `ops_core` 책임 분리 및 의미 재정의
  - [x] 위치 이동 검토 문서화
  - [x] `modules/validation` bridge 패키지 추가
  - [x] 운영 핵심 import를 `modules.validation...` 기준으로 전환
  - [x] 현재 기준 레거시 문서/테스트 import 정리

## 대기(Next)

- Part2 다음 우선순위 모듈 착수 준비
- run 중심 저장 구조 및 report context 반영 설계의 구현 전환
- 새 테스트 회사 추가 시 raw generation config만 추가하는 운영 규칙 유지
- `modules/validation` bridge 추가 후 실제 import 전환 검토

## 운영 고정 원칙

1. KPI 계산은 `modules/kpi/*`에서만 수행한다.
2. OPS는 Validation/Orchestration 역할만 수행한다.
3. Builder는 render-only를 유지한다.
4. 모든 경로/저장은 `company_key` 기준을 유지한다.

## 현재 구조 메모 (2026-03 기준)

- 콘솔 진입점: `ui/ops_console.py`
- 실제 콘솔 패키지: `ui/console/`
- Agent 탭: `ui/console/tabs/agent_tab.py` → `ui/console/agent/service.py`
- Agent 데이터 읽기:
  - `common/run_storage/runs.py`
  - `common/run_storage/artifacts.py`
  - `common/run_storage/report_context.py`

## 링크

- 현재 단계 문서: `docs/ai/07_current_phase.md`
- Part2 허브(레거시): `docs/part2/README.md`
