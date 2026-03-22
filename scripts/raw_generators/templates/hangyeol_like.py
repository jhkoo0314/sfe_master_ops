from __future__ import annotations

from pathlib import Path

from scripts.raw_generators.configs import RawGenerationConfig
from scripts.raw_generators.writers import write_json_summary


def run_template(config: RawGenerationConfig) -> None:
    from scripts.raw_generators.templates import hangyeol_like_helpers as hangyeol

    hangyeol.COMPANY_KEY = config.company_key
    hangyeol.COMPANY_NAME = config.company_name
    hangyeol.OUTPUT_ROOT = hangyeol.ROOT / "data" / "company_source" / config.company_key

    portfolio = hangyeol.portfolio_frame()
    rep_df, account_master = hangyeol.build_account_master()
    assignment_raw = hangyeol.build_company_assignment(account_master, rep_df)
    crm_raw = hangyeol.generate_crm_raw(account_master, portfolio)
    target_raw, sales_raw = hangyeol.generate_target_and_sales(account_master, portfolio)
    ship_raw = hangyeol.transform_fact_ship(portfolio)
    hangyeol.write_outputs(rep_df, account_master, assignment_raw, crm_raw, target_raw, sales_raw, ship_raw)

    summary = {
        "company_key": config.company_key,
        "company_name": config.company_name,
        "template_type": config.template_type,
        "output_mode": config.output_mode,
        "rep_count": int(len(rep_df)),
        "clinic_rep_count": int((rep_df["rep_role"] == "의원").sum()),
        "hospital_rep_count": int((rep_df["rep_role"] == "종합병원").sum()),
        "account_count": int(len(account_master)),
        "crm_rows": int(len(crm_raw)),
        "target_rows": int(len(target_raw)),
        "sales_rows": int(len(sales_raw)),
        "fact_ship_rows": int(len(ship_raw)),
        "output_root": str(Path(hangyeol.OUTPUT_ROOT)),
    }
    write_json_summary(Path(hangyeol.OUTPUT_ROOT) / "generation_summary.json", summary)
    print(summary)
