# SFE OPS Master Document Index

작성일: 2026-03-10

## 0. 이 문서의 역할

이 문서는 `sfe_ops_master_docs` 아래에 있는 마스터 문서 세트를
처음부터 끝까지 어떤 순서로 읽어야 하는지 안내하는 `진입 문서`다.

쉽게 말하면:

- 어떤 문서가 가장 중요한지
- 무엇부터 읽어야 하는지
- 각 문서가 무슨 역할인지

를 한 장으로 정리한 문서다.

---

## 1. 가장 먼저 기억할 문장

`SFE OPS의 중심은 Sandbox가 아니라 OPS Engine이며, 모든 모듈은 adapter -> module -> Result Asset -> OPS 순서로 연결된다.`

이 문장이 전체 문서 세트의 출발점이다.

---

## 2. 문서 우선순위

앞으로 SFE OPS 관련 판단은 아래 순서로 기준을 본다.

1. `sfe_ops_master_docs` 아래 마스터 문서 세트
2. 루트 `AGENTS.md`
3. 기존 `project_modules/00_SFE_OPS` 개별 문서

즉 기존 문서와 마스터 문서가 충돌하면
마스터 문서 세트를 우선한다.

---

## 3. 추천 읽기 순서

### Step 1. 전체 기준부터 읽기

1. `01_SFE_OPS_Master_PRD.md`
2. `02_SFE_OPS_Integrated_Plan.md`
3. `03_SFE_OPS_Technical_Stack.md`

이 3개를 먼저 읽으면 아래가 잡힌다.

- 왜 이 프로젝트를 하는가
- 5개 모듈을 어떤 순서로 여는가
- 기술은 어떤 역할로 쓰는가

### Step 2. 모듈별 역할 읽기

4. `04_Behavior_CRM_Implementation_Plan.md`
5. `07_Prescription_Data_Flow_Implementation_Plan.md`
6. `05_SFE_Sandbox_Implementation_Plan.md`
7. `06_Territory_Optimizer_Implementation_Plan.md`
8. `08_HTML_Builder_Implementation_Plan.md`

이 순서는 공식 통합 계획 순서와 같다.

즉:

`CRM -> Prescription -> Sandbox -> Territory -> HTML Builder`

### Step 3. 통합 구현 규칙 읽기

9. 루트 `AGENTS.md`

이 문서는 실제 작업할 때 계속 확인하는 규칙 문서다.

---

## 4. 문서별 역할 요약

### 4.1 `01_SFE_OPS_Master_PRD.md`

- 프로젝트의 최상위 정의
- 무엇을 만들고 무엇을 만들지 않는지 고정
- 세계관과 성공 기준 고정

### 4.2 `02_SFE_OPS_Integrated_Plan.md`

- 전체 기획 순서
- 어떤 모듈을 어떤 논리로 여는지 고정
- 단계 전환 기준 고정

### 4.3 `03_SFE_OPS_Technical_Stack.md`

- 공식 기술 스택 정리
- 각 기술의 역할과 금지할 오해 정리

### 4.4 `04_Behavior_CRM_Implementation_Plan.md`

- CRM 출발 자산 구조 정리
- 병원/지점/담당자 공통축 출발점 정리

### 4.5 `05_SFE_Sandbox_Implementation_Plan.md`

- Sandbox를 허브가 아니라 분석엔진으로 재정의
- 통합 분석 자산 구조 정리

### 4.6 `06_Territory_Optimizer_Implementation_Plan.md`

- Territory의 공식 입력과 실행 자산 구조 정리
- Sandbox 후속 Allocation 모듈로 위치 고정

### 4.7 `07_Prescription_Data_Flow_Implementation_Plan.md`

- Prescription 범용 검증 구조 정리
- hospital/pharmacy/wholesaler 키 원칙 정리

### 4.8 `08_HTML_Builder_Implementation_Plan.md`

- Builder를 최종 표현 모듈로 고정
- 범용 보고 입력 구조 정리

### 4.9 `AGENTS.md`

- 실제 작업 중 항상 따라야 하는 통합 규칙
- 문서 우선순위, 설명 방식, 구현 순서 원칙 정리

---

## 5. 읽을 때 꼭 지킬 해석 원칙

아래 원칙을 놓치면 다시 문서가 흔들린다.

1. 중심은 `OPS Engine`이다.
2. Sandbox는 중요하지만 허브가 아니다.
3. raw는 OPS로 바로 가지 않는다.
4. 먼저 adapter가 raw를 공통 구조로 번역한다.
5. module은 Result Asset을 만든다.
6. OPS는 Result Asset만 검증하고 다음 연결을 판단한다.
7. 회사 맞춤보다 범용 규칙이 먼저다.

---

## 6. 이 문서 세트의 목표

이 문서 세트의 목표는 문서를 더 많이 만드는 것이 아니다.

진짜 목표는 아래다.

1. 기준점을 하나로 모은다.
2. 문서끼리 충돌하지 않게 한다.
3. 구현 전에 세계관이 흔들리지 않게 한다.
4. 비개발자도 같은 기준으로 설명을 따라갈 수 있게 한다.

---

## 7. 한 줄 결론

`SFE OPS 마스터 문서 세트는 PRD -> 통합 Plan -> 기술 스택 -> 모듈별 구현계획 -> AGENTS 순서로 읽어야 하며, 모든 해석은 OPS 중심 세계관과 adapter -> module -> Result Asset -> OPS 원칙 위에서만 이뤄져야 한다.`
