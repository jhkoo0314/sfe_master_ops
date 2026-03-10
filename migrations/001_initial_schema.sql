-- SFE OPS Supabase 초기 스키마
-- Phase 1: OPS Core 운영 메타 테이블 3종
-- 실행 대상: Supabase SQL Editor
-- 작성일: 2026-03-10

-- ────────────────────────────────────────
-- 0. 확장 및 공통 설정
-- ────────────────────────────────────────

-- UUID 생성 확장 (Supabase 기본 활성화 상태)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ────────────────────────────────────────
-- 1. ops_run_log - 모듈 실행 이력 테이블
-- ────────────────────────────────────────
-- 각 모듈이 실행될 때마다 1건 기록.
-- OPS가 "언제", "어떤 모듈이", "어떤 결과로" 실행됐는지 추적.

CREATE TABLE IF NOT EXISTS ops_run_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_name     TEXT NOT NULL,                          -- 'crm' | 'prescription' | 'sandbox' | 'territory' | 'builder'
    run_started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),     -- 실행 시작 시각
    run_finished_at TIMESTAMPTZ,                            -- 실행 완료 시각 (NULL이면 진행 중)
    run_status      TEXT NOT NULL DEFAULT 'running',        -- 'running' | 'success' | 'failed'
    input_summary   JSONB,                                  -- 입력 파일명, 행 수 등 요약
    error_message   TEXT,                                   -- 실패 시 오류 메시지
    triggered_by    TEXT,                                   -- 실행 주체 ('ui' | 'api' | 'test')
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE ops_run_log IS 'OPS 모듈 실행 이력. 각 실행마다 1건 기록.';
COMMENT ON COLUMN ops_run_log.module_name IS '실행된 모듈 식별자 (crm, prescription, sandbox, territory, builder)';
COMMENT ON COLUMN ops_run_log.run_status IS '실행 상태: running(진행 중), success(성공), failed(실패)';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_ops_run_log_module ON ops_run_log (module_name);
CREATE INDEX IF NOT EXISTS idx_ops_run_log_status ON ops_run_log (run_status);
CREATE INDEX IF NOT EXISTS idx_ops_run_log_started ON ops_run_log (run_started_at DESC);


-- ────────────────────────────────────────
-- 2. ops_asset_meta - Result Asset 메타 테이블
-- ────────────────────────────────────────
-- 각 모듈이 생성한 Result Asset의 품질 평가 결과와 메타를 저장.
-- OPS가 "어떤 자산이", "어떤 품질로", "다음 어디로 갈 수 있는지" 판단한 결과.

CREATE TABLE IF NOT EXISTS ops_asset_meta (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_log_id          UUID REFERENCES ops_run_log(id) ON DELETE CASCADE,
    module_name         TEXT NOT NULL,                      -- 생산 모듈
    asset_type          TEXT NOT NULL,                      -- 'crm_result_asset' | 'prescription_result_asset' | ...
    quality_status      TEXT NOT NULL,                      -- 'pass' | 'warn' | 'fail'
    quality_score       NUMERIC(5, 2),                      -- 0.00 ~ 100.00
    reasoning_note      TEXT,                               -- OPS 판단 근거 (사람이 읽을 수 있는 설명)
    asset_payload       JSONB,                              -- Result Asset 핵심 요약 payload
    next_modules        TEXT[],                             -- 연결 가능한 다음 모듈 목록
    asset_file_path     TEXT,                               -- 로컬 저장 경로 (있는 경우)
    evaluated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE ops_asset_meta IS 'OPS가 평가한 Result Asset 메타. 품질 상태와 다음 연결 가능 모듈을 저장.';
COMMENT ON COLUMN ops_asset_meta.quality_status IS 'OPS 품질 게이트 결과: pass(통과), warn(주의), fail(실패)';
COMMENT ON COLUMN ops_asset_meta.reasoning_note IS 'OPS가 왜 이 판단을 내렸는지 사람이 읽을 수 있는 설명';
COMMENT ON COLUMN ops_asset_meta.next_modules IS '이 자산을 재사용할 수 있는 다음 모듈 목록';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_ops_asset_meta_module ON ops_asset_meta (module_name);
CREATE INDEX IF NOT EXISTS idx_ops_asset_meta_status ON ops_asset_meta (quality_status);
CREATE INDEX IF NOT EXISTS idx_ops_asset_meta_type ON ops_asset_meta (asset_type);
CREATE INDEX IF NOT EXISTS idx_ops_asset_meta_evaluated ON ops_asset_meta (evaluated_at DESC);


-- ────────────────────────────────────────
-- 3. ops_connection_log - 모듈 간 연결 판단 이력
-- ────────────────────────────────────────
-- OPS가 "A모듈 -> B모듈" 연결을 허용하거나 거부한 이력.
-- 연결의 근거와 자산 ID를 추적.

CREATE TABLE IF NOT EXISTS ops_connection_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_module         TEXT NOT NULL,                      -- 연결 출발 모듈
    to_module           TEXT NOT NULL,                      -- 연결 도착 모듈
    from_asset_id       UUID REFERENCES ops_asset_meta(id) ON DELETE SET NULL,
    connection_status   TEXT NOT NULL,                      -- 'allowed' | 'blocked'
    block_reason        TEXT,                               -- 거부된 경우 이유
    connection_note     TEXT,                               -- OPS 판단 노트
    connected_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE ops_connection_log IS 'OPS 모듈 간 연결 판단 이력. 허용/거부 근거를 추적.';
COMMENT ON COLUMN ops_connection_log.connection_status IS '연결 판단: allowed(허용), blocked(거부)';
COMMENT ON COLUMN ops_connection_log.block_reason IS '연결이 거부된 경우 그 이유 (품질 미달, 키 불일치 등)';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_ops_connection_log_from ON ops_connection_log (from_module);
CREATE INDEX IF NOT EXISTS idx_ops_connection_log_to ON ops_connection_log (to_module);
CREATE INDEX IF NOT EXISTS idx_ops_connection_log_status ON ops_connection_log (connection_status);
CREATE INDEX IF NOT EXISTS idx_ops_connection_log_connected ON ops_connection_log (connected_at DESC);


-- ────────────────────────────────────────
-- 4. 행 보안 정책 (RLS) - 기본 설정
-- ────────────────────────────────────────
-- 초기에는 service_role로만 접근하므로 RLS 비활성화.
-- 실운영 전환 시 정책 추가 예정.

ALTER TABLE ops_run_log DISABLE ROW LEVEL SECURITY;
ALTER TABLE ops_asset_meta DISABLE ROW LEVEL SECURITY;
ALTER TABLE ops_connection_log DISABLE ROW LEVEL SECURITY;
