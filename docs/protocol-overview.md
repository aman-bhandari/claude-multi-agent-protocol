# Protocol Overview

A convention for coordinating multiple AI agents — each owning its own repository — without a central scheduler or shared mutable state.

## The problem this solves

Once you run more than one agent against a multi-repo codebase, two coordination failures show up quickly:

1. **Data races at shared files.** Two agents edit the same file, one overwrites the other's work, git merge cannot reconcile because neither agent knew the other was writing. A file lock would solve this but introduces a dependency on a coordinator neither agent wants to run.
2. **Intent drift.** An upstream agent's understanding of "what we are building" drifts from a downstream agent's understanding over hours of independent work. The next integration point surprises both.

The central insight of this protocol is that these two problems want opposite solutions. Data coordination wants one-way flow (no cycles, no contention). Intent coordination wants bidirectional flow (every agent both reads and writes the shared understanding).

Conflating them — routing both data and intent through the same file — causes every agent to either rubber-stamp or rewrite every change, because there is no signal telling them which kind of message they are looking at. This protocol separates the two surfaces.

## The two surfaces

| Surface | Direction | File | Writer(s) | Reader(s) |
|---------|-----------|------|-----------|-----------|
| **HANDOVER** | One-way (upstream → downstream) | `HANDOVER.md` in the upstream repo | Only the upstream agent | Every downstream agent that consumes the upstream |
| **SYNC** | Bidirectional | `SYNC.md` in the shared commons repo | All agents; each writes only its own section | All agents |

HANDOVER is the data outbox. When agent A finishes work that agent B needs, A appends an entry to its own `HANDOVER.md`. B reads it, acts on it, advances its own local `.last-processed.md` marker. The file has a single writer, so there are no merge conflicts. Downstream agents never write here; they only read.

SYNC is the shared intent surface. Every agent has a section in `SYNC.md` stating its current focus, recent shift, and open questions for other agents. Agents read each other's sections to stay aligned on the bigger picture. The single-writer-per-section rule means merges are trivial (agents never edit each other's sections).

## Why not put everything in SYNC?

SYNC is small, low-frequency, human-readable intent. If you put data there (a queue of work items, a log of artefacts produced, a stream of events), three things break:

- The file grows fast and becomes unscannable.
- The single-writer-per-section rule does not apply cleanly; multiple agents may want to enqueue work.
- The commons repo becomes a hot spot of commits, defeating the design goal of low-frequency intent coordination.

Data flows downstream; keep it there. SYNC is for the questions one agent wants another to answer.

## Why not put everything in HANDOVER?

HANDOVER is per-upstream-repo. If agent A and agent B both need to know a decision agent C made, and that decision is written only in C's HANDOVER, A has to read C's HANDOVER even though A does not consume C's data downstream. The dependency graph of "who reads whose HANDOVER" gets tangled fast.

Intent decisions live in one place (SYNC), and every agent reads that one place. Data artefacts live per-upstream (HANDOVER), and only downstream consumers need to read them.

## The four roles

For the protocol's rules to be useful, give each agent a defined role. This repo's examples use these four:

- **Orchestrator** (the human). Final arbiter on conflicts. May edit any section of SYNC to resolve disagreements. Does not typically write HANDOVER entries.
- **Producer Agent.** Writes upstream work to its own repository. Drops HANDOVER entries for downstream agents when work is ready for consumption.
- **Processor Agent.** Reads Producer's HANDOVER, acts on each entry, writes its own outputs to its own repository. Drops HANDOVER entries for the next downstream agent.
- **Publisher Agent.** Reads Processor's HANDOVER, renders final artefacts (web pages, blog posts, reports), does not write a downstream HANDOVER because nothing consumes its output inside the cluster.

These names are placeholders. Adapt to your cluster: Planner / Engineer / Reviewer / Deployer; Ingest / Transform / Serve; Designer / Developer / Tester. What matters is that the pipeline is acyclic and each agent has exactly one upstream it reads from (except the first, which reads from the human) and zero or one downstream it writes to.

## Cycle prevention

The protocol enforces acyclicity by convention, not mechanism. If Processor writes a HANDOVER entry addressed to Producer, Producer should refuse — that is a cycle. Legitimate upstream feedback goes through SYNC, not HANDOVER.

A cycle via SYNC is harmless because SYNC is intent, not work. Processor asking Producer a question in its `open-question` field is coordination, not data flow.

## Single-writer invariants

- `HANDOVER.md`: single writer (the owning repo's agent). Downstream agents only read.
- `SYNC.md`: single writer per section. Each agent writes only its own section. The Orchestrator may edit any section to resolve conflicts.
- Each agent's `.last-processed.md`: single writer (the owning agent). Stored in the agent's own repo. Not committed to commons.

These invariants eliminate the need for file locks or a coordinator process. Git is the serializer; merges are structurally impossible to conflict (on HANDOVER because only one writer; on SYNC because only one writer per section). Conflicts on commons file edits reduce to document-level conflicts that the Orchestrator resolves.

## When the protocol does not fit

This protocol fits three or more agents with one-way data dependencies and a human-in-the-loop. It does not fit:

- **Peer-to-peer agents** with no hierarchical dependency. (Use a shared event bus instead; the bus replaces HANDOVER.)
- **Agents that need immediate response** (sub-second). (The protocol is polling-based via file reads; latency is measured in human-check-in intervals, not seconds.)
- **Single-agent setups.** (Nothing to coordinate.)

For the target case — a research lab, a content pipeline, a multi-stage code-review workflow with agents owning their own repos — it is light, append-only, git-friendly, and introduces no runtime dependencies.

## How to adopt

See `docs/handover-spec.md` and `docs/sync-spec.md` for the two format contracts. See `examples/` for working examples of each file. See `scripts/validate.py` for the conformance validator that any adopting repo can run against its own HANDOVER + SYNC.

Steps:

1. Create a **commons** repo for your cluster. This is where `SYNC.md` lives. Keep it small; nothing else goes here except the sync file and the protocol docs (or a pointer to this repo).
2. In each agent's own repo, add `HANDOVER.md` with the schema from `docs/handover-spec.md`. Start with an empty queue.
3. In the commons repo, add `SYNC.md` with one section per agent. The schema is in `docs/sync-spec.md`.
4. Each agent's operator prompt references both files: "before starting work, read `../commons/SYNC.md` and `../upstream-repo/HANDOVER.md`; after finishing, append to your own `HANDOVER.md` and update your SYNC section."
5. Run `scripts/validate.py path/to/handover path/to/sync` in CI on both repos. Fail the build on schema violations.
6. When agents disagree, the Orchestrator adds a Conflict Registry row in SYNC.md and resolves it inline.

Adopting teams typically extend the SYNC schema first (adding fields for their domain), then the HANDOVER schema. The validator is designed to accept a schema config file so extensions do not require editing the validator itself. That extension point is called out in `docs/sync-spec.md`.
