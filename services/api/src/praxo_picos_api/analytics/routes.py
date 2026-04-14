"""Analytics API with dual-response pattern: narrative (always) + detail (opt-in).

Simple-mode frontend reads narrative only. Advanced mode reads both.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from services.api.src.praxo_picos_api.db.models import ConsentRecord
from services.api.src.praxo_picos_api.db.object_store import ObjectStore
from services.api.src.praxo_picos_api.db.session import get_session
from services.api.src.praxo_picos_api.models import (
    Meeting,
    ObjectType,
    Person,
)
from services.api.src.praxo_picos_api.narrative import (
    InsightRanker,
    NarrativeGenerator,
    ProgressiveDisclosure,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])
privacy_router = APIRouter(prefix="/api/privacy", tags=["privacy"])

_narrator = NarrativeGenerator()
_ranker = InsightRanker()
_progressive = ProgressiveDisclosure()


def _meeting_list_item(m: Meeting) -> dict[str, Any]:
    """Build a list-view item for a meeting with narrative summary."""
    narrative = _narrator.meeting_narrative(m.attrs | {"title": m.title or "Meeting"})
    score = m.overall_score

    return {
        "id": m.id,
        "title": m.title,
        "start_time": m.start_time.isoformat() if m.start_time else None,
        "end_time": m.end_time.isoformat() if m.end_time else None,
        "duration_minutes": m.duration_minutes,
        "attendee_count": len(m.attendee_ids),
        "has_intelligence": m.has_intelligence,
        "intelligence_score": score,
        "score_dot": _score_dot(score),
        "narrative": narrative.model_dump(),
    }


def _score_dot(score: float | None) -> str:
    if score is None:
        return "none"
    if score >= 0.75:
        return "green"
    if score >= 0.5:
        return "yellow"
    return "red"


@router.get("/meetings")
async def list_meetings(
    range_weeks: int = Query(default=4, ge=1, le=52),
    detail: str = Query(default="simple", pattern="^(simple|full)$"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """List meetings with intelligence indicators.

    Simple mode: each meeting has headline, score_dot, trend_arrow.
    Full mode: adds complete scorecard and all sub-scores.
    """
    store = ObjectStore(session)
    since = datetime.now(UTC) - timedelta(weeks=range_weeks)
    objects = await store.query(object_type=ObjectType.MEETING, since=since, limit=200)
    meetings = [o for o in objects if isinstance(o, Meeting)]

    items = [_meeting_list_item(m) for m in meetings]

    if detail == "full":
        for item, m in zip(items, meetings, strict=True):
            item["detail"] = m.attrs

    total = len(meetings)
    availability = _progressive.meeting_insights(total)

    return {
        "meetings": items,
        "total": total,
        "availability": {
            "available": availability.available,
            "learning": [
                {"type": lp.insight_type, "message": lp.message, "progress": lp.progress_pct}
                for lp in availability.learning
            ],
        },
    }


@router.get("/meetings/{meeting_id}")
async def get_meeting(
    meeting_id: str,
    detail: str = Query(default="simple", pattern="^(simple|full)$"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get full meeting intelligence.

    Simple: narrative coaching summary, key numbers, per-person one-liners.
    Full: complete intelligence payload.
    """
    store = ObjectStore(session)
    obj = await store.get(meeting_id)

    if obj is None or not isinstance(obj, Meeting):
        return {"error": "Meeting not found"}

    narrative = _narrator.meeting_narrative(obj.attrs | {"title": obj.title or "Meeting"})
    insights = _ranker.from_meeting(obj.attrs | {"id": obj.id, "title": obj.title})
    ranked = _ranker.rank(insights, max_results=3)

    result: dict[str, Any] = {
        "id": obj.id,
        "title": obj.title,
        "start_time": obj.start_time.isoformat() if obj.start_time else None,
        "end_time": obj.end_time.isoformat() if obj.end_time else None,
        "duration_minutes": obj.duration_minutes,
        "attendee_ids": obj.attendee_ids,
        "summary": obj.summary,
        "has_intelligence": obj.has_intelligence,
        "intelligence_score": obj.overall_score,
        "narrative": narrative.model_dump(),
        "top_insights": [
            {"headline": i.headline, "detail": i.detail, "actionable": i.actionable}
            for i in ranked
        ],
    }

    if detail == "full":
        result["intelligence"] = obj.attrs

    return result


@router.get("/person/{person_id}")
async def get_person(
    person_id: str,
    detail: str = Query(default="simple", pattern="^(simple|full)$"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get person intelligence.

    Simple: relationship summary, trend, coaching tip.
    Full: communication dynamics, decay curves, topic analysis.
    """
    store = ObjectStore(session)
    obj = await store.get(person_id)

    if obj is None or not isinstance(obj, Person):
        return {"error": "Person not found"}

    narrative = _narrator.person_narrative(
        obj.attrs | {"name": obj.name, "id": obj.id}
    )
    insights = _ranker.from_person(obj.attrs | {"name": obj.name, "id": obj.id})
    ranked = _ranker.rank(insights, max_results=2)

    result: dict[str, Any] = {
        "id": obj.id,
        "name": obj.name,
        "email": obj.email,
        "organization": obj.organization,
        "role": obj.role,
        "importance_level": obj.importance_level,
        "narrative": narrative.model_dump(),
        "top_insights": [
            {"headline": i.headline, "detail": i.detail, "actionable": i.actionable}
            for i in ranked
        ],
    }

    if detail == "full":
        result["intelligence"] = obj.attrs
        rels = await store.get_relationships(person_id)
        result["relationships"] = [
            {
                "id": r.id,
                "target_id": r.target_id if r.source_id == person_id else r.source_id,
                "type": r.relationship_type.value,
                "attrs": r.attrs,
            }
            for r in rels
        ]

    return result


@router.get("/day")
async def daily_summary(
    date: str | None = Query(default=None),
    detail: str = Query(default="simple", pattern="^(simple|full)$"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Daily intelligence summary -- the 'Your Day' card.

    Simple: top 5 ranked insights, energy headline, people needing attention.
    Full: complete per-meeting breakdown, energy timeline, all relationship changes.
    """
    store = ObjectStore(session)

    if date:
        try:
            day_start = datetime.fromisoformat(date).replace(
                hour=0, minute=0, second=0, tzinfo=UTC
            )
        except ValueError:
            day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0)
    else:
        day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0)

    day_end = day_start + timedelta(days=1)

    objects = await store.query(
        object_type=ObjectType.MEETING, since=day_start, until=day_end, limit=50
    )
    meetings = [o for o in objects if isinstance(o, Meeting)]
    meeting_dicts = [m.attrs | {"title": m.title, "id": m.id} for m in meetings]

    all_insights = []
    for md in meeting_dicts:
        all_insights.extend(_ranker.from_meeting(md))

    people_objects = await store.query(object_type=ObjectType.PERSON, limit=50)
    people_needing_attention = []
    for p in people_objects:
        if isinstance(p, Person):
            p_insights = _ranker.from_person(p.attrs | {"name": p.name, "id": p.id})
            for pi in p_insights:
                if pi.actionable:
                    people_needing_attention.append({"name": p.name, "reason": pi.headline})
            all_insights.extend(p_insights)

    ranked = _ranker.rank(all_insights, max_results=5)
    narrative = _narrator.day_narrative(
        meeting_dicts,
        people_needing_attention=people_needing_attention[:3],
    )

    result: dict[str, Any] = {
        "date": day_start.date().isoformat(),
        "meeting_count": len(meetings),
        "narrative": narrative.model_dump(),
        "top_insights": [
            {"headline": i.headline, "detail": i.detail, "actionable": i.actionable}
            for i in ranked
        ],
        "people_needing_attention": people_needing_attention[:3],
    }

    if detail == "full":
        result["meetings"] = [_meeting_list_item(m) for m in meetings]

    return result


@router.get("/readiness")
async def intelligence_readiness(
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """What intelligence features are available given accumulated data.

    Used by the frontend to show/hide sections and display learning placeholders.
    """
    store = ObjectStore(session)
    total_meetings = await store.count(object_type=ObjectType.MEETING)
    total_people = await store.count(object_type=ObjectType.PERSON)
    total_insights = await store.count(object_type=ObjectType.INSIGHT)

    readiness = _progressive.global_readiness(
        total_meetings=total_meetings,
        total_days=0,
        total_people=total_people,
    )

    return {
        "counts": {
            "meetings": total_meetings,
            "people": total_people,
            "insights": total_insights,
        },
        "readiness": {
            domain: {
                "available": avail.available,
                "learning": [
                    {"type": lp.insight_type, "message": lp.message, "progress": lp.progress_pct}
                    for lp in avail.learning
                ],
            }
            for domain, avail in readiness.items()
        },
    }


# ── Consent / Privacy API ──────────────────────────────────────────

CONSENT_DOMAINS = [
    {"domain": "meetings", "label": "Analyze my meetings", "description": "Track speaking patterns, attention, and coaching tips", "default": "opted_in"},
    {"domain": "screen", "label": "Read my screen", "description": "Understand app usage and deep focus patterns", "default": "opted_in"},
    {"domain": "screen_vision", "label": "Body language analysis", "description": "Analyze video frames for posture and expression", "default": "opted_in"},
    {"domain": "health", "label": "Track my health", "description": "Connect Apple Health for sleep and energy data", "default": "not_asked"},
    {"domain": "location", "label": "Track my location", "description": "Know where you work best", "default": "not_asked"},
    {"domain": "finance", "label": "Import financial data", "description": "Track subscriptions and life admin", "default": "not_asked"},
]


@privacy_router.get("/consent")
async def get_consent(
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """List all domain consent states with labels."""
    result = await session.execute(select(ConsentRecord))
    stored = {r.domain: r.status for r in result.scalars()}

    domains = []
    for d in CONSENT_DOMAINS:
        domains.append({
            "domain": d["domain"],
            "label": d["label"],
            "description": d["description"],
            "status": stored.get(d["domain"], d["default"]),
        })

    return {"domains": domains}


@privacy_router.patch("/consent")
async def update_consent(
    updates: dict[str, str],
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Toggle consent for one or more domains. Body: {"domain_name": "opted_in"|"opted_out"}"""
    valid_domains = {d["domain"] for d in CONSENT_DOMAINS}
    valid_statuses = {"opted_in", "opted_out", "not_asked"}

    updated = []
    for domain, status in updates.items():
        if domain not in valid_domains or status not in valid_statuses:
            continue
        existing = await session.get(ConsentRecord, domain)
        if existing:
            existing.status = status
        else:
            session.add(ConsentRecord(domain=domain, status=status))
        updated.append(domain)

    await session.commit()
    return {"updated": updated}


async def _check_consent(session: AsyncSession, domain: str) -> bool:
    """Check if a domain is consented. Defaults to True for meetings/screen."""
    record = await session.get(ConsentRecord, domain)
    if record is None:
        return domain in ("meetings", "screen", "screen_vision")
    return record.status == "opted_in"


def _filter_intelligence_by_consent(
    intelligence: dict[str, Any],
    consented_domains: set[str],
) -> dict[str, Any]:
    """Remove intelligence sections the user hasn't consented to."""
    filtered = dict(intelligence)
    if "screen_vision" not in consented_domains:
        filtered.pop("body_language", None)
    if "screen" not in consented_domains:
        filtered.pop("attention", None)
        filtered.pop("visual_signals", None)
        filtered.pop("cognitive_energy", None)
    return filtered
