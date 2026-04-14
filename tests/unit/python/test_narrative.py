"""Tests for the narrative layer (Phase 0D)."""
from __future__ import annotations

import pytest

from services.api.src.praxo_picos_api.narrative import (
    InsightRanker,
    NarrativeGenerator,
    ProgressiveDisclosure,
    RankedInsight,
)
from services.api.src.praxo_picos_api.narrative.progressive import ProgressiveThresholds


class TestNarrativeGenerator:
    def setup_method(self):
        self.gen = NarrativeGenerator()

    def test_meeting_narrative_with_scorecard(self):
        data = {
            "title": "Design Review",
            "scorecard": {"overall_score": 0.85, "vs_30d_avg": {"delivery_trend": "improving"}},
            "coaching_report": {
                "what_went_well": ["Good eye contact", "Clear structure"],
                "what_to_improve": ["Spoke too fast"],
            },
            "delivery_metrics": {"pace_wpm": 145},
        }
        result = self.gen.meeting_narrative(data)
        assert "Design Review" in result.headline
        assert result.trend == "improving"
        assert result.sentiment == "positive"
        assert "scorecard" in result.available_depth
        assert "coaching" in result.available_depth

    def test_meeting_narrative_without_scorecard(self):
        data = {
            "title": "Quick Sync",
            "delivery_metrics": {"pace_wpm": 160, "filler_rate_per_min": 3.2},
        }
        result = self.gen.meeting_narrative(data)
        assert "Quick Sync" in result.headline
        assert result.trend == "stable"
        assert len(result.bullets) > 0

    def test_person_narrative_cooling(self):
        data = {
            "name": "Sarah Chen",
            "relationship_dynamics": {"trend": "cooling"},
            "communication_dynamic": {"pace_diff_pct": 15},
        }
        result = self.gen.person_narrative(data)
        assert "cooling" in result.headline.lower()
        assert result.sentiment == "attention"

    def test_person_narrative_stable(self):
        data = {
            "name": "Bob",
            "relationship_dynamics": {"trend": "stable"},
        }
        result = self.gen.person_narrative(data)
        assert "Bob" in result.headline

    def test_day_narrative_no_meetings(self):
        result = self.gen.day_narrative([])
        assert "no meetings" in result.headline.lower()
        assert result.sentiment == "positive"

    def test_day_narrative_with_meetings(self):
        meetings = [
            {"title": "Standup", "scorecard": {"overall_score": 0.7}},
            {"title": "Design Review", "scorecard": {"overall_score": 0.9}},
        ]
        result = self.gen.day_narrative(meetings)
        assert "2 meetings" in result.headline
        assert "Design Review" in result.headline


class TestInsightRanker:
    def setup_method(self):
        self.ranker = InsightRanker()

    def test_rank_limits_results(self):
        insights = [
            RankedInsight(headline=f"Insight {i}", detail="", category="test", score=0.0)
            for i in range(10)
        ]
        ranked = self.ranker.rank(insights, max_results=3)
        assert len(ranked) <= 3

    def test_actionable_insights_rank_higher(self):
        insights = [
            RankedInsight(headline="Non-actionable", detail="", category="a", score=0.0),
            RankedInsight(
                headline="Actionable", detail="", category="b", score=0.0, actionable=True,
            ),
        ]
        ranked = self.ranker.rank(insights, max_results=2)
        assert ranked[0].headline == "Actionable"

    def test_category_diversity(self):
        insights = [
            RankedInsight(headline=f"Cat A #{i}", detail="", category="same", score=0.0, actionable=True)
            for i in range(5)
        ]
        ranked = self.ranker.rank(insights, max_results=5)
        assert len(ranked) <= 2

    def test_from_meeting_high_filler_rate(self):
        data = {
            "title": "Standup",
            "delivery_metrics": {"filler_rate_per_min": 8.5},
        }
        insights = self.ranker.from_meeting(data)
        assert any("filler" in i.headline.lower() for i in insights)

    def test_from_person_cooling(self):
        data = {
            "name": "Sarah",
            "relationship_dynamics": {"trend": "cooling"},
        }
        insights = self.ranker.from_person(data)
        assert any("cooling" in i.headline.lower() for i in insights)


class TestProgressiveDisclosure:
    def test_first_meeting_unlocks_delivery(self):
        pd = ProgressiveDisclosure()
        result = pd.meeting_insights(1)
        assert "delivery_metrics" in result.available
        assert "coaching_report" not in result.available

    def test_three_meetings_unlocks_coaching(self):
        pd = ProgressiveDisclosure()
        result = pd.meeting_insights(3)
        assert "coaching_report" in result.available

    def test_five_meetings_unlocks_scorecard(self):
        pd = ProgressiveDisclosure()
        result = pd.meeting_insights(5)
        assert "scorecard" in result.available
        assert "trend_comparison" in result.available

    def test_zero_meetings_shows_learning(self):
        pd = ProgressiveDisclosure()
        result = pd.meeting_insights(0)
        assert len(result.learning) > 0
        assert any("first meeting" in lp.message.lower() for lp in result.learning)

    def test_person_style_after_threshold(self):
        pd = ProgressiveDisclosure(ProgressiveThresholds(min_meetings_for_style=3))
        result = pd.person_insights(3, total_days_known=10)
        assert "communication_style" in result.available

    def test_person_style_before_threshold(self):
        pd = ProgressiveDisclosure(ProgressiveThresholds(min_meetings_for_style=3))
        result = pd.person_insights(1, total_days_known=5)
        assert "communication_style" not in result.available
        assert any(lp.insight_type == "communication_style" for lp in result.learning)

    def test_energy_insights_timeline(self):
        pd = ProgressiveDisclosure()
        early = pd.energy_insights(3)
        assert "daily_energy" in early.available
        assert "circadian_map" not in early.available

        later = pd.energy_insights(14)
        assert "circadian_map" in later.available
        assert "peak_hours" in later.available

    def test_global_readiness(self):
        pd = ProgressiveDisclosure()
        result = pd.global_readiness(total_meetings=0, total_days=0, total_people=0)
        assert "meetings" in result
        assert "energy" in result
        assert "people" in result
