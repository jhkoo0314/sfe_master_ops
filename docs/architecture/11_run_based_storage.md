# Run-Based Storage Spec

작성일: 2026-03-16

이 문서는 Sales Data OS의 저장 구조를 `module 중심`에서 `run 중심`으로 전환하기 위한 구현 명세다.

## 1. 목적
- 기존 구조는 `data/ops_validation/{company_key}/{module}/...`에 모듈별 결과가 저장되어, 한 번의 실행 단위를 추적하기 어렵다.
- Agent Layer를 Builder 이후에 붙이기 위해서는, 한 실행의 최종 결과를 한 묶음으로 읽을 `Final Report Package`와 `report_context`가 필요하다.
- 따라서 실행 단위(run)를 최상위 부모로 두고, 산출물/로그/컨텍스트를 run 하위로 묶는다.

## 2. 저장 원칙
- 하나의 실행(run)이 최상위 부모다.
- 모든 산출물은 가능하면 run 하위에 귀속된다.
- Builder는 사람용 출력물(HTML/PDF)과 Agent용 컨텍스트(JSON)를 함께 생성한다.
- DB와 파일 저장소 역할을 분리한다.
- 실제 파일(html/pdf/json)은 파일시스템 또는 storage에 둔다.
- 메타/인덱스/조회는 DB(Supabase)에 둔다.

## 3. 표준 run 폴더 구조
현재 코드의 기준 루트 `data/ops_validation/{company_key}/`를 유지하고, run 하위를 추가한다.

```text
data/ops_validation/{company_key}/
  runs/
    {run_id}/
      run_meta.json
      pipeline_summary.json
      report_context.full.json
      report_context.prompt.json
      artifacts.index.json
      artifacts/
        intermediate/
          crm_result_asset.json
          prescription_result_asset.json
          sandbox_result_asset.json
          territory_result_asset.json
          radar_result_asset.json
          *_validation_summary.json
        final/
          crm_analysis_preview.html
          sandbox_report_preview.html
          territory_map_preview.html
          prescription_flow_preview.html
          radar_report_preview.html
          total_valid_preview.html
          *_input_standard.json
          *_payload_standard.json
          *_result_asset.json
        evidence/
          evidence_index.json
          source_versions.json
      logs/
        run_steps.json
        runner_events.jsonl
      chat/
        agent_chat_history.jsonl
```

## 4. 파일명 규칙
필수 파일:
- `run_meta.json`
- `pipeline_summary.json`
- `report_context.full.json`
- `report_context.prompt.json`
- `artifacts.index.json`
- `logs/run_steps.json`
- `artifacts/final/total_valid_preview.html` (통합 실행 또는 builder 실행 시)

모드별 선택 파일:
- `artifacts/final/crm_analysis_preview.html`
- `artifacts/final/sandbox_report_preview.html`
- `artifacts/final/territory_map_preview.html`
- `artifacts/final/prescription_flow_preview.html`
- `artifacts/final/radar_report_preview.html`

권장 보조 파일:
- `artifacts/evidence/evidence_index.json`
- `artifacts/evidence/source_versions.json`
- `chat/agent_chat_history.jsonl`

## 5. run_meta.json 스키마

```json
{
  "run_id": "a8d1b8b8-5c22-4f1c-9b6d-6f3c42f37a11",
  "company_key": "daon_pharma",
  "mode": "integrated_full",
  "started_at": "2026-03-16T13:10:12+09:00",
  "finished_at": "2026-03-16T13:12:08+09:00",
  "status": "success",
  "triggered_by": "streamlit_ui",
  "input_summary": {
    "uploaded_files": ["crm_activity_raw.xlsx", "sales_raw.xlsx"],
    "used_existing_source": true
  },
  "validation_status": "PASS",
  "confidence_grade": "A",
  "final_outputs": {
    "html": [
      "artifacts/final/crm_analysis_preview.html",
      "artifacts/final/sandbox_report_preview.html",
      "artifacts/final/total_valid_preview.html"
    ],
    "contexts": [
      "pipeline_summary.json",
      "report_context.full.json",
      "report_context.prompt.json",
      "artifacts.index.json"
    ]
  }
}
```

## 6. report_context 분리 규칙

### 6.1 `report_context.full.json`
목적:
- 근거 추적(evidence trace)과 감사용 원본 컨텍스트

포함 필드(권장):
- `run_id`, `company_key`, `mode`, `generated_at`
- `period`, `comparison_period`, `org_scope`
- `validation_summary`, `confidence_grade`
- `executive_summary`, `key_findings`, `kpi_summary`, `radar_summary`, `territory_summary`
- `priority_issues`
- `evidence_index` (result asset/summary/html 경로 + hash)
- `linked_artifacts`
- `source_versions`

### 6.2 `report_context.prompt.json`
목적:
- LLM 입력 최적화(짧고 핵심만)

포함 필드(권장):
- `run_id`, `mode`, `generated_at`
- `executive_summary`
- `top_findings` (최대 5)
- `kpi_changes` (핵심 KPI만)
- `priority_issues` (최대 5)
- `answer_scope`
- `forbidden_actions`

규칙:
- `prompt`는 `full`의 부분집합 + 모델 제약 메타다.
- 수치 원본은 `full`만 신뢰 원본으로 본다.

## 7. Builder 책임 정의
Builder는 KPI 재계산을 하지 않는다.  
Builder는 render/composition 레이어로서 다음을 생성한다.

필수 생성물:
- 최종 보고 출력물: `*.html` (향후 `*.pdf`)
- `pipeline_summary.json`
- `report_context.full.json`
- `report_context.prompt.json`
- `artifacts.index.json`
- `evidence_index` 및 `linked_artifacts`

정리:
- Builder는 계산 엔진이 아니다.
- Builder는 Final Report Package 생성자다.

## 8. 저장 흐름
1. 실행 시작 시 `run_id` 생성
2. `runs/{run_id}/run_meta.json` 초안 저장 (`status=running`)
3. step 실행 후 `artifacts/intermediate`와 `logs/run_steps.json` 갱신
4. validation 결과 반영 (`validation_status`, `quality_score`)
5. builder 실행 후 `artifacts/final` 생성
6. builder 종료 시 `pipeline_summary.json`, `report_context.full.json`, `report_context.prompt.json`, `artifacts.index.json` 생성
7. `run_meta.json` 완료 상태로 갱신 (`status=success|failed`)
8. DB 테이블(`runs`, `run_steps`, `run_artifacts`, `run_report_context`) 동기화

## 9. 점진 마이그레이션 가이드
- 1단계: 기존 모듈별 저장 유지 + run 폴더 병행 생성
- 2단계: Streamlit/Agent 조회는 run 폴더 우선, 기존 경로 fallback
- 3단계: DB 저장 로직 연결 후 run 단위 조회 기본화
- 4단계: 안정화 후 기존 `module 단독 조회`는 read-only로 축소

## 10. 현재 코드와 연결 포인트
- 실행 run_id 생성: `modules/validation/workflow/execution_service.py`
- 실행 모드/step 순서: `modules/validation/workflow/execution_registry.py`
- Builder 출력 생성: `scripts/validate_builder_with_ops.py`
- Builder 결과 스키마: `modules/builder/schemas.py`
- 현재 회사별 저장 루트: `data/ops_validation/{company_key}/`
- 현재 Agent는 최신 run bundle(`pipeline_summary.json`, `report_context.*`, `artifacts.index.json`)을 우선 읽고, 없을 때만 legacy 요약으로 fallback 한다.
