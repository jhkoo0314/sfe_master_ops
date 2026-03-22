# 21. OPS Core Refactor Plan

## 문서 목적

이 문서는 현재 [`ops_core/`](/C:/sfe_master_ops/ops_core)가 맡고 있는 책임을 정리하고,  
이를 Sales Data OS 기준에 맞게 **Validation / Orchestration Layer**로 다시 얇게 만드는 리팩토링 계획서다.

이 문서의 목적은 세 가지다.

1. `ops_core`가 지금 실제로 어떤 역할을 하고 있는지 구분한다.
2. `ops_core`에서 빠져야 할 책임과 남아야 할 책임을 나눈다.
3. 최종적으로 `ops_core`를 `modules` 안 책임으로 정리할 수 있는 안전한 단계 순서를 만든다.

중요:

- 이 문서는 “지금 당장 폴더를 이름 바꾸고 이동하자”는 문서가 아니다.
- 먼저 **책임 분리**를 하고, 나중에 **위치 이동**을 검토하는 문서다.
- 안정성이 개념적 깔끔함보다 우선이다.

---

## 1. 현재 문제 요약

현재 [`ops_core/`](/C:/sfe_master_ops/ops_core)는 이름상으로는 OPS 중심 코어처럼 보이지만,  
실제 코드 기준으로는 아래 역할이 함께 섞여 있다.

### 1.1 현재 들어있는 역할

- FastAPI 앱 진입점
- 모듈별 Result Asset 평가 API
- API용 파이프라인 오케스트레이션
- 실제 운영 콘솔 실행 서비스
- 월별 raw 자동 병합
- intake 실행 연결
- staged source root 전환
- 실행 스크립트 import/cache 초기화

즉 지금은 아래가 같이 들어 있다.

- `판정하는 역할`
- `실행 순서를 제어하는 역할`
- `파일/런타임을 준비하는 역할`

이 상태가 계속되면,

- `ops_core`가 Validation Layer보다 “전체 실행 엔진”처럼 커지고
- 수정 범위가 넓어지고
- 장애 원인 추적이 어려워지고
- 나중에 `modules/ops` 또는 `modules/validation`으로 옮기기도 어려워진다.

---

## 2. Sales Data OS 기준에서 OPS가 맡아야 하는 역할

Sales Data OS 기준에서 OPS는 시스템 전체가 아니다.

OPS는 아래 역할만 가져야 한다.

- Result Asset 품질 평가
- 다음 단계 handoff 가능 여부 판단
- 실행 순서 통제
- validation output 관리

OPS가 가져서는 안 되는 역할은 아래다.

- raw 정리/자동 수정 책임
- staging 파일 생성 책임
- 월별 raw 병합 책임
- 파일 복사/환경변수 전환 같은 런타임 보조 책임
- 전체 시스템의 최상위 엔진 역할

쉽게 말하면:

- OPS는 “이 결과를 넘겨도 되는지 판단하는 레이어”다.
- raw를 정리하고 파일을 옮기는 레이어는 아니다.

---

## 3. 현재 `ops_core` 내부 역할 분해

### 3.1 남겨도 되는 책임

아래는 OPS 본연의 역할에 가깝다.

- [`ops_core/api/crm_router.py`](/C:/sfe_master_ops/ops_core/api/crm_router.py)
- [`ops_core/api/prescription_router.py`](/C:/sfe_master_ops/ops_core/api/prescription_router.py)
- [`ops_core/api/sandbox_router.py`](/C:/sfe_master_ops/ops_core/api/sandbox_router.py)
- [`ops_core/api/territory_router.py`](/C:/sfe_master_ops/ops_core/api/territory_router.py)
- [`ops_core/api/pipeline_router.py`](/C:/sfe_master_ops/ops_core/api/pipeline_router.py)
- [`ops_core/workflow/orchestrator.py`](/C:/sfe_master_ops/ops_core/workflow/orchestrator.py)
- [`ops_core/workflow/schemas.py`](/C:/sfe_master_ops/ops_core/workflow/schemas.py)

이 파일들은 본질적으로:

- 평가
- handoff 판단
- 순서 제어

를 담당한다.

### 3.2 줄여야 하는 책임

아래는 OPS 본연의 역할보다 “실행 보조”에 가깝다.

- [`ops_core/workflow/execution_service.py`](/C:/sfe_master_ops/ops_core/workflow/execution_service.py)
- [`ops_core/workflow/execution_registry.py`](/C:/sfe_master_ops/ops_core/workflow/execution_registry.py)
- [`ops_core/workflow/monthly_source_merge.py`](/C:/sfe_master_ops/ops_core/workflow/monthly_source_merge.py)

현재 섞여 있는 책임:

- 업로드 파일 source 반영
- monthly raw 병합
- intake 호출
- `_intake_staging` 입력 전환
- script runtime cache 초기화
- 환경변수 기반 source root override

이 중 상당수는 장기적으로 `ops_core` 밖으로 이동해야 한다.

---

## 4. 최종 방향

최종 방향은 아래처럼 본다.

### 4.1 개념적 최종 위치

장기적으로는 아래 형태가 가장 자연스럽다.

```text
modules/
  intake/
  crm/
  prescription/
  sandbox/
  territory/
  radar/
  validation/   # 또는 ops/
```

즉 지금의 `ops_core`는 결국:

- `modules/validation`
또는
- `modules/ops`

안 성격으로 수렴하는 것이 맞다.

### 4.2 하지만 지금 바로 하지 않을 것

지금 당장 아래를 바로 하지는 않는다.

- `ops_core -> modules/ops` 대규모 rename
- import 경로 일괄 변경
- FastAPI 진입점 대량 이동

이유:

- 현재 콘솔, 스크립트, 문서, 실행 경로가 이미 `ops_core`를 중심으로 묶여 있다.
- 지금은 “개념상 맞는 이름”보다 “안전하게 분리 가능한 구조”가 먼저다.

---

## 5. 리팩토링 핵심 원칙

### 5.1 이름보다 책임을 먼저 옮긴다

순서는 아래가 맞다.

1. `ops_core`를 얇게 만든다.
2. runtime/helper 책임을 밖으로 뺀다.
3. 실제로 남는 것이 Validation / Orchestration만 되게 만든다.
4. 마지막에만 위치 이동을 검토한다.

### 5.2 thin wrapper를 유지한다

기존 import 경로나 실행 진입점이 많이 쓰이는 상태이므로,
새 위치로 책임을 옮기더라도 기존 파일은 당분간 thin wrapper로 유지한다.

### 5.3 KPI 계산은 절대 들어오지 않는다

`ops_core` 리팩토링 중에도 아래는 금지한다.

- KPI 계산 로직 추가
- Builder 계산 로직 추가
- raw 직접 해석 로직 추가

---

## 6. 목표 구조

중간 목표는 아래다.

```text
ops_core/
  main.py
  api/
    crm_router.py
    prescription_router.py
    sandbox_router.py
    territory_router.py
    pipeline_router.py
  workflow/
    orchestrator.py
    schemas.py
    execution_models.py
    execution_registry.py
modules/
  intake/
    service.py
    staging.py
    runtime.py
    merge.py
common/
  runtime_helpers/
    import_cache.py
```

설명:

- `ops_core` 안에는 평가와 순서 제어만 남긴다.
- intake/staging/monthly merge는 `modules/intake` 쪽으로 더 이동한다.
- import cache reset 같은 런타임 잡일은 별도 helper로 뺀다.

---

## 7. 단계별 실행 계획

## Step 1. `execution_service.py` 내부 책임 분해

진행 상태:

- `2026-03-22 완료`

목표:

- 실행 서비스에서 “판단”과 “준비”를 분리한다.

분리 대상:

- source 반영
- intake 준비
- staged source root 전환
- blocker message 조립
- step 실행 루프
- summary 수집

완료 기준:

- [`execution_service.py`](/C:/sfe_master_ops/ops_core/workflow/execution_service.py)에서 파일 준비/환경 전환 코드 비중이 줄어든다.
- 실행 준비 전용 helper가 별도 파일로 분리된다.

---

## Step 2. monthly merge 책임 이동

진행 상태:

- `2026-03-22 완료`

목표:

- `monthly_source_merge.py`를 OPS 본체가 아니라 intake 준비 레이어로 본다.

방향:

- 장기적으로 `modules/intake/merge.py` 또는 유사 위치로 이동
- 현재 파일은 thin wrapper로 유지 가능

완료 기준:

- monthly merge가 “실행 전 source 준비” 책임으로 명확히 분리된다.
- 실제 병합 구현은 `modules/intake/merge.py`로 이동하고, `ops_core` 쪽은 thin wrapper만 유지한다.

---

## Step 3. staged source runtime helper 이동

진행 상태:

- `2026-03-22 완료`

목표:

- `_intake_staging` 입력 전환 책임을 `ops_core`에서 줄인다.

대상:

- `OPS_COMPANY_SOURCE_ROOT` override
- staging fallback copy
- source root 계산 보조

완료 기준:

- `execution_service.py`는 “staged input을 사용한다”만 선언하고,
  실제 경로 준비는 intake/runtime helper가 담당한다.
- 실제 staging 경로 계산, fallback copy, source root override 제어는 `modules/intake/runtime.py`가 담당한다.

---

## Step 4. script import/cache reset 책임 이동

진행 상태:

- `2026-03-22 완료`

목표:

- `execution_registry.py`에서 runtime cache cleanup 책임을 제거한다.

대상:

- `clear_execution_runtime_modules`
- script import reload 보조

이유:

- 실행 모드 정의 파일은 “무엇을 실행하는가”만 알아야 한다.
- “어떻게 import cache를 지우는가”까지 알 필요는 없다.

완료 기준:

- [`execution_registry.py`](/C:/sfe_master_ops/ops_core/workflow/execution_registry.py)는 모드/step 정의 전용이 된다.
- script import/cache reset은 [`common/runtime_helpers/import_cache.py`](/C:/sfe_master_ops/common/runtime_helpers/import_cache.py)에서 담당한다.

---

## Step 5. `orchestrator.py`와 `execution_service.py` 경계 정리

진행 상태:

- `2026-03-22 완료`

목표:

- 파이프라인 조정기가 두 개처럼 보이는 상태를 줄인다.

정리 원칙:

- `orchestrator.py`
  - Result Asset 평가 흐름 전용
- `execution_service.py`
  - 실제 실행 호출 전용

선택지:

1. `execution_service.py`가 `orchestrator.py`를 재사용
2. 둘의 역할을 더 명확히 분리하고 공용 모델만 공유

완료 기준:

- “평가 오케스트레이션”과 “실행 오케스트레이션”이 문서와 코드 모두에서 구분된다.
- `orchestrator.py`는 Result Asset 평가 흐름 진입점(`run_validation_pipeline`)으로,
  `execution_service.py`는 실제 실행 흐름 진입점(`run_runtime_execution_mode`)으로 명시된다.

---

## Step 6. `ops_core` 의미 재정의

진행 상태:

- `2026-03-22 완료`

목표:

- 물리적 이동 전에 개념부터 정리한다.

작업:

- 문서에서 `ops_core`를 “Validation / Orchestration Layer 구현 패키지”로 설명
- “플랫폼 중심 코어”처럼 읽히는 문구 제거

완료 기준:

- 문서, 주석, README 설명이 Sales Data OS 기준과 맞는다.
- `ops_core`는 “플랫폼 중심 코어”가 아니라 “Validation / Orchestration Layer 구현 패키지”로 설명된다.

---

## Step 7. 마지막에만 위치 이동 검토

진행 상태:

- `2026-03-22 완료`

목표:

- 실제로 `ops_core` 안에 Validation / Orchestration만 남은 뒤,
  그때 `modules/validation` 또는 `modules/ops` 이동을 판단한다.

검토 조건:

- intake/staging/monthly merge 책임이 충분히 빠졌는가
- execution runtime helper가 분리됐는가
- import bridge 없이도 역할 설명이 자연스러운가

가능한 최종안:

```text
modules/
  validation/
```

또는

```text
modules/
  ops/
```

문서 기준으로는 `modules/validation`이 더 안전하다.

이유:

- `OPS = Validation / Orchestration Layer`라는 의미가 더 직접적으로 드러난다.
- `ops`라는 이름만 쓰면 다시 시스템 전체처럼 오해될 수 있다.

Step 7 검토 결과:

- 개념적으로는 `modules/validation` 이동 방향이 맞다.
- 다만 현재 외부 Python 참조가 많고 실행 명령도 `ops_core.main:app` 기준이어서,
  `지금 즉시 hard rename`은 보류한다.
- 다음 안전한 방법은 `modules/validation bridge 패키지`를 먼저 만들고 점진 전환하는 방식이다.

상세 검토 문서:

- [`22_ops_core_location_migration_review.md`](/C:/sfe_master_ops/docs/architecture/22_ops_core_location_migration_review.md)

---

## 8. 파일별 분류표

### 계속 `ops_core`에 남겨도 되는 것

- `main.py`
- `api/crm_router.py`
- `api/prescription_router.py`
- `api/sandbox_router.py`
- `api/territory_router.py`
- `api/pipeline_router.py`
- `workflow/orchestrator.py`
- `workflow/schemas.py`
- `workflow/execution_models.py`

### 책임을 줄여야 하는 것

- `workflow/execution_service.py`
- `workflow/execution_registry.py`

### 장기적으로 밖으로 옮길 후보

- `workflow/monthly_source_merge.py`
- staged source runtime helper
- script import/cache cleanup helper

---

## 9. 하지 말아야 할 것

- 지금 바로 `ops_core` 폴더 rename
- 대규모 import 경로 일괄 변경
- `ops_core`에 raw 처리 책임 추가
- `ops_core`에 KPI 계산 책임 추가
- intake 책임을 다시 `ops_core` 쪽으로 되돌리는 변경

---

## 10. 성공 기준

이 계획이 성공했다고 보려면 아래가 가능해야 한다.

1. `ops_core`가 Validation / Orchestration 책임 중심으로 얇아진다.
2. intake/staging/monthly merge는 `modules/intake` 또는 별도 runtime helper로 빠진다.
3. `execution_registry.py`는 모드 정의 전용이 된다.
4. `orchestrator.py`와 `execution_service.py`의 경계가 명확해진다.
5. 그 뒤에야 `ops_core -> modules/validation` 이동을 안전하게 검토할 수 있다.

---

## 11. 최종 판단

냉정하게 보면, 장기적으로 `ops_core`는 `modules` 안 책임으로 들어가는 것이 맞다.

다만 정답 순서는 아래다.

1. **지금은 개념적 rename보다 책임 분리**
2. **그 다음 얇아진 `ops_core` 확인**
3. **마지막에만 위치 이동**

한 줄 요약:

**`ops_core`의 최종 목적지는 `modules/validation`에 가깝지만, 지금 당장 폴더를 옮기기보다 먼저 Validation / Orchestration 외 책임을 덜어내는 구조 리팩토링이 우선이다.**
