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

## 진행중(In Progress)

- Part2 진행 문서의 최신 구조 반영(Agent 탭/Run storage 포함)
  - [x] Agent 탭 연결 상태와 경로 반영
  - [x] run_storage 경로 반영
- 실제 회사 raw intake/onboarding 공통화 설계 고정
  - [x] intake gate 운영 설계 문서 작성
  - [x] 공통 intake engine 구현 계획 문서 작성
  - [x] 공통엔진 1개 + `scenario + mapping + rules` 업데이트 구조로 방향 고정
  - [ ] intake/onboarding 공통엔진 구현
- raw generator 구조 단순화 설계 고정
  - [x] 공통 생성기 구조 설계 문서 초안 작성
  - [ ] 설정 기반 공통 generation engine 구현 (후순위, 현재 필수 구현 아님)
  - [ ] 회사별 generator thin wrapper 전환 (후순위, 현재 필수 구현 아님)

## 대기(Next)

- 공통 intake/onboarding engine 구현 착수
- Part2 다음 우선순위 모듈 착수 준비
- run 중심 저장 구조 및 report context 반영 설계의 구현 전환
- raw generator 공통화 구현 착수 (후순위, 필요 시)

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
