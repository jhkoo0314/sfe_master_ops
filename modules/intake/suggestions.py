from __future__ import annotations

import re
from difflib import SequenceMatcher

from .models import IntakeSuggestion
from .rules import IntakeRule


_SEMANTIC_LABELS = {
    "activity_date": "활동일",
    "rep": "담당자",
    "account": "거래처/병원",
    "activity_type": "활동유형",
    "organization": "조직",
    "product": "제품/품목",
    "amount": "금액",
    "period": "기준월",
    "target_value": "목표값",
    "ship_date": "출고일",
    "pharmacy": "약국",
    "quantity": "수량",
    "hospital": "병원",
}

_NEGATIVE_TOKENS = {
    "activity_date": {"기관", "병원", "거래처", "횟수", "메모", "내용", "주소", "위도", "경도", "코드"},
    "rep": {"본부", "지점", "팀", "조직", "채널", "지역", "거래처", "병원", "제품", "브랜드"},
    "account": {"금액", "수량", "본부", "지점", "팀", "조직", "채널", "브랜드", "제품", "매출"},
    "activity_type": {"일자", "날짜", "금액", "수량", "코드", "병원", "거래처"},
    "organization": {"금액", "수량", "제품", "브랜드", "거래처", "병원", "위도", "경도"},
    "product": {
        "본부",
        "지점",
        "팀",
        "조직",
        "거래처",
        "병원",
        "주소",
        "위도",
        "경도",
        "사원",
        "담당",
        "manufacturer",
        "pharmacy",
        "wholesaler",
        "제약사",
        "약국",
        "도매",
    },
    "amount": {"코드", "본부", "지점", "팀", "거래처", "병원", "브랜드", "제품명"},
    "period": {"금액", "수량", "코드", "본부", "지점", "팀", "브랜드"},
    "ship_date": {"데이터", "소스", "금액", "수량", "위도", "경도", "주소"},
    "pharmacy": {"위도", "경도"},
    "quantity": {"금액", "주소", "위도", "경도", "코드"},
    "hospital": {"금액", "수량", "위도", "경도"},
}

_POSITIVE_TOKENS = {
    "activity_date": {"일", "일자", "date"},
    "rep": {"담당", "사원", "영업"},
    "account": {"병원", "거래처", "기관", "account"},
    "activity_type": {"활동", "유형", "액션", "채널", "방문", "call"},
    "organization": {"본부", "지점", "팀", "조직", "부서"},
    "product": {"제품", "품목", "브랜드", "brand", "sku"},
    "amount": {"금액", "매출", "amount"},
    "period": {"월", "년월", "yyyymm", "month"},
    "target_value": {"목표", "계획", "금액", "수량"},
    "ship_date": {"출고", "납품", "date"},
    "pharmacy": {"약국", "pharmacy"},
    "quantity": {"수량", "qty", "quantity"},
    "hospital": {"병원", "hospital"},
}


def _normalize_text(value: str) -> str:
    return "".join(ch for ch in str(value).strip().lower() if ch.isalnum())


def _tokenize_text(value: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z]+|\d+|[가-힣]+", str(value))]


def _score_candidate_columns(
    columns: list[str],
    aliases: tuple[str, ...],
    *,
    semantic_field: str,
) -> list[tuple[float, str]]:
    normalized_aliases = [_normalize_text(alias) for alias in aliases]
    alias_tokens = {token for alias in aliases for token in _tokenize_text(alias)}
    negative_tokens = _NEGATIVE_TOKENS.get(semantic_field, set())
    positive_tokens = _POSITIVE_TOKENS.get(semantic_field, set())
    scored: list[tuple[float, str]] = []
    for column in columns:
        normalized_column = _normalize_text(column)
        column_tokens = set(_tokenize_text(column))
        has_positive_hint = any(token in normalized_column for token in positive_tokens) or any(
            token in column_tokens for token in positive_tokens
        )
        if (column_tokens & negative_tokens) and not has_positive_hint:
            continue
        best_score = 0.0
        for alias in normalized_aliases:
            if not alias:
                continue
            score = SequenceMatcher(None, normalized_column, alias).ratio()
            if alias in normalized_column or normalized_column in alias:
                score = max(score, 0.92)
            if column_tokens & alias_tokens:
                score = max(score, 0.88)
            if any(token in normalized_column for token in positive_tokens):
                score = max(score, 0.72)
            best_score = max(best_score, score)
        if best_score >= 0.6:
            scored.append((best_score, column))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored


def rank_candidate_columns(
    columns: list[str],
    aliases: tuple[str, ...],
    *,
    semantic_field: str,
    limit: int = 3,
) -> list[str]:
    scored = _score_candidate_columns(columns, aliases, semantic_field=semantic_field)
    result: list[str] = []
    for _score, column in scored:
        if column not in result:
            result.append(column)
        if len(result) >= limit:
            break
    return result


def infer_best_candidate_column(
    columns: list[str],
    aliases: tuple[str, ...],
    *,
    semantic_field: str,
    min_score: float = 0.86,
    min_gap: float = 0.08,
) -> str | None:
    scored = _score_candidate_columns(columns, aliases, semantic_field=semantic_field)
    if not scored:
        return None

    best_score, best_column = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0
    if best_score >= 0.92:
        return best_column
    if best_score >= min_score and (best_score - second_score) >= min_gap:
        return best_column
    return None


def build_missing_required_field_suggestion(
    *,
    source_key: str,
    semantic_field: str,
    columns: list[str],
    rule: IntakeRule,
) -> IntakeSuggestion:
    aliases = rule.field_aliases.get(semantic_field, ())
    candidates = rank_candidate_columns(columns, aliases, semantic_field=semantic_field)
    semantic_label = _SEMANTIC_LABELS.get(semantic_field, semantic_field)
    candidate_text = ", ".join(candidates) if candidates else "뚜렷한 후보 없음"
    return IntakeSuggestion(
        source_key=source_key,
        suggestion_type="required_mapping_candidate",
        message=(
            f"`{semantic_label}` 역할 컬럼을 엔진이 아직 자동 확정하지 못했습니다. "
            f"가장 가능성 높은 후보: {candidate_text}. "
            "이 후보가 맞는지만 한 번 확인해 주세요."
        ),
        candidate_columns=candidates,
    )


def build_optional_field_suggestion(
    *,
    source_key: str,
    semantic_field: str,
    columns: list[str],
    rule: IntakeRule,
) -> IntakeSuggestion:
    aliases = rule.field_aliases.get(semantic_field, ())
    candidates = rank_candidate_columns(columns, aliases, semantic_field=semantic_field)
    semantic_label = _SEMANTIC_LABELS.get(semantic_field, semantic_field)
    candidate_text = ", ".join(candidates) if candidates else "후보 없음"
    return IntakeSuggestion(
        source_key=source_key,
        suggestion_type="review_optional_mapping",
        message=(
            f"`{semantic_label}` 컬럼은 필수는 아니지만 있으면 결과 해석이 더 정확해집니다. "
            f"추천 후보: {candidate_text}."
        ),
        candidate_columns=candidates,
    )


def build_mapping_review_suggestion(
    *,
    source_key: str,
    columns: list[str],
    rule: IntakeRule,
) -> IntakeSuggestion:
    semantic_fields = list(rule.required_fields[:3]) or list(rule.field_aliases.keys())[:3]
    return IntakeSuggestion(
        source_key=source_key,
        suggestion_type="mapping_review_required",
        message=(
            "현재 업로드 컬럼명만으로 표준 의미를 충분히 연결하지 못했습니다. "
            f"먼저 {', '.join(semantic_fields)} 기준 컬럼을 확인해 주세요."
        ),
        candidate_columns=columns[:10],
    )


def build_optional_source_missing_suggestion(source_key: str) -> IntakeSuggestion:
    return IntakeSuggestion(
        source_key=source_key,
        suggestion_type="optional_source_missing",
        message="이 파일은 없어도 이번 intake는 진행됩니다. 다만 있으면 연결 정확도와 설명 품질이 더 좋아집니다.",
        candidate_columns=[],
    )


def build_saved_mapping_fallback_suggestion(source_key: str) -> IntakeSuggestion:
    return IntakeSuggestion(
        source_key=source_key,
        suggestion_type="defer_to_saved_mapping",
        message="이번 업로드에서 컬럼 정보를 읽지 못해 저장된 회사 매핑 또는 기존 source 구조를 우선 참고합니다.",
        candidate_columns=[],
    )
