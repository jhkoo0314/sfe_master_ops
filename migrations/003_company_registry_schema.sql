-- 003_company_registry_schema.sql
-- Sales Data OS company registry / fixed company_key schema
-- 작성일: 2026-03-19
-- 기준: 회사 이름과 시스템 고정 key 분리

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =========================================================
-- 1) company_registry
-- =========================================================
-- 사용자가 보는 회사 이름과 시스템이 쓰는 고정 company_key를 분리 저장
-- 모든 run / source / standard / validation 경로는 company_key 기준으로 유지

CREATE TABLE IF NOT EXISTS company_registry (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_key             TEXT NOT NULL UNIQUE,
    company_name            TEXT NOT NULL,
    company_name_normalized TEXT NOT NULL,

    status                  TEXT NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'inactive')),

    company_code_external   TEXT,
    aliases_json            JSONB NOT NULL DEFAULT '[]'::jsonb,
    notes                   TEXT,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE company_registry IS '회사 등록 마스터. 표시용 회사 이름과 시스템 고정 company_key를 분리 관리.';
COMMENT ON COLUMN company_registry.company_key IS '시스템 내부 고정 회사 키. 경로/run/저장 기준.';
COMMENT ON COLUMN company_registry.company_name IS '현재 표시용 회사 이름.';
COMMENT ON COLUMN company_registry.company_name_normalized IS '검색/중복 확인용 정규화 회사 이름.';
COMMENT ON COLUMN company_registry.status IS '활성 상태. active/inactive';
COMMENT ON COLUMN company_registry.company_code_external IS '외부 시스템/업무에서 쓰는 회사 코드가 있을 경우 저장.';
COMMENT ON COLUMN company_registry.aliases_json IS '과거 이름, 별칭, 검색 보정용 이름 목록.';

CREATE INDEX IF NOT EXISTS idx_company_registry_name_norm
    ON company_registry (company_name_normalized);

CREATE INDEX IF NOT EXISTS idx_company_registry_status
    ON company_registry (status);

DROP TRIGGER IF EXISTS trg_company_registry_updated_at ON company_registry;
CREATE TRIGGER trg_company_registry_updated_at
BEFORE UPDATE ON company_registry
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- =========================================================
-- 2) runs -> company_registry FK
-- =========================================================
-- 기존 runs.company_key는 유지하되, 등록된 회사와 연결 가능한 FK를 추가
-- 초기 단계에서는 nullable로 두고 점진 마이그레이션 후 NOT NULL 검토

ALTER TABLE runs
ADD COLUMN IF NOT EXISTS company_registry_id UUID REFERENCES company_registry(id) ON DELETE SET NULL;

COMMENT ON COLUMN runs.company_registry_id IS 'company_registry 연결용 FK. 점진 전환 단계에서는 nullable.';

CREATE INDEX IF NOT EXISTS idx_runs_company_registry
    ON runs (company_registry_id, started_at DESC);

-- =========================================================
-- 3) seed for existing companies
-- =========================================================
-- 기존 운영 중인 회사를 registry에 선등록

INSERT INTO company_registry (
    company_key,
    company_name,
    company_name_normalized,
    aliases_json
)
VALUES
    (
        'daon_pharma',
        '다온파마',
        '다온파마',
        '["daon_pharma","daon-pharma","Daon Pharma","다온제약"]'::jsonb
    ),
    (
        'hangyeol_pharma',
        '한결제약',
        '한결제약',
        '["hangyeol_pharma","hangyeol-pharma","Hangyeol Pharma","한결파마"]'::jsonb
    )
ON CONFLICT (company_key) DO UPDATE
SET
    company_name = EXCLUDED.company_name,
    company_name_normalized = EXCLUDED.company_name_normalized,
    aliases_json = EXCLUDED.aliases_json,
    updated_at = now();

-- =========================================================
-- 4) backfill runs.company_registry_id
-- =========================================================
-- 기존 runs가 있으면 company_key 기준으로 registry FK를 연결

UPDATE runs r
SET company_registry_id = c.id
FROM company_registry c
WHERE r.company_registry_id IS NULL
  AND r.company_key = c.company_key;

-- =========================================================
-- 5) RLS 기본값
-- =========================================================

ALTER TABLE company_registry DISABLE ROW LEVEL SECURITY;
