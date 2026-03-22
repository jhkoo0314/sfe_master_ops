from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.intake.rules import get_intake_rule
from modules.intake.suggestions import build_missing_required_field_suggestion


def test_required_mapping_suggestion_uses_clearer_message():
    rule = get_intake_rule("target")
    suggestion = build_missing_required_field_suggestion(
        source_key="target",
        semantic_field="target_value",
        columns=["계획금액", "기준년월"],
        rule=rule,
    )

    assert "엔진이 아직 자동 확정하지 못했습니다" in suggestion.message
    assert "이 후보가 맞는지만 한 번 확인해 주세요." in suggestion.message
    assert suggestion.candidate_columns == ["계획금액"]


def test_required_mapping_suggestion_filters_noisy_candidates():
    rule = get_intake_rule("sales")
    suggestion = build_missing_required_field_suggestion(
        source_key="sales",
        semantic_field="product",
        columns=["본부코드", "거래처코드", "브랜드코드", "제품명"],
        rule=rule,
    )

    assert "제품명" in suggestion.candidate_columns
    assert "본부코드" not in suggestion.candidate_columns
    assert "거래처코드" not in suggestion.candidate_columns


def test_activity_date_suggestion_does_not_pick_hospital_or_notes():
    rule = get_intake_rule("crm_activity")
    suggestion = build_missing_required_field_suggestion(
        source_key="crm_activity",
        semantic_field="activity_date",
        columns=["방문기관", "방문횟수", "활동메모", "방문일자"],
        rule=rule,
    )

    assert suggestion.candidate_columns == ["방문일자"]
