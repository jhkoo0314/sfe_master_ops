"""
CRM Activity Adapter - CRM 활동 파일 → CrmStandardActivity 변환

핵심 원칙:
  - 컬럼 매핑은 CrmActivityAdapterConfig로 외부에서 주입한다.
  - Salesforce, Veeva CRM, 자체 CRM 등 어떤 시스템 데이터도 처리한다.
  - 활동 유형 표준화 규칙도 Config에서 주입 (회사별 용어 차이 흡수).
  - 출력(CrmStandardActivity)이 계약(Contract)이며, 이 구조는 변하지 않는다.

흐름:
  어떤 CRM 파일 + CrmActivityAdapterConfig → CrmStandardActivity (공통 계약)
"""

from datetime import date
from pathlib import Path
import re
from typing import Any
try:
    import polars as pl
except ModuleNotFoundError:  # pragma: no cover - 환경 의존 fallback
    pl = None
import pandas as pd

from modules.crm.schemas import CompanyMasterStandard, CrmStandardActivity
from adapters.crm.adapter_config import CrmActivityAdapterConfig
from common.exceptions import AdapterInputError, AdapterMappingError


# 기본 활동 유형 표준화 매핑 (Config에서 오버라이드 가능)
_DEFAULT_ACTIVITY_TYPE_MAP: dict[str, str] = {
    "pt": "PT",
    "제품설명": "PT",
    "detailing": "PT",
    "detail": "PT",
    "시연": "Demo",
    "demo": "Demo",
    "행사": "Demo",
    "event": "Demo",
    "group": "Demo",
    "디지털": "Demo",
    "edetail": "Demo",
    "closing": "Closing",
    "close": "Closing",
    "클로징": "Closing",
    "니즈환기": "Needs",
    "needs": "Needs",
    "needcreation": "Needs",
    "need": "Needs",
    "대면": "FaceToFace",
    "방문": "FaceToFace",
    "visit": "FaceToFace",
    "f2f": "FaceToFace",
    "facetoface": "FaceToFace",
    "컨택": "Contact",
    "전화": "Contact",
    "call": "Contact",
    "phone": "Contact",
    "email": "Contact",
    "이메일": "Contact",
    "video": "Contact",
    "remote": "Contact",
    "접근": "Access",
    "access": "Access",
    "피드백": "Feedback",
    "feedback": "Feedback",
}

_BEHAVIOR8_CANONICAL = ("PT", "Demo", "Closing", "Needs", "FaceToFace", "Contact", "Access", "Feedback")


def load_crm_activity_from_file(
    file_path: str | Path,
    config: CrmActivityAdapterConfig,
    company_master: list[CompanyMasterStandard],
) -> tuple[list[CrmStandardActivity], list[dict]]:
    """
    CRM 활동 파일(Excel/CSV)을 읽어 CrmStandardActivity 목록을 반환합니다.

    Args:
        file_path: CRM 활동 파일 경로
        config: 이 파일의 컬럼 매핑 설정 (CrmActivityAdapterConfig)
        company_master: 담당자-병원 연결 정보 (rep_id + 병원명 → hospital_id, branch_id)

    Returns:
        (표준화 성공 목록, 매핑 실패 목록)
    """
    path = Path(file_path)
    if not path.exists():
        raise AdapterInputError(f"CRM 활동 파일을 찾을 수 없습니다: {path}")

    try:
        if path.suffix.lower() in (".xlsx", ".xls"):
            if pl is not None:
                df = pl.read_excel(str(path))
            else:
                df = pd.read_excel(str(path))
        else:
            if pl is not None:
                df = pl.read_csv(str(path), encoding="utf-8-sig")
            else:
                df = pd.read_csv(str(path), encoding="utf-8-sig")
    except Exception as e:
        raise AdapterInputError(f"파일 읽기 실패: {path}", detail=str(e))

    return _convert_dataframe_to_standard_activity(df, config, company_master)


def load_crm_activity_from_records(
    records: list[dict],
    config: CrmActivityAdapterConfig,
    company_master: list[CompanyMasterStandard],
) -> tuple[list[CrmStandardActivity], list[dict]]:
    """
    딕셔너리 목록을 CrmStandardActivity 목록으로 변환합니다.
    fixture 데이터, API 응답, DB 쿼리 결과 등에 사용합니다.

    Args:
        records: 딕셔너리 목록
        config: 이 데이터의 키 매핑 설정
        company_master: 담당자-병원 연결 정보

    Returns:
        (표준화 성공 목록, 매핑 실패 목록)
    """
    if not records:
        return [], []

    # 날짜 객체가 포함된 경우 polars 호환 처리
    str_records = []
    for r in records:
        row = dict(r)
        for k, v in row.items():
            if isinstance(v, date):
                row[k] = str(v)
            elif isinstance(v, list):
                row[k] = ",".join(str(x) for x in v)
        str_records.append(row)

    df = pl.DataFrame(str_records) if pl is not None else pd.DataFrame(str_records)
    return _convert_dataframe_to_standard_activity(df, config, company_master)


def _convert_dataframe_to_standard_activity(
    df: Any,
    config: CrmActivityAdapterConfig,
    company_master: list[CompanyMasterStandard],
) -> tuple[list[CrmStandardActivity], list[dict]]:
    """내부 공통 변환 로직."""
    # 필수 컬럼 확인
    required_cols = {
        "rep_id": config.rep_id_col,
        "activity_date": config.activity_date_col,
        "activity_type": config.activity_type_col,
    }
    columns = list(df.columns)
    missing = [f"{field}({col})" for field, col in required_cols.items() if col not in columns]
    resolved_hospital_id_col = config.hospital_id_col
    if not resolved_hospital_id_col and "hospital_id" in columns:
        resolved_hospital_id_col = "hospital_id"

    has_hospital_name = config.hospital_name_col in columns
    has_hospital_id = bool(resolved_hospital_id_col and resolved_hospital_id_col in columns)
    if not has_hospital_name and not has_hospital_id:
        missing.append(
            f"hospital_name_or_id({config.hospital_name_col}"
                + (f" | {resolved_hospital_id_col}" if resolved_hospital_id_col else "")
                + ")"
            )
    if missing:
        raise AdapterInputError(
            "필수 컬럼이 파일에 없습니다.",
            detail=f"누락 항목: {missing} | 파일 컬럼: {columns}"
        )

    # 활동 유형 표준화 맵 (Config 우선, 없으면 기본 맵)
    source_map = config.activity_type_map or _DEFAULT_ACTIVITY_TYPE_MAP
    act_type_map = {str(k).strip().lower(): str(v).strip() for k, v in source_map.items()}

    # 회사 마스터 인덱스: (rep_id, normalized_hospital_name) → (hospital_id, branch_id, rep_name, branch_name)
    master_name_index: dict[tuple[str, str], tuple[str, str, str, str]] = {}
    master_id_index: dict[tuple[str, str], tuple[str, str, str, str]] = {}
    for m in company_master:
        name_key = (m.rep_id, m.hospital_name.replace(" ", "").lower())
        id_key = (m.rep_id, m.hospital_id)
        mapped = (m.hospital_id, m.branch_id, m.rep_name, m.branch_name)
        master_name_index[name_key] = mapped
        master_id_index[id_key] = mapped

    result: list[CrmStandardActivity] = []
    unmapped: list[dict] = []
    row_index = 0

    rows = df.iter_rows(named=True) if pl is not None and isinstance(df, pl.DataFrame) else df.to_dict(orient="records")
    for row in rows:
        row_index += 1
        rep_id = str(row.get(config.rep_id_col, "")).strip()
        raw_hospital_name = str(row.get(config.hospital_name_col, "")).strip() if has_hospital_name else ""
        raw_hospital_id = str(row.get(resolved_hospital_id_col, "")).strip() if has_hospital_id and resolved_hospital_id_col else ""
        normalized_hospital = raw_hospital_name.replace(" ", "").lower()

        # 담당자-병원 매핑: hospital_id가 있으면 직접 연결을 우선, 없으면 병원명으로 역매핑
        mapping = None
        if raw_hospital_id:
            mapping = master_id_index.get((rep_id, raw_hospital_id))
        if mapping is None and normalized_hospital:
            mapping = master_name_index.get((rep_id, normalized_hospital))
        if not mapping:
            unmapped.append({
                "row_index": row_index,
                "rep_id": rep_id,
                "hospital_name": raw_hospital_name,
                "hospital_id": raw_hospital_id,
                "reason": "company_master에 (rep_id, 병원명/병원ID) 조합 없음",
            })
            continue

        hospital_id, branch_id, rep_name, branch_name = mapping

        # 날짜 파싱 (다양한 포맷 지원)
        try:
            raw_date = str(row.get(config.activity_date_col, "")).strip()
            act_date = _parse_date_flexible(raw_date)
            metric_month = act_date.strftime("%Y%m")
        except Exception:
            unmapped.append({
                "row_index": row_index,
                "rep_id": rep_id,
                "hospital_name": raw_hospital_name,
                "reason": f"날짜 파싱 실패: '{row.get(config.activity_date_col)}'",
            })
            continue

        # 활동 유형 표준화 (Config 맵 사용)
        raw_type_value = str(row.get(config.activity_type_col, "방문")).strip()
        raw_type = raw_type_value.lower()
        mapped_type = act_type_map.get(raw_type, raw_type_value)
        activity_type = _normalize_to_behavior8(mapped_type, raw_type_value)

        # 방문 건수
        visit_count = 1
        if config.visit_count_col and config.visit_count_col in columns:
            try:
                visit_count = int(row.get(config.visit_count_col) or 1)
            except (ValueError, TypeError):
                visit_count = 1

        # 디테일 여부
        has_detail = False
        if config.has_detail_call_col and config.has_detail_call_col in columns:
            detail_raw = str(row.get(config.has_detail_call_col, "N")).strip().upper()
            has_detail = detail_raw in ("Y", "TRUE", "1", "예", "YES")

        # 제품 목록 파싱 (쉼표 구분 문자열 또는 이미 파싱된 형태)
        products: list[str] = []
        if config.products_mentioned_col and config.products_mentioned_col in columns:
            products_raw = row.get(config.products_mentioned_col, "")
            if isinstance(products_raw, str) and products_raw.strip():
                products = [p.strip() for p in products_raw.split(",") if p.strip()]

        # 비고
        notes = None
        if config.notes_col and config.notes_col in columns:
            notes_raw = str(row.get(config.notes_col, "") or "").strip()
            notes = notes_raw if notes_raw else None

        trust_level = None
        if config.trust_level_col and config.trust_level_col in columns:
            trust_raw = str(row.get(config.trust_level_col, "") or "").strip()
            trust_level = trust_raw or None

        def _to_float(col_name: str | None) -> float | None:
            if not col_name or col_name not in columns:
                return None
            raw = row.get(col_name)
            if raw is None or raw == "":
                return None
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None

        sentiment_score = _to_float(config.sentiment_score_col)
        quality_factor = _to_float(config.quality_factor_col)
        impact_factor = _to_float(config.impact_factor_col)
        activity_weight = _to_float(config.activity_weight_col)
        weighted_activity_score = _to_float(config.weighted_activity_score_col)

        next_action_text = None
        if config.next_action_text_col and config.next_action_text_col in columns:
            next_action_raw = str(row.get(config.next_action_text_col, "") or "").strip()
            next_action_text = next_action_raw or None

        try:
            activity = CrmStandardActivity(
                hospital_id=hospital_id,
                rep_id=rep_id,
                branch_id=branch_id,
                rep_name=rep_name,
                branch_name=branch_name,
                activity_date=act_date,
                metric_month=metric_month,
                activity_type=activity_type,
                activity_type_raw=raw_type_value or None,
                activity_type_standard=activity_type,
                visit_count=visit_count,
                products_mentioned=products,
                has_detail_call=has_detail,
                notes=notes,
                trust_level=trust_level,
                sentiment_score=sentiment_score,
                quality_factor=quality_factor,
                impact_factor=impact_factor,
                activity_weight=activity_weight,
                weighted_activity_score=weighted_activity_score,
                next_action_text=next_action_text,
                raw_row_index=row_index,
            )
            result.append(activity)
        except Exception as e:
            raise AdapterMappingError(
                f"CrmStandardActivity 변환 실패: row={row_index}",
                detail=str(e)
            )

    return result, unmapped


def _parse_date_flexible(raw: str) -> date:
    """
    다양한 날짜 포맷을 파싱합니다.
    - YYYY-MM-DD
    - YYYYMMDD
    - YYYY/MM/DD
    - DD/MM/YYYY (MM/DD/YYYY는 구분 불가하므로 주의)
    """
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            continue
    raise ValueError(f"날짜 파싱 실패: '{raw}'")


def _normalize_to_behavior8(mapped: str | None, raw: str | None) -> str:
    """
    어떤 입력이 와도 표준 활동유형을 8대 행동값으로 고정한다.
    """
    candidates = [mapped, raw]
    direct = {
        "pt": "PT",
        "demo": "Demo",
        "closing": "Closing",
        "needs": "Needs",
        "facetoface": "FaceToFace",
        "contact": "Contact",
        "access": "Access",
        "feedback": "Feedback",
    }
    aliases = {
        "제품설명": "PT",
        "detail": "PT",
        "detailing": "PT",
        "시연": "Demo",
        "행사": "Demo",
        "event": "Demo",
        "group": "Demo",
        "디지털": "Demo",
        "edetail": "Demo",
        "close": "Closing",
        "클로징": "Closing",
        "니즈환기": "Needs",
        "need": "Needs",
        "needcreation": "Needs",
        "대면": "FaceToFace",
        "방문": "FaceToFace",
        "visit": "FaceToFace",
        "f2f": "FaceToFace",
        "컨택": "Contact",
        "전화": "Contact",
        "call": "Contact",
        "phone": "Contact",
        "email": "Contact",
        "이메일": "Contact",
        "video": "Contact",
        "remote": "Contact",
        "접근": "Access",
        "피드백": "Feedback",
    }
    for value in candidates:
        token = _normalize_type_token(value)
        if not token:
            continue
        if token in direct:
            return direct[token]
        if token in aliases:
            return aliases[token]
    return "FaceToFace"


def _normalize_type_token(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    for canonical in _BEHAVIOR8_CANONICAL:
        if text == canonical:
            return canonical.lower()
    text = text.lower()
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"[\s\-_\/]+", "", text)
    return text
