from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import pandas as pd

from common.company_profile import get_company_ops_profile
from scripts.raw_generators.configs import RawGenerationConfig
from scripts.raw_generators.writers import write_csv_table, write_json_summary, write_monthly_outputs


def _month_start(month_token: str) -> str:
    return f"{month_token}-01"


def _month_end(month_token: str) -> str:
    month = pd.Period(month_token, freq="M")
    return month.end_time.normalize().strftime("%Y-%m-%d")


def _configure_daon_module(config: RawGenerationConfig, *, seed: int | None = None) -> object:
    from scripts.raw_generators.templates import daon_like_helpers as daon

    daon.COMPANY_KEY = config.company_key
    daon.COMPANY_NAME = config.company_name
    daon.PROFILE = get_company_ops_profile(config.company_key)
    daon.OUTPUT_ROOT = daon.ROOT / "data" / "company_source" / config.company_key
    daon.CLINIC_REP_COUNT = config.clinic_rep_count
    daon.HOSPITAL_REP_COUNT = config.hospital_rep_count
    daon.BRANCH_DEFS = [dict(branch) for branch in daon.ALL_BRANCH_DEFS[: config.branch_count]]
    daon.START_DATE = _month_start(config.start_month)
    daon.END_DATE = _month_end(config.end_month)

    if config.portfolio_source == "hangyeol_portfolio":
        daon.PORTFOLIO_PATH = daon.ROOT / "docs" / "part1" / "hangyeol-pharma-portfolio-draft.csv"

    resolved_seed = seed if seed is not None else getattr(daon, "SEED", 20260310)
    daon.SEED = resolved_seed
    random.seed(resolved_seed)
    np.random.seed(resolved_seed)
    return daon


def run_template(config: RawGenerationConfig) -> None:
    daon = _configure_daon_module(config)

    portfolio = daon.load_portfolio()
    hospital_pool = daon.load_hospital_pool()
    clinic_df, hospital_df = daon.select_accounts(hospital_pool)
    rep_df = daon.build_rep_master(clinic_df, hospital_df)
    account_master = daon.build_account_master(rep_df, clinic_df, hospital_df)
    assignment_raw = daon.build_company_assignment(account_master, rep_df)
    crm_raw = daon.generate_crm_raw(account_master, portfolio)
    target_raw, sales_raw = daon.generate_target_and_sales(account_master, portfolio)
    ship_raw = daon.generate_fact_ship(account_master, sales_raw, portfolio)
    daon.write_outputs(rep_df, account_master, assignment_raw, crm_raw, target_raw, sales_raw, ship_raw)

    summary = {
        "company_key": config.company_key,
        "company_name": config.company_name,
        "template_type": config.template_type,
        "output_mode": config.output_mode,
        "rep_count": int(len(rep_df)),
        "clinic_rep_count": int((rep_df["rep_role"] == "의원").sum()),
        "hospital_rep_count": int((rep_df["rep_role"] == "종합병원").sum()),
        "account_count": int(len(account_master)),
        "clinic_account_count": int((account_master["account_type"] == "의원").sum()),
        "hospital_account_count": int((account_master["account_type"] != "의원").sum()),
        "crm_rows": int(len(crm_raw)),
        "target_rows": int(len(target_raw)),
        "sales_rows": int(len(sales_raw)),
        "fact_ship_rows": int(len(ship_raw)),
        "date_range": [daon.START_DATE, daon.END_DATE],
        "output_root": str(Path(daon.OUTPUT_ROOT)),
    }
    daon.write_json_summary(Path(daon.OUTPUT_ROOT) / "generation_summary.json", summary)
    print(summary)


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

    for row_idx in list(result.index[missing_mask]):
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


def _month_bounds(month: pd.Period) -> tuple[str, str]:
    start = month.to_timestamp(how="start")
    end = month.to_timestamp(how="end").normalize()
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def run_monthly_and_merged_template(config: RawGenerationConfig) -> None:
    daon = _configure_daon_module(config, seed=20260322)
    monthly_root = Path(daon.OUTPUT_ROOT) / "monthly_raw"
    monthly_root.mkdir(parents=True, exist_ok=True)
    months = pd.period_range(config.start_month, config.end_month, freq="M")

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
        month_seed = daon.SEED + idx
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
        write_monthly_outputs(
            monthly_root,
            yyyymm,
            {
                "crm_activity": crm_raw,
                "target": target_raw,
                "sales": sales_raw,
                "prescription": ship_raw,
            },
        )
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
    summary = {
        "company_key": config.company_key,
        "company_name": config.company_name,
        "scenario": "monthly_raw_generation_and_merge_validation",
        "template_type": config.template_type,
        "output_mode": config.output_mode,
        "month_range": [config.start_month, config.end_month],
        "month_count": int(len(months)),
        "branch_count": int(len(daon.BRANCH_DEFS)),
        "rep_count": int(len(rep_df)),
        "clinic_rep_count": int((rep_df["rep_role"] == "의원").sum()),
        "hospital_rep_count": int((rep_df["rep_role"] == "종합병원").sum()),
        "monthly_sum_rows": monthly_sum,
        "merged_rows": merged_sum,
        "row_count_validation": {k: monthly_sum[k] == merged_sum[k] for k in monthly_sum},
        "output_root": str(Path(daon.OUTPUT_ROOT)),
    }

    write_json_summary(Path(daon.OUTPUT_ROOT) / "monthly_generation_plan_summary.json", summary)
    write_csv_table(Path(daon.OUTPUT_ROOT) / "monthly_generation_breakdown.csv", month_summary_df)
    print(summary)
