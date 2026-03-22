from __future__ import annotations

from difflib import SequenceMatcher

from .models import IntakeSuggestion
from .rules import IntakeRule


def _normalize_text(value: str) -> str:
    return "".join(ch for ch in str(value).strip().lower() if ch.isalnum())


def _rank_candidate_columns(columns: list[str], aliases: tuple[str, ...], limit: int = 3) -> list[str]:
    normalized_aliases = [_normalize_text(alias) for alias in aliases]
    scored: list[tuple[float, str]] = []
    for column in columns:
        normalized_column = _normalize_text(column)
        best_score = 0.0
        for alias in normalized_aliases:
            if not alias:
                continue
            score = SequenceMatcher(None, normalized_column, alias).ratio()
            if alias in normalized_column or normalized_column in alias:
                score = max(score, 0.92)
            best_score = max(best_score, score)
        if best_score > 0:
            scored.append((best_score, column))
    scored.sort(key=lambda item: (-item[0], item[1]))
    result: list[str] = []
    for _score, column in scored:
        if column not in result:
            result.append(column)
        if len(result) >= limit:
            break
    return result


def build_missing_required_field_suggestion(
    *,
    source_key: str,
    semantic_field: str,
    columns: list[str],
    rule: IntakeRule,
) -> IntakeSuggestion:
    aliases = rule.field_aliases.get(semantic_field, ())
    candidates = _rank_candidate_columns(columns, aliases)
    candidate_text = ", ".join(candidates) if candidates else "뚜렷한 후보 없음"
    return IntakeSuggestion(
        source_key=source_key,
        suggestion_type="required_mapping_candidate",
        message=(
            f"필수 의미 `{semantic_field}` 를 아직 확정하지 못했습니다. "
            f"추천 후보: {candidate_text}. 사람이 한 번 확인하는 것이 안전합니다."
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
    candidates = _rank_candidate_columns(columns, aliases)
    candidate_text = ", ".join(candidates) if candidates else "후보 없음"
    return IntakeSuggestion(
        source_key=source_key,
        suggestion_type="review_optional_mapping",
        message=(
            f"`{semantic_field}` 의미 컬럼은 필수는 아니지만 있으면 결과 해석이 더 정확해집니다. "
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
        message="선택 입력이 없어도 이번 intake는 진행됩니다. 다만 이 파일이 있으면 연결 정확도와 설명 품질이 더 좋아집니다.",
        candidate_columns=[],
    )


def build_saved_mapping_fallback_suggestion(source_key: str) -> IntakeSuggestion:
    return IntakeSuggestion(
        source_key=source_key,
        suggestion_type="defer_to_saved_mapping",
        message="이번 업로드에서 컬럼 정보를 읽지 못해 저장된 회사 매핑 또는 기존 source 구조를 우선 참고합니다.",
        candidate_columns=[],
    )
