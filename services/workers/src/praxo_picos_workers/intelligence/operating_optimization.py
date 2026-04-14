"""Tier 1: Personal Operating Optimization.

Derives strategic operating scores from existing metrics:
  cognitive_load_score, context_switch_tax, decision_fatigue_index,
  deep_work_probability, recovery_need_score, calendar_fragmentation_penalty.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OperatingOptimizationProfile:
    cognitive_load_score: float = 0.5
    context_switch_tax: float = 0.0
    decision_fatigue_index: float = 0.0
    deep_work_probability: float = 0.5
    peak_performance_window: str = ""
    recovery_need_score: float = 0.0
    stress_carryover_risk: float = 0.0
    calendar_fragmentation_penalty: float = 0.0
    energy_adjusted_priority_score: float = 0.5
    attention_fragmentation_index: float = 0.0
    overload_probability: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cognitive_load_score": round(self.cognitive_load_score, 3),
            "context_switch_tax": round(self.context_switch_tax, 3),
            "decision_fatigue_index": round(self.decision_fatigue_index, 3),
            "deep_work_probability": round(self.deep_work_probability, 3),
            "peak_performance_window": self.peak_performance_window,
            "recovery_need_score": round(self.recovery_need_score, 3),
            "stress_carryover_risk": round(self.stress_carryover_risk, 3),
            "calendar_fragmentation_penalty": round(self.calendar_fragmentation_penalty, 3),
            "energy_adjusted_priority_score": round(self.energy_adjusted_priority_score, 3),
            "attention_fragmentation_index": round(self.attention_fragmentation_index, 3),
            "overload_probability": round(self.overload_probability, 3),
        }


class OperatingOptimizationScorer:
    """Computes operating optimization scores from energy + attention data."""

    def score(self, energy_attrs: dict[str, Any]) -> OperatingOptimizationProfile:
        energy = energy_attrs.get("cognitive_energy", {})
        deep_work = energy_attrs.get("deep_work_blocks", [])
        deep_total = energy_attrs.get("deep_work_total_min", 0)

        hourly = energy.get("hourly", [])
        peak = energy.get("peak_hours", "")
        avg_energy = energy.get("avg_energy", 0.5)
        meeting_count = energy.get("meeting_count", 0)
        consec = energy.get("consecutive_meeting_max", 0)

        total_switches = sum(h.get("switch_rate", 0) * h.get("frame_count", 0) for h in hourly)
        total_frames = sum(h.get("frame_count", 0) for h in hourly)

        cog_load = 1.0 - avg_energy
        switch_tax = (total_switches / max(1, total_frames)) if total_frames else 0
        fatigue = self._decision_fatigue(meeting_count, consec, avg_energy)
        dwp = self._deep_work_probability(deep_total, meeting_count)
        recovery = self._recovery_need(consec, avg_energy)
        stress = self._stress_carryover(consec, avg_energy, meeting_count)
        frag = self._calendar_fragmentation(meeting_count, hourly)
        eap = avg_energy * 0.6 + (1.0 - fatigue) * 0.4
        attn_frag = switch_tax
        overload = self._overload_probability(meeting_count, consec, avg_energy)

        return OperatingOptimizationProfile(
            cognitive_load_score=max(0.0, min(1.0, cog_load)),
            context_switch_tax=max(0.0, min(1.0, switch_tax)),
            decision_fatigue_index=fatigue,
            deep_work_probability=dwp,
            peak_performance_window=peak,
            recovery_need_score=recovery,
            stress_carryover_risk=stress,
            calendar_fragmentation_penalty=frag,
            energy_adjusted_priority_score=max(0.0, min(1.0, eap)),
            attention_fragmentation_index=max(0.0, min(1.0, attn_frag)),
            overload_probability=overload,
        )

    def _decision_fatigue(self, meetings: int, consec: int, energy: float) -> float:
        fatigue = 0.0
        fatigue += min(0.4, meetings * 0.06)
        fatigue += min(0.3, consec * 0.1)
        fatigue += max(0.0, (0.5 - energy) * 0.6)
        return max(0.0, min(1.0, fatigue))

    def _deep_work_probability(self, deep_total_min: float, meetings: int) -> float:
        if meetings >= 6:
            return 0.1
        if deep_total_min > 120:
            return 0.9
        if deep_total_min > 60:
            return 0.7
        if deep_total_min > 30:
            return 0.5
        return 0.3

    def _recovery_need(self, consec: int, energy: float) -> float:
        need = 0.0
        need += min(0.5, consec * 0.15)
        need += max(0.0, (0.5 - energy) * 0.5)
        return max(0.0, min(1.0, need))

    def _stress_carryover(self, consec: int, energy: float, meetings: int) -> float:
        risk = 0.0
        if consec >= 3:
            risk += 0.3
        if energy < 0.4:
            risk += 0.3
        if meetings >= 5:
            risk += 0.2
        return max(0.0, min(1.0, risk))

    def _calendar_fragmentation(self, meetings: int, hourly: list) -> float:
        if not hourly or meetings == 0:
            return 0.0
        active_hours = len([h for h in hourly if h.get("frame_count", 0) > 0])
        if active_hours == 0:
            return 0.0
        return min(1.0, meetings / active_hours)

    def _overload_probability(self, meetings: int, consec: int, energy: float) -> float:
        prob = 0.0
        if meetings >= 6:
            prob += 0.35
        elif meetings >= 4:
            prob += 0.15
        if consec >= 3:
            prob += 0.25
        if energy < 0.35:
            prob += 0.25
        return max(0.0, min(1.0, prob))
