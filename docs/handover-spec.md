# HANDOVER.md — Format Specification

The data outbox of a single upstream repository. One file, one writer, append-only.

## File location

`HANDOVER.md` lives at the root of the upstream repository. Each agent in a pipeline owns exactly one HANDOVER file — the one in its own repo. Downstream agents read it; they do not write to it.

## Single writer rule

Only the agent that owns the upstream repo writes to that repo's `HANDOVER.md`. Downstream agents never append, edit, or delete entries. This is the invariant that eliminates merge conflicts: git never sees two writers racing on this file.

If a downstream agent needs to respond, it does so in **SYNC.md** (intent surface), not here. Data flows one way. Intent flows both ways.

## Document shape

```markdown
# HANDOVER Queue — <producer agent name>

<One-line description of what this producer produces.>

## Queue

<One entry per unit of work ready for downstream consumption. Newest at top.>

## Processed (archive)

<Optional. Entries a downstream agent has consumed, moved here by the upstream
writer after the downstream agent advances its `.last-processed.md`. Keeps the
active Queue short while preserving the audit trail.>
```

The `## Queue` section is required. The `## Processed` section is optional; if present, it preserves entries after downstream consumption.

## Entry schema (required fields)

Each queue entry is a block at level 3 (`###`) with a frontmatter-style metadata block:

```markdown
### [entry-id]: <short human title>

- **date**: YYYY-MM-DD
- **from**: <producer agent name>
- **for**: <downstream agent name, or "any">
- **status**: queued | processed | abandoned
- **artifact-path**: path/in/repo/to/the/thing/produced
- **summary**: <one to three sentences; what was produced and why downstream cares>
```

### Field semantics

- `date` — ISO 8601 date when the entry was written.
- `from` — the producer agent's name. Matches the SYNC.md section name.
- `for` — the downstream agent's name. `any` means any downstream can consume.
- `status` — lifecycle state.
  - `queued`: ready for consumption.
  - `processed`: a downstream agent has acted on it (moved by the producer after the downstream advances its `.last-processed.md`).
  - `abandoned`: the producer withdrew the entry before consumption. Rare. Requires a reason line.
- `artifact-path` — path, relative to the producer's repo root, pointing at what was produced. For entries whose "artifact" is itself textual (a decision, a question), the path can be a docs file. The rule is: the path points at *something readable*, not at an abstract reference.
- `summary` — one to three sentences. No narrative. Narrative belongs in the Observer's chronicle, not here.

## Entry ID format

`[entry-id]` is a short slug, unique within the queue. Date-suffixed is the simplest convention: `2026-03-04-session-12`. Sequential numbers (`entry-042`) also work but require coordination if multiple branches are producing. Date-suffixed is preferred because it sorts naturally.

## Append-only rule

Entries are added, not edited or deleted. If a producer changes its mind, it adds a new entry rather than editing the old one. A lifecycle transition (queued → processed → archived) modifies the `status` field and, optionally, moves the entry between the `## Queue` and `## Processed` sections. Historical content inside an entry is not rewritten.

This is the same discipline as an append-only decision log. The reasoning trail is as valuable as the current state.

## Downstream consumption

A downstream agent that wants to process the queue:

1. Read `HANDOVER.md` in the upstream repo.
2. For each entry whose `for` is `any` or matches the downstream's name, compare against the downstream's own `.last-processed.md` marker.
3. Process each new entry in order (newest queue entries are at top, so iterate in reverse for chronological processing).
4. Advance `.last-processed.md` to the last processed entry's id.
5. Commit in own repo.

The producer can then move processed entries to `## Processed` on its next update. Downstream agents do not move entries; that would violate the single-writer rule.

## Example

See `examples/upstream-repo/HANDOVER.md` for a working example of this format. It carries three synthetic entries demonstrating a typical queue shape.

## Extension points

Teams that need additional fields (a priority level, a review checklist, a link to a generated artefact bundle) can extend the schema by adding new `- **field**: value` rows below the required ones. The validator (`scripts/validate.py`) treats required fields as hard failures and unknown fields as warnings, so extensions do not break the validator.

What they cannot do:
- Drop required fields. All six are load-bearing.
- Change the single-writer rule. Multiple writers destroy the merge-conflict immunity.
- Put intent in this file. Intent goes in SYNC.md.

## What this file is NOT

- Not a chat log. Entries are data artefacts, not conversation.
- Not a decision log. Decisions about direction go in SYNC.md's Decision Log section.
- Not a task tracker. Tasks live in each agent's own repo tooling.
- Not a read-receipts surface. Downstream agents signal consumption by advancing their own `.last-processed.md`, not by editing the producer's HANDOVER.
