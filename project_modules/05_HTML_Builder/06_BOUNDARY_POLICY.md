# Boundary Policy

작성일: 2026-03-12

## 목적

Builder, OPS, 계산 모듈의 경계를 짧고 분명하게 고정한다.

## 계산 모듈이 하는 일

- 데이터 정리
- 계산
- 요약 결과 생성
- Result Asset 생성

## OPS가 하는 일

- 결과 검증
- 품질 상태 확인
- 다음 전달 판단
- 어떤 템플릿 계약을 쓸지 연결

## Builder가 하는 일

- 템플릿 선택
- payload 주입
- HTML 생성

## 하지 않는 일

- Builder가 raw를 직접 읽지 않음
- Builder가 계산을 다시 하지 않음
- Builder가 공식 Result Asset을 대신하지 않음
- OPS가 템플릿 엔진처럼 비대해지지 않음

## 한 줄 결론

`계산은 모듈, 판단은 OPS, 표현은 Builder가 맡는다.`

