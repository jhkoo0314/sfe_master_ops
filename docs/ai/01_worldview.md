# OPS Worldview

## 한 줄 정의

SFE OPS는 5개 모듈을 단순 통합하는 시스템이 아니라, 각 모듈의 Result Asset을 검증하고 연결하는 중앙 운영 엔진이다.

## 핵심 원칙

1. 중심은 `OPS Engine`이다.
2. 모듈은 `OPS를 통해 연결되는 방사형 구조`다.
3. raw는 OPS로 직접 가지 않는다.
4. `adapter`가 회사별 raw를 공통 구조로 번역한다.
5. `module`은 자기 `Result Asset`을 만든다.
6. OPS는 `Result Asset`을 검증하고 다음 연결을 판단한다.
7. `Builder`는 최종 표현 단계다.
8. `Sandbox`는 핵심 분석엔진이지만 전체 허브는 아니다.

## 역할 요약

- `adapter`: 회사별 차이를 흡수하는 입구
- `module`: 도메인 처리기
- `OPS`: 검증, 연결, 상태 판단 게이트
- `builder`: 최종 보고 자산 생성기

## 공식 흐름

`원천데이터 -> Adapter -> Module -> Result Asset -> OPS -> Builder`

## 금지할 오해

- Sandbox가 전체 허브다
- OPS가 raw를 직접 해석한다
- Builder가 계산 중심 엔진이다
- 모든 모듈을 하나의 거대 모듈로 합쳐야 한다
- 모듈 간 raw 직접 전달이 허용된다

## 결론

SFE OPS는 adapter-first와 Result Asset 중심 원칙 아래 OPS를 중앙 엔진으로 두는 운영 구조다.