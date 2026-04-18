# HANDOVER Queue — Producer Agent

Synthetic example demonstrating the HANDOVER format for a three-agent pipeline (Producer → Processor → Publisher). The Producer writes raw source material; the Processor enriches and normalises; the Publisher renders final output.

## Queue

### 2026-03-04-document-batch-12: Quarterly policy documents processed

- **date**: 2026-03-04
- **from**: Producer
- **for**: Processor
- **status**: queued
- **artifact-path**: source/policy-docs/2026-q1/
- **summary**: Twelve quarterly policy documents ingested from the source system. Text extracted, basic metadata attached (title, effective-date, category). Ready for the Processor's enrichment pass — cross-reference resolution, definition extraction, and structured-summary generation.

### 2026-03-05-schema-migration-note: Source schema changed; two fields renamed

- **date**: 2026-03-05
- **from**: Producer
- **for**: any
- **status**: queued
- **artifact-path**: docs/schema-v3-notes.md
- **summary**: The upstream CMS renamed two fields (`doc_type` → `document_category`, `effective_from` → `effective_date`). Producer updated its extractor to read both old and new names for backwards compatibility; next 90 days of ingests may see either. Processor and Publisher should tolerate both. Full migration notes in the referenced artifact.

## Processed (archive)

### 2026-02-28-document-batch-11: Prior quarter's documents, fully processed

- **date**: 2026-02-28
- **from**: Producer
- **for**: Processor
- **status**: processed
- **artifact-path**: source/policy-docs/2025-q4/
- **summary**: Q4 2025 batch. Processor advanced `.last-processed.md` to this entry on 2026-03-01; Producer moved the entry here on the next update cycle. Retained for audit.

---

## How this file is consumed

Downstream agents (Processor, Publisher, any future agent) read this file, compare against their own `.last-processed.md` marker (stored in their own repo), and act on anything newer.

Only the Producer writes to this file. Processor and Publisher respond via the shared SYNC.md at the commons repo, not by editing this file.
