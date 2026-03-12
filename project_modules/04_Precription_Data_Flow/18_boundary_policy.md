# Prescription Boundary Policy

## 목적
Prescription, OPS, Builder의 책임 경계를 짧고 분명하게 고정한다.

## Prescription이 하는 일
- 원천 스냅샷 읽기
- 병합/마스터링/추적/정산/KPI/validation 실행
- 상세 산출물 생성
- 승인 가능한 공식 패키지 export

## OPS가 하는 일
- 승인된 결과 검증
- 품질 상태 확인
- 다음 연결 판단
- 운영 게이트 역할 수행

## Builder가 하는 일
- payload를 읽어 사람이 보는 결과 생성
- 계산 로직을 대신하지 않음

## 하지 않는 일
- Prescription이 OPS를 대신하지 않음
- OPS가 Prescription 계산을 다시 하지 않음
- Builder가 정산 엔진이 되지 않음

## 한 줄 결론
`Prescription은 계산, OPS는 관제, Builder는 표현을 맡는다.`
