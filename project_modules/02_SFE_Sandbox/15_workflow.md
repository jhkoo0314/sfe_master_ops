# Sandbox Independent Workflow Guide

## 1) 문서 목적
이 문서는 Sandbox를 독립 실행형 분석 엔진으로 설계/운영하기 위한 표준 가이드다.

핵심 목표:
- 승인된 입력 자산만 읽는다.
- 시나리오별 분석 결과를 재현 가능하게 만든다.
- 승인된 결과만 OPS에 넘긴다.

## 2) 시스템 철학
- Sandbox는 OPS가 아니다.
- Sandbox는 분석 엔진이다.
- OPS는 관제와 연결 판단을 맡는다.
- Builder는 사람이 보는 결과만 만든다.

한 줄 정의:
- `Sandbox는 독립 실행형 분석 엔진이고, OPS는 승인된 Sandbox 결과를 읽는 관제 게이트다.`

## 3) 핵심 개념 정리

### 3.1 입력 자산
- CRM, Sales, Target, Prescription 등 승인된 입력 재료

### 3.2 시나리오
- 같은 입력 자산을 어떤 조건으로 해석할지 정의한 실행 규칙

### 3.3 결과 자산
- `sandbox_result_asset`
- Sandbox의 공식 판단 결과

### 3.4 handoff 패키지
- OPS에 넘길 승인 완료 패키지
- `sandbox_result_asset + sandbox_builder_payload + sandbox_ops_handoff`

### 3.5 approval_status
- `draft`
- `approved`
- `rejected`

## 4) 표준 아키텍처
- 입력 자산
- 시나리오 실행
- 품질 검증
- 결과 자산 생성
- 승인
- OPS handoff

## 5) 표준 실행 흐름
1. 입력 자산 준비
2. 시나리오 선택
3. 분석 실행
4. 품질 게이트 확인
5. 시나리오 비교
6. 승인안 선택
7. handoff 패키지 생성
8. OPS 전달

핵심:
- Sandbox 안에서는 분석을 반복할 수 있다.
- OPS로는 승인된 결과만 보낸다.

## 6) 데이터 표준화 규칙
- 원천 raw가 아니라 승인된 입력 자산 기준
- 표준 컬럼 유지
- ID 기반 조인
- 월 포맷 고정

## 7) 조인 설계 규칙
- 시나리오별 기준 grain을 먼저 정한다.
- 입력 자산을 같은 grain으로 맞춘다.
- 조인 실패 시 즉시 중단한다.

## 8) 승인 흐름
- 분석 담당자 실행
- 검토자 품질 확인
- 승인자 승인
- handoff export

## 9) 운영 규칙
- 승인 전 결과를 OPS 결과로 취급하지 않는다.
- 승인 버전은 덮어쓰지 않는다.
- 이전 승인 결과와 차이를 기록한다.

## 10) 최종 결론
- Sandbox의 올바른 자리란 `실험 가능한 독립 분석 엔진`이고, OPS의 올바른 자리는 `승인된 결과만 읽는 연결 게이트`다.
