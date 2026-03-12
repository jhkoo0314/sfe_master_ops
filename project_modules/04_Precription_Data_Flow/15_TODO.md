# TODO - Prescription Data Flow Independent Build Checklist

기준 문서:
- `01_business_rules.md`
- `08_rebuild_requirements.md`
- `12_PLAN.md`
- `13_PRD.md`
- `14_Runbook.md`
- `17_ops_handoff_contract.md`
- `18_boundary_policy.md`

작성일: 2026-03-12

## 0. 고정 원칙
- [x] KPI 금액 기준은 `amount_ship`
- [x] 날짜 기준은 `ship_date`
- [x] 기간 기준은 `year_month`, `year_quarter`, `year`
- [x] 권역 기준은 `territory_code`
- [x] 쉐어 정산 grain은 `year_quarter x territory_code x brand`
- [x] 추적 시작 이전 기간 소급 귀속 금지
- [x] 공식 결과는 승인 패키지로 export 한다
- [x] 로컬 화면은 선택 기능이다

## 1. Phase 1 - Input Contract
- [x] 원천 컬럼 계약 고정
- [x] lineage 컬럼 기준 고정
- [ ] 입력 manifest 파일 구조 고정
- [ ] 룰 버전/기준일 메타 구조 고정

완료 기준:
- [ ] 입력 파일 누락 여부를 실행 전에 판정 가능
- [ ] 컬럼 계약 문서와 실제 코드 용어 일치

## 2. Phase 2 - Mastering & Tracking
- [x] `ingest_merge` 실행 가능
- [x] `mastering` 실행 가능
- [x] `tracking_validation` 실행 가능
- [ ] tracking 품질 상태 규칙 고정
- [ ] `tracking_report.*` -> 공식 요약 구조 연결

완료 기준:
- [ ] `pharmacy_uid` 누락 0건
- [ ] `tracking_report.*` 생성 성공
- [ ] coverage/gap 계산 검증 통과

## 3. Phase 3 - Share Settlement
- [x] `share_engine` 기본 정산 실행 가능
- [x] 전분기 연장(`extended`) 처리 가능
- [ ] overlap OFF 기본 경로 회귀 테스트 고정
- [ ] overlap ON 확장 계획 별도 정리

완료 기준:
- [ ] 보전성 위배 0건
- [ ] `share_rule_source` 허용값 외 0건

## 4. Phase 4 - KPI & Validation
- [x] 월/분기/연 KPI 산출 가능
- [x] `validation_report.*` 생성 가능
- [x] `trace_log.*` 생성 가능
- [ ] KPI 요약과 validation 요약 연결 규칙 고정

완료 기준:
- [ ] KPI 출력 6종 누락 0건
- [ ] validation 치명 이슈 구조화 기록 성공

## 5. Phase 5 - Approval Package
- [ ] `prescription_result_asset.json` 구조 고정
- [ ] `prescription_builder_payload.json` 구조 고정
- [ ] `prescription_ops_handoff.json` 구조 고정
- [ ] 승인 메타 필드 고정
- [ ] `quality_status`, `handoff_ready` 규칙 고정

완료 기준:
- [ ] 승인 패키지 3종 생성 성공
- [ ] 승인 메타 누락 0건
- [ ] handoff contract 검증 통과

## 6. Phase 6 - Optional Local Workbench
- [ ] 로컬 검토 화면이 필요하면 별도 보조 도구로 유지
- [ ] 화면이 없어도 CLI 기준 완료 가능해야 함
- [ ] 화면은 조회/검토/다운로드 중심으로 제한
- [ ] 화면에서만 가능한 핵심 로직 금지

완료 기준:
- [ ] 로컬 화면이 없어도 end-to-end 실행 가능
- [ ] 화면이 있더라도 승인 패키지 규격과 충돌하지 않음

## 7. 공통 테스트 전략
- [ ] `pytest -m unit`
- [ ] `pytest -m contract`
- [ ] `pytest -m integration`
- [ ] `pytest -m regression`
- [ ] `pytest -m e2e`
- [ ] 선택적으로 `pytest -m local_workbench_smoke`

## 8. 최종 완료 기준
- [ ] 한 명령 흐름으로 핵심 파이프라인 실행 가능
- [ ] tracking/share/KPI/validation/trace 산출물 생성
- [ ] 승인 패키지 3종 생성
- [ ] 로컬 화면 없이도 실행 가능
- [ ] OPS handoff 기준 충족
- [ ] 문서 용어와 코드 용어 일치
