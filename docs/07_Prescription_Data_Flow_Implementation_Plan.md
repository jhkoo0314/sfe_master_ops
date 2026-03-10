# Prescription Data Flow Implementation Plan

작성일: 2026-03-10

## 0. 이 문서의 역할

이 문서는 Prescription Data Flow 모듈을 아무것도 없는 상태에서 다시 시작하기 위한 공식 구현계획서다.

Prescription은 지금 프로젝트에서 특히 중요하다.
이유는 아래 두 가지다.

1. 실데이터가 없어도 범용 규칙을 먼저 세우기 좋다.
2. 다른 모듈 분석의 신뢰도를 검증하는 축이 되기 때문이다.

---

## 1. 모듈 한 줄 정의

`Prescription Data Flow는 도매 -> 약국 -> 병원 흐름을 범용 규칙으로 추적해 검증 자산을 만드는 Validation 모듈이다.`

---

## 2. OPS 세계관 안에서의 위치

Prescription은 아래처럼 이해한다.

1. raw 거래 파일 저장 모듈이 아니다.
2. 흐름 검증 자산 생산 모듈이다.
3. CRM이 만든 병원/지점/담당자 문맥을 재사용한다.
4. Sandbox 분석을 보강하거나 검증하는 축이 된다.

즉 Prescription은 `독립 검증 모듈`이다.

---

## 3. 가장 중요한 비가역 원칙

Prescription에서는 아래 순서를 절대 바꾸지 않는다.

1. 병원 키는 CRM의 `hospital_id`를 재사용
2. 약국 raw를 보고 범용 `pharmacy_id` 규칙 설계
3. 도매 raw를 보고 범용 `wholesaler_id` 규칙 설계
4. `도매 -> 약국 -> 병원` 연결 규칙 설계
5. 그 다음 `prescription_raw_adapter` 구현
6. 그 다음 module service 구현
7. 그 다음 Result Asset 생성
8. 마지막에 OPS 평가 연결

쉽게 말하면:

- 회사 맞춤보다 범용 키 규칙이 먼저다.

---

## 4. 공식 입력 구조

Prescription의 공식 입력 구조는 아래다.

`public/basis data + raw flow data + crm_result_asset -> prescription_master -> company_prescription_standard -> prescription_standard_flow -> prescription_result_asset -> OPS`

중요한 해석:

1. raw는 adapter가 먼저 받는다.
2. CRM 문맥은 OPS를 통해 전달받는다.
3. module 내부에서 흐름과 문맥을 결합한다.

---

## 5. 공통 키 기준

Prescription에서 중요한 키는 아래다.

1. `hospital_id`
2. `pharmacy_id`
3. `wholesaler_id`
4. `product_id`
5. `ingredient_code`
6. `metric_month`
7. `lineage_key`

이 중 가장 중요한 것은 아래다.

1. `hospital_id`는 CRM 기준을 재사용
2. `pharmacy_id`, `wholesaler_id`는 범용 규칙으로 새로 정리

---

## 6. 공식 Result Asset

Prescription의 공식 Result Asset은 `prescription_result_asset`이다.

최소 payload는 아래 성격을 가져야 한다.

1. `lineage_summary`
2. `reconciliation_summary`
3. `validation_gap_summary`
4. `mapping_quality_summary`
5. 필요 시 `crm_context_summary`

즉 결과는 거래 목록이 아니라
`흐름과 검증 요약 자산`이어야 한다.

---

## 7. 구현 순서

Prescription은 아래 순서를 공식으로 따른다.

1. 기준 데이터 정리
2. `prescription_master` 안정화
3. `company_prescription_standard` 안정화
4. `prescription_standard_flow` 안정화
5. `prescription_result_asset` 안정화
6. OPS 평가 연결
7. Sandbox 재사용 연결

---

## 8. OPS 연결 기준

OPS는 Prescription 자산을 볼 때 아래를 본다.

1. `hospital_id` 문맥이 안정적인가
2. 흐름 연결이 설명 가능한가
3. 미매핑이 어디서 생기는지 보이는가
4. 검증 자산으로 재사용 가능한가

Prescription의 주요 후속 연결 대상은 아래다.

1. `SFE Sandbox`

---

## 9. 완료 기준

Prescription 단계는 아래가 가능해질 때 완료로 본다.

1. `hospital_id` 재사용 원칙이 고정된다.
2. `pharmacy_id`, `wholesaler_id` 범용 규칙이 정리된다.
3. 흐름 기준표와 표준 흐름 계층이 정리된다.
4. `prescription_result_asset`이 생성된다.
5. OPS가 검증 자산으로 평가할 수 있다.

---

## 10. 금지할 순서

아래는 하지 않는다.

1. 회사 맞춤 규칙부터 만드는 것
2. `pharmacy_id`, `wholesaler_id` 기준 없이 pipeline부터 키우는 것
3. 거래 raw를 OPS에 직접 보내는 것
4. Sandbox 확장을 위해 Prescription 원칙을 흔드는 것

---

## 11. 한 줄 결론

`Prescription Data Flow는 실데이터가 없을 때도 범용 규칙을 먼저 세우기 좋은 핵심 Validation 모듈이므로, CRM hospital_id 재사용과 pharmacy/wholesaler 범용 규칙을 먼저 고정한 뒤 adapter -> standard_flow -> result_asset -> OPS 순서로 단단하게 확장해야 한다.`
