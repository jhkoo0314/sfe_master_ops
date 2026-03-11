from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.console_shared import (
    get_execution_mode_description,
    get_execution_mode_label,
    get_execution_mode_modules,
    get_execution_mode_requirements,
    get_mode_pipeline_steps,
    get_mode_required_uploads,
)


def test_crm_to_territory_mode_metadata():
    assert get_execution_mode_label("crm_to_territory") == "CRM -> Territory"
    assert get_execution_mode_modules("crm_to_territory") == ["crm", "territory"]
    assert "권역 분석" in get_execution_mode_description("crm_to_territory")
    assert "거래처 담당 배정" in get_execution_mode_requirements("crm_to_territory")


def test_crm_to_territory_mode_required_uploads():
    assert get_mode_required_uploads("crm_to_territory") == [
        "crm_activity",
        "crm_rep_master",
        "crm_account_assignment",
        "sales",
        "target",
    ]


def test_crm_to_territory_mode_pipeline_steps():
    steps = get_mode_pipeline_steps("crm_to_territory")

    assert len(steps) == 2
    assert steps[0]["module"] == "crm"
    assert steps[1]["module"] == "territory"
    assert "정규화" in steps[1]["label"]
