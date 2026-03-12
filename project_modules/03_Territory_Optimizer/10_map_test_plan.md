# Territory Independent Build Test Plan

## 목적
Territory 독립 실행형 구조에서 시나리오 재현성, 승인 패키지 안정성, OPS handoff 가능성을 검증한다.

## 단위 테스트
- 시나리오 ID 생성 규칙
- 병원 중복 배정 감지
- 커버리지 계산 함수
- 과부하 판정 함수
- handoff manifest 생성 함수

## 통합 테스트
- `sandbox_result_asset + territory_reference_master -> territory_result_asset`
- 시나리오 비교 -> 승인 버전 선택
- 승인 버전 -> `territory_ops_handoff.json` 생성

## 회귀 테스트
- 동일 입력 + 동일 시나리오 설정이면 결과 동일
- 이전 승인 버전과 새 승인 버전 차이점 계산 가능
- OPS import contract 통과 여부 확인

## 테스트 데이터셋
- 정상 시나리오 1세트
- 중복 배정 오류 1세트
- 권역 미매핑 1세트
- 과부하 시나리오 1세트
- 승인 메타 누락 1세트

## 합격 기준
- 치명 오류 0건
- 승인 패키지 생성 성공
- handoff 필수 메타 누락 0건
- 동일 시나리오 재실행 결과 일관성 확보
