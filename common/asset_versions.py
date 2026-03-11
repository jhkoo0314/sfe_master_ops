from __future__ import annotations

from collections.abc import Mapping
from typing import Any


CRM_RESULT_SCHEMA_VERSION = "crm_result_asset_v1"
PRESCRIPTION_RESULT_SCHEMA_VERSION = "prescription_result_asset_v1"
SANDBOX_INPUT_SCHEMA_VERSION = "sandbox_input_standard_v1"
SANDBOX_RESULT_SCHEMA_VERSION = "sandbox_result_asset_v1"
SANDBOX_TEMPLATE_PAYLOAD_VERSION = "sandbox_template_payload_chunked_v1"
TERRITORY_RESULT_SCHEMA_VERSION = "territory_result_asset_v1"
HTML_BUILDER_RESULT_SCHEMA_VERSION = "html_builder_result_asset_v1"

CRM_BUILDER_PAYLOAD_VERSION = "crm_builder_payload_chunked_v1"
PRESCRIPTION_BUILDER_PAYLOAD_VERSION = "prescription_builder_payload_chunked_v1"
TERRITORY_BUILDER_PAYLOAD_VERSION = "territory_builder_payload_v1"

BUILDER_INPUT_SCHEMA_VERSION = "builder_input_standard_v1"
BUILDER_PAYLOAD_VERSION = "builder_payload_standard_v1"
BUILDER_CONTRACT_VERSION = "builder_contract_v1"


def attach_builder_payload_version(
    payload: Mapping[str, Any],
    *,
    payload_version: str,
    source_asset_schema_version: str | None = None,
    builder_contract_version: str = BUILDER_CONTRACT_VERSION,
) -> dict[str, Any]:
    wrapped: dict[str, Any] = {
        "payload_version": payload_version,
        "builder_contract_version": builder_contract_version,
    }
    if source_asset_schema_version:
        wrapped["source_asset_schema_version"] = source_asset_schema_version
    wrapped.update(dict(payload))
    return wrapped


def build_source_version_snapshot(
    module_name: str,
    *,
    schema_version: str | None = None,
    payload_version: str | None = None,
    builder_contract_version: str | None = None,
) -> dict[str, dict[str, str]]:
    snapshot: dict[str, str] = {}
    if schema_version:
        snapshot["schema_version"] = schema_version
    if payload_version:
        snapshot["payload_version"] = payload_version
    if builder_contract_version:
        snapshot["builder_contract_version"] = builder_contract_version
    return {module_name: snapshot} if snapshot else {}


def extract_source_version_snapshot(
    module_name: str,
    payload: Mapping[str, Any] | None,
) -> dict[str, dict[str, str]]:
    if payload is None:
        return {}
    return build_source_version_snapshot(
        module_name,
        schema_version=_string_or_none(payload.get("source_asset_schema_version") or payload.get("schema_version")),
        payload_version=_string_or_none(payload.get("payload_version")),
        builder_contract_version=_string_or_none(payload.get("builder_contract_version")),
    )


def _string_or_none(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None
