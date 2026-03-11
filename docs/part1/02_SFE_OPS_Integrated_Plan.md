# SFE OPS Integrated Plan

작성일: 2026-03-10

## 0. 이 문서의 역할

이 문서는 SFE OPS를 아무것도 없는 상태에서 다시 시작하기 위한 `통합 기획안`이다.

이 문서는 개발 일정표가 아니다.
또 단순 TODO 문서도 아니다.

이 문서는 아래를 고정한다.

1. 전체 프로젝트를 어떤 논리로 전개할지
2. 무엇을 먼저 하고 무엇을 뒤로 미룰지
3. 어떤 순서로 5개 모듈을 열지
4. 실데이터가 없을 때 어떤 기준으로 전진할지

---

## 1. 계획의 출발점

이 기획안은 기존 코드 상태를 기준으로 쓰는 문서가 아니다.

이 문서는 아래 가정에서 시작한다.

1. 아직 공식 구조는 없다.
2. 지금부터 하나의 기준 문서 체계로 다시 시작한다.
3. 모든 모듈은 같은 세계관 아래에서 다시 배치한다.

즉 이 문서는 `처음부터 다시 시작하는 공식 설계 순서`를 정하는 문서다.

---

## 2. 공식 통합 계획 한 줄 정의

`SFE OPS 통합 계획은 CRM이 만든 공통 병원/지점/담당자 축 위에 Prescription의 범용 검증 구조를 올리고, 그 위에서 Sandbox를 통합 분석엔진으로 정립한 다음, Territory와 HTML Builder를 차례대로 연결하는 계획이다.`

---

## 3. 공식 단계 구분

### 3.1 단계 0 - 기준 문서 통합

목적:

- 여러 문서를 단일 기준 세트로 다시 묶는다.

산출물:

- PRD
- 통합 Plan
- 기술 스택 문서
- 모듈별 구현계획서 5개
- AGENTS

완료 판단:

- 앞으로 무엇을 기준으로 설명하고 구현해야 하는지가 하나로 정리된다.

### 3.2 단계 1 - CRM 기반 공통축 안정화

목적:

- 병원, 지점, 담당자 기준을 CRM 기준으로 먼저 안정화한다.

핵심 흐름:

- `hospital_public -> hospital_master`
- `company_master -> company_master_standard`
- `crm_raw -> crm_standard_activity`
- `crm_standard_activity -> crm_result_asset -> OPS`

이 단계에서 중요한 것:

- `hospital_id`
- `branch_id`
- `rep_id`

완료 판단:

- CRM이 다른 모듈이 재사용 가능한 출발 자산을 안정적으로 만든다.

### 3.3 단계 2 - Prescription 범용 검증 구조 구축

목적:

- 회사가 없어도 성립하는 흐름 검증 구조를 먼저 만든다.

핵심 원칙:

1. 병원 키는 CRM의 `hospital_id`를 재사용
2. `pharmacy_id` 범용 규칙 설계
3. `wholesaler_id` 범용 규칙 설계
4. `도매 -> 약국 -> 병원` 연결 규칙 설계
5. 그 다음 raw adapter 구현

완료 판단:

- Prescription이 범용 흐름 검증 자산을 만든다.

### 3.4 단계 3 - Sandbox 통합 분석 구조 정립

목적:

- Sandbox를 전체 허브가 아니라 `OPS가 허용한 자산 조합을 분석하는 엔진`으로 고정한다.

핵심 입력:

- `crm_result_asset`
- 매출
- 목표
- 필요 시 `prescription_result_asset`

핵심 산출:

- `sandbox_result_asset`

완료 판단:

- Sandbox가 OPS 중심 구조 안에서 분석엔진 역할로 선명해진다.

### 3.5 단계 4 - Territory 확장

목적:

- Sandbox 결과를 공간 실행 관점으로 재사용한다.

전제조건:

- `hospital_id`, `branch_id`, `rep_id` 안정화
- Sandbox 결과 자산 안정화
- Territory reference master 준비

완료 판단:

- Territory가 독립 모듈로 설명 가능하고, Sandbox 재사용 가치가 공간 분석으로 이어진다.

### 3.6 단계 5 - HTML Builder 범용 출력화

목적:

- 여러 모듈의 Result Asset을 공통 보고 입력으로 받을 수 있게 한다.

핵심 산출:

- `builder_input_reference`
- `builder_input_standard`
- `builder_payload_standard`
- `html_builder_result_asset`

완료 판단:

- HTML Builder가 범용 표현 모듈로 정리된다.

---

## 4. 공식 우선순위

현재 기준의 공식 우선순위는 아래다.

1. 기준 문서 통합
2. CRM 기반 공통축 안정화
3. Prescription 범용 구조
4. Sandbox 통합 분석 표준화
5. Territory
6. HTML Builder 범용화

즉 `Sandbox를 먼저 크게 키우는 계획`은 공식 기준이 아니다.

---

## 5. 왜 이 순서인가

### 5.1 CRM을 먼저 보는 이유

CRM은 병원/지점/담당자 문맥을 가장 먼저 안정화할 수 있는 출발점이다.

### 5.2 Prescription을 두 번째로 두는 이유

Prescription은 공공/기준 데이터와 범용 흐름 규칙만으로도 많은 부분을 먼저 설계할 수 있다.

### 5.3 Sandbox를 세 번째로 두는 이유

Sandbox는 통합 분석엔진이므로, CRM과 Prescription 중 최소한 일부 기준이 먼저 잡혀야 역할이 분명해진다.

### 5.4 Territory를 네 번째로 두는 이유

Territory는 병원/지점/담당자와 공간 신호가 모두 안정된 뒤에야 재사용 가치가 커진다.

### 5.5 HTML Builder를 마지막에 두는 이유

HTML Builder는 계산보다 표현 모듈이기 때문에 앞단 자산 구조가 정리된 뒤 붙이는 것이 맞다.

---

## 6. 실데이터가 없을 때의 운영 계획

실데이터가 없다고 해서 멈추지 않는다.

대신 아래 방식으로 전진한다.

1. 공공데이터와 기준데이터를 우선 활용한다.
2. fixture와 mock으로 흐름을 검증한다.
3. 회사 맞춤 규칙보다 범용 규칙을 먼저 세운다.
4. raw adapter 자리를 먼저 고정한다.
5. Result Asset과 OPS 평가 구조를 먼저 고정한다.

즉 지금의 계획은 `정답 구현`보다 `안 무너지는 골격`을 만드는 계획이다.

---

## 7. 단계별 산출물

### 7.1 CRM 단계 산출물

- `hospital_master`
- `company_master_standard`
- `crm_standard_activity`
- `crm_result_asset`

### 7.2 Prescription 단계 산출물

- `prescription_master`
- `company_prescription_standard`
- `prescription_standard_flow`
- `prescription_result_asset`

### 7.3 Sandbox 단계 산출물

- `sandbox_reference_master`
- `sandbox_domain_standard`
- `sandbox_input_standard`
- `sandbox_result_asset`

### 7.4 Territory 단계 산출물

- `territory_reference_master`
- `territory_entity_standard`
- `territory_input_standard`
- `territory_result_asset`

### 7.5 HTML Builder 단계 산출물

- `builder_input_reference`
- `builder_input_standard`
- `builder_payload_standard`
- `html_builder_result_asset`

---

## 8. 단계 전환 기준

한 단계가 끝났다고 보기 위한 공통 기준은 아래다.

1. adapter가 먼저 존재한다.
2. 공통 키가 설명 가능하다.
3. Result Asset이 만들어진다.
4. OPS가 그 자산을 평가한다.
5. 다음 모듈 handoff가 문서 기준으로 설명 가능하다.

---

## 9. 지금 의도적으로 미루는 것

아래는 지금 일부러 늦춘다.

1. 특정 회사 완전 맞춤 구현
2. 모든 연결을 한 번에 active로 여는 것
3. Sandbox 중심 구조로 다시 설계하는 것
4. raw 공통 업로드 엔진을 너무 빨리 일반화하는 것
5. 실데이터가 없는데도 세부 business rule을 과도하게 확정하는 것

---

## 10. 공식 판단 문장

앞으로 계획을 점검할 때는 아래 문장을 기준으로 본다.

1. 지금 하는 일이 adapter-first 순서를 지키는가
2. 지금 하는 일이 CRM 공통축을 더 단단하게 만드는가
3. 지금 하는 일이 Sandbox를 허브가 아니라 분석엔진으로 만드는가
4. 지금 하는 일이 Result Asset 중심 구조를 강화하는가
5. 지금 하는 일이 회사 맞춤보다 범용 규칙을 먼저 세우는가

---

## 11. 한 줄 결론

`SFE OPS의 공식 통합 계획은 CRM 공통축 안정화 -> Prescription 범용 구조 -> Sandbox 통합 분석 표준화 -> Territory -> HTML Builder 순서로 전체 5모듈을 다시 정렬하는 것이다.`
