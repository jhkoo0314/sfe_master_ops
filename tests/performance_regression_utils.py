from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import contextmanager
import importlib
import json
import os
from pathlib import Path
from statistics import mean
import time
from types import ModuleType
from typing import Any, Iterator


@contextmanager
def company_env(company_key: str, company_name: str | None = None) -> Iterator[None]:
    previous_key = os.environ.get("OPS_COMPANY_KEY")
    previous_name = os.environ.get("OPS_COMPANY_NAME")

    os.environ["OPS_COMPANY_KEY"] = company_key
    if company_name:
        os.environ["OPS_COMPANY_NAME"] = company_name
    else:
        os.environ.pop("OPS_COMPANY_NAME", None)

    try:
        yield
    finally:
        _restore_env("OPS_COMPANY_KEY", previous_key)
        _restore_env("OPS_COMPANY_NAME", previous_name)


def load_script_module(
    module_name: str,
    *,
    company_key: str,
    company_name: str | None = None,
) -> ModuleType:
    with company_env(company_key, company_name):
        module = importlib.import_module(module_name)
        return importlib.reload(module)


@contextmanager
def temporary_module_attributes(
    module: ModuleType,
    updates: Mapping[str, Any],
) -> Iterator[None]:
    sentinel = object()
    previous: dict[str, Any] = {}

    for name, value in updates.items():
        previous[name] = getattr(module, name, sentinel)
        setattr(module, name, value)

    try:
        yield
    finally:
        for name, value in previous.items():
            if value is sentinel:
                delattr(module, name)
            else:
                setattr(module, name, value)


def run_script_main(
    module_name: str,
    *,
    company_key: str,
    company_name: str | None = None,
    attribute_overrides: Mapping[str, Any] | None = None,
) -> float:
    module = load_script_module(
        module_name,
        company_key=company_key,
        company_name=company_name,
    )

    start = time.perf_counter()
    if attribute_overrides:
        with temporary_module_attributes(module, attribute_overrides):
            module.main()
    else:
        module.main()
    return time.perf_counter() - start


def ensure_script_outputs(
    *,
    required_paths: Sequence[Path],
    script_modules: Sequence[str],
    company_key: str,
    company_name: str | None = None,
) -> None:
    if all(path.exists() for path in required_paths):
        return

    for module_name in script_modules:
        run_script_main(
            module_name,
            company_key=company_key,
            company_name=company_name,
        )

    missing = [str(path) for path in required_paths if not path.exists()]
    assert not missing, f"회귀 테스트용 산출물이 없습니다: {missing}"


def collect_directory_stats(root: Path, pattern: str = "*.js") -> dict[str, int]:
    files = [path for path in root.glob(pattern) if path.is_file()]
    sizes = [path.stat().st_size for path in files]
    return {
        "count": len(sizes),
        "total_bytes": sum(sizes),
        "max_bytes": max(sizes, default=0),
    }


def measure_json_parse_seconds(path: Path, *, repeats: int = 5) -> float:
    content = path.read_text(encoding="utf-8")
    samples: list[float] = []

    for _ in range(max(1, repeats)):
        start = time.perf_counter()
        json.loads(content)
        samples.append(time.perf_counter() - start)

    return mean(samples)


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value
