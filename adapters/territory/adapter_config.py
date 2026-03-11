from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class TerritoryActivityAdapterConfig(BaseModel):
    """
    회사 거래처 마스터를 Territory 활동 표준 행으로 붙일 때 쓰는 컬럼 설정.

    CRM 표준 파일은 컬럼이 이미 고정되어 있으므로,
    여기서는 주로 회사 거래처 파일의 컬럼 차이만 흡수한다.
    """
    hospital_id_col: str
    hospital_name_col: str
    rep_id_col: str
    rep_name_col: str
    branch_id_col: Optional[str] = None
    branch_name_col: Optional[str] = None
    region_key_col: Optional[str] = None
    sub_region_key_col: Optional[str] = None
    latitude_col: str = "latitude"
    longitude_col: str = "longitude"

    @classmethod
    def hangyeol_account_example(cls) -> "TerritoryActivityAdapterConfig":
        return cls(
            hospital_id_col="account_id",
            hospital_name_col="account_name",
            rep_id_col="rep_id",
            rep_name_col="rep_name",
            branch_id_col="branch_id",
            branch_name_col="branch_name",
            region_key_col="region_key",
            sub_region_key_col="sub_region_key",
            latitude_col="latitude",
            longitude_col="longitude",
        )
