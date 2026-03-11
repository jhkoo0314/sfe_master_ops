from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.sandbox.schemas import (
    SandboxInputStandard,
    CrmDomainRecord,
    SalesDomainRecord,
    TargetDomainRecord,
)
from modules.sandbox.builder_payload import build_chunked_sandbox_payload
from modules.sandbox.service import build_sandbox_result_asset
from ops_core.api.sandbox_router import evaluate_sandbox_asset
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root

COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
CRM_STANDARD_ROOT = get_company_root(ROOT, "ops_standard", COMPANY_KEY) / "crm"
SANDBOX_STANDARD_ROOT = get_company_root(ROOT, "ops_standard", COMPANY_KEY) / "sandbox"
OUTPUT_ROOT = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "sandbox"


def load_crm_domain_records() -> list[CrmDomainRecord]:
    crm_df = pd.read_excel(CRM_STANDARD_ROOT / "ops_crm_activity.xlsx")
    company_df = pd.read_excel(CRM_STANDARD_ROOT / "ops_company_master.xlsx")
    rep_meta_df = company_df[["rep_id", "rep_name", "branch_id", "branch_name"]].drop_duplicates(subset=["rep_id"])
    rep_meta_map = {
        str(row.rep_id): {
            "rep_name": str(row.rep_name),
            "branch_id": str(row.branch_id),
            "branch_name": str(row.branch_name),
        }
        for row in rep_meta_df.itertuples(index=False)
    }
    grouped = (
        crm_df.groupby(["hospital_id", "rep_id", "metric_month"], as_index=False)
        .agg(
            total_visits=("visit_count", "sum"),
            detail_call_count=("has_detail_call", "sum"),
            active_day_count=("activity_date", "nunique"),
            avg_sentiment_score=("sentiment_score", "mean"),
            avg_quality_factor=("quality_factor", "mean"),
            avg_impact_factor=("impact_factor", "mean"),
            avg_weighted_activity_score=("weighted_activity_score", "mean"),
            next_action_count=("next_action_text", lambda s: int(sum(1 for v in s if pd.notna(v) and str(v).strip()))),
            activity_types=("activity_type", lambda s: sorted(set(str(v) for v in s if pd.notna(v)))),
        )
    )
    records = []
    for row in grouped.itertuples(index=False):
        meta = rep_meta_map.get(str(row.rep_id), {})
        records.append(CrmDomainRecord(
            hospital_id=str(row.hospital_id),
            rep_id=str(row.rep_id),
            rep_name=meta.get("rep_name"),
            branch_id=meta.get("branch_id"),
            branch_name=meta.get("branch_name"),
            metric_month=str(row.metric_month),
            total_visits=int(row.total_visits),
            detail_call_count=int(row.detail_call_count),
            active_day_count=int(row.active_day_count),
            avg_sentiment_score=None if pd.isna(row.avg_sentiment_score) else float(row.avg_sentiment_score),
            avg_quality_factor=None if pd.isna(row.avg_quality_factor) else float(row.avg_quality_factor),
            avg_impact_factor=None if pd.isna(row.avg_impact_factor) else float(row.avg_impact_factor),
            avg_weighted_activity_score=None if pd.isna(row.avg_weighted_activity_score) else float(row.avg_weighted_activity_score),
            next_action_count=int(row.next_action_count),
            activity_types=list(row.activity_types),
        ))
    return records


def load_sales_records() -> list[SalesDomainRecord]:
    sales_df = pd.read_excel(SANDBOX_STANDARD_ROOT / "ops_sales_records.xlsx")
    records = []
    for row in sales_df.to_dict(orient="records"):
        row["hospital_id"] = str(row["hospital_id"])
        row["rep_id"] = str(row["rep_id"])
        row["metric_month"] = str(row["metric_month"])
        row["product_id"] = str(row["product_id"])
        records.append(SalesDomainRecord(**row))
    return records


def load_target_records() -> list[TargetDomainRecord]:
    target_df = pd.read_excel(SANDBOX_STANDARD_ROOT / "ops_target_records.xlsx")
    records = []
    for row in target_df.to_dict(orient="records"):
        row["rep_id"] = str(row["rep_id"])
        row["metric_month"] = str(row["metric_month"])
        row["product_id"] = str(row["product_id"])
        if row.get("hospital_id") is not None and not pd.isna(row.get("hospital_id")):
            row["hospital_id"] = str(row["hospital_id"])
        records.append(TargetDomainRecord(**row))
    return records


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    chunk_root = OUTPUT_ROOT / "sandbox_template_payload_assets"
    chunk_root.mkdir(parents=True, exist_ok=True)

    for existing in chunk_root.glob("*.js"):
        existing.unlink()

    crm_records = load_crm_domain_records()
    sales_records = load_sales_records()
    target_records = load_target_records()
    metric_months = sorted({r.metric_month for r in sales_records} | {r.metric_month for r in crm_records})

    input_std = SandboxInputStandard(
        scenario=f"{COMPANY_KEY}_crm_sales_target",
        metric_months=metric_months,
        crm_records=crm_records,
        sales_records=sales_records,
        target_records=target_records,
        created_by=f"{COMPANY_KEY}_source_adapter",
    )
    result_asset = build_sandbox_result_asset(input_std)
    if result_asset.dashboard_payload is not None:
        manifest, asset_chunks = build_chunked_sandbox_payload(
            result_asset.dashboard_payload.template_payload or {}
        )
        for chunk_name, chunk_payload in asset_chunks.items():
            branch_key_json = json.dumps(str(chunk_payload.get("branch_name") or ""), ensure_ascii=False)
            chunk_script = (
                "window.__SANDBOX_BRANCH_DATA__ = window.__SANDBOX_BRANCH_DATA__ || {};\n"
                f"window.__SANDBOX_BRANCH_DATA__[{branch_key_json}] = "
                f"{json.dumps(chunk_payload.get('branch_payload', {}), ensure_ascii=False)};\n"
            )
            (chunk_root / chunk_name).write_text(chunk_script, encoding="utf-8")
        manifest["asset_base"] = chunk_root.name
        result_asset.dashboard_payload.template_payload = manifest
    evaluation = evaluate_sandbox_asset(result_asset)

    (OUTPUT_ROOT / "sandbox_result_asset.json").write_text(
        json.dumps(result_asset.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "sandbox_ops_evaluation.json").write_text(
        json.dumps(evaluation.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "crm_record_count": len(crm_records),
        "sales_record_count": len(sales_records),
        "target_record_count": len(target_records),
        "metric_month_count": len(metric_months),
        "quality_status": evaluation.quality_status,
        "quality_score": evaluation.quality_score,
        "next_modules": evaluation.next_modules,
    }
    (OUTPUT_ROOT / "sandbox_validation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Validated {COMPANY_NAME} sandbox data with OPS:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
