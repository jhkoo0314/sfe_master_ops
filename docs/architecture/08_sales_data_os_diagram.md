
# Sales Data OS Architecture Diagram

작성일: 2026-03-16

이 문서는 Sales Data OS 전체 구조를 **한 장의 아키텍처 다이어그램으로 설명**한다.

---

## Overall System Architecture

flowchart TD

subgraph Data_Layer
A1[CRM Activity]
A2[Sales Data]
A3[Target Data]
A4[Prescription Data]
A5[Master Data]
end

subgraph Adapter_Layer
B1[CRM Adapter]
B2[Sales Adapter]
B3[Prescription Adapter]
B4[Territory Adapter]
end

subgraph Core_Engine
C1[CRM KPI Engine]
C2[Sandbox KPI Engine]
C3[Territory KPI Engine]
C4[Prescription KPI Engine]

C5[CRM Service]
C6[Sandbox Service]
C7[Territory Service]
C8[Prescription Service]
end

subgraph Result_Assets
D1[crm_result_asset]
D2[sandbox_result_asset]
D3[territory_result_asset]
D4[prescription_result_asset]
end

subgraph OPS_Validation
E1[Quality Validation]
E2[Mapping Validation]
E3[Pipeline Orchestration]
end

subgraph Intelligence
F1[Sandbox Analysis]
F2[Territory Analysis]
F3[Prescription Analysis]
F4[RADAR Decision Engine]
end

subgraph Composition
G1[Block Payload]
G2[Block Registry]
G3[Block Resolver]
G4[Slot Renderer]
G5[Chunk Lazy Load]
end

subgraph Presentation
H1[Builder Engine]
H2[HTML Templates]
H3[Report Preview]
end

A1 --> B1
A2 --> B2
A3 --> B2
A4 --> B3
A5 --> B4

B1 --> C1
B2 --> C2
B3 --> C3
B4 --> C4

C1 --> C5
C2 --> C6
C3 --> C7
C4 --> C8

C5 --> D1
C6 --> D2
C7 --> D3
C8 --> D4

D1 --> E1
D2 --> E1
D3 --> E1
D4 --> E1

E1 --> F1
E1 --> F2
E1 --> F3
E1 --> F4

F1 --> G1
F2 --> G1
F3 --> G1
F4 --> G1

G1 --> G2
G2 --> G3
G3 --> G4
G4 --> G5

G5 --> H1
H1 --> H2
H2 --> H3


````

---

# Layer Responsibilities

## Data Layer

원천 영업 데이터를 저장하는 계층

대표 데이터

* CRM activity
* Sales
* Target
* Prescription
* Master data

---

## Adapter Layer

회사별 데이터 포맷을 **표준 스키마로 정규화**

예

* CRM activity 표준화
* Sales / Target 정규화
* Prescription 연결 데이터 정리

---

## Core Engine Layer

KPI 계산 및 도메인 집계를 담당

구성

KPI Engine

* CRM KPI Engine
* Sandbox KPI Engine
* Territory KPI Engine
* Prescription KPI Engine

Domain Services

* CRM Service
* Sandbox Service
* Territory Service
* Prescription Service

---

## Result Asset Layer

각 모듈이 계산 결과를 **표준 결과 자산 형태로 저장**

예

* crm_result_asset.json
* sandbox_result_asset.json
* territory_result_asset.json
* prescription_result_asset.json

---

## OPS (Validation Layer)

OPS는 시스템 전체가 아니라 **검증 계층**

역할

* 데이터 품질 검증
* 매핑 상태 검증
* 파이프라인 실행 통제

OPS는 다음을 하지 않는다

* KPI 계산
* 분석 로직 구현
* 보고서 렌더링

---

## Intelligence Layer

분석 및 의사결정 지원 계층

모듈

Sandbox
→ KPI 기반 분석 대시보드

Territory
→ 권역 및 담당자 구조 분석

Prescription
→ 처방 흐름 분석

RADAR
→ signal detection / issue prioritization / decision option

---

## Composition / Resolver Layer

분석 결과를 **표현 가능한 구조로 해석하는 계층**

구성

* block payload
* block registry
* block resolver
* slot renderer
* chunk lazy-load

이 구조는 현재 **Sandbox 대시보드에서 먼저 적용된 패턴**

---

## Presentation Layer

최종 표현 계층

구성

* Builder Engine
* HTML Templates
* Report Preview

Builder는 **render-only 원칙**을 따른다.

Builder는 KPI를 재계산하지 않는다.

---

# 핵심 설계 원칙

## 1. KPI Single Source

KPI는 반드시 KPI Engine에서만 계산한다.

금지

* Builder KPI 계산
* 분석 모듈 KPI 재계산
* payload 단계 중복 계산

---

## 2. Validation First

OPS 검증 통과 데이터만 분석 / 표현 레이어로 전달

---

## 3. Analysis / Rendering Separation

분석과 표현을 완전히 분리

분석

* Sandbox
* Territory
* Prescription
* RADAR

표현

* Builder
* HTML

---

## 4. Block Composition

Sandbox는 결과를 **block payload 단위로 구성**

block resolver가 slot 기준으로 데이터를 해석한다.

이 구조는 향후 다른 보고서 구조에도 확장 가능하다.

---

# System Flow Summary

Raw Data
→ Adapter
→ Core Engine
→ Result Asset
→ OPS Validation
→ Intelligence
→ Block Resolver
→ Builder
→ HTML Reports

---

# System Goal

Sales Data OS의 목적은 단순한 대시보드가 아니라

**영업 데이터를 분석 가능한 운영 체계로 만드는 것**이다.

이 구조는 다음을 가능하게 한다.

* KPI 기반 영업 운영
* 분석 자동화
* 의사결정 지원
* 보고서 자동 생성

```

---

## 이 다이어그램의 장점

포트폴리오에서 이 그림 하나로 아래를 **10초 안에 설명할 수 있다.**

```

Raw Data
→ Adapter
→ KPI Engine
→ OPS Validation
→ Intelligence
→ Block Resolver
→ Builder
→ HTML Reports

```

즉 **일반 BI가 아니라 “운영 OS” 구조**라는 걸 보여준다.

---

## 마지막으로 중요한 것

지금 재현님 프로젝트의 진짜 강점은 이것이다.

일반적인 BI 구조

```

Raw Data
→ Dashboard

```

재현님 구조

```

Raw Data
→ Adapter
→ KPI Engine
→ OPS Validation
→ Intelligence
→ Composition
→ Builder

```

즉 **데이터 운영 체계(OS)**다.

---

원하면 다음으로  
**면접관이 이 구조를 봤을 때 바로 이해하도록 만드는 "1페이지 Architecture Slide"**도 만들어줄게.  
(포트폴리오에서 제일 중요한 자료다.)
```
