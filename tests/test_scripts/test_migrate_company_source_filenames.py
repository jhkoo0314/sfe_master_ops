from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.migrate_company_source_filenames import migrate_company_source


def test_migrate_company_source_renames_legacy_files(tmp_path):
    company_root = tmp_path / "daon_pharma"
    legacy_file = company_root / "crm" / "hangyeol_crm_activity_raw.xlsx"
    legacy_file.parent.mkdir(parents=True, exist_ok=True)
    legacy_file.write_text("legacy", encoding="utf-8")

    summary = migrate_company_source(company_root)

    new_file = company_root / "crm" / "crm_activity_raw.xlsx"
    assert new_file.exists()
    assert new_file.read_text(encoding="utf-8") == "legacy"
    assert summary["renamed"][0]["to"].endswith(str(Path("crm") / "crm_activity_raw.xlsx"))
