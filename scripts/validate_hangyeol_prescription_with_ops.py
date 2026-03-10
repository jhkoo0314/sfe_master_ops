from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.crm.adapter_config import HospitalAdapterConfig
from adapters.crm.hospital_adapter import load_hospital_master_from_file
from common.company_runtime import get_active_company_key, get_active_company_name, get_company_root
from modules.prescription.schemas import CompanyPrescriptionStandard
from modules.prescription.flow_builder import build_hospital_region_index, build_prescription_standard_flow
from modules.prescription.service import build_prescription_result_asset
from ops_core.api.prescription_router import evaluate_prescription_asset


COMPANY_KEY = get_active_company_key()
COMPANY_NAME = get_active_company_name(COMPANY_KEY)
SOURCE_ROOT = get_company_root(ROOT, "company_source", COMPANY_KEY)
STANDARD_ROOT = get_company_root(ROOT, "ops_standard", COMPANY_KEY) / "prescription"
OUTPUT_ROOT = get_company_root(ROOT, "ops_validation", COMPANY_KEY) / "prescription"
ACCOUNT_MASTER_PATH = SOURCE_ROOT / "company" / "hangyeol_account_master.xlsx"


def load_standard_records() -> list[CompanyPrescriptionStandard]:
    df = pd.read_excel(STANDARD_ROOT / "ops_prescription_standard.xlsx")
    records: list[CompanyPrescriptionStandard] = []
    for row in df.to_dict(orient="records"):
        row["record_type"] = str(row["record_type"])
        row["wholesaler_id"] = str(row["wholesaler_id"])
        row["wholesaler_name"] = str(row["wholesaler_name"])
        row["pharmacy_id"] = str(row["pharmacy_id"])
        row["pharmacy_name"] = str(row["pharmacy_name"])
        row["pharmacy_region_key"] = str(row["pharmacy_region_key"])
        row["pharmacy_sub_region_key"] = str(row["pharmacy_sub_region_key"])
        row["product_id"] = str(row["product_id"])
        row["product_name"] = str(row["product_name"])
        row["metric_month"] = str(row["metric_month"])
        if row.get("pharmacy_postal_code") is not None and pd.isna(row["pharmacy_postal_code"]):
            row["pharmacy_postal_code"] = None
        if row.get("ingredient_code") is not None and pd.isna(row["ingredient_code"]):
            row["ingredient_code"] = None
        if row.get("amount") is not None and pd.isna(row["amount"]):
            row["amount"] = None
        if row.get("unit") is not None and pd.isna(row["unit"]):
            row["unit"] = None
        if row.get("hospital_id") is not None and pd.isna(row["hospital_id"]):
            row["hospital_id"] = None
        records.append(CompanyPrescriptionStandard(**row))
    return records


def _to_quarter(metric_month: str) -> str:
    year = metric_month[:4]
    month = int(metric_month[4:6])
    quarter = ((month - 1) // 3) + 1
    return f"{year}-Q{quarter}"


def load_hospital_assignment_frame() -> pd.DataFrame:
    assignment_df = pd.read_excel(ACCOUNT_MASTER_PATH)
    assignment_df = assignment_df.rename(
        columns={
            "account_id": "hospital_id",
            "account_name": "hospital_name_master",
            "account_type": "hospital_type_master",
            "rep_id": "rep_id",
            "rep_name": "rep_name",
            "branch_id": "branch_id",
            "branch_name": "branch_name",
            "region_key": "hospital_region_key",
            "sub_region_key": "hospital_sub_region_key",
        }
    )
    keep_columns = [
        "hospital_id",
        "hospital_name_master",
        "hospital_type_master",
        "rep_id",
        "rep_name",
        "branch_id",
        "branch_name",
        "hospital_region_key",
        "hospital_sub_region_key",
    ]
    return assignment_df[keep_columns].drop_duplicates(subset=["hospital_id"])


def build_flow_report_frame(
    flows,
    assignment_df: pd.DataFrame,
) -> pd.DataFrame:
    flow_df = pd.DataFrame([flow.model_dump(mode="json") for flow in flows])
    flow_df["metric_month"] = flow_df["metric_month"].astype(str)
    flow_df["year_quarter"] = flow_df["metric_month"].apply(_to_quarter)
    flow_df["flow_status"] = flow_df["is_complete"].map(
        {True: "connected", False: "unmapped"}
    )
    flow_df = flow_df.merge(assignment_df, on="hospital_id", how="left")
    flow_df["hospital_name_final"] = flow_df["hospital_name"].fillna(flow_df["hospital_name_master"])
    flow_df["hospital_type_final"] = flow_df["hospital_type_master"].fillna("미확인")
    flow_df["rep_id"] = flow_df["rep_id"].fillna("UNASSIGNED")
    flow_df["rep_name"] = flow_df["rep_name"].fillna("미배정")
    flow_df["branch_id"] = flow_df["branch_id"].fillna("UNASSIGNED")
    flow_df["branch_name"] = flow_df["branch_name"].fillna("미배정")
    flow_df["total_amount"] = flow_df["total_amount"].fillna(0.0)
    flow_df["hospital_mapping_method"] = flow_df["hospital_mapping_method"].fillna("unmapped")
    return flow_df[
        [
            "year_quarter",
            "metric_month",
            "lineage_key",
            "flow_status",
            "hospital_mapping_method",
            "wholesaler_id",
            "wholesaler_name",
            "wholesaler_region_key",
            "pharmacy_id",
            "pharmacy_name",
            "pharmacy_region_key",
            "pharmacy_sub_region_key",
            "hospital_id",
            "hospital_name_final",
            "hospital_type_final",
            "rep_id",
            "rep_name",
            "branch_id",
            "branch_name",
            "product_id",
            "product_name",
            "ingredient_code",
            "total_quantity",
            "total_amount",
            "source_record_type",
        ]
    ].rename(
        columns={
            "hospital_name_final": "hospital_name",
            "hospital_type_final": "hospital_type",
        }
    )


def build_gap_report_frame(
    gaps,
    flow_report_df: pd.DataFrame,
) -> pd.DataFrame:
    gap_df = pd.DataFrame([gap.model_dump(mode="json") for gap in gaps])
    if gap_df.empty:
        return pd.DataFrame(
            columns=[
                "year_quarter",
                "metric_month",
                "pharmacy_id",
                "pharmacy_name",
                "pharmacy_region_key",
                "wholesaler_id",
                "product_id",
                "product_name",
                "quantity",
                "gap_reason",
                "raw_row_index",
            ]
        )
    gap_df["metric_month"] = gap_df["metric_month"].astype(str)
    gap_df["year_quarter"] = gap_df["metric_month"].apply(_to_quarter)
    product_lookup = (
        flow_report_df[["product_id", "product_name"]]
        .drop_duplicates(subset=["product_id"])
    )
    gap_df = gap_df.merge(product_lookup, on="product_id", how="left")
    return gap_df[
        [
            "year_quarter",
            "metric_month",
            "pharmacy_id",
            "pharmacy_name",
            "pharmacy_region_key",
            "wholesaler_id",
            "product_id",
            "product_name",
            "quantity",
            "gap_reason",
            "raw_row_index",
        ]
    ]


def build_quarter_kpi_frame(flow_report_df: pd.DataFrame) -> pd.DataFrame:
    connected_df = flow_report_df[flow_report_df["flow_status"] == "connected"].copy()
    if connected_df.empty:
        return pd.DataFrame()
    grouped = connected_df.groupby(
        ["year_quarter", "rep_id", "rep_name", "branch_id", "branch_name", "product_name"],
        dropna=False,
        as_index=False,
    ).agg(
        total_quantity=("total_quantity", "sum"),
        total_amount=("total_amount", "sum"),
        flow_count=("lineage_key", "count"),
        pharmacy_count=("pharmacy_id", "nunique"),
        hospital_count=("hospital_id", "nunique"),
        wholesaler_count=("wholesaler_id", "nunique"),
    )
    return grouped.sort_values(
        ["year_quarter", "rep_name", "total_amount"],
        ascending=[True, True, False],
    )


def build_hospital_trace_frame(flow_report_df: pd.DataFrame) -> pd.DataFrame:
    connected_df = flow_report_df[flow_report_df["flow_status"] == "connected"].copy()
    if connected_df.empty:
        return pd.DataFrame()
    grouped = connected_df.groupby(
        [
            "year_quarter",
            "hospital_id",
            "hospital_name",
            "hospital_type",
            "rep_id",
            "rep_name",
            "branch_name",
            "product_name",
        ],
        dropna=False,
        as_index=False,
    ).agg(
        total_quantity=("total_quantity", "sum"),
        total_amount=("total_amount", "sum"),
        pharmacy_count=("pharmacy_id", "nunique"),
        wholesaler_count=("wholesaler_id", "nunique"),
        active_month_count=("metric_month", "nunique"),
        flow_count=("lineage_key", "count"),
    )
    return grouped.sort_values(
        ["year_quarter", "rep_name", "hospital_name", "total_amount"],
        ascending=[True, True, True, False],
    )


def build_region_summary_frame(
    flow_report_df: pd.DataFrame,
    gap_report_df: pd.DataFrame,
) -> pd.DataFrame:
    flow_summary = flow_report_df.groupby(
        ["year_quarter", "pharmacy_region_key", "pharmacy_sub_region_key"],
        dropna=False,
        as_index=False,
    ).agg(
        flow_count=("lineage_key", "count"),
        connected_flow_count=("flow_status", lambda s: int((s == "connected").sum())),
        unmapped_flow_count=("flow_status", lambda s: int((s == "unmapped").sum())),
        total_amount=("total_amount", "sum"),
        pharmacy_count=("pharmacy_id", "nunique"),
        hospital_count=("hospital_id", "nunique"),
    )
    if gap_report_df.empty:
        flow_summary["gap_quantity"] = 0.0
        flow_summary["gap_record_count"] = 0
        return flow_summary

    gap_summary = gap_report_df.groupby(
        ["year_quarter", "pharmacy_region_key"],
        dropna=False,
        as_index=False,
    ).agg(
        gap_record_count=("pharmacy_id", "count"),
        gap_quantity=("quantity", "sum"),
    )
    return flow_summary.merge(
        gap_summary,
        on=["year_quarter", "pharmacy_region_key"],
        how="left",
    ).fillna({"gap_record_count": 0, "gap_quantity": 0.0})


def build_claim_validation_frame(flow_report_df: pd.DataFrame) -> pd.DataFrame:
    connected_df = flow_report_df[flow_report_df["flow_status"] == "connected"].copy()
    if connected_df.empty:
        return pd.DataFrame()
    connected_df["year"] = connected_df["metric_month"].astype(str).str[:4]
    connected_df["year_month"] = (
        connected_df["metric_month"].astype(str).str[:4]
        + "-"
        + connected_df["metric_month"].astype(str).str[4:6]
    )

    grouping_base = [
        "rep_id",
        "rep_name",
        "branch_name",
        "hospital_id",
        "hospital_name",
        "hospital_type",
        "product_name",
    ]

    def aggregate_claims(period_type: str, period_column: str, top_n: int) -> pd.DataFrame:
        group_columns = [period_column, *grouping_base]
        if period_column != "year":
            group_columns.insert(1, "year")
        grouped = connected_df.groupby(
            group_columns,
            dropna=False,
            as_index=False,
        ).agg(
            tracked_amount=("total_amount", "sum"),
            pharmacy_count=("pharmacy_id", "nunique"),
            wholesaler_count=("wholesaler_id", "nunique"),
            active_month_count=("metric_month", "nunique"),
            flow_count=("lineage_key", "count"),
        )
        grouped = grouped.rename(columns={period_column: "period_value"})
        if "year" not in grouped.columns:
            grouped["year"] = grouped["period_value"]
        grouped["period_type"] = period_type
        grouped["period_label"] = grouped["period_value"]
        grouped["year_quarter"] = ""
        grouped["year_month"] = ""
        if period_type == "quarter":
            grouped["year_quarter"] = grouped["period_value"]
        elif period_type == "month":
            grouped["year_month"] = grouped["period_value"]

        ranked = (
            grouped.sort_values(["period_value", "tracked_amount"], ascending=[True, False])
            .groupby("period_value", group_keys=False)
            .head(top_n)
            .reset_index(drop=True)
        )
        return ranked

    claim_candidates = pd.concat(
        [
            aggregate_claims("month", "year_month", 10),
            aggregate_claims("quarter", "year_quarter", 30),
            aggregate_claims("year", "year", 60),
        ],
        ignore_index=True,
    )

    factors = [0.99, 1.04, 1.11, 0.92, 1.18]
    records: list[dict] = []
    for idx, row in claim_candidates.iterrows():
        tracked_amount = float(row["tracked_amount"])
        factor = factors[idx % len(factors)]
        claimed_amount = round(tracked_amount * factor, 2)
        variance_amount = round(claimed_amount - tracked_amount, 2)
        variance_rate = round(variance_amount / tracked_amount, 4) if tracked_amount else 0.0
        abs_rate = abs(variance_rate)
        if abs_rate <= 0.05:
            verdict = "PASS"
            note = "주장값과 추적값 차이가 작아서 정상 범위입니다."
        elif abs_rate <= 0.15:
            verdict = "REVIEW"
            note = "차이가 있어 추가 확인이 필요합니다."
        else:
            verdict = "SUSPECT"
            note = "차이가 커서 도매/약국 흐름 재확인이 필요합니다."

        period_value = str(row["period_value"])
        records.append(
            {
                "claim_case_id": f"PDF-CLAIM-{idx + 1:03d}",
                "period_type": row["period_type"],
                "period_label": period_value,
                "period_value": period_value,
                "year": str(row["year"]),
                "year_quarter": row["year_quarter"],
                "year_month": row["year_month"],
                "rep_id": row["rep_id"],
                "rep_name": row["rep_name"],
                "branch_name": row["branch_name"],
                "hospital_id": row["hospital_id"],
                "hospital_name": row["hospital_name"],
                "hospital_type": row["hospital_type"],
                "product_name": row["product_name"],
                "claimed_amount": claimed_amount,
                "tracked_amount": tracked_amount,
                "variance_amount": variance_amount,
                "variance_rate": variance_rate,
                "verdict": verdict,
                "pharmacy_count": int(row["pharmacy_count"]),
                "wholesaler_count": int(row["wholesaler_count"]),
                "active_month_count": int(row["active_month_count"]),
                "flow_count": int(row["flow_count"]),
                "claim_source": "synthetic_demo_claim",
                "review_note": note,
            }
        )

    return pd.DataFrame(records)


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    hospitals = load_hospital_master_from_file(
        SOURCE_ROOT / "company" / "hangyeol_account_master.xlsx",
        config=HospitalAdapterConfig.hangyeol_account_example(),
    )
    sub_idx, reg_idx = build_hospital_region_index(hospitals)
    standards = load_standard_records()
    flows, gaps = build_prescription_standard_flow(
        standards,
        sub_idx,
        reg_idx,
        prefer_hospital_types=["의원", "종합병원", "상급종합"],
    )
    asset = build_prescription_result_asset(
        flows,
        gaps,
        adapter_failed_count=0,
        total_raw_count=len(standards),
        notes="hangyeol fact_ship source -> adapter normalization -> ops prescription validation",
    )
    evaluation = evaluate_prescription_asset(asset)
    assignment_df = load_hospital_assignment_frame()
    flow_report_df = build_flow_report_frame(flows, assignment_df)
    gap_report_df = build_gap_report_frame(gaps, flow_report_df)
    quarter_kpi_df = build_quarter_kpi_frame(flow_report_df)
    hospital_trace_df = build_hospital_trace_frame(flow_report_df)
    region_summary_df = build_region_summary_frame(flow_report_df, gap_report_df)
    claim_validation_df = build_claim_validation_frame(flow_report_df)

    (OUTPUT_ROOT / "prescription_result_asset.json").write_text(
        json.dumps(asset.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "prescription_ops_evaluation.json").write_text(
        json.dumps(evaluation.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    flow_report_df.to_excel(OUTPUT_ROOT / "prescription_flow_records.xlsx", index=False)
    gap_report_df.to_excel(OUTPUT_ROOT / "prescription_gap_records.xlsx", index=False)
    quarter_kpi_df.to_excel(OUTPUT_ROOT / "prescription_rep_kpi_quarter.xlsx", index=False)
    hospital_trace_df.to_excel(OUTPUT_ROOT / "prescription_hospital_trace_quarter.xlsx", index=False)
    region_summary_df.to_excel(OUTPUT_ROOT / "prescription_region_summary.xlsx", index=False)
    claim_validation_df.to_excel(OUTPUT_ROOT / "prescription_claim_validation.xlsx", index=False)

    claim_summary = {
        "total_cases": int(len(claim_validation_df)),
        "pass_count": int((claim_validation_df["verdict"] == "PASS").sum()) if not claim_validation_df.empty else 0,
        "review_count": int((claim_validation_df["verdict"] == "REVIEW").sum()) if not claim_validation_df.empty else 0,
        "suspect_count": int((claim_validation_df["verdict"] == "SUSPECT").sum()) if not claim_validation_df.empty else 0,
    }

    summary = {
        "standard_record_count": len(standards),
        "flow_record_count": len(flows),
        "gap_record_count": len(gaps),
        "quality_status": evaluation.quality_status,
        "quality_score": evaluation.quality_score,
        "next_modules": evaluation.next_modules,
        "flow_completion_rate": asset.mapping_quality.flow_completion_rate,
        "connected_hospital_count": asset.lineage_summary.unique_hospitals_connected,
        "claim_validation_summary": claim_summary,
        "output_files": {
            "flow_records": "prescription_flow_records.xlsx",
            "gap_records": "prescription_gap_records.xlsx",
            "rep_kpi_quarter": "prescription_rep_kpi_quarter.xlsx",
            "hospital_trace_quarter": "prescription_hospital_trace_quarter.xlsx",
            "region_summary": "prescription_region_summary.xlsx",
            "claim_validation": "prescription_claim_validation.xlsx",
        },
    }
    (OUTPUT_ROOT / "prescription_validation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Validated {COMPANY_NAME} prescription data with OPS:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
