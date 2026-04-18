# SYNC.md — Shared Intent Surface

Last full review: 2026-03-05 (schema migration acknowledgement).

---

## Goal Status

Top-level objective of the cluster:

> Turn raw quarterly policy documents into searchable, cross-referenced, user-facing pages with accurate citations and stable URLs. One full pipeline run per quarter. Human review before publish.

Current phase: **Q1 2026 quarterly batch.** Complete when the twelve Q1 documents have cleared Producer ingest, Processor enrichment, and Publisher render, and the Orchestrator has approved the render diff against the previous quarter's baseline.

---

## Decision Log (append-only, newest at bottom)

- 2026-02-14 -- Adopted the three-agent pipeline (Producer / Processor / Publisher) over a single-agent monolith. Rationale: independent failure domains make debugging quarterly regressions tractable. Decision recorded after a single-agent pipeline silently regressed in Q4 2025 for eleven days before surfacing.
- 2026-02-14 -- HANDOVER schema set per `docs/handover-spec.md`. Single-writer invariant on each repo's HANDOVER file. Processor and Publisher respond via this SYNC file, not by editing HANDOVERs.
- 2026-02-28 -- Adopted `.last-processed.md` pattern for downstream consumption tracking. Each agent stores its own marker in its own repo, not in commons. Reason: commons stays small and stable; per-agent state belongs to the agent.
- 2026-03-05 -- Source schema v3 rolled out by the upstream CMS. Producer tolerates both v2 and v3 field names for the next 90 days. Processor and Publisher acknowledged. Full schema-migration notes in Producer's `docs/schema-v3-notes.md`; HANDOVER entry `2026-03-05-schema-migration-note` is the downstream announcement.

---

## Conflict Registry

- 2026-03-03 -- Processor -- The Producer's new `document_category` values include two categories that were merged in the Processor's v2 taxonomy. Proposed resolution: temporarily retain the v2 collapsed categories in Processor outputs; add an open-question below so the Orchestrator can decide whether to re-expand. Awaiting: Orchestrator. -- RESOLVED 2026-03-04: Orchestrator decided to keep the Processor's v2 taxonomy for Q1 to avoid disrupting downstream URL stability; Producer will emit the new categories starting Q2 once Publisher URL patterns are updated to cover the expanded set.

---

## Producer (writes: upstream-repo agent)

- **current-focus** (2026-03-05): Q1 2026 batch ingest complete; twelve documents processed and sitting in HANDOVER queue. Schema v3 migration notes published. Awaiting Processor pickup.
- **recent-shift** (2026-03-05): Handled the schema v3 rollout from the upstream CMS. Added dual-read support for the two renamed fields. Ran a back-compat test against Q4 2025 fixtures; all twelve cleared. No regressions in the extraction path.
- **open-question** (2026-03-02): When the 90-day dual-read window closes (2026-06-05), which agent owns the v2-field-name deprecation check? Producer can emit a warning on ingest when old names are seen, but downstream validation belongs somewhere. Awaiting: Orchestrator.

## Processor (writes: processing-repo agent)

- **current-focus** (2026-03-05): Pulling the Q1 2026 batch from Producer's HANDOVER. First three documents cross-referenced and enriched; remaining nine queued for tomorrow's run. Definition-extraction pass scheduled for end of week.
- **recent-shift** (2026-03-04): Orchestrator resolved the v3 taxonomy conflict. Processor will retain v2 taxonomy for Q1. Adjusted the category-mapping table to collapse the two new v3 categories into their v2 parent. Noted in HANDOVER entry once the Q1 batch is complete.
- **open-question** (2026-03-04): (none)

## Publisher (writes: publisher-repo agent)

- **current-focus** (2026-03-05): Watching Processor's HANDOVER queue. Nothing to render yet; the Q1 batch will come through once Processor finishes. URL-pattern update for Q2's expanded taxonomy is on the Publisher's internal roadmap for April.
- **recent-shift** (2026-02-20): Updated the schema.org `Article` JSON-LD mapping to include the new `document_category` field from Processor outputs. Change is backwards-compatible; entries without the field render without it.
- **open-question** (2026-03-02): Processor's enriched outputs carry a `definitions` list. Currently rendered inline as footnotes. Is a dedicated `/glossary` page worth building, or keep footnotes? No build pressure — decide when we have full Q1 to see how bulky inline footnotes actually get. Awaiting: Orchestrator.

---

## Stale-section watchdog

Any agent section whose field timestamps are all older than 7 days gets flagged on the next Orchestrator check-in. Empty sections (no `current-focus`, `recent-shift`, or `open-question`) are flagged to the owning agent.
