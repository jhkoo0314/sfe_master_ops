# Sales Data OS 구조 재정렬 및 Agent/Run 중심 설계 문서

작성일: 2026-03-16

이 문서는 **현재 저장소를 실제로 확인한 결과**와 **그 위에 올리는 설계 제안**을 명확히 구분해 기록합니다.  
비개발자 기준으로 쉽게 이해할 수 있게 설명합니다.

---

## 1. 저장소 조사 결과 요약 (확인된 사실)

### 1-1. 핵심 폴더/파일 구조
- 루트 핵심 폴더: `adapters`, `modules`, `ops_core(compat)`, `result_assets`, `scripts`, `ui`, `templates`, `data`, `docs`, `migrations`
- Streamlit 콘솔 진입점: `ui/ops_console.py`
- 실행 모드/파이프라인: `modules/validation/workflow/execution_registry.py`, `modules/validation/workflow/execution_service.py`
- Builder 실행/출력: `scripts/validate_builder_with_ops.py`, `modules/builder/service.py`, `modules/builder/schemas.py`
- Result Asset 스키마: `result_assets/*_result_asset.py`
- KPI 단일 계산: `modules/kpi/*_engine.py`
- OPS 평가 로직: `modules/validation/api/*_router.py`
- Supabase 스키마: `migrations/001_initial_schema.sql`

### 1-2. 실행/결과 저장 구조
- 실행 로그는 파일 저장만 존재: `data/ops_validation/{company_key}/pipeline/console_run_history.jsonl`
- Result Asset은 모듈별 폴더에 `*_result_asset.json`로 저장됨
- Builder 결과는 `*_preview.html`과 `*_result_asset.json` 생성

### 1-3. Supabase 흔적
- 설정만 존재: `common/config.py` (URL/Key)
- 실제 Supabase 저장 로직은 코드에서 확인되지 않음
- 스키마는 OPS 시절 기준 테이블 3개만 있음
  - `ops_run_log`, `ops_asset_meta`, `ops_connection_log`

---

## 2. 현재 구조 문제 진단 (사실 기반 해석)

### 2-1. 현재 구조 상태
- **부분적 Sales Data OS 구조**에 가까움
  - Adapter → Core Engine(KPI) → OPS Validation → Builder 흐름은 존재
- **run 중심 구조는 미흡**
  - 실행마다 run_id가 생성되지만, 산출물이 run 단위로 묶이지 않음

### 2-2. 문제점
- run 부모 개념 부재
  - run_id는 생성되지만, 저장 구조가 module 중심
- final report context 부재
  - Agent가 읽을 요약 컨텍스트 없음
- Builder 출력과 evidence 연결 약함
  - 보고서는 있지만, 근거 요약/연결 메타 부족
- Supabase 스키마가 OPS 단일 로그 중심
  - run 중심 구조와 맞지 않음

---

## 3. 목표 아키텍처 설계 (제안)

### 3-1. 최종 흐름
```
Data Layer -> Adapter Layer -> Core Engine -> Result Assets -> OPS Validation -> Builder/Composition -> Final Report Package -> Agent
```

### 3-2. 레이어 역할
- Data Layer: 원천 데이터 보관
- Adapter Layer: 표준 구조로 정렬
- Core Engine: KPI 단일 계산
- Result Assets: 모듈별 표준 결과
- OPS Validation: 품질 검증/연결 판단
- Builder/Composition: 승인된 payload를 HTML/PDF로 표현
- Final Report Package: Builder 결과 + 요약 컨텍스트 묶음
- Agent Layer: 최종 결과 해석/질의응답

### 3-3. Agent 위치와 책임
- Agent는 **Builder 이후**에 붙어야 함
- 이유
  - 실행 모드가 분석 범위를 이미 결정함
  - 사용자는 “완성된 보고서” 기준으로 질문
  - Agent는 분석 범위를 결정하지 않고 결과를 해석
- 금지
  - KPI 재계산
  - 원본 데이터 재조인

---

## 4. Supabase 스키마 재설계안 (제안)

### 4-1. 새 테이블 구조
- `runs`: 실행의 최상위 단위
- `run_steps`: 단계별 결과
- `run_artifacts`: 산출물 메타
- `run_report_context`: Agent 입력용 요약 컨텍스트
- `agent_chat_logs` (선택)

### 4-2. 기존 OPS 테이블 매핑
- `ops_run_log` → `runs`
- `ops_asset_meta` → `run_artifacts`
- `ops_connection_log` → `run_steps` 내부로 흡수

### 4-3. 전환 전략
- 점진 이전 권장
  - 신규 run 중심 테이블 추가
  - 기존 ops_* 유지하되 기록 중단

---

## 5. Final Report Package / report_context 설계 (제안)

### 5-1. 핵심 원칙
- Agent는 Builder 이후 패키지를 기본 입력으로 사용
- HTML/PDF만이 아니라 **구조화 JSON 컨텍스트** 필요
- 필요 시 하위 evidence까지 추적 가능해야 함

### 5-2. 컨텍스트 예시
```json
{
  "run_id": "...",
  "company_key": "...",
  "mode": "crm_to_sandbox",
  "generated_at": "...",
  "period": "2025 Q3",
  "comparison_period": "2025 Q2",
  "org_scope": {"region": "...", "team": "...", "rep": "..."},
  "validation_summary": {"overall_status": "PASS", "scores": {...}},
  "confidence_grade": "A",
  "executive_summary": "...",
  "key_findings": ["..."],
  "kpi_summary": {"hir": 0.82, "rtr": 0.71},
  "radar_summary": {"signals": [...], "priorities": [...]},
  "territory_summary": {"coverage": "...", "gaps": [...]},
  "priority_issues": [...],
  "evidence_index": [
    {"type": "crm_result_asset", "path": "...", "hash": "..."}
  ],
  "linked_artifacts": [
    {"type": "html", "path": ".../sandbox_report_preview.html"}
  ],
  "prompt_context": {
    "allowed_scope": "final_report_package_only",
    "forbidden": ["recalculate_kpi", "raw_rejoin"]
  }
}
```

### 5-3. 저장 방식
- DB: `run_report_context.context_json`
- 파일: `data/ops_validation/{company_key}/final_report/{run_id}/report_context.json`

---

## 6. Streamlit Agent 탭 MVP 설계 (제안)

### 6-1. 붙일 위치
- `ui/ops_console.py` 탭에 Agent 추가
- `ui/console_tabs.py`에 `render_agent_tab()` 추가

### 6-2. 필요한 상태값
- `st.session_state.selected_run_id`
- `st.session_state.report_context`
- `st.session_state.agent_history`

### 6-3. 초기 허용/금지
- 허용: 보고서 요약, KPI 변화 설명, Radar 신호 설명
- 금지: KPI 재계산, 원본 데이터 재조인, 보고서 범위 밖 추정

---

## 7. 실행 계획 (제안)

### Phase 1. 조사/정리
- 목표: report_context 스키마 문서화
- DoD: report_context 문서 초안 완성

### Phase 2. 저장 구조 리팩토링
- 목표: run 중심 폴더 구조 도입
- DoD: report_context 파일 생성 확인

### Phase 3. Supabase 연결
- 목표: run 기반 테이블 저장
- DoD: 실행 시 DB 기록 생성

### Phase 4. Streamlit Agent 탭 MVP
- 목표: 보고서 기반 Q/A
- DoD: 질문 1개 입력 → report_context 기반 응답

### Phase 5. 안정화
- 목표: 근거 추적/품질 통제
- DoD: 응답에 evidence 링크 포함

---

## 8. 구현 우선순위 Top 10 (제안)
1. report_context 스키마 정의
2. Builder 종료 시 report_context 생성
3. final_report 폴더 구조 도입
4. runs 테이블 추가
5. run_steps 저장
6. run_artifacts 저장
7. Agent 탭 추가
8. report_context 로딩
9. agent_chat_logs 저장
10. LLM 연동

---

## 9. 문서/파일 변경 제안

### 새 문서
- `docs/architecture/final_report_package.md`
- `docs/architecture/10_agent_tab_mvp.md`
- `docs/architecture/11_run_based_storage.md`

### 수정 문서
- `STRUCTURE.md`
- `RUNBOOK.md`

### 코드 수정 대상
- `scripts/validate_builder_with_ops.py`
- `modules/builder/service.py`
- `modules/validation/workflow/execution_service.py`
- `ui/ops_console.py`
- `ui/console_tabs.py`

---

## 즉시 구현 가능한 최소 단위
- Builder 완료 시 report_context 파일 생성
- Agent 탭에서 report_context 읽기

## 보류 가능 항목
- Supabase 실제 연동
- LLM 실제 호출

---

이 문서는 **Sales Data OS** 기준으로 OPS를 Validation/Orchestration Layer로만 해석합니다.
