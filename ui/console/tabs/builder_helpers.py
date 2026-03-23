from __future__ import annotations

import io
import json
from pathlib import Path
import re
import zipfile


def build_period_filter_defaults(period_mode: str, selected_year: str, selected_sub_period: str) -> dict:
    defaults = {
        "period_mode": "all",
        "year": selected_year or "",
        "month": "",
        "quarter": "",
    }
    if period_mode == "연간":
        defaults["period_mode"] = "year"
    elif period_mode == "분기별":
        defaults["period_mode"] = "quarter"
        quarter_map = {"1분기": "Q1", "2분기": "Q2", "3분기": "Q3", "4분기": "Q4"}
        defaults["quarter"] = f"{selected_year}-{quarter_map.get(selected_sub_period, 'Q1')}" if selected_year else ""
    elif period_mode == "월별":
        defaults["period_mode"] = "month"
        month_num = selected_sub_period.replace("월", "").zfill(2)
        defaults["month"] = f"{selected_year}-{month_num}" if selected_year else ""
    return defaults


def materialize_periodized_report(report_output_path: str, report_period: str, report_filters: dict) -> str:
    source_path = Path(report_output_path)
    if not source_path.exists():
        return report_output_path
    if report_filters.get("period_mode") == "all":
        return report_output_path

    safe_period = (
        report_period.replace(" ", "_")
        .replace("년", "")
        .replace("월", "")
        .replace("분기", "Q")
        .replace("/", "_")
    )
    target_path = source_path.with_name(f"{source_path.stem}__{safe_period}{source_path.suffix}")
    html = source_path.read_text(encoding="utf-8")
    injected = (
        "<script>"
        f"window.__OPS_DEFAULT_FILTER__ = {json.dumps(report_filters, ensure_ascii=False)};"
        "</script>\n</head>"
    )
    if "window.__OPS_DEFAULT_FILTER__" in html:
        materialized = html
    else:
        materialized = html.replace("</head>", injected, 1)
    target_path.write_text(materialized, encoding="utf-8")
    return str(target_path)


def _iter_referenced_asset_dirs(report_path: Path) -> list[Path]:
    asset_dirs: list[Path] = []
    default_asset_dir = report_path.parent / f"{report_path.stem}_assets"
    if default_asset_dir.exists():
        asset_dirs.append(default_asset_dir)

    try:
        html = report_path.read_text(encoding="utf-8")
    except OSError:
        html = ""

    for match in re.finditer(r'"asset_base"\s*:\s*"([^"]+)"', html):
        asset_name = str(match.group(1) or "").strip()
        if not asset_name:
            continue
        asset_dir = report_path.parent / asset_name
        if asset_dir.exists():
            asset_dirs.append(asset_dir)

    unique_dirs: list[Path] = []
    seen: set[Path] = set()
    for asset_dir in asset_dirs:
        if asset_dir in seen:
            continue
        seen.add(asset_dir)
        unique_dirs.append(asset_dir)
    return unique_dirs


def _iter_report_bundle_paths(report_type: str, report_path: Path) -> list[Path]:
    builder_root = report_path.parent
    bundle_paths: list[Path] = [report_path]

    for asset_dir in _iter_referenced_asset_dirs(report_path):
        bundle_paths.extend(path for path in asset_dir.rglob("*") if path.is_file())

    if report_type == "통합 검증 보고서":
        child_reports = [
            "crm_analysis_preview.html",
            "sandbox_report_preview.html",
            "territory_map_preview.html",
            "prescription_flow_preview.html",
            "radar_report_preview.html",
        ]
        for child_name in child_reports:
            child_path = builder_root / child_name
            if not child_path.exists():
                continue
            bundle_paths.append(child_path)
            for child_asset_dir in _iter_referenced_asset_dirs(child_path):
                bundle_paths.extend(path for path in child_asset_dir.rglob("*") if path.is_file())

    unique_paths: list[Path] = []
    seen: set[Path] = set()
    for path in bundle_paths:
        if path in seen or not path.exists():
            continue
        seen.add(path)
        unique_paths.append(path)
    return unique_paths


def build_report_download_artifact(
    report_output_path: str,
    report_type: str,
    report_period: str,
    report_filters: dict,
) -> tuple[bytes, str, str, str, str]:
    effective_report_path = Path(materialize_periodized_report(report_output_path, report_period, report_filters))
    if not effective_report_path.exists():
        raise FileNotFoundError(f"보고서 파일을 찾지 못했습니다: {effective_report_path}")

    base_name = effective_report_path.stem
    has_asset_dir = bool(_iter_referenced_asset_dirs(effective_report_path))
    needs_bundle = has_asset_dir or report_type == "통합 검증 보고서"

    if not needs_bundle:
        return (
            effective_report_path.read_bytes(),
            effective_report_path.name,
            "text/html",
            "⬇️ 생성된 보고서 다운로드",
            str(effective_report_path),
        )

    bundle_name = f"{base_name}_bundle.zip"
    bundle_buffer = io.BytesIO()
    builder_root = effective_report_path.parent
    with zipfile.ZipFile(bundle_buffer, "w", zipfile.ZIP_DEFLATED) as bundle_zip:
        for path in _iter_report_bundle_paths(report_type, effective_report_path):
            bundle_zip.write(path, arcname=str(path.relative_to(builder_root)))
    return (
        bundle_buffer.getvalue(),
        bundle_name,
        "application/zip",
        "⬇️ 보고서 번들 다운로드 (.zip)",
        str(effective_report_path),
    )


__all__ = [
    "build_period_filter_defaults",
    "build_report_download_artifact",
    "materialize_periodized_report",
]
