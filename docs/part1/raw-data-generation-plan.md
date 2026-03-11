# SFE Raw 데이터 생성 기준 문서

## 1. 문서 목적

이 문서는 `C:\sfe_master_ops\data\raw` 기준의 테스트용 raw 데이터를 실제 운영 직전 수준으로 다시 만들기 위한 기준 문서다.

핵심 목적은 3가지다.

1. CRM 중심 운영 로직이 실제로 계산 가능한 raw 데이터 만들기
2. `sales`와 `fact_ship`의 브랜드/품목 체계를 `한결제약` 기준으로 통일하기
3. 어댑터 정규화를 거쳐 `ops_console.py`, `html_builder`, 결과 템플릿에서 바로 검증 가능한 리허설 데이터 세트 만들기

이 문서는 앞으로 raw 데이터 설계의 단일 기준 문서로 사용한다.

1. 새 방향이 필요하면 이 문서를 먼저 수정한다.
2. 중복 설명 문서는 늘리지 않는다.
3. 세부 초안이나 작업 파일도 이 문서의 방향을 벗어나면 안 된다.
4. 이후 새로 만드는 관련 문서에는 이 기준 문서 경로를 첫 부분에 참조로 남긴다.

## 2. 현재 판단

현재 raw 파일의 기본 키 정합성은 좋은 편이다.

- 병원ID
- 담당자ID
- 지점ID

위 3개는 `crm`, `sales`, `target`, `assignment`에서 잘 맞는다.

하지만 실운영용 raw로 보기에는 아직 부족한 부분이 있다.

1. CRM이 단순 활동 파일 수준이라 KPI 계산 중심 설계가 더 필요하다.
2. `fact_ship`와 `sales`의 브랜드/품목 체계는 산발적일 가능성이 높다.
3. 원본형 raw에서 OPS 표준형으로 넘어가는 어댑터 관점이 아직 충분히 반영되지 않았다.

## 3. OPS 세계관 기준 원칙

OPS의 목표는 깔끔한 정제 파일만 받는 도구가 아니다.

핵심은 아래 흐름이다.

`회사 원본형 raw -> Adapter 정규화 -> OPS 표준 자산 -> 운영콘솔 검증 -> 결과 보고서/지도/빌더`

즉:

1. 회사별 원본 데이터는 지저분해도 된다.
2. 어댑터가 컬럼, 코드, 브랜드, 날짜, 키를 정리한다.
3. 운영콘솔은 회사별 파일 형식을 직접 알지 않고 OPS 표준 자산만 받는다.
4. 그래서 raw 생성도 "회사 원본형"과 "OPS 표준형"을 함께 검증할 수 있어야 한다.

## 4. 가장 중요한 설계 원칙

이번 raw 데이터 생성은 `sales` 중심이 아니라 `CRM` 중심으로 설계한다.

이유:

1. CRM이 가장 많은 원천 이벤트를 공급한다.
2. HIR, RTR, BCR, PHR 같은 핵심 선행지표가 CRM에서 계산된다.
3. `sales`, `target`, `fact_ship`는 CRM 행동의 결과 검증 또는 연결 증빙 역할을 한다.

즉 구조는 아래 순서로 잡는다.

`CRM 행동 데이터 -> KPI 계산 가능 구조 -> Sales/Target 결과 연결 -> Fact_ship 유통 연결`

## 5. 참고한 기준 문서

이번 계획은 아래 자료를 반영한다.

- `data/raw/company/sample_SFE_Master_Logic_v1.0.xlsx`
- `data/raw/crm/02_detailed-plan-v2.md`
- `data/raw/crm/03_metrics-logic-v2.md`

## 6. Master Logic 5개 시트 반영 원칙

### 6.1 Activity_Weights

CRM raw에는 아래 8개 활동이 실제로 들어가야 한다.

- PT
- 시연
- 클로징
- 대면
- 니즈환기
- 컨택
- 접근
- 피드백

주의:

1. 활동명만 있으면 안 된다.
2. 활동별 발생 빈도도 현실적으로 다르게 넣어야 한다.
3. `컨택`, `대면`은 상대적으로 많고 `PT`, `클로징`은 적어야 자연스럽다.

### 6.2 Segment_Weights

병원 규모와 전략 비중을 raw 설계에 반영해야 한다.

- 상급종합
- 종합병원
- 일반의원
- 약국/기타

같은 행동이라도 계정 난이도와 성과 기대치가 다르게 보이게 해야 한다.

### 6.3 Metric_Specs

CRM raw는 아래 지표를 계산할 수 있는 필드를 가져야 한다.

- HIR
- RTR
- BCR
- PHR
- FGR
- PI

### 6.4 Coaching_Rules

raw 안에는 아래 코칭 시나리오가 일부러 보이게 들어가야 한다.

- 방문수는 높은데 HIR 낮은 담당자
- HIR은 높은데 Reach가 낮은 담당자
- RTR 하락 담당자
- HIR, PHR 둘 다 높은 우수 담당자

### 6.5 System_Setup

운영 환경 가정도 데이터 기간에 반영한다.

- 리포팅 시차 1개월
- 전략 리드타임 4주
- T-score 기준 70
- 분석 분기 기준

## 7. CRM raw 설계 방향

CRM은 가장 먼저 설계하고 생성한다.

### 7.1 CRM raw의 목표

단순 활동 기록 파일이 아니라, 행동평가 숫자가 계산 가능한 원재료 파일이어야 한다.

### 7.2 CRM 권장 컬럼

- `activity_id`
- `activity_date`
- `rep_id`
- `rep_name`
- `branch_id`
- `branch_name`
- `hospital_id`
- `hospital_name`
- `hospital_segment`
- `contact_id`
- `product_id`
- `product_name`
- `activity_type`
- `activity_weight`
- `quality_factor`
- `impact_factor`
- `trust_level`
- `trust_factor`
- `sentiment_score`
- `next_action_date`
- `next_action_text`
- `next_action_owner`
- `is_next_action_valid`
- `is_duplicate_suspected`
- `is_short_memo`
- `channel`
- `call_count`
- `weighted_call`

### 7.3 CRM에서 반드시 살아 있어야 하는 숫자

#### HIR용

- `activity_weight`
- `quality_factor`
- `impact_factor`
- `trust_factor`

#### RTR용

- `sentiment_score`
- 활동일자
- 신뢰도

#### BCR용

- 활동일자 간격
- 사용자별 활동량
- 몰아치기 여부

#### PHR/NAR용

- `next_action_date`
- `next_action_text`
- `is_next_action_valid`
- 예정 대비 실제 실행 여부

## 8. 브랜드/품목 통일 원칙

현재 가장 큰 구조 문제는 `fact_ship`와 `sales`의 브랜드/품목 체계가 다를 수 있다는 점이다.

그래서 먼저 해야 하는 것은 raw 생성이 아니라 **한결제약 기준 품목 마스터**를 만드는 일이다.

### 8.1 먼저 만들 기준 파일

#### 한결제약 품목 마스터

- `canonical_product_id`
- `canonical_brand`
- `canonical_product_name`
- `sku`
- `formulation`
- `strength`
- `pack_size`
- `portfolio_group`
- `strategic_weight`

#### 브랜드 매핑표

- `fact_ship.brand -> canonical_brand`
- `fact_ship.sku -> canonical_product_id`
- `sales.품목명 -> canonical_brand`
- `sales.품목ID -> canonical_product_id`

### 8.2 생성 순서

1. `sales` 품목 후보 추출
2. `fact_ship` 브랜드/SKU 후보 추출
3. 중복/유사/불일치 항목 분류
4. 한결제약 기준 이름으로 통일
5. 매핑표 확정

## 9. 조직 운영 가정

이번 raw 데이터는 실제 운영 직전 리허설을 가정하므로 담당자 수도 명확히 고정한다.

- 의원 담당자 80명
- 종합병원 담당자 45명
- 총 담당자 125명

의미:

1. 의원 담당자는 대면 빈도와 계정 수가 많고, 반복 컨택 비중이 높게 설계한다.
2. 종합병원 담당자는 담당 계정 수는 적지만 PT, 시연, 클로징 비중이 상대적으로 높게 설계한다.
3. 동일 제품이라도 의원 포트폴리오와 종합병원 포트폴리오의 활동 패턴이 다르게 보이게 만든다.

## 10. 데이터 레이어 기준

앞으로 생성하는 데이터는 두 층으로 나눈다.

### 10.1 회사 원본형 raw

실제 현업에서 바로 받을 법한 파일이다.

특징:

1. 컬럼명이 제각각일 수 있다.
2. 브랜드명 표기가 흔들릴 수 있다.
3. 날짜 형식이 섞일 수 있다.
4. 일부 누락값, 중복값, 오타가 포함될 수 있다.

예:

- CRM 활동 원본
- 실적 원본
- 목표 원본
- shipment 원본

### 10.2 OPS 표준형 raw

어댑터를 통과한 뒤 OPS가 읽는 표준 자산이다.

예:

- `OPS_CRM_ACTIVITY`
- `OPS_SALES`
- `OPS_TARGET`
- `OPS_SHIPMENT`
- `OPS_ACCOUNT_MASTER`
- `OPS_REP_MASTER`

### 10.3 어댑터의 역할

어댑터는 아래 항목을 정리한다.

1. 컬럼명 표준화
2. 브랜드/품목명 표준화
3. 날짜 형식 표준화
4. 병원ID/담당자ID/지점ID 정규화
5. 단위와 코드 체계 정리
6. 누락과 이상치 기본 검증

즉, 운영콘솔에 맞춰 원본 파일을 억지로 만드는 것이 아니라, 원본형 raw를 현실적으로 만들고 어댑터가 OPS 표준으로 바꾸게 하는 것이 목표다.

## 11. 파일별 생성 전략

### 11.1 기준 마스터

먼저 아래 마스터를 만든다.

- 병원 마스터
- 담당자 마스터
- 지점 마스터
- 한결제약 품목 마스터
- 브랜드 매핑표
- 담당자 포지션 구분 컬럼

담당자 마스터에는 아래 구분을 포함한다.

- `rep_role`: 의원 / 종합병원
- `account_capacity`: 담당 가능 계정 수
- `channel_focus`: Clinic / General Hospital / Mixed
- `product_focus_group`: 의원 중심 브랜드군 / 병원 중심 브랜드군

### 11.2 CRM

가장 먼저 생성한다.

목적:

- KPI 계산의 원재료
- 행동 품질/신뢰도/다음 액션 포함
- 전체 운영 철학을 반영한 중심 데이터

추가 반영:

1. 의원 담당자 80명은 `컨택`, `대면`, `피드백` 비중이 높게 생성
2. 종합병원 담당자 45명은 `PT`, `시연`, `클로징` 비중이 더 높게 생성
3. 같은 브랜드라도 채널에 따라 활동 밀도와 전환 속도를 다르게 만든다

### 11.3 Target

병원 × 품목 × 월 기준으로 만든다.

원칙:

- 병원 규모
- 전략 중요도
- 담당자 포트폴리오

를 반영해 목표값을 만든다.

### 11.4 Sales

CRM 행동과 어느 정도 인과가 느껴지게 만든다.

원칙:

1. HIR/PHR이 높은 곳은 평균적으로 성과가 더 좋게 설계
2. 하지만 100% 직선 관계는 아니게 만든다
3. 외생 변수처럼 보이는 예외 사례도 포함한다

### 11.5 Fact_ship

도매상-약국-품목-SKU-출고일 기준으로 만든다.

원칙:

1. 일부는 `sales`와 자연스럽게 연결
2. 일부는 연결이 약하거나 누락
3. 그래야 Prescription 흐름 테스트가 의미 있다

## 12. 테스트 세트 구성

운영 직전 검증용으로 3세트를 권장한다.

### 12.1 정상 세트

- 정합성 높음
- KPI 계산 잘 됨
- 보고서/지도/슬라이드 시연용

### 12.2 경계 세트

- 일부 `self_only`
- 일부 next action 무효
- 일부 목표 누락
- 일부 브랜드 매핑 불완전

### 12.3 오류 유도 세트

- 중복 활동
- 짧은 메모
- 동일 텍스트 반복
- Rx 연결 누락
- 좌표/브랜드 일부 누락

추가 원칙:

1. 정상 세트만 만들지 않는다.
2. 실제 현업처럼 지저분한 회사 원본형 raw도 반드시 포함한다.
3. 같은 데이터가 어댑터를 거쳐 OPS 표준형으로 바뀌는지 확인할 수 있어야 한다.

## 13. 최종 생성 대상 파일

### 13.1 회사/마스터

- `data/raw/company/product_master_hangyeol_pharma.xlsx`
- `data/raw/company/product_brand_mapping.xlsx`
- `data/raw/company/hospital_master.xlsx`
- `data/raw/company/rep_master.xlsx`

### 13.2 회사 원본형 raw

- `data/raw/crm/sample_daily_crm_activity_2026.xlsx`
- `data/raw/sales/sample_hospital_performance.xlsx`
- `data/raw/target/sample_hospital_monthly_targets.xlsx`
- `data/raw/company/sample_fact_ship_pharmacy_raw_label.csv`

### 13.3 OPS 표준형 raw

- `data/ops_standard/ops_crm_activity.xlsx`
- `data/ops_standard/ops_sales.xlsx`
- `data/ops_standard/ops_target.xlsx`
- `data/ops_standard/ops_shipment.xlsx`
- `data/ops_standard/ops_account_master.xlsx`
- `data/ops_standard/ops_rep_master.xlsx`

### 13.4 있으면 좋은 보조 파일

- `data/raw/crm/sample_next_action_log.xlsx`
- `data/raw/company/sample_account_health_bridge.xlsx`

## 14. 실제 작업 순서

### 단계 1. 품목 후보 추출

- `sales` 품목ID/품목명 추출
- `fact_ship` 브랜드/SKU 추출

### 단계 2. 한결제약 품목 마스터 초안 생성

- 대표 브랜드군 정리
- SKU와 품목ID 연결

### 단계 3. 브랜드 매핑표 생성

- 두 파일 간 불일치 해소

### 단계 4. 병원/담당자/지점 마스터 정리

- 병원 규모, 전략 비중 포함

### 단계 5. 회사 원본형 CRM raw 생성

- 활동, 품질, 영향도, 신뢰도, next action 포함

### 단계 6. 회사 원본형 Target 생성

- 병원 × 품목 × 월 목표 생성

### 단계 7. 회사 원본형 Sales 생성

- CRM 행동 패턴과 일부 연결되게 생성

### 단계 8. 회사 원본형 Fact_ship 생성

- 유통 흐름 및 연결 불완전 사례 반영

### 단계 9. Adapter 정규화 규칙 적용

- 회사 원본형 raw를 OPS 표준형으로 변환
- 제품, 병원, 담당자, 날짜 체계 정리
- 누락과 이상치 검증 로그 생성

### 단계 10. 정합성 검증

필수 검증:

- 병원ID 정합성
- 담당자ID 정합성
- 지점ID 정합성
- `sales`와 `target`의 `월 + 병원 + 품목` 정합성
- `fact_ship`와 `sales`의 브랜드/품목 매핑률

### 단계 11. UI/템플릿 검증

아래 화면에서 테스트:

- `ops_console.py`
- `html_builder`
- `report_template.html`
- `spatial_preview_template.html`

## 15. 최종 결론

이번 raw 데이터 생성의 핵심은 단순 샘플 제작이 아니다.

핵심 우선순위는 아래와 같다.

1. CRM 계산 로직 설계
2. 한결제약 품목 마스터
3. 브랜드 매핑표
4. 회사 원본형 raw 생성
5. 어댑터 정규화
6. OPS 표준형 raw 검증

즉, 브랜드 정합만 맞추는 것이 아니라 **지저분한 회사 원본형 raw가 어댑터를 거쳐 OPS에서 바로 검증되고 결과를 낼 수 있는 운영 리허설 데이터 세트**를 만드는 것이 이번 작업의 목표다.
