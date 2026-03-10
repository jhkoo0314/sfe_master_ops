"""
HTML Builder 스키마

Layer 1: OPS Report Builder
  - Sandbox/Territory/CRM Result Asset → 분석 보고 HTML 자동 생성
  - 정해진 템플릿 슬롯에 데이터 자동 주입

Layer 2: WebSlide Studio
  - WebSlide Architect v3.5 페르소나 기반 슬라이드 제작기
  - 파일 업로드/붙여넣기 → Analyst → Blueprint → Build 흐름
  - 출력: 단일 HTML 웹슬라이드
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ────────────────────────────────────────
# Layer 1: OPS Report Builder 스키마
# ────────────────────────────────────────

ReportSourceModule = Literal["crm", "sandbox", "territory", "prescription"]

class ReportSection(BaseModel):
    """보고서 섹션 하나 (슬롯에 주입될 단위)."""
    section_id: str
    section_title: str
    section_type: Literal["kpi_cards", "chart", "table", "map", "gap_list", "text"]
    data: dict = Field(default_factory=dict)     # 주입된 실제 데이터
    render_hint: str = ""                         # Builder가 시각화 시 참고할 힌트

class OpsReportPayload(BaseModel):
    """
    OPS Result Asset → HTML 렌더링을 위한 표준 페이로드.
    Builder는 이 객체를 받아 HTML을 생성한다.
    """
    report_title: str
    source_module: ReportSourceModule
    period_label: str
    sections: list[ReportSection] = Field(default_factory=list)
    executive_summary: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)


# ────────────────────────────────────────
# Layer 2: WebSlide Studio 스키마
# ────────────────────────────────────────

WebSlideTheme = Literal[
    "A_signature_premium",
    "B_enterprise_swiss",
    "C_minimal_keynote",
    "D_analytical_dashboard",
    "E_deep_tech_dark",
]

WebSlidePhase = Literal["intake", "strategy", "blueprint", "build", "done"]

class WebSlideSlotContent(BaseModel):
    """업로드/붙여넣기된 원본 콘텐츠."""
    content_type: Literal["text", "file_text", "json_data", "asset_data"]
    raw_text: str = ""
    filename: Optional[str] = None
    source_module: Optional[str] = None   # OPS 모듈 데이터 참조 시

class SlideBlueprint(BaseModel):
    """WebSlide Architect Blueprint 형식."""
    slide_number: int
    slide_type: Literal["message", "structure", "data"]
    purpose: str
    headline: str
    support_points: list[str] = Field(default_factory=list)
    visual_type: str           # "chart", "KPI cards", "process flow" 등
    layout_type: str           # "centered hero", "split left-right" 등
    density: Literal["low", "medium", "high"]
    background_treatment: str
    notes_for_build: str = ""

class WebSlideSession(BaseModel):
    """
    WebSlide Studio 세션 상태.
    페르소나 상태머신(PHASE 0~4)을 추적한다.
    """
    session_id: str
    current_phase: WebSlidePhase = "intake"
    selected_theme: Optional[WebSlideTheme] = None

    # 입력된 콘텐츠
    input_contents: list[WebSlideSlotContent] = Field(default_factory=list)

    # Analyst 결과 (PHASE 0)
    analyst_summary: Optional[str] = None
    analyst_questions: list[str] = Field(default_factory=list)

    # Blueprint (PHASE 2)
    blueprints: list[SlideBlueprint] = Field(default_factory=list)
    blueprint_approved: bool = False

    # 최종 HTML (PHASE 3)
    output_html: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# ────────────────────────────────────────
# Builder Result Asset
# ────────────────────────────────────────

class HtmlBuilderResultAsset(BaseModel):
    """
    HTML Builder 최종 산출물.
    OPS가 이 자산을 평가하여 보고 자산으로 승인한다.
    """
    asset_type: str = "html_builder_result_asset"

    # Layer 1 결과
    ops_report_html: Optional[str] = None
    report_payload: Optional[OpsReportPayload] = None

    # Layer 2 결과
    webslide_html: Optional[str] = None
    webslide_session: Optional[WebSlideSession] = None

    # 공통
    generated_at: datetime = Field(default_factory=datetime.now)
    source_modules: list[str] = Field(default_factory=list)
