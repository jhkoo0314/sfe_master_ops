from __future__ import annotations

from functools import lru_cache
from typing import Any

from common.config import settings

try:
    from supabase import Client, create_client
except ImportError:  # pragma: no cover - optional runtime dependency
    Client = Any  # type: ignore[misc,assignment]
    create_client = None


@lru_cache(maxsize=1)
def get_supabase_client(use_service_role: bool = True) -> Client | None:
    if create_client is None:
        return None

    supabase_url = settings.supabase_url.strip()
    if not supabase_url:
        return None

    api_key = settings.supabase_service_role_key.strip() if use_service_role else ""
    if not api_key:
        api_key = settings.supabase_anon_key.strip()
    if not api_key:
        return None

    try:
        return create_client(supabase_url, api_key)
    except Exception:
        return None
