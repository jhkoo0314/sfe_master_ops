"""
OPS Core FastAPI 앱 진입점

SFE OPS의 중앙 판단 엔진.
모든 모듈의 Result Asset 평가, 연결 판단, 상태 조회를 담당한다.

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
    title="SFE OPS Core API",
    description=(
        "SFE OPS 중앙 운영 엔진. "
        "5개 모듈(CRM, Prescription, Sandbox, Territory, Builder)의 "
        "Result Asset을 평가하고 연결을 판단합니다.\n\n"
        "핵심 원칙: 원천데이터 → Adapter → Module → Result Asset → OPS"
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
# Phase 6 Builder는 UI 레이어로 제공 (ui/html_builder.html)
# Phase 8 Streamlit 콘솔 도입 예정


# ────────────────────────────────────────
# 기본 엔드포인트
# ────────────────────────────────────────

@app.get("/", summary="OPS Core 상태 확인")
async def root():
    return {
        "service": "SFE OPS Core API",
        "version": "0.1.0",
        "status": "running",
        "principle": "원천데이터 → Adapter → Module → Result Asset → OPS",
        "active_modules": ["crm", "prescription", "sandbox", "territory", "pipeline"],
        "ui_modules": ["builder (html_builder.html)"],
        "planned_modules": ["streamlit_console"],
        "pipeline": {
            "endpoint": "POST /ops/pipeline/run",
            "flow": "crm → prescription → sandbox → territory → builder",
            "status_endpoint": "GET /ops/pipeline/status",
        }
    }


@app.get("/ops/diagram")
async def get_pipeline_diagram():
    """OPS 파이프라인 흐름 다이어그램 반환."""
    return {
        "pipeline": [
            {"step": 1, "module": "crm",          "asset": "crm_result_asset",          "eval": "POST /ops/crm/evaluate"},
            {"step": 2, "module": "prescription",  "asset": "prescription_result_asset",  "eval": "POST /ops/prescription/evaluate", "optional": True},
            {"step": 3, "module": "sandbox",       "asset": "sandbox_result_asset",       "eval": "POST /ops/sandbox/evaluate"},
            {"step": 4, "module": "territory",     "asset": "territory_result_asset",     "eval": "POST /ops/territory/evaluate"},
            {"step": 5, "module": "builder",       "asset": "html_builder_result_asset",  "eval": "UI: ui/html_builder.html"},
        ],
        "orchestrator": "POST /ops/pipeline/run",
        "principle": "원천데이터 → Adapter → Module → Result Asset → OPS 평가 → Handoff",
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
            "prescription": {"status": "planned"},
            "sandbox": {"status": "planned"},
            "territory": {"status": "planned"},
            "builder": {"status": "planned"},
        }
    }
