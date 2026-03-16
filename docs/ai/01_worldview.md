# Sales Data OS Worldview

## 한 줄 정의

Sales Data OS는 모듈 계산 결과를 표준 자산으로 만들고, 검증(OPS)과 인텔리전스(RADAR)를 거쳐 최종 표현(Builder)으로 연결하는 운영 시스템이다.

## 핵심 원칙

1. 시스템 전체 명칭은 `Sales Data OS`다.
2. `OPS`는 `Validation / Orchestration Layer`다.
3. raw는 OPS로 직접 가지 않는다.
4. `adapter`가 회사별 raw를 공통 구조로 번역한다.
5. `module/core engine`은 공식 KPI와 결과 자산을 만든다.
6. OPS는 `Result Asset` 품질과 다음 단계 전달 가능 여부를 판단한다.
7. `Intelligence(RADAR)`는 KPI 재계산 없이 신호/우선순위를 해석한다.
8. `Builder`는 최종 표현 단계이며 재계산하지 않는다.

## 역할 요약

- `adapter`: 회사별 차이를 흡수하는 입구
- `module/core engine`: 도메인 계산 처리기
- `OPS`: 검증, 연결, 상태 판단 게이트
- `RADAR`: 신호 탐지/우선순위 해석 레이어
- `builder`: 최종 보고 자산 생성기 (render-only)

## 공식 흐름

`원천데이터 -> Adapter -> Module/Core Engine -> Result Asset -> Validation Layer(OPS) -> Intelligence(RADAR) -> Builder`

## 금지할 오해

- OPS가 시스템 전체다
- OPS가 raw를 직접 해석한다
- Builder가 계산 중심 엔진이다
- RADAR가 KPI를 재계산한다
- 모든 모듈을 하나의 거대 모듈로 합쳐야 한다
- 모듈 간 raw 직접 전달이 허용된다

## 결론

Sales Data OS는 adapter-first와 Result Asset 중심 원칙 아래, OPS를 검증 레이어로 두고 RADAR/Builder로 안전하게 전달하는 운영 구조다.
