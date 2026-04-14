"""Tier 3: Context Assembly -- pre-briefs, talking points, follow-up generation.

Produces strategic prep artifacts for meetings, people, and decisions.
Uses LLM for synthesis, grounded in accumulated intelligence data.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from services.api.src.praxo_picos_api.agents.llm_provider import LLMProvider, ModelTier

logger = logging.getLogger(__name__)

PRE_BRIEF_SYSTEM = """\
You are a strategic executive briefing assistant. Generate a concise pre-meeting brief. Return JSON:
  "summary": string (2-3 sentence overview of what matters in this meeting),
  "stakeholder_map": list of {"name": string, "role": string, "predicted_stance": string, "approach": string},
  "key_risks": list of strings (what could go wrong),
  "suggested_framing": string (how to frame the discussion for best outcome),
  "objection_forecast": list of {"objection": string, "suggested_response": string},
  "open_threads": list of strings (unresolved items from prior interactions),
  "talking_points": list of strings (3-5 key points to make),
  "follow_up_needed_after": list of strings (people/actions to follow up on)
Be specific and actionable."""

FOLLOW_UP_SYSTEM = """\
Generate personalized follow-up messages for each attendee after this meeting. Return JSON:
  "follow_ups": list of {
    "person_name": string,
    "tone": "executive"|"collaborative"|"accountability"|"supportive",
    "subject_line": string,
    "body": string (2-4 sentences, tailored to this person's style and the meeting outcome)
  }
Tailor each message to the recipient's communication style and what was discussed."""


@dataclass
class PreBriefPacket:
    summary: str = ""
    stakeholder_map: list[dict[str, str]] = field(default_factory=list)
    key_risks: list[str] = field(default_factory=list)
    suggested_framing: str = ""
    objection_forecast: list[dict[str, str]] = field(default_factory=list)
    open_threads: list[str] = field(default_factory=list)
    talking_points: list[str] = field(default_factory=list)
    follow_up_needed_after: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "stakeholder_map": self.stakeholder_map,
            "key_risks": self.key_risks,
            "suggested_framing": self.suggested_framing,
            "objection_forecast": self.objection_forecast,
            "open_threads": self.open_threads,
            "talking_points": self.talking_points,
            "follow_up_needed_after": self.follow_up_needed_after,
        }


@dataclass
class FollowUpPlan:
    follow_ups: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"follow_ups": self.follow_ups}


class ContextAssembler:
    """Generates strategic context artifacts using LLM synthesis."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def generate_pre_brief(
        self,
        meeting_context: dict[str, Any],
        attendee_profiles: list[dict[str, Any]],
        prior_interactions: list[dict[str, Any]] | None = None,
    ) -> PreBriefPacket:
        """Generate a pre-meeting briefing packet."""
        context_parts = [
            f"MEETING: {json.dumps(meeting_context, indent=1, default=str)}",
        ]
        if attendee_profiles:
            context_parts.append(
                f"ATTENDEES: {json.dumps(attendee_profiles[:10], indent=1, default=str)}"
            )
        if prior_interactions:
            context_parts.append(
                f"PRIOR INTERACTIONS: {json.dumps(prior_interactions[:5], indent=1, default=str)}"
            )

        prompt = "\n\n".join(context_parts)

        try:
            raw = await self._llm.complete_structured(
                prompt[:6000],
                tier=ModelTier.REASONING,
                system=PRE_BRIEF_SYSTEM,
                max_tokens=2048,
            )
            return PreBriefPacket(
                summary=raw.get("summary", ""),
                stakeholder_map=raw.get("stakeholder_map", []),
                key_risks=raw.get("key_risks", []),
                suggested_framing=raw.get("suggested_framing", ""),
                objection_forecast=raw.get("objection_forecast", []),
                open_threads=raw.get("open_threads", []),
                talking_points=raw.get("talking_points", []),
                follow_up_needed_after=raw.get("follow_up_needed_after", []),
            )
        except Exception:
            logger.warning("Pre-brief generation failed", exc_info=True)
            return PreBriefPacket()

    async def generate_follow_ups(
        self,
        meeting_summary: str,
        attendee_profiles: list[dict[str, Any]],
        decisions: list[str] | None = None,
        action_items: list[str] | None = None,
    ) -> FollowUpPlan:
        """Generate personalized follow-up messages per attendee."""
        context = {
            "meeting_summary": meeting_summary,
            "attendees": attendee_profiles[:10],
            "decisions": decisions or [],
            "action_items": action_items or [],
        }

        try:
            raw = await self._llm.complete_structured(
                json.dumps(context, indent=1, default=str)[:5000],
                tier=ModelTier.REASONING,
                system=FOLLOW_UP_SYSTEM,
                max_tokens=2048,
            )
            return FollowUpPlan(follow_ups=raw.get("follow_ups", []))
        except Exception:
            logger.warning("Follow-up generation failed", exc_info=True)
            return FollowUpPlan()

    async def generate_context_delta(
        self,
        person_name: str,
        person_attrs: dict[str, Any],
        last_interaction_summary: str = "",
    ) -> str:
        """Generate a context delta summary since last interaction with a person."""
        prompt = (
            f"Person: {person_name}\n"
            f"Last interaction: {last_interaction_summary}\n"
            f"Current data: {json.dumps(person_attrs, indent=1, default=str)[:3000]}\n\n"
            "Write a 2-3 sentence summary of what has changed since the last "
            "interaction and what the user should know before reconnecting."
        )

        try:
            return await self._llm.complete_text(
                prompt,
                tier=ModelTier.LIGHTWEIGHT,
                max_tokens=256,
            )
        except Exception:
            return ""
