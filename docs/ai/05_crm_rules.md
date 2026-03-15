# CRM Rules

## 목적

이 문서는 Behavior CRM 모듈의 공식 입력 철학, KPI 구조, 점수 반영 원칙을 정의한다.

CRM은 단순 활동 저장소가 아니라 OPS에 전달할 출발 자산을 만드는 모듈이다.

## CRM 위치

CRM은 5개 모듈 중 가장 먼저 공통 문맥을 만든다.

핵심 역할:
- 병원/지점/담당자 축 안정화
- 활동 데이터 표준화
- 행동 기반 KPI 자산 생성
- 다른 모듈이 재사용할 출발 자산 제공

## 공식 입력 흐름

`hospital_public -> hospital_master -> company_master_standard -> crm_standard_activity -> crm_result_asset -> OPS`

## 공통 계산 원칙

- 기본 단위: 사용자 x 기간(일/주/월)
- 타임존: Asia/Seoul
- 결측값은 `0`이 아니라 `unscored`
- `self_only`는 핵심 점수 반영 상한 적용
- 동일 계정/동일 텍스트 반복은 감점
- 추상적 Next Action은 무효
- 설명 20자 미만 또는 중복 의심 입력은 품질 감점

## 데이터 신뢰도 등급

- `verified`: 객관 증빙 기반
- `assisted`: 일부 증빙 + 사용자 보정
- `self_only`: 자기기입

예시 trust factor:
- verified = 1.0
- assisted = 0.85
- self_only = 0.7

## KPI 구조

### 선행행동 계층
- HIR
- RTR
- BCR
- PHR

### 운영관리 계층
- NAR
- AHS
- PV

### 결과검증 계층
- FGR
- PI
- TRG
- SWR

원칙:
운영 중심은 선행지표다.
결과지표는 검증과 전략 보정에 사용한다.

## 핵심 공식

### HIR
`HIR = SUM(activity_weight * quality_factor * impact_factor * trust_factor) / total_activities`

### RTR
`RTR = SUM(sentiment_score * time_decay * trust_factor) / relationship_events`

### BCR
`BCR = 0.4 * volume_score + 0.6 * regularity_score`

### PHR
`PHR = valid_next_actions / total_activities`

### NAR
`NAR = executed_on_time_next_actions / due_next_actions`

### AHS
`AHS = 0.35*recency + 0.25*rtr_component + 0.20*coverage + 0.20*competitor_risk_inverse`

### PV
`PV = SUM(stage_value * stage_progress_prob) / avg_stage_dwell_days`

### FGR
`FGR = 0.6*quantity_growth + 0.4*revenue_growth`

### PI
`PI = (weighted_prescription * 0.7) + (growth_component * 0.3)`

### TRG
`TRG = (revenue_current - revenue_baseline_adjusted) / revenue_baseline_adjusted`

### SWR
`SWR = accounts_meeting_target_share / target_accounts`

## CoachScore 원칙

CoachScore는 코칭 우선순위용 내부 지표다.

`CoachScore = 0.30*HIR + 0.20*RTR + 0.15*BCR + 0.15*PHR + 0.10*NAR + 0.10*AHS`

원칙:
- 결과지표는 CoachScore에 직접 넣지 않는다.
- CoachScore 단독으로 개인 평가하지 않는다.

## CRM 결과 자산 최소 포함 항목

- 행동 프로파일
- KPI 요약
- 활동 문맥 요약
- 매핑/품질 요약
- `metric_version`
- `unscored` 상태
- 신뢰도 분포

## 철학

CRM의 핵심은 입력 강제가 아니라 고효과 행동의 반복 실행 유도다.