"""Tier 2: LLM-derived intelligence from transcript analysis.

Analyzes meeting transcripts for semantic patterns that raw metrics cannot detect:
  hedging, vagueness, objection handling, consensus quality, hidden disagreement,
  persuasion effectiveness, behavioral coaching patterns.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from services.api.src.praxo_picos_api.agents.llm_provider import LLMProvider, ModelTier

logger = logging.getLogger(__name__)

TRANSCRIPT_ANALYSIS_SYSTEM = """\
You are an expert meeting analyst. Analyze the meeting transcript and existing metrics.
Return JSON with ALL of the following fields:

1. BEHAVIORAL COACHING:
  "hedging_rate": float 0-1 (how often the speaker hedges: "maybe", "I think", "sort of"),
  "persuasion_effectiveness": float 0-1 (how well key points land based on engagement),
  "challenge_response_pattern": "defensive"|"curious"|"dismissive"|"collaborative"|"avoidant",
  "patience_decay_detected": boolean (did patience visibly drop late in meeting),
  "tone_consistency": float 0-1 (how consistent is tone throughout),

2. MEETING INTELLIGENCE:
  "consensus_quality": "genuine"|"surface"|"forced"|"absent",
  "hidden_disagreement_detected": boolean,
  "hidden_disagreement_evidence": string or null,
  "vagueness_density": float 0-1 (how much language is vague vs specific),
  "accountability_strength": float 0-1 (how clearly action items are assigned),
  "decision_clarity": float 0-1 (how clearly decisions are stated),

3. EXECUTIVE PERFORMANCE:
  "objection_handling_effectiveness": float 0-1,
  "narrative_resonance_score": float 0-1 (did the main story/framing land),
  "decision_driving_moments": list of {"timestamp_approx": string, "description": string},
  "message_compression_score": float 0-1 (how efficiently key points communicated),

4. COMMUNICATION DYNAMICS:
  "emotional_temperature": "warm"|"neutral"|"tense"|"hostile",
  "disagreement_detection_score": float 0-1,
  "trust_preservation_score": float 0-1 (did interactions maintain trust),
  "social_signal_asymmetry": float 0-1 (power imbalance in communication)

Be precise. Use evidence from the transcript. If data is insufficient, use 0.5 as default."""

PERSON_ANALYSIS_SYSTEM = """\
Analyze this person's communication patterns across meetings. Return JSON:
  "preferred_message_style": "data_driven"|"vision_led"|"relationship_first"|"action_oriented"|"consensus_seeking",
  "decision_driver_profile": "analytical"|"intuitive"|"authority"|"collaborative"|"pragmatic",
  "influenceability_profile": "easily_influenced"|"evidence_based"|"authority_driven"|"peer_influenced"|"independent",
  "silent_resistance_probability": float 0-1,
  "response_under_pressure": "calm"|"defensive"|"aggressive"|"avoidant"|"analytical",
  "best_approach_for_asks": string (one sentence recommendation),
  "topics_that_land_well": list of strings,
  "topics_that_create_friction": list of strings
Be concise. Base analysis on evidence provided."""


@dataclass
class TranscriptIntelligence:
    hedging_rate: float = 0.5
    persuasion_effectiveness: float = 0.5
    challenge_response_pattern: str = "collaborative"
    patience_decay_detected: bool = False
    tone_consistency: float = 0.5
    consensus_quality: str = "genuine"
    hidden_disagreement_detected: bool = False
    hidden_disagreement_evidence: str | None = None
    vagueness_density: float = 0.5
    accountability_strength: float = 0.5
    decision_clarity: float = 0.5
    objection_handling_effectiveness: float = 0.5
    narrative_resonance_score: float = 0.5
    decision_driving_moments: list[dict[str, str]] = field(default_factory=list)
    message_compression_score: float = 0.5
    emotional_temperature: str = "neutral"
    disagreement_detection_score: float = 0.0
    trust_preservation_score: float = 0.5
    social_signal_asymmetry: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "hedging_rate": round(self.hedging_rate, 3),
            "persuasion_effectiveness": round(self.persuasion_effectiveness, 3),
            "challenge_response_pattern": self.challenge_response_pattern,
            "patience_decay_detected": self.patience_decay_detected,
            "tone_consistency": round(self.tone_consistency, 3),
            "consensus_quality": self.consensus_quality,
            "hidden_disagreement_detected": self.hidden_disagreement_detected,
            "hidden_disagreement_evidence": self.hidden_disagreement_evidence,
            "vagueness_density": round(self.vagueness_density, 3),
            "accountability_strength": round(self.accountability_strength, 3),
            "decision_clarity": round(self.decision_clarity, 3),
            "objection_handling_effectiveness": round(self.objection_handling_effectiveness, 3),
            "narrative_resonance_score": round(self.narrative_resonance_score, 3),
            "decision_driving_moments": self.decision_driving_moments,
            "message_compression_score": round(self.message_compression_score, 3),
            "emotional_temperature": self.emotional_temperature,
            "disagreement_detection_score": round(self.disagreement_detection_score, 3),
            "trust_preservation_score": round(self.trust_preservation_score, 3),
            "social_signal_asymmetry": round(self.social_signal_asymmetry, 3),
        }


@dataclass
class PersonBehavioralProfile:
    preferred_message_style: str = "action_oriented"
    decision_driver_profile: str = "pragmatic"
    influenceability_profile: str = "evidence_based"
    silent_resistance_probability: float = 0.0
    response_under_pressure: str = "calm"
    best_approach_for_asks: str = ""
    topics_that_land_well: list[str] = field(default_factory=list)
    topics_that_create_friction: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "preferred_message_style": self.preferred_message_style,
            "decision_driver_profile": self.decision_driver_profile,
            "influenceability_profile": self.influenceability_profile,
            "silent_resistance_probability": round(self.silent_resistance_probability, 3),
            "response_under_pressure": self.response_under_pressure,
            "best_approach_for_asks": self.best_approach_for_asks,
            "topics_that_land_well": self.topics_that_land_well,
            "topics_that_create_friction": self.topics_that_create_friction,
        }


class TranscriptAnalyzer:
    """LLM-powered transcript analysis for semantic intelligence."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def analyze_meeting(
        self,
        transcript_text: str,
        existing_metrics: dict[str, Any] | None = None,
    ) -> TranscriptIntelligence:
        """Analyze a meeting transcript for behavioral and strategic patterns."""
        if not transcript_text or len(transcript_text.strip()) < 50:
            return TranscriptIntelligence()

        context = f"TRANSCRIPT:\n{transcript_text[:6000]}"
        if existing_metrics:
            import json
            relevant = {
                k: existing_metrics[k]
                for k in ("delivery_metrics", "power_dynamics", "attention")
                if k in existing_metrics
            }
            if relevant:
                context += f"\n\nEXISTING METRICS:\n{json.dumps(relevant, indent=1, default=str)}"

        try:
            raw = await self._llm.complete_structured(
                context,
                tier=ModelTier.REASONING,
                system=TRANSCRIPT_ANALYSIS_SYSTEM,
                max_tokens=2048,
            )
            return self._parse_meeting_result(raw)
        except Exception:
            logger.warning("Transcript analysis failed", exc_info=True)
            return TranscriptIntelligence()

    async def analyze_person(
        self,
        person_context: str,
    ) -> PersonBehavioralProfile:
        """Analyze accumulated context about a person for behavioral profiling."""
        if not person_context or len(person_context.strip()) < 30:
            return PersonBehavioralProfile()

        try:
            raw = await self._llm.complete_structured(
                person_context[:4000],
                tier=ModelTier.REASONING,
                system=PERSON_ANALYSIS_SYSTEM,
                max_tokens=1024,
            )
            return self._parse_person_result(raw)
        except Exception:
            logger.warning("Person analysis failed", exc_info=True)
            return PersonBehavioralProfile()

    @staticmethod
    def _parse_meeting_result(raw: dict[str, Any]) -> TranscriptIntelligence:
        return TranscriptIntelligence(
            hedging_rate=_float(raw, "hedging_rate", 0.5),
            persuasion_effectiveness=_float(raw, "persuasion_effectiveness", 0.5),
            challenge_response_pattern=raw.get("challenge_response_pattern", "collaborative"),
            patience_decay_detected=raw.get("patience_decay_detected", False),
            tone_consistency=_float(raw, "tone_consistency", 0.5),
            consensus_quality=raw.get("consensus_quality", "genuine"),
            hidden_disagreement_detected=raw.get("hidden_disagreement_detected", False),
            hidden_disagreement_evidence=raw.get("hidden_disagreement_evidence"),
            vagueness_density=_float(raw, "vagueness_density", 0.5),
            accountability_strength=_float(raw, "accountability_strength", 0.5),
            decision_clarity=_float(raw, "decision_clarity", 0.5),
            objection_handling_effectiveness=_float(raw, "objection_handling_effectiveness", 0.5),
            narrative_resonance_score=_float(raw, "narrative_resonance_score", 0.5),
            decision_driving_moments=raw.get("decision_driving_moments", []),
            message_compression_score=_float(raw, "message_compression_score", 0.5),
            emotional_temperature=raw.get("emotional_temperature", "neutral"),
            disagreement_detection_score=_float(raw, "disagreement_detection_score", 0.0),
            trust_preservation_score=_float(raw, "trust_preservation_score", 0.5),
            social_signal_asymmetry=_float(raw, "social_signal_asymmetry", 0.0),
        )

    @staticmethod
    def _parse_person_result(raw: dict[str, Any]) -> PersonBehavioralProfile:
        return PersonBehavioralProfile(
            preferred_message_style=raw.get("preferred_message_style", "action_oriented"),
            decision_driver_profile=raw.get("decision_driver_profile", "pragmatic"),
            influenceability_profile=raw.get("influenceability_profile", "evidence_based"),
            silent_resistance_probability=_float(raw, "silent_resistance_probability", 0.0),
            response_under_pressure=raw.get("response_under_pressure", "calm"),
            best_approach_for_asks=raw.get("best_approach_for_asks", ""),
            topics_that_land_well=raw.get("topics_that_land_well", []),
            topics_that_create_friction=raw.get("topics_that_create_friction", []),
        )


def _float(d: dict, key: str, default: float) -> float:
    val = d.get(key, default)
    try:
        return float(val)
    except (TypeError, ValueError):
        return default
