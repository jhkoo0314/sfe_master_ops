# PRD (Product Requirements Document) - Sandbox Independent Build

## 1. 제품 개요
- 제품명: Sandbox Analysis Engine
- 제품 형태: 독립 실행 콘솔 + 시나리오 분석 엔진 + OPS handoff exporter
- 목적: 승인된 입력 자산을 바탕으로 재현 가능한 분석 결과를 만들고, 승인된 결과만 OPS에 전달

## 2. 문제 정의
- Sandbox가 OPS 허브처럼 읽히면 역할 충돌이 생긴다.
- 분석 결과와 OPS 전달 결과가 섞이면 운영 기준이 흔들린다.
- 승인 전 시나리오를 공식 결과처럼 취급하면 재현성과 책임 구분이 무너진다.

## 3. 목표
- Sandbox를 독립 실행형 분석 엔진으로 고정
- 시나리오별 분석 결과 재현성 확보
- 승인된 결과만 OPS에 handoff
- Builder는 표현 계층으로 분리 유지

## 4. 비목표 (Out of Scope)
- OPS를 Sandbox 안에서 대체하는 것
- 다른 독립 모듈의 실험 기능을 Sandbox core에 포함하는 것
- 승인 전 결과를 OPS 공식 결과로 바로 반영하는 것

## 5. 사용자
- 분석 담당자
- 검토자
- 승인자
- OPS 수신자

## 6. 핵심 사용자 시나리오
1. 사용자가 승인된 입력 자산을 준비한다.
2. Sandbox 시나리오를 선택해 분석을 실행한다.
3. 품질 게이트를 확인하고 시나리오를 비교한다.
4. 승인된 시나리오를 선택한다.
5. `sandbox_ops_handoff.json`과 공식 산출물을 만든다.
6. OPS가 이 결과를 읽어 다음 연결을 판단한다.

## 7. 기능 요구사항
- FR-1: 시나리오 선택 기반 분석 실행
- FR-2: 입력 자산 표준화 및 조인 검증
- FR-3: 분석 결과 요약과 품질 상태 생성
- FR-4: 승인 메타 관리
- FR-5: OPS handoff 패키지 생성
- FR-6: Builder payload 생성

## 8. 비기능 요구사항
- NFR-1: 동일 입력 + 동일 시나리오 재현성
- NFR-2: 승인 전후 결과 분리 저장
- NFR-3: Fail-Fast 검증
- NFR-4: 승인 이력 추적 가능
- NFR-5: UTF-8 고정

## 9. 데이터 요구사항
- 표준 컬럼 체계 사용
- 필수 ID 키 유지
- 승인 메타 필수
- 결과 파일 3종 유지:
  - `sandbox_result_asset`
  - `sandbox_builder_payload`
  - `sandbox_ops_handoff`

## 10. 아키텍처 요구사항
- 공통 엔진 책임:
  - load -> normalize -> join_validate -> analyze -> summarize -> approve/export
- Sandbox 책임:
  - 독립 분석 실행
- OPS 책임:
  - 승인된 결과 검증 및 연결 판단
- Builder 책임:
  - 표현 계층만 담당

## 11. 성공 지표 (KPI)
- 시나리오 재현율
- handoff 성공률
- 승인 메타 누락 0건
- 품질 게이트 실패 조기 감지율

## 12. 릴리즈/도입 계획
- Phase 0: 정체성 재정의, 범위 밖 내용 제거, handoff 계약 추가
- Phase 1: 승인 구조와 품질 문서 보강
- Phase 2: 운영 자동화와 비교 리포트 확장

## 13. 리스크 및 대응
- Sandbox가 다시 허브처럼 커질 위험
  - 대응: boundary policy 문서화
- 승인 전 결과 오용 위험
  - 대응: approval_status와 handoff contract 강제
- Builder와 분석 경계 혼선
  - 대응: payload/asset 역할 분리 문서화

## 14. 승인 기준
- `sandbox_result_asset.json` 생성
- `sandbox_ops_handoff.json` 생성
- 승인 메타 존재
- 품질 체크리스트 통과
