from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd


MERGEABLE_SOURCE_KEYS = ("crm_activity", "sales", "target", "prescription")
MONTHLY_FILE_NAMES = {
    "crm_activity": "crm_activity_raw.xlsx",
    "sales": "sales_raw.xlsx",
    "target": "target_raw.xlsx",
    "prescription": "fact_ship_raw.csv",
}


@dataclass(frozen=True)
class MonthlyMergeResult:
    monthly_root: str
    months_detected: list[str]
    merged_sources: dict[str, int]

    @property
    def has_data(self) -> bool:
        return bool(self.months_detected)


def _read_monthly_frame(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def get_monthly_raw_root(source_targets: Mapping[str, tuple[str, str]]) -> Path | None:
    crm_target = source_targets.get("crm_activity")
    if crm_target is None:
        return None
    crm_target_path = Path(crm_target[0])
    company_root = crm_target_path.parents[1]
    return company_root / "monthly_raw"


def inspect_monthly_raw(source_targets: Mapping[str, tuple[str, str]]) -> MonthlyMergeResult:
    monthly_root = get_monthly_raw_root(source_targets)
    if monthly_root is None or not monthly_root.exists():
        return MonthlyMergeResult(monthly_root=str(monthly_root) if monthly_root else "", months_detected=[], merged_sources={})

    month_dirs = sorted([item for item in monthly_root.iterdir() if item.is_dir()])
    merged_sources: dict[str, int] = {}
    for source_key, file_name in MONTHLY_FILE_NAMES.items():
        available_count = sum(1 for month_dir in month_dirs if (month_dir / file_name).exists())
        if available_count > 0:
            merged_sources[source_key] = available_count
    return MonthlyMergeResult(
        monthly_root=str(monthly_root),
        months_detected=[item.name for item in month_dirs],
        merged_sources=merged_sources,
    )


def merge_monthly_raw_sources(
    *,
    source_targets: Mapping[str, tuple[str, str]],
    skip_keys: set[str] | None = None,
) -> MonthlyMergeResult:
    skip_keys = skip_keys or set()
    inspected = inspect_monthly_raw(source_targets)
    if not inspected.has_data:
        return inspected

    monthly_root = Path(inspected.monthly_root)
    month_dirs = [monthly_root / month for month in inspected.months_detected]
    merged_sources: dict[str, int] = {}

    for source_key in MERGEABLE_SOURCE_KEYS:
        if source_key in skip_keys:
            continue
        target_info = source_targets.get(source_key)
        file_name = MONTHLY_FILE_NAMES.get(source_key)
        if target_info is None or not file_name:
            continue

        monthly_paths = [month_dir / file_name for month_dir in month_dirs if (month_dir / file_name).exists()]
        if not monthly_paths:
            continue

        frames = [_read_monthly_frame(path) for path in monthly_paths]
        merged_df = pd.concat(frames, ignore_index=True)
        target_path = Path(target_info[0])
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.suffix.lower() == ".csv":
            merged_df.to_csv(target_path, index=False, encoding="utf-8-sig")
        else:
            merged_df.to_excel(target_path, index=False)
        merged_sources[source_key] = len(monthly_paths)

    return MonthlyMergeResult(
        monthly_root=inspected.monthly_root,
        months_detected=inspected.months_detected,
        merged_sources=merged_sources,
    )

