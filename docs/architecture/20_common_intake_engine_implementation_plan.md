# 20. Common Intake Engine Implementation Plan

## 문서 목적

이 문서는 `Intake Gate + Onboarding`을 실제 코드로 옮기기 위한 **공통엔진 구현 계획서**다.

즉 `19_intake_gate_and_onboarding_plan.md`가 운영 설계 문서라면,  
이 문서는 그것을 **어떤 파일 구조와 어떤 작업 순서로 구현할지** 설명하는 실행 계획 문서다.

---

## 1. 구현 목표

구현 목표는 단순하다.

1. 새 회사 raw를 받는 **공통엔진 1개**를 만든다.
2. 회사마다 새 스크립트를 만들지 않고, 시나리오/매핑/룰 업데이트로 처리한다.
3. 자동 수정 가능한 것은 engine이 직접 처리한다.
4. 수정 불가 항목은 제안으로 남긴다.
5. onboarding 결과를 저장해 다음 실행 때 재사용한다.
6. Adapter 이후 기존 파이프라인은 최대한 건드리지 않는다.

즉 이 엔진의 목표는 **raw를 adapter-ready 상태로 만드는 것**이다.

---

## 2. 구현 범위

### 이번 구현에 포함

- intake 검사
- 자동 보정
- 제안 생성
- onboarding-ready 데이터 생성
- 회사별 매핑 저장
- 운영 콘솔 연결

### 이번 구현에 포함하지 않음

- KPI 계산
- OPS 평가 로직 변경
- Builder 로직 변경
- 테스트용 raw generator 구조 개편

즉 이번 구현은 철저히 `raw -> adapter 이전`까지만 다룬다.

---

## 3. 목표 아키텍처

목표 구조는 아래다.

```text
ui upload
  -> intake engine
      -> file inspection
      -> schema inspection
      -> value inspection
      -> auto-fix
      -> suggestion build
      -> onboarding package build
  -> adapter
  -> existing pipeline
```

핵심 원칙:

- 운영에서 보이는 엔진은 하나여야 한다.
- 회사마다 새 intake 파일이 생기면 안 된다.
- 엔진이 읽는 업데이트 대상은 `시나리오 + 매핑 + 룰`이다.

---

## 4. 새로 필요한 핵심 구성요소

### 4.1 Intake Engine

역할:

- 업로드된 raw를 검사
- 문제를 찾음
- 자동 수정
- 수정 제안 생성
- onboarding-ready 결과물 반환

예상 파일:

- `modules/intake/service.py`

### 4.2 Scenario Registry

역할:

- source별 처리 시나리오 정의
- 어떤 입력 묶음인지 정의
- 어떤 매핑과 룰을 읽어야 하는지 연결

예상 파일:

- `modules/intake/scenarios.py`

### 4.3 Mapping Registry

역할:

- 회사별 컬럼 매핑과 intake 결정 저장
- 다음 업로드에서 재사용
- 시나리오가 요구하는 표준 의미와 실제 컬럼을 연결

예상 파일:

- `common/company_onboarding_registry.py`

### 4.4 Intake Rules

역할:

- 파일별 검사 규칙 정의
- 어떤 컬럼이 최소 필수인지 정의
- 어떤 자동 수정이 가능한지 정의

예상 파일:

- `modules/intake/rules.py`

### 4.5 Auto Fixers

역할:

- 월/날짜 형식 보정
- 컬럼명 정리
- 중복 제거
- 값 표준화

예상 파일:

- `modules/intake/fixers.py`

### 4.6 Suggestion Builder

역할:

- 자동 수정 불가 항목에 대한 제안 생성
- 사람이 읽는 문장으로 반환

예상 파일:

- `modules/intake/suggestions.py`

### 4.7 Onboarding Package

역할:

- intake 결과를 onboarding-ready 구조로 묶음
- Adapter에 넘길 정리본 경로와 매핑 정보 포함
- source별 기간 범위와 공통 분석 구간 정보 포함

예상 파일:

- `modules/intake/models.py`

---

## 5. 코드 구조 제안

```text
modules/
  intake/
    __init__.py
    service.py
    models.py
    scenarios.py
    rules.py
    fixers.py
    suggestions.py
    staging.py
common/
  company_onboarding_registry.py
ui/console/
  tabs/
    upload_tab.py
    pipeline_tab.py
```

---

## 6. 데이터 모델 제안

### 6.1 IntakeFinding

무슨 문제가 있었는지 기록

예상 필드:

- `level`
  - `info`
  - `warn`
  - `error`
- `source_key`
- `issue_code`
- `message`
- `column_name`
- `row_estimate`

### 6.2 IntakeFix

무엇을 자동 수정했는지 기록

예상 필드:

- `source_key`
- `fix_type`
- `message`
- `affected_count`

### 6.3 IntakeSuggestion

자동 수정이 어려운 부분에 대한 제안

예상 필드:

- `source_key`
- `suggestion_type`
- `message`
- `candidate_columns`

### 6.4 OnboardingPackage

onboarding-ready 상태를 표현

예상 필드:

- `company_key`
- `source_key`
- `original_path`
- `staged_path`
- `status`
- `findings`
- `fixes`
- `suggestions`
- `resolved_mapping`
- `period_coverage`
- `ready_for_adapter`

### 6.5 IntakeResult 추가 정보

운영 콘솔 설명용으로 아래 정보도 함께 필요하다.

- `period_coverages`
- `timing_alerts`
- `analysis_basis_sources`
- `analysis_start_month`
- `analysis_end_month`
- `analysis_month_count`
- `analysis_summary_message`
- `proceed_confirmation_message`

---

## 7. 단계별 구현 순서

### Phase 1. 공통엔진 뼈대 먼저 고정

목표:

- 운영에서 보이는 intake engine 1개의 입출력 구조를 먼저 고정

작업:

1. `modules/intake/service.py` 추가
2. `modules/intake/models.py` 추가
3. 공통 엔진 입력/출력 계약 고정
4. `execution_service.py`에서 호출 가능한 형태로 인터페이스 정의

완료 기준:

- “공통엔진 1개”로 intake 결과를 반환할 수 있는 구조가 정해짐

### Phase 2. 시나리오 / 매핑 / 룰 구조 추가

목표:

- 회사별 파일 증가 없이 업데이트 가능한 구조를 만든다

작업:

1. `modules/intake/scenarios.py` 추가
2. `common/company_onboarding_registry.py` 추가
3. `modules/intake/rules.py` 추가
4. 시나리오가 매핑과 룰을 읽는 구조 정의

완료 기준:

- 엔진은 하나고, 회사 차이는 시나리오/매핑/룰 업데이트로 처리 가능

### Phase 3. 자동 수정기 추가

목표:

- 사람이 매번 다시 업로드하지 않아도 되는 수준의 기본 보정 구현

작업:

1. 월 형식 보정
2. 날짜 형식 보정
3. 컬럼명 trim
4. 중복 제거
5. csv/xlsx 정리

완료 기준:

- 단순 형식 오류는 intake가 스스로 보정 가능

### Phase 4. 제안 생성기 추가

목표:

- 자동 수정 불가 항목을 사람이 이해할 수 있는 문장으로 설명

작업:

1. 컬럼 후보 추천
2. 매핑 제안 생성
3. 위험도 메시지 생성

완료 기준:

- intake 결과를 콘솔에서 바로 읽을 수 있음
- 비치명적 candidate 제안은 실행 차단이 아니라 advisory로 남길 수 있음

### Phase 5. staging / onboarding-ready 저장

목표:

- 원본 raw는 보존하고, Adapter용 정리본을 따로 저장

작업:

1. staging 경로 설계
2. source별 정리본 저장
3. onboarding package 저장

완료 기준:

- Adapter는 intake 결과물만 읽도록 연결 가능

### Phase 6. 운영 콘솔 연결

목표:

- 업로드 후 intake 결과와 onboarding 가능 여부를 UI에 표시

작업:

1. 업로드 탭에서 intake 실행
2. findings / fixes / suggestions 표시
3. onboarding-ready 상태 표시
4. 파이프라인 탭에서 adapter-ready 여부 확인
5. 기간 차이 감지 시 계속 진행 여부 확인
6. 분석 인텔리전스 탭에 공통 분석 구간 설명 문구 표시
7. 실행은 허용됐지만 해석 전에 다시 볼 advisory 항목 표시

완료 기준:

- 사용자 입장에서 raw 업로드 후 무슨 일이 일어났는지 보임
- 기간 차이가 있을 때도 “무엇이 앞서 있고 실제로 몇 개월 기준 분석이 진행되는지” 이해 가능

### Phase 7. execution service 연결

목표:

- intake/onboarding 통과 결과를 기존 Adapter 실행 흐름으로 연결

작업:

1. `execution_service.py`에서 intake 결과 사용
2. Adapter 입력을 source raw 대신 staged raw로 전환
3. 실패 시 intake 원인 메시지 반환

완료 기준:

- `raw -> intake -> onboarding -> adapter -> existing pipeline`가 실제로 연결됨

---

## 8. 파일별 실제 수정 대상

### 새 파일

- `modules/intake/service.py`
- `modules/intake/models.py`
- `modules/intake/scenarios.py`
- `modules/intake/rules.py`
- `modules/intake/fixers.py`
- `modules/intake/suggestions.py`
- `modules/intake/staging.py`
- `common/company_onboarding_registry.py`

### 수정 파일

- `ui/console/tabs/upload_tab.py`
- `ui/console/tabs/pipeline_tab.py`
- `ui/console/state.py`
- `modules/validation/workflow/execution_service.py`
- `common/company_profile.py`

### 이유

- `upload_tab.py`
  - 업로드 직후 intake 결과 표시 필요
- `pipeline_tab.py`
  - onboarding-ready 상태를 보여줘야 함
- `state.py`
  - intake 결과 세션 보관 필요
- `execution_service.py`
  - `modules/intake`를 호출하고 Adapter 입력으로 연결해야 함
- `company_profile.py`
  - 장기적으로는 adapter example 중심 구조를 줄이고, onboarding 저장값과 연결해야 함

---

## 9. staging 저장 전략

원본 raw는 그대로 보존한다.

새로 필요한 경로 예시는 아래다.

```text
data/company_source/{company_key}/_intake_staging/
data/company_source/{company_key}/_intake_staging/{source_key}/
data/company_source/{company_key}/_onboarding/
```

여기에 저장할 것:

- 정리된 raw 파일
- intake 결과 json
- onboarding package json

이렇게 해야:

- 원본 손상 방지
- 자동 수정 이력 추적 가능
- 문제가 생겼을 때 되돌리기 쉬움

---

## 10. 운영 콘솔에서 보여줄 화면

### 업로드 직후

- 파일 인식 결과
- 핵심 컬럼 인식 결과
- 자동 수정 내역
- 수정 제안
- onboarding 가능 여부

### 파이프라인 실행 전

- source별 intake 상태
- Adapter 전달 준비 여부
- blocked 항목 여부

### 실행 후

- 기존 파이프라인 결과 유지

즉 intake는 앞단 투명성을 높이고, 이후 실행 흐름은 기존 구조를 활용한다.

현재 운영 보정 메모 (`2026-03-22`):

- 인테이크가 너무 빡빡하면 사용자 피로가 커지므로, candidate가 있는 비치명적 매핑 애매함은 advisory로 완화했다.
- 다온제약 실제 컬럼 기준 보강 완료
  - CRM: `실행일`, `액션유형`
  - Prescription: `brand (브랜드)`, `sku (SKU)`

---

## 11. 가장 먼저 구현해야 하는 최소 MVP

최소 MVP는 아래 정도면 충분하다.

1. 공통 intake engine 1개 생성
2. 시나리오 / 매핑 / 룰 구조 연결
3. 월/날짜 형식 자동 수정
4. 컬럼명 trim / 단순 유사 컬럼 추천
5. 필수 컬럼 존재 여부 점검
6. intake findings / fixes / suggestions 반환
7. staging 파일 저장
8. adapter-ready 여부 판단

즉 처음부터 완벽한 온보딩 자동화가 아니라,
**“다시 업로드를 덜 하게 만드는 자동 보정형 intake”**부터 시작하는 것이 맞다.

---

## 12. 성공 기준

이 구현이 성공했다고 보려면 아래가 가능해야 한다.

1. 사용자는 회사 등록과 raw 업로드만 한다.
2. 운영에서 보이는 intake engine은 하나다.
3. 회사별 스크립트 추가 없이 시나리오/매핑/룰 업데이트로 새 회사를 수용한다.
4. intake engine이 기본 오류를 자동 수정한다.
5. 수정 불가 항목은 제안으로 보여준다.
6. onboarding-ready 결과가 staging에 저장된다.
7. Adapter는 회사별 수정 없이 재사용된다.
8. 이후 기존 파이프라인은 그대로 돈다.

---

## 13. 최종 정리

이 구현의 본질은 새 엔진을 하나 더 만드는 것이 아니다.  
이미 준비된 Adapter 이후 파이프라인을 살리기 위해, **실제 회사 raw를 앞단에서 정리해주는 공통 intake/onboarding 엔진을 만드는 것**이다.

구현 위치 원칙:

- 실제 intake/onboarding 처리 책임은 `modules/intake` 아래에 둔다.
- `modules/validation/workflow/execution_service.py`는 실행 순서 안에서 이 모듈을 호출하는 orchestration 역할만 가진다.

핵심 한 줄은 아래다.

**공통 intake engine의 목표는 회사 raw를 검사하고 고치고 제안해서, 시나리오/매핑/룰 업데이트만으로 결국 Adapter가 읽을 수 있는 안정된 입력으로 바꾸는 것이다.**
