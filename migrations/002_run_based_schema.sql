-- 002_run_based_schema.sql
-- Sales Data OS run-based schema v2
-- 작성일: 2026-03-16
-- 기준: run 중심 저장 / Builder 이후 Agent / company_key 유지

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =========================================================
-- 0) 공통 updated_at 트리거 함수
-- =========================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =========================================================
-- 1) runs
-- =========================================================
-- 하나의 실행(run)을 대표하는 최상위 메타 테이블
-- 모든 step / artifact / report_context / agent_chat_log의 부모

CREATE TABLE IF NOT EXISTS runs (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_key               TEXT NOT NULL UNIQUE,
    company_key           TEXT NOT NULL,

    mode                  TEXT NOT NULL,
    run_status            TEXT NOT NULL DEFAULT 'running'
                          CHECK (run_status IN ('running','success','failed','partial','cancelled')),

    triggered_by          TEXT NOT NULL DEFAULT 'system'
                          CHECK (triggered_by IN ('streamlit_ui','api','scheduler','test','system')),

    input_summary         JSONB NOT NULL DEFAULT '{}'::jsonb,

    period_label          TEXT,
    period_start          DATE,
    period_end            DATE,
    comparison_label      TEXT,
    comparison_start      DATE,
    comparison_end        DATE,

    validation_status     TEXT
                          CHECK (validation_status IN ('pass','warn','fail')),

    confidence_grade      TEXT
                          CHECK (confidence_grade IN ('verified','assisted','self_only')),

    final_report_path     TEXT,
    report_context_path   TEXT,

    started_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at           TIMESTAMPTZ,
    error_message         TEXT,

    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE runs IS '실행(run) 최상위 메타. 모든 step/artifact/context/chat log의 부모.';
COMMENT ON COLUMN runs.run_key IS '외부/내부 표시용 실행 키. 예: run_20260316_221012_daon_crm_sandbox';
COMMENT ON COLUMN runs.company_key IS '데이터/출력/스토리지 경로를 구분하기 위한 조직/회사 식별 키.';
COMMENT ON COLUMN runs.mode IS '실행 모드. 예: crm_sandbox, crm_pdf, prescription, territory, integrated_full';
COMMENT ON COLUMN runs.run_status IS '실행 상태. running/success/failed/partial/cancelled';
COMMENT ON COLUMN runs.input_summary IS '입력 파일명, 건수, 업로드 요약 등 실행 입력 메타';
COMMENT ON COLUMN runs.validation_status IS '최종 검증 상태. pass/warn/fail';
COMMENT ON COLUMN runs.confidence_grade IS '신뢰도 등급. verified/assisted/self_only';
COMMENT ON COLUMN runs.final_report_path IS '최종 보고서 대표 경로(html/pdf 등)';
COMMENT ON COLUMN runs.report_context_path IS '최종 report_context 파일 경로';

CREATE INDEX IF NOT EXISTS idx_runs_company_started
    ON runs (company_key, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_runs_company_mode_started
    ON runs (company_key, mode, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_runs_status_started
    ON runs (run_status, started_at DESC);

DROP TRIGGER IF EXISTS trg_runs_updated_at ON runs;
CREATE TRIGGER trg_runs_updated_at
BEFORE UPDATE ON runs
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- =========================================================
-- 2) run_steps
-- =========================================================
-- 실행 과정의 단계별 로그
-- 예: adapter, crm_engine, kpi_engine, radar_engine, validation_gate, builder

CREATE TABLE IF NOT EXISTS run_steps (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id                UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,

    step_name             TEXT NOT NULL,
    step_order            INTEGER NOT NULL,

    step_status           TEXT NOT NULL
                          CHECK (step_status IN ('running','success','failed','partial','skipped')),

    quality_status        TEXT
                          CHECK (quality_status IN ('pass','warn','fail')),

    input_summary         JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_summary        JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message         TEXT,

    started_at            TIMESTAMPTZ,
    finished_at           TIMESTAMPTZ,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE run_steps IS '실행 단계별 로그. validation, builder 단계 포함.';
COMMENT ON COLUMN run_steps.step_name IS '예: adapter, crm_engine, sandbox_engine, radar_engine, validation_gate, builder';
COMMENT ON COLUMN run_steps.step_order IS 'run 내부 단계 순서. 1부터 순차 증가.';
COMMENT ON COLUMN run_steps.step_status IS '실행 상태. running/success/failed/partial/skipped';
COMMENT ON COLUMN run_steps.quality_status IS '단계 산출 품질 상태. pass/warn/fail';

CREATE UNIQUE INDEX IF NOT EXISTS uq_run_steps_run_order
    ON run_steps (run_id, step_order);

CREATE INDEX IF NOT EXISTS idx_run_steps_run_created
    ON run_steps (run_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_run_steps_status
    ON run_steps (step_status);

-- =========================================================
-- 3) run_artifacts
-- =========================================================
-- 실행이 만든 파일/출력물/근거 메타
-- 실제 파일은 파일시스템 또는 스토리지에 저장하고, 여기에는 메타만 저장

CREATE TABLE IF NOT EXISTS run_artifacts (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id                UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    step_id               UUID REFERENCES run_steps(id) ON DELETE SET NULL,

    artifact_type         TEXT NOT NULL,
    artifact_role         TEXT NOT NULL,
    artifact_name         TEXT NOT NULL,

    artifact_class        TEXT NOT NULL
                          CHECK (artifact_class IN ('intermediate','final','evidence','agent_context')),

    storage_path          TEXT NOT NULL,
    mime_type             TEXT,
    content_hash          TEXT,

    payload               JSONB NOT NULL DEFAULT '{}'::jsonb,
    quality_status        TEXT
                          CHECK (quality_status IN ('pass','warn','fail')),
    quality_score         NUMERIC(5,2),

    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE run_artifacts IS '실행 산출물 메타. 파일 자체는 스토리지/파일시스템에 보관.';
COMMENT ON COLUMN run_artifacts.artifact_type IS '구체 산출물 타입. 예: crm_result_asset, sandbox_result_asset, report_html, report_pdf, report_context_full';
COMMENT ON COLUMN run_artifacts.artifact_role IS '산출물 역할. 예: primary_output, preview, validation_summary, evidence_bundle';
COMMENT ON COLUMN run_artifacts.artifact_name IS '표시용 산출물 이름 또는 파일명.';
COMMENT ON COLUMN run_artifacts.artifact_class IS '산출물 분류. intermediate/final/evidence/agent_context';
COMMENT ON COLUMN run_artifacts.storage_path IS '파일시스템 또는 Supabase Storage 경로.';
COMMENT ON COLUMN run_artifacts.content_hash IS '중복 방지/근거 추적용 해시 값.';
COMMENT ON COLUMN run_artifacts.payload IS '행 수, 요약 수치, 미리보기 메타 등 소형 JSON 메타.';

CREATE INDEX IF NOT EXISTS idx_run_artifacts_run
    ON run_artifacts (run_id);

CREATE INDEX IF NOT EXISTS idx_run_artifacts_step
    ON run_artifacts (step_id);

CREATE INDEX IF NOT EXISTS idx_run_artifacts_class_type
    ON run_artifacts (artifact_class, artifact_type);

CREATE INDEX IF NOT EXISTS idx_run_artifacts_run_class
    ON run_artifacts (run_id, artifact_class);

-- =========================================================
-- 4) run_report_context
-- =========================================================
-- Agent 입력용 최종 리포트 컨텍스트
-- full_context_json: 근거 추적용 전체 컨텍스트
-- prompt_context_json: LLM 호출 최적화용 축약 컨텍스트

CREATE TABLE IF NOT EXISTS run_report_context (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id                UUID NOT NULL UNIQUE REFERENCES runs(id) ON DELETE CASCADE,

    mode                  TEXT NOT NULL,
    context_version       TEXT NOT NULL DEFAULT 'v1',

    full_context_json     JSONB NOT NULL,
    prompt_context_json   JSONB NOT NULL,

    executive_summary     TEXT,
    key_findings          JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_index        JSONB NOT NULL DEFAULT '[]'::jsonb,

    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE run_report_context IS 'Agent 입력용 최종 리포트 컨텍스트. full/prompt를 분리 저장.';
COMMENT ON COLUMN run_report_context.mode IS '중복 저장된 실행 모드(조회 편의용 denormalized field).';
COMMENT ON COLUMN run_report_context.context_version IS '컨텍스트 스키마 버전.';
COMMENT ON COLUMN run_report_context.full_context_json IS '근거 추적용 전체 컨텍스트.';
COMMENT ON COLUMN run_report_context.prompt_context_json IS 'LLM 호출 최적화용 축약 컨텍스트.';
COMMENT ON COLUMN run_report_context.executive_summary IS '최종 리포트 핵심 요약 텍스트.';
COMMENT ON COLUMN run_report_context.key_findings IS '핵심 인사이트 목록.';
COMMENT ON COLUMN run_report_context.evidence_index IS '근거 artifact 참조 목록.';

CREATE INDEX IF NOT EXISTS idx_run_report_context_mode
    ON run_report_context (mode);

DROP TRIGGER IF EXISTS trg_run_report_context_updated_at ON run_report_context;
CREATE TRIGGER trg_run_report_context_updated_at
BEFORE UPDATE ON run_report_context
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- =========================================================
-- 5) agent_chat_logs
-- =========================================================
-- Agent 탭 질의응답 이력
-- 초기에는 단순 저장, 이후 품질 분석/질문 유형 분류 확장 가능

CREATE TABLE IF NOT EXISTS agent_chat_logs (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id                UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,

    mode                  TEXT NOT NULL,
    user_question         TEXT NOT NULL,
    assistant_answer      TEXT NOT NULL,

    used_context_version  TEXT,
    answer_scope          TEXT NOT NULL DEFAULT 'final_report_only'
                          CHECK (answer_scope IN ('final_report_only','evidence_trace')),

    question_type         TEXT,
    model_name            TEXT,

    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE agent_chat_logs IS 'Agent 탭 질의응답 이력.';
COMMENT ON COLUMN agent_chat_logs.mode IS '질의 당시 기준 실행 모드.';
COMMENT ON COLUMN agent_chat_logs.used_context_version IS '답변 생성에 사용한 report context 버전.';
COMMENT ON COLUMN agent_chat_logs.answer_scope IS '답변 허용 범위. final_report_only 또는 evidence_trace';
COMMENT ON COLUMN agent_chat_logs.question_type IS '질문 분류. 예: summary, comparison, insight, warning';
COMMENT ON COLUMN agent_chat_logs.model_name IS '응답 생성에 사용한 모델명.';

CREATE INDEX IF NOT EXISTS idx_agent_chat_logs_run_created
    ON agent_chat_logs (run_id, created_at DESC);

-- =========================================================
-- 6) RLS 기본값 (초기: 비활성)
-- =========================================================
-- 초기 개발 단계에서는 service_role 또는 내부 시스템 전용 사용을 전제로 비활성.
-- 추후 멀티유저/권한 분리 필요 시 정책 재설계.

ALTER TABLE runs DISABLE ROW LEVEL SECURITY;
ALTER TABLE run_steps DISABLE ROW LEVEL SECURITY;
ALTER TABLE run_artifacts DISABLE ROW LEVEL SECURITY;
ALTER TABLE run_report_context DISABLE ROW LEVEL SECURITY;
ALTER TABLE agent_chat_logs DISABLE ROW LEVEL SECURITY;

-- =========================================================
-- 7) 기존 ops_* 처리 방안
-- =========================================================
-- 권장 정책:
-- 1) ops_run_log, ops_asset_meta, ops_connection_log는 read-only 유지
-- 2) 신규 쓰기는 runs/run_steps/run_artifacts/run_report_context/agent_chat_logs로 전환
-- 3) 운영 안정화 후 ops_*는 폐기 예정 대상으로 문서화