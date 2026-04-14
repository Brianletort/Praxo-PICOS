"""Stage 2a: LLM-based enrichment of promoted MemoryObjects.

Extracts entities, topics, commitments, action items, and sentiment
per source type. Uses the lightweight model for speed.
"""
from __future__ import annotations

import logging
from typing import Any

from services.api.src.praxo_picos_api.agents.llm_provider import LLMProvider, ModelTier
from services.api.src.praxo_picos_api.models import MemoryObject, ObjectType

logger = logging.getLogger(__name__)

_EMAIL_SYSTEM = (
    "Extract structured metadata from this email. Return JSON with: "
    "topics (list of 1-3 word topics), sentiment (positive/neutral/negative), "
    "urgency (low/medium/high), asks (list of requests made), "
    "commitments (list of promises), people_mentioned (list of names). "
    "Be concise."
)

_CALENDAR_SYSTEM = (
    "Extract structured metadata from this calendar event. Return JSON with: "
    "meeting_type (one_on_one/team/all_hands/external/workshop/other), "
    "topics (list of 1-3 word agenda topics), "
    "prep_materials (list of documents/links mentioned). Be concise."
)

_DOCUMENT_SYSTEM = (
    "Extract structured metadata from this document. Return JSON with: "
    "topics (list of 1-5 key topics), entities (list of people/orgs/projects mentioned), "
    "document_type (memo/report/notes/spec/plan/other), "
    "key_claims (list of 1-3 main assertions or conclusions). Be concise."
)

_SCREEN_SYSTEM = (
    "Classify this screen activity based on OCR text. Return JSON with: "
    "activity_type (coding/browsing/meeting/writing/communication/design/admin/other), "
    "topics (list of 1-2 word topics if identifiable). Be concise."
)


class LLMEnricher:
    """Sends MemoryObjects through LLMs to extract structured metadata."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def enrich(self, obj: MemoryObject) -> dict[str, Any] | None:
        """Enrich a single MemoryObject. Returns attrs to merge, or None if skipped."""
        text = self._build_text(obj)
        if not text or len(text.strip()) < 20:
            return None

        system = self._system_for_type(obj.object_type)
        if not system:
            return None

        try:
            result = await self._llm.complete_structured(
                text[:3000],
                tier=ModelTier.LIGHTWEIGHT,
                system=system,
                max_tokens=512,
            )
            return {"llm_enrichment": result}
        except Exception:
            logger.warning("LLM enrichment failed for %s", obj.id, exc_info=True)
            return None

    @staticmethod
    def _build_text(obj: MemoryObject) -> str:
        parts = []
        if obj.title:
            parts.append(f"Title: {obj.title}")
        if obj.body:
            parts.append(obj.body[:2500])
        meta = obj.attrs
        if meta.get("app_name"):
            parts.append(f"App: {meta['app_name']}")
        if meta.get("window_name"):
            parts.append(f"Window: {meta['window_name']}")
        return "\n".join(parts)

    @staticmethod
    def _system_for_type(obj_type: ObjectType) -> str | None:
        mapping = {
            ObjectType.EMAIL: _EMAIL_SYSTEM,
            ObjectType.CALENDAR_EVENT: _CALENDAR_SYSTEM,
            ObjectType.DOCUMENT: _DOCUMENT_SYSTEM,
            ObjectType.VAULT_NOTE: _DOCUMENT_SYSTEM,
            ObjectType.SCREEN_CAPTURE: _SCREEN_SYSTEM,
        }
        return mapping.get(obj_type)
