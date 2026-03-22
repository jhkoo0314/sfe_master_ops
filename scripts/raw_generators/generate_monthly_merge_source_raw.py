from __future__ import annotations

from pathlib import Path
import random
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.company_runtime import get_active_company_key, get_active_company_name
from common.company_profile import get_company_ops_profile
from scripts.raw_generators import generate_daon_source_raw as daon


COMPANY_KEY = get_active_company_key("monthly_merge_pharma")
COMPANY_NAME = get_active_company_name("월별검증제약")
START_MONTH = "2025-01"
END_MONTH = "2025-06"
CLINIC_REP_COUNT = 50
HOSPITAL_REP_COUNT = 25
SEED = 20260322


def _fill_missing_rep_assignments(account_master: pd.DataFrame, rep_df: pd.DataFrame) -> pd.DataFrame:
    result = account_master.copy()
    rep_id_blank = result["rep_id"].isna() | result["rep_id"].astype(str).str.strip().eq("")
    rep_name_blank = result["rep_name"].isna() | result["rep_name"].astype(str).str.strip().eq("")
    missing_mask = rep_id_blank | rep_name_blank
    if not bool(missing_mask.any()):
        return result

    clinic_reps = rep_df[rep_df["rep_role"] == "의원"].reset_index(drop=True)
    hospital_reps = rep_df[rep_df["rep_role"] == "종합병원"].reset_index(drop=True)
    clinic_idx = 0
    hospital_idx = 0

    missing_indices = list(result.index[missing_mask])
    for row_idx in missing_indices:
        account_type = str(result.at[row_idx, "account_type"])
        role_reps = clinic_reps if account_type == "의원" else hospital_reps
        if role_reps.empty:
            continue

        branch_name = str(result.at[row_idx, "branch_name"])
        same_branch = role_reps[role_reps["branch_name"] == branch_name]
        if not same_branch.empty:
            selected = same_branch.iloc[0]
        elif account_type == "의원":
            selected = role_reps.iloc[clinic_idx % len(role_reps)]
            clinic_idx += 1
        else:
            selected = role_reps.iloc[hospital_idx % len(role_reps)]
            hospital_idx += 1

        result.at[row_idx, "rep_id"] = selected["rep_id"]
        result.at[row_idx, "rep_name"] = selected["rep_name"]
        result.at[row_idx, "channel_focus"] = selected["channel_focus"]
        result.at[row_idx, "product_focus_group"] = selected["product_focus_group"]
    return result


def _configure_base() -> Path:
    daon.COMPANY_KEY = COMPANY_KEY
    daon.COMPANY_NAME = COMPANY_NAME
    daon.PROFILE = get_company_ops_profile(COMPANY_KEY)
    daon.OUTPUT_ROOT = ROOT / "data" / "company_source" / COMPANY_KEY
    daon.CLINIC_REP_COUNT = CLINIC_REP_COUNT
    daon.HOSPITAL_REP_COUNT = HOSPITAL_REP_COUNT
    daon.SEED = SEED
    preferred = ROOT / "docs" / "part1" / "hangyeol-pharma-portfolio-draft.csv"
    fallback = ROOT / "docs" / "hangyeol-pharma-portfolio-draft.csv"
    daon.PORTFOLIO_PATH = preferred if preferred.exists() else fallback
    random.seed(SEED)
    np.random.seed(SEED)
    monthly_root = daon.OUTPUT_ROOT / "monthly_raw"
    monthly_root.mkdir(parents=True, exist_ok=True)
    return monthly_root


def _save_monthly_files(
    monthly_root: Path,
    yyyymm: str,
    crm_raw: pd.DataFrame,
    target_raw: pd.DataFrame,
    sales_raw: pd.DataFrame,
    ship_raw: pd.DataFrame,
) -> None:
    month_dir = monthly_root / yyyymm
    month_dir.mkdir(parents=True, exist_ok=True)
    crm_raw.to_excel(month_dir / "crm_activity_raw.xlsx", index=False)
    target_raw.to_excel(month_dir / "target_raw.xlsx", index=False)
    sales_raw.to_excel(month_dir / "sales_raw.xlsx", index=False)
    ship_raw.to_csv(month_dir / "fact_ship_raw.csv", index=False, encoding="utf-8-sig")


def _month_bounds(month: pd.Period) -> tuple[str, str]:
    start = month.to_timestamp(how="start")
    end = month.to_timestamp(how="end").normalize()
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def main() -> None:
    monthly_root = _configure_base()
    months = pd.period_range(START_MONTH, END_MONTH, freq="M")

    portfolio = daon.load_portfolio()
    hospital_pool = daon.load_hospital_pool()
    clinic_df, hospital_df = daon.select_accounts(hospital_pool)
    rep_df = daon.build_rep_master(clinic_df, hospital_df)
    account_master = daon.build_account_master(rep_df, clinic_df, hospital_df)
    account_master = _fill_missing_rep_assignments(account_master, rep_df)
    assignment_raw = daon.build_company_assignment(account_master, rep_df)

    monthly_crm: list[pd.DataFrame] = []
    monthly_target: list[pd.DataFrame] = []
    monthly_sales: list[pd.DataFrame] = []
    monthly_ship: list[pd.DataFrame] = []
    monthly_rows: list[dict[str, int | str]] = []

    for idx, month in enumerate(months, start=1):
        month_seed = SEED + idx
        random.seed(month_seed)
        np.random.seed(month_seed)

        start_date, end_date = _month_bounds(month)
        daon.START_DATE = start_date
        daon.END_DATE = end_date

        crm_raw = daon.generate_crm_raw(account_master, portfolio)
        target_raw_full, sales_raw_full = daon.generate_target_and_sales(account_master, portfolio)
        yyyymm = month.strftime("%Y%m")
        target_raw = target_raw_full[target_raw_full["기준년월"] == yyyymm].reset_index(drop=True)
        sales_raw = sales_raw_full[sales_raw_full["기준년월"] == yyyymm].reset_index(drop=True)
        ship_raw = daon.generate_fact_ship(account_master, sales_raw, portfolio)

        monthly_crm.append(crm_raw)
        monthly_target.append(target_raw)
        monthly_sales.append(sales_raw)
        monthly_ship.append(ship_raw)
        _save_monthly_files(monthly_root, yyyymm, crm_raw, target_raw, sales_raw, ship_raw)

        monthly_rows.append(
            {
                "yyyymm": yyyymm,
                "crm_rows": int(len(crm_raw)),
                "target_rows": int(len(target_raw)),
                "sales_rows": int(len(sales_raw)),
                "fact_ship_rows": int(len(ship_raw)),
            }
        )

    merged_crm = pd.concat(monthly_crm, ignore_index=True)
    merged_target = pd.concat(monthly_target, ignore_index=True)
    merged_sales = pd.concat(monthly_sales, ignore_index=True)
    merged_ship = pd.concat(monthly_ship, ignore_index=True)

    daon.write_outputs(
        rep_df=rep_df,
        account_master=account_master,
        assignment_raw=assignment_raw,
        crm_raw=merged_crm,
        target_raw=merged_target,
        sales_raw=merged_sales,
        ship_raw=merged_ship,
    )

    month_summary_df = pd.DataFrame(monthly_rows)
    monthly_sum = {
        "crm_rows": int(month_summary_df["crm_rows"].sum()),
        "target_rows": int(month_summary_df["target_rows"].sum()),
        "sales_rows": int(month_summary_df["sales_rows"].sum()),
        "fact_ship_rows": int(month_summary_df["fact_ship_rows"].sum()),
    }
    merged_sum = {
        "crm_rows": int(len(merged_crm)),
        "target_rows": int(len(merged_target)),
        "sales_rows": int(len(merged_sales)),
        "fact_ship_rows": int(len(merged_ship)),
    }

    validation = {k: monthly_sum[k] == merged_sum[k] for k in monthly_sum}
    summary = {
        "company_key": COMPANY_KEY,
        "company_name": COMPANY_NAME,
        "scenario": "monthly_raw_generation_and_merge_validation",
        "month_range": [START_MONTH, END_MONTH],
        "month_count": int(len(months)),
        "branch_count": int(len(daon.BRANCH_DEFS)),
        "rep_count": int(len(rep_df)),
        "clinic_rep_count": int((rep_df["rep_role"] == "의원").sum()),
        "hospital_rep_count": int((rep_df["rep_role"] == "종합병원").sum()),
        "monthly_sum_rows": monthly_sum,
        "merged_rows": merged_sum,
        "row_count_validation": validation,
        "output_root": str(daon.OUTPUT_ROOT),
    }

    (daon.OUTPUT_ROOT / "monthly_generation_plan_summary.json").write_text(
        pd.Series(summary).to_json(force_ascii=False, indent=2),
        encoding="utf-8",
    )
    month_summary_df.to_csv(daon.OUTPUT_ROOT / "monthly_generation_breakdown.csv", index=False, encoding="utf-8-sig")
    print(summary)


if __name__ == "__main__":
    main()
