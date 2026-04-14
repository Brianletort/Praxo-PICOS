"""Tests for context assembly and predictive engine serialization."""
from __future__ import annotations

import pytest

from services.workers.src.praxo_picos_workers.intelligence.context_assembly import (
    FollowUpPlan,
    PreBriefPacket,
)
from services.workers.src.praxo_picos_workers.intelligence.predictive_engine import (
    DecisionIntelligence,
    PredictiveEngine,
    StakeholderPrediction,
)


class TestPreBriefPacket:
    def test_empty_to_dict(self):
        p = PreBriefPacket()
        d = p.to_dict()
        assert d["summary"] == ""
        assert d["stakeholder_map"] == []
        assert d["talking_points"] == []

    def test_populated_to_dict(self):
        p = PreBriefPacket(
            summary="Key meeting about budget",
            talking_points=["Lead with ROI", "Address timeline concerns"],
            key_risks=["Budget pushback from finance"],
        )
        d = p.to_dict()
        assert "budget" in d["summary"].lower()
        assert len(d["talking_points"]) == 2
        assert len(d["key_risks"]) == 1


class TestFollowUpPlan:
    def test_empty_to_dict(self):
        f = FollowUpPlan()
        d = f.to_dict()
        assert d["follow_ups"] == []

    def test_with_follow_ups(self):
        f = FollowUpPlan(follow_ups=[
            {"person_name": "Alice", "tone": "executive", "subject_line": "Re: Budget", "body": "Thanks for the discussion."},
        ])
        d = f.to_dict()
        assert len(d["follow_ups"]) == 1
        assert d["follow_ups"][0]["person_name"] == "Alice"


class TestStakeholderPrediction:
    def test_to_dict_serialization(self):
        sp = StakeholderPrediction(
            person_id="p1",
            person_name="Sarah",
            approval_likelihood=0.75,
            escalation_risk=0.1,
            objection_probability_by_theme={"budget": 0.6, "timeline": 0.3},
        )
        d = sp.to_dict()
        assert d["person_name"] == "Sarah"
        assert d["approval_likelihood"] == 0.75
        assert d["objection_probability_by_theme"]["budget"] == 0.6


class TestDecisionIntelligence:
    def test_to_dict_serialization(self):
        di = DecisionIntelligence(
            decision_quality_score=0.82,
            bias_markers=["dominated_by_few_voices"],
        )
        d = di.to_dict()
        assert d["decision_quality_score"] == 0.82
        assert "dominated_by_few_voices" in d["bias_markers"]


class TestPredictiveEngineEdgeCases:
    def test_empty_person_attrs(self):
        engine = PredictiveEngine()
        pred = engine.predict_stakeholder({})
        assert 0.0 <= pred.approval_likelihood <= 1.0
        assert 0.0 <= pred.escalation_risk <= 1.0

    def test_empty_decision_attrs(self):
        engine = PredictiveEngine()
        result = engine.assess_decision({})
        assert 0.0 <= result.decision_quality_score <= 1.0
        assert isinstance(result.bias_markers, list)

    def test_all_scores_clamped(self):
        engine = PredictiveEngine()
        extreme = {
            "relationship_intelligence": {"stakeholder_alignment_score": 2.0, "friction_index": -1.0},
            "behavioral_profile": {"silent_resistance_probability": 5.0},
            "relationship_dynamics": {"interaction_count": 1000},
        }
        pred = engine.predict_stakeholder(extreme)
        assert pred.approval_likelihood <= 1.0
        assert pred.escalation_risk >= 0.0
