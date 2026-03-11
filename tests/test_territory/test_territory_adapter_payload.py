from __future__ import annotations

import json
import pandas as pd

from adapters.territory import TerritoryActivityAdapterConfig, load_territory_activity_from_frames
from modules.builder.service import (
    build_template_payload,
    build_territory_template_input,
    prepare_territory_chunk_assets,
)
from modules.sandbox.schemas import HospitalAnalysisRecord
from modules.territory import builder_payload as territory_builder_payload
from modules.territory.schemas import GeoCoord
from modules.territory.service import build_territory_result_asset
from tests.fixtures.territory_fixtures import HOSPITAL_ANALYSIS_RECORDS, HOSPITAL_REGION_MAP


def _build_coord_map() -> dict[str, GeoCoord]:
    return {
        "H001": GeoCoord(lat=37.501, lng=127.021, source="exact"),
        "H002": GeoCoord(lat=37.524, lng=127.035, source="exact"),
        "H003": GeoCoord(lat=35.145, lng=129.059, source="exact"),
        "H004": GeoCoord(lat=35.168, lng=129.072, source="exact"),
        "H005": GeoCoord(lat=37.482, lng=126.642, source="exact"),
        "H006": GeoCoord(lat=37.463, lng=126.651, source="exact"),
    }


def _build_name_map() -> dict[str, str]:
    return {
        "H001": "서울A병원",
        "H002": "서울B병원",
        "H003": "부산A병원",
        "H004": "부산B병원",
        "H005": "인천A병원",
        "H006": "인천B병원",
    }


def _build_rep_map() -> dict[str, str]:
    return {
        "H001": "REP001",
        "H002": "REP001",
        "H003": "REP002",
        "H004": "REP002",
        "H005": "REP003",
        "H006": "",
    }


def _build_territory_asset():
    hospital_records = [HospitalAnalysisRecord(**row) for row in HOSPITAL_ANALYSIS_RECORDS]
    return build_territory_result_asset(
        hospital_records=hospital_records,
        hospital_region_map=HOSPITAL_REGION_MAP,
        hospital_coord_map=_build_coord_map(),
        hospital_name_map=_build_name_map(),
        hospital_rep_map=_build_rep_map(),
    )


def test_territory_activity_adapter_builds_standard_rows():
    crm_df = pd.DataFrame(
        [
            {
                "hospital_id": "H001",
                "rep_id": "REP001",
                "rep_name": "강민준",
                "branch_id": "B001",
                "branch_name": "서울본부",
                "activity_date": "2026-01-03",
                "metric_month": "202601",
                "activity_type": "방문",
                "visit_count": 1,
                "raw_row_index": 10,
            },
            {
                "hospital_id": "H002",
                "rep_id": "REP001",
                "rep_name": "강민준",
                "branch_id": "B001",
                "branch_name": "서울본부",
                "activity_date": "2026-01-03",
                "metric_month": "202601",
                "activity_type": "방문",
                "visit_count": 2,
                "raw_row_index": 11,
            },
        ]
    )
    account_df = pd.DataFrame(
        [
            {
                "account_id": "H001",
                "account_name": "서울A병원",
                "rep_id": "REP001",
                "rep_name": "강민준",
                "branch_id": "B001",
                "branch_name": "서울본부",
                "region_key": "서울",
                "sub_region_key": "강남",
                "latitude": 37.501,
                "longitude": 127.021,
            },
            {
                "account_id": "H002",
                "account_name": "서울B병원",
                "rep_id": "REP001",
                "rep_name": "강민준",
                "branch_id": "B001",
                "branch_name": "서울본부",
                "region_key": "서울",
                "sub_region_key": "송파",
                "latitude": 37.524,
                "longitude": 127.035,
            },
        ]
    )

    rows, unmapped = load_territory_activity_from_frames(
        crm_df,
        account_df,
        TerritoryActivityAdapterConfig.hangyeol_account_example(),
    )

    assert not unmapped
    assert len(rows) == 2
    assert rows[0].month_key == "2026-01"
    assert rows[0].date_key == "2026-01-03"
    assert rows[1].route_order == 11


def test_territory_builder_payload_groups_by_rep_month_date(monkeypatch):
    territory_asset = _build_territory_asset()
    activity_df = pd.DataFrame(
        [
            {
                "hospital_id": "H001",
                "hospital_name": "서울A병원",
                "rep_id": "REP001",
                "rep_name": "강민준",
                "branch_id": "B001",
                "branch_name": "서울본부",
                "activity_date": "2026-01-03",
                "month_key": "2026-01",
                "date_key": "2026-01-03",
                "latitude": 37.501,
                "longitude": 127.021,
                "region_key": "서울",
                "sub_region_key": "강남",
                "activity_type": "방문",
                "visit_count": 1,
                "route_order": 10,
            },
            {
                "hospital_id": "H002",
                "hospital_name": "서울B병원",
                "rep_id": "REP001",
                "rep_name": "강민준",
                "branch_id": "B001",
                "branch_name": "서울본부",
                "activity_date": "2026-01-03",
                "month_key": "2026-01",
                "date_key": "2026-01-03",
                "latitude": 37.524,
                "longitude": 127.035,
                "region_key": "서울",
                "sub_region_key": "송파",
                "activity_type": "방문",
                "visit_count": 1,
                "route_order": 11,
            },
            {
                "hospital_id": "H001",
                "hospital_name": "서울A병원",
                "rep_id": "REP001",
                "rep_name": "강민준",
                "branch_id": "B001",
                "branch_name": "서울본부",
                "activity_date": "2026-01-04",
                "month_key": "2026-01",
                "date_key": "2026-01-04",
                "latitude": 37.501,
                "longitude": 127.021,
                "region_key": "서울",
                "sub_region_key": "강남",
                "activity_type": "방문",
                "visit_count": 1,
                "route_order": 12,
            },
            {
                "hospital_id": "H003",
                "hospital_name": "부산A병원",
                "rep_id": "REP002",
                "rep_name": "강서연",
                "branch_id": "B002",
                "branch_name": "영남본부",
                "activity_date": "2026-01-04",
                "month_key": "2026-01",
                "date_key": "2026-01-04",
                "latitude": 35.145,
                "longitude": 129.059,
                "region_key": "부산",
                "sub_region_key": "부산진구",
                "activity_type": "방문",
                "visit_count": 1,
                "route_order": 20,
            },
        ]
    )
    monkeypatch.setattr(territory_builder_payload.pd, "read_excel", lambda *_args, **_kwargs: activity_df.copy())

    payload = territory_builder_payload.build_territory_builder_payload(
        territory_asset,
        territory_activity_path=__file__,
    )

    assert "markers" not in payload
    assert "hospital_catalog" in payload
    assert payload["default_selection"] == {}
    assert payload["filters"]["rep_options"][0]["label"] == "강민준"

    rep_payload = payload["rep_payloads"]["REP001"]
    assert rep_payload["months"][0]["value"] == "2026-01"
    assert rep_payload["dates_by_month"]["2026-01"][0]["value"] == "__ALL__"
    selection = rep_payload["views"]["2026-01|2026-01-03"]
    assert len(selection["points"]) == 2
    assert "route_groups" not in selection
    assert selection["summary"]["stop_count"] == 2
    assert selection["summary"]["distance_km"] > 0
    assert "강민준" in selection["insight_text"]

    month_selection = rep_payload["views"]["2026-01|__ALL__"]
    assert len(month_selection["route_groups"]) == 2
    assert "points" not in month_selection
    assert month_selection["summary"]["visit_count"] == 3
    assert month_selection["summary"]["selected_hospital_count"] == 2
    assert month_selection["scope"]["is_month_aggregate"] is True

    manifest, month_chunks = territory_builder_payload.build_chunked_territory_payload(payload)
    assert manifest["data_mode"] == territory_builder_payload.CHUNKED_TERRITORY_DATA_MODE
    assert manifest["hospital_catalog"] == {}
    assert manifest["rep_payloads"] == {}
    assert "REP001" in manifest["rep_index"]
    assert manifest["rep_index"]["REP001"]["rep_asset"] in month_chunks
    assert manifest["rep_index"]["REP001"]["month_assets"]["2026-01"] in month_chunks
    assert "hospital_catalog" in month_chunks[manifest["rep_index"]["REP001"]["rep_asset"]]
    assert month_chunks[manifest["rep_index"]["REP001"]["month_assets"]["2026-01"]]["views"]["2026-01|__ALL__"]["scope"]["is_month_aggregate"] is True


def test_builder_service_chunks_full_territory_payload_before_render(monkeypatch, tmp_path):
    territory_asset = _build_territory_asset()
    activity_df = pd.DataFrame(
        [
            {
                "hospital_id": "H001",
                "hospital_name": "서울A병원",
                "rep_id": "REP001",
                "rep_name": "강민준",
                "branch_id": "B001",
                "branch_name": "서울본부",
                "activity_date": "2026-01-03",
                "month_key": "2026-01",
                "date_key": "2026-01-03",
                "latitude": 37.501,
                "longitude": 127.021,
                "region_key": "서울",
                "sub_region_key": "강남",
                "activity_type": "방문",
                "visit_count": 1,
                "route_order": 10,
            },
            {
                "hospital_id": "H002",
                "hospital_name": "서울B병원",
                "rep_id": "REP001",
                "rep_name": "강민준",
                "branch_id": "B001",
                "branch_name": "서울본부",
                "activity_date": "2026-01-04",
                "month_key": "2026-01",
                "date_key": "2026-01-04",
                "latitude": 37.524,
                "longitude": 127.035,
                "region_key": "서울",
                "sub_region_key": "송파",
                "activity_type": "방문",
                "visit_count": 1,
                "route_order": 11,
            },
        ]
    )
    monkeypatch.setattr(territory_builder_payload.pd, "read_excel", lambda *_args, **_kwargs: activity_df.copy())

    full_payload = territory_builder_payload.build_territory_builder_payload(
        territory_asset,
        territory_activity_path=__file__,
    )
    payload_path = tmp_path / "territory_builder_payload.json"
    payload_path.write_text(json.dumps(full_payload, ensure_ascii=False), encoding="utf-8")
    template_path = tmp_path / "territory_optimizer_template.html"
    template_path.write_text("<script>window.__TERRITORY_DATA__ = {};</script>", encoding="utf-8")

    builder_input = build_territory_template_input(
        str(template_path),
        builder_payload_path=str(payload_path),
    )
    builder_payload = build_template_payload(builder_input)
    prepare_territory_chunk_assets(
        builder_payload,
        payload_source_path=str(payload_path),
        output_root=str(tmp_path),
    )

    assert builder_payload.payload["data_mode"] == territory_builder_payload.CHUNKED_TERRITORY_DATA_MODE
    assert builder_payload.payload["hospital_catalog"] == {}
    assert builder_payload.payload["rep_payloads"] == {}
    assert builder_payload.payload["asset_base"] == "territory_map_preview_assets"
    assert (tmp_path / "territory_map_preview_assets").exists()
    assert any((tmp_path / "territory_map_preview_assets").glob("*.js"))
