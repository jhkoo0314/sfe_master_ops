# Current Phase

## 현재 단계 정의

현재 단계는 `Part2 완료` 단계다.  
이 문서는 실행 안내/요약 전용이다.

Part1 기준 구조 고정과 CRM KPI 거버넌스 복구(Phase 1~6)는 완료 상태로 본다.

## 단일 기준 고정

- Part2 진행 상태(Completed / In Progress / Next)의 단일 기준은 `docs/architecture/12_part2_status_source_of_truth.md`다.
- 우선순위가 충돌하면 이 문서가 아니라 위 단일 기준 문서를 따른다.
- 이 문서는 단일 기준 문서를 요약 안내하는 용도로만 유지한다.

## 현재 상태 요약

- CRM 공식 KPI 계산: `modules/kpi/crm_engine.py`
- Sandbox KPI 분리 1차: `modules/kpi/sandbox_engine.py`
- Territory KPI 분리 1차: `modules/kpi/territory_engine.py`
- Prescription KPI 분리 1차: `modules/kpi/prescription_engine.py`
- Builder는 KPI 재계산 없이 payload 주입만 수행
- Sandbox는 CRM KPI 재계산 없이 입력 KPI 사용
- Territory builder payload는 KPI 계산 없이 조립/분할만 수행
- Prescription builder payload는 KPI 계산 없이 조립/분할만 수행
- `hangyeol_pharma`, `daon_pharma` 회귀 검증 통과
- `monthly_merge_pharma` 6개월 월별 raw 생성/병합 검증 통과
- raw generator 공통화 2차 정리 완료
  - 실행 경로는 `config -> engine -> template -> helper -> writer`
  - legacy generator 파일은 제거 완료
  - 새 테스트 회사는 config 추가 방식으로 확장
- `hangyeol_pharma`, `daon_pharma` 기준 최종 HTML 6종 생성 검증 통과
- `monthly_merge_pharma`는 6개월 월별 raw 생성/병합과 실행모드별 점검 완료
- Sandbox 최종 HTML 지점/담당자 필터 복구 완료
  - `report_template`에 지점 chunk 로더 반영
  - `branch_index` 기반 지점 옵션 + 선택 지점 asset 로딩 방식으로 동작
- Sandbox 기반 실행모드에서 RADAR 단계 자동 실행 반영
  - `scripts/validate_radar_with_ops.py`
  - `data/ops_validation/{company_key}/radar/radar_result_asset.json` 생성
- 운영 콘솔에서 월별 raw 업로드 후 자동 병합 실행 가능
- 분석 인텔리전스 탭에서 판정 해석 문장과 근거 수치 확인 가능
- 다음 구현 우선순위는 테스트용 raw generator 공통화보다 실제 운영용 공통 intake/onboarding engine이다.
- 방향은 `공통엔진 1개 + scenario/mapping/rules 업데이트` 기준으로 고정한다.
- 공통 intake/onboarding engine Phase 1~7 연결 완료
  - 공통 intake 엔진 1개
  - 시나리오/매핑/룰 구조
  - 자동 수정
  - 제안 생성
  - 비치명적 candidate 제안은 advisory로 완화
  - source별 기간 범위 감지
  - 기간 차이 경고 + 공통 분석 구간 계산
  - 실행 전 진행 확인 문구
  - 분석 인텔리전스 탭 설명 문구 + intake 주의사항 표시
  - `_intake_staging`, `_onboarding` 저장
  - 운영 콘솔 표시
  - execution service의 staged raw 실제 입력 연결
- 다온제약 intake 인식 보강 완료 (`2026-03-22`)
  - `실행일`, `액션유형`, `brand (브랜드)`, `sku (SKU)` 같은 실제 컬럼 표현 인식 강화
  - 현재 다온제약 intake 결과는 `ready / ready_for_adapter=True` 기준으로 유지
  - 즉 치명적이지 않은 애매함은 실행을 막지 않고, 분석 탭에서 설명하는 방향으로 정렬됨
- `monthly_merge_pharma`는 `_intake_staging` 입력 기준으로 `scripts/validate_full_pipeline.py` 재검증 완료 (`2026-03-22`)
  - 전체 상태 `WARN`
  - 전체 점수 `94.7`
  - Territory는 의도된 운영 점검 경고(`WARN`)로 유지
  - Builder HTML 6종 생성 확인
- `hangyeol_pharma`는 `_intake_staging` 입력 기준으로 `scripts/validate_full_pipeline.py` 재검증 완료 (`2026-03-22`)
  - 전체 상태 `PASS`
  - 전체 점수 `96.7`
  - Builder HTML 6종 생성 확인
  - 현재 raw 기간은 source별로 다름
    - `sales`, `target`: `202601 ~ 202606` (6개월)
    - `prescription`: `202501 ~ 202512` (12개월)
  - 따라서 한결제약을 “raw generator 기준 6개월 월별 검증 데이터”로 단순화해서 보면 안 된다.
  - 현재 intake/콘솔은 이 차이를 감지해
    - 실행 전에는 계속 진행 여부를 확인하고
    - 분석 탭에서는 공통 분석 구간 기준 6개월 검증 완료 문구를 보여준다.
- `ops_core` 구조 리팩토링 Step 1~7 완료 (`2026-03-22`)
  - 실행 준비 책임 분리
  - monthly merge / staging runtime / cache reset 본체를 `ops_core` 밖으로 이동
  - 평가 오케스트레이션과 실제 실행 오케스트레이션 경계 정리
  - `ops_core`를 `Validation / Orchestration Layer 구현 패키지`로 문서 정렬
  - 위치 이동 검토 결과: 최종 방향은 `modules/validation`, 하지만 지금 즉시 폴더 이동은 보류
  - `modules/validation bridge 패키지` 추가 완료
  - 일부 운영 코드는 이미 `modules.validation...` bridge import로 전환 시작
  - API 실행 진입점도 `modules.validation.main:app`와 `ops_core.main:app`를 함께 지원
  - 운영 스크립트 기본 import도 `modules.validation...` 기준으로 전환 완료
  - 현재 결론은 `modules.validation`을 기본으로 쓰고, `ops_core`는 호환용으로 유지하는 것
- 현재 기준 문서/테스트 import 정리 완료 (`2026-03-22`)
  - 저장소 지도/런북/구조 문서는 `modules.validation`을 기본 경로로 설명
  - `ops_core`는 호환 경로로만 표기
  - 테스트에서는 `ops_core` 호환성 확인용 bridge 테스트만 의도적으로 유지
- `tera_pharma` 테스트 회사 생성 완료 (`2026-03-22`)
  - 회사명 `테라제약`
  - 기간 `2025-01 ~ 2025-12`
  - 지점 `6개`
  - 담당자: 의원 `30명`, 종합병원 `30명`
  - 매출/목표/CRM 기간 검산 완료
  - 생성 위치: `data/company_source/tera_pharma/`
  - 제품 기준표는 `docs/part1/hangyeol-pharma-portfolio-draft.csv`를 사용
    - 이유: 제품명만 맞추기 위한 것이 아니라 브랜드/SKU/제형/포장단위/전략 비중을 공통으로 맞추기 위해서다
- `company_000001` 메가제약 기준 실사용 월별 업로드 검증 완료 (`2026-03-23`)
  - 실제 UI에서 월별 raw 업로드 -> 자동 병합 -> intake -> 파이프라인 -> Builder 흐름 확인
  - Prescription 월별 필터도 생성본 기준으로 정상 동작 확인
- `company_000002` 보정테스트제약 기준 지저분한 raw intake 자동보정 검증 완료 (`2026-03-23`)
  - 컬럼명 공백, 날짜/월 형식 흔들림, 중복 행이 있는 raw로 점검
  - `_intake_staging` 보정본 생성과 전체 파이프라인 연결 확인
- Territory 보고서는 외부 지도 CDN 의존 없이 오프라인 번들 기준으로 열리도록 안정화 완료 (`2026-03-23`)
- Prescription 보고서는 월별 필터와 월별 detail asset 로딩이 실제 Builder 생성본 기준으로 정상화 완료 (`2026-03-23`)
- 최종 판단: Part2 완료 선언 가능 (`2026-03-23`)
  - 이유: 핵심 구현과 실사용 검증이 모두 끝났고, 남은 항목은 운영 경고 최적화와 다음 단계 확장 과제로 분류됨

## 지금 해야 할 것

- `docs/architecture/12_part2_status_source_of_truth.md`의 `Completed / Next` 상태를 먼저 확인한다.
- `modules.validation` 기본 경로 기준으로 새 작업을 계속 누적한다.

## 지금 하지 않을 것

- 단일 기준 문서와 다른 임의 우선순위를 새로 만들지 않는다.
- 상태 변경을 `docs/ai/07_current_phase.md`에 먼저 기록하지 않는다.
- `docs/architecture/12_part2_status_source_of_truth.md` 갱신 없이 진행 상태를 확정하지 않는다.
- `ops_core`를 지금 바로 hard rename 하지 않는다.

## Codex 작업 제한

- 세계관을 바꾸지 않는다.
- Builder를 계산 엔진으로 확장하지 않는다.
- Sandbox에서 CRM KPI를 재계산하지 않는다.
- `company_key` 경로 원칙을 무시하지 않는다.

## 결론

Part2 우선순위와 상태는 `docs/architecture/12_part2_status_source_of_truth.md`만 기준으로 본다.

## 문서 기준

- Part2 진행 상태의 단일 기준은 `docs/architecture/12_part2_status_source_of_truth.md`다.
- 이 문서는 실행 안내/요약만 유지하고, 세부 체크리스트는 architecture 문서에만 누적한다.
