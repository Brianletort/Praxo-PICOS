"""Stage 3b: Update per-person communication style and relationship dynamics.

Runs after meeting intelligence to update Person.attrs with accumulated
style profiles and relationship trends.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from services.api.src.praxo_picos_api.agents.llm_provider import LLMProvider
from services.api.src.praxo_picos_api.db.object_store import ObjectStore
from services.api.src.praxo_picos_api.models import Meeting, ObjectType, Person

from ..analytics.communication_style import CommunicationStyleDNA
from ..analytics.meeting_delivery import DeliveryMetrics
from ..analytics.relationship_dynamics import (
    InteractionRecord,
    RelationshipDynamicsTracker,
)
from ..intelligence.relationship_intelligence import RelationshipIntelligenceScorer
from ..intelligence.transcript_analysis import PersonBehavioralProfile, TranscriptAnalyzer

logger = logging.getLogger(__name__)


class PersonIntelligenceRunner:
    """Updates communication style and relationship dynamics for all people."""

    def __init__(self, store: ObjectStore, llm: LLMProvider | None = None) -> None:
        self._store = store
        self._llm = llm

    async def update_all(self) -> int:
        """Recompute person intelligence from all meetings. Returns people updated."""
        meetings = await self._store.query(object_type=ObjectType.MEETING, limit=500)
        people = await self._store.query(object_type=ObjectType.PERSON, limit=500)

        meeting_list = [m for m in meetings if isinstance(m, Meeting)]
        person_list = [p for p in people if isinstance(p, Person)]

        if not meeting_list or not person_list:
            return 0

        person_map = {p.id: p for p in person_list}
        names = {p.id: p.display_name for p in person_list}

        style_dna = CommunicationStyleDNA(min_meetings=3)
        rel_tracker = RelationshipDynamicsTracker()

        for m in meeting_list:
            delivery_raw = m.attrs.get("delivery_metrics")
            if delivery_raw and isinstance(delivery_raw, dict):
                dm = DeliveryMetrics(
                    pace_wpm=delivery_raw.get("pace_wpm", 0),
                    filler_rate_per_min=delivery_raw.get("filler_rate_per_min", 0),
                    talk_listen_ratio=delivery_raw.get("talk_listen_ratio", 0),
                    question_rate_per_min=delivery_raw.get("question_rate_per_min", 0),
                    monologue_max_s=delivery_raw.get("monologue_max_s", 0),
                    vocabulary_complexity=delivery_raw.get("vocabulary_complexity", 0),
                )
                style_dna.add_meeting(dm, m.attendee_ids, names)

            for pid in m.attendee_ids:
                rel_tracker.add_interaction(InteractionRecord(
                    person_id=pid,
                    timestamp=m.start_time,
                    interaction_type="meeting",
                    is_one_on_one=len(m.attendee_ids) == 1,
                    initiated_by_you=m.source_id.startswith("cal_") if m.source_id else False,
                    attendee_count=len(m.attendee_ids),
                ))

        updated = 0
        now = datetime.now(UTC)
        for person in person_list:
            changed = False

            shift = style_dna.compute_style_shift(person.id, person.display_name)
            if shift:
                person.attrs["communication_dynamic"] = shift.to_dict()
                changed = True

            profile = style_dna.get_profile(person.id, person.display_name)
            if profile:
                person.attrs["style_profile"] = profile.to_dict()
                changed = True

            rel_metrics = rel_tracker.get_metrics(person.id, person.display_name, now)
            if rel_metrics.interaction_count > 0:
                person.attrs["relationship_dynamics"] = rel_metrics.to_dict()
                changed = True

            if changed:
                rel_scorer = RelationshipIntelligenceScorer()
                rel_intel = rel_scorer.score(person.attrs)
                person.attrs["relationship_intelligence"] = rel_intel.to_dict()

                if self._llm and person.attrs.get("relationship_dynamics", {}).get("interaction_count", 0) >= 5:
                    try:
                        import json
                        context = json.dumps({
                            "name": person.display_name,
                            "style_profile": person.attrs.get("style_profile", {}),
                            "communication_dynamic": person.attrs.get("communication_dynamic", {}),
                            "relationship_dynamics": person.attrs.get("relationship_dynamics", {}),
                        }, indent=1, default=str)
                        analyzer = TranscriptAnalyzer(self._llm)
                        behavioral = await analyzer.analyze_person(context)
                        person.attrs["behavioral_profile"] = behavioral.to_dict()
                    except Exception:
                        logger.warning("Person behavioral profiling failed for %s", person.id)

                await self._store.put(person)
                updated += 1

        return updated
