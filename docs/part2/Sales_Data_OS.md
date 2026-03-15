아래는 **Codex CLI 전용 마스터 프롬프트**다.
목표는 현재 `SFE OPS` 저장소를 **“OPS 중심 구조”에서 “Sales Data OS 중심 구조”로 재정의**하고, 실제 코드/문서/폴더/네이밍까지 일관되게 정리하도록 지시하는 것이다.

그대로 붙여 넣어도 되고, 저장소 상황에 맞게 회사명/폴더명만 바꿔도 된다.

---

# Codex CLI Master Prompt

## SFE OPS → Sales Data OS 구조 재정의 및 리팩토링

당신은 이 저장소의 **시니어 제품 아키텍트 + 리팩토링 리드 엔지니어**다.
목표는 현재 프로젝트를 단순한 `OPS 운영 콘솔`이 아니라, **제약 영업 데이터 통합/검증/분석/의사결정 지원 플랫폼인 “Sales Data OS”**로 재정의하고, 코드 구조·문서·네이밍·런북·UI 설명까지 일관되게 정리하는 것이다.

중요:
이 작업은 단순 rename이 아니다.
**아키텍처 관점에서 시스템의 중심을 재정의**하는 작업이다.

---

## 0. 프로젝트 재정의 목표

현재 구조는 개념상 `OPS`가 중심처럼 보이지만, 실제 역할을 보면 OPS는 계산 엔진이 아니라 아래 역할에 가깝다.

* 중간 매핑
* 품질 검증
* 다음 단계 전달 판단
* 파이프라인 운영 통제

즉 OPS는 시스템 전체가 아니라 **Validation / Orchestration Layer**에 가깝다.

따라서 시스템 전체를 다음처럼 재정의한다.

### 새로운 최상위 정의

* 시스템명: **Sales Data OS**
* 목적: 제약 영업 데이터를 표준화하고, KPI를 계산하고, 검증하고, 분석/의사결정 레이어에 전달하는 플랫폼

### 레이어 구조

1. **Data Layer**

   * CRM / Sales / Target / Prescription / Company Master raw data
2. **Adapter Layer**

   * raw → standard schema 정규화
3. **Core Engine Layer**

   * KPI Engine
   * module-specific business calculation
4. **Validation Layer**

   * 기존 OPS의 핵심 역할
   * 품질 검증 / 매핑 검증 / 다음 단계 전달 판단
5. **Intelligence Layer**

   * Sandbox
   * Territory
   * Prescription
   * RADAR (예정)
6. **Presentation Layer**

   * Builder
   * HTML / payload / preview / download

---

## 1. 이번 작업의 핵심 원칙

반드시 아래 원칙을 지켜라.

### 원칙 A. 기존 작동 흐름을 최대한 보존

* 현재 동작하는 파이프라인을 깨지 않는다.
* 먼저 분석하고, 최소 침습적으로 구조를 바꾼다.
* 작동 보존 > 과도한 리네이밍

### 원칙 B. 개념과 코드 구조를 일치

* 문서상 설명과 실제 코드 구조가 최대한 일치해야 한다.
* “OPS가 시스템 중심”처럼 보이는 표현을 걷어내고, “OPS는 validation/orchestration layer”로 재정의한다.

### 원칙 C. KPI는 단일 소스 유지

* KPI 재계산 중복 금지
* `modules/kpi/*.py`를 단일 계산 소스로 유지
* Builder / Sandbox / Territory / Prescription / RADAR는 KPI를 재계산하지 않는다.

### 원칙 D. 포트폴리오 설득력 강화

* 결과적으로 이 저장소는 “운영 콘솔”이 아니라
  **Sales Intelligence Platform / Sales Data OS**처럼 보이게 만들어라.

---

## 2. 먼저 해야 할 일: 저장소 분석

아무 수정도 하기 전에 아래를 수행하라.

1. 전체 폴더 구조 스캔
2. `ops`, `ops_core`, `ops_console`, `ops_validation`, `ops_standard`, `OPS` 등의 명칭이 들어간 파일/폴더/문서 검색
3. 실제 의존 관계 파악

   * Adapter
   * KPI Engine
   * Validation
   * Sandbox
   * Territory
   * Prescription
   * Builder
4. 엔트리포인트 파악

   * FastAPI
   * Streamlit console
   * scripts
5. 현재 네이밍이 개념적으로 잘못된 곳을 분류

   * “실제 OPS 역할”
   * “실제 Core Engine 역할”
   * “실제 Presentation 역할”

분석 결과를 먼저 문서로 요약하라.

### 생성할 분석 문서

`docs/architecture/current_state_audit.md`

문서에는 반드시 포함:

* 현재 구조 요약
* 실제 시스템 중심이 무엇인지
* OPS가 실제로 맡는 역할
* rename 위험 구간
* 안전하게 바꿀 수 있는 구간
* 보류해야 할 구간

---

## 3. 목표 아키텍처 문서 작성

다음 문서를 새로 작성하라.

### 생성 문서

`docs/architecture/sales_data_os_architecture.md`

반드시 포함할 내용:

1. 시스템 한 줄 정의
2. 왜 OPS 중심 정의가 어색했는지
3. Sales Data OS 재정의
4. 레이어 구조
5. 모듈별 책임
6. 데이터 흐름
7. KPI 단일 소스 원칙
8. Validation Layer로서 OPS의 위치
9. Intelligence Layer에서 Sandbox / Territory / Prescription / RADAR 역할
10. Builder의 역할
11. 포트폴리오 관점 설명 문장

문체는 기획 문서 + 아키텍처 문서 중간 톤으로 작성하라.

---

## 4. 변경 전략 수립 문서 작성

무작정 rename하지 말고, 아래 문서를 먼저 작성하라.

### 생성 문서

`docs/architecture/refactor_plan_sales_data_os.md`

반드시 아래 형식으로 작성:

* 변경 목표
* 비목표
* 영향 범위
* 리스크
* 단계별 실행 계획
* 롤백 포인트
* 테스트 항목

단계는 최소 아래처럼 나눠라.

### Phase 1

문서/설명/네이밍 재정의
(가장 안전)

### Phase 2

코드 내 개념명 정리
(변수명, 주석, docstring, UI 라벨)

### Phase 3

폴더/모듈 alias 또는 점진적 rename
(필요 시만)

### Phase 4

RADAR를 Intelligence Layer에 정식 편입할 준비

---

## 5. 실제 코드/문서 변경 지시

이제 실제 변경을 수행하라.

### 5-1. RUNBOOK 재작성

기존 RUNBOOK을 아래 관점으로 재작성하라.

* 전체 시스템명은 `Sales Data OS`
* OPS는 `Validation / Orchestration Layer`
* 현재 실행 흐름은 유지
* 사용자가 혼란 없이 이해할 수 있도록 설명 개선

가능하면 기존 RUNBOOK은 보존하고, 아래 새 문서를 만든다.

`docs/runbook/sales_data_os_runbook.md`

필수 포함:

* 전체 아키텍처 개요
* 운영 콘솔 역할
* 파이프라인 흐름
* 모듈별 책임
* KPI 엔진 위치
* Builder 역할
* OPS 역할 재정의

---

### 5-2. UI/문서 라벨 정리

아래 성격의 표현을 점검하고 수정하라.

예시:

* “OPS가 계산한다”처럼 읽히는 표현 제거
* “OPS 시스템” → “Sales Data OS”
* “OPS 결과” → 맥락에 따라 “validation result”, “platform result”, “module result” 등으로 구체화

단, 사용자가 이미 익숙한 용어가 있으면 무리한 전면 교체는 금지한다.
필요하면 아래처럼 병기하라.

* `Sales Data OS Console (기존 OPS Console)`
* `Validation Layer (OPS)`

---

### 5-3. 코드 주석 / docstring 정리

아래 기준으로 수정하라.

* `ops`가 전체 시스템처럼 설명된 docstring 수정
* `modules/kpi`는 KPI single source로 설명
* Builder는 “render only, no recalc” 원칙 명시
* Sandbox / Territory / Prescription / RADAR는 Intelligence Layer 소속으로 설명

---

### 5-4. 엔트리포인트 설명 정리

FastAPI, Streamlit, scripts의 역할을 다음처럼 정리하라.

* API: 파이프라인 제어 및 실행 인터페이스
* Console: 운영 검증용 UI
* Scripts: raw 생성 / 정규화 / 검증 / 통합 실행 유틸리티

---

## 6. 폴더/모듈 rename 규칙

중요:
실제 import 경로가 많이 얽혀 있으면 **즉시 rename하지 말고 alias 전략**을 먼저 검토하라.

권장 전략:

* 1차: 문서, 주석, UI 라벨만 변경
* 2차: 새 개념명 alias 도입
* 3차: 테스트 통과 후 실제 rename 검토

예:

* `ops_core`는 당장 rename하지 말고 유지 가능
* 대신 문서에서 `platform orchestration API`로 설명
* `ops_validation`은 유지 가능하지만 문서상 `validation outputs`로 재정의
* `ops_standard`는 유지 가능하지만 문서상 `standardized data layer`로 설명

즉, **코드 안정성이 우선**이다.

---

## 7. RADAR 편입을 고려한 구조 정리

이번 작업은 RADAR를 즉시 완성하는 것이 아니다.
하지만 RADAR가 들어갈 자리를 명확히 만들어야 한다.

RADAR는 아래로 정의하라.

* Layer: Intelligence Layer
* Input:

  * KPI engine output
  * validation-approved result asset
  * sandbox summary metrics
* Responsibility:

  * signal detection
  * issue prioritization
  * decision option templating
* Non-goal:

  * KPI 재계산
  * 현장 액션 자동 결정
  * 원인 확정

이 내용을 아키텍처 문서와 refactor plan에 반영하라.

---

## 8. 반드시 수정/생성할 산출물

최소한 아래 파일들을 생성 또는 수정하라.

### 새로 만들 문서

* `docs/architecture/current_state_audit.md`
* `docs/architecture/sales_data_os_architecture.md`
* `docs/architecture/refactor_plan_sales_data_os.md`
* `docs/runbook/sales_data_os_runbook.md`

### 수정 대상

* 기존 RUNBOOK 관련 문서
* README 또는 메인 소개 문서
* 운영 콘솔 설명 문구
* 주요 모듈 docstring
* KPI module docstring
* Builder 관련 설명 문서

---

## 9. 최종 결과 보고 형식

작업이 끝나면 아래 형식으로 결과를 정리하라.

### 1. What changed

* 변경한 파일 목록
* 변경 목적 요약

### 2. Architecture summary

* 이전 구조 정의
* 새 구조 정의
* OPS의 새 위치

### 3. Safe changes vs deferred changes

* 바로 반영한 것
* 위험해서 보류한 것

### 4. Next recommended step

* RADAR 설계 연결 포인트
* 추가 rename 필요 여부
* 테스트 보완 필요 사항

---

## 10. 작업 방식 제약

반드시 지켜라.

* 먼저 분석 → 그 다음 변경
* 한 번에 과도한 rename 금지
* import 깨질 수 있는 rename은 신중히
* 실행 흐름 보존
* 문서/개념 정리가 코드보다 먼저
* 기존 작동 검증이 가능한 범위 안에서만 변경
* 변경 이유를 주석/문서로 남길 것

---

## 11. 최종 목표 문장

이번 리팩토링의 최종 목표는 다음 문장을 시스템 전체에서 성립시키는 것이다.

**“이 프로젝트는 OPS가 중심인 도구가 아니라, KPI 계산·검증·분석·의사결정 지원이 연결된 제약 영업용 Sales Data OS이며, OPS는 그 안의 Validation/Orchestration Layer다.”**

---

## 12. 실행 시작

이제 바로 시작하라.

작업 순서:

1. 저장소 분석
2. 현재 상태 감사 문서 작성
3. 목표 아키텍처 문서 작성
4. 리팩토링 계획 문서 작성
5. 안전한 범위의 문서/라벨/주석 수정
6. 결과 요약 보고

불필요한 대규모 rename은 하지 말고,
**“개념 정렬 → 문서 정렬 → UI 정렬 → 코드 정렬”** 순서로 진행하라.
