# Module Map

## 공식 순서

`CRM -> Prescription -> Sandbox -> Territory -> HTML Builder`

이 순서는 구현 우선순위이자 모듈 연결의 공식 기준이다.

## 모듈별 정의

### CRM
활동기록을 행동프로파일과 KPI 자산으로 바꾸는 출발 모듈

### Prescription
도매 -> 약국 -> 병원 흐름을 추적해 검증 자산을 만드는 모듈

### Sandbox
OPS가 허용한 자산 조합을 받아 통합 분석 자산을 만드는 핵심 분석엔진

### Territory
활동과 공간 정보를 결합해 권역 실행 자산을 만드는 모듈

### HTML Builder
Result Asset을 사람이 읽는 HTML 보고 자산으로 바꾸는 최종 표현 모듈

## 연결 원칙

1. 모듈끼리 raw를 직접 주고받지 않는다.
2. 모듈 간 교환 단위는 `Result Asset`이다.
3. OPS가 상태, 품질, 연결을 판단한다.
4. Builder는 OPS가 허용한 자산만 표현한다.

## 기능 요약

- CRM = 출발 자산
- Prescription = 검증 자산
- Sandbox = 분석 자산
- Territory = 실행 자산
- Builder = 표현 자산

## 금지할 오해

- Sandbox가 전체 허브다
- Builder가 계산을 해야 한다
- CRM은 단순 기록 저장소다
- 모든 모듈이 반드시 Sandbox를 거쳐야 한다
- 모듈 연결은 raw 직접 전달 방식이다

## 결론

5개 모듈은 역할이 다른 독립 처리기이며, OPS가 Result Asset 기준으로 연결과 검증을 맡는다.