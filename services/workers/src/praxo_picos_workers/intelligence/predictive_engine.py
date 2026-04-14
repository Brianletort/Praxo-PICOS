"""Tier 3: Predictive stakeholder strategy and decision intelligence.

Uses historical data patterns + LLM to predict outcomes, generate
context assembly artifacts, and produce strategic recommendations.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from services.api.src.praxo_picos_api.agents.llm_provider import LLMProvider, ModelTier

logger = logging.getLogger(__name__)


@dataclass
class StakeholderPrediction:
    person_id: str
    person_name: str = ""
    approval_likelihood: float = 0.5
    escalation_risk: float = 0.0
    socialization_required_score: float = 0.5
    objection_probability_by_theme: dict[str, float] = field(default_factory=dict)
    ideal_messenger_score: float = 0.5
    timing_advantage_score: float = 0.5
    meeting_readiness_score: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "person_id": self.person_id,
            "person_name": self.person_name,
            "approval_likelihood": round(self.approval_likelihood, 3),
            "escalation_risk": round(self.escalation_risk, 3),
            "socialization_required_score": round(self.socialization_required_score, 3),
            "objection_probability_by_theme": {
                k: round(v, 2) for k, v in self.objection_probability_by_theme.items()
            },
            "ideal_messenger_score": round(self.ideal_messenger_score, 3),
            "timing_advantage_score": round(self.timing_advantage_score, 3),
            "meeting_readiness_score": round(self.meeting_readiness_score, 3),
        }


@dataclass
class DecisionIntelligence:
    decision_quality_score: float = 0.5
    assumption_density: float = 0.5
    evidence_strength_score: float = 0.5
    option_diversity_score: float = 0.5
    bias_markers: list[str] = field(default_factory=list)
    decision_reversal_probability: float = 0.0
    outcome_attribution_confidence: float = 0.5
    regret_risk_estimate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_quality_score": round(self.decision_quality_score, 3),
            "assumption_density": round(self.assumption_density, 3),
            "evidence_strength_score": round(self.evidence_strength_score, 3),
            "option_diversity_score": round(self.option_diversity_score, 3),
            "bias_markers": self.bias_markers,
            "decision_reversal_probability": round(self.decision_reversal_probability, 3),
            "outcome_attribution_confidence": round(self.outcome_attribution_confidence, 3),
            "regret_risk_estimate": round(self.regret_risk_estimate, 3),
        }


class PredictiveEngine:
    """Generates predictive scores from accumulated historical data."""

    def predict_stakeholder(
        self,
        person_attrs: dict[str, Any],
        meeting_context: str = "",
    ) -> StakeholderPrediction:
        """Predict stakeholder behavior based on historical patterns."""
        rel = person_attrs.get("relationship_intelligence", {})
        dynamics = person_attrs.get("relationship_dynamics", {})
        behavioral = person_attrs.get("behavioral_profile", {})

        alignment = rel.get("stakeholder_alignment_score", 0.5)
        trust = rel.get("trust_trend", "stable")
        friction = rel.get("friction_index", 0.0)
        follow_through = rel.get("follow_through_probability", 0.5)
        resistance = behavioral.get("silent_resistance_probability", 0.0)
        interaction_count = dynamics.get("interaction_count", 0)

        approval = self._predict_approval(alignment, trust, friction, resistance)
        escalation = self._predict_escalation(friction, trust, resistance)
        socialization = self._predict_socialization_need(alignment, interaction_count, trust)

        topics = behavioral.get("topics_that_create_friction", [])
        objection_probs = {t: min(1.0, friction + 0.2) for t in topics[:5]} if topics else {}

        readiness = self._meeting_readiness(alignment, follow_through, friction)

        return StakeholderPrediction(
            person_id=person_attrs.get("person_id", ""),
            person_name=person_attrs.get("person_name", ""),
            approval_likelihood=approval,
            escalation_risk=escalation,
            socialization_required_score=socialization,
            objection_probability_by_theme=objection_probs,
            meeting_readiness_score=readiness,
        )

    def assess_decision(
        self,
        decision_attrs: dict[str, Any],
    ) -> DecisionIntelligence:
        """Assess decision quality from available evidence."""
        transcript_intel = decision_attrs.get("transcript_intelligence", {})
        meeting_intel = decision_attrs.get("meeting_intelligence", {})

        clarity = transcript_intel.get("decision_clarity", 0.5)
        consensus = meeting_intel.get("consensus_confidence", 0.5)
        accountability = transcript_intel.get("accountability_strength", 0.5)
        vagueness = transcript_intel.get("vagueness_density", 0.5)
        hidden_disagree = transcript_intel.get("hidden_disagreement_detected", False)

        quality = (clarity * 0.3 + consensus * 0.3 + accountability * 0.2 + (1.0 - vagueness) * 0.2)
        assumption_density = vagueness * 0.6 + (1.0 - clarity) * 0.4
        evidence_strength = clarity * 0.5 + (1.0 - vagueness) * 0.5

        bias_markers = []
        if meeting_intel.get("speaking_equity_score", 1.0) < 0.3:
            bias_markers.append("dominated_by_few_voices")
        if hidden_disagree:
            bias_markers.append("hidden_disagreement_present")
        if meeting_intel.get("meeting_fatigue_risk", 0) > 0.5:
            bias_markers.append("decision_under_fatigue")

        reversal = 0.0
        if hidden_disagree:
            reversal += 0.3
        if vagueness > 0.6:
            reversal += 0.2
        if consensus < 0.4:
            reversal += 0.3

        regret = max(0.0, 1.0 - quality) * 0.5 + reversal * 0.3

        return DecisionIntelligence(
            decision_quality_score=max(0.0, min(1.0, quality)),
            assumption_density=max(0.0, min(1.0, assumption_density)),
            evidence_strength_score=max(0.0, min(1.0, evidence_strength)),
            option_diversity_score=max(0.0, min(1.0, 1.0 - vagueness)),
            bias_markers=bias_markers,
            decision_reversal_probability=max(0.0, min(1.0, reversal)),
            outcome_attribution_confidence=max(0.0, min(1.0, clarity)),
            regret_risk_estimate=max(0.0, min(1.0, regret)),
        )

    def _predict_approval(self, alignment: float, trust: str, friction: float, resistance: float) -> float:
        score = alignment * 0.4
        trust_bonus = {"warming": 0.2, "strengthening": 0.25, "stable": 0.1}.get(trust, 0.0)
        score += trust_bonus
        score -= friction * 0.2
        score -= resistance * 0.15
        return max(0.0, min(1.0, score + 0.1))

    def _predict_escalation(self, friction: float, trust: str, resistance: float) -> float:
        risk = friction * 0.4
        if trust in ("weakening", "at_risk", "cooling"):
            risk += 0.25
        risk += resistance * 0.2
        return max(0.0, min(1.0, risk))

    def _predict_socialization_need(self, alignment: float, count: int, trust: str) -> float:
        need = max(0.0, 0.8 - alignment)
        if count < 5:
            need += 0.2
        if trust in ("weakening", "at_risk"):
            need += 0.15
        return max(0.0, min(1.0, need))

    def _meeting_readiness(self, alignment: float, follow_through: float, friction: float) -> float:
        return max(0.0, min(1.0, alignment * 0.4 + follow_through * 0.3 + (1.0 - friction) * 0.3))
