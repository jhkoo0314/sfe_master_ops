from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .models import IntakeFix


def _load_uploaded_frame(info: dict[str, Any]) -> pd.DataFrame:
    file_bytes = info["file_bytes"]
    file_name = str(info.get("name") or "").lower()
    if file_name.endswith(".csv") or str(info.get("file_ext") or "").lower() == ".csv":
        return pd.read_csv(io.BytesIO(file_bytes))
    return pd.read_excel(io.BytesIO(file_bytes))


def _normalize_header_name(name: Any) -> str:
    return " ".join(str(name).strip().split())


def _deduplicate_headers(columns: list[str]) -> tuple[list[str], int]:
    seen: dict[str, int] = {}
    deduped: list[str] = []
    changed = 0
    for column in columns:
        count = seen.get(column, 0)
        seen[column] = count + 1
        if count == 0:
            deduped.append(column)
            continue
        changed += 1
        deduped.append(f"{column}_{count + 1}")
    return deduped, changed


def _looks_like_month_column(column_name: str) -> bool:
    lowered = column_name.lower()
    return any(token in lowered for token in ["yyyymm", "month", "월", "기준월", "매출월", "목표월"])


def _looks_like_date_column(column_name: str) -> bool:
    lowered = column_name.lower()
    return any(token in lowered for token in ["date", "일자", "날짜", "방문일", "활동일", "출고일", "납품일"])


def _normalize_month_value(value: Any) -> str | Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return value
    text = str(value).strip()
    if not text:
        return value
    compact = (
        text.replace("-", "")
        .replace(".", "")
        .replace("/", "")
        .replace(" ", "")
    )
    if len(compact) >= 6 and compact[:6].isdigit():
        year = compact[:4]
        month = compact[4:6]
        if 1 <= int(month) <= 12:
            return f"{year}{month}"
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return value
    return f"{parsed.year:04d}{parsed.month:02d}"


def _normalize_date_value(value: Any) -> str | Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return value
    return parsed.strftime("%Y-%m-%d")


def _count_changes(before: pd.Series, after: pd.Series) -> int:
    return sum(
        1
        for prev, current in zip(before.tolist(), after.tolist(), strict=False)
        if not (pd.isna(prev) and pd.isna(current)) and str(prev) != str(current)
    )


@dataclass
class IntakeFixerResult:
    dataframe: pd.DataFrame | None
    columns: list[str]
    row_count: int
    preview_rows: list[dict[str, Any]] = field(default_factory=list)
    fixes: list[IntakeFix] = field(default_factory=list)


def apply_basic_intake_fixes_to_dataframe(source_key: str, dataframe: pd.DataFrame | None) -> IntakeFixerResult:
    if dataframe is None:
        return IntakeFixerResult(
            dataframe=None,
            columns=[],
            row_count=0,
            preview_rows=[],
            fixes=[],
        )

    df = dataframe.copy()
    fixes: list[IntakeFix] = []

    original_columns = [str(column) for column in df.columns]
    normalized_columns = [_normalize_header_name(column) for column in original_columns]
    if normalized_columns != original_columns:
        change_count = sum(1 for before, after in zip(original_columns, normalized_columns, strict=False) if before != after)
        df.columns = normalized_columns
        fixes.append(
            IntakeFix(
                source_key=source_key,
                fix_type="trim_column_names",
                message="컬럼명 앞뒤 공백과 중복 공백을 정리했습니다.",
                affected_count=change_count,
            )
        )
    deduped_columns, deduped_count = _deduplicate_headers([str(column) for column in df.columns])
    if deduped_count:
        df.columns = deduped_columns
        fixes.append(
            IntakeFix(
                source_key=source_key,
                fix_type="deduplicate_headers",
                message="중복 컬럼명을 구분 가능한 이름으로 정리했습니다.",
                affected_count=deduped_count,
            )
        )

    before_rows = len(df)
    df = df.drop_duplicates()
    duplicate_removed = before_rows - len(df)
    if duplicate_removed:
        fixes.append(
            IntakeFix(
                source_key=source_key,
                fix_type="drop_duplicate_rows",
                message="완전히 같은 행을 제거했습니다.",
                affected_count=duplicate_removed,
            )
        )

    for column in list(df.columns):
        series_before = df[column].copy()
        if _looks_like_month_column(column):
            df[column] = df[column].map(_normalize_month_value)
            changed = _count_changes(series_before, df[column])
            if changed:
                fixes.append(
                    IntakeFix(
                        source_key=source_key,
                        fix_type="normalize_month_format",
                        message=f"`{column}` 값을 YYYYMM 기준으로 맞췄습니다.",
                        affected_count=changed,
                    )
                )
        elif _looks_like_date_column(column):
            df[column] = df[column].map(_normalize_date_value)
            changed = _count_changes(series_before, df[column])
            if changed:
                fixes.append(
                    IntakeFix(
                        source_key=source_key,
                        fix_type="normalize_date_format",
                        message=f"`{column}` 값을 YYYY-MM-DD 기준으로 맞췄습니다.",
                        affected_count=changed,
                    )
                )

    preview_rows = df.head(3).where(pd.notna(df), None).to_dict("records")
    return IntakeFixerResult(
        dataframe=df,
        columns=[str(column) for column in df.columns],
        row_count=int(len(df)),
        preview_rows=preview_rows,
        fixes=fixes,
    )


def apply_basic_intake_fixes(source_key: str, info: dict[str, Any]) -> IntakeFixerResult:
    if "file_bytes" not in info:
        return IntakeFixerResult(
            dataframe=None,
            columns=[str(column) for column in info.get("columns", []) if column is not None],
            row_count=int(info.get("row_count") or 0),
            preview_rows=[row for row in info.get("preview", []) if isinstance(row, dict)],
            fixes=[],
        )

    return apply_basic_intake_fixes_to_dataframe(source_key, _load_uploaded_frame(info))
