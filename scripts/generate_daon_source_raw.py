from __future__ import annotations

import random
from dataclasses import dataclass
from itertools import cycle
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROOT = ROOT / "data" / "public"
OUTPUT_ROOT = ROOT / "data" / "company_source" / "daon_pharma"
PORTFOLIO_PATH = ROOT / "docs" / "hangyeol-pharma-portfolio-draft.csv"

COMPANY_KEY = "daon_pharma"
COMPANY_NAME = "다온제약"
SEED = 20260310
CLINIC_REP_COUNT = 75
HOSPITAL_REP_COUNT = 33
START_DATE = "2025-01-01"
END_DATE = "2025-12-31"

random.seed(SEED)
np.random.seed(SEED)

ACTIVITY_TYPES = ["접근", "컨택", "대면", "pt", "시연", "니즈환기", "클로징", "피드백"]
TRUST_LEVELS = ["verified", "assisted", "self_only"]
CHANNELS = ["대면", "전화", "문자", "이메일", "화상"]
ACTIVITY_WEIGHTS = {
    "pt": 3.5,
    "시연": 3.0,
    "클로징": 4.0,
    "대면": 2.0,
    "니즈환기": 1.5,
    "컨택": 1.2,
    "접근": 1.0,
    "피드백": 1.0,
}
BRANCH_DEFS = [
    {"branch_id": "B01", "branch_name": "서울지점", "regions": ["서울"]},
    {"branch_id": "B02", "branch_name": "경기지점", "regions": ["경기"]},
    {"branch_id": "B03", "branch_name": "인천지점", "regions": ["인천"]},
    {"branch_id": "B04", "branch_name": "부산지점", "regions": ["부산", "경남"]},
    {"branch_id": "B05", "branch_name": "대구지점", "regions": ["대구", "경북"]},
    {"branch_id": "B06", "branch_name": "광주지점", "regions": ["광주", "전남", "전북"]},
    {"branch_id": "B07", "branch_name": "대전지점", "regions": ["대전", "충남", "충북", "세종"]},
    {"branch_id": "B08", "branch_name": "울산지점", "regions": ["울산"]},
    {"branch_id": "B09", "branch_name": "강원지점", "regions": ["강원"]},
    {"branch_id": "B10", "branch_name": "제주지점", "regions": ["제주"]},
]
SURNAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황", "안", "송", "류", "전"]
GIVEN_NAMES = [
    "민준", "서연", "도윤", "하린", "지민", "예린", "우진", "서준", "수아", "지후",
    "현우", "나연", "유진", "태윤", "가은", "선우", "시우", "소연", "주원", "다은",
]


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


def load_portfolio() -> pd.DataFrame:
    portfolio = pd.read_csv(PORTFOLIO_PATH).copy()
    portfolio["company_name"] = COMPANY_NAME
    return portfolio


def load_hospital_pool() -> pd.DataFrame:
    usecols = [
        "암호화요양기호", "요양기관명", "종별코드명", "시도코드명", "시군구코드명",
        "주소", "전화번호", "총의사수", "좌표(X)", "좌표(Y)",
    ]
    df = pd.read_excel(PUBLIC_ROOT / "1.병원정보서비스(2025.12.).xlsx", usecols=usecols)
    df = df.rename(
        columns={
            "암호화요양기호": "account_id",
            "요양기관명": "account_name",
            "종별코드명": "account_type",
            "시도코드명": "region_key",
            "시군구코드명": "sub_region_key",
            "주소": "address",
            "전화번호": "phone",
            "총의사수": "doctor_count",
            "좌표(X)": "longitude",
            "좌표(Y)": "latitude",
        }
    )
    df = df[df["region_key"].isin({region for branch in BRANCH_DEFS for region in branch["regions"]})].copy()
    df["doctor_count"] = df["doctor_count"].fillna(1).astype(int)
    df["account_name"] = df["account_name"].astype(str).str.strip()
    df = df.dropna(subset=["account_id", "account_name", "account_type", "region_key", "sub_region_key"])
    return df


def load_pharmacy_pool() -> pd.DataFrame:
    usecols = ["암호화요양기호", "요양기관명", "시도코드명", "시군구코드명", "우편번호", "주소", "전화번호", "좌표(X)", "좌표(Y)"]
    df = pd.read_excel(PUBLIC_ROOT / "2.약국정보서비스(2025.12.).xlsx", usecols=usecols)
    df = df.rename(
        columns={
            "암호화요양기호": "pharmacy_account_id",
            "요양기관명": "pharmacy_name",
            "시도코드명": "pharmacy_region_key",
            "시군구코드명": "pharmacy_sub_region_key",
            "우편번호": "postal_code",
            "주소": "pharmacy_addr",
            "전화번호": "pharmacy_phone",
            "좌표(X)": "pharmacy_longitude",
            "좌표(Y)": "pharmacy_latitude",
        }
    )
    df = df[df["pharmacy_region_key"].isin({region for branch in BRANCH_DEFS for region in branch["regions"]})].copy()
    return df.dropna(subset=["pharmacy_account_id", "pharmacy_name", "pharmacy_region_key", "pharmacy_sub_region_key"])


def load_wholesaler_pool() -> pd.DataFrame:
    df = pd.read_csv(PUBLIC_ROOT / "3. 전국의약품도매업소표준데이터.csv")
    df = df[df["business_type(업종명)"].isin(["일반종합도매", "수입의약품도매"])].copy()
    df = df[df["business_status(영업상태명)"] == "영업"].copy()
    df["region_key"] = df["road_address(소재지도로명주소)"].astype(str).str.split().str[0]
    short_region_map = {
        "서울특별시": "서울", "경기도": "경기", "인천광역시": "인천", "부산광역시": "부산", "대구광역시": "대구",
        "광주광역시": "광주", "대전광역시": "대전", "울산광역시": "울산", "강원특별자치도": "강원",
        "제주특별자치도": "제주", "경상남도": "경남", "경상북도": "경북", "전라남도": "전남", "전북특별자치도": "전북",
        "충청남도": "충남", "충청북도": "충북", "세종특별자치시": "세종",
    }
    df["region_key"] = df["region_key"].map(short_region_map).fillna(df["region_key"])
    df = df[df["region_key"].isin({region for branch in BRANCH_DEFS for region in branch["regions"]})].copy()
    df = df.rename(
        columns={
            "facility_name(시설명)": "wholesaler_name",
            "road_address(소재지도로명주소)": "road_address",
            "latitude(위도)": "wholesaler_latitude",
            "longitude(경도)": "wholesaler_longitude",
            "phone(전화번호)": "wholesaler_phone",
        }
    )
    return df.dropna(subset=["wholesaler_name", "region_key"])


def _allocate_counts(branch_bases: pd.DataFrame, total: int) -> list[int]:
    weights = branch_bases["weight"] / branch_bases["weight"].sum()
    raw = (weights * total).round().astype(int)
    diff = int(total - raw.sum())
    order = list(weights.sort_values(ascending=False).index)
    idx = 0
    while diff != 0:
        target = order[idx % len(order)]
        raw.loc[target] += 1 if diff > 0 else -1
        diff += -1 if diff > 0 else 1
        idx += 1
    return raw.tolist()


def build_rep_master(clinic_accounts: pd.DataFrame, hospital_accounts: pd.DataFrame) -> pd.DataFrame:
    clinic_base = clinic_accounts.groupby(["branch_id", "branch_name"], as_index=False).size().rename(columns={"size": "weight"})
    hospital_base = hospital_accounts.groupby(["branch_id", "branch_name"], as_index=False).size().rename(columns={"size": "weight"})
    clinic_counts = _allocate_counts(clinic_base, CLINIC_REP_COUNT)
    hospital_counts = _allocate_counts(hospital_base, HOSPITAL_REP_COUNT)
    rep_names = unique_names(CLINIC_REP_COUNT + HOSPITAL_REP_COUNT)
    name_idx = 0
    profiles: list[RepProfile] = []

    for row, count in zip(clinic_base.itertuples(index=False), clinic_counts):
        for _ in range(count):
            profiles.append(
                RepProfile(
                    rep_id=f"CR{len([p for p in profiles if p.rep_role == '의원']) + 1:03d}",
                    rep_name=rep_names[name_idx],
                    branch_id=row.branch_id,
                    branch_name=row.branch_name,
                    rep_role="의원",
                    channel_focus="Clinic",
                    product_focus_group="의원 성장군",
                    account_capacity=random.randint(12, 18),
                )
            )
            name_idx += 1
    for row, count in zip(hospital_base.itertuples(index=False), hospital_counts):
        for _ in range(count):
            profiles.append(
                RepProfile(
                    rep_id=f"HR{len([p for p in profiles if p.rep_role == '종합병원']) + 1:03d}",
                    rep_name=rep_names[name_idx],
                    branch_id=row.branch_id,
                    branch_name=row.branch_name,
                    rep_role="종합병원",
                    channel_focus="General Hospital",
                    product_focus_group="병원 핵심군",
                    account_capacity=random.randint(5, 9),
                )
            )
            name_idx += 1
    return pd.DataFrame([p.__dict__ for p in profiles])


def attach_branch(account_df: pd.DataFrame) -> pd.DataFrame:
    branch_rows = []
    for branch in BRANCH_DEFS:
        for region in branch["regions"]:
            branch_rows.append(
                {
                    "region_key": region,
                    "branch_id": branch["branch_id"],
                    "branch_name": branch["branch_name"],
                }
            )
    branch_map = pd.DataFrame(branch_rows)
    return account_df.merge(branch_map, on="region_key", how="left")


def select_accounts(hospital_pool: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    clinics = hospital_pool[hospital_pool["account_type"] == "의원"].copy()
    hospitals = hospital_pool[hospital_pool["account_type"].isin(["병원", "종합병원", "상급종합"])].copy()
    hospitals = hospitals[hospitals["doctor_count"] >= 20].copy()

    clinics = attach_branch(clinics)
    hospitals = attach_branch(hospitals)
    clinics = clinics.dropna(subset=["branch_id"])
    hospitals = hospitals.dropna(subset=["branch_id"])

    clinic_counts = {"서울지점": 190, "경기지점": 250, "인천지점": 80, "부산지점": 120, "대구지점": 90, "광주지점": 90, "대전지점": 120, "울산지점": 45, "강원지점": 45, "제주지점": 25}
    hospital_counts = {"서울지점": 42, "경기지점": 46, "인천지점": 12, "부산지점": 28, "대구지점": 22, "광주지점": 16, "대전지점": 26, "울산지점": 8, "강원지점": 9, "제주지점": 4}

    clinic_selected = []
    for branch_name, count in clinic_counts.items():
        subset = clinics[clinics["branch_name"] == branch_name]
        sample_n = min(count, len(subset))
        clinic_selected.append(subset.sample(n=sample_n, random_state=SEED + sample_n))

    hospital_selected = []
    for branch_name, count in hospital_counts.items():
        subset = hospitals[hospitals["branch_name"] == branch_name]
        sample_n = min(count, len(subset))
        hospital_selected.append(subset.sample(n=sample_n, random_state=SEED + 100 + sample_n))

    clinic_df = pd.concat(clinic_selected, ignore_index=True)
    hospital_df = pd.concat(hospital_selected, ignore_index=True)
    return clinic_df, hospital_df


def assign_accounts_to_reps(account_df: pd.DataFrame, rep_df: pd.DataFrame, rep_role: str) -> pd.DataFrame:
    role_reps = rep_df[rep_df["rep_role"] == rep_role].copy()
    account_df = account_df.copy()
    account_df["rep_id"] = None
    account_df["rep_name"] = None
    account_df["channel_focus"] = role_reps["channel_focus"].iloc[0]
    account_df["product_focus_group"] = role_reps["product_focus_group"].iloc[0]

    for branch_name, branch_accounts in account_df.groupby("branch_name"):
        reps = role_reps[role_reps["branch_name"] == branch_name].copy().reset_index(drop=True)
        if reps.empty:
            continue
        account_indices = list(branch_accounts.index)
        random.shuffle(account_indices)
        cursor = 0
        for rep in reps.itertuples(index=False):
            take = min(rep.account_capacity, len(account_indices) - cursor)
            assigned = account_indices[cursor:cursor + take]
            account_df.loc[assigned, "rep_id"] = rep.rep_id
            account_df.loc[assigned, "rep_name"] = rep.rep_name
            cursor += take
        if cursor < len(account_indices):
            leftovers = account_indices[cursor:]
            rep_cycle = cycle(reps.itertuples(index=False))
            for idx, rep in zip(leftovers, rep_cycle):
                account_df.loc[idx, "rep_id"] = rep.rep_id
                account_df.loc[idx, "rep_name"] = rep.rep_name
    return account_df


def build_account_master(rep_df: pd.DataFrame, clinic_df: pd.DataFrame, hospital_df: pd.DataFrame) -> pd.DataFrame:
    clinic_assigned = assign_accounts_to_reps(clinic_df, rep_df, "의원")
    hospital_assigned = assign_accounts_to_reps(hospital_df, rep_df, "종합병원")
    account_master = pd.concat([clinic_assigned, hospital_assigned], ignore_index=True)
    account_master["company_name"] = COMPANY_NAME
    account_master["latitude"] = account_master["latitude"].round(6)
    account_master["longitude"] = account_master["longitude"].round(6)
    keep_cols = [
        "account_id", "account_name", "account_type", "branch_id", "branch_name", "rep_id", "rep_name",
        "address", "region_key", "sub_region_key", "channel_focus", "product_focus_group", "latitude", "longitude", "company_name",
    ]
    return account_master[keep_cols]


def build_company_assignment(account_master: pd.DataFrame, rep_df: pd.DataFrame) -> pd.DataFrame:
    assignment = account_master.merge(
        rep_df[["rep_id", "rep_role", "account_capacity", "product_focus_group"]],
        on="rep_id",
        how="left",
        suffixes=("", "_rep"),
    )
    assignment = assignment.rename(
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
            "product_focus_group_rep": "제품집중군",
            "account_capacity": "배정가능계정수",
        }
    )
    assignment["주담당여부"] = "Y"
    assignment.loc[assignment.index % 17 == 0, "거래처명"] = assignment.loc[assignment.index % 17 == 0, "거래처명"].str.replace("의원", " 의원", regex=False)
    assignment.loc[assignment.index % 41 == 0, "주담당여부"] = "y"
    return assignment


def choose_products(portfolio: pd.DataFrame, account_type: str) -> list[dict]:
    if account_type == "의원":
        pool = portfolio[portfolio["care_setting"].isin(["Clinic", "Mixed"])].copy()
        size = random.randint(3, 5)
    else:
        pool = portfolio[portfolio["care_setting"].isin(["General Hospital", "Mixed"])].copy()
        size = random.randint(4, 6)
    return pool.sample(n=min(size, len(pool)), random_state=random.randint(1, 999999)).to_dict("records")


def messy_account_name(name: str, idx: int) -> str:
    if idx % 37 == 0:
        return f" {name}"
    if idx % 43 == 0:
        return name.replace("의원", " 의원")
    if idx % 53 == 0:
        return name.replace("병원", " 병원")
    return name


def generate_crm_raw(account_master: pd.DataFrame, portfolio: pd.DataFrame) -> pd.DataFrame:
    business_days = pd.date_range(START_DATE, END_DATE, freq="B")
    rows: list[dict] = []
    rep_weights = {
        "의원": [0.16, 0.24, 0.25, 0.05, 0.03, 0.10, 0.07, 0.10],
        "종합병원": [0.08, 0.12, 0.18, 0.19, 0.12, 0.10, 0.15, 0.06],
    }

    for idx, account in enumerate(account_master.itertuples(index=False)):
        account_products = choose_products(portfolio, account.account_type)
        for month_start in pd.date_range(START_DATE, END_DATE, freq="MS"):
            monthly_contacts = random.randint(3, 6) if account.account_type == "의원" else random.randint(4, 8)
            month_days = [d for d in business_days if d.month == month_start.month]
            sample_days = random.sample(month_days, k=min(monthly_contacts, len(month_days)))
            for act_day in sample_days:
                activity = random.choices(ACTIVITY_TYPES, weights=rep_weights["의원" if account.account_type == "의원" else "종합병원"], k=1)[0]
                mentioned = random.sample(account_products, k=min(len(account_products), random.randint(1, 2)))
                product_names = [p["canonical_brand"] for p in mentioned]
                activity_weight = ACTIVITY_WEIGHTS[activity]
                quality_factor = round(random.uniform(0.72, 1.35), 2)
                impact_factor = round(random.uniform(0.75, 1.50), 2)
                note = f"{product_names[0]} 설명 후 follow-up 필요"
                if idx % 29 == 0:
                    note = "재방문 예정"
                next_action = "KOL 의견 반영 자료 전달" if account.account_type != "의원" else "처방 패턴 확인 및 재접촉"
                next_date = act_day + pd.Timedelta(days=random.randint(5, 28))
                rows.append(
                    {
                        "실행일": act_day.strftime("%Y/%m/%d") if (idx + act_day.day) % 2 == 0 else act_day.strftime("%Y-%m-%d"),
                        "영업사원코드": account.rep_id,
                        "영업사원명": account.rep_name,
                        "방문기관": messy_account_name(account.account_name, idx),
                        "기관위도": account.latitude,
                        "기관경도": account.longitude,
                        "액션유형": activity,
                        "접점채널": random.choice(CHANNELS),
                        "언급브랜드": ", ".join(product_names),
                        "활동메모": note,
                        "차기액션": next_action if idx % 31 != 0 else None,
                        "차기액션일": next_date.strftime("%Y-%m-%d"),
                        "신뢰등급": random.choices(TRUST_LEVELS, weights=[0.52, 0.34, 0.14], k=1)[0],
                        "정서점수": round(random.uniform(0.35, 1.00), 2),
                        "품질계수": quality_factor,
                        "영향계수": impact_factor,
                        "행동가중치": activity_weight,
                        "가중활동점수": round(activity_weight * quality_factor * impact_factor, 2),
                        "중복의심": "Y" if idx % 47 == 0 else "N",
                        "상세콜여부": "Y" if activity in {"pt", "시연", "클로징"} else "N",
                        "방문횟수": 2 if idx % 61 == 0 else 1,
                    }
                )
    crm_df = pd.DataFrame(rows).sort_values(["실행일", "영업사원코드"]).reset_index(drop=True)
    duplicate_rows = crm_df.sample(n=min(600, len(crm_df) // 80), random_state=SEED).copy()
    if not duplicate_rows.empty:
        duplicate_rows["중복의심"] = "Y"
        crm_df = pd.concat([crm_df, duplicate_rows], ignore_index=True)
    return crm_df


def product_name_variant(name: str, idx: int) -> str:
    if idx % 23 == 0:
        return f"{name} "
    if idx % 31 == 0:
        return name.replace("정", " 정", 1)
    return name


def generate_target_and_sales(account_master: pd.DataFrame, portfolio: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    months = pd.period_range("2025-01", "2025-12", freq="M")
    target_rows: list[dict] = []
    sales_rows: list[dict] = []
    for idx, account in enumerate(account_master.itertuples(index=False)):
        products = choose_products(portfolio, account.account_type)
        for month in months:
            seasonality = {1: 0.94, 2: 0.92, 3: 1.02, 4: 1.04, 5: 1.05, 6: 1.03, 7: 0.97, 8: 0.95, 9: 1.06, 10: 1.08, 11: 1.10, 12: 1.07}[month.month]
            channel_scale = 1.35 if account.account_type != "의원" else 1.0
            for product in products:
                target_amount = int(random.randint(700000, 1900000) * float(product["strategic_weight"]) * seasonality * channel_scale)
                attainment = np.clip(np.random.normal(loc=0.99 if account.account_type == "의원" else 0.96, scale=0.18), 0.55, 1.45)
                sales_amount = int(target_amount * attainment)
                product_name = product_name_variant(str(product["canonical_brand"]), idx)
                target_rows.append(
                    {
                        "기준년월": month.strftime("%Y%m"),
                        "본부코드": account.branch_id,
                        "본부명": account.branch_name,
                        "영업사원코드": account.rep_id,
                        "영업사원명": account.rep_name,
                        "거래처코드": account.account_id,
                        "거래처명": messy_account_name(account.account_name, idx),
                        "브랜드코드": product["canonical_product_id"],
                        "브랜드명": product_name,
                        "계획금액": target_amount,
                    }
                )
                sales_rows.append(
                    {
                        "기준년월": month.strftime("%Y%m"),
                        "본부코드": account.branch_id,
                        "본부명": account.branch_name,
                        "영업사원코드": account.rep_id,
                        "영업사원명": account.rep_name,
                        "거래처코드": account.account_id,
                        "거래처명": messy_account_name(account.account_name, idx),
                        "브랜드코드": product["canonical_product_id"],
                        "브랜드명": product_name,
                        "매출금액": sales_amount,
                        "매출수량": max(1, int(sales_amount / random.randint(20000, 90000))),
                        "달성률": round((sales_amount / target_amount) * 100, 1),
                    }
                )
    return pd.DataFrame(target_rows), pd.DataFrame(sales_rows)


def generate_fact_ship(account_master: pd.DataFrame, sales_raw: pd.DataFrame, portfolio: pd.DataFrame) -> pd.DataFrame:
    pharmacy_pool = load_pharmacy_pool()
    wholesaler_pool = load_wholesaler_pool()
    account_region_map = account_master.groupby("region_key")["account_id"].apply(list).to_dict()
    product_sku_map = portfolio.set_index("canonical_brand")["canonical_sku"].to_dict()
    product_form_map = portfolio.set_index("canonical_brand")["formulation"].to_dict()
    product_pack_map = portfolio.set_index("canonical_brand")["pack_size"].to_dict()
    rows: list[dict] = []
    sales_sample = sales_raw.sample(n=min(42000, len(sales_raw)), random_state=SEED).reset_index(drop=True)

    for idx, row in sales_sample.iterrows():
        region_key = None
        account_id = str(row["거래처코드"])
        matched = account_master[account_master["account_id"].astype(str) == account_id]
        if not matched.empty:
            region_key = str(matched.iloc[0]["region_key"])
        region_key = region_key or random.choice(list(account_region_map.keys()))
        pharmacy_candidates = pharmacy_pool[pharmacy_pool["pharmacy_region_key"] == region_key]
        wholesaler_candidates = wholesaler_pool[wholesaler_pool["region_key"] == region_key]
        if pharmacy_candidates.empty:
            pharmacy_candidates = pharmacy_pool
        if wholesaler_candidates.empty:
            wholesaler_candidates = wholesaler_pool
        pharmacy = pharmacy_candidates.sample(n=1, random_state=SEED + idx).iloc[0]
        wholesaler = wholesaler_candidates.sample(n=1, random_state=SEED + 1000 + idx).iloc[0]
        ship_date = pd.Timestamp(str(row["기준년월"]) + "01") + pd.Timedelta(days=random.randint(0, 26))
        qty = max(1, int(row["매출수량"] * random.uniform(0.8, 1.6)))
        amount_ship = int(row["매출금액"] * random.uniform(0.85, 1.25))
        brand = str(row["브랜드명"]).strip()
        rows.append(
            {
                "ship_date (출고일)": ship_date.strftime("%Y-%m-%d") if idx % 2 == 0 else ship_date.strftime("%Y/%m/%d"),
                "manufacturer_name (제약사)": COMPANY_NAME,
                "mfg_to_wholesaler_path (제약사-도매상경로)": f"{COMPANY_NAME}->{wholesaler['wholesaler_name']}",
                "wholesaler_name (도매상명)": wholesaler["wholesaler_name"],
                "wholesaler_raw_name (도매원본명)": wholesaler["wholesaler_name"].replace("주식회사 ", "") if idx % 19 == 0 else wholesaler["wholesaler_name"],
                "wholesaler_region_key (도매시도)": region_key,
                "wholesaler_latitude (도매위도)": wholesaler["wholesaler_latitude"],
                "wholesaler_longitude (도매경도)": wholesaler["wholesaler_longitude"],
                "pharmacy_name (약국명)": pharmacy["pharmacy_name"] if idx % 17 else f" {pharmacy['pharmacy_name']}",
                "pharmacy_account_id (약국거래처ID)": pharmacy["pharmacy_account_id"],
                "pharmacy_region_key (약국시도)": pharmacy["pharmacy_region_key"],
                "pharmacy_sub_region_key (약국시군구)": pharmacy["pharmacy_sub_region_key"],
                "pharmacy_addr (약국주소)": pharmacy["pharmacy_addr"],
                "pharmacy_latitude (약국위도)": pharmacy["pharmacy_latitude"],
                "pharmacy_longitude (약국경도)": pharmacy["pharmacy_longitude"],
                "brand (브랜드)": brand,
                "sku (SKU)": product_sku_map.get(brand.replace(" ", ""), product_sku_map.get(brand, brand)),
                "formulation (제형)": product_form_map.get(brand.replace(" ", ""), product_form_map.get(brand, "정")),
                "pack_size (포장단위)": product_pack_map.get(brand.replace(" ", ""), product_pack_map.get(brand, "300정")),
                "qty (수량)": qty,
                "amount_ship (출고금액)": amount_ship,
                "data_source (데이터소스)": "daon_source_simulated",
            }
        )
    return pd.DataFrame(rows)


def write_outputs(rep_df: pd.DataFrame, account_master: pd.DataFrame, assignment_raw: pd.DataFrame, crm_raw: pd.DataFrame, target_raw: pd.DataFrame, sales_raw: pd.DataFrame, ship_raw: pd.DataFrame) -> None:
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
    portfolio = load_portfolio()
    hospital_pool = load_hospital_pool()
    clinic_df, hospital_df = select_accounts(hospital_pool)
    rep_df = build_rep_master(clinic_df, hospital_df)
    account_master = build_account_master(rep_df, clinic_df, hospital_df)
    assignment_raw = build_company_assignment(account_master, rep_df)
    crm_raw = generate_crm_raw(account_master, portfolio)
    target_raw, sales_raw = generate_target_and_sales(account_master, portfolio)
    ship_raw = generate_fact_ship(account_master, sales_raw, portfolio)
    write_outputs(rep_df, account_master, assignment_raw, crm_raw, target_raw, sales_raw, ship_raw)

    summary = {
        "company_key": COMPANY_KEY,
        "company_name": COMPANY_NAME,
        "rep_count": int(len(rep_df)),
        "clinic_rep_count": int((rep_df["rep_role"] == "의원").sum()),
        "hospital_rep_count": int((rep_df["rep_role"] == "종합병원").sum()),
        "account_count": int(len(account_master)),
        "clinic_account_count": int((account_master["account_type"] == "의원").sum()),
        "hospital_account_count": int((account_master["account_type"] != "의원").sum()),
        "crm_rows": int(len(crm_raw)),
        "target_rows": int(len(target_raw)),
        "sales_rows": int(len(sales_raw)),
        "fact_ship_rows": int(len(ship_raw)),
        "date_range": [START_DATE, END_DATE],
        "output_root": str(OUTPUT_ROOT),
    }
    (OUTPUT_ROOT / "generation_summary.json").write_text(pd.Series(summary).to_json(force_ascii=False, indent=2), encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
