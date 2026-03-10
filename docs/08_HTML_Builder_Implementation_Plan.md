# HTML Builder Implementation Plan

작성일: 2026-03-10

## 0. 이 문서의 역할

이 문서는 HTML Builder 모듈을 아무것도 없는 상태에서 다시 시작하기 위한 공식 구현계획서다.

HTML Builder는 종종 과소평가되거나 반대로 과대평가되기 쉽다.
그래서 이 문서는 Builder의 정확한 자리를 고정한다.

---

## 1. 모듈 한 줄 정의

`HTML Builder는 OPS가 허용한 Result Asset을 사람이 읽는 보고 자산으로 바꾸는 최종 표현 모듈이다.`

---

## 2. OPS 세계관 안에서의 위치

HTML Builder는 아래처럼 이해한다.

1. 계산 중심 모듈이 아니다.
2. 표현과 전달 모듈이다.
3. raw를 직접 해석하는 모듈로 시작하지 않는다.
4. 다른 모듈이 만든 자산을 보고서/웹슬라이드로 바꾼다.

즉 Builder는 `마지막 소비 모듈`이다.

---

## 3. 공식 입력 구조

Builder의 공식 입력 구조는 아래다.

`result_assets -> builder_input_reference -> builder_input_standard -> builder_payload_standard -> html_builder_result_asset`

핵심은 아래다.

1. CRM, Sandbox, Territory, Prescription 자산을 받을 수 있다.
2. 하지만 바로 받지 않고 공통 입력 규격으로 먼저 맞춘다.
3. 그 다음 템플릿이 읽는 payload로 바꾼다.

---

## 4. 공통 키 기준

Builder는 직접 엔터티 키를 계산하는 모듈은 아니다.
하지만 아래 메타는 분명해야 한다.

1. `source_module`
2. `asset_type`
3. `report_title`
4. `executive_summary`
5. `section_cards`
6. `source_references`

즉 Builder의 핵심은 계산키보다 `표현 메타 정리`다.

---

## 5. 공식 Result Asset

Builder의 공식 Result Asset은 `html_builder_result_asset`이다.

최소 payload는 아래 성격을 가져야 한다.

1. `render_summary`
2. `report_payload_summary`
3. `template_reference`
4. `output_reference`

즉 결과는 HTML 파일 자체만이 아니라
`어떤 자산을 어떻게 표현했는지 설명 가능한 보고 자산`이어야 한다.

---

## 6. 구현 순서

Builder는 아래 순서로 구현한다.

1. `builder_input_reference` 기준 정리
2. 모듈별 Builder input adapter 정리
3. `builder_input_standard` 작성
4. `builder_payload_standard` 작성
5. `html_builder_result_asset` 정리
6. 운영 콘솔 결과 UX 연결

---

## 7. OPS 연결 기준

OPS는 Builder 입력 또는 Builder 자산을 볼 때 아래를 본다.

1. 제목과 요약이 있는가
2. 핵심 숫자가 있는가
3. 섹션 구조가 최소 기준을 만족하는가
4. 사람이 읽을 수 있는 결과물로 바뀔 수 있는가

Builder의 주요 선행 입력은 아래다.

1. `SFE Sandbox`
2. 이후 `Behavior CRM`, `Territory`, `Prescription`

---

## 8. 완료 기준

Builder 단계는 아래가 가능해질 때 완료로 본다.

1. 공통 입력 기준이 정리된다.
2. 서로 다른 모듈 자산이 같은 보고 입력 구조로 바뀐다.
3. 템플릿이 읽는 payload가 정리된다.
4. `html_builder_result_asset`이 생성된다.
5. OPS가 표현용 연결을 판단할 수 있다.

---

## 9. 금지할 순서

아래는 하지 않는다.

1. Builder를 전체 허브처럼 다루는 것
2. raw 문서 파싱을 Builder의 기본 책임으로 고정하는 것
3. 입력 표준화 없이 바로 템플릿부터 늘리는 것
4. 앞단 자산 구조가 불안정한데 출력 레이어만 화려하게 키우는 것

---

## 10. 한 줄 결론

`HTML Builder는 raw를 직접 해석하는 엔진이 아니라 OPS가 허용한 Result Asset을 사람이 읽는 보고 자산으로 바꾸는 마지막 표현 모듈이므로, input reference -> input standard -> payload standard 순서로 범용 입력 계층부터 정리해야 한다.`
