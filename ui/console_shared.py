import io
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
import time

import pandas as pd
import streamlit as st
from common.company_profile import get_company_ops_profile
from common.company_runtime import get_active_company_key as env_company_key, get_active_company_name as env_company_name
from ops_core.workflow.execution_registry import (
    get_execution_mode_description as workflow_get_execution_mode_description,
    get_execution_mode_label as workflow_get_execution_mode_label,
    get_execution_mode_modules as workflow_get_execution_mode_modules,
    get_execution_mode_requirements as workflow_get_execution_mode_requirements,
    get_mode_pipeline_steps as workflow_get_mode_pipeline_steps,
    get_mode_required_uploads as workflow_get_mode_required_uploads,
)
from ops_core.workflow.execution_service import build_execution_context, run_execution_mode


def init_console_state() -> None:
    if "pipeline_result" not in st.session_state:
        st.session_state.pipeline_result = None
    if "uploaded_data" not in st.session_state:
        st.session_state.uploaded_data = {
            "crm_activity": None,
            "crm_rep_master": None,
            "crm_account_assignment": None,
            "crm_rules": None,
            "sales": None,
            "target": None,
            "prescription": None,
        }
    if "uploaded_tokens" not in st.session_state:
        st.session_state.uploaded_tokens = {
            "crm_activity": None,
            "crm_rep_master": None,
            "crm_account_assignment": None,
            "crm_rules": None,
            "sales": None,
            "target": None,
            "prescription": None,
        }
    if "run_log" not in st.session_state:
        st.session_state.run_log = []
    if "module_status" not in st.session_state:
        st.session_state.module_status = {
            "crm": "미실행",
            "prescription": "미실행",
            "sandbox": "미실행",
            "territory": "미실행",
            "builder": "미실행",
        }
    if "execution_mode" not in st.session_state:
        st.session_state.execution_mode = "crm_to_sandbox"
    if "company_key" not in st.session_state:
        st.session_state.company_key = env_company_key()
    if "company_name" not in st.session_state:
        st.session_state.company_name = env_company_name(st.session_state.company_key)


def add_log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.run_log.append(f"[{ts}] {msg}")


@st.cache_data(show_spinner=False)
def load_uploaded_dataframe(file_name: str, file_bytes: bytes) -> pd.DataFrame:
    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    return pd.read_excel(io.BytesIO(file_bytes))


def get_file_token(uploaded_file) -> str:
    file_size = getattr(uploaded_file, "size", None)
    if file_size is None:
        file_size = len(uploaded_file.getvalue())
    return f"{uploaded_file.name}:{file_size}"


def load_file_once(module_key: str, uploaded_file, label: str) -> dict:
    token = get_file_token(uploaded_file)
    existing = st.session_state.uploaded_data.get(module_key)
    if st.session_state.uploaded_tokens.get(module_key) == token and existing is not None:
        return existing

    file_bytes = uploaded_file.getvalue()
    df = load_uploaded_dataframe(uploaded_file.name, file_bytes)
    info = {
        "name": uploaded_file.name,
        "row_count": int(len(df)),
        "columns": list(df.columns),
        "preview": df.head(3).to_dict("records"),
        "file_bytes": file_bytes,
        "file_ext": os.path.splitext(uploaded_file.name)[1].lower(),
    }
    st.session_state.uploaded_data[module_key] = info
    st.session_state.uploaded_tokens[module_key] = token
    add_log(f"{label} 데이터 {len(df)}건 업로드")
    return info


def render_page_hero(title: str, subtitle: str, badge: str | None = None) -> None:
    badge_html = f'<span class="app-badge">{badge}</span>' if badge else ""
    st.markdown(
        f"""
        <div class="page-hero">
          <div>
            <div class="hero-kicker">SFE MASTER OPS</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
          <div>{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_panel_header(title: str, description: str = "") -> None:
    desc_html = f"<p>{description}</p>" if description else ""
    st.markdown(
        f"""
        <div class="panel-header">
          <h3>{title}</h3>
          {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_block_card(title: str, description: str, eyebrow: str = "") -> None:
    eyebrow_html = f'<div class="block-eyebrow">{eyebrow}</div>' if eyebrow else ""
    st.markdown(
        f"""
        <div class="block-card">
          {eyebrow_html}
          <h4>{title}</h4>
          <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upload_row(
    module_key: str,
    uploader_key: str,
    title: str,
    required_level: str,
    short_desc: str,
    sample_path: str,
    examples: list[str],
    notes: list[str],
    upload_label: str,
) -> None:
    level_colors = {
        "필수": ("rgba(248,81,73,0.10)", "#f85149"),
        "권장": ("rgba(210,153,34,0.12)", "#d29922"),
        "선택": ("rgba(88,166,255,0.10)", "#58a6ff"),
    }
    bg, fg = level_colors.get(required_level, ("rgba(139,148,158,0.16)", "#e6edf3"))
    current = st.session_state.uploaded_data.get(module_key)

    left, mid, right = st.columns([1.2, 2.4, 1.6])
    with left:
        st.markdown(
            f"""
            <div style="padding-top:6px">
              <div style="display:inline-flex;align-items:center;padding:4px 10px;border-radius:999px;background:{bg};color:{fg};font-size:11px;font-weight:800;margin-bottom:8px;">{required_level}</div>
              <div style="font-weight:800;font-size:15px;">{title}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with mid:
        status_text = f"업로드됨 · {current['name']} · {current['row_count']}건" if current else "업로드 전"
        st.markdown(
            f"""
            <div style="padding-top:6px">
              <div style="font-size:13px;font-weight:700;">{short_desc}</div>
              <div style="font-size:12px;color:#8b949e;margin-top:4px;">샘플: <code>{sample_path}</code></div>
              <div style="font-size:12px;color:#8b949e;margin-top:4px;">상태: {status_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("예시", expanded=False):
            for item in examples:
                st.markdown(f"- {item}")
            st.markdown("**체크 포인트**")
            for item in notes:
                st.markdown(f"- {item}")
    with right:
        uploaded_file = st.file_uploader(upload_label, type=["csv", "xlsx"], key=uploader_key, label_visibility="collapsed")
        if uploaded_file:
            try:
                info = load_file_once(module_key, uploaded_file, title)
                st.success(f"{info['row_count']}건")
            except Exception as exc:
                st.error(f"오류: {exc}")

    latest = st.session_state.uploaded_data.get(module_key)
    if latest:
        with st.expander(f"{title} 미리보기", expanded=False):
            st.dataframe(pd.DataFrame(latest["preview"]), use_container_width=True, hide_index=True)
    st.markdown("<div style='margin:8px 0 14px;border-top:1px solid rgba(48,54,61,0.8);'></div>", unsafe_allow_html=True)


def get_execution_mode_label(mode: str) -> str:
    return workflow_get_execution_mode_label(mode)


def get_execution_mode_description(mode: str) -> str:
    return workflow_get_execution_mode_description(mode)


def get_execution_mode_requirements(mode: str) -> str:
    return workflow_get_execution_mode_requirements(mode)


def get_execution_mode_modules(mode: str) -> list[str]:
    return workflow_get_execution_mode_modules(mode)


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_active_company_key() -> str:
    return st.session_state.get("company_key", env_company_key())


def get_active_company_name() -> str:
    return st.session_state.get("company_name", env_company_name(get_active_company_key()))


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


def render_stage_badge(label: str, value: str) -> str:
    palette = {
        "정규화": ("rgba(88,166,255,0.10)", "#58a6ff"),
        "검증결과": ("rgba(63,185,80,0.10)", "#3fb950"),
        "Builder": ("rgba(210,153,34,0.12)", "#d29922"),
        "원천": ("rgba(248,81,73,0.10)", "#f85149"),
    }
    bg, fg = palette.get(label, ("rgba(139,148,158,0.16)", "#e6edf3"))
    return (
        f"<span style=\"display:inline-flex;align-items:center;padding:4px 10px;border-radius:999px;"
        f"background:{bg};color:{fg};font-size:11px;font-weight:800;margin-right:8px;\">"
        f"{label} · {value}</span>"
    )


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
        "통합 검증 보고서",
    ]


def get_report_type_description(report_type: str) -> str:
    descriptions = {
        "CRM 행동 분석 보고서": "CRM 활동 raw를 바탕으로 행동 품질, 신뢰도, 파이프라인 흐름, 담당자별 CoachScore를 보는 CRM 전용 HTML 보고서입니다.",
        "Sandbox 성과 보고서": "실적, 목표, CRM을 묶어 성과 분석 결과를 보여주는 HTML 보고서입니다.",
        "Territory 권역 지도 보고서": "권역별 커버리지와 이동 흐름을 지도 중심으로 보는 HTML 보고서입니다.",
        "PDF 처방흐름 보고서": "Prescription Data Flow 비교표와 추적 보조표를 중심으로 보는 HTML 보고서입니다.",
        "통합 검증 보고서": "HTML Builder 화면을 열어 Sandbox, CRM, Territory, Prescription 결과를 한 곳에서 미리보는 통합 진입 보고서입니다.",
    }
    return descriptions.get(report_type, "")


def get_report_type_artifacts(report_type: str) -> str:
    artifacts = {
        "CRM 행동 분석 보고서": "연결 파일: crm_analysis_preview.html / crm_result_asset.json",
        "Sandbox 성과 보고서": "연결 파일: sandbox_report_preview.html / sandbox_result_asset.json",
        "Territory 권역 지도 보고서": "연결 파일: territory_map_preview.html / territory_result_asset.json",
        "PDF 처방흐름 보고서": "연결 파일: prescription_flow_preview.html / prescription_claim_validation.xlsx",
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


def get_crm_package_status(uploaded: dict) -> dict:
    activity = uploaded.get("crm_activity") is not None
    rep_master = uploaded.get("crm_rep_master") is not None
    assignment = uploaded.get("crm_account_assignment") is not None
    rules = uploaded.get("crm_rules") is not None
    required_ready = activity and rep_master
    package_count = sum([activity, rep_master, assignment, rules])
    return {
        "activity": activity,
        "rep_master": rep_master,
        "assignment": assignment,
        "rules": rules,
        "required_ready": required_ready,
        "package_count": package_count,
    }


def get_source_target_map() -> dict[str, tuple[str, str]]:
    root = Path(get_project_root())
    company_key = get_active_company_key()
    profile = get_company_ops_profile(company_key)
    return profile.resolved_source_targets(root, company_key)


def get_source_target_display_path(source_key: str) -> str:
    root = Path(get_project_root())
    company_key = get_active_company_key()
    profile = get_company_ops_profile(company_key)
    relative_path, _ = profile.source_targets[source_key]
    return str(Path("data") / "company_source" / company_key / Path(relative_path))


def get_source_target_rows(execution_mode: str, uploaded: dict) -> list[dict]:
    label_map = {
        "crm_activity": "CRM 활동 원본",
        "crm_rep_master": "담당자 / 조직 마스터",
        "crm_account_assignment": "거래처 / 병원 담당 배정",
        "crm_rules": "CRM 규칙 / KPI 설정",
        "sales": "실적(매출) 데이터",
        "target": "목표 데이터",
        "prescription": "Prescription 데이터",
    }
    rows = []
    source_targets = get_source_target_map()
    required_keys = set(get_mode_required_uploads(execution_mode))
    for key, (target_path, _) in source_targets.items():
        info = uploaded.get(key)
        if key not in required_keys and info is None:
            continue
        rows.append(
            {
                "항목": label_map.get(key, key),
                "실행 필요": "필수" if key in required_keys else "선택",
                "현재 소스": info["name"] if info else "기존 파일 사용",
                "실제 반영 경로": target_path,
                "반영 방식": "업로드 파일 덮어쓰기" if info else "기존 source 유지",
            }
        )
    return rows


def save_pipeline_run_history(result: dict, uploaded: dict) -> str:
    root = get_project_root()
    history_dir = os.path.join(root, "data", "ops_validation", get_active_company_key(), "pipeline")
    Path(history_dir).mkdir(parents=True, exist_ok=True)
    history_path = os.path.join(history_dir, "console_run_history.jsonl")
    record = {
        "saved_at": datetime.now().isoformat(),
        "run_id": result.get("run_id"),
        "execution_mode": result.get("execution_mode"),
        "execution_mode_label": result.get("execution_mode_label"),
        "company_key": get_active_company_key(),
        "company_name": get_active_company_name(),
        "overall_status": result.get("overall_status"),
        "overall_score": result.get("overall_score"),
        "total_duration_ms": result.get("total_duration_ms"),
        "steps": result.get("steps", []),
        "input_files": {
            key: {
                "uploaded_name": value.get("name"),
                "row_count": value.get("row_count"),
            }
            for key, value in uploaded.items()
            if value is not None
        },
        "source_targets": get_source_target_rows(result.get("execution_mode", "crm_to_sandbox"), uploaded),
    }
    with open(history_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return history_path


def get_mode_required_uploads(execution_mode: str) -> list[str]:
    return workflow_get_mode_required_uploads(execution_mode)


def get_mode_pipeline_steps(execution_mode: str) -> list[dict]:
    return [
        {"module": step.module, "label": step.label, "fn": step.runner}
        for step in workflow_get_mode_pipeline_steps(execution_mode)
    ]


def run_actual_pipeline(execution_mode: str, uploaded: dict) -> dict:
    context = build_execution_context(
        project_root=get_project_root(),
        company_key=get_active_company_key(),
        company_name=get_active_company_name(),
        source_targets=get_source_target_map(),
    )
    return run_execution_mode(
        context=context,
        execution_mode=execution_mode,
        uploaded=uploaded,
    ).to_dict()


def run_mock_pipeline(execution_mode: str, uploaded: dict) -> dict:
    import random
    import time

    steps = []
    modules = ["crm", "prescription", "sandbox", "territory", "builder"]
    mode_label = get_execution_mode_label(execution_mode)
    crm_status = get_crm_package_status(uploaded)
    active_modules = get_execution_mode_modules(execution_mode)

    for i, mod in enumerate(modules):
        time.sleep(0.1)
        s = "PASS"
        note = f"✅ {mod} 평가 완료."

        if mod not in active_modules:
            s = "SKIP"
            note = f"⏭️ 선택한 흐름에 {mod} 단계가 없어 이번 실행에서는 건너뜁니다."
        elif mod == "crm":
            if not crm_status["required_ready"]:
                s = "WARN"
                note = "⚠️ CRM 활동 원본 + 담당자 마스터가 모두 있어야 CRM 분석이 안정적으로 시작됩니다."
            elif not crm_status["assignment"] or not crm_status["rules"]:
                note = "✅ CRM 필수 패키지는 준비됨. 배정표/규칙표가 없어서 기본 규칙으로 진행합니다."
        elif mod == "prescription":
            if uploaded.get("prescription") is None:
                s = "WARN"
                note = "⚠️ Prescription 흐름을 선택했지만 fact_ship 같은 원천데이터가 없어 분석이 제한됩니다."
        elif mod == "sandbox":
            has_core = uploaded.get("sales") is not None or uploaded.get("target") is not None
            if not has_core:
                s = "WARN"
                note = "⚠️ 실적/목표 핵심 입력이 부족해서 샘플 기준의 Sandbox 판단만 가능합니다."
        elif mod == "territory":
            if uploaded.get("crm_activity") is None:
                s = "WARN"
                note = "⚠️ Territory는 CRM 활동 데이터가 있어야 이동 흐름을 더 자연스럽게 볼 수 있습니다."
        elif mod == "builder":
            note = "✅ 최종 결과물 생성 준비 완료."

        steps.append(
            {
                "step": i + 1,
                "module": mod,
                "status": s,
                "score": round(random.uniform(70, 98), 1) if s != "SKIP" else 0,
                "reasoning_note": note,
                "next_modules": ["territory"] if mod == "sandbox" and s == "PASS" else ["builder"] if mod == "territory" and s == "PASS" else [],
                "duration_ms": random.randint(20, 150),
            }
        )

    active_scores = [s["score"] for s in steps if s["status"] != "SKIP"]
    overall = "WARN" if any(s["status"] == "WARN" for s in steps) else "PASS"
    return {
        "run_id": str(uuid.uuid4())[:8],
        "execution_mode": execution_mode,
        "execution_mode_label": mode_label,
        "overall_status": overall,
        "overall_score": round(sum(active_scores) / len(active_scores), 1) if active_scores else 0,
        "steps": steps,
        "final_eligible_modules": [m for m in ["territory", "builder"] if m in active_modules],
        "recommended_actions": [
            f"선택 흐름: {' -> '.join(get_execution_mode_modules(execution_mode)).upper()}",
            "현재는 검증 단계라 선택한 흐름만 순차적으로 점검합니다.",
        ],
        "total_duration_ms": sum(s["duration_ms"] for s in steps),
    }
