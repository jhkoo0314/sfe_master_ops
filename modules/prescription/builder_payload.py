from __future__ import annotations

from copy import deepcopy
import re

import pandas as pd

from modules.kpi import build_prescription_builder_context


CHUNKED_PRESCRIPTION_DATA_MODE = "chunked_prescription_detail_assets_v1"
PRESCRIPTION_DETAIL_BUCKETS = (
    "claims",
    "gaps",
    "hospital_traces",
    "rep_kpis",
)


def _sanitize_chunk_token(value: str | None) -> str:
    text = str(value or "").strip().lower()
    cleaned = re.sub(r"[^0-9a-z]+", "_", text).strip("_")
    return cleaned or "all"


def _build_chunk_name(bucket: str, key: str) -> str:
    return f"{bucket}__{_sanitize_chunk_token(key)}.js"


def _group_detail_rows(bucket: str, rows: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {"ALL": rows}
    if bucket not in PRESCRIPTION_DETAIL_BUCKETS:
        return groups

    for row in rows:
        period_key = str(row.get("year_quarter") or "").strip()
        if not period_key:
            continue
        groups.setdefault(period_key, []).append(row)
    return groups


def build_chunked_prescription_payload(payload: dict) -> tuple[dict, dict[str, dict]]:
    manifest = deepcopy(payload)
    asset_manifest: dict[str, dict[str, str]] = {}
    asset_counts: dict[str, int] = {}
    asset_chunks: dict[str, dict] = {}

    for bucket in PRESCRIPTION_DETAIL_BUCKETS:
        rows = list(manifest.get(bucket) or [])
        asset_counts[bucket] = len(rows)
        grouped_rows = _group_detail_rows(bucket, rows)
        bucket_manifest: dict[str, str] = {}

        for cache_key, chunk_rows in grouped_rows.items():
            if not chunk_rows:
                continue
            file_name = _build_chunk_name(bucket, cache_key)
            bucket_manifest[cache_key] = file_name
            asset_chunks[file_name] = {
                "bucket": bucket,
                "cache_key": cache_key,
                "rows": chunk_rows,
            }

        asset_manifest[bucket] = bucket_manifest
        manifest[bucket] = []

    manifest["data_mode"] = CHUNKED_PRESCRIPTION_DATA_MODE
    manifest["asset_base"] = ""
    manifest["detail_asset_manifest"] = asset_manifest
    manifest["detail_asset_counts"] = asset_counts
    return manifest, asset_chunks


def build_prescription_builder_payload(
    *,
    company_name: str,
    summary: dict,
    claim_df: pd.DataFrame,
    flow_df: pd.DataFrame,
    gap_df: pd.DataFrame,
    rep_kpi_df: pd.DataFrame,
    download_files: dict[str, str] | None = None,
) -> dict:
    return build_prescription_builder_context(
        company_name=company_name,
        summary=summary,
        claim_df=claim_df,
        flow_df=flow_df,
        gap_df=gap_df,
        rep_kpi_df=rep_kpi_df,
        download_files=download_files,
    )
