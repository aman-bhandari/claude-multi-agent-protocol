# SYNC.md — Format Specification

The shared intent surface of a multi-agent cluster. One file in a shared commons repo. Multiple writers, one section per writer.

## File location

`SYNC.md` lives at the root of a **commons** repository — a small repo whose only purpose is to hold this file (and the protocol docs, or a pointer to them). No data artefacts live in the commons repo. No code lives in the commons repo. Just intent.

Why a separate repo and not a file inside one of the agent repos: neutrality. No agent owns the intent surface more than another.

## Document shape

```markdown
# SYNC.md — Shared Intent Surface

Last full review: <YYYY-MM-DD> (<short tag for what changed>).

---

## Goal Status

<The cluster's top-level objective. Updated when the objective changes,
which is rare. Typically a paragraph plus a phase label.>

---

## Decision Log (append-only, newest at bottom)

<One-line decisions that shape cluster behavior. Never edited, never deleted.>

- <ISO date> -- <one-line decision>

---

## Conflict Registry

<Disagreements between agents, or between an agent and a durable contract.
Raised by the discovering agent; resolved by the Orchestrator.>

---

## <agent-name> (writes: <which repo>)

- **current-focus** (<ISO date>): <what this agent is doing right now>
- **recent-shift** (<ISO date>): <what changed since the last update>
- **open-question** (<ISO date>): <what this agent wants another to answer>

## <next agent>
...
```

Sections are required in this order:
1. Goal Status
2. Decision Log
3. Conflict Registry
4. One section per agent (any order)

## Single-writer-per-section rule

Each agent writes only the section named after it. Never edit another agent's section. This is the invariant that eliminates SYNC merge conflicts.

The one exception: the **Orchestrator** (human-in-the-loop). The Orchestrator may edit any section, including another agent's, to resolve conflicts. Orchestrator edits of another agent's section should append a dated Orchestrator-note line rather than rewriting in place.

## Agent section schema

Each agent section carries exactly three fields:

- `current-focus`: what the agent is doing right now. One paragraph maximum. Written in the present tense.
- `recent-shift`: what changed since the last update. One paragraph maximum. Written in past tense or completed-action framing.
- `open-question`: what the agent wants another agent (or the Orchestrator) to answer. Explicit about the addressee. If nothing is open, write the field as `- **open-question** (<ISO date>): (none)` so the validator still sees a date and a value.

No fourth field. No narrative. No decision text (decisions go in the Decision Log). No data artefacts (those go in the upstream repo's HANDOVER).

### Why exactly three

- `current-focus` is for answering "what are you working on?" without reading the data.
- `recent-shift` is for answering "what changed since I last looked?" without a git log.
- `open-question` is for answering "what do you need from me?" without a meeting.

Four fields invites narrative. Two fields collapses too much context. Three is the minimum that separates present, past, and ask.

### Timestamp rule

Every field line carries an ISO 8601 date. The date is updated when the content of that field changes. An unchanged field's date does not move.

If all three fields in a section have a date older than 7 days, the section is considered **stale** and should be flagged to the owning agent. A stale-section watchdog is described in `docs/protocol-overview.md`.

## Decision Log schema

One line per decision. ISO date, double-dash separator, one-line summary. No headers, no sub-bullets, no decision numbers.

```
- 2026-03-04 -- Adopted append-only HANDOVER.md rather than a ring buffer. Reason: audit trail is more valuable than active-queue size.
```

Decisions are never edited. If a decision is superseded, a new row below records the supersession:

```
- 2026-03-14 -- Supersedes 2026-03-04 HANDOVER append-only decision for entries older than 90 days. Archive-to-separate-file rule adopted for long-running queues.
```

The 2026-03-04 line stays. The 2026-03-14 line amends it.

## Conflict Registry schema

Entries appear when an agent discovers a disagreement. One block per conflict:

```markdown
- <ISO date> -- <owning-agent-name> -- <one-line description>. Proposed resolution: <...>. Awaiting: <Orchestrator | other agent name>.
```

When resolved, append `-- RESOLVED <ISO date>: <one-line note>` to the same row. The row stays; the registry is append-only.

## Extension points

Teams that want to add per-agent fields can extend the three-field schema. The validator treats:

- `current-focus`, `recent-shift`, `open-question` as required (hard fail if missing).
- Any other `**field**:` line as an extension (warning, not fail).

Common extensions:
- `blocking`: a hard blocker the Orchestrator should know about.
- `next-check-in`: when this agent will next update its section.
- `confidence`: how certain the agent is about its `current-focus` statement.

Teams that want to extend the section set (adding a new top-level section like `## Resource Budget`) should add it below `## Conflict Registry` and above the agent sections. The validator accepts any number of top-level `##` sections before the agent sections; it fails only if one of the required top-level sections (Goal Status, Decision Log, Conflict Registry) is missing.

## Example

See `examples/commons/SYNC.md` for a working example of this format. It carries a Goal Status paragraph, three Decision Log entries, one Conflict Registry entry, and three agent sections (Producer / Processor / Publisher) with realistic but synthetic content.

## What this file is NOT

- Not a chat channel. Low frequency. Update when intent changes, not per commit.
- Not a task list. Tasks live in each agent's own tooling.
- Not a content store. Narrative entries belong in whichever agent's repo handles narrative.
- Not a substitute for durable contracts. Each agent's repo-level `CLAUDE.md` (or equivalent) is the durable contract; SYNC is transient intent. On conflict between the two, CLAUDE.md wins and the conflict gets a Conflict Registry entry.
