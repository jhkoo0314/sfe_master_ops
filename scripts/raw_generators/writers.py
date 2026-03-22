from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import pandas as pd


def write_source_outputs(dataframes: Mapping[str, pd.DataFrame], output_paths: Mapping[str, Path]) -> None:
    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    for source_key, dataframe in dataframes.items():
        path = output_paths[source_key]
        if path.suffix.lower() == ".csv":
            dataframe.to_csv(path, index=False, encoding="utf-8-sig")
        else:
            dataframe.to_excel(path, index=False)


def write_monthly_outputs(monthly_root: Path, yyyymm: str, dataframes: Mapping[str, pd.DataFrame]) -> None:
    month_dir = monthly_root / yyyymm
    month_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "crm_activity": month_dir / "crm_activity_raw.xlsx",
        "target": month_dir / "target_raw.xlsx",
        "sales": month_dir / "sales_raw.xlsx",
        "prescription": month_dir / "fact_ship_raw.csv",
    }
    write_source_outputs(dataframes, output_paths)


def write_json_summary(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv_table(path: Path, dataframe: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False, encoding="utf-8-sig")


__all__ = [
    "write_source_outputs",
    "write_monthly_outputs",
    "write_json_summary",
    "write_csv_table",
]
