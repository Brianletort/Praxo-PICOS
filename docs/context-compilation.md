# Context Compilation Theory

Praxo-PICOS implements the reference architecture described in the Context Compilation Theory research program. This document maps PICOS concepts to the theoretical framework.

## The Theory

Context Compilation Theory argues that context should not only be retrieved or remembered -- it should be **compiled**: selected, transformed, governed, optimized, and lowered into executable context packs for models, agents, and interfaces.

The theory introduces **Context IR** as a portable intermediate representation, analogous to compiler IRs in software engineering, and defines a reference architecture with six layers.

### Reference Architecture

```
Source → Substrate → Compiler → IR → Lowering → Runtime
```

## PICOS Mapping

| Theory Layer | PICOS Implementation |
|-------------|---------------------|
| **Source** | Five data sources: Mail, Calendar, Screenpipe (OCR + audio + frames), Documents, Obsidian Vault |
| **Substrate** | `ExtractedRecord` with raw text, timestamps, and source metadata stored in SQLite + FTS5 |
| **Compiler** | `EnrichmentPipeline` — three-stage processor that promotes, enriches (LLM extraction, entity resolution, meeting assembly), and analyzes |
| **IR** | `MemoryObject` with typed `attrs` — the intermediate representation carrying structured intelligence (delivery metrics, power dynamics, body language, relationship scores) |
| **Lowering** | Intelligence scorers that lower complex multi-signal data into actionable derived fields (executive presence, stakeholder alignment, decision quality, cognitive load) |
| **Runtime** | MCP tools, AI assistant chat, daily briefs, pre-brief packets, follow-up generation — context delivered at the right moment in the right form |

### Source Layer

PICOS captures from five heterogeneous sources, each with its own extractor:

- **Mail** — Apple Mail database, extracting sender, recipients, subject, body
- **Calendar** — Apple Calendar database, extracting events with start/end times
- **Screen** — Screenpipe OCR text, audio transcriptions with speaker diarization, video frames with body language signals
- **Documents** — filesystem watcher for document changes
- **Vault** — Obsidian vault markdown notes

### Substrate Layer

Raw signals are normalized into `ExtractionRecord` dataclasses with a uniform schema: source, source_id, title, body, timestamp, metadata. These are persisted to SQLite and indexed in FTS5 for keyword search.

### Compiler Layer

The `EnrichmentPipeline` implements three compiler passes:

1. **Promotion pass** — maps raw records to typed `MemoryObject` instances (Email, CalendarEvent, ScreenCapture, Document, VaultNote, Meeting, Person, Insight)
2. **Enrichment pass** — LLM-based entity/topic/sentiment extraction, cross-source person resolution and deduplication, calendar + screenpipe meeting assembly
3. **Intelligence pass** — runs the full analytics stack: delivery analysis, power dynamics, frame analysis, body language vision, attention tracking, cognitive energy profiling, communication style DNA, relationship dynamics

### IR Layer

`MemoryObject` serves as the Context IR. Each object carries:

- **Type** — determines which intelligence analyzers apply
- **Attrs** — structured dictionary accumulating intelligence outputs
- **Sensitivity** — governance classification (internal, confidential, restricted)
- **Retention band** — lifecycle management (ephemeral, durable, archival)
- **Confidence** — quality signal for downstream consumers

The IR supports relationships via `RelationshipRecord` edges (ATTENDED, COMMUNICATES_WITH, MENTIONED_IN, RELATES_TO), enabling graph traversal across the knowledge base.

### Lowering Layer

Intelligence scorers lower the rich IR into derived fields tuned for specific use cases:

- `ExecutivePerformanceScorer` — lowers delivery + body language into presence/clarity/confidence scores
- `MeetingIntelligenceScorer` — lowers power dynamics + attention into consensus/ROI/tension scores
- `RelationshipIntelligenceScorer` — lowers interaction patterns into trust/friction/sponsorship scores
- `OperatingOptimizationScorer` — lowers energy + attention into cognitive load/deep work/recovery scores
- `TranscriptAnalyzer` — lowers transcript text into behavioral coaching and meeting quality assessments
- `PredictiveEngine` — lowers accumulated intelligence into stakeholder predictions and decision quality

### Runtime Layer

Compiled context is delivered through multiple channels:

- **MCP Tools** — `search_memory`, `get_daily_brief`, `list_sources`, `get_source_status` for AI assistants
- **Chat API** — hybrid search with BM25 FTS, context-grounded responses
- **Pre-Brief Packets** — stakeholder maps, objection forecasts, talking points generated before meetings
- **Follow-Up Generation** — personalized messages tailored per recipient's communication style
- **Daily Briefs** — synthesized intelligence organized by source
- **Coaching Reports** — narrative-form feedback on meeting performance

## Papers

The theory is formalized in four Zenodo preprints (April 2026):

### Foundational

**Toward a Theory of Context Compilation for Human-AI Systems**
DOI: [10.5281/zenodo.19490060](https://doi.org/10.5281/zenodo.19490060)

Introduces the constrained-optimization formulation for context compilation, a taxonomy across adjacent paradigms (RAG, memory, long-context, prompt assembly), the six-layer reference architecture, portable Context IR schema, and CompileBench for measuring compilation quality.

### Trilogy

**Paper 1: Context IR and Compiler Passes for Enterprise AI**
DOI: [10.5281/zenodo.19546798](https://doi.org/10.5281/zenodo.19546798)

Operationalizes the theory with a four-level Context IR, taxonomy of compiler passes, formal treatment of context graph breaks, and policy-as-types governance.

**Paper 2: Paged Context Memory**
DOI: [10.5281/zenodo.19546800](https://doi.org/10.5281/zenodo.19546800)

Context as semantic runtime: evidence blocks, working sets, locality, hot/warm/cold lifecycle transitions, speculation, context GC, linking, and policy-preserving provenance.

**Paper 3: Quantized Context**
DOI: [10.5281/zenodo.19546802](https://doi.org/10.5281/zenodo.19546802)

Optimization as precision control: semantic precision ladder, mixed-precision assembly, semantic outlier protection, and recovery paths.

**Trilogy Hub:** [brianletort.ai/research/context-compilation-trilogy](https://www.brianletort.ai/research/context-compilation-trilogy)

## Reference Implementation

The MemoryOS repository serves as the reference implementation companion for Context Compilation Theory. PICOS builds on this foundation to deliver a production-grade executive intelligence system.
