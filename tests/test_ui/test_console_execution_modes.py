from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ui.console_shared as console_shared
from ops_core.workflow.execution_registry import (
    get_execution_mode_description,
    get_execution_mode_label,
    get_execution_mode_modules,
    get_execution_mode_requirements,
    get_mode_pipeline_steps,
    get_mode_required_uploads,
)
from ui.console_shared import (
    get_source_target_display_path,
    get_source_target_map,
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
    assert steps[0].module == "crm"
    assert steps[1].module == "territory"
    assert "정규화" in steps[1].label


def test_source_target_map_uses_company_profile(monkeypatch):
    monkeypatch.setattr(console_shared, "get_project_root", lambda: str(ROOT))
    monkeypatch.setattr(console_shared, "get_active_company_key", lambda: "daon_pharma")

    source_targets = get_source_target_map()

    assert source_targets["crm_activity"][0].endswith(
        str(Path("data") / "company_source" / "daon_pharma" / "crm" / "crm_activity_raw.xlsx")
    )
    assert get_source_target_display_path("sales") == str(
        Path("data") / "company_source" / "daon_pharma" / "sales" / "sales_raw.xlsx"
    )
