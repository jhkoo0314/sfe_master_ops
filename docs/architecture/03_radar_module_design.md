# RADAR Module Design

## For Sales Data OS / SFE Portfolio Prototype

Version: v0.1
Status: Draft for Implementation

---

## 1. 문서 목적

이 문서는 Sales Data OS 내 **RADAR 모듈**의 역할, 입력, 출력, 처리 단계, 금지 규칙, 구현 범위를 정의한다.
목표는 RADAR를 단순 대시보드가 아니라 **의사결정 지원용 Intelligence Layer 모듈**로 구현하는 것이다.

본 문서는 **실무 완전 대응 시스템**이 아니라, **포트폴리오 수준에서 구조적 기획력과 실행 가능성**을 보여주는 것을 목표로 한다.

---

## 2. 모듈 한 줄 정의

**RADAR는 validation 승인된 KPI/분석 결과를 바탕으로 조기 경보 신호를 탐지하고, 우선순위를 부여하고, 의사결정 선택지 템플릿을 생성하는 Intelligence Layer 모듈이다.**

---

## 3. 모듈 위치

RADAR는 Sales Data OS의 **Intelligence Layer**에 속한다.

```text
Sales Data OS

Data Layer
Adapter Layer
Core Engine Layer
Validation / Orchestration Layer (OPS)
Intelligence Layer
  - Sandbox
  - Territory
  - Prescription
  - RADAR
Presentation Layer
  - Builder
```

---

## 4. RADAR의 책임

RADAR는 아래 3가지만 수행한다.

### 4.1 Signal Detection

* KPI 및 요약 지표에서 경보 후보를 탐지한다.
* 기준값(threshold), 변화율(delta), 조합 규칙(rule bundle)을 사용한다.

### 4.2 Issue Prioritization

* 탐지된 signal에 우선순위를 부여한다.
* 심각도, 영향 범위, 반복성, 최근성 등을 반영한다.

### 4.3 Decision Option Templating

* signal 유형별로 대응 선택지 템플릿을 생성한다.
* 최종 결정은 사람(경영진/관리자)이 수행한다.

---

## 5. RADAR의 비책임

RADAR는 아래를 하지 않는다.

### 5.1 KPI 재계산 금지

* KPI는 반드시 `modules/kpi/*`에서만 계산한다.
* RADAR는 KPI 결과를 입력으로 소비만 한다.

### 5.2 원인 확정 금지

* RADAR는 "확정 원인"을 말하지 않는다.
* 가능성 있는 원인 후보 또는 해석 힌트 수준만 허용한다.

### 5.3 현장 행동 자동 지시 금지

* 특정 병원 방문/면담/점심 약속/동선 지시 금지
* 스케줄 수준 액션 추천 금지

### 5.4 Builder 역할 침범 금지

* RADAR는 렌더링 책임이 없다.
* HTML 구성은 Builder가 담당한다.

---

## 6. 입력 계약 (Input Contract)

RADAR는 반드시 **validation-approved input**만 사용한다.

### 6.1 필수 입력

1. **KPI Engine Output**

   * CRM KPI 결과
   * Sandbox KPI 결과
   * Territory KPI 결과
   * Prescription KPI 결과 중 필요한 요약값

2. **Validation-approved Result Asset**

   * OPS validation 통과 결과
   * 최소한 usable / approved 상태의 asset

3. **Sandbox Summary Metrics**

   * 샌드박스의 요약 지표
   * 예: branch summary, rep summary, item summary, trend summary

---

## 7. 입력 데이터 모델 초안

### 7.1 radar_input.json 개념 구조

```json
{
  "meta": {
    "company_key": "daon_pharma",
    "run_id": "2026-03-16T10-20-00",
    "period_type": "monthly",
    "period_value": "2026-03",
    "source_status": "validation_approved"
  },
  "kpi_summary": {
    "goal_attainment_pct": 93.2,
    "pv_change_pct": -18.4,
    "hir": 58.3,
    "rtr": 67.1,
    "bcr": 61.5,
    "phr": 64.2
  },
  "scope_summaries": {
    "by_branch": [],
    "by_rep": [],
    "by_product": []
  },
  "validation_summary": {
    "status": "approved",
    "warnings": [],
    "quality_score": 0.94
  },
  "sandbox_summary": {
    "top_declines": [],
    "top_gains": [],
    "trend_flags": []
  }
}
```

---

## 8. 출력 계약 (Output Contract)

RADAR는 아래 3개 구조를 출력한다.

### 8.1 Signal List

탐지된 경보 목록

### 8.2 Priority Score

각 signal의 상대 우선순위

### 8.3 Decision Option Template

signal 유형별 대응 선택지 템플릿

---

## 9. 출력 데이터 모델 초안

### 9.1 radar_result_asset.json 개념 구조

```json
{
  "meta": {
    "company_key": "daon_pharma",
    "run_id": "2026-03-16T10-20-00",
    "period_type": "monthly",
    "period_value": "2026-03",
    "generated_at": "2026-03-16T10:30:00"
  },
  "summary": {
    "overall_status": "warning",
    "signal_count": 3,
    "top_issue": "RTR weakness with sales underperformance"
  },
  "signals": [
    {
      "signal_id": "SIG-RTR-001",
      "signal_type": "rtr_drop",
      "severity": "warning",
      "priority_score": 82,
      "title": "RTR below expected range",
      "message": "RTR is below threshold and linked with weak goal attainment.",
      "scope": {
        "level": "company",
        "branch_keys": ["daegu"]
      },
      "evidence": {
        "rtr": 67.1,
        "threshold": 70.0,
        "goal_attainment_pct": 93.2
      },
      "possible_explanations": [
        "relationship maintenance weakness",
        "coverage inconsistency",
        "recent field execution slowdown"
      ],
      "decision_options": [
        {
          "option_code": "A",
          "label": "manager coaching focus",
          "description": "Review branch-level relationship maintenance gaps and strengthen coaching."
        },
        {
          "option_code": "B",
          "label": "monitor one more cycle",
          "description": "Keep current execution but track next monthly trend before intervention."
        }
      ]
    }
  ]
}
```

---

## 10. RADAR 처리 단계

RADAR는 아래 4단계로 처리한다.

### Step 1. Input Load

* KPI result
* validation-approved asset
* sandbox summary
  를 로드한다.

### Step 2. Signal Rule Evaluation

* threshold rule
* delta rule
* combination rule
  를 적용해 signal 후보를 만든다.

### Step 3. Priority Scoring

각 signal에 대해 점수화한다.

예시 기준:

* severity
* business impact
* trend persistence
* scope size
* validation confidence

### Step 4. Decision Template Generation

signal 유형별 템플릿을 생성한다.

---

## 11. Signal 설계 원칙

RADAR signal은 많을수록 좋은 것이 아니다.
포트폴리오 기준에서는 **소수의 명확한 signal**이 중요하다.

### 목표

* 한 번의 monthly run에서 **0~5개 signal**
* signal 남발 금지
* 중요 문제만 요약

### signal 유형

1. Performance signal
2. Trend signal
3. Execution signal
4. Compound signal

---

## 12. 1차 Signal 후보

포트폴리오 v0.1에서는 아래 signal만 구현한다.

### 12.1 Goal Underperformance Signal

* 조건: `goal_attainment_pct < threshold`
* 목적: 매출/성과 미달 경보

### 12.2 PV Decline Signal

* 조건: `pv_change_pct <= negative threshold`
* 목적: 성장성 저하 경보

### 12.3 HIR Weakness Signal

* 조건: `hir < threshold`
* 목적: 핵심 타겟 접촉 부족 경보

### 12.4 RTR Weakness Signal

* 조건: `rtr < threshold`
* 목적: 관계 유지 약화 경보

### 12.5 Compound Risk Signal

* 조건: 복수 signal 동시 발생
* 예: `goal_attainment low` + `rtr low`
* 목적: 의사결정 우선순위 상승

---

## 13. Threshold 정책

포트폴리오 버전에서는 **고정 임계값**을 우선 적용한다.

### 예시 기본값

* `goal_attainment_pct < 95` → warning
* `goal_attainment_pct < 90` → critical
* `pv_change_pct <= -15` → warning
* `pv_change_pct <= -25` → critical
* `hir < 60` → warning
* `hir < 50` → critical
* `rtr < 70` → warning
* `rtr < 60` → critical

### 비고

실무형 동적 threshold는 추후 과제로 남긴다.

---

## 14. Priority Score 설계

우선순위는 아래 요소를 합산하여 계산한다.

### 예시 점수 요소

* severity score
* business impact score
* persistence score
* scope score
* confidence score

### 예시

```text
priority_score =
(severity * 0.35) +
(impact * 0.25) +
(persistence * 0.15) +
(scope * 0.15) +
(confidence * 0.10)
```

출력은 0~100 정수로 정규화한다.

---

## 15. Decision Option Template 설계

RADAR는 선택지만 제시한다.
선택지는 액션 실행 지시가 아니라 **관리 관점 대응 옵션**이어야 한다.

### 예시 템플릿 유형

#### A. Coaching Focus

* 팀장/관리자 코칭 강화
* branch-level 리뷰
* KPI 원인 drill-down

#### B. Monitoring Hold

* 이번 cycle은 추가 조치 없이 추세 관찰
* 다음 cycle 비교 기준 확보

#### C. Selective Intervention

* 특정 지점/담당자군만 추가 점검
* 제한적 개입

#### D. Strategic Escalation

* 경영진 보고 필요
* 추가 자원/정책 검토 필요

---

## 16. 파일/모듈 설계

`modules/radar/` 구조는 아래처럼 시작한다.

```text
modules/radar/
  __init__.py
  schemas.py
  service.py
  signal_engine.py
  priority_engine.py
  option_engine.py
```

---

## 17. 모듈별 책임

### schemas.py

* 입력/출력 데이터 모델 정의
* pydantic schema 또는 dataclass
* 계약 위반 시 fail

### service.py

* RADAR 진입점
* 전체 실행 orchestration
* 다른 engine 호출

### signal_engine.py

* signal rule 평가
* threshold / delta / compound rule 처리

### priority_engine.py

* signal 우선순위 점수 계산

### option_engine.py

* decision option template 생성

---

## 18. 서비스 인터페이스 초안

### 18.1 Python interface 예시

```python
def build_radar_result(
    radar_input: RadarInput,
) -> RadarResultAsset:
    ...
```

### 18.2 처리 흐름

```python
input_data = load_radar_input(...)
signals = evaluate_signals(input_data)
prioritized = score_signals(signals, input_data)
options = attach_decision_options(prioritized)
result = build_result_asset(input_data, options)
return result
```

---

## 19. Validation 연동 규칙

RADAR는 validation 통과 결과만 사용한다.

### 규칙

* validation status가 approved / usable 이 아니면 fail 또는 skip
* low-confidence asset은 signal confidence에 반영
* validation 경고가 많은 경우 summary에 표시

---

## 20. Builder 연동 규칙

RADAR는 최종적으로 Builder가 렌더링할 수 있는 payload를 제공한다.

### 규칙

* RADAR는 HTML 생성 안 함
* `radar_result_asset.json` 생성
* 필요 시 `radar_builder_payload.json` 생성
* Builder는 해당 payload를 소비해서 보고서 생성

---

## 21. 실패 처리 규칙

아래 경우 RADAR는 fail-fast 또는 graceful skip 한다.

### fail

* 필수 입력 누락
* schema validation 실패
* KPI input 없음
* validation-approved 상태 아님

### skip 또는 warning

* signal 없음
* scope summary 일부 누락
* sandbox summary 제한적 제공

---

## 22. 테스트 기준

### 단위 테스트

* signal rule 테스트
* priority score 테스트
* option template 테스트
* schema validation 테스트

### 금지 규칙 테스트

아래가 발견되면 fail 처리

* RADAR 내부 KPI 재계산
* 원인 확정 문구 생성
* 현장 스케줄 지시 문구 생성

---

## 23. 포트폴리오 구현 범위

v0.1 구현 범위는 아래로 제한한다.

### 포함

* company-level monthly radar
* 4~5개 signal
* fixed threshold
* priority score
* decision options 2~3개
* JSON result asset 생성

### 제외

* branch/rep full drill-down
* dynamic threshold learning
* AI 자유서술형 해석
* 일정/동선 추천
* 실시간 event-driven radar

---

## 24. Codex 구현 우선순위

### Phase 1

* `modules/radar/` 폴더 생성
* schema 정의
* service stub 작성

### Phase 2

* signal engine 구현
* fixed threshold rule 구현

### Phase 3

* priority engine 구현
* option template 구현

### Phase 4

* result asset 생성
* Builder 연동 준비

---

## 25. 완료 기준 (Definition of Done)

아래를 만족하면 v0.1 완료로 본다.

* `modules/radar/` 기본 구조 생성
* 입력 schema / 출력 schema 정의 완료
* 4개 이상 signal rule 동작
* priority score 계산 가능
* decision option template 생성 가능
* KPI 재계산 없이 result asset 생성 가능
* validation-approved input만 처리
* unit test 통과

---

## 26. 최종 정의

**RADAR는 Sales Data OS의 Intelligence Layer에서 동작하는 조기 경보 및 의사결정 지원 모듈이며, KPI 계산 엔진이 아니라 validation 승인된 KPI 결과를 해석 가능한 signal과 선택지로 변환하는 모듈이다.**

---


