# 18. Real Company Raw Input Flow

## 문서 목적

이 문서는 **실제 회사 raw 데이터가 들어왔을 때** Sales Data OS가 어떻게 동작하는지 설명하는 기준 문서다.

중요:

- 이 문서는 테스트용 raw 생성기 문서가 아니다.
- 실제 운영에서 더 중요한 것은 `raw 생성`이 아니라 `raw 수용 -> 해석 -> 정규화 -> 검증 -> 전달` 흐름이다.
- 테스트용 raw 생성 구조는 `docs/architecture/17_raw_generator_refactor_plan.md`를 참고하되, 우선순위는 이 문서보다 낮다.
- 실제 운영에서 바깥에 보이는 입력 엔진은 하나여야 하며, 회사별 새 스크립트가 아니라 `scenario + mapping + rules` 업데이트로 차이를 흡수하는 방향을 기준으로 본다.

이 문서는 Part2 진행 상태 문서가 아니라 실제 입력 처리 구조 설명 문서다.  
진행 상태 단일 기준은 계속 `docs/architecture/12_part2_status_source_of_truth.md`를 따른다.

---

## 1. 핵심 질문

실제 운영에서 중요한 질문은 아래다.

1. 실제 회사 raw 파일이 들어오면 어디에 저장되는가
2. 회사마다 다른 raw 파일 구조를 누가 해석하는가
3. 월별 파일이 들어오면 어떻게 병합되는가
4. 실행모드에 따라 어떤 단계까지 도는가
5. `PASS/WARN/APPROVED`는 어디서 왜 결정되는가
6. 최종적으로 어떤 결과물이 만들어지는가

이 문서는 이 질문에 답하기 위해 만든다.

---

## 2. 가장 중요한 원칙

실제 회사 raw가 들어왔을 때 Sales Data OS는 아래 원칙으로 움직인다.

1. raw를 OPS가 직접 읽지 않는다.
2. 먼저 회사별 raw를 Adapter가 표준 구조로 바꾼다.
3. KPI 계산은 `modules/kpi/*`에서만 한다.
4. OPS는 Validation / Orchestration Layer로서 품질과 전달 가능 여부를 판단한다.
5. Builder는 이미 계산되고 검증된 payload만 읽는다.

즉 핵심 흐름은 아래다.

`real company raw -> company source path -> adapter -> core engine/module -> validation layer(OPS) -> intelligence -> builder`

---

## 3. 실제 입력 시작점

### 3.1 입력 경로

실제 회사 raw는 아래 두 방식으로 들어올 수 있다.

#### 방식 1. 운영 콘솔 업로드

운영 콘솔에서 사용자가 파일을 올린다.

관련 위치:

- `ui/console/tabs/upload_tab.py`
- `ui/console/state.py`

#### 방식 2. 회사 폴더 직접 저장

이미 회사별 source 폴더에 raw 파일이 존재할 수 있다.

기준 경로:

```text
data/company_source/{company_key}/
```

예:

```text
data/company_source/daon_pharma/
data/company_source/hangyeol_pharma/
data/company_source/monthly_merge_pharma/
```

### 3.2 왜 `company_key`가 중요한가

회사명은 바뀌거나 비슷할 수 있지만 `company_key`는 고정 식별자다.  
그래서 모든 실행/저장/검증 경로는 회사명 대신 `company_key` 기준으로 움직인다.

---

## 4. 실제 raw를 누가 해석하는가

### 4.1 회사 프로필이 먼저 결정된다

실제 회사 raw가 들어오면 먼저 어떤 회사인지 정한다.

관련 위치:

- `common/company_registry.py`
- `common/company_profile.py`
- `ui/console/paths.py`

여기서 정해지는 것:

- 어떤 회사인지
- 어느 source 경로를 쓸지
- 어떤 adapter 설정을 쓸지

### 4.2 왜 회사 프로필이 필요한가

회사마다 raw 파일 구조가 조금씩 다를 수 있기 때문이다.

예를 들면:

- 컬럼명이 다를 수 있음
- 파일명이 다를 수 있음
- 병원/담당자/제품 식별 방식이 다를 수 있음

이 차이는 OPS가 직접 감당하지 않고, 회사 프로필 + Adapter 설정에서 먼저 흡수한다.

---

## 5. 월별 raw가 들어왔을 때

### 5.1 기본 구조

월별 파일은 아래 경로에 들어간다.

```text
data/company_source/{company_key}/monthly_raw/YYYYMM/
```

예:

```text
data/company_source/monthly_merge_pharma/monthly_raw/202501/
data/company_source/monthly_merge_pharma/monthly_raw/202502/
```

### 5.2 어떤 파일이 월별 병합 대상인가

현재 병합 대상은 아래 4개다.

- `crm_activity`
- `sales`
- `target`
- `prescription`

관련 위치:

- `modules/intake/merge.py`

### 5.3 실제 동작 방식

파이프라인 실행 전에 아래를 먼저 본다.

1. `monthly_raw` 폴더가 있는지
2. 월별 파일이 몇 개월 들어왔는지
3. 업로드 파일로 덮어쓸 항목은 있는지

그 다음 자동으로:

1. 월별 파일을 읽고
2. 파일 종류별로 세로 병합하고
3. 표준 source 파일 위치에 저장한다

즉 월별 raw는 실행 전에 **보조 입력 구조**로 처리되고, 이후 파이프라인은 평소와 같은 표준 source 파일을 기준으로 계속 진행한다.

---

## 6. 실행할 때 실제로 무슨 일이 일어나는가

관련 위치:

- `modules/validation/workflow/execution_service.py`
- `modules/validation/workflow/execution_registry.py`
- `ui/console/tabs/pipeline_tab.py`

실행 순서는 아래와 같다.

1. 활성 회사 선택
2. 실행모드 선택
3. 업로드 파일이 있으면 source 경로에 반영
4. `monthly_raw`가 있으면 자동 병합
5. 실행모드에 필요한 필수 입력이 있는지 확인
6. 모듈 단계를 순서대로 실행
7. 각 단계의 summary를 읽어 결과를 묶음
8. run 저장과 실행 분석 문서를 남김

---

## 7. 실행모드는 왜 중요한가

실행모드는 “어디까지 볼 것인가”를 정하는 운영 선택지다.

예:

- `CRM -> PDF`
- `CRM -> Sandbox`
- `Sandbox -> HTML`
- `CRM -> Territory`
- `통합 실행`

즉 실제 회사 raw가 들어와도 항상 전체를 다 돌리는 것은 아니다.  
운영 목적에 따라 필요한 단계만 선택할 수 있다.

---

## 8. Adapter 이후에는 어떻게 흘러가는가

### 8.1 Adapter Layer

raw를 표준 스키마로 바꾼다.

관련 위치:

- `adapters/crm/*`
- `adapters/sandbox/*`
- `adapters/prescription/*`
- `adapters/territory/*`

### 8.2 Core Engine / Module Layer

모듈별 계산과 결과 자산 조립을 수행한다.

관련 위치:

- `modules/crm/*`
- `modules/sandbox/*`
- `modules/prescription/*`
- `modules/territory/*`
- `modules/kpi/*`

중요:

- KPI 계산은 `modules/kpi/*`가 단일 소스다.
- Builder나 RADAR가 KPI를 다시 계산하지 않는다.

### 8.3 Validation Layer (OPS)

품질과 전달 가능 여부를 판단한다.

관련 위치:

- `modules/validation/api/*_router.py`
- `scripts/validate_*_with_ops.py`

OPS가 하는 일:

- 매핑 상태 확인
- 품질 점수 계산
- 다음 모듈로 넘길 수 있는지 판단

OPS가 하지 않는 일:

- 시스템 전체 KPI 계산
- 보고서 렌더링
- 원본 raw 직접 해석

---

## 9. 왜 PASS / WARN / APPROVED가 나오는가

각 단계는 summary 파일을 남긴다.  
이 summary 안의 품질 상태와 점수를 기준으로 단계 결과가 정해진다.

예:

- `PASS`
  - 다음 단계로 넘겨도 되는 품질 상태
- `WARN`
  - 실행은 가능하지만 운영 점검이 필요한 상태
- `APPROVED`
  - 승인 기준을 만족해 다음 의사결정 단계로 활용 가능한 상태

운영 콘솔에서는 이제 아래를 같이 보여준다.

- 원래 판정 메모(`reasoning_note`)
- 사람이 읽는 해석 문장
- 근거 수치

관련 위치:

- `ui/console/analysis_explainer.py`
- `ui/console/tabs/artifacts_tab.py`
- `ui/console/runner.py`

즉 사용자는 단순히 `WARN`만 보는 것이 아니라, **왜 WARN인지**를 같이 읽을 수 있다.

---

## 10. 실제 WARN 사례 해석 예시

`monthly_merge_pharma` 점검에서 Territory 포함 모드는 `WARN`이 나왔다.

하지만 의미는 “데이터 부족으로 실패”가 아니다.

실제 의미:

- 커버리지는 충분함
- 활동 표준 파일도 생성됨
- 실행은 끝까지 완료됨
- 다만 담당자 배치 불균형이 감지돼 운영 점검 경고가 발생

즉 이 구조는 실제 운영에서 생길 수 있는 이상 징후를 걸러내는 역할을 한다.

---

## 11. 최종 결과물은 무엇인가

실행이 끝나면 아래가 남는다.

### 11.1 표준화 결과

```text
data/ops_standard/{company_key}/...
```

### 11.2 검증 결과

```text
data/ops_validation/{company_key}/crm/
data/ops_validation/{company_key}/sandbox/
data/ops_validation/{company_key}/territory/
data/ops_validation/{company_key}/prescription/
data/ops_validation/{company_key}/radar/
```

### 11.3 Builder 결과

```text
data/ops_validation/{company_key}/builder/*.html
```

### 11.4 실행 분석 문서

```text
data/ops_validation/{company_key}/pipeline/latest_execution_analysis.md
```

이 문서에는 아래가 포함된다.

- 실행모드
- 전체 상태
- 단계별 판정
- 해석 문장
- 근거 수치

---

## 12. 운영 관점에서 더 중요한 문서 우선순위

실제 회사 raw가 들어왔을 때의 운영 기준은 아래 순서로 보면 된다.

1. `AGENTS.md`
2. `SKILL.md`
3. `docs/architecture/12_part2_status_source_of_truth.md`
4. 이 문서 `docs/architecture/18_real_company_raw_input_flow.md`
5. `README.md`
6. `RUNBOOK.md`
7. `STRUCTURE.md`

테스트 데이터 생성 문서는 그 다음이다.

- `docs/architecture/17_raw_generator_refactor_plan.md`

즉 `17번`은 보조 문서이고, 실제 운영 기준은 이 문서가 더 중요하다.

---

## 13. 최종 정리

실제 회사 raw가 들어왔을 때 Sales Data OS의 핵심은 아래다.

1. raw를 받는다.
2. `company_key` 기준으로 저장/선택한다.
3. 회사 프로필과 Adapter가 차이를 흡수한다.
4. 실행모드에 따라 필요한 단계만 실행한다.
5. OPS가 품질과 전달 가능 여부를 판단한다.
6. Intelligence와 Builder가 승인된 결과만 소비한다.
7. 사용자는 실행 결과와 판정 이유를 함께 읽는다.

한 줄로 요약하면 아래다.

**실제 회사 raw 입력에서 중요한 것은 생성기가 아니라, raw를 안전하게 수용하고 표준화하고 검증하고 다음 단계로 넘기는 Sales Data OS의 운영 흐름이다.**
