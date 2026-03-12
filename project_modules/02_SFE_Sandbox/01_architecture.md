# 01 Architecture

## 목적
Sandbox를 OPS 내부 허브가 아니라, 독립 실행 가능한 분석 엔진으로 정의한다.

## 한 줄 정의
- Sandbox는 승인된 입력 자산을 받아 시나리오별 분석 결과를 만들고, 승인된 결과만 OPS에 넘기는 독립 분석 모듈이다.

## 아키텍처 원칙
- Sandbox는 OPS를 대신하지 않는다.
- Sandbox는 raw를 직접 관제하는 허브가 아니다.
- Sandbox는 `입력 자산 -> 분석 표준화 -> 결과 자산 -> handoff` 흐름으로 동작한다.
- Builder는 표현 계층이고 Sandbox 본체가 아니다.

## 구성요소와 책임
- `load`: 승인된 입력 자산 읽기
- `normalize`: 분석용 표준 구조로 맞추기
- `join_validate`: 키/그레인/누락 검증
- `analyze`: 시나리오별 계산 수행
- `summarize`: 결과 요약과 품질 상태 정리
- `export`: `sandbox_result_asset`, `sandbox_builder_payload`, `sandbox_ops_handoff` 생성

## 데이터 흐름
1. Approved Input Asset Load
2. Normalize
3. Join Validate
4. Analyze
5. Summarize
6. Approve / Export
7. OPS Handoff

## 경계 원칙
- Sandbox 내부:
  - 시나리오 실행
  - 비교
  - 분석 결과 생성
- OPS:
  - 승인된 결과 검증
  - 다음 연결 판단
- Builder:
  - 결과 표현

## 확장 규칙
- 신규 분석 시나리오는 시나리오 YAML로 추가한다.
- 신규 입력 자산은 계약 문서와 schema를 먼저 고친다.
- Sandbox 범위 밖 기능은 core 문서에 넣지 않는다.
