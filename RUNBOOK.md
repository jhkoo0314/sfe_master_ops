# SFE OPS 실행 가이드 (RUNBOOK)

작성일: 2026-03-10

---

## 0. 핵심 원칙 한 줄 확인

```
원천데이터 -> Adapter -> Module -> Result Asset -> OPS
```

---

## 1. 사전 준비

### 1-1. uv 설치 확인

```bash
uv --version
# 설치 안 된 경우: pip install uv 또는 https://docs.astral.sh/uv/
```

### 1-2. 의존성 설치

```bash
# 프로젝트 루트에서 실행
uv sync

# dev 의존성 포함
uv sync --extra dev
```

### 1-3. 환경 변수 설정

```bash
# .env.example 복사
copy .env.example .env

# .env 파일을 열어 Supabase 정보 입력
# SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
```

---

## 2. OPS Core API 실행

```bash
# 개발 서버 실행 (자동 리로드)
uv run uvicorn ops_core.main:app --reload --host 0.0.0.0 --port 8000

# API 문서 확인
# http://localhost:8000/docs
```

---

## 3. Streamlit 운영 콘솔 실행

```bash
uv run streamlit run ui/app.py --server.port 8501
# http://localhost:8501
```

---

## 4. 테스트 실행

```bash
# 전체 테스트
uv run pytest

# 특정 모듈 테스트
uv run pytest tests/test_crm/
uv run pytest tests/test_prescription/

# 결과 상세 출력
uv run pytest -v

# 커버리지 확인
uv run pytest --cov=.
```

---

## 5. Supabase 스키마 적용

### 초기 스키마 적용 (처음 한 번만)

1. Supabase 대시보드 접속: https://app.supabase.com
2. 해당 프로젝트 선택
3. 좌측 메뉴 → SQL Editor
4. `migrations/001_initial_schema.sql` 내용 붙여넣기 후 실행

### 스키마 변경 시

- 새 마이그레이션 파일을 `migrations/` 아래 순번으로 추가
- 예: `002_add_crm_tables.sql`

---

## 6. 데이터 디렉토리 구조

```
data/
├── hospital_master/      # 공공 병원 기준 데이터
├── company_master/       # 회사 마스터 데이터
└── raw/                  # 원천 데이터 임시 보관
```

---

## 7. 모듈별 실행 흐름 요약

### CRM 모듈 실행 순서

1. `data/hospital_master/` 에 공공 병원 파일 준비
2. `data/company_master/` 에 회사 마스터 파일 준비
3. CRM raw 파일 업로드 (UI 또는 API)
4. Adapter 실행 → `crm_standard_activity` 생성
5. Result Asset 생성 → `crm_result_asset`
6. OPS 평가 요청 → `POST /ops/crm/evaluate`

### Prescription 모듈 실행 순서 (CRM 완료 후)

1. 범용 키 규칙 확인 (pharmacy_id, wholesaler_id)
2. Prescription raw 파일 업로드
3. Adapter 실행 → `prescription_standard_flow` 생성
4. Result Asset 생성 → `prescription_result_asset`
5. OPS 평가 요청 → `POST /ops/prescription/evaluate`

---

## 8. 문제 해결

| 증상                      | 원인                                    | 해결                                      |
| ------------------------- | --------------------------------------- | ----------------------------------------- |
| `hospital_id` 매핑 실패   | 회사 마스터의 병원명이 공공 기준과 다름 | Adapter 매핑 규칙 확인                    |
| OPS quality_status = fail | Result Asset 필수 항목 누락             | 해당 모듈 로그 확인 후 Adapter부터 재실행 |
| Supabase 연결 실패        | .env 설정 오류                          | SUPABASE_URL, KEY 재확인                  |
| 테스트 실패               | fixture 데이터 없음                     | `tests/fixtures/` 에 샘플 데이터 추가     |

---

## 9. 금지 사항 (AGENTS.md 요약)

- raw 데이터를 OPS로 직접 보내지 않는다.
- Sandbox를 전체 허브처럼 설계하지 않는다.
- Adapter 없이 Module부터 키우지 않는다.
- 회사 맞춤 규칙을 범용 규칙보다 먼저 만들지 않는다.
