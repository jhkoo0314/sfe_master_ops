from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.company_profile import get_company_ops_profile


def test_daon_profile_uses_company_specific_generator():
    profile = get_company_ops_profile("daon_pharma")

    assert profile.company_key == "daon_pharma"
    assert profile.source_path(Path("C:/tmp/company_source/daon_pharma"), "crm_activity") == (
        Path("C:/tmp/company_source/daon_pharma") / "crm" / "crm_activity_raw.xlsx"
    )


def test_unknown_company_uses_hangyeol_compatible_defaults():
    profile = get_company_ops_profile("custom_pharma")

    resolved = profile.resolved_source_targets(Path("C:/project"), "custom_pharma")

    assert resolved["prescription"][0].endswith(
        str(Path("data") / "company_source" / "custom_pharma" / "company" / "fact_ship_raw.csv")
    )
