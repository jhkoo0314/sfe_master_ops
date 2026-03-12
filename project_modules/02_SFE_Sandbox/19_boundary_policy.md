# Sandbox Boundary Policy

## 목적
Sandbox, OPS, Builder의 책임 경계를 짧고 분명하게 고정한다.

## Sandbox가 하는 일
- 승인된 입력 자산 읽기
- 시나리오별 분석 실행
- 품질 상태 계산
- 공식 결과 자산 생성
- 승인 패키지 export

## OPS가 하는 일
- 승인된 결과 검증
- 품질 상태 확인
- 다음 모듈 연결 판단
- 운영 게이트 역할 수행

## Builder가 하는 일
- payload를 읽어 사람이 보는 결과 생성
- 계산 로직을 대신하지 않음

## 하지 않는 일
- Sandbox가 OPS를 대신하지 않음
- OPS가 Sandbox 분석을 다시 하지 않음
- Builder가 분석 엔진이 되지 않음

## 한 줄 결론
`Sandbox는 분석, OPS는 관제, Builder는 표현을 맡는다.`
