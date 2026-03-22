from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.intake.service import _resolve_mapping


def test_resolve_mapping_matches_realistic_crm_columns():
    resolved_mapping, missing_required, _missing_review = _resolve_mapping(
        ["방문일자", "영업사원명", "방문기관", "활동유형", "활동메모"],
        "crm_activity",
    )

    assert resolved_mapping["activity_date"] == "방문일자"
    assert resolved_mapping["rep"] == "영업사원명"
    assert resolved_mapping["account"] == "방문기관"
    assert resolved_mapping["activity_type"] == "활동유형"
    assert missing_required == []


def test_resolve_mapping_matches_daon_crm_activity_columns():
    resolved_mapping, missing_required, _missing_review = _resolve_mapping(
        ["실행일", "영업사원코드", "영업사원명", "방문기관", "액션유형", "접점채널", "활동메모"],
        "crm_activity",
    )

    assert resolved_mapping["activity_date"] == "실행일"
    assert resolved_mapping["rep"] in {"영업사원코드", "영업사원명"}
    assert resolved_mapping["account"] == "방문기관"
    assert resolved_mapping["activity_type"] == "액션유형"
    assert missing_required == []


def test_resolve_mapping_matches_realistic_sales_and_target_columns():
    sales_mapping, sales_missing_required, _ = _resolve_mapping(
        ["거래처코드", "브랜드코드", "매출금액", "기준년월"],
        "sales",
    )
    target_mapping, target_missing_required, _ = _resolve_mapping(
        ["기준년월", "계획금액"],
        "target",
    )

    assert sales_mapping["account"] == "거래처코드"
    assert sales_mapping["product"] == "브랜드코드"
    assert sales_mapping["amount"] == "매출금액"
    assert sales_mapping["period"] == "기준년월"
    assert sales_missing_required == []

    assert target_mapping["period"] == "기준년월"
    assert target_mapping["target_value"] == "계획금액"
    assert target_missing_required == []


def test_resolve_mapping_matches_realistic_prescription_columns():
    resolved_mapping, missing_required, _missing_review = _resolve_mapping(
        [
            "ship_date (출고일)",
            "pharmacy_account_id (약국거래처ID)",
            "제품명",
            "출고수량",
            "amount_ship (출고금액)",
        ],
        "prescription",
    )

    assert resolved_mapping["ship_date"] == "ship_date (출고일)"
    assert resolved_mapping["pharmacy"] == "pharmacy_account_id (약국거래처ID)"
    assert resolved_mapping["product"] == "제품명"
    assert resolved_mapping["quantity"] == "출고수량"
    assert missing_required == []


def test_resolve_mapping_matches_daon_prescription_columns():
    resolved_mapping, missing_required, _missing_review = _resolve_mapping(
        [
            "ship_date (출고일)",
            "pharmacy_name (약국명)",
            "brand (브랜드)",
            "sku (SKU)",
            "qty (수량)",
            "amount_ship (출고금액)",
        ],
        "prescription",
    )

    assert resolved_mapping["ship_date"] == "ship_date (출고일)"
    assert resolved_mapping["pharmacy"] == "pharmacy_name (약국명)"
    assert resolved_mapping["product"] in {"brand (브랜드)", "sku (SKU)"}
    assert resolved_mapping["quantity"] == "qty (수량)"
    assert missing_required == []
