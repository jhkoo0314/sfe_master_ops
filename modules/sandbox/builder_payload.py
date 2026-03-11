from __future__ import annotations

import hashlib
import re


CHUNKED_SANDBOX_DATA_MODE = "chunked_sandbox_branch_assets_v1"


def build_chunked_sandbox_payload(payload: dict) -> tuple[dict, dict[str, dict]]:
    branches = payload.get("branches", {}) or {}

    manifest = {
        key: value
        for key, value in payload.items()
        if key != "branches"
    }
    manifest["data_mode"] = CHUNKED_SANDBOX_DATA_MODE
    manifest["asset_base"] = ""
    manifest["branches"] = {}
    manifest["branch_asset_manifest"] = {}
    manifest["branch_index"] = []

    asset_chunks: dict[str, dict] = {}
    member_count = 0
    for branch_name in sorted(branches):
        branch_payload = branches[branch_name]
        chunk_name = _build_branch_chunk_name(branch_name)
        manifest["branch_asset_manifest"][branch_name] = chunk_name
        manifest["branch_index"].append(
            {
                "key": branch_name,
                "label": branch_name,
                "member_count": len((branch_payload or {}).get("members", []) or []),
            }
        )
        asset_chunks[chunk_name] = {
            "branch_name": branch_name,
            "branch_payload": branch_payload,
        }
        member_count += len((branch_payload or {}).get("members", []) or [])

    manifest["branch_asset_counts"] = {
        "branch_count": len(manifest["branch_asset_manifest"]),
        "member_count": member_count,
    }
    return manifest, asset_chunks


def _build_branch_chunk_name(branch_name: str) -> str:
    safe_token = re.sub(r"[^A-Za-z0-9_-]+", "_", str(branch_name or "").strip()).strip("_")
    digest = hashlib.sha1(str(branch_name or "").encode("utf-8")).hexdigest()[:8]
    prefix = safe_token or "branch"
    return f"{prefix}__{digest}.js"
