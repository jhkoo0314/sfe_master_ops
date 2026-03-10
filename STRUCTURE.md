# SFE OPS 저장소 구조

작성일: 2026-03-10

---

## 핵심 원칙

```
원천데이터 -> Adapter -> Module -> Result Asset -> OPS
```

---

## 디렉토리 구조

```
sfe_master_ops/
│
├── adapters/                   # Adapter 레이어: 회사별 raw를 공통 구조로 번역
│   ├── __init__.py
│   ├── crm/                    # CRM raw adapter
│   ├── prescription/           # Prescription raw adapter
│   └── ...
│
├── modules/                    # Module 레이어: Result Asset을 만드는 처리기
│   ├── crm/                    # Behavior CRM 모듈
│   ├── prescription/           # Prescription Data Flow 모듈
│   ├── sandbox/                # SFE Sandbox 모듈
│   ├── territory/              # Territory Optimizer 모듈
│   └── builder/                # HTML Builder 모듈
│
├── ops_core/                   # OPS Core 레이어: 중앙 판단 엔진 (FastAPI)
│   ├── api/                    # FastAPI 라우터
│   ├── schemas/                # OPS 입출력 Pydantic 스키마
│   └── main.py                 # FastAPI 앱 진입점
│
├── result_assets/              # Result Asset 스키마 정의 (Pydantic 모델)
│   ├── crm_result_asset.py
│   ├── prescription_result_asset.py
│   ├── sandbox_result_asset.py
│   ├── territory_result_asset.py
│   └── builder_result_asset.py
│
├── common/                     # 공통 유틸리티
│   ├── exceptions.py           # 레이어별 예외 클래스
│   ├── types.py                # 공통 타입, Enum, 상수
│   └── config.py               # 환경 설정 (pydantic-settings)
│
├── tests/                      # 테스트
│   ├── fixtures/               # fixture 데이터 (Excel, CSV, JSON)
│   ├── test_crm/
│   ├── test_prescription/
│   ├── test_sandbox/
│   ├── test_territory/
│   └── test_builder/
│
├── ui/                         # Streamlit 운영 콘솔 (비개발자 운영 화면)
│   └── app.py
│
├── migrations/                 # Supabase SQL 마이그레이션
│   └── 001_initial_schema.sql
│
├── data/                       # 로컬 데이터 (gitignore 처리)
│   ├── hospital_master/
│   ├── company_master/
│   └── raw/
│
├── pyproject.toml              # uv 프로젝트 설정
├── .env.example                # 환경 변수 템플릿
├── .env                        # 실제 환경 변수 (git 제외)
├── RUNBOOK.md                  # 실행 가이드
├── STRUCTURE.md                # 이 문서
├── TODO.md                     # 전체 구현 계획
└── AGENTS.md                   # 구현 규칙 (항상 먼저 확인)
```

---

## 레이어별 역할 요약

| 레이어       | 폴더             | 역할                              | 기술                |
| ------------ | ---------------- | --------------------------------- | ------------------- |
| UI           | `ui/`            | 운영 콘솔 (업로드/실행/확인)      | Streamlit           |
| OPS Core     | `ops_core/`      | 중앙 판단 엔진 (평가/연결/게이트) | FastAPI + Pydantic  |
| Module       | `modules/`       | Result Asset 생산 처리기          | Python + Polars     |
| Adapter      | `adapters/`      | raw → 공통 구조 번역              | Python + Polars     |
| Result Asset | `result_assets/` | 모듈 간 교환 단위 정의            | Pydantic            |
| Common       | `common/`        | 예외/타입/설정 공유               | Python              |
| Storage      | `migrations/`    | 운영 메타 저장 스키마             | Supabase PostgreSQL |
| Test         | `tests/`         | 계층별 독립 검증                  | pytest              |

---

## 중요 원칙

1. **OPS Core는 Result Asset만 본다.** raw를 직접 읽지 않는다.
2. **Adapter가 항상 먼저다.** Adapter 없이 Module부터 키우지 않는다.
3. **각 레이어는 독립적으로 테스트 가능해야 한다.**
4. **회사 맞춤 로직은 Adapter 안에서만 처리한다.**
