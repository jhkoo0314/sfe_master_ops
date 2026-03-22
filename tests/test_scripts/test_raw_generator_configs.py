from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.raw_generators import get_raw_generation_config, list_raw_generation_configs


def test_raw_generation_configs_cover_current_companies():
    daon = get_raw_generation_config("daon_pharma")
    hangyeol = get_raw_generation_config("hangyeol_pharma")
    monthly_merge = get_raw_generation_config("monthly_merge_pharma")
    tera = get_raw_generation_config("tera_pharma")

    assert daon is not None
    assert daon.template_type == "daon_like"
    assert daon.output_mode == "merged_only"

    assert hangyeol is not None
    assert hangyeol.template_type == "hangyeol_like"
    assert hangyeol.output_mode == "merged_only"

    assert monthly_merge is not None
    assert monthly_merge.template_type == "daon_like"
    assert monthly_merge.output_mode == "monthly_and_merged"

    assert tera is not None
    assert tera.template_type == "daon_like"
    assert tera.branch_count == 6
    assert tera.clinic_rep_count == 30
    assert tera.hospital_rep_count == 30


def test_list_raw_generation_configs_returns_current_registry():
    config_keys = {config.company_key for config in list_raw_generation_configs()}

    assert {"daon_pharma", "hangyeol_pharma", "monthly_merge_pharma", "tera_pharma"} <= config_keys
