from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from common.supabase_client import get_supabase_client


@dataclass(frozen=True)
class CompanyRegistryEntry:
    company_key: str
    company_name: str
    company_name_normalized: str
    status: str = "active"
    company_code_external: str | None = None
    aliases: tuple[str, ...] = ()
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_dict(cls, payload: dict) -> "CompanyRegistryEntry":
        return cls(
            company_key=str(payload.get("company_key", "")).strip(),
            company_name=str(payload.get("company_name", "")).strip(),
            company_name_normalized=str(payload.get("company_name_normalized", "")).strip(),
            status=str(payload.get("status", "active")).strip() or "active",
            company_code_external=(
                str(payload.get("company_code_external")).strip()
                if payload.get("company_code_external") is not None
                else None
            ),
            aliases=tuple(str(item).strip() for item in payload.get("aliases", []) if str(item).strip()),
            notes=str(payload.get("notes", "")).strip(),
            created_at=str(payload.get("created_at", "")).strip(),
            updated_at=str(payload.get("updated_at", "")).strip(),
        )

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["aliases"] = list(self.aliases)
        return payload


_DEFAULT_COMPANIES: tuple[CompanyRegistryEntry, ...] = (
    CompanyRegistryEntry(
        company_key="daon_pharma",
        company_name="다온파마",
        company_name_normalized="다온파마",
        company_code_external="daon_pharma",
        aliases=("daon-pharma", "Daon Pharma", "다온제약"),
    ),
    CompanyRegistryEntry(
        company_key="hangyeol_pharma",
        company_name="한결제약",
        company_name_normalized="한결제약",
        company_code_external="hangyeol_pharma",
        aliases=("hangyeol-pharma", "Hangyeol Pharma", "한결파마"),
    ),
    CompanyRegistryEntry(
        company_key="monthly_merge_pharma",
        company_name="월별검증제약",
        company_name_normalized="월별검증제약",
        company_code_external="monthly_merge_pharma",
        aliases=("monthly-merge-pharma", "Monthly Merge Pharma"),
    ),
    CompanyRegistryEntry(
        company_key="tera_pharma",
        company_name="테라제약",
        company_name_normalized="테라제약",
        company_code_external="tera_pharma",
        aliases=("tera-pharma", "Tera Pharma", "테라파마"),
    ),
)


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def normalize_company_name(company_name: str) -> str:
    return " ".join(company_name.strip().lower().split())


def get_registry_store_path(project_root: str | Path) -> Path:
    return Path(project_root) / "data" / "system" / "company_registry.local.json"


def _write_registry_store(path: Path, companies: list[CompanyRegistryEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"companies": [item.to_dict() for item in companies]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ensure_registry_seeded(project_root: str | Path) -> None:
    path = get_registry_store_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"companies": []}
    else:
        payload = {"companies": []}

    companies = [CompanyRegistryEntry.from_dict(item) for item in payload.get("companies", [])]
    existing_keys = {item.company_key for item in companies}
    changed = False
    for default_entry in _DEFAULT_COMPANIES:
        if default_entry.company_key not in existing_keys:
            seeded = CompanyRegistryEntry(
                company_key=default_entry.company_key,
                company_name=default_entry.company_name,
                company_name_normalized=default_entry.company_name_normalized,
                status=default_entry.status,
                company_code_external=default_entry.company_code_external,
                aliases=default_entry.aliases,
                notes=default_entry.notes,
                created_at=_now_iso(),
                updated_at=_now_iso(),
            )
            companies.append(seeded)
            changed = True

    if changed or not path.exists():
        _write_registry_store(path, companies)


def _entry_from_supabase_row(row: dict) -> CompanyRegistryEntry:
    aliases_json = row.get("aliases_json") or []
    if isinstance(aliases_json, str):
        try:
            aliases_json = json.loads(aliases_json)
        except json.JSONDecodeError:
            aliases_json = []
    return CompanyRegistryEntry(
        company_key=str(row.get("company_key", "")).strip(),
        company_name=str(row.get("company_name", "")).strip(),
        company_name_normalized=str(row.get("company_name_normalized", "")).strip(),
        status=str(row.get("status", "active")).strip() or "active",
        company_code_external=(str(row.get("company_code_external")).strip() if row.get("company_code_external") else None),
        aliases=tuple(str(item).strip() for item in aliases_json if str(item).strip()),
        notes=str(row.get("notes", "")).strip(),
        created_at=str(row.get("created_at", "")).strip(),
        updated_at=str(row.get("updated_at", "")).strip(),
    )


def _load_companies_from_supabase(active_only: bool = True) -> list[CompanyRegistryEntry] | None:
    client = get_supabase_client()
    if client is None:
        return None
    try:
        query = client.table("company_registry").select(
            "company_key, company_name, company_name_normalized, status, company_code_external, aliases_json, notes, created_at, updated_at"
        )
        if active_only:
            query = query.eq("status", "active")
        response = query.order("company_name_normalized").execute()
        rows = getattr(response, "data", None) or []
        return [_entry_from_supabase_row(row) for row in rows]
    except Exception:
        return None


def _sync_local_registry_from_entries(project_root: str | Path, companies: list[CompanyRegistryEntry]) -> None:
    if not companies:
        return
    _write_registry_store(get_registry_store_path(project_root), companies)


def _load_local_companies(project_root: str | Path) -> list[CompanyRegistryEntry]:
    ensure_registry_seeded(project_root)
    path = get_registry_store_path(project_root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [CompanyRegistryEntry.from_dict(item) for item in payload.get("companies", [])]


def _merge_company_entries(
    primary: list[CompanyRegistryEntry],
    secondary: list[CompanyRegistryEntry],
) -> list[CompanyRegistryEntry]:
    merged: dict[str, CompanyRegistryEntry] = {item.company_key: item for item in secondary}
    for item in primary:
        merged[item.company_key] = item
    return list(merged.values())


def list_registered_companies(project_root: str | Path, active_only: bool = True) -> list[CompanyRegistryEntry]:
    local_companies = _load_local_companies(project_root)
    companies = _load_companies_from_supabase(active_only=False)
    if companies is not None:
        merged_companies = _merge_company_entries(primary=companies, secondary=local_companies)
        _sync_local_registry_from_entries(project_root, merged_companies)
        if active_only:
            merged_companies = [item for item in merged_companies if item.status == "active"]
        return sorted(merged_companies, key=lambda item: (item.company_name_normalized, item.company_key))

    if active_only:
        local_companies = [item for item in local_companies if item.status == "active"]
    return sorted(local_companies, key=lambda item: (item.company_name_normalized, item.company_key))


def get_company_by_key(project_root: str | Path, company_key: str) -> CompanyRegistryEntry | None:
    company_key = company_key.strip()
    if not company_key:
        return None
    for entry in list_registered_companies(project_root, active_only=False):
        if entry.company_key == company_key:
            return entry
    return None


def find_company_by_name(project_root: str | Path, company_name: str) -> CompanyRegistryEntry | None:
    normalized = normalize_company_name(company_name)
    if not normalized:
        return None
    for entry in list_registered_companies(project_root, active_only=False):
        if entry.company_name_normalized == normalized:
            return entry
        alias_normalized = [normalize_company_name(alias) for alias in entry.aliases]
        if normalized in alias_normalized:
            return entry
    return None


def resolve_company_reference(project_root: str | Path, company_ref: str) -> CompanyRegistryEntry | None:
    cleaned_ref = str(company_ref).strip()
    if not cleaned_ref:
        return None

    by_key = get_company_by_key(project_root, cleaned_ref)
    if by_key is not None:
        return by_key

    normalized_ref = normalize_company_name(cleaned_ref)
    for entry in list_registered_companies(project_root, active_only=False):
        if entry.company_name_normalized == normalized_ref:
            return entry
        if entry.company_code_external and normalize_company_name(entry.company_code_external) == normalized_ref:
            return entry
        alias_normalized = [normalize_company_name(alias) for alias in entry.aliases]
        if normalized_ref in alias_normalized:
            return entry
    return None


def _next_generated_company_key(companies: list[CompanyRegistryEntry]) -> str:
    prefix = "company_"
    max_index = 0
    for entry in companies:
        if not entry.company_key.startswith(prefix):
            continue
        suffix = entry.company_key[len(prefix):]
        if suffix.isdigit():
            max_index = max(max_index, int(suffix))
    return f"{prefix}{max_index + 1:06d}"


def register_company(
    project_root: str | Path,
    company_name: str,
    company_code_external: str | None = None,
) -> CompanyRegistryEntry:
    cleaned_name = company_name.strip()
    if not cleaned_name:
        raise ValueError("회사 이름이 비어 있습니다.")

    ensure_registry_seeded(project_root)
    existing = find_company_by_name(project_root, cleaned_name)
    if existing is not None:
        return existing

    path = get_registry_store_path(project_root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    companies = [CompanyRegistryEntry.from_dict(item) for item in payload.get("companies", [])]
    now_iso = _now_iso()
    new_entry = CompanyRegistryEntry(
        company_key=_next_generated_company_key(companies),
        company_name=cleaned_name,
        company_name_normalized=normalize_company_name(cleaned_name),
        company_code_external=company_code_external.strip() if company_code_external else None,
        created_at=now_iso,
        updated_at=now_iso,
    )
    client = get_supabase_client()
    if client is not None:
        try:
            response = (
                client.table("company_registry")
                .insert(
                    {
                        "company_key": new_entry.company_key,
                        "company_name": new_entry.company_name,
                        "company_name_normalized": new_entry.company_name_normalized,
                        "status": new_entry.status,
                        "company_code_external": new_entry.company_code_external,
                        "aliases_json": list(new_entry.aliases),
                        "notes": new_entry.notes,
                    }
                )
                .execute()
            )
            rows = getattr(response, "data", None) or []
            if rows:
                inserted_entry = _entry_from_supabase_row(rows[0])
                companies.append(inserted_entry)
                _write_registry_store(path, companies)
                return inserted_entry
        except Exception:
            pass

    companies.append(new_entry)
    _write_registry_store(path, companies)
    return new_entry
