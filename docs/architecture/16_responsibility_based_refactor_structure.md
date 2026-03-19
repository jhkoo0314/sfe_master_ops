# Responsibility-Based Refactor Structure

## 1. 목적

현재 구조는 기능은 동작하지만, 아래 문제가 누적되고 있다.

- `ui/console_tabs.py`에 UI + Agent 처리 + artifact 로딩 + history 저장 + fallback 로직이 섞여 있음
- `modules/sandbox/service.py`에 Sandbox 계산 결과 조립 + payload 생성 + branch asset 분할 + 템플릿 대응 로직이 섞여 있음
- `common/run_registry.py`에 run 저장 + context 생성 + artifact 저장 + Agent 지원 로직이 계속 커지고 있음

이 상태로 기능을 계속 추가하면,

- 수정 충돌이 잦아지고
- 버그 원인 추적이 어려워지고
- Agent / Sandbox / UI 책임이 계속 뒤섞인다.

따라서 다음 단계에서는 **파일 분리만이 아니라 폴더 구조까지 책임 기준으로 리팩토링**해야 한다.

---

## 2. 핵심 원칙

### 2.1 분리 기준

분리 기준은 “기능 이름”이 아니라 **책임**이다.

예:

- UI는 화면 배치만 담당
- Agent는 질문 처리 흐름만 담당
- artifact loader는 결과물 로딩만 담당
- Sandbox service는 orchestration만 담당
- Sandbox builder는 payload/asset 조립만 담당

### 2.2 Sales Data OS 원칙 유지

- 시스템 전체는 `Sales Data OS`
- `OPS`는 Validation / Orchestration Layer
- KPI 계산은 `modules/kpi/*` 단일 소스 유지
- Builder는 render-only 유지
- Sandbox/Agent는 KPI 재계산 금지

### 2.3 리팩토링 우선순위

대규모 rename이나 import 이동을 한 번에 하지 않는다.

순서:

1. 구조 문서 확정
2. 신규 폴더/파일 추가
3. 기존 파일에서 책임별 함수 이동
4. 기존 진입점은 thin wrapper로 유지
5. 동작 안정화 후 잔여 정리

---

## 3. 목표 폴더 구조

## 3.1 UI / Console / Agent

현재 문제:

- `ui/console_tabs.py` 하나에 여러 탭과 Agent 로직이 함께 있음
- `ui/ops_console.py`도 앱 진입점, 레이아웃, 탭 연결 책임이 한 파일에 모여 있음

목표:

```text
ui/
  console/
    app.py
    layout.py
    theme.py
    sidebar.py
    state.py
    tabs/
      dashboard_tab.py
      upload_tab.py
      pipeline_tab.py
      artifacts_tab.py
      agent_tab.py
    agent/
      agent_service.py
      agent_context.py
      agent_artifacts.py
      agent_history.py
      agent_mock.py
      agent_llm.py
```

책임:

- `ui/console/app.py`
  - 기존 `ops_console.py` 역할
  - 콘솔 진입점
  - 탭 라우팅

- `ui/console/layout.py`
  - 공통 화면 배치
  - 상단 레이아웃/메인 구조

- `ui/console/theme.py`
  - CSS/스타일 주입

- `ui/console/sidebar.py`
  - 회사 선택
  - 실행 옵션
  - 사이드바 입력 처리

- `ui/console/state.py`
  - Streamlit session state 초기화/관리

- `ui/console/tabs/*`
  - 화면 렌더링 전용
  - Streamlit widget 배치
  - 사용자 입력 수집

- `ui/console/agent/agent_service.py`
  - Agent 질문 처리 orchestration
  - 질문 -> artifact 로딩 -> LLM 호출 -> 응답 저장 흐름

- `ui/console/agent/agent_context.py`
  - run context 로딩
  - DB/local/fallback 문맥 처리

- `ui/console/agent/agent_artifacts.py`
  - `run_artifacts` 조회
  - 실제 payload/result asset/html 로딩
  - artifact 우선순위 정리

- `ui/console/agent/agent_history.py`
  - Agent chat history 저장/조회

- `ui/console/agent/agent_mock.py`
  - fallback answer 생성

- `ui/console/agent/agent_llm.py`
  - provider별 API 호출

---

## 3.2 Sandbox

현재 문제:

- `modules/sandbox/service.py`에 로딩/계산 결과 조립/템플릿 대응이 함께 있음

목표:

```text
modules/
  sandbox/
    service.py
    builders/
      group_payload_builder.py
      member_payload_builder.py
      product_payload_builder.py
      activity_analysis_builder.py
      asset_manifest_builder.py
    loaders/
      crm_loader.py
      sales_loader.py
      target_loader.py
    schemas/
      sandbox_payload_schema.py
      sandbox_asset_schema.py
```

책임:

- `service.py`
  - Sandbox 전체 orchestration만 담당
  - builder/loaders 호출

- `builders/*`
  - payload 조립
  - branch/member/product 구조 변환
  - branch asset manifest 생성

- `loaders/*`
  - 표준 데이터 읽기
  - source/result asset 입수

- `schemas/*`
  - payload/result asset 구조 정의

주의:

- KPI 계산은 계속 `modules/kpi/sandbox_engine.py` 기준 유지
- Sandbox builder는 계산 결과를 구조화만 해야 한다

---

## 3.3 Run Storage / Agent Runtime

현재 문제:

- `common/run_registry.py`에 run 저장과 Agent 지원 로직이 함께 커지고 있음

목표:

```text
common/
  run_storage/
    runs.py
    run_steps.py
    run_artifacts.py
    run_report_context.py
  agent_runtime/
    artifact_registry.py
    artifact_loader.py
    report_context_builder.py
```

책임:

- `run_storage/*`
  - DB 저장/조회 전용
  - `runs`
  - `run_steps`
  - `run_artifacts`
  - `run_report_context`

- `agent_runtime/*`
  - Agent가 어떤 artifact를 읽을지 결정
  - artifact를 실제로 로드
  - report context 생성/확장

즉:

- 저장 로직과
- 해석 로직을 분리해야 한다

---

## 4. 단계별 이동 계획

## Step 1. UI Console 패키지 분리

우선순위 가장 높음.

이유:

- 현재 `ui/ops_console.py`, `ui/console_tabs.py`, `ui/console_sidebar.py`, `ui/console_state.py`가 루트에 흩어져 있음
- 콘솔 관련 파일을 하나의 패키지로 먼저 묶어야 이후 Agent/Tabs 분리가 안정적임

작업:

- `ui/console/` 폴더 신설
- `ops_console.py` 역할을 `ui/console/app.py`로 이동
- `console_sidebar.py`, `console_state.py`도 `ui/console/` 하위로 이동
- 기존 진입 파일은 thin wrapper 또는 import bridge로 유지

완료 기준:

- 콘솔 관련 루트 파일이 `ui/console/` 패키지로 정리됨

---

## Step 2. UI Agent 분리

작업:

- `ui/console/agent/` 폴더 신설
- Agent 관련 함수 이동
- `ui/console/tabs/agent_tab.py`에서 얇게 호출

완료 기준:

- 콘솔 탭 파일에서 Agent 전용 로직 대부분 제거

---

## Step 3. UI Tabs 분리

작업:

- `dashboard`, `upload`, `pipeline`, `artifacts`, `agent` 탭 렌더 함수 분리

완료 기준:

- `ui/console/app.py`는 탭 라우팅만 담당

---

## Step 4. Run Storage 분리

작업:

- `common/run_registry.py`를 역할별 파일로 분리

완료 기준:

- run 저장/조회와 Agent runtime helper가 분리됨

---

## Step 5. Sandbox builders 분리

작업:

- `modules/sandbox/service.py` 내부 함수들을 builder/loaders로 이동

완료 기준:

- `service.py`는 orchestration만 남음

주의:

- 이 단계에서는 계산식 변경 금지
- payload/result asset 구조를 유지하면서 내부 책임만 분리

---

## 5. 하지 말아야 할 것

- 처음부터 import 전체 rename
- 동작 중인 경로를 한 번에 대규모 변경
- KPI 계산 로직을 Builder/Sandbox/UI로 흩뿌리는 변경
- Agent 질문 유형별 하드코딩을 본질 해결처럼 착각하는 것

---

## 6. 이번 리팩토링의 핵심 목표

이 리팩토링의 목적은 “파일 정리”가 아니다.

핵심 목적은 아래 3가지다.

1. Agent가 `run_artifacts`를 읽는 구조를 유지 가능한 형태로 만든다
2. Sandbox payload 조립 로직의 충돌을 줄인다
3. Console / Agent / Storage / Builder / Sandbox 책임을 다시 분리한다

---

## 7. 최종 판단

현재는 단순히 `service.py`, `console_tabs.py`를 쪼개는 수준으로 끝내면 안 된다.

반드시 아래처럼 가야 한다.

- Console은 `ui/console/` 패키지로
- Agent는 Console 하위 Agent 폴더로
- Sandbox 조립은 builders 폴더로
- run 저장은 run_storage 폴더로

즉, **책임 기준 폴더 구조 리팩토링**이 이번 단계의 올바른 방향이다.
