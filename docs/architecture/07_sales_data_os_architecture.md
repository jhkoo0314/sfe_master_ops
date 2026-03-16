# Sales Data OS Architecture

작성일: 2026-03-16

---

# 1. 시스템 정의

이 저장소의 전체 시스템은 **Sales Data OS**다.  
여기서 `OPS`는 시스템 전체를 의미하지 않는다.

`OPS`는 **Validation / Orchestration Layer**를 의미한다.

한 줄 정의:

Sales Data OS는 제약 영업 데이터를 표준화하고 KPI를 계산하고 품질을 검증한 뒤  
분석·의사결정·표현 레이어로 안전하게 전달하는 **영업 데이터 운영 체계**다.

핵심 설계 철학

- 계산과 검증의 분리
- 분석과 표현의 분리
- 데이터 품질 검증 이후에만 의사결정 계층으로 전달

---

# 2. Layer Model

Sales Data OS는 다음과 같은 계층 구조로 설계되어 있다.

Raw Data  
→ Adapter  
→ Core Engine  
→ Result Asset  
→ Validation / Orchestration (OPS)  
→ Intelligence  
→ Composition / Resolver  
→ Presentation

각 레이어의 책임은 명확하게 분리되어 있다.

---

# 3. Layer 설명

## Layer 1. Data Layer

영업 운영에서 생성되는 **원천 데이터 계층**

대표 데이터

- CRM 활동 데이터
- Sales 실적 데이터
- Target 목표 데이터
- Prescription 처방 데이터
- Master 데이터 (병원 / 담당자 / 조직)

특징

- 회사마다 데이터 포맷이 다름
- 직접 분석에 사용하지 않음
- 반드시 Adapter를 거쳐야 함

---

## Layer 2. Adapter Layer

Adapter는 raw 데이터를 **표준 스키마로 정규화**한다.

목적

- 회사별 데이터 포맷 차이 흡수
- 분석 가능한 표준 데이터 구조 생성

대표 역할

- CRM activity 표준화
- Sales / Target 정규화
- Prescription 연결 데이터 정리
- Territory 활동 정리

위치

adapters/*

---

## Layer 3. Core Engine Layer

Core Engine은 **KPI 계산과 도메인 집계 로직**을 담당한다.

### KPI Engine

modules/kpi/*

공식 KPI 계산의 **단일 소스**

예

- CRM KPI
- Sandbox KPI
- Territory KPI
- Prescription KPI

### Module Service

각 모듈의 계산 및 집계를 담당

modules/crm/service.py  
modules/sandbox/service.py  
modules/territory/service.py  
modules/prescription/service.py  

역할

- KPI Engine 호출
- 도메인 집계
- Result Asset 생성

---

## Layer 4. Validation / Orchestration Layer (OPS)

OPS는 **검증과 실행 통제 계층**이다.

OPS 역할

- Result Asset 품질 검증
- 매핑 상태 검증
- 데이터 정합성 검증
- 다음 단계 전달 가능 여부 판단
- 파이프라인 실행 오케스트레이션

OPS는 다음을 담당하지 않는다

- KPI 계산
- 분석 로직 구현
- 보고서 렌더링
- 의사결정 확정

위치

ops_core/*

OPS는 **관제 계층**이다.

---

## Layer 5. Intelligence Layer

Intelligence Layer는 **분석 및 해석 계층**이다.

여기서는 KPI 결과와 도메인 데이터를 기반으로 분석을 수행한다.

### Sandbox

목적

- KPI 분석
- 담당자 / 지점 비교
- 활동 / 성과 관계 분석
- Drill-down 분석

특징

- 탐색형 분석
- Dashboard 중심 구조

---

### Territory

목적

- 권역 구조 분석
- 담당자 커버리지 분석
- 지역 기반 성과 해석

---

### Prescription

목적

- 처방 흐름 해석
- 연결 품질 분석
- 처방 데이터 기반 gap 분석

---

### RADAR (Decision Intelligence)

RADAR는 의사결정 보조 계층이다.

입력

- KPI Engine 결과
- OPS 검증 완료 Result Asset
- Sandbox summary metrics

출력

radar_result_asset.json  
radar_report_preview.html  

역할

- signal detection
- issue prioritization
- decision option templating

RADAR는 다음을 하지 않는다

- KPI 재계산
- 현장 액션 자동 지시
- 원인 확정

---

## Layer 6. Composition / Resolver Layer

Composition Layer는 **분석 결과를 표현 가능한 구조로 해석하는 계층**이다.

이 계층은 Sandbox 대시보드에서 먼저 구현된 구조다.

핵심 구성

- block payload
- block registry
- block resolver
- slot renderer
- chunk lazy-load 처리

역할

- 분석 결과를 block 단위 자산으로 해석
- slot 기준으로 데이터 선택
- branch asset lazy-load 처리
- fallback 처리
- renderer에 필요한 데이터 공급

---

## Layer 7. Presentation Layer

Presentation Layer는 **표현 계층**이다.

구성

modules/builder/*  
templates/*  

Builder 역할

- HTML 템플릿 렌더
- payload 주입
- 대용량 payload asset 분리
- preview HTML 생성

Builder는 **render-only 원칙**을 따른다.

Builder는 다음을 하지 않는다

- KPI 계산
- raw 데이터 해석
- 분석 로직 구현
- 검증 판단

Builder 입력은 반드시 **OPS 검증 통과 payload**여야 한다.

---

# 4. 모듈 책임

## adapters

adapters/*

raw 데이터를 표준 데이터로 변환

---

## KPI Engine

modules/kpi/*

KPI 공식 계산 엔진  
KPI single source of truth

---

## Domain Modules

modules/crm/*  
modules/sandbox/*  
modules/territory/*  
modules/prescription/*  

역할

- 도메인 계산
- Result Asset 생성
- 분석 payload 조립

---

## Sandbox Block System

modules/sandbox/block_registry.py  
modules/sandbox/block_resolver.py  

역할

- block payload 해석
- slot 기반 데이터 선택
- chunk lazy-load 처리
- fallback 처리

Sandbox는 block payload + resolver 기반 대시보드 구조를 가진다.

---

## OPS

ops_core/*

Validation / Orchestration

---

## Builder

modules/builder/*  
templates/*  

HTML 렌더링

---

## UI Console

ui/*

Streamlit 기반 운영 콘솔

역할

- 파일 업로드
- 파이프라인 실행
- 결과 탐색

---

# 5. KPI Single Source Rule

KPI 공식은 반드시 아래 엔진만 사용한다.

modules/kpi/crm_engine.py  
modules/kpi/sandbox_engine.py  
modules/kpi/territory_engine.py  
modules/kpi/prescription_engine.py  

금지 사항

- Builder KPI 재계산
- Sandbox의 CRM KPI 재계산
- Territory KPI 재계산
- RADAR KPI 재계산
- payload 단계 중복 계산

KPI 계산은 반드시 KPI Engine에서만 수행한다.

---

# 6. Block Composition Principle

Sandbox는 결과를 단일 payload로만 전달하지 않고  
block payload 구조로도 제공한다.

핵심 원칙

- 분석 결과는 block 단위 자산으로 제공 가능
- resolver는 block registry를 기준으로 block을 해석
- 템플릿은 slot 기준으로 block을 소비
- chunk 데이터는 manifest + lazy-load asset 구조로 처리
- fallback은 허용하지만 계산 로직은 템플릿에 넣지 않는다

이 구조는 현재 Sandbox에서 먼저 적용되었으며  
향후 다른 보고서 구조에도 확장 가능하다.

---

# 7. 데이터 흐름

Raw Data  
→ Adapter  
→ Core Engine  
→ Result Asset  
→ Validation Layer (OPS)  
→ Intelligence  
→ Composition / Resolver  
→ Presentation (Builder)

핵심 원칙

**계산 / 검증 / 표현은 반드시 분리되어야 한다.**

이 구조를 통해

- KPI 신뢰성
- 분석 확장성
- 보고서 안정성

을 동시에 확보할 수 있다.

---

# 결론

Sales Data OS는 단순한 대시보드 시스템이 아니라

데이터 표준화 → KPI 계산 → 품질 검증 → 분석 → 의사결정 → 표현

으로 이어지는 **영업 데이터 운영 체계**다.

특히 Sandbox에서 도입된

- block payload
- resolver
- slot renderer

구조는 분석 결과를 **재사용 가능한 분석 자산으로 만드는 핵심 구조**다.