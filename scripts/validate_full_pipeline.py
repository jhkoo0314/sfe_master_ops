from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.company_profile import get_company_ops_profile
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root
from ops_core.workflow.execution_registry import get_execution_mode_modules
from ops_core.workflow.execution_service import build_execution_context, run_execution_mode
from scripts.generate_source_raw import main as generate_source_main


def main() -> None:
    company_key = get_active_company_key()
    company_name = get_active_company_name(company_key)
    profile = get_company_ops_profile(company_key)
    output_root = get_company_root(ROOT, "ops_validation", company_key) / "pipeline"
    output_root.mkdir(parents=True, exist_ok=True)

    generation_note = None
    if profile.raw_generator_module:
        try:
            generate_source_main()
        except FileNotFoundError as exc:
            generation_note = f"raw 생성용 샘플 파일이 없어 생성 단계는 건너뛰었습니다: {exc}"
        except Exception as exc:
            generation_note = f"raw 생성 단계는 건너뛰고 기존 source 파일을 사용했습니다: {exc}"
    else:
        generation_note = "등록된 raw 생성 모듈이 없어 기존 source 파일을 그대로 사용했습니다."

    context = build_execution_context(
        project_root=ROOT,
        company_key=company_key,
        company_name=company_name,
    )
    result = run_execution_mode(
        context=context,
        execution_mode="integrated_full",
    )

    pipeline_summary = {
        "company": company_name,
        "company_key": company_key,
        "execution_mode": result.execution_mode,
        "execution_mode_label": result.execution_mode_label,
        "overall_status": result.overall_status,
        "overall_score": result.overall_score,
        "total_duration_ms": result.total_duration_ms,
        "stages": {
            module: result.summary_by_module.get(module, {})
            for module in get_execution_mode_modules("integrated_full")
        },
        "steps": [step.to_dict() for step in result.steps],
        "generation_note": generation_note,
        "all_passed": result.overall_status == "PASS",
    }

    (output_root / "pipeline_validation_summary.json").write_text(
        json.dumps(pipeline_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Validated {company_name} full pipeline:")
    print(json.dumps(pipeline_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
