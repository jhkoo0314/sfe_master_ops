# AGENTS.md

## Mission

이 저장소의 최상위 시스템 개념은 **SFE OPS**가 아니라 **Sales Data OS**다.  
모든 구현, 문서, 설명, 네이밍, UI 문구는 이 원칙을 기준으로 정렬한다.

이 프로젝트는 제약 영업 데이터를 표준화하고, KPI를 계산하고, 검증하고, 분석 및 의사결정 레이어에 전달하는 **Sales Data OS**다.  
`OPS`는 시스템 전체가 아니라 그 안의 **Validation / Orchestration Layer**다.

---

## Core Architecture Principle

항상 아래 구조를 기준으로 판단한다.

1. **Data Layer**
   - CRM / Sales / Target / Prescription / Master raw data

2. **Adapter Layer**
   - raw 데이터를 표준 스키마로 정규화

3. **Core Engine Layer**
   - KPI Engine
   - 모듈별 비즈니스 계산 로직

4. **Validation / Orchestration Layer**
   - 기존 OPS의 실제 역할
   - 품질 검증
   - 매핑 검증
   - 다음 단계 전달 판단
   - 파이프라인 통제

5. **Intelligence Layer**
   - Sandbox
   - Territory
   - Prescription
   - RADAR

6. **Presentation Layer**
   - Builder
   - HTML / preview / payload / download

---

## Naming Policy

### Top-level naming
- 시스템 전체를 설명할 때는 반드시 `Sales Data OS`를 사용한다.
- `OPS 시스템`, `OPS 전체 플랫폼` 같은 표현은 금지한다.
- `OPS`는 반드시 다음 의미로만 사용한다.
  - `Validation Layer`
  - `Orchestration Layer`
  - `운영 통제 레이어`

### Allowed phrasing
- `Sales Data OS`
- `Validation Layer (OPS)`
- `OPS validation result`
- `platform result`
- `module result`
- `standardized data layer`

### Disallowed phrasing
- `OPS가 모든 계산을 담당한다`
- `OPS가 시스템 중심이다`
- `OPS가 KPI를 계산한다`
- `Builder가 KPI를 다시 계산한다`
- `Sandbox가 CRM KPI를 다시 계산한다`
- `RADAR가 KPI를 다시 계산한다`

---

## KPI Single Source Rule

KPI는 반드시 **단일 계산 소스**를 유지한다.

### Source of truth
- `modules/kpi/crm_engine.py`
- `modules/kpi/sandbox_engine.py`
- `modules/kpi/territory_engine.py`
- `modules/kpi/prescription_engine.py`

### Mandatory rules
- Builder는 KPI를 재계산하지 않는다.
- Sandbox는 CRM KPI를 재계산하지 않는다.
- Territory는 KPI를 재계산하지 않는다.
- Prescription Builder는 KPI를 재계산하지 않는다.
- RADAR는 KPI를 재계산하지 않는다.
- KPI 계산 로직이 필요하면 반드시 `modules/kpi/*`로 수렴시킨다.

### Forbidden patterns
- presentation 레이어에서 KPI 재계산
- payload 조립 단계에서 KPI 재계산
- 임시 스크립트 내부에서 중복 KPI 계산
- 동일 KPI 공식을 여러 파일에 복붙

---

## OPS Role Rule

`OPS`는 아래 역할만 가진다.

- 중간 매핑
- 품질 검증
- 전달 가능 여부 판단
- 파이프라인 운영 통제
- validation output 관리

`OPS`는 아래 역할을 가지지 않는다.

- 전체 시스템의 최상위 개념
- KPI 단일 계산 엔진
- BI 분석 엔진
- 의사결정 엔진
- 보고서 렌더러

문서, 주석, UI, README, RUNBOOK 어디에서도 OPS를 시스템 전체처럼 설명하지 않는다.

---

## Module Responsibility Rule

각 모듈의 책임은 아래처럼 유지한다.

### Adapter
- raw를 standard schema로 변환
- 원본 의미를 보존
- `raw`와 `standard`를 혼동하지 않는다

### KPI Engine
- 공식 KPI 계산의 단일 소스
- 지표 공식 변경 시 여기서만 수정

### Validation Layer (OPS)
- 품질 검증
- 매핑 검증
- 전달 판단
- 단계별 실행 통제

### Sandbox
- 분석
- 드릴다운
- 비교
- 추이 해석
- 원인 탐색 보조

### Territory
- 권역/담당자 활동 구조 분석
- 지역/커버리지 관점 인텔리전스 제공

### Prescription
- 처방 흐름 및 관련 검증 결과 제공

### RADAR
- signal detection
- issue prioritization
- decision option templating
- KPI 재계산 금지
- 현장 액션 자동 결정 금지
- 원인 확정 금지

### Builder
- 렌더링 전용
- payload 소비 전용
- 재계산 금지

---

## Builder Rule

Builder는 항상 **render-only layer**로 유지한다.

### Builder must
- 이미 계산된 payload만 사용
- HTML / preview / asset 생성만 담당
- 무거운 데이터는 manifest + asset 구조를 우선 고려

### Builder must not
- raw 직접 해석
- KPI 재계산
- 비즈니스 로직 재구현
- 모듈 책임 침범

Builder 관련 주석/docstring에는 가능하면 아래 문장을 유지한다.

- `Builder is render-only and does not recalculate KPI.`
- `Builder consumes validated payloads only.`

---

## Documentation Rule

모든 문서와 설명은 아래 원칙을 따른다.

### Documentation must
- 시스템 전체를 `Sales Data OS`로 설명
- OPS를 `Validation / Orchestration Layer`로 설명
- KPI single source 원칙 명시
- 각 레이어 책임을 구분해서 설명

### Documentation must not
- 현재 구조를 단순 대시보드처럼 축소 설명
- OPS를 플랫폼 전체로 오해하게 만들기
- 모듈 책임을 섞어서 설명
- Builder와 계산 엔진의 역할을 혼합 설명

---

## Refactor Rule

리팩토링 시에는 항상 아래 순서를 따른다.

1. 개념 정렬
2. 문서 정렬
3. UI/라벨 정렬
4. 주석/docstring 정렬
5. 안전한 코드 구조 정리
6. 마지막에 필요한 경우에만 실제 rename 검토

### Mandatory constraints
- 먼저 분석하고, 그 다음 수정한다.
- 작동 중인 import 경로는 성급히 rename하지 않는다.
- 대규모 rename보다 alias / 설명 정리를 우선한다.
- 기존 파이프라인이 깨질 위험이 있으면 rename을 보류한다.
- 코드 안정성이 개념적 깔끔함보다 우선이다.

---

## UI Label Rule

UI에서는 사용자가 기존 용어에 익숙할 수 있으므로 점진적으로 정렬한다.

### Preferred pattern
- `Sales Data OS Console`
- `Validation Layer (OPS)`
- `OPS Validation Result`
- `Module Result`
- `Builder Preview`

### Avoid
- `OPS Main System`
- `OPS Dashboard Platform`
- `OPS Intelligence Engine`

---

## Result Asset Rule

Result asset은 모듈 계산 결과와 검증 결과를 다음 단계에 안전하게 전달하는 표준 산출물이다.

### Result asset principles
- 다음 단계는 result asset을 소비한다.
- result asset 이후 단계에서 의미를 다시 계산하지 않는다.
- payload는 계산 결과의 표현이지 계산 엔진이 아니다.
- validation 승인된 asset만 Intelligence/Builder로 전달한다.

---

## RADAR Readiness Rule

RADAR는 즉시 완성할 필요는 없지만, 구조적으로 항상 아래 위치에 놓는다.

- Layer: `Intelligence Layer`
- Input:
  - KPI engine output
  - validation-approved result asset
  - sandbox summary metrics
- Responsibility:
  - signal detection
  - issue prioritization
  - decision option templating

### RADAR must not
- KPI 재계산
- 현장 액션 자동 결정
- 원인 단정
- 스케줄/동선 수준의 실행 지시

---

## Comment & Docstring Rule

주석과 docstring은 아래 기준으로 작성한다.

### Prefer
- 역할 기반 설명
- 어느 레이어 책임인지 명시
- 재계산 금지 여부 명시
- 입력/출력 경계 명확화

### Avoid
- 모호한 “중앙 엔진”, “핵심 시스템” 표현
- Builder/OPS가 모든 것을 처리하는 것처럼 보이는 표현
- 실제 책임보다 과장된 설명

---

## Change Acceptance Checklist

아래 조건을 만족해야 좋은 변경이다.

- [ ] 시스템 전체 설명이 `Sales Data OS` 기준으로 정렬되었는가
- [ ] OPS가 Validation / Orchestration Layer로 내려왔는가
- [ ] KPI single source 원칙이 유지되는가
- [ ] Builder가 render-only 원칙을 지키는가
- [ ] Sandbox / Territory / Prescription / RADAR 책임이 구분되는가
- [ ] 문서와 코드 설명이 서로 충돌하지 않는가
- [ ] 작동 중인 파이프라인을 깨지 않았는가

---

## Final Definition

이 저장소를 설명할 때는 항상 아래 정의를 기준으로 삼는다.

**이 프로젝트는 OPS가 중심인 도구가 아니라, KPI 계산·검증·분석·의사결정 지원이 연결된 제약 영업용 Sales Data OS이며, OPS는 그 안의 Validation / Orchestration Layer다.**