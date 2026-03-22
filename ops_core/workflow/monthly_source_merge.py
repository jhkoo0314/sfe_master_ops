from __future__ import annotations

"""
Thin wrapper kept for backward compatibility.

Monthly raw merge is now treated as intake preparation logic, so the
implementation lives in ``modules.intake.merge``.
"""

from modules.intake.merge import (
    MERGEABLE_SOURCE_KEYS,
    MONTHLY_FILE_NAMES,
    MonthlyMergeResult,
    get_monthly_raw_root,
    inspect_monthly_raw,
    merge_monthly_raw_sources,
)

__all__ = [
    "MERGEABLE_SOURCE_KEYS",
    "MONTHLY_FILE_NAMES",
    "MonthlyMergeResult",
    "get_monthly_raw_root",
    "inspect_monthly_raw",
    "merge_monthly_raw_sources",
]
