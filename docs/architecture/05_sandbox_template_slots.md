# Sandbox Template Slots (Stage 1)

작성일: 2026-03-16

## 목적

이 문서는 Sandbox HTML(`templates/report_template.html`)을
"자유 배치"가 아닌 **제한된 슬롯 기반 조립 구조**로 재정의하기 위한 설계 문서다.

중요:
- 현재 HTML/Builder를 전면 교체하지 않는다.
- Stage 2에서 적용할 슬롯 계약만 먼저 고정한다.

## 슬롯 설계 원칙

1. 슬롯은 화면의 고정 위치 단위다.
2. 슬롯은 허용된 block_id만 렌더할 수 있다.
3. 슬롯은 우선순위 순서대로 블록을 시도한다.
4. 블록이 없으면 슬롯 fallback 정책을 적용한다.
5. 슬롯은 계산하지 않고 전달받은 블록만 표현한다.

## 슬롯 카탈로그

| slot_id | 화면 위치/의도 | 허용 블록 | 우선순위 | fallback |
|---|---|---|---|---|
| `header_kpi_slot` | 상단 6 KPI 카드 | `official_kpi_6`, `total_summary`, `data_health` | 1) official_kpi_6, 2) total_summary, 3) data_health | 카드 값 `N/A`, 품질 상태만 표시 |
| `main_trend_slot` | Layer 01 달성률/추세 | `total_trend`, `total_summary`, `branch_summary` | 1) scoped trend, 2) total trend | 빈 차트 + "데이터 없음" |
| `capability_radar_slot` | 그룹/개인 레이더 | `total_summary`, `member_performance`, `branch_summary` | 1) member, 2) branch, 3) total | 6축 0값 레이더 |
| `branch_compare_slot` | 그룹 인과/상관 분석 | `activity_analysis`, `branch_summary` | 1) scoped activity_analysis | 표/차트 숨김 + 안내문 |
| `member_rank_slot` | 개인 선택/순위/코칭 | `branch_member_summary`, `member_performance` | 1) branch_member_summary, 2) member_performance | 담당자 선택 비활성 |
| `product_analysis_slot` | 품목 필터/PM 매트릭스 | `product_analysis`, `branch_summary`, `member_performance` | 1) product_analysis | 필터에 "ALL"만 노출 |
| `data_health_slot` | 정합성/결측 패널 | `data_health`, `missing_data` | 1) data_health, 2) missing_data | 패널 접힘 유지 |
| `insight_slot` | 전략 코멘트/요약 | `executive_insight`, `member_performance` | 1) executive_insight, 2) coach fields | 기본 안내 텍스트 |
| `runtime_manifest_slot` | chunk 로딩 제어 | `template_runtime_manifest` | 1) runtime_manifest | non-chunk 모드로 강등 |

## 슬롯별 최소 입력 계약

### 1) `header_kpi_slot`
- 최소 입력:
  - `official_kpi_6.monthly_attainment_rate`
  - `official_kpi_6.annual_attainment_rate`
  - 또는 `total_summary.achieve`, `total_summary.avg.PI`, `total_summary.avg.FGR`
- 비고:
  - 현재 템플릿은 period 기반 재계산 사용이 많으므로 Stage 2에서 블록 우선 순위로 치환

### 2) `main_trend_slot`
- 최소 입력:
  - `*.monthly_actual[12]`
  - `*.monthly_target[12]`
- 스코프:
  - TOTAL / branch / rep + product 필터

### 3) `capability_radar_slot`
- 최소 입력:
  - `HIR`, `RTR`, `BCR`, `PHR`, `PI`, `FGR`
- 스코프:
  - 개인 선택 시 `member_performance`
  - 미선택 시 `total_summary` 또는 `branch_summary`

### 4) `branch_compare_slot`
- 최소 입력:
  - `analysis.importance`
  - `analysis.correlation`
  - `analysis.adj_correlation`

### 5) `member_rank_slot`
- 최소 입력:
  - `branch.members[].성명`
  - `branch.members[].지점순위`
  - `coach_scenario`, `coach_action`

### 6) `product_analysis_slot`
- 최소 입력:
  - `products[]`
  - `total_prod_analysis`
  - 개인 스코프 시 `prod_matrix` 또는 `prod_analysis`

### 7) `data_health_slot`
- 최소 입력:
  - `data_health.integrity_score`
  - `data_health.mapped_fields`
- 선택 입력:
  - `missing_data[]`
  - `data_health.operational_notes[]`

### 8) `insight_slot`
- 최소 입력:
  - `dashboard_payload.insight_messages[]`
- 대체 입력:
  - `member.coach_scenario`, `member.coach_action`

### 9) `runtime_manifest_slot`
- 최소 입력:
  - `data_mode`
  - `branch_asset_manifest`
  - `branch_index`
- 동작:
  - 지점 변경 시 lazy-load
  - 실패 시 TOTAL로 자동 fallback

## 슬롯 렌더 우선순위 규칙

1. 전역 공통 슬롯: `runtime_manifest_slot` -> `header_kpi_slot` -> `data_health_slot`
2. 그룹뷰: `main_trend_slot` -> `capability_radar_slot` -> `branch_compare_slot`
3. 개인뷰: `member_rank_slot` -> `capability_radar_slot` -> `product_analysis_slot` -> `insight_slot`

## 블록 부재 시 fallback 정책

- `supported` 블록 없음:
  - 슬롯을 숨기지 말고 "데이터 없음" placeholder 표시
- `chunk` 로딩 실패:
  - 브랜치 선택을 TOTAL로 되돌리고 경고 상태 출력
- 필수 필드 누락:
  - 해당 슬롯만 skip, 페이지 전체 렌더는 계속

## Block 조립형 HTML 최소 규칙 (Stage 2 구현 기준)

1. 템플릿 렌더 함수는 `resolve_block(slot_id)`만 호출한다.
2. 블록 해석은 `modules/sandbox/block_registry.py`를 단일 기준으로 사용한다.
3. 템플릿 JS에서 KPI/상관 계산식을 새로 만들지 않는다.
4. chunk 모드와 non-chunk 모드를 동일한 block_id 인터페이스로 숨긴다.
5. 신규 차트 추가 시 "필드 경로"가 아니라 "slot 허용 block"만 확장한다.
