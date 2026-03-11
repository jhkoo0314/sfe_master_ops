from __future__ import annotations

import json
import random
import time
import uuid
from datetime import datetime
from pathlib import Path

from ops_core.workflow.execution_registry import (
    get_execution_mode_label,
    get_execution_mode_modules,
    get_mode_pipeline_steps as workflow_get_mode_pipeline_steps,
    get_mode_required_uploads,
)
from ops_core.workflow.execution_service import build_execution_context, run_execution_mode
from ui.console_paths import (
    get_active_company_key,
    get_active_company_name,
    get_project_root,
    get_source_target_map,
)


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
    for key, (target_path, _file_format) in source_targets.items():
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
    history_dir = Path(root) / "data" / "ops_validation" / get_active_company_key() / "pipeline"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_path = history_dir / "console_run_history.jsonl"

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
    return str(history_path)


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
    steps = []
    modules = ["crm", "prescription", "sandbox", "territory", "builder"]
    mode_label = get_execution_mode_label(execution_mode)
    crm_status = get_crm_package_status(uploaded)
    active_modules = get_execution_mode_modules(execution_mode)

    for index, module in enumerate(modules):
        time.sleep(0.1)
        status = "PASS"
        note = f"✅ {module} 평가 완료."

        if module not in active_modules:
            status = "SKIP"
            note = f"⏭️ 선택한 흐름에 {module} 단계가 없어 이번 실행에서는 건너뜁니다."
        elif module == "crm":
            if not crm_status["required_ready"]:
                status = "WARN"
                note = "⚠️ CRM 활동 원본 + 담당자 마스터가 모두 있어야 CRM 분석이 안정적으로 시작됩니다."
            elif not crm_status["assignment"] or not crm_status["rules"]:
                note = "✅ CRM 필수 패키지는 준비됨. 배정표/규칙표가 없어서 기본 규칙으로 진행합니다."
        elif module == "prescription":
            if uploaded.get("prescription") is None:
                status = "WARN"
                note = "⚠️ Prescription 흐름을 선택했지만 fact_ship 같은 원천데이터가 없어 분석이 제한됩니다."
        elif module == "sandbox":
            has_core = uploaded.get("sales") is not None or uploaded.get("target") is not None
            if not has_core:
                status = "WARN"
                note = "⚠️ 실적/목표 핵심 입력이 부족해서 샘플 기준의 Sandbox 판단만 가능합니다."
        elif module == "territory":
            if uploaded.get("crm_activity") is None:
                status = "WARN"
                note = "⚠️ Territory는 CRM 활동 데이터가 있어야 이동 흐름을 더 자연스럽게 볼 수 있습니다."
        elif module == "builder":
            note = "✅ 최종 결과물 생성 준비 완료."

        steps.append(
            {
                "step": index + 1,
                "module": module,
                "status": status,
                "score": round(random.uniform(70, 98), 1) if status != "SKIP" else 0,
                "reasoning_note": note,
                "next_modules": ["territory"] if module == "sandbox" and status == "PASS" else ["builder"] if module == "territory" and status == "PASS" else [],
                "duration_ms": random.randint(20, 150),
            }
        )

    active_scores = [step["score"] for step in steps if step["status"] != "SKIP"]
    overall = "WARN" if any(step["status"] == "WARN" for step in steps) else "PASS"
    return {
        "run_id": str(uuid.uuid4())[:8],
        "execution_mode": execution_mode,
        "execution_mode_label": mode_label,
        "overall_status": overall,
        "overall_score": round(sum(active_scores) / len(active_scores), 1) if active_scores else 0,
        "steps": steps,
        "final_eligible_modules": [module for module in ["territory", "builder"] if module in active_modules],
        "recommended_actions": [
            f"선택 흐름: {' -> '.join(get_execution_mode_modules(execution_mode)).upper()}",
            "현재는 검증 단계라 선택한 흐름만 순차적으로 점검합니다.",
        ],
        "total_duration_ms": sum(step["duration_ms"] for step in steps),
    }
