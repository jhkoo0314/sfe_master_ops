# Sales Data OS Architecture

작성일: 2026-03-16

## 1. 시스템 정의

이 저장소의 전체 시스템은 `Sales Data OS`다.  
`OPS`는 시스템 전체가 아니라 `Validation / Orchestration Layer`를 의미한다.

한 줄 정의:

`Sales Data OS는 제약 영업 데이터를 표준화하고, KPI를 계산하고, 품질을 검증한 뒤, 분석/의사결정/표현 레이어로 안전하게 전달하는 운영 체계다.`

## 2. Layer Model

### Layer 1. Data Layer
- CRM / Sales / Target / Prescription / Master raw data

### Layer 2. Adapter Layer
- raw -> standard schema 정규화
- 회사별 포맷 차이를 흡수

### Layer 3. Core Engine Layer
- KPI Engine (`modules/kpi/*`)
- 모듈별 계산/집계 로직 (`modules/*/service.py`)

### Layer 4. Validation / Orchestration Layer (OPS)
- Result Asset 품질 검증
- 매핑 검증
- handoff 가능 여부 판단
- 파이프라인 실행 통제

### Layer 5. Intelligence Layer
- Sandbox: 분석/비교/드릴다운
- Territory: 권역/담당자 구조 분석
- Prescription: 처방 흐름 및 품질 해석
- RADAR(예정): signal detection / issue prioritization / decision option templating

### Layer 6. Presentation Layer
- Builder: render-only
- HTML preview/download payload 전달

## 3. 모듈 책임

- `adapters/*`: raw를 표준 데이터로 변환
- `modules/kpi/*`: KPI 공식 계산 단일 소스
- `modules/crm|sandbox|territory|prescription/*`: 모듈 도메인 처리 + Result Asset 조립
- `ops_core/*`: Validation/Orchestration 실행
- `modules/builder/*`, `templates/*`: 렌더링
- `ui/*`: 운영 콘솔 인터페이스

## 4. KPI Single Source Rule

KPI 공식은 아래 엔진만 source of truth로 사용한다.

- `modules/kpi/crm_engine.py`
- `modules/kpi/sandbox_engine.py`
- `modules/kpi/territory_engine.py`
- `modules/kpi/prescription_engine.py`

금지:
- Builder KPI 재계산
- Sandbox의 CRM KPI 재계산
- Territory KPI 재계산
- RADAR KPI 재계산
- payload 단계 중복 계산

## 5. OPS 정의 (Validation Layer)

OPS는 다음만 담당한다.

- 품질 검증
- 매핑 검증
- 전달 판단
- 실행 오케스트레이션

OPS는 다음을 담당하지 않는다.

- 시스템 전체 정의
- KPI 단일 계산 엔진
- 보고서 렌더러
- 분석 결과 확정 엔진

## 6. Intelligence Layer 상세

### Sandbox
- KPI 결과와 도메인 데이터를 기반으로 분석/탐색

### Territory
- 지역/담당자/커버리지 구조 해석

### Prescription
- 처방 흐름, 연결 품질, gap 해석

### RADAR (Readiness)
- 입력:
  - KPI engine output
  - validation-approved result asset
  - sandbox summary metrics
- 역할:
  - signal detection
  - issue prioritization
  - decision option templating
- 비역할:
  - KPI 재계산
  - 현장 액션 자동 지시
  - 원인 확정

## 7. Builder Render-Only Principle

Builder는 표현 계층이다.

- Builder is render-only and does not recalculate KPI.
- Builder consumes validated payloads only.

Builder는:
- 템플릿 주입
- HTML 생성
- 대용량 payload 분할 asset 처리

Builder는 하지 않는다:
- raw 해석
- KPI/비즈니스 규칙 재구현
- 검증 판단 대체

## 8. 데이터 흐름

`Raw Data -> Adapter -> Module/Core Engine -> Result Asset -> Validation Layer (OPS) -> Intelligence/Builder`

핵심은 "계산과 검증, 표현의 분리"다.
