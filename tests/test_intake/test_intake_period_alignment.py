from pathlib import Path
import shutil
import sys
from uuid import uuid4

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.intake import build_intake_result, load_intake_result_snapshot


def _make_temp_dir() -> Path:
    temp_dir = ROOT / "tests" / "_tmp_priority1" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_intake_detects_period_gap_and_common_analysis_window():
    tmp_path = _make_temp_dir()
    try:
        company_key = "demo_company"
        source_root = tmp_path / "data" / "company_source" / company_key
        crm_path = source_root / "crm" / "crm_activity_raw.xlsx"
        sales_path = source_root / "sales" / "sales_raw.xlsx"
        target_path = source_root / "target" / "target_raw.xlsx"

        crm_path.parent.mkdir(parents=True, exist_ok=True)
        sales_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        pd.DataFrame(
            {
                "activity_date": pd.to_datetime(
                    ["2026-01-05", "2026-02-05", "2026-03-05", "2026-04-05", "2026-05-05", "2026-06-05"]
                ),
                "rep_id": ["REP001"] * 6,
                "hospital_id": ["H001"] * 6,
                "activity_type": ["방문"] * 6,
            }
        ).to_excel(crm_path, index=False)
        pd.DataFrame(
            {
                "hospital_id": ["H001"] * 6,
                "product_id": ["P001"] * 6,
                "sales_amount": [10, 20, 30, 40, 50, 60],
                "yyyymm": ["202601", "202602", "202603", "202604", "202605", "202606"],
            }
        ).to_excel(sales_path, index=False)
        pd.DataFrame(
            {
                "target_amount": [100] * 8,
                "yyyymm": ["202601", "202602", "202603", "202604", "202605", "202606", "202607", "202608"],
            }
        ).to_excel(target_path, index=False)

        result = build_intake_result(
            project_root=tmp_path,
            company_key=company_key,
            company_name="Demo Company",
            source_targets={
                "crm_activity": (str(crm_path), "excel"),
                "sales": (str(sales_path), "excel"),
                "target": (str(target_path), "excel"),
            },
            execution_mode="crm_to_sandbox",
        )

        assert result.analysis_month_count == 6
        assert result.analysis_start_month == "202601"
        assert result.analysis_end_month == "202606"
        assert result.proceed_confirmation_message is not None
        assert "6개월" in result.proceed_confirmation_message
        assert len(result.timing_alerts) == 1
        assert result.timing_alerts[0].source_key == "target"
        assert result.timing_alerts[0].direction == "ahead"
        assert result.timing_alerts[0].month_gap == 2
        target_package = next(package for package in result.packages if package.source_key == "target")
        assert target_package.period_coverage is not None
        assert target_package.period_coverage.end_month == "202608"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_intake_snapshot_keeps_cache_signature():
    tmp_path = _make_temp_dir()
    try:
        company_key = "demo_company"
        sales_path = tmp_path / "data" / "company_source" / company_key / "sales" / "sales_raw.xlsx"
        sales_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            {
                "hospital_id": ["H001"],
                "product_id": ["P001"],
                "sales_amount": [10],
                "yyyymm": ["202601"],
            }
        ).to_excel(sales_path, index=False)

        result = build_intake_result(
            project_root=tmp_path,
            company_key=company_key,
            company_name="Demo Company",
            source_targets={"sales": (str(sales_path), "excel")},
            execution_mode="sandbox_to_html",
            cache_signature="demo-signature",
        )

        snapshot = load_intake_result_snapshot(tmp_path, company_key)

        assert result.cache_signature == "demo-signature"
        assert snapshot is not None
        assert snapshot["cache_signature"] == "demo-signature"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)
