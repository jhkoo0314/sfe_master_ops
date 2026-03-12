# Behavior CRM Implementation Plan

작성일: 2026-03-10

## 0. 이 문서의 역할

이 문서는 Behavior CRM 모듈을 아무것도 없는 상태에서 다시 시작하기 위한 공식 구현계획서다.

핵심은 아래다.

1. CRM이 SFE OPS 안에서 어떤 역할을 하는가
2. 어떤 입력 구조로 시작해야 하는가
3. 어떤 순서로 구현해야 하는가
4. 언제 완료로 볼 것인가

---

## 1. 모듈 한 줄 정의

`Behavior CRM은 활동기록을 행동프로파일과 KPI 구조로 바꿔 OPS에 전달하는 출발 자산 모듈이다.`

---

## 2. OPS 세계관 안에서의 위치

CRM은 5개 모듈 중 `가장 먼저 공통 문맥을 만드는 모듈`이다.

중요한 이유는 아래다.

1. 병원/지점/담당자 축을 먼저 안정화할 수 있다.
2. 다른 모듈이 재사용할 출발 자산을 만든다.
3. Prescription과 Sandbox가 읽을 문맥 자산의 기반이 된다.

즉 CRM은 단순 원본 입력 저장소가 아니라,
`공통 문맥 자산 생산 모듈`이다.

---

## 3. 공식 입력 구조

CRM의 공식 입력 흐름은 아래다.

`hospital_public -> hospital_master -> company_master_standard -> crm_standard_activity -> crm_result_asset -> OPS`

이 순서가 중요한 이유는 아래다.

1. 공공 기준 병원 축이 먼저 있어야 한다.
2. 회사 마스터를 그 위에 연결해야 한다.
3. 그 다음에 CRM raw를 표준 활동 데이터로 바꿔야 한다.
4. 마지막에만 Result Asset이 나온다.

---

## 4. 공통 키 기준

CRM에서 특히 중요한 키는 아래다.

1. `hospital_id`
2. `branch_id`
3. `rep_id`
4. `activity_date`
5. `metric_month`

중요:

- `hospital_id`는 뒤 모듈이 재사용할 핵심 축이다.
- CRM은 이 축을 가능한 한 먼저 안정화해야 한다.

---

## 5. 공식 Result Asset

CRM의 공식 Result Asset은 `crm_result_asset`이다.

최소한 아래 성격을 가져야 한다.

1. 행동프로파일
2. KPI 요약
3. 활동 문맥 요약
4. 매핑/품질 요약

OPS가 봐야 하는 핵심은 아래다.

1. 병원/지점/담당자 축이 설명 가능한가
2. 행동 의미가 설명 가능한가
3. 후속 재사용 목적이 분명한가

---

## 6. 구현 순서

CRM은 아래 순서로 구현한다.

1. `hospital_master` 설계
2. 공공 병원 기준 데이터 가공 계층 구현
3. `company_master_standard` 설계
4. 회사 마스터 표준화 계층 구현
5. `crm_standard_activity` 설계
6. CRM raw adapter 구현
7. `crm_result_asset` 생성기 구현
8. OPS 평가 연결

---

## 7. OPS 연결 기준

OPS는 CRM 자산을 볼 때 아래를 본다.

1. `hospital_id`, `branch_id`, `rep_id`가 설명 가능한가
2. 행동프로파일/KPI가 후속 해석용으로 충분한가
3. 품질 요약이 있는가
4. 다음 연결 대상이 무엇인지 분명한가

CRM의 공식 연결 대상은 아래다.

1. `Prescription Data Flow`
2. `SFE Sandbox`

---

## 8. 완료 기준

CRM 단계는 아래가 가능해질 때 완료로 본다.

1. 공공 병원 기준이 `hospital_master`로 정리된다.
2. 회사 구조가 `company_master_standard`로 정리된다.
3. CRM raw가 `crm_standard_activity`로 표준화된다.
4. `crm_result_asset`이 생성된다.
5. OPS가 CRM 자산을 평가할 수 있다.

---

## 9. 금지할 순서

아래는 하지 않는다.

1. 병원 기준 없이 CRM raw부터 크게 키우는 것
2. 회사 예외 규칙을 공통 규칙보다 먼저 만드는 것
3. CRM raw를 OPS에 직접 보내는 것
4. Sandbox가 CRM을 해석해주기를 기다리는 것

---

## 10. 한 줄 결론

`Behavior CRM은 SFE OPS의 출발 자산 모듈이므로, 병원/지점/담당자 공통축을 먼저 단단하게 만들고 그 위에 행동프로파일과 KPI 구조를 얹어 Prescription과 Sandbox가 재사용 가능한 crm_result_asset을 안정적으로 생산해야 한다.`
