# Part2 Status Source Of Truth

작성일: 2026-03-16  
상태: `active`

## 문서 목적

이 문서는 Part2 진행 상태의 단일 기준 문서다.  
Part2의 완료/진행/대기 상태는 이 문서를 기준으로 본다.

## 현재 기준

- 현재 단계: `Part2 KPI 엔진 분리 진행`
- 완료된 축:
  - CRM KPI 엔진 운영 (`modules/kpi/crm_engine.py`)
  - Sandbox KPI 엔진 1차 분리 (`modules/kpi/sandbox_engine.py`)
  - Territory KPI 엔진 1차 분리 (`modules/kpi/territory_engine.py`)
  - Prescription KPI 엔진 1차 분리 (`modules/kpi/prescription_engine.py`)
  - Builder KPI 재계산 금지 원칙 유지
  - Sandbox에서 CRM KPI 재계산 금지 원칙 유지

## 완료(Completed)

- KPI 엔진 모듈 체계 생성
- `hangyeol_pharma`, `daon_pharma` 회귀 검증 통과
- Builder 최종 HTML 6종 생성 검증 통과
- Sandbox 보고서 지점/담당자 필터 복구 반영

## 진행중(In Progress)

- Prescription 분리 회귀/문서 동기화 마감

## 대기(Next)

- Part2 다음 우선순위 모듈 착수 준비
- run 중심 저장 구조 및 report context 반영 설계의 구현 전환

## 운영 고정 원칙

1. KPI 계산은 `modules/kpi/*`에서만 수행한다.
2. OPS는 Validation/Orchestration 역할만 수행한다.
3. Builder는 render-only를 유지한다.
4. 모든 경로/저장은 `company_key` 기준을 유지한다.

## 링크

- 현재 단계 문서: `docs/ai/07_current_phase.md`
- Part2 허브(레거시): `docs/part2/README.md`
