"""
Validation Layer (OPS) FastAPI 앱 진입점

Sales Data OS에서 OPS는 Validation / Orchestration Layer를 담당한다.
이 패키지는 플랫폼 전체 코어가 아니라 현재 Validation / Orchestration 구현 경계다.
주요 역할은 Result Asset 평가, 연결 판단, 상태 조회다.

실행:
  uv run uvicorn ops_core.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ops_core.api.crm_router import router as crm_router
from ops_core.api.prescription_router import router as prescription_router
from ops_core.api.sandbox_router import router as sandbox_router
from ops_core.api.territory_router import router as territory_router
from ops_core.api.pipeline_router import router as pipeline_router

# ────────────────────────────────────────
# FastAPI 앱 초기화
# ────────────────────────────────────────

app = FastAPI(
    title="Sales Data OS Validation API (OPS)",
    description=(
        "Sales Data OS의 Validation / Orchestration API. "
        "5개 모듈(CRM, Prescription, Sandbox, Territory, Builder)의 "
        "Result Asset을 평가하고 연결을 판단합니다.\n\n"
        "핵심 원칙: 원천데이터 → Adapter → Module → Result Asset → Validation Layer (OPS)"
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정 (Streamlit 콘솔에서 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────
# 라우터 등록
# ────────────────────────────────────────

app.include_router(crm_router)
app.include_router(prescription_router)
app.include_router(sandbox_router)
app.include_router(territory_router)
app.include_router(pipeline_router)
# Builder는 UI + 검증 스크립트 레이어로 제공
# Streamlit 운영 콘솔은 현재 ui/ops_console.py 에서 사용 중


# ────────────────────────────────────────
# 기본 엔드포인트
# ────────────────────────────────────────

@app.get("/", summary="Validation Layer (OPS) 상태 확인")
async def root():
    return {
        "service": "Sales Data OS Validation API (OPS)",
        "version": "0.1.0",
        "status": "running",
        "principle": "원천데이터 → Adapter → Module → Result Asset → Validation Layer (OPS)",
        "active_modules": ["crm", "prescription", "sandbox", "territory", "pipeline"],
        "ui_modules": [
            "streamlit_console (ui/ops_console.py)",
            "builder_html (scripts/validate_builder_with_ops.py)",
        ],
        "planned_modules": [],
        "pipeline": {
            "endpoint": "POST /ops/pipeline/run",
            "flow": "crm → prescription → sandbox → territory → builder",
            "status_endpoint": "GET /ops/pipeline/status",
        }
    }


@app.get("/ops/diagram")
async def get_pipeline_diagram():
    """Validation Layer (OPS) 파이프라인 흐름 다이어그램 반환."""
    return {
        "pipeline": [
            {"step": 1, "module": "crm",          "asset": "crm_result_asset",          "eval": "POST /ops/crm/evaluate"},
            {"step": 2, "module": "prescription",  "asset": "prescription_result_asset",  "eval": "POST /ops/prescription/evaluate", "optional": True},
            {"step": 3, "module": "sandbox",       "asset": "sandbox_result_asset",       "eval": "POST /ops/sandbox/evaluate"},
            {"step": 4, "module": "territory",     "asset": "territory_result_asset",     "eval": "POST /ops/territory/evaluate"},
            {"step": 5, "module": "builder",       "asset": "html_builder_result_asset",  "eval": "UI: templates/total_valid_templates.html"},
        ],
        "orchestrator": "POST /ops/pipeline/run",
        "principle": "원천데이터 → Adapter → Module → Result Asset → OPS Validation 평가 → Handoff",
    }

@app.get("/ops/status", summary="전체 모듈 상태 조회")
async def ops_status():
    """현재 활성화된 모듈과 각 모듈의 엔드포인트 상태를 반환합니다."""
    return {
        "modules": {
            "crm": {
                "status": "active",
                "evaluate_endpoint": "/ops/crm/evaluate",
            },
            "prescription": {
                "status": "active",
                "evaluate_endpoint": "/ops/prescription/evaluate",
            },
            "sandbox": {
                "status": "active",
                "evaluate_endpoint": "/ops/sandbox/evaluate",
            },
            "territory": {
                "status": "active",
                "evaluate_endpoint": "/ops/territory/evaluate",
            },
            "builder": {
                "status": "ui-active",
                "evaluate_endpoint": "ui/ops_console.py + scripts/validate_builder_with_ops.py",
            },
        }
    }
