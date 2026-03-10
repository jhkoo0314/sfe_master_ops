# SFE Sandbox Implementation Plan

작성일: 2026-03-10

## 0. 이 문서의 역할

이 문서는 SFE Sandbox 모듈을 아무것도 없는 상태에서 다시 시작하기 위한 공식 구현계획서다.

이 문서의 가장 중요한 목적은 Sandbox를 다시 `정확한 자리`에 놓는 것이다.

즉:

- Sandbox는 중요하다
- 하지만 전체 허브는 아니다
- OPS가 허용한 자산 조합을 분석하는 엔진이다

---

## 1. 모듈 한 줄 정의

`SFE Sandbox는 OPS가 허용한 CRM, 실적, 목표, 필요 시 Prescription 자산을 조합해 통합 분석 자산을 만드는 핵심 분석엔진이다.`

---

## 2. OPS 세계관 안에서의 위치

Sandbox는 아래처럼 이해해야 한다.

1. 공통규칙엔진이 아니다.
2. 분석엔진이다.
3. 여러 자산을 선택적으로 받아 시나리오별 분석을 수행한다.
4. 분석 결과를 다시 Result Asset으로 OPS에 돌려준다.

틀린 이해:

- Sandbox가 전체 허브다
- 모든 모듈은 Sandbox를 반드시 거쳐야 한다

맞는 이해:

- OPS가 중심
- Sandbox는 핵심 분석 모듈

---

## 3. 공식 입력 구조

Sandbox의 공식 입력은 고정 파이프라인이 아니다.

기본 구조는 아래다.

`crm_result_asset + sales + targets (+ prescription_result_asset 선택) -> sandbox_reference_master -> sandbox_domain_standard -> sandbox_input_standard -> sandbox_result_asset -> OPS`

핵심은 아래다.

1. 입력 조합은 시나리오에 따라 달라진다.
2. 하지만 OPS가 허용한 자산만 들어온다.
3. Sandbox는 raw의 차이를 직접 감당하는 허브가 아니다.

---

## 4. 공통 키 기준

Sandbox에서 중요한 기준은 아래다.

1. `hospital_id`
2. `branch_id`
3. `rep_id`
4. `product_id`
5. `metric_month`

이 키가 흐려지면 Sandbox는 분석은 할 수 있어도
후속 재사용 자산으로서 가치가 약해진다.

---

## 5. 공식 Result Asset

Sandbox의 공식 Result Asset은 `sandbox_result_asset`이다.

최소 payload는 아래 성격을 가져야 한다.

1. `analysis_summary`
2. `dashboard_summary`
3. `domain_quality_summary`
4. `join_quality_summary`
5. `planned_handoff_candidates`

즉 Sandbox 결과는 단순 화면이 아니라
`후속 재사용 가능한 분석 자산`이어야 한다.

---

## 6. 구현 순서

Sandbox는 아래 순서로 구현한다.

1. `sandbox_reference_master` 계약
2. 도메인별 입력 규격 정리
3. `sandbox_domain_standard` 작성
4. `sandbox_input_standard` 작성
5. `sandbox_result_asset` 작성
6. OPS 품질 게이트 연결
7. Territory / Builder handoff 연결

---

## 7. OPS 연결 기준

OPS는 Sandbox 자산을 볼 때 아래를 본다.

1. 어떤 자산 조합이 들어왔는가
2. 조인키가 안정적인가
3. 병원/지점/담당자 기준이 유지되는가
4. 분석 요약이 후속 모듈에서 재사용 가능한가

Sandbox의 주요 후속 연결 대상은 아래다.

1. `Territory Optimizer`
2. `HTML Builder`

---

## 8. 완료 기준

Sandbox 단계는 아래가 가능해질 때 완료로 본다.

1. 기준 마스터가 정리된다.
2. 도메인 표준화 계층이 생긴다.
3. 시나리오별 입력 조합이 `sandbox_input_standard`로 정리된다.
4. `sandbox_result_asset`이 생성된다.
5. OPS가 후속 연결 후보를 판단할 수 있다.

---

## 9. 금지할 순서

아래는 하지 않는다.

1. Sandbox를 전체 허브처럼 다시 설계하는 것
2. OPS 대신 Sandbox가 연결 판단을 하게 만드는 것
3. domain standard 없이 화면 출력부터 키우는 것
4. Prescription이 없어도 될 시나리오까지 강제로 포함시키는 것

---

## 10. 한 줄 결론

`SFE Sandbox는 OPS를 대신하는 허브가 아니라, OPS가 허용한 자산 조합을 읽어 통합 분석 자산으로 바꾸는 분석엔진이므로, reference master -> domain standard -> input standard -> result asset 순서로 다시 가볍고 명확하게 정리해야 한다.`
