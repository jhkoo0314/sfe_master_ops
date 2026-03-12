# Territory Optimizer Independent Build PRD

## 목적
Territory를 OPS 내부 부속 계산이 아니라, 독립적으로 시나리오를 실험하고 승인된 결과만 OPS에 넘기는 공간 분석 모듈로 재정의한다.

## 제품 개요
- 제품명: Territory Scenario Lab
- 형태: 독립 실행 콘솔 + 시나리오 비교 엔진 + OPS handoff exporter
- 핵심 산출물:
  - `territory_result_asset.json`
  - `territory_builder_payload.json`
  - `territory_ops_handoff.json`
  - `territory_map_preview.html` (선택)

## 사용자
- Territory 분석 담당자: 권역안/배치안 실험
- OPS 검토자: 승인된 결과 수신 및 연결 판단
- 관리자: 승인, 버전 관리, 변경 이력 확인

## 범위
- 포함:
  - 시나리오별 권역/담당자/병원 배치 실험
  - 커버리지/과부하/공백 구간 비교
  - 지도 미리보기 생성
  - 승인된 결과의 OPS handoff 패키지 생성
- 제외:
  - OPS 내부에서 반복적인 권역 실험 수행
  - 승인 전 결과를 OPS 공식 산출물로 직접 반영
  - Territory가 CRM/Sandbox 원천 raw를 직접 대체하는 것

## 기능 요구사항
- FR-1: 동일 입력으로 여러 시나리오를 독립 실행/비교할 수 있어야 한다.
- FR-2: 승인 전 시나리오와 승인 완료 시나리오를 구분 저장해야 한다.
- FR-3: 승인된 시나리오는 `territory_result_asset`과 handoff manifest로 내보낼 수 있어야 한다.
- FR-4: 지도 미리보기는 분석 보조 수단이어야 하며, Territory 본체를 대신하지 않는다.
- FR-5: OPS는 승인 패키지만 읽고 Territory 내부 시뮬레이션은 다시 수행하지 않는다.

## 비기능 요구사항
- NFR-1: 동일 입력 + 동일 시나리오 설정이면 동일 결과가 재현되어야 한다.
- NFR-2: Territory 실험은 OPS 운영 파이프라인과 분리되어야 한다.
- NFR-3: 승인/반려/재실행 이력이 남아야 한다.
- NFR-4: UTF-8 고정, 기존 승인 결과 덮어쓰기 금지.

## KPI
- 동일 입력/동일 시나리오 재현율 100%
- 승인 패키지 OPS import 성공률 100%
- 시나리오별 품질 게이트 통과 여부 즉시 확인 가능
- 승인 전후 버전 추적 가능

## 승인 기준
- 승인된 시나리오에서 `territory_result_asset.json` 생성 성공
- `territory_ops_handoff.json` 생성 성공
- 품질 게이트 통과
- 동일 시나리오 재실행 시 결과 일관성 확인
