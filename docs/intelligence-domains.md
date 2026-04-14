# Intelligence Domains

Praxo-PICOS implements ten intelligence domains that transform raw multimodal signals into actionable executive intelligence. Each domain builds on the extraction pipeline (mail, calendar, screen capture, documents, vault) and the enrichment pipeline (LLM enrichment, person resolution, meeting assembly, deep screenpipe analysis).

## Architecture

```
Raw Signals → Extraction → Promotion → LLM Enrichment → Meeting Assembly
                                                              ↓
                                          Intelligence Analysis (10 Domains)
                                                              ↓
                                              Context Assembly + Prediction
```

The pipeline runs automatically every 15 minutes. No user intervention required.

---

## Domain 1: Executive Performance Intelligence

**Module:** `intelligence/executive_performance.py`

Scores your presence, clarity, and delivery in meetings. Uses delivery metrics (pace, filler rate, talk/listen ratio) and body language analysis (eye contact, posture, energy trajectory) to produce a composite executive presence score.

**Derived fields:**
- `executive_presence_score` — composite of delivery, clarity, confidence (0–1)
- `clarity_score` — vocabulary complexity, monologue length, question rate
- `brevity_efficiency_score` — signal-to-noise in speaking time
- `confidence_stability_score` — filler rate, pause quality, energy stability
- `filler_word_density` — filler words per minute
- `talk_to_listen_ratio` — speaking vs silence time
- `audience_engagement_curve` — per-frame engagement time-series
- `confidence_leakage_markers` — detected indicators (slouched posture, low eye contact, high filler rate, energy decline)

**Source data:** `DeliveryAnalyzer`, `VisionAnalyzer`, `FrameAnalyzer`

---

## Domain 2: Relationship Intelligence

**Module:** `intelligence/relationship_intelligence.py`

Tracks how every stakeholder relationship evolves over time. Combines interaction frequency, communication style shifts, and behavioral profiling to surface trust trends, friction, and sponsorship potential.

**Derived fields:**
- `stakeholder_alignment_score` — current alignment estimate (0–1)
- `trust_trend` — "strengthening", "stable", "weakening", "at_risk"
- `response_reliability_score` — commitment completion rate
- `follow_through_probability` — likelihood commitments are met
- `friction_index` — resistance patterns from pace/style differences and cooling trends
- `relationship_decay_velocity` — how fast the relationship weakens without contact
- `sponsorship_potential` — likelihood of active support
- `political_sensitivity` — communication style mismatches that signal care needed
- `influence_dependency` — how much you drive the relationship vs reciprocal

**Source data:** `RelationshipDynamicsTracker`, `CommunicationStyleDNA`, `PersonResolver`

---

## Domain 3: Meeting Intelligence Beyond Summaries

**Module:** `intelligence/meeting_intelligence_scores.py`

Goes beyond "discussed X, action Y, owner Z" to surface hidden dynamics: real vs surface consensus, who dominated, who disengaged, whether the meeting was worth having.

**Derived fields:**
- `consensus_confidence` — real agreement vs surface agreement (0–1)
- `decision_ambiguity_score` — clarity of decisions made
- `commitment_strength_score` — firmness of commitments (notes, follow-up, questions)
- `meeting_ROI_score` — was this meeting worth having
- `room_energy_curve` — engagement trajectory over time
- `speaking_equity_score` — 1 minus Gini coefficient of talk time
- `interruption_asymmetry` — who interrupts whom
- `meeting_fatigue_risk` — app switches, low focus, rising filler rate
- `unresolved_tension_index` — interruption density per speaker
- `alignment_decay_risk` — ghost speakers and low focus predict post-meeting erosion

**Source data:** `PowerDynamicsAnalyzer`, `AttentionTracker`, `DeliveryAnalyzer`, `ScorecardBuilder`

---

## Domain 4: Personal Operating Optimization

**Module:** `intelligence/operating_optimization.py`

Learns when you do your best thinking, when to avoid hard decisions, which meeting patterns drain you, and what context-switching costs.

**Derived fields:**
- `cognitive_load_score` — current mental load estimate (0–1)
- `context_switch_tax` — switching rate per frame
- `decision_fatigue_index` — accumulated from meetings, consecutive blocks, low energy
- `deep_work_probability` — likelihood of achieving focus in a time block
- `peak_performance_window` — best hours for hard thinking
- `recovery_need_score` — when rest is needed
- `stress_carryover_risk` — yesterday's stress affecting today
- `calendar_fragmentation_penalty` — how broken up the schedule is
- `energy_adjusted_priority_score` — what to work on given current state
- `attention_fragmentation_index` — context-switch density
- `overload_probability` — likelihood of burnout given today's load

**Source data:** `CognitiveEnergyTracker`, `AttentionTracker`, `EnergyIntelligenceRunner`

---

## Domain 5: Behavioral Coaching

**Module:** `intelligence/transcript_analysis.py` (meeting analysis path)

Analyzes your communication patterns over time to provide coaching. LLM-powered semantic analysis detects hedging, persuasion effectiveness, challenge-response patterns, and patience decay.

**Derived fields:**
- `hedging_rate` — frequency of softening language ("maybe", "I think", "sort of")
- `persuasion_effectiveness` — how well key points land based on engagement
- `challenge_response_pattern` — "defensive", "curious", "dismissive", "collaborative", "avoidant"
- `patience_decay_detected` — did patience drop late in meeting
- `tone_consistency` — delivery matching intent throughout
- `objection_handling_effectiveness` — response quality when challenged
- `narrative_resonance_score` — did the main story/framing land
- `message_compression_score` — how efficiently key points communicated

**Source data:** `TranscriptAnalyzer` (LLM Tier: REASONING), `DeliveryAnalyzer`

---

## Domain 6: Predictive Stakeholder Strategy

**Module:** `intelligence/predictive_engine.py` (stakeholder prediction path)

Predicts stakeholder behavior from accumulated historical patterns. Combines relationship intelligence, behavioral profiles, and interaction history to forecast approval, resistance, and optimal approach.

**Derived fields:**
- `approval_likelihood` — will they support this proposal (0–1)
- `escalation_risk` — will this escalate (0–1)
- `socialization_required_score` — how much pre-work is needed (0–1)
- `objection_probability_by_theme` — what pushback to expect per topic
- `ideal_messenger_score` — who should deliver the message
- `timing_advantage_score` — when to make the ask
- `meeting_readiness_score` — is the group ready for a decision

**Source data:** `RelationshipIntelligenceScorer`, `PersonBehavioralProfile`, `RelationshipDynamicsTracker`

---

## Domain 7: Decision Intelligence

**Module:** `intelligence/predictive_engine.py` (decision assessment path)

Evaluates decision quality from transcript and meeting intelligence. Detects bias, assumption density, hidden disagreement, and predicts reversal risk.

**Derived fields:**
- `decision_quality_score` — composite quality rating (0–1)
- `assumption_density` — how many unstated assumptions
- `evidence_strength_score` — quality of supporting data
- `option_diversity_score` — were alternatives considered
- `bias_markers` — "dominated_by_few_voices", "hidden_disagreement_present", "decision_under_fatigue"
- `decision_reversal_probability` — likelihood of reversal (0–1)
- `outcome_attribution_confidence` — can we trace results to the decision
- `regret_risk_estimate` — likely regret score

**Source data:** `TranscriptAnalyzer`, `MeetingIntelligenceScorer`

---

## Domain 8: Real-Time Context Assembly

**Module:** `intelligence/context_assembly.py`

Produces strategic prep artifacts for meetings, people, and decisions. Generates pre-brief packets with stakeholder maps, objection forecasts, and suggested framing. Generates personalized follow-up messages tailored per recipient.

**Artifacts:**
- **Pre-Brief Packet** — summary, stakeholder map, key risks, suggested framing, objection forecast, open threads, talking points, follow-up plan
- **Follow-Up Plan** — custom message per attendee with appropriate tone (executive, collaborative, accountability, supportive)
- **Context Delta** — what changed since last interaction with a person

**Source data:** LLM synthesis (Tier: REASONING) grounded in accumulated intelligence data

---

## Domain 9: Behavioral Profiling (Person)

**Module:** `intelligence/transcript_analysis.py` (person analysis path)

Builds durable behavioral profiles for every person you interact with. LLM-powered analysis of accumulated communication patterns determines preferred styles, decision drivers, and resistance patterns.

**Derived fields:**
- `preferred_message_style` — "data_driven", "vision_led", "relationship_first", "action_oriented", "consensus_seeking"
- `decision_driver_profile` — "analytical", "intuitive", "authority", "collaborative", "pragmatic"
- `influenceability_profile` — "easily_influenced", "evidence_based", "authority_driven", "peer_influenced", "independent"
- `silent_resistance_probability` — public yes, private drag detection (0–1)
- `response_under_pressure` — "calm", "defensive", "aggressive", "avoidant", "analytical"
- `best_approach_for_asks` — one-sentence recommendation
- `topics_that_land_well` — what resonates
- `topics_that_create_friction` — what to avoid

**Source data:** `TranscriptAnalyzer` (LLM Tier: REASONING), `CommunicationStyleDNA`, `RelationshipDynamicsTracker`

---

## Domain 10: Communication Style DNA

**Module:** `analytics/communication_style.py`

Tracks how communication dynamics shift between you and each person across meetings. Detects pace adaptation, talk-ratio changes, and style convergence or divergence over time.

**Derived fields (per-person):**
- `style_profile` — baseline metrics (pace, filler rate, talk ratio, question rate, vocabulary complexity)
- `communication_dynamic` — how your style shifts when interacting with this person (pace_diff_pct, talk_ratio_diff_pct, convergence indicators)

**Source data:** `DeliveryAnalyzer` metrics accumulated across meetings by `PersonIntelligenceRunner`

---

## Pipeline Integration

All domains are wired through the `EnrichmentPipeline` which runs three stages:

1. **Promote** — raw `ExtractedRecord` rows become typed `MemoryObject` instances (Email, CalendarEvent, ScreenCapture, Document, VaultNote)
2. **Enrich** — LLM extraction of entities, topics, sentiment; person resolution; meeting assembly with screenpipe correlation
3. **Analyze** — intelligence scoring (meeting, person, energy) with full analytics stack

The pipeline is idempotent. Records track their processing state in `ProcessingStatus` to avoid reprocessing.

## Data Sources

| Source | Extractor | Deep Connector |
|--------|-----------|----------------|
| Apple Mail | `MailExtractor` | — |
| Apple Calendar | `CalendarExtractor` | — |
| Screenpipe (OCR) | `ScreenpipeExtractor` | `ScreenpipeDeepConnector` |
| Screenpipe (Audio) | — | `ScreenpipeDeepConnector` |
| Screenpipe (Frames) | — | `ScreenpipeDeepConnector` |
| Documents | `DocumentsExtractor` | — |
| Obsidian Vault | `VaultExtractor` | — |
