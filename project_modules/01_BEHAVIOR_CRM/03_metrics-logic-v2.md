# CRM 지표별 상세 로직 명세서 v2 (선행지표 중심)

## 1. 문서 목적

본 문서는 `crm-rebuild-detailed-plan-v2.md` 기준으로 KPI 로직을 재정의한다.  
핵심 목표는 입력 강제가 아니라 "좋은 행동 유도"이며, 지표 체계는 선행-운영-결과 3계층으로 구성한다.

## 2. 공통 규칙

### 2.1 계산 단위

- 기본 단위: 사용자 x 기간(일/주/월)
- 타임존: Asia/Seoul

### 2.2 데이터 신뢰도 등급

- `verified`: 객관 증빙 기반
- `assisted`: 일부 증빙 + 사용자 보정
- `self_only`: 자기기입

### 2.3 점수 반영 규칙

1. `self_only` 데이터는 핵심 점수 반영 상한 적용
2. 동일 계정/동일 텍스트 반복은 감점
3. 추상적 Next Action은 무효 처리
4. 결측값은 `0`이 아닌 `unscored`로 처리

---

## 3. KPI 아키텍처

### 3.1 선행행동 계층 (코어)

- HIR, RTR, BCR, PHR

### 3.2 운영관리 계층 (보조)

- NAR, AHS, PV

### 3.3 결과검증 계층 (후행)

- FGR, PI
- TRG, SWR (경영 리포팅 보조 지표)

---

## 4. HIR (High-Impact Rate)

### 4.1 정의

성과기여 가능성이 높은 행동의 실행 품질 지수

### 4.2 계산식

`HIR = SUM(activity_weight * quality_factor * impact_factor * trust_factor) / total_activities`

### 4.3 파라미터

- `activity_weight` (예: visit 1.3, presentation 1.4, follow_up 1.2, call 0.9, message 0.6)
- `quality_factor` (0.7~1.3)
- `impact_factor` (0.8~1.5, 과거 성과 연계도 기반)
- `trust_factor` (verified 1.0, assisted 0.85, self_only 0.7)

### 4.4 예외처리

- 설명 20자 미만 또는 중복 의심 건은 0.3배
- self_only만 존재하는 기간은 HIR 상한 적용

### 4.5 코칭 해석

- HIR 낮음 + 활동수 높음: 행동 품질 문제
- HIR 낮음 + 활동수 낮음: 우선순위/실행량 문제

---

## 5. RTR (Relationship Temperature Rate)

### 5.1 정의

계정 관계의 현재 온도를 나타내는 지표

### 5.2 계산식

`RTR = SUM(sentiment_score * time_decay * trust_factor) / relationship_events`

### 5.3 보조 규칙

- 최근 7일 가중치 최대
- 30일 초과 이벤트는 감쇠 반영

### 5.4 코칭 해석

- RTR 하락: 관계 냉각 조짐, 접촉 전략 재설계 필요

---

## 6. BCR (Behavior Consistency Rate)

### 6.1 정의

실행의 규칙성과 루틴 품질을 측정하는 지표

### 6.2 계산식

`BCR = 0.4 * volume_score + 0.6 * regularity_score`

### 6.3 보조 규칙

- regularity_score는 활동 간격 표준편차 역수 기반
- 몰아치기 입력 패턴은 감점

### 6.4 코칭 해석

- BCR 낮음: 단기 집중/장기 공백 패턴 개선 필요

---

## 7. PHR (Proactive Health Rate)

### 7.1 정의

활동이 구체적 Next Action으로 연결되는 비율

### 7.2 계산식

`PHR = valid_next_actions / total_activities`

### 7.3 유효 기준

- 미래 날짜 존재
- 실행 주체/행동/기한이 명확
- "추후 연락", "검토 예정" 등 추상 메모 제외

### 7.4 코칭 해석

- PHR 낮음: 미팅이 파이프라인 전진으로 연결되지 않음

---

## 8. NAR (Next Action Reliability)

### 8.1 정의

계획된 Next Action이 기한 내 실제 이행되는 신뢰도

### 8.2 계산식

`NAR = executed_on_time_next_actions / due_next_actions`

### 8.3 판정 규칙

- `due`: 기준기간 내 예정일 도래
- `on_time`: 예정일 +2일 이내 실행
- `due_next_actions < 5`: 참고지표 플래그

### 8.4 코칭 해석

- NAR 낮음 + PHR 높음: 계획은 세우나 실행력이 약함

---

## 9. AHS (Account Health Score)

### 9.1 정의

계정의 접점/관계/경쟁 리스크를 통합한 건강도

### 9.2 계산식

`AHS = 0.35*recency + 0.25*rtr_component + 0.20*coverage + 0.20*competitor_risk_inverse`

### 9.3 코칭 해석

- AHS 저하: 관계/커버리지/경쟁 대응 중 취약축 보완 필요

---

## 10. PV (Pipeline Velocity)

### 10.1 정의

파이프라인 전진 가치의 시간 대비 이동 속도

### 10.2 계산식

`PV = SUM(stage_value * stage_progress_prob) / avg_stage_dwell_days`

### 10.3 코칭 해석

- PV 저하 + dwell 증가: 병목 단계 코칭 필요

---

## 11. FGR (Field Growth Rate)

### 11.1 정의

담당 영역의 성장률 (제약 특성 반영)

### 11.2 계산식

`FGR = 0.6*quantity_growth + 0.4*revenue_growth`

### 11.3 보조 규칙

- 약가/공급/정책 이슈 발생 시 보정 플래그

---

## 12. PI (Prescription Index)

### 12.1 정의

계정 난이도와 처방 성과를 보정한 종합 성과지수

### 12.2 계산식

`PI = (weighted_prescription * 0.7) + (growth_component * 0.3)`

### 12.3 보정 요소

- 계정 유형 가중치
- 제품 전략 가중치
- 지역/포트폴리오 난이도 보정

---

## 13. TRG/SWR (경영 보조 지표)

### 13.1 TRG

`TRG = (revenue_current - revenue_baseline_adjusted) / revenue_baseline_adjusted`

### 13.2 SWR

`SWR = accounts_meeting_target_share / target_accounts`

### 13.3 사용 원칙

- 개인 코칭의 1차 지표로 사용 금지
- 월/분기 경영 리포팅 보조 지표로 사용

---

## 14. 운영 종합 스코어 (코칭 우선순위용)

### 14.1 목적

보상 직접 연계가 아닌 코칭 우선순위 선정을 위한 내부 지표

### 14.2 계산식 (예시)

`CoachScore = 0.30*HIR + 0.20*RTR + 0.15*BCR + 0.15*PHR + 0.10*NAR + 0.10*AHS`

### 14.3 원칙

- 결과지표(FGR/PI/TRG/SWR)는 검증 레이어에서 별도 확인
- CoachScore 단독으로 개인 평가 금지

---

## 15. 품질보증 체크리스트

1. `unscored` 처리 일관성
2. self_only 반영 상한 정책 준수
3. 중복/추상 입력 로그 보존
4. 월간 시차 상관 분석(HIR/RTR/BCR/PHR -> FGR/PI)
5. 지표 버전 태깅(`metric_version`)

## 16. 결론

본 로직의 핵심은 "입력 많이 하기"가 아니라 "고효과 행동을 반복 실행"하게 만드는 것이다.  
따라서 선행지표(HIR/RTR/BCR/PHR)가 운영의 중심이며, 결과지표(FGR/PI/TRG/SWR)는 검증과 전략 보정에 사용한다.
