"""
HTML Builder 스키마

OPS Report Builder
  - Sandbox/Territory/CRM/Prescription payload → 분석 보고 HTML 자동 생성
  - 정해진 템플릿 슬롯에 데이터 자동 주입
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


# ────────────────────────────────────────
# Layer 1: OPS Report Builder 스키마
# ────────────────────────────────────────

ReportSourceModule = Literal["crm", "sandbox", "territory", "prescription"]
BuilderTemplateKey = Literal["report_template", "territory_map", "prescription_flow", "crm_analysis"]

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


class BuilderInputReference(BaseModel):
    """
    Builder가 어떤 자산을 어떤 템플릿으로 보낼지 설명하는 참조 정보.
    OPS는 이 메타를 보고 표현 연결을 판단한다.
    """
    template_key: BuilderTemplateKey
    template_path: str
    source_module: ReportSourceModule
    asset_type: str
    source_asset_path: Optional[str] = None
    description: str = ""


class BuilderInputStandard(BaseModel):
    """
    Builder가 받는 공통 입력 규격.
    모듈별 자산을 바로 HTML로 보내지 않고 이 구조로 먼저 맞춘다.
    """
    template_key: BuilderTemplateKey
    template_path: str
    report_title: str
    executive_summary: list[str] = Field(default_factory=list)
    source_references: list[BuilderInputReference] = Field(default_factory=list)
    payload_seed: dict[str, Any] = Field(default_factory=dict)
    source_modules: list[str] = Field(default_factory=list)


class BuilderPayloadStandard(BaseModel):
    """
    템플릿이 바로 읽는 최종 주입용 데이터.
    """
    template_key: BuilderTemplateKey
    template_path: str
    report_title: str
    payload: dict[str, Any] = Field(default_factory=dict)
    source_modules: list[str] = Field(default_factory=list)
    output_name: str = "builder_output.html"
    render_mode: Literal["report_data_json", "territory_window_vars", "prescription_window_vars", "crm_window_vars"] = "report_data_json"

# ────────────────────────────────────────
# Builder Result Asset
# ────────────────────────────────────────

class HtmlBuilderResultAsset(BaseModel):
    """
    HTML Builder 최종 산출물.
    OPS가 이 자산을 평가하여 보고 자산으로 승인한다.
    """
    asset_type: str = "html_builder_result_asset"

    # Builder 입력/표현 메타
    template_reference: Optional[BuilderInputReference] = None
    render_summary: dict[str, Any] = Field(default_factory=dict)
    report_payload_summary: dict[str, Any] = Field(default_factory=dict)
    output_reference: dict[str, Any] = Field(default_factory=dict)

    # HTML 결과
    ops_report_html: Optional[str] = None
    report_payload: Optional[OpsReportPayload] = None
    builder_input: Optional[BuilderInputStandard] = None
    builder_payload: Optional[BuilderPayloadStandard] = None

    # 공통
    generated_at: datetime = Field(default_factory=datetime.now)
    source_modules: list[str] = Field(default_factory=list)
