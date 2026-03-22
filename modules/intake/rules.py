from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class IntakeRule:
    source_key: str
    required_fields: tuple[str, ...]
    field_aliases: dict[str, tuple[str, ...]]
    review_fields: tuple[str, ...] = field(default_factory=tuple)


_STANDARD_RULES: dict[str, IntakeRule] = {
    "crm_activity": IntakeRule(
        source_key="crm_activity",
        required_fields=("activity_date", "rep", "account", "activity_type"),
        review_fields=("notes", "product"),
        field_aliases={
            "activity_date": ("activity_date", "visit_date", "방문일", "방문일자", "활동일", "실행일", "date"),
            "rep": ("rep_id", "rep_name", "담당자", "담당자명", "사원명", "영업사원명", "영업사원코드"),
            "account": ("hospital_id", "hospital_name", "account_id", "병원코드", "병원명", "거래처명", "방문기관"),
            "activity_type": ("activity_type", "활동유형", "액션유형", "activity", "call_type", "접점채널"),
            "notes": ("note", "notes", "활동내용", "코멘트"),
            "product": ("product_id", "product_name", "품목", "제품", "brand"),
        },
    ),
    "crm_rep_master": IntakeRule(
        source_key="crm_rep_master",
        required_fields=("rep", "organization"),
        review_fields=("role",),
        field_aliases={
            "rep": ("rep_id", "rep_name", "담당자id", "담당자명", "사원번호", "사원명", "영업사원명", "영업사원코드"),
            "organization": ("branch_name", "team_name", "조직", "지점", "팀", "부서", "본부명", "본부코드"),
            "role": ("role", "직무", "직책"),
        },
    ),
    "crm_account_assignment": IntakeRule(
        source_key="crm_account_assignment",
        required_fields=("account", "rep"),
        field_aliases={
            "account": ("hospital_id", "hospital_name", "account_id", "병원코드", "병원명", "거래처명", "거래처코드"),
            "rep": ("rep_id", "rep_name", "담당자id", "담당자명", "사원명", "영업사원명"),
        },
    ),
    "crm_rules": IntakeRule(
        source_key="crm_rules",
        required_fields=(),
        review_fields=("rule_name", "rule_value"),
        field_aliases={
            "rule_name": ("rule_name", "rule", "규칙명", "kpi_name"),
            "rule_value": ("rule_value", "value", "기준값", "가중치"),
        },
    ),
    "sales": IntakeRule(
        source_key="sales",
        required_fields=("account", "product", "amount", "period"),
        review_fields=("rep",),
        field_aliases={
            "account": ("hospital_id", "hospital_name", "account_id", "병원코드", "병원명", "거래처명", "거래처코드"),
            "product": ("product_id", "product_name", "품목코드", "품목명", "제품명", "브랜드명", "브랜드코드"),
            "amount": ("sales_amount", "amount", "매출", "매출액", "매출금액", "금액"),
            "period": ("yyyymm", "sales_month", "month", "매출월", "기준년월", "월"),
            "rep": ("rep_id", "rep_name", "담당자", "사원명", "영업사원명"),
        },
    ),
    "target": IntakeRule(
        source_key="target",
        required_fields=("period", "target_value"),
        review_fields=("account", "rep", "product"),
        field_aliases={
            "period": ("yyyymm", "target_month", "month", "목표월", "기준년월", "월"),
            "target_value": ("target_amount", "target_qty", "목표금액", "목표수량", "계획금액", "목표"),
            "account": ("hospital_id", "hospital_name", "병원코드", "병원명"),
            "rep": ("rep_id", "rep_name", "담당자", "사원명", "영업사원명"),
            "product": ("product_id", "product_name", "품목명", "제품명"),
        },
    ),
    "prescription": IntakeRule(
        source_key="prescription",
        required_fields=("ship_date", "pharmacy", "product", "quantity"),
        review_fields=("hospital", "amount"),
        field_aliases={
            "ship_date": ("ship_date", "date", "출고일", "납품일", "ship_date출고일"),
            "pharmacy": ("pharmacy_name", "약국명", "약국", "customer_name", "pharmacy_account_id"),
            "product": ("product_id", "product_name", "품목명", "제품명", "brand", "brand브랜드", "sku", "skusku"),
            "quantity": ("qty", "quantity", "수량", "출고수량"),
            "hospital": ("hospital_name", "병원명", "account_name"),
            "amount": ("amount", "sales_amount", "공급가액", "출고금액", "amount_ship"),
        },
    ),
}


def get_intake_rule(source_key: str) -> IntakeRule | None:
    return _STANDARD_RULES.get(source_key)


def list_intake_rules() -> list[IntakeRule]:
    return list(_STANDARD_RULES.values())
