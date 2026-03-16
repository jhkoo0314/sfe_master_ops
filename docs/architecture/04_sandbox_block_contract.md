# Sandbox Block Contract (Stage 1)

작성일: 2026-03-16

## 1) 왜 블록 구조로 전환하는가

현재 Sandbox 결과는 `report_template.html` 중심으로 payload가 크게 묶여 있습니다.
이 구조는 빠르게 화면을 만들기에는 유리하지만, 아래 문제가 있습니다.

- 차트/카드 교체 시 payload 구조도 같이 바꿔야 해서 결합도가 높음
- 서비스 계산(`modules/sandbox/service.py`)이 템플릿 표현 요구를 직접 많이 반영함
- Builder/에이전트가 "분석 자산 단위"로 재사용하기 어려움

따라서 Stage 1에서는 기능 교체가 아니라, **현재 payload를 블록 단위 계약으로 명시**해 Stage 2 리팩토링 준비를 완료합니다.

## 2) 기존 구조의 문제

- 현재 핵심 데이터는 `SandboxResultAsset.dashboard_payload.template_payload` 1개 dict로 전달됨
- `branches` 상세는 용량 때문에 chunk 자산으로 분리되며(`sandbox_template_payload_assets/*.js`), manifest와 상세가 분리됨
- 템플릿(`templates/report_template.html`)은 개별 필드 단위 접근이 많아 블록 경계가 코드에 드러나지 않음
- `official_kpi_6`, `data_health`, `missing_data`, `insight_messages` 일부는 payload에 존재하지만 템플릿 소비는 제한적임

## 3) Block 설계 원칙

1. 차트/카드/표는 "필드"가 아니라 "블록"을 소비한다.
2. 블록은 `block_id` + `source_path` + `required_fields`를 최소 계약으로 가진다.
3. KPI 공식은 `modules/kpi/sandbox_engine.py` 결과만 공식값으로 사용한다.
4. Builder는 render-only 원칙을 유지하고, 필요한 경우 `builder_transform`만 수행한다.
5. chunk 모드에서는 manifest 블록과 상세 블록을 분리해 계약한다.
6. 블록 미존재 시 슬롯 fallback 규칙으로 처리하고 계산 로직을 템플릿에 추가하지 않는다.

## 4) Block Catalog

| block_id | 목적 | 소비 주체(UI) | source_path | 필수 필드 | 선택 필드 | 현재 존재 | 계산 주체 | 에이전트 재사용 |
|---|---|---|---|---|---|---|---|---|
| `official_kpi_6` | 공식 KPI 6개 제공 | 상단 KPI 카드(향후), 요약 리포트 | `dashboard_payload.template_payload.official_kpi_6` | `monthly_sales`, `monthly_target`, `monthly_attainment_rate`, `quarterly_sales`, `quarterly_target`, `annual_attainment_rate`, `metric_version` | `reference_month`, `reference_quarter`, `reference_year` | Y | official_engine | Y |
| `total_summary` | 전사 요약 KPI 평균/달성률 | 그룹뷰 KPI/레이더/요약 | `dashboard_payload.template_payload.total` | `achieve`, `avg`, `monthly_actual`, `monthly_target`, `analysis` | - | Y | sandbox_service | Y |
| `total_trend` | 전사 시계열(월/분기/연) | 그룹뷰 실적 추세 | `dashboard_payload.template_payload.total.monthly_actual`, `...monthly_target` | `monthly_actual`, `monthly_target` | - | Y | sandbox_service | Y |
| `branch_summary` | 지점 단위 요약 | 지점 선택 후 그룹뷰 | `dashboard_payload.template_payload.branches.{branch}` 또는 `sandbox_template_payload_assets/*.js` | `achieve`, `avg`, `monthly_actual`, `monthly_target`, `analysis`, `members` | `prod_analysis` | Y (chunk 의존) | sandbox_service + builder_transform | Y |
| `branch_member_summary` | 지점 내 담당자 목록/기본 상태 | 담당자 셀렉터, 개인뷰 진입 | `...branches.{branch}.members[]` | `성명`, `rep_id`, `지점순위`, `monthly_actual`, `monthly_target` | `coach_scenario`, `coach_action` | Y (chunk 의존) | sandbox_service + builder_transform | Y |
| `member_performance` | 개인 KPI/효율/지니 | 개인뷰 KPI 카드/레이더 | `...members[]` | `HIR`, `RTR`, `BCR`, `PHR`, `PI`, `FGR`, `efficiency`, `sustainability`, `gini` | `shap` | Y (chunk 의존) | official_engine + sandbox_service | Y |
| `product_analysis` | 품목별 성과/성장/비중 | 품목 셀렉터, PM scatter | `template_payload.total_prod_analysis`, `...members[].prod_matrix`, `...members[].prod_analysis` | `products`, `total_prod_analysis` | `prod_matrix`, `prod_analysis` | Y | sandbox_service | Y |
| `activity_analysis` | 행동 가중치/상관 분석 | Tornado, Matrix, 활동 breakdown | `...total.analysis`, `...branches.{branch}.analysis`, `...members[].activity_counts` | `analysis.importance`, `analysis.correlation`, `analysis.adj_correlation` | `activity_counts`, `shap`, `ccf` | Y (chunk 의존) | sandbox_service | Y |
| `data_health` | 데이터 정합/매핑 상태 | 품질 패널(현재 일부 미연결) | `template_payload.data_health` | `integrity_score`, `mapped_fields`, `operational_notes` | `missing_fields` | Y | sandbox_service | Y |
| `missing_data` | 결측/미매핑 항목 | 품질 경고 패널(현재 미연결) | `template_payload.missing_data` | list 객체 | - | Y | sandbox_service | Y |
| `executive_insight` | 운영 인사이트 텍스트 | 요약 문구/노트 영역(향후) | `dashboard_payload.insight_messages` | list[str] | - | Y | sandbox_service | Y |
| `template_runtime_manifest` | chunk 로딩 메타 | branch lazy-load 런타임 | `template_payload.data_mode`, `asset_base`, `branch_asset_manifest`, `branch_index`, `branch_asset_counts` | `data_mode`, `branch_asset_manifest`, `branch_index` | `asset_base`, `branch_asset_counts`, `branches` | Y | builder_transform | Y |

## 5) 블록별 데이터 계약 상세

### A. `official_kpi_6`
- 계약 목적: 상단 KPI의 공식값을 고정 계산 소스에서 공급
- producer: `modules/kpi/sandbox_engine.py::compute_sandbox_official_kpi_6`
- 검증: `validate_official_kpi_6_payload`
- 주의: 현재 템플릿은 이 블록을 직접 렌더하지 않고 `total.monthly_*` 기반 계산을 주로 사용

### B. `total_summary` / `total_trend`
- producer: `modules/sandbox/service.py::_build_report_template_payload`
- 핵심 필드:
  - `total.achieve`
  - `total.avg.{HIR,RTR,BCR,PHR,PI,FGR}`
  - `total.monthly_actual[12]`, `total.monthly_target[12]`
  - `total.analysis.{importance,correlation,adj_correlation,ccf}`
- 현재 템플릿 소비:
  - group view KPI/레이더/토네이도/매트릭스

### C. `branch_summary` / `branch_member_summary`
- producer: `service.py::_build_report_template_payload`
- transform: `modules/sandbox/builder_payload.py::build_chunked_sandbox_payload`
- chunk 모드 계약:
  - manifest에는 `branches={}`일 수 있음
  - 실제 지점 데이터는 `sandbox_template_payload_assets/*.js`에서 `window.__SANDBOX_BRANCH_DATA__[branch]`로 로드
- 필수 필드:
  - branch: `members`, `avg`, `monthly_actual`, `monthly_target`, `analysis`, `achieve`
  - member: `성명`, `rep_id`, `지점순위`, KPI 6개, `monthly_actual`, `monthly_target`

### D. `member_performance`
- producer 혼합:
  - KPI 6개 평균: `compute_sandbox_rep_kpis` (official_engine)
  - 효율/지속성/지니/코칭: sandbox_service 파생
- 템플릿 소비:
  - 개인 KPI 카드
  - 개인 레이더/활동분석
  - 코칭 카드/지니 카드

### E. `product_analysis`
- producer: sandbox_service
- 필수 필드:
  - 전사: `products[]`, `total_prod_analysis[product].{monthly_actual,monthly_target,analysis,achieve}`
  - 개인: `prod_matrix[]`, `prod_analysis{}`
- 템플릿 소비:
  - 품목 선택 필터
  - PM scatter
  - 품목별 시계열 스코프

### F. `activity_analysis`
- producer: sandbox_service
- 필수 필드:
  - `analysis.importance`
  - `analysis.correlation`
  - `analysis.adj_correlation`
- 템플릿 소비:
  - group tornado
  - correlation matrix(구/보정)
  - 개인 activity breakdown

### G. `data_health` / `missing_data`
- producer: sandbox_service
- 현재 상태:
  - payload에는 존재
  - 템플릿 DOM은 있으나 실제 렌더 로직 연결은 제한적
- Stage 2 권장:
  - `data_health_slot`에서 전용 렌더 함수로 연결

### H. `executive_insight`
- source: `dashboard_payload.insight_messages`
- producer: `_inject_data_to_template`에서 생성
- 현재 상태: report_template에서 실소비 없음
- Stage 2 권장: insight 슬롯에 텍스트 블록으로 렌더

### I. `template_runtime_manifest`
- producer: builder_transform
  - `validate_sandbox_with_ops.py` 또는 `prepare_sandbox_chunk_assets`
- 필수 필드:
  - `data_mode`, `branch_asset_manifest`, `branch_index`
- 역할:
  - branch lazy-load를 위한 런타임 계약

## 6) 계산 주체 책임 구분

- official_engine
  - `modules/kpi/sandbox_engine.py`
  - 범위: 공식 KPI 6, 담당자 KPI 평균
- sandbox_service
  - `modules/sandbox/service.py`
  - 범위: branch/member/product/activity/data_health 등 분석 블록 조립
- builder_transform
  - `modules/sandbox/builder_payload.py`
  - `modules/builder/service.py::prepare_sandbox_chunk_assets`
  - 범위: chunk manifest/asset 분리, 경로 주입
- unsupported
  - 현 구조에 블록이 없거나 source_path 미정인 경우

## 7) "차트는 필드가 아니라 블록을 소비" 원칙

예시:
- `chart_g_radar`는 `total_summary` 블록을 소비한다.
- `chart_g_tornado`/`table_old`/`table_new`는 `activity_analysis` 블록을 소비한다.
- `chart_r_pm`은 `product_analysis` 블록을 소비한다.

구현 규칙:
1. 템플릿 JS는 `db.xxx` 개별 필드 접근 대신 블록 리졸버를 경유한다.
2. 블록 리졸버는 `block_id -> source_path` 매핑(registry)만 참조한다.
3. 필드 계산/보정은 service 또는 engine에서 끝내고 템플릿에서 재계산하지 않는다.

## 8) 미지원 블록 처리 원칙

- 상태 분류:
  - `supported`: source_path/필수 필드 충족
  - `derived`: 원본 블록에서 파생 가능하지만 직결 경로 없음
  - `unsupported`: 현재 payload에 없음
- fallback:
  - 슬롯 렌더 실패 시 "블록 없음" 안내 카드 표시
  - 전체 렌더 실패로 전파하지 않음
  - WARN 로그만 남기고 다른 슬롯은 계속 렌더

## 9) Builder/에이전트 연계 방향

Stage 2에서 구현할 최소 방향:

1. `block_registry.py` 기반 block resolver 추가
2. 템플릿 렌더 함수 입력을 `payload` 대신 `resolved_blocks`로 전환
3. chunk 로딩 이후 `branch_summary`/`member_performance` 블록 재해석
4. RADAR/다른 보고서도 동일 패턴(블록 + 슬롯)로 확장

---

## 즉시 지원 / 추가 리팩토링 / 미지원 분류

- 즉시 지원 가능
  - `official_kpi_6`, `total_summary`, `total_trend`, `branch_summary`, `branch_member_summary`, `member_performance`, `product_analysis`, `activity_analysis`, `data_health`, `missing_data`, `template_runtime_manifest`
- 추가 리팩토링 필요
  - `executive_insight` (payload 존재, 템플릿 슬롯 미연결)
- 미지원
  - 없음 (본 문서 범위의 후보 블록 기준)
