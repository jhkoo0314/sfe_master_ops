from __future__ import annotations

import json
import os

import pandas as pd
import streamlit as st

from ops_core.workflow.execution_registry import get_execution_mode_modules
from ui.console_paths import get_active_company_key, get_project_root


def get_artifact_directories(module: str) -> list[tuple[str, str]]:
    root = get_project_root()
    company = get_active_company_key()
    mapping = {
        "crm": [
            ("정규화 파일", os.path.join(root, "data", "ops_standard", company, "crm")),
            ("검증 산출물", os.path.join(root, "data", "ops_validation", company, "crm")),
        ],
        "prescription": [
            ("정규화 파일", os.path.join(root, "data", "ops_standard", company, "prescription")),
            ("검증 산출물", os.path.join(root, "data", "ops_validation", company, "prescription")),
        ],
        "sandbox": [
            ("정규화 파일", os.path.join(root, "data", "ops_standard", company, "sandbox")),
            ("검증 산출물", os.path.join(root, "data", "ops_validation", company, "sandbox")),
        ],
        "territory": [
            ("정규화 파일", os.path.join(root, "data", "ops_standard", company, "territory")),
            ("검증 산출물", os.path.join(root, "data", "ops_validation", company, "territory")),
        ],
        "builder": [("Builder 결과", os.path.join(root, "data", "ops_validation", company, "builder"))],
    }
    return mapping.get(module, [])


def get_artifact_stage(source_label: str, module: str) -> tuple[str, str]:
    if source_label == "정규화 파일":
        return "정규화", "NORMALIZED"
    if source_label == "검증 산출물":
        return "검증결과", "VALIDATION"
    if source_label == "Builder 결과":
        return "Builder", "BUILDER"
    return source_label, module.upper()


def collect_artifact_files(execution_mode: str) -> list[dict]:
    collected: list[dict] = []
    seen_paths: set[str] = set()

    for module in get_execution_mode_modules(execution_mode):
        for source_label, folder in get_artifact_directories(module):
            if not os.path.isdir(folder):
                continue
            for file_name in sorted(os.listdir(folder)):
                path = os.path.join(folder, file_name)
                if not os.path.isfile(path) or path in seen_paths:
                    continue
                ext = os.path.splitext(file_name)[1].lower()
                if ext not in {".xlsx", ".csv", ".json", ".html"}:
                    continue
                seen_paths.add(path)
                stage_label, stage_value = get_artifact_stage(source_label, module)
                collected.append(
                    {
                        "module": module,
                        "source_label": source_label,
                        "stage_label": stage_label,
                        "stage_value": stage_value,
                        "name": file_name,
                        "path": path,
                        "ext": ext,
                        "size_kb": round(os.path.getsize(path) / 1024, 1),
                    }
                )
    return collected


@st.cache_data(show_spinner=False)
def load_artifact_preview(path: str, ext: str, max_rows: int = 10) -> tuple[pd.DataFrame | None, str]:
    try:
        if ext == ".csv":
            return pd.read_csv(path, nrows=max_rows), "table"
        if ext == ".xlsx":
            return pd.read_excel(path, nrows=max_rows), "table"
        if ext == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return pd.DataFrame(data[:max_rows]), "table"
            if isinstance(data, dict):
                if all(isinstance(v, (str, int, float, bool, type(None))) for v in data.values()):
                    rows = [{"key": k, "value": v} for k, v in list(data.items())[:max_rows]]
                    return pd.DataFrame(rows), "table"
                rows = [{"key": k, "value": json.dumps(v, ensure_ascii=False)} for k, v in list(data.items())[:max_rows]]
                return pd.DataFrame(rows), "table"
        return None, "download_only"
    except Exception as exc:
        return pd.DataFrame([{"preview_error": str(exc)}]), "table"


def get_report_type_options() -> list[str]:
    return [
        "CRM 행동 분석 보고서",
        "Sandbox 성과 보고서",
        "Territory 권역 지도 보고서",
        "PDF 처방흐름 보고서",
        "RADAR Decision Brief",
        "통합 검증 보고서",
    ]


def get_report_type_description(report_type: str) -> str:
    descriptions = {
        "CRM 행동 분석 보고서": "CRM 활동 raw를 바탕으로 행동 품질, 신뢰도, 파이프라인 흐름, 담당자별 CoachScore를 보는 CRM 전용 HTML 보고서입니다.",
        "Sandbox 성과 보고서": "실적, 목표, CRM을 묶어 성과 분석 결과를 보여주는 HTML 보고서입니다.",
        "Territory 권역 지도 보고서": "권역별 커버리지와 이동 흐름을 지도 중심으로 보는 HTML 보고서입니다.",
        "PDF 처방흐름 보고서": "Prescription Data Flow 비교표와 추적 보조표를 중심으로 보는 HTML 보고서입니다.",
        "RADAR Decision Brief": "Validation 승인 KPI/요약 입력으로 생성된 신호, 우선순위, 의사결정 옵션 템플릿 보고서입니다.",
        "통합 검증 보고서": "HTML Builder 화면을 열어 Sandbox, CRM, Territory, Prescription 결과를 한 곳에서 미리보는 통합 진입 보고서입니다.",
    }
    return descriptions.get(report_type, "")


def get_report_type_artifacts(report_type: str) -> str:
    artifacts = {
        "CRM 행동 분석 보고서": "연결 파일: crm_analysis_preview.html / crm_result_asset.json",
        "Sandbox 성과 보고서": "연결 파일: sandbox_report_preview.html / sandbox_result_asset.json",
        "Territory 권역 지도 보고서": "연결 파일: territory_map_preview.html / territory_result_asset.json",
        "PDF 처방흐름 보고서": "연결 파일: prescription_flow_preview.html / prescription_claim_validation.xlsx",
        "RADAR Decision Brief": "연결 파일: radar_report_preview.html / radar_result_asset.json",
        "통합 검증 보고서": "연결 파일: data/ops_validation/{company}/builder/total_valid_preview.html",
    }
    return artifacts.get(report_type, "")


def get_report_output_path(report_type: str) -> str | None:
    root = get_project_root()
    builder_root = os.path.join(root, "data", "ops_validation", get_active_company_key(), "builder")
    mapping = {
        "CRM 행동 분석 보고서": os.path.join(builder_root, "crm_analysis_preview.html"),
        "Sandbox 성과 보고서": os.path.join(builder_root, "sandbox_report_preview.html"),
        "Territory 권역 지도 보고서": os.path.join(builder_root, "territory_map_preview.html"),
        "PDF 처방흐름 보고서": os.path.join(builder_root, "prescription_flow_preview.html"),
        "RADAR Decision Brief": os.path.join(builder_root, "radar_report_preview.html"),
        "통합 검증 보고서": os.path.join(builder_root, "total_valid_preview.html"),
    }
    return mapping.get(report_type)


def get_report_download_paths(report_type: str) -> list[tuple[str, str]]:
    root = get_project_root()
    company = get_active_company_key()
    prescription_root = os.path.join(root, "data", "ops_validation", company, "prescription")
    if report_type != "PDF 처방흐름 보고서":
        return []
    return [
        ("비교표 원본", os.path.join(prescription_root, "prescription_claim_validation.xlsx")),
        ("흐름 원본", os.path.join(prescription_root, "prescription_flow_records.xlsx")),
        ("미연결 원본", os.path.join(prescription_root, "prescription_gap_records.xlsx")),
        ("병원 추적 요약", os.path.join(prescription_root, "prescription_hospital_trace_quarter.xlsx")),
        ("담당자 KPI 요약", os.path.join(prescription_root, "prescription_rep_kpi_quarter.xlsx")),
    ]
