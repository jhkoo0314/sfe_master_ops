# Territory Optimizer Implementation Plan

작성일: 2026-03-10

## 0. 이 문서의 역할

이 문서는 Territory Optimizer 모듈을 아무것도 없는 상태에서 다시 시작하기 위한 공식 구현계획서다.

Territory는 가장 먼저 여는 모듈은 아니다.
하지만 나중에 붙는다고 해서 중요도가 낮은 것도 아니다.

이 문서는 Territory를 `언제`, `무엇이 준비된 뒤`, `어떤 형태로` 여는지 고정한다.

---

## 1. 모듈 한 줄 정의

`Territory Optimizer는 Sandbox가 만든 분석 자산을 공간 실행 관점으로 다시 해석해 커버리지, 동선, 배치 효율 자산을 만드는 Allocation 모듈이다.`

---

## 2. OPS 세계관 안에서의 위치

Territory는 아래처럼 이해한다.

1. Sandbox의 하위 화면이 아니다.
2. 독립 모듈이다.
3. OPS가 연결한 분석 자산을 읽는 후속 모듈이다.
4. 공간 실행 판단 자산을 다시 OPS에 돌려준다.

즉 Territory의 공식 자리는
`Sandbox 결과를 재사용하는 후속 공간 분석 모듈`이다.

---

## 3. 공식 입력 구조

Territory의 공식 입력은 아래다.

`sandbox_result_asset + territory_reference_master -> territory_entity_standard -> territory_input_standard -> territory_result_asset -> OPS`

즉 Territory는 raw를 직접 읽는 모듈로 시작하지 않는다.

먼저 필요한 것은 아래다.

1. Sandbox 결과 자산
2. 권역/좌표 기준
3. 병원/지점/담당자 공통축

---

## 4. 공통 키 기준

Territory에서 중요한 키는 아래다.

1. `hospital_id`
2. `branch_id`
3. `rep_id`
4. `territory_id`
5. `region_key`

공간 모듈이라고 해서 지리 정보만 중요하지 않다.
앞단의 병원/지점/담당자 축이 먼저 안정돼 있어야 한다.

---

## 5. 공식 Result Asset

Territory의 공식 Result Asset은 `territory_result_asset`이다.

최소 payload는 아래 성격을 가져야 한다.

1. `territory_summary`
2. `coverage_summary`
3. `optimization_summary`
4. `handoff_quality_summary`

즉 결과는 단순 지도 그림이 아니라
`실행 판단 자산`이어야 한다.

---

## 6. 구현 순서

Territory는 아래 순서로 구현한다.

1. 권역/좌표 기준 정리
2. `territory_reference_master` 계약
3. Sandbox 결과와 권역 기준 연결
4. `territory_entity_standard` 작성
5. `territory_input_standard` 작성
6. `territory_result_asset` 작성
7. OPS 품질 게이트 연결

---

## 7. OPS 연결 기준

OPS는 Territory 자산 또는 Territory handoff를 볼 때 아래를 본다.

1. 권역키가 충분한가
2. 지리 신호가 있는가
3. 커버리지나 최적화 의도가 분명한가
4. 병원/지점/담당자 축이 유지되는가

`Sandbox -> Territory`는 중요하지만,
입력 기준이 안정된 뒤에만 공식 연결로 본다.

---

## 8. 완료 기준

Territory 단계는 아래가 가능해질 때 완료로 본다.

1. 권역 기준표가 정리된다.
2. 공간 실행용 entity standard가 정리된다.
3. `territory_input_standard`가 만들어진다.
4. `territory_result_asset`이 생성된다.
5. OPS가 Territory 자산을 평가할 수 있다.

---

## 9. 금지할 순서

아래는 하지 않는다.

1. Sandbox 결과 안정화 전에 Territory부터 키우는 것
2. `hospital_id`, `branch_id`, `rep_id` 없이 공간 계산부터 만드는 것
3. 단순 지도 시각화를 Territory 완료로 착각하는 것
4. planned 검토 단계와 공식 연결 단계를 섞는 것

---

## 10. 한 줄 결론

`Territory Optimizer는 Sandbox 안의 부속 기능이 아니라 Sandbox 결과를 공간 실행 자산으로 다시 해석하는 독립 Allocation 모듈이므로, 공통축과 Sandbox 자산이 안정된 뒤에야 reference master -> input standard -> territory_result_asset 순서로 여는 것이 맞다.`
