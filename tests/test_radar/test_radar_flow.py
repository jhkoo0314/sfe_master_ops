import re

import pytest
from pydantic import ValidationError

from modules.radar.option_engine import build_decision_options
from modules.radar.priority_engine import score_signals
from modules.radar.schemas import RadarInputStandard
from modules.radar.service import build_radar_result_asset
from modules.radar.signal_engine import detect_signals


def _build_valid_input(**overrides) -> RadarInputStandard:
    base = {
        "meta": {
            "company_key": "daon_pharma",
            "run_id": "run-2026-03-16-001",
            "period_type": "monthly",
            "period_value": "2026-03",
            "source_status": "validation_approved",
        },
        "kpi_summary": {
            "goal_attainment_pct": 88.4,
            "pv_change_pct": -26.0,
            "hir": 48.5,
            "rtr": 58.2,
            "bcr": 61.0,
            "phr": 63.0,
        },
        "scope_summaries": {
            "by_branch": [{"branch_key": "seoul"}, {"branch_key": "daegu"}],
            "by_rep": [{"rep_id": "REP001"}, {"rep_id": "REP002"}, {"rep_id": "REP003"}],
            "by_product": [],
        },
        "validation_summary": {
            "status": "approved",
            "warnings": [],
            "quality_score": 0.93,
        },
        "sandbox_summary": {
            "top_declines": [],
            "top_gains": [],
            "trend_flags": ["pv_down_2_cycles", "goal_down_2_cycles"],
        },
    }
    for key, value in overrides.items():
        base[key] = value
    return RadarInputStandard(**base)


class TestRadarSchemaValidation:
    def test_requires_validation_approved_or_usable(self):
        with pytest.raises(ValidationError):
            _build_valid_input(validation_summary={"status": "failed", "warnings": [], "quality_score": 0.8})

    def test_requires_source_status_contract(self):
        with pytest.raises(ValidationError):
            _build_valid_input(
                meta={
                    "company_key": "daon_pharma",
                    "run_id": "run-2026-03-16-001",
                    "period_type": "monthly",
                    "period_value": "2026-03",
                    "source_status": "raw_source",
                }
            )

    def test_missing_required_kpi_field_fails(self):
        with pytest.raises(ValidationError):
            _build_valid_input(kpi_summary={"goal_attainment_pct": 92.0, "pv_change_pct": -10.0, "hir": 70.0})


class TestRadarSignalDetection:
    def test_detects_all_v01_signal_types(self):
        radar_input = _build_valid_input()
        signals = detect_signals(radar_input)
        signal_types = {s.signal_type for s in signals}
        assert "goal_underperformance" in signal_types
        assert "pv_decline" in signal_types
        assert "hir_weakness" in signal_types
        assert "rtr_weakness" in signal_types
        assert "compound_risk" in signal_types

    def test_compound_risk_requires_multiple_weak_signals(self):
        weak_input = _build_valid_input(
            kpi_summary={
                "goal_attainment_pct": 94.0,
                "pv_change_pct": -10.0,
                "hir": 75.0,
                "rtr": 75.0,
                "bcr": 60.0,
                "phr": 60.0,
            }
        )
        weak_signals = detect_signals(weak_input)
        assert {s.signal_type for s in weak_signals} == {"goal_underperformance"}

        strong_input = _build_valid_input(
            kpi_summary={
                "goal_attainment_pct": 89.0,
                "pv_change_pct": -20.0,
                "hir": 58.0,
                "rtr": 68.0,
                "bcr": 60.0,
                "phr": 60.0,
            }
        )
        strong_signals = detect_signals(strong_input)
        assert "compound_risk" in {s.signal_type for s in strong_signals}


class TestRadarPriorityScoring:
    def test_priority_score_range_and_order(self):
        radar_input = _build_valid_input()
        detected = detect_signals(radar_input)
        scored = score_signals(detected, radar_input)
        assert len(scored) > 0
        for signal in scored:
            assert 0 <= signal.priority_score <= 100
            assert signal.priority_breakdown is not None

        ordered_scores = [s.priority_score for s in scored]
        assert ordered_scores == sorted(ordered_scores, reverse=True)


class TestRadarDecisionOptions:
    def test_generates_allowed_option_styles_only(self):
        radar_input = _build_valid_input()
        detected = detect_signals(radar_input)
        one_signal = detected[0]
        options = build_decision_options(one_signal)
        styles = {opt.style for opt in options}
        assert styles.issubset(
            {"coaching_focus", "monitoring_hold", "selective_intervention", "strategic_escalation"}
        )

    def test_no_forbidden_directive_language(self):
        result = build_radar_result_asset(_build_valid_input())
        forbidden_terms = [
            r"\btomorrow\b",
            r"\bvisit\b",
            r"\bschedule\b",
            r"\bhospital [a-z0-9_-]+\b",
            r"내일",
            r"방문하",
            r"스케줄",
            r"동선",
        ]
        full_text = " ".join(
            [signal.message for signal in result.signals]
            + [opt.description for signal in result.signals for opt in signal.decision_options]
        ).lower()
        for pattern in forbidden_terms:
            assert re.search(pattern, full_text) is None, f"forbidden directive detected: {pattern}"

    def test_no_root_cause_certainty_language(self):
        result = build_radar_result_asset(_build_valid_input())
        forbidden_certainty = [
            "root cause is",
            "definitive root cause",
            "확정 원인",
            "원인이 확정",
            "원인은",
        ]
        full_text = " ".join(
            [signal.message for signal in result.signals]
            + [exp for signal in result.signals for exp in signal.possible_explanations]
            + [opt.description for signal in result.signals for opt in signal.decision_options]
        ).lower()
        for term in forbidden_certainty:
            assert term.lower() not in full_text


class TestRadarGuardrails:
    def test_no_kpi_engine_import_in_radar_module(self):
        radar_files = [
            "modules/radar/service.py",
            "modules/radar/signal_engine.py",
            "modules/radar/priority_engine.py",
            "modules/radar/option_engine.py",
        ]
        disallowed_patterns = [
            "from modules.kpi",
            "import modules.kpi",
            "compute_crm_kpi_bundle",
            "compute_sandbox_rep_kpis",
            "compute_sandbox_official_kpi_6",
        ]
        for path in radar_files:
            with open(path, encoding="utf-8") as fp:
                text = fp.read()
            for pattern in disallowed_patterns:
                assert pattern not in text, f"kpi recalculation dependency found in {path}: {pattern}"

    def test_result_asset_structure(self):
        result = build_radar_result_asset(_build_valid_input())
        assert result.asset_type == "radar_result_asset"
        assert result.summary.signal_count == len(result.signals)
        assert result.summary.overall_status in {"normal", "warning", "critical"}
