"""Tests for the strategic intelligence layer (Tiers 1-3)."""
from __future__ import annotations

import pytest

from services.workers.src.praxo_picos_workers.intelligence.executive_performance import (
    ExecutivePerformanceScorer,
)
from services.workers.src.praxo_picos_workers.intelligence.meeting_intelligence_scores import (
    MeetingIntelligenceScorer,
)
from services.workers.src.praxo_picos_workers.intelligence.operating_optimization import (
    OperatingOptimizationScorer,
)
from services.workers.src.praxo_picos_workers.intelligence.predictive_engine import (
    PredictiveEngine,
)
from services.workers.src.praxo_picos_workers.intelligence.relationship_intelligence import (
    RelationshipIntelligenceScorer,
)
from services.workers.src.praxo_picos_workers.intelligence.transcript_analysis import (
    TranscriptIntelligence,
    PersonBehavioralProfile,
)


class TestExecutivePerformance:
    def test_good_metrics_produce_high_scores(self):
        scorer = ExecutivePerformanceScorer()
        attrs = {
            "delivery_metrics": {
                "pace_wpm": 140,
                "filler_rate_per_min": 1.5,
                "talk_listen_ratio": 0.4,
                "vocabulary_complexity": 0.55,
                "monologue_max_s": 45,
                "question_rate_per_min": 1.0,
                "monologue_count": 0,
                "pause_strategic": 5,
                "pause_awkward": 0,
            },
            "body_language": {
                "eye_contact_pct": 0.8,
                "dominant_posture": "upright",
                "dominant_expression": "engaged",
                "energy_trajectory": "stable",
            },
        }
        result = scorer.score(attrs)
        assert result.executive_presence_score > 0.7
        assert result.clarity_score > 0.7
        assert result.brevity_efficiency_score > 0.7
        assert len(result.confidence_leakage_markers) == 0

    def test_poor_metrics_flag_leakage(self):
        scorer = ExecutivePerformanceScorer()
        attrs = {
            "delivery_metrics": {"filler_rate_per_min": 8.0, "pause_awkward": 5},
            "body_language": {"eye_contact_pct": 0.2, "dominant_posture": "slouched", "energy_trajectory": "decreasing"},
        }
        result = scorer.score(attrs)
        assert len(result.confidence_leakage_markers) >= 3

    def test_empty_attrs_return_defaults(self):
        scorer = ExecutivePerformanceScorer()
        result = scorer.score({})
        assert 0.0 <= result.executive_presence_score <= 1.0
        d = result.to_dict()
        assert "executive_presence_score" in d

    def test_engagement_curve_from_per_frame(self):
        scorer = ExecutivePerformanceScorer()
        attrs = {
            "body_language": {
                "per_frame": [
                    {"energy": "high", "expression": "engaged"},
                    {"energy": "moderate", "expression": "neutral"},
                    {"energy": "low", "expression": "distracted"},
                ],
            },
            "delivery_metrics": {},
        }
        result = scorer.score(attrs)
        assert len(result.audience_engagement_curve) == 3
        assert result.audience_engagement_curve[0] > result.audience_engagement_curve[2]


class TestMeetingIntelligence:
    def test_balanced_meeting_scores_well(self):
        scorer = MeetingIntelligenceScorer()
        attrs = {
            "power_dynamics": {"gini_coefficient": 0.2, "ghost_speakers": [], "total_speakers": 4, "interruptions": {}},
            "attention": {"focus_ratio": 0.9, "app_switch_count": 1, "note_taking_detected": True, "post_meeting_followup": True, "pre_meeting_docs_opened": 2},
            "delivery_metrics": {"question_count": 5, "monologue_count": 0, "talk_listen_ratio": 0.35},
            "scorecard": {"overall_score": 0.85},
        }
        result = scorer.score(attrs)
        assert result.speaking_equity_score > 0.7
        assert result.consensus_confidence > 0.5
        assert result.meeting_ROI_score > 0.5

    def test_dominated_meeting_flags_issues(self):
        scorer = MeetingIntelligenceScorer()
        attrs = {
            "power_dynamics": {"gini_coefficient": 0.8, "ghost_speakers": ["A", "B"], "total_speakers": 5, "interruptions": {"C": {"A": 5, "B": 3}}},
            "attention": {"focus_ratio": 0.4, "app_switch_count": 10},
            "delivery_metrics": {},
        }
        result = scorer.score(attrs)
        assert result.speaking_equity_score < 0.3
        assert result.alignment_decay_risk > 0.3

    def test_to_dict_has_all_fields(self):
        scorer = MeetingIntelligenceScorer()
        d = scorer.score({}).to_dict()
        assert "consensus_confidence" in d
        assert "meeting_ROI_score" in d
        assert "interruption_asymmetry" in d


class TestRelationshipIntelligence:
    def test_strong_relationship(self):
        scorer = RelationshipIntelligenceScorer()
        attrs = {
            "relationship_dynamics": {"trend": "warming", "interaction_count": 20, "one_on_one_ratio": 0.6, "initiated_by_you_ratio": 0.5, "commitment_completion_rate": 0.9, "last_interaction_days_ago": 3},
            "communication_dynamic": {"pace_diff_pct": 5},
        }
        result = scorer.score(attrs)
        assert result.stakeholder_alignment_score > 0.6
        assert result.friction_index < 0.3
        assert result.trust_trend == "strengthening"

    def test_cooling_relationship_flags_risk(self):
        scorer = RelationshipIntelligenceScorer()
        attrs = {
            "relationship_dynamics": {"trend": "cooling", "interaction_count": 5, "commitment_completion_rate": 0.3, "last_interaction_days_ago": 35},
            "communication_dynamic": {"pace_diff_pct": 25},
        }
        result = scorer.score(attrs)
        assert result.friction_index > 0.4
        assert result.relationship_decay_velocity > 0


class TestOperatingOptimization:
    def test_high_meeting_load(self):
        scorer = OperatingOptimizationScorer()
        attrs = {
            "cognitive_energy": {"avg_energy": 0.3, "meeting_count": 7, "consecutive_meeting_max": 4, "hourly": [{"switch_rate": 0.5, "frame_count": 10}]},
            "deep_work_blocks": [],
            "deep_work_total_min": 0,
        }
        result = scorer.score(attrs)
        assert result.overload_probability > 0.5
        assert result.decision_fatigue_index > 0.3
        assert result.deep_work_probability < 0.3

    def test_low_meeting_load(self):
        scorer = OperatingOptimizationScorer()
        attrs = {
            "cognitive_energy": {"avg_energy": 0.8, "meeting_count": 1, "consecutive_meeting_max": 1, "hourly": []},
            "deep_work_total_min": 180,
        }
        result = scorer.score(attrs)
        assert result.overload_probability < 0.3
        assert result.deep_work_probability > 0.7


class TestPredictiveEngine:
    def test_aligned_stakeholder_high_approval(self):
        engine = PredictiveEngine()
        attrs = {
            "relationship_intelligence": {"stakeholder_alignment_score": 0.8, "trust_trend": "strengthening", "friction_index": 0.1, "follow_through_probability": 0.9},
            "relationship_dynamics": {"interaction_count": 15},
            "behavioral_profile": {"silent_resistance_probability": 0.05, "topics_that_create_friction": []},
        }
        pred = engine.predict_stakeholder(attrs)
        assert pred.approval_likelihood > 0.5
        assert pred.escalation_risk < 0.3

    def test_friction_stakeholder_high_risk(self):
        engine = PredictiveEngine()
        attrs = {
            "relationship_intelligence": {"stakeholder_alignment_score": 0.2, "trust_trend": "weakening", "friction_index": 0.7, "follow_through_probability": 0.3},
            "relationship_dynamics": {"interaction_count": 3},
            "behavioral_profile": {"silent_resistance_probability": 0.6, "topics_that_create_friction": ["budget", "timeline"]},
        }
        pred = engine.predict_stakeholder(attrs)
        assert pred.approval_likelihood < 0.5
        assert pred.escalation_risk > 0.3
        assert len(pred.objection_probability_by_theme) > 0

    def test_decision_quality_assessment(self):
        engine = PredictiveEngine()
        attrs = {
            "transcript_intelligence": {"decision_clarity": 0.8, "accountability_strength": 0.7, "vagueness_density": 0.2, "hidden_disagreement_detected": False},
            "meeting_intelligence": {"consensus_confidence": 0.7, "speaking_equity_score": 0.6},
        }
        result = engine.assess_decision(attrs)
        assert result.decision_quality_score > 0.6
        assert len(result.bias_markers) == 0

    def test_poor_decision_flags_bias(self):
        engine = PredictiveEngine()
        attrs = {
            "transcript_intelligence": {"decision_clarity": 0.3, "vagueness_density": 0.8, "hidden_disagreement_detected": True, "accountability_strength": 0.2},
            "meeting_intelligence": {"consensus_confidence": 0.3, "speaking_equity_score": 0.2, "meeting_fatigue_risk": 0.7},
        }
        result = engine.assess_decision(attrs)
        assert result.decision_quality_score < 0.5
        assert len(result.bias_markers) >= 2
        assert result.decision_reversal_probability > 0.3


class TestDataclassSerialize:
    def test_transcript_intelligence_to_dict(self):
        ti = TranscriptIntelligence(hedging_rate=0.3, consensus_quality="surface")
        d = ti.to_dict()
        assert d["hedging_rate"] == 0.3
        assert d["consensus_quality"] == "surface"
        assert "objection_handling_effectiveness" in d

    def test_person_behavioral_to_dict(self):
        bp = PersonBehavioralProfile(preferred_message_style="data_driven")
        d = bp.to_dict()
        assert d["preferred_message_style"] == "data_driven"
        assert "topics_that_land_well" in d
