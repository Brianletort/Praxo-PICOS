from __future__ import annotations

import logging
from typing import Any

from services.api.src.praxo_picos_api.agents.llm_provider import LLMProvider, ModelTier
from services.api.src.praxo_picos_api.models.base import NarrativeResponse

logger = logging.getLogger(__name__)


class NarrativeGenerator:
    """Transforms raw analytics into plain-English prose at three depth levels.

    headline -- one sentence (fast model)
    brief    -- 2-3 sentences with one supporting data point (fast model)
    full     -- paragraph-level coaching / analysis (reasoning model)
    """

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self._llm = llm

    # ── Template-based generation (no LLM needed) ────────────────

    def meeting_narrative(self, meeting_data: dict[str, Any]) -> NarrativeResponse:
        """Build a narrative for a single meeting from its attrs."""
        scorecard = meeting_data.get("scorecard", {})
        coaching = meeting_data.get("coaching_report", {})
        delivery = meeting_data.get("delivery_metrics", {})
        title = meeting_data.get("title", "Meeting")

        overall = scorecard.get("overall_score")
        headline = self._meeting_headline(title, overall, delivery)

        bullets = []
        for item in coaching.get("what_went_well", [])[:2]:
            bullets.append(item)
        for item in coaching.get("what_to_improve", [])[:1]:
            bullets.append(item)
        if not bullets and delivery:
            bullets = self._delivery_bullets(delivery)

        trend = scorecard.get("vs_30d_avg", {}).get("delivery_trend", "stable")
        sentiment = "positive" if overall and overall >= 0.75 else (
            "attention" if overall and overall < 0.5 else "neutral"
        )

        depth = []
        if scorecard:
            depth.append("scorecard")
        if coaching:
            depth.append("coaching")
        if delivery:
            depth.append("delivery")
        if meeting_data.get("body_language"):
            depth.append("body_language")
        if meeting_data.get("attention"):
            depth.append("attention")
        if meeting_data.get("power_dynamics"):
            depth.append("power_dynamics")

        return NarrativeResponse(
            headline=headline,
            bullets=bullets,
            trend=trend,
            sentiment=sentiment,
            available_depth=depth,
        )

    def person_narrative(self, person_data: dict[str, Any]) -> NarrativeResponse:
        """Build a narrative for a person from their attrs."""
        name = person_data.get("name", "This person")
        dynamics = person_data.get("relationship_dynamics", {})
        comm = person_data.get("communication_dynamic", {})

        trend = dynamics.get("trend", "stable")
        headline = self._person_headline(name, trend, dynamics)

        bullets = []
        if comm:
            style_note = self._style_note(name, comm)
            if style_note:
                bullets.append(style_note)
        completion_rate = dynamics.get("commitment_completion_rate")
        if completion_rate is not None:
            pct = int(completion_rate * 100)
            bullets.append(f"Your completion rate with {name}: {pct}%")
        freq = dynamics.get("interaction_frequency")
        if freq:
            bullets.append(f"You interact roughly {freq}")

        sentiment = "attention" if trend == "cooling" else (
            "positive" if trend == "warming" else "neutral"
        )

        depth = []
        if comm:
            depth.append("communication_style")
        if dynamics:
            depth.append("relationship_dynamics")

        return NarrativeResponse(
            headline=headline,
            bullets=bullets,
            trend=trend,
            sentiment=sentiment,
            available_depth=depth,
        )

    def day_narrative(
        self,
        meetings: list[dict[str, Any]],
        energy: dict[str, Any] | None = None,
        people_needing_attention: list[dict[str, Any]] | None = None,
    ) -> NarrativeResponse:
        """Build a daily summary narrative."""
        n = len(meetings)
        if n == 0:
            return NarrativeResponse(
                headline="No meetings today -- a good day for deep work",
                bullets=["Focus on your top priorities"],
                trend="stable",
                sentiment="positive",
            )

        scored = [m for m in meetings if m.get("scorecard", {}).get("overall_score")]
        best = max(scored, key=lambda m: m["scorecard"]["overall_score"]) if scored else None

        headline = f"You had {n} meeting{'s' if n != 1 else ''} today"
        if best:
            score = best["scorecard"]["overall_score"]
            headline += f". Best: {best.get('title', 'meeting')} ({int(score * 100)})"

        bullets = []
        if energy and energy.get("peak_hours"):
            bullets.append(f"Peak focus: {energy['peak_hours']}")
        if people_needing_attention:
            for p in people_needing_attention[:2]:
                bullets.append(f"{p.get('name', '?')} -- {p.get('reason', 'needs attention')}")

        return NarrativeResponse(
            headline=headline,
            bullets=bullets,
            trend="stable",
            sentiment="neutral",
            available_depth=["meetings", "energy", "people"],
        )

    # ── LLM-powered generation (for full coaching reports) ───────

    async def generate_coaching_report(
        self,
        meeting_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a full coaching report using the reasoning model.

        Falls back to template-based output if no LLM is available.
        """
        if self._llm is None:
            return self._template_coaching(meeting_data)

        prompt = self._coaching_prompt(meeting_data)
        return await self._llm.complete_structured(
            prompt,
            tier=ModelTier.REASONING,
            system=(
                "You are a personal meeting coach. Analyze the meeting data and produce "
                "a coaching report with sections: what_went_well (list), what_to_improve (list), "
                "opportunities (list), tips (list personalized to this person's patterns). "
                "Be specific, cite data points, and keep each item to one sentence."
            ),
            max_tokens=2048,
        )

    # ── Private helpers ──────────────────────────────────────────

    @staticmethod
    def _meeting_headline(title: str, score: float | None, delivery: dict[str, Any]) -> str:
        if score is not None:
            quality = "great" if score >= 0.8 else ("solid" if score >= 0.6 else "rough")
            return f"{title} -- a {quality} meeting ({int(score * 100)})"
        pace = delivery.get("pace_wpm")
        if pace:
            return f"{title} -- you spoke at {pace} WPM"
        return title

    @staticmethod
    def _person_headline(name: str, trend: str, dynamics: dict[str, Any]) -> str:
        if trend == "cooling":
            return f"Your relationship with {name} is cooling -- consider reconnecting"
        if trend == "warming":
            return f"Things are going well with {name}"
        last = dynamics.get("last_interaction_days_ago")
        if last and last > 14:
            return f"You haven't connected with {name} in {last} days"
        return f"Stable relationship with {name}"

    @staticmethod
    def _style_note(name: str, comm: dict[str, Any]) -> str | None:
        pace_diff = comm.get("pace_diff_pct")
        if pace_diff and abs(pace_diff) > 10:
            direction = "faster" if pace_diff > 0 else "slower"
            return f"You speak {abs(int(pace_diff))}% {direction} with {name}"
        return None

    @staticmethod
    def _delivery_bullets(delivery: dict[str, Any]) -> list[str]:
        bullets = []
        pace = delivery.get("pace_wpm")
        if pace:
            bullets.append(f"Speaking pace: {pace} WPM")
        filler = delivery.get("filler_rate_per_min")
        if filler is not None:
            bullets.append(f"Filler word rate: {filler:.1f}/min")
        ratio = delivery.get("talk_listen_ratio")
        if ratio is not None:
            bullets.append(f"Talk-to-listen ratio: {int(ratio * 100)}%")
        return bullets

    @staticmethod
    def _template_coaching(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "what_went_well": data.get("coaching_report", {}).get("what_went_well", []),
            "what_to_improve": data.get("coaching_report", {}).get("what_to_improve", []),
            "opportunities": data.get("coaching_report", {}).get("opportunities", []),
            "tips": data.get("coaching_report", {}).get("tips", []),
        }

    @staticmethod
    def _coaching_prompt(data: dict[str, Any]) -> str:
        import json
        relevant = {
            k: data[k] for k in (
                "title", "delivery_metrics", "attention", "body_language",
                "power_dynamics", "scorecard",
            ) if k in data
        }
        return (
            "Analyze this meeting data and generate a coaching report.\n\n"
            f"{json.dumps(relevant, indent=2, default=str)}"
        )
