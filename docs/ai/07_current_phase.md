# Current Phase

## 현재 단계 정의

현재 단계는 `Part2 KPI 엔진 분리 진행` 단계다.

Part1 기준 구조 고정과 CRM KPI 거버넌스 복구(Phase 1~6)는 완료 상태로 본다.

## 현재 상태 요약

- CRM 공식 KPI 계산: `modules/kpi/crm_engine.py`
- Sandbox KPI 분리 1차: `modules/kpi/sandbox_engine.py`
- Territory KPI 분리 1차: `modules/kpi/territory_engine.py`
- Prescription KPI 분리 1차: `modules/kpi/prescription_engine.py`
- Builder는 KPI 재계산 없이 payload 주입만 수행
- Sandbox는 CRM KPI 재계산 없이 입력 KPI 사용
- Territory builder payload는 KPI 계산 없이 조립/분할만 수행
- Prescription builder payload는 KPI 계산 없이 조립/분할만 수행
- `hangyeol_pharma`, `daon_pharma` 회귀 검증 통과
- 최종 HTML 6종 생성 검증 통과(2개 회사)
- Sandbox 최종 HTML 지점/담당자 필터 복구 완료
  - `report_template`에 지점 chunk 로더 반영
  - `branch_index` 기반 지점 옵션 + 선택 지점 asset 로딩 방식으로 동작
- Sandbox 기반 실행모드에서 RADAR 단계 자동 실행 반영
  - `scripts/validate_radar_with_ops.py`
  - `data/ops_validation/{company_key}/radar/radar_result_asset.json` 생성

## 이번 단계의 목적

1. Prescription 분리 회귀/문서 동기화 마감
2. 모듈 하나 완료 후 다음 모듈로 이동
3. 매 단계마다 회귀 + 문서 동기화 마감

## 지금 해야 할 것

- Prescription 분리 회귀/문서 동기화 마감
- 다음 모듈(신규 Part2 우선순위) 착수 준비

## 지금 하지 않을 것

- 여러 모듈 동시 대규모 분리
- OPS/Builder 역할 재정의
- 공식 KPI 정의 확정 전 무리한 엔진 확장

## Codex 작업 제한

- 세계관을 바꾸지 않는다.
- Builder를 계산 엔진으로 확장하지 않는다.
- Sandbox에서 CRM KPI를 재계산하지 않는다.
- `company_key` 경로 원칙을 무시하지 않는다.

## 결론

지금의 우선순위는 `Sandbox/RADAR/Builder 연계 안정화 -> 회귀/문서 마감 -> 다음 모듈 착수`다.
