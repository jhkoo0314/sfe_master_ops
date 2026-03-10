from __future__ import annotations

from dataclasses import dataclass
from itertools import cycle
from pathlib import Path
import random

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw"
OUTPUT_ROOT = ROOT / "data" / "raw" / "company_source" / "hangyeol_pharma"

SEED = 20260310
random.seed(SEED)
np.random.seed(SEED)


SURNAMES = [
    "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
    "한", "오", "서", "신", "권", "황", "안", "송", "류", "전",
]
GIVEN_NAMES = [
    "민준", "서연", "도윤", "하린", "지민", "예린", "우진", "서준", "수아", "지후",
    "현우", "나연", "유진", "태윤", "가은", "선우", "시우", "소연", "주원", "다은",
]
SPECIALTIES = [
    "내과", "가정의학과", "소아청소년과", "정형외과", "이비인후과",
    "신경과", "재활의학과", "비뇨의학과", "산부인과", "피부과",
]
ACTIVITY_TYPES = ["접근", "컨택", "대면", "PT", "시연", "니즈환기", "클로징", "피드백"]
TRUST_LEVELS = ["verified", "assisted", "self_only"]
CHANNELS = ["대면", "전화", "문자", "이메일", "화상"]
ACTIVITY_WEIGHTS = {
    "PT": 3.5,
    "시연": 3.0,
    "클로징": 4.0,
    "대면": 2.0,
    "니즈환기": 1.5,
    "컨택": 1.2,
    "접근": 1.0,
    "피드백": 1.0,
}
REGION_CENTROIDS = {
    "서울특별시": (37.5665, 126.9780),
    "부산광역시": (35.1796, 129.0756),
    "대구광역시": (35.8714, 128.6014),
    "인천광역시": (37.4563, 126.7052),
    "광주광역시": (35.1595, 126.8526),
    "대전광역시": (36.3504, 127.3845),
    "울산광역시": (35.5384, 129.3114),
    "세종특별자치시": (36.4800, 127.2890),
    "경기도": (37.4138, 127.5183),
    "강원특별자치도": (37.8228, 128.1555),
    "충청북도": (36.6357, 127.4917),
    "충청남도": (36.6588, 126.6728),
    "전북특별자치도": (35.8242, 127.1480),
    "전라남도": (34.8161, 126.4630),
    "경상북도": (36.4919, 128.8889),
    "경상남도": (35.4606, 128.2132),
    "제주특별자치도": (33.4996, 126.5312),
}


@dataclass
class RepProfile:
    rep_id: str
    rep_name: str
    branch_id: str
    branch_name: str
    rep_role: str
    channel_focus: str
    product_focus_group: str
    account_capacity: int


def unique_names(count: int) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    surname_idx = 0
    given_idx = 0
    while len(names) < count:
        candidate = f"{SURNAMES[surname_idx % len(SURNAMES)]}{GIVEN_NAMES[given_idx % len(GIVEN_NAMES)]}"
        given_idx += 1
        if given_idx % len(GIVEN_NAMES) == 0:
            surname_idx += 1
        if candidate in seen:
            candidate = f"{candidate}{len(names) % 9 + 1}"
        seen.add(candidate)
        names.append(candidate)
    return names


def synthesize_coord(region_key: str, sub_region_key: str, account_id: str) -> tuple[float, float]:
    base_lat, base_lng = REGION_CENTROIDS.get(region_key, (36.5, 127.8))
    seed = sum(ord(ch) for ch in f"{region_key}|{sub_region_key}|{account_id}")
    rng = random.Random(seed)
    lat = round(base_lat + rng.uniform(-0.08, 0.08), 6)
    lng = round(base_lng + rng.uniform(-0.08, 0.08), 6)
    return lat, lng


def split_korean_address(address: str) -> tuple[str, str]:
    parts = str(address).strip().split()
    region = parts[0] if len(parts) >= 1 else "미상"
    sub_region = parts[1] if len(parts) >= 2 else "미상"
    return region, sub_region


def branch_distribution(branch_df: pd.DataFrame, total: int) -> list[int]:
    weights = branch_df["hospital_count"] / branch_df["hospital_count"].sum()
    raw = (weights * total).round().astype(int)
    diff = total - raw.sum()
    order = list(weights.sort_values(ascending=False).index)
    idx = 0
    while diff != 0:
        target = order[idx % len(order)]
        raw.loc[target] += 1 if diff > 0 else -1
        diff += -1 if diff > 0 else 1
        idx += 1
    return raw.tolist()


def build_rep_master(branch_df: pd.DataFrame) -> pd.DataFrame:
    clinic_counts = branch_distribution(branch_df, 80)
    hospital_counts = branch_distribution(branch_df, 45)
    rep_names = unique_names(125)

    profiles: list[RepProfile] = []
    name_idx = 0
    for row, clinic_count, hospital_count in zip(branch_df.itertuples(index=False), clinic_counts, hospital_counts):
        for seq in range(clinic_count):
            rep_code = f"CR{len([p for p in profiles if p.rep_role == '의원']) + 1:03d}"
            profiles.append(
                RepProfile(
                    rep_id=rep_code,
                    rep_name=rep_names[name_idx],
                    branch_id=row.branch_id,
                    branch_name=row.branch_name,
                    rep_role="의원",
                    channel_focus="Clinic",
                    product_focus_group="의원 중심 브랜드군",
                    account_capacity=random.randint(10, 16),
                )
            )
            name_idx += 1
        for seq in range(hospital_count):
            rep_code = f"HR{len([p for p in profiles if p.rep_role == '종합병원']) + 1:03d}"
            profiles.append(
                RepProfile(
                    rep_id=rep_code,
                    rep_name=rep_names[name_idx],
                    branch_id=row.branch_id,
                    branch_name=row.branch_name,
                    rep_role="종합병원",
                    channel_focus="General Hospital",
                    product_focus_group="병원 중심 브랜드군",
                    account_capacity=random.randint(6, 10),
                )
            )
            name_idx += 1

    rep_df = pd.DataFrame([p.__dict__ for p in profiles])
    return rep_df


def synthesize_clinic_accounts(branch_df: pd.DataFrame, rep_df: pd.DataFrame) -> pd.DataFrame:
    clinic_rows: list[dict] = []
    city_lookup = {
        "서울지점": "서울특별시",
        "경기지점": "경기도",
        "인천지점": "인천광역시",
        "부산지점": "부산광역시",
        "대구지점": "대구광역시",
        "광주지점": "광주광역시",
        "대전지점": "대전광역시",
        "울산지점": "울산광역시",
        "강원지점": "강원특별자치도",
        "제주지점": "제주특별자치도",
    }
    clinic_reps = rep_df[rep_df["rep_role"] == "의원"].copy()
    serial = 1
    for row in clinic_reps.itertuples(index=False):
        clinic_count = random.randint(10, 14)
        city = city_lookup.get(row.branch_name, "경기도")
        for _ in range(clinic_count):
            doctor = random.choice(SURNAMES) + random.choice(GIVEN_NAMES)
            specialty = random.choice(SPECIALTIES)
            account_name = f"{doctor}{specialty}의원"
            district = f"{random.randint(1, 25)}구"
            clinic_rows.append(
                {
                    "account_id": f"C{serial:04d}",
                    "account_name": account_name,
                    "account_type": "의원",
                    "branch_id": row.branch_id,
                    "branch_name": row.branch_name,
                    "rep_id": row.rep_id,
                    "rep_name": row.rep_name,
                    "address": f"{city} {district} {specialty}로 {random.randint(10, 300)}",
                    "region_key": city,
                    "sub_region_key": district,
                    "channel_focus": "Clinic",
                }
            )
            serial += 1
    return pd.DataFrame(clinic_rows)


def build_account_master() -> tuple[pd.DataFrame, pd.DataFrame]:
    assignment = pd.read_excel(RAW_ROOT / "company" / "sample_hospital_assignment_data.xlsx")
    branch_df = (
        assignment.groupby(["지점ID", "지점명"], as_index=False)
        .agg(hospital_count=("병원ID", "count"))
        .rename(columns={"지점ID": "branch_id", "지점명": "branch_name"})
    )
    rep_df = build_rep_master(branch_df)

    hospital_reps = rep_df[rep_df["rep_role"] == "종합병원"].reset_index(drop=True)
    hospital_base = assignment.copy().rename(
        columns={
            "병원ID": "account_id",
            "요양기관명": "account_name",
            "종별코드명": "account_type",
            "주소": "address",
        }
    )
    region_split = hospital_base["address"].astype(str).str.split()
    hospital_base["region_key"] = region_split.str[0].fillna("미상")
    hospital_base["sub_region_key"] = region_split.str[1].fillna("미상")
    hospital_base["channel_focus"] = "General Hospital"
    hospital_base = hospital_base[
        ["account_id", "account_name", "account_type", "address", "region_key", "sub_region_key", "channel_focus"]
    ]
    hospital_base["rep_id"] = ""
    hospital_base["rep_name"] = ""
    hospital_base["branch_id"] = ""
    hospital_base["branch_name"] = ""

    hospital_idx = 0
    for rep in hospital_reps.itertuples(index=False):
        cap = rep.account_capacity
        subset = hospital_base.iloc[hospital_idx:hospital_idx + cap].copy()
        if subset.empty:
            break
        hospital_base.loc[subset.index, "rep_id"] = rep.rep_id
        hospital_base.loc[subset.index, "rep_name"] = rep.rep_name
        hospital_base.loc[subset.index, "branch_id"] = rep.branch_id
        hospital_base.loc[subset.index, "branch_name"] = rep.branch_name
        hospital_idx += cap

    if hospital_base["rep_id"].eq("").any():
        leftovers = hospital_base[hospital_base["rep_id"].eq("")]
        rep_cycle = cycle(hospital_reps.itertuples(index=False))
        for idx, rep in zip(leftovers.index, rep_cycle):
            hospital_base.loc[idx, ["rep_id", "rep_name", "branch_id", "branch_name"]] = [
                rep.rep_id, rep.rep_name, rep.branch_id, rep.branch_name
            ]

    clinic_base = synthesize_clinic_accounts(branch_df, rep_df)
    account_master = pd.concat([hospital_base, clinic_base], ignore_index=True)
    account_master = account_master.merge(
        rep_df[["rep_id", "rep_role", "channel_focus", "product_focus_group"]],
        on="rep_id",
        how="left",
        suffixes=("", "_rep"),
    )
    account_master["channel_focus"] = account_master["channel_focus"].fillna(account_master["channel_focus_rep"])
    account_master["product_focus_group"] = account_master["product_focus_group"].fillna("미정")
    account_master = account_master.drop(columns=["channel_focus_rep"])
    coords = account_master.apply(
        lambda row: synthesize_coord(str(row["region_key"]), str(row["sub_region_key"]), str(row["account_id"])),
        axis=1,
        result_type="expand",
    )
    account_master["latitude"] = coords[0]
    account_master["longitude"] = coords[1]
    account_master["company_name"] = "한결제약"
    return rep_df, account_master


def build_company_assignment(account_master: pd.DataFrame, rep_df: pd.DataFrame) -> pd.DataFrame:
    merged = account_master.merge(
        rep_df[["rep_id", "rep_role", "account_capacity", "product_focus_group"]],
        on="rep_id",
        how="left",
    )
    assignment_raw = merged.rename(
        columns={
            "rep_id": "영업사원코드",
            "rep_name": "영업사원명",
            "branch_id": "본부코드",
            "branch_name": "본부명",
            "account_id": "거래처코드",
            "account_name": "거래처명",
            "account_type": "기관구분",
            "address": "주소원본",
            "region_key": "광역시도",
            "sub_region_key": "시군구",
            "rep_role": "담당채널",
            "channel_focus": "주력채널",
            "product_focus_group": "제품집중군",
            "account_capacity": "배정가능계정수",
        }
    )
    for dup_col in ["rep_role_x", "rep_role_y", "product_focus_group_x", "product_focus_group_y"]:
        if dup_col in assignment_raw.columns:
            assignment_raw = assignment_raw.drop(columns=[dup_col])
    assignment_raw["주담당여부"] = "Y"
    assignment_raw["거래처명"] = assignment_raw["거래처명"].mask(
        assignment_raw.index % 13 == 0,
        assignment_raw["거래처명"].str.replace("의원", " 의원", regex=False),
    )
    return assignment_raw


def portfolio_frame() -> pd.DataFrame:
    return pd.read_csv(ROOT / "docs" / "hangyeol-pharma-portfolio-draft.csv")


def product_pool(portfolio: pd.DataFrame, account_type: str) -> pd.DataFrame:
    if account_type == "의원":
        return portfolio[portfolio["care_setting"].isin(["Clinic", "Mixed"])].copy()
    return portfolio[portfolio["care_setting"].isin(["General Hospital", "Mixed"])].copy()


def choose_products(portfolio: pd.DataFrame, account_type: str) -> list[dict]:
    pool = product_pool(portfolio, account_type)
    size = random.randint(3, 5) if account_type == "의원" else random.randint(4, 6)
    sampled = pool.sample(n=min(size, len(pool)), replace=False, random_state=random.randint(1, 999999))
    return sampled.to_dict("records")


def generate_crm_raw(account_master: pd.DataFrame, portfolio: pd.DataFrame) -> pd.DataFrame:
    business_days = pd.date_range("2026-01-01", "2026-03-31", freq="B")
    rows: list[dict] = []
    rep_type_weights = {
        "의원": [0.18, 0.24, 0.22, 0.06, 0.04, 0.10, 0.08, 0.08],
        "종합병원": [0.08, 0.12, 0.18, 0.18, 0.14, 0.10, 0.12, 0.08],
    }
    trust_weights = [0.48, 0.36, 0.16]

    for account in account_master.itertuples(index=False):
        monthly_contacts = random.randint(4, 7) if account.account_type == "의원" else random.randint(6, 10)
        account_products = choose_products(portfolio, account.account_type)
        for month_start in pd.date_range("2026-01-01", "2026-03-01", freq="MS"):
            month_days = [d for d in business_days if d.month == month_start.month]
            sample_days = random.sample(month_days, k=min(monthly_contacts, len(month_days)))
            for act_day in sample_days:
                activity = random.choices(ACTIVITY_TYPES, weights=rep_type_weights[account.rep_role], k=1)[0]
                activity_weight = ACTIVITY_WEIGHTS[activity]
                trust = random.choices(TRUST_LEVELS, weights=trust_weights, k=1)[0]
                product_names = [p["canonical_brand"] for p in random.sample(account_products, k=min(len(account_products), random.randint(1, 2)))]
                next_gap = random.randint(3, 21)
                next_date = act_day + pd.Timedelta(days=next_gap)
                note_seed = f"{activity} 이후 {product_names[0]} 중심 follow-up 필요"
                if random.random() < 0.08:
                    note_seed = "재방문 예정"
                visit_count = random.randint(1, 2)
                quality_factor = round(random.uniform(0.7, 1.3), 2)
                impact_factor = round(random.uniform(0.8, 1.5), 2)
                rows.append(
                    {
                        "실행일": act_day.strftime("%Y/%m/%d") if random.random() < 0.5 else act_day.strftime("%Y-%m-%d"),
                        "영업사원코드": account.rep_id,
                        "영업사원명": account.rep_name,
                        "방문기관": account.account_name if random.random() < 0.9 else f" {account.account_name}",
                        "기관위도": account.latitude,
                        "기관경도": account.longitude,
                        "액션유형": activity,
                        "접점채널": random.choice(CHANNELS),
                        "언급브랜드": ", ".join(product_names),
                        "활동메모": note_seed,
                        "차기액션": "원내 key doctor follow-up" if account.account_type != "의원" else "처방 패턴 확인 및 재접촉",
                        "차기액션일": next_date.strftime("%Y-%m-%d"),
                        "신뢰등급": trust,
                        "정서점수": round(random.uniform(0.4, 1.0), 2),
                        "품질계수": quality_factor,
                        "영향계수": impact_factor,
                        "행동가중치": activity_weight,
                        "가중활동점수": round(activity_weight * quality_factor * impact_factor, 2),
                        "중복의심": "Y" if random.random() < 0.04 else "N",
                        "상세콜여부": "Y" if activity in {"PT", "시연", "클로징"} else "N",
                        "방문횟수": visit_count,
                    }
                )
    crm_df = pd.DataFrame(rows).sort_values(["실행일", "영업사원코드"]).reset_index(drop=True)
    return crm_df


def generate_target_and_sales(account_master: pd.DataFrame, portfolio: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    months = pd.period_range("2026-01", "2026-06", freq="M")
    target_rows: list[dict] = []
    sales_rows: list[dict] = []
    for account in account_master.itertuples(index=False):
        products = choose_products(portfolio, account.account_type)
        base_scale = 1.6 if account.account_type != "의원" else 1.0
        for month in months:
            seasonality = 1.12 if month.month in (1, 2) else 1.0
            for product in products:
                strategic_weight = float(product["strategic_weight"])
                target_amount = int(random.randint(900000, 2200000) * strategic_weight * base_scale * seasonality)
                attainment = np.clip(np.random.normal(loc=1.01 if account.rep_role == "의원" else 0.98, scale=0.14), 0.62, 1.38)
                sales_amount = int(target_amount * attainment)
                target_rows.append(
                    {
                        "기준년월": str(month),
                        "본부코드": account.branch_id,
                        "본부명": account.branch_name,
                        "영업사원코드": account.rep_id,
                        "영업사원명": account.rep_name,
                        "거래처코드": account.account_id,
                        "거래처명": account.account_name,
                        "브랜드코드": product["canonical_product_id"],
                        "브랜드명": product["canonical_brand"],
                        "계획금액": target_amount,
                    }
                )
                sales_rows.append(
                    {
                        "기준년월": str(month),
                        "본부코드": account.branch_id,
                        "본부명": account.branch_name,
                        "영업사원코드": account.rep_id,
                        "영업사원명": account.rep_name,
                        "거래처코드": account.account_id,
                        "거래처명": account.account_name,
                        "브랜드코드": product["canonical_product_id"],
                        "브랜드명": product["canonical_brand"],
                        "계획금액": target_amount,
                        "매출금액": sales_amount,
                        "달성률": round(sales_amount / target_amount * 100, 1),
                        "매출수량": max(1, int(sales_amount / random.randint(18000, 78000))),
                    }
                )
    return pd.DataFrame(target_rows), pd.DataFrame(sales_rows)


def transform_fact_ship(portfolio: pd.DataFrame) -> pd.DataFrame:
    fact_ship = pd.read_csv(RAW_ROOT / "company" / "sample_fact_ship_pharmacy_raw_label.csv")
    allowed = set(portfolio["canonical_brand"])
    ship_df = fact_ship[fact_ship["brand (브랜드)"].isin(allowed)].copy()
    ship_df["manufacturer_name (제약사)"] = "한결제약"
    ship_df["mfg_to_wholesaler_path (제약사-도매상경로)"] = (
        "한결제약->" + ship_df["wholesaler_name (도매상명)"].astype(str)
    )
    ship_df["data_source (데이터소스)"] = "hangyeol_source_simulated"
    ship_df.loc[ship_df.index[::17], "wholesaler_raw_name (도매원본명)"] = (
        ship_df.loc[ship_df.index[::17], "wholesaler_name (도매상명)"].astype(str).str.replace("주식회사 ", "", regex=False)
    )
    pharmacy_regions = ship_df["pharmacy_addr (약국주소)"].astype(str).apply(split_korean_address)
    ship_df["pharmacy_region_key (약국시도)"] = pharmacy_regions.str[0]
    ship_df["pharmacy_sub_region_key (약국시군구)"] = pharmacy_regions.str[1]
    ship_df["wholesaler_region_key (도매시도)"] = ship_df["pharmacy_region_key (약국시도)"]
    pharmacy_coords = ship_df.apply(
        lambda row: synthesize_coord(
            str(row["pharmacy_region_key (약국시도)"]),
            str(row["pharmacy_sub_region_key (약국시군구)"]),
            str(row["pharmacy_name (약국명)"]),
        ),
        axis=1,
        result_type="expand",
    )
    ship_df["pharmacy_latitude (약국위도)"] = pharmacy_coords[0]
    ship_df["pharmacy_longitude (약국경도)"] = pharmacy_coords[1]
    wholesaler_coords = ship_df.apply(
        lambda row: synthesize_coord(
            str(row["wholesaler_region_key (도매시도)"]),
            str(row["pharmacy_sub_region_key (약국시군구)"]),
            str(row["wholesaler_name (도매상명)"]),
        ),
        axis=1,
        result_type="expand",
    )
    ship_df["wholesaler_latitude (도매위도)"] = wholesaler_coords[0]
    ship_df["wholesaler_longitude (도매경도)"] = wholesaler_coords[1]
    return ship_df


def write_outputs(rep_df: pd.DataFrame, account_master: pd.DataFrame, assignment_raw: pd.DataFrame,
                  crm_raw: pd.DataFrame, target_raw: pd.DataFrame, sales_raw: pd.DataFrame,
                  ship_raw: pd.DataFrame) -> None:
    (OUTPUT_ROOT / "crm").mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "sales").mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "target").mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "company").mkdir(parents=True, exist_ok=True)

    rep_df.to_excel(OUTPUT_ROOT / "company" / "hangyeol_rep_master.xlsx", index=False)
    account_master.to_excel(OUTPUT_ROOT / "company" / "hangyeol_account_master.xlsx", index=False)
    assignment_raw.to_excel(OUTPUT_ROOT / "company" / "hangyeol_company_assignment_raw.xlsx", index=False)
    crm_raw.to_excel(OUTPUT_ROOT / "crm" / "hangyeol_crm_activity_raw.xlsx", index=False)
    target_raw.to_excel(OUTPUT_ROOT / "target" / "hangyeol_target_raw.xlsx", index=False)
    sales_raw.to_excel(OUTPUT_ROOT / "sales" / "hangyeol_sales_raw.xlsx", index=False)
    ship_raw.to_csv(OUTPUT_ROOT / "company" / "hangyeol_fact_ship_raw.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    portfolio = portfolio_frame()
    rep_df, account_master = build_account_master()
    assignment_raw = build_company_assignment(account_master, rep_df)
    crm_raw = generate_crm_raw(account_master, portfolio)
    target_raw, sales_raw = generate_target_and_sales(account_master, portfolio)
    ship_raw = transform_fact_ship(portfolio)
    write_outputs(rep_df, account_master, assignment_raw, crm_raw, target_raw, sales_raw, ship_raw)

    print("Generated Hangyeol source raw files:")
    print(f"  reps={len(rep_df)}")
    print(f"  accounts={len(account_master)}")
    print(f"  crm_rows={len(crm_raw)}")
    print(f"  target_rows={len(target_raw)}")
    print(f"  sales_rows={len(sales_raw)}")
    print(f"  ship_rows={len(ship_raw)}")
    print(f"  output={OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
