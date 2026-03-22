from pathlib import Path
import json
import shutil
import sys
from uuid import uuid4

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.raw_generators.writers import (
    write_csv_table,
    write_json_summary,
    write_monthly_outputs,
    write_source_outputs,
)


def _make_temp_dir() -> Path:
    temp_dir = ROOT / "tests" / "_tmp_priority1" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_write_source_outputs_and_summaries():
    tmp_path = _make_temp_dir()
    try:
        output_paths = {
            "sales": tmp_path / "sales" / "sales_raw.xlsx",
            "prescription": tmp_path / "company" / "fact_ship_raw.csv",
        }
        write_source_outputs(
            {
                "sales": pd.DataFrame({"기준년월": ["202501"], "매출금액": [100]}),
                "prescription": pd.DataFrame({"ship_date (출고일)": ["2025-01-01"], "qty (수량)": [1]}),
            },
            output_paths,
        )
        write_json_summary(tmp_path / "generation_summary.json", {"company_key": "demo"})
        write_csv_table(tmp_path / "breakdown.csv", pd.DataFrame({"yyyymm": ["202501"], "crm_rows": [10]}))

        assert output_paths["sales"].exists()
        assert output_paths["prescription"].exists()
        assert json.loads((tmp_path / "generation_summary.json").read_text(encoding="utf-8"))["company_key"] == "demo"
        assert (tmp_path / "breakdown.csv").exists()
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_write_monthly_outputs_creates_expected_files():
    tmp_path = _make_temp_dir()
    try:
        write_monthly_outputs(
            tmp_path,
            "202501",
            {
                "crm_activity": pd.DataFrame({"실행일": ["2025-01-01"]}),
                "target": pd.DataFrame({"기준년월": ["202501"]}),
                "sales": pd.DataFrame({"기준년월": ["202501"]}),
                "prescription": pd.DataFrame({"ship_date (출고일)": ["2025-01-01"]}),
            },
        )

        month_dir = tmp_path / "202501"
        assert (month_dir / "crm_activity_raw.xlsx").exists()
        assert (month_dir / "target_raw.xlsx").exists()
        assert (month_dir / "sales_raw.xlsx").exists()
        assert (month_dir / "fact_ship_raw.csv").exists()
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)
