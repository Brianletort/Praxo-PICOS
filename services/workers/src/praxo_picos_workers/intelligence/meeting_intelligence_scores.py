"""Tier 1: Meeting Intelligence Beyond Summaries.

Derives strategic meeting scores from existing metrics:
  consensus_confidence, decision_ambiguity_score, commitment_strength_score,
  meeting_ROI_score, room_energy_curve, speaking_equity_score.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MeetingIntelligenceProfile:
    consensus_confidence: float = 0.5
    decision_ambiguity_score: float = 0.5
    commitment_strength_score: float = 0.5
    meeting_ROI_score: float = 0.5
    room_energy_curve: list[float] = field(default_factory=list)
    speaking_equity_score: float = 0.5
    interruption_asymmetry: float = 0.0
    meeting_fatigue_risk: float = 0.0
    unresolved_tension_index: float = 0.0
    alignment_decay_risk: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "consensus_confidence": round(self.consensus_confidence, 3),
            "decision_ambiguity_score": round(self.decision_ambiguity_score, 3),
            "commitment_strength_score": round(self.commitment_strength_score, 3),
            "meeting_ROI_score": round(self.meeting_ROI_score, 3),
            "room_energy_curve": [round(v, 2) for v in self.room_energy_curve],
            "speaking_equity_score": round(self.speaking_equity_score, 3),
            "interruption_asymmetry": round(self.interruption_asymmetry, 3),
            "meeting_fatigue_risk": round(self.meeting_fatigue_risk, 3),
            "unresolved_tension_index": round(self.unresolved_tension_index, 3),
            "alignment_decay_risk": round(self.alignment_decay_risk, 3),
        }


class MeetingIntelligenceScorer:
    """Computes strategic meeting scores from existing attrs."""

    def score(self, attrs: dict[str, Any]) -> MeetingIntelligenceProfile:
        power = attrs.get("power_dynamics", {})
        delivery = attrs.get("delivery_metrics", {})
        attention = attrs.get("attention", {})
        body = attrs.get("body_language", {})
        scorecard = attrs.get("scorecard", {})

        gini = power.get("gini_coefficient", 0.5)
        speaking_equity = max(0.0, 1.0 - gini)

        interruptions = power.get("interruptions", {})
        asymmetry = self._interruption_asymmetry(interruptions)

        consensus = self._consensus_confidence(power, attention)
        decision_ambiguity = self._decision_ambiguity(power, delivery)
        commitment_strength = self._commitment_strength(delivery, attention)
        roi = self._meeting_roi(scorecard, attention, delivery)
        fatigue = self._fatigue_risk(attention, delivery)
        tension = self._tension_index(interruptions, power)
        alignment_risk = self._alignment_decay(power, attention)
        energy_curve = self._room_energy(body)

        return MeetingIntelligenceProfile(
            consensus_confidence=consensus,
            decision_ambiguity_score=decision_ambiguity,
            commitment_strength_score=commitment_strength,
            meeting_ROI_score=roi,
            room_energy_curve=energy_curve,
            speaking_equity_score=speaking_equity,
            interruption_asymmetry=asymmetry,
            meeting_fatigue_risk=fatigue,
            unresolved_tension_index=tension,
            alignment_decay_risk=alignment_risk,
        )

    def _consensus_confidence(self, power: dict, attention: dict) -> float:
        gini = power.get("gini_coefficient", 0.5)
        ghosts = len(power.get("ghost_speakers", []))
        speakers = power.get("total_speakers", 1)
        focus = attention.get("focus_ratio", 0.5)

        score = 0.5
        if gini < 0.3:
            score += 0.2
        elif gini < 0.5:
            score += 0.1

        ghost_ratio = ghosts / max(1, speakers)
        score -= ghost_ratio * 0.3

        score += focus * 0.2
        return max(0.0, min(1.0, score))

    def _decision_ambiguity(self, power: dict, delivery: dict) -> float:
        ghosts = len(power.get("ghost_speakers", []))
        speakers = power.get("total_speakers", 1)
        monologues = delivery.get("monologue_count", 0)
        questions = delivery.get("question_count", 0)

        ambiguity = 0.3
        ambiguity += (ghosts / max(1, speakers)) * 0.3
        if monologues > 2:
            ambiguity += 0.15
        if questions < 2:
            ambiguity += 0.1
        return max(0.0, min(1.0, ambiguity))

    def _commitment_strength(self, delivery: dict, attention: dict) -> float:
        followup = attention.get("post_meeting_followup", False)
        notes = attention.get("note_taking_detected", False)
        questions = delivery.get("question_count", 0)

        score = 0.3
        if followup:
            score += 0.3
        if notes:
            score += 0.2
        if questions > 3:
            score += 0.2
        return min(1.0, score)

    def _meeting_roi(self, scorecard: dict, attention: dict, delivery: dict) -> float:
        overall = scorecard.get("overall_score", 0.5)
        focus = attention.get("focus_ratio", 0.5)
        ratio = delivery.get("talk_listen_ratio", 0.5)

        balanced_ratio = 1.0 - abs(ratio - 0.4) * 2
        return max(0.0, min(1.0, overall * 0.4 + focus * 0.3 + balanced_ratio * 0.3))

    def _fatigue_risk(self, attention: dict, delivery: dict) -> float:
        switches = attention.get("app_switch_count", 0)
        focus = attention.get("focus_ratio", 1.0)
        filler = delivery.get("filler_rate_per_min", 0)

        risk = 0.0
        risk += min(0.3, switches * 0.03)
        risk += max(0.0, (1.0 - focus) * 0.3)
        risk += min(0.2, filler * 0.03)
        return min(1.0, risk)

    def _tension_index(self, interruptions: dict, power: dict) -> float:
        total_interrupts = sum(
            sum(targets.values()) for targets in interruptions.values()
        ) if interruptions else 0
        speakers = power.get("total_speakers", 1)

        if speakers <= 1:
            return 0.0
        per_speaker = total_interrupts / speakers
        return min(1.0, per_speaker * 0.15)

    def _alignment_decay(self, power: dict, attention: dict) -> float:
        ghosts = len(power.get("ghost_speakers", []))
        focus = attention.get("focus_ratio", 1.0)

        risk = 0.0
        risk += ghosts * 0.15
        risk += max(0.0, (1.0 - focus) * 0.3)
        return min(1.0, risk)

    def _room_energy(self, body: dict) -> list[float]:
        per_frame = body.get("per_frame", [])
        if not per_frame:
            return []

        energy_map = {"high": 1.0, "moderate": 0.6, "low": 0.3, "flat": 0.1}
        return [energy_map.get(f.get("energy", "moderate"), 0.5) for f in per_frame]

    @staticmethod
    def _interruption_asymmetry(interruptions: dict) -> float:
        if not interruptions:
            return 0.0

        outgoing = {
            speaker: sum(targets.values())
            for speaker, targets in interruptions.items()
        }
        if len(outgoing) < 2:
            return 0.0

        vals = list(outgoing.values())
        max_val = max(vals)
        min_val = min(vals)
        total = sum(vals)
        if total == 0:
            return 0.0
        return (max_val - min_val) / total
