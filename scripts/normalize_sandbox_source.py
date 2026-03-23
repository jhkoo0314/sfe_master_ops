from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.sandbox.domain_adapter import load_sales_from_records, load_target_from_records
from common.company_profile import get_company_ops_profile
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root

COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
PROFILE = get_company_ops_profile(COMPANY_KEY)
SOURCE_ROOT = get_company_root(ROOT, "company_source", COMPANY_KEY)
OUTPUT_ROOT = get_company_root(ROOT, "ops_standard", COMPANY_KEY) / "sandbox"


def _refresh_runtime_context() -> None:
    global COMPANY_KEY, COMPANY_NAME, PROFILE, SOURCE_ROOT, OUTPUT_ROOT
    COMPANY_KEY = get_active_company_key()
    COMPANY_NAME = get_active_company_name(COMPANY_KEY)
    PROFILE = get_company_ops_profile(COMPANY_KEY)
    SOURCE_ROOT = get_company_root(ROOT, "company_source", COMPANY_KEY)
    OUTPUT_ROOT = get_company_root(ROOT, "ops_standard", COMPANY_KEY) / "sandbox"


def _normalize_name(value: object) -> str:
    return "".join(str(value or "").strip().split()).lower()


def _build_account_lookup_maps(account_raw: pd.DataFrame) -> tuple[dict[str, str], set[str]]:
    account_ids = {
        str(value).strip()
        for value in account_raw.get("account_id", pd.Series(dtype="object")).tolist()
        if str(value).strip()
    }
    name_to_id: dict[str, str] = {}
    if {"account_name", "account_id"}.issubset(account_raw.columns):
        for row in account_raw[["account_name", "account_id"]].dropna(subset=["account_name", "account_id"]).itertuples(index=False):
            normalized_name = _normalize_name(row.account_name)
            account_id = str(row.account_id).strip()
            if normalized_name and account_id:
                name_to_id[normalized_name] = account_id
    return name_to_id, account_ids


def _remap_hospital_keys_to_active_accounts(
    dataframe: pd.DataFrame,
    *,
    hospital_id_columns: tuple[str, ...],
    hospital_name_columns: tuple[str, ...],
    name_to_id: dict[str, str],
    valid_account_ids: set[str],
) -> pd.DataFrame:
    if dataframe.empty or not name_to_id:
        return dataframe

    df = dataframe.copy()
    existing_id_columns = [column for column in hospital_id_columns if column in df.columns]
    existing_name_columns = [column for column in hospital_name_columns if column in df.columns]
    if not existing_id_columns or not existing_name_columns:
        return df

    for index, row in df.iterrows():
        mapped_id = None
        for name_column in existing_name_columns:
            normalized_name = _normalize_name(row.get(name_column))
            if normalized_name in name_to_id:
                mapped_id = name_to_id[normalized_name]
                break
        if not mapped_id:
            continue

        for id_column in existing_id_columns:
            current_id = str(row.get(id_column) or "").strip()
            if not current_id or current_id not in valid_account_ids:
                df.at[index, id_column] = mapped_id

    return df


def models_to_frame(models: list) -> pd.DataFrame:
    return pd.DataFrame([m.model_dump(mode="json") for m in models])


def main() -> None:
    _refresh_runtime_context()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    sales_file = PROFILE.source_path(SOURCE_ROOT, "sales")
    target_file = PROFILE.source_path(SOURCE_ROOT, "target")
    account_file = PROFILE.source_path(SOURCE_ROOT, "crm_account_assignment")

    sales_raw = pd.read_excel(sales_file)
    target_raw = pd.read_excel(target_file)
    account_raw = pd.read_excel(account_file)
    hospital_name_to_id, valid_account_ids = _build_account_lookup_maps(account_raw)

    sales_raw = _remap_hospital_keys_to_active_accounts(
        sales_raw,
        hospital_id_columns=("거래처코드", "병원코드", "account_id", "hospital_id"),
        hospital_name_columns=("거래처명", "병원명", "account_name", "hospital_name"),
        name_to_id=hospital_name_to_id,
        valid_account_ids=valid_account_ids,
    )
    target_raw = _remap_hospital_keys_to_active_accounts(
        target_raw,
        hospital_id_columns=("거래처코드", "병원코드", "account_id", "hospital_id"),
        hospital_name_columns=("거래처명", "병원명", "account_name", "hospital_name"),
        name_to_id=hospital_name_to_id,
        valid_account_ids=valid_account_ids,
    )

    sales_records, sales_failed = load_sales_from_records(
        sales_raw.to_dict(orient="records"),
        config=PROFILE.sales_adapter_factory(),
        source_label=f"{COMPANY_KEY}_sales_raw",
        hospital_name_to_id=hospital_name_to_id,
    )

    target_records, target_failed = load_target_from_records(
        target_raw.to_dict(orient="records"),
        config=PROFILE.target_adapter_factory(),
        source_label=f"{COMPANY_KEY}_target_raw",
        hospital_name_to_id=hospital_name_to_id,
    )

    sales_df = models_to_frame(sales_records)
    target_df = models_to_frame(target_records)

    sales_df.to_excel(OUTPUT_ROOT / "ops_sales_records.xlsx", index=False)
    target_df.to_excel(OUTPUT_ROOT / "ops_target_records.xlsx", index=False)

    if sales_failed:
        pd.DataFrame(sales_failed).to_excel(OUTPUT_ROOT / "failed_sales_rows.xlsx", index=False)
    if target_failed:
        pd.DataFrame(target_failed).to_excel(OUTPUT_ROOT / "failed_target_rows.xlsx", index=False)

    report = {
        "company": COMPANY_NAME,
        "company_key": COMPANY_KEY,
        "source_root": str(SOURCE_ROOT),
        "output_root": str(OUTPUT_ROOT),
        "sales_source_file": str(sales_file),
        "target_source_file": str(target_file),
        "sales_record_count": len(sales_records),
        "target_record_count": len(target_records),
        "sales_failed_count": len(sales_failed),
        "target_failed_count": len(target_failed),
        "sales_unique_hospitals": len({r.hospital_id for r in sales_records}),
        "target_unique_hospitals": len({r.hospital_id for r in target_records if r.hospital_id}),
        "sales_months": sorted({r.metric_month for r in sales_records}),
        "target_months": sorted({r.metric_month for r in target_records}),
    }
    (OUTPUT_ROOT / "normalization_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Normalized {COMPANY_NAME} sandbox source data:")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
