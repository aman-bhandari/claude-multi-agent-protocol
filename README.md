# claude-multi-agent-protocol

HANDOVER + SYNC inter-repo protocol for multi-agent AI systems. A file-based convention for coordinating three or more agents that each own their own repository, without a central scheduler or shared mutable state.

## What this is

Two coordination surfaces, separated by direction:

1. **HANDOVER.md** — lives in each upstream repo. One-way data flow. The producing agent writes; downstream agents read. Single writer per file, so no merge conflicts. Append-only entries.
2. **SYNC.md** — lives in a shared commons repo. Bidirectional intent flow. Every agent has its own section with three fields (`current-focus`, `recent-shift`, `open-question`). Single writer per section, so merges are trivial.

The central insight: data coordination wants one-way flow (no cycles, no contention). Intent coordination wants bidirectional flow. Conflating them in one file causes every agent to either rubber-stamp or rewrite every change. Separating them makes the protocol git-friendly, append-only, and requires no runtime coordinator.

This repo ships:
- Format specifications for both files (`docs/handover-spec.md`, `docs/sync-spec.md`)
- Protocol overview explaining the rationale (`docs/protocol-overview.md`)
- Working synthetic examples (`examples/upstream-repo/HANDOVER.md`, `examples/commons/SYNC.md`)
- Conformance validator (`scripts/validate.py`, zero dependencies)
- Integrity check that smoke-tests the validator

## Tech stack

- Plain markdown for both protocol files and all documentation
- Python 3.10+ stdlib for the conformance validator (argparse, re, pathlib — no external packages)
- Bash + GitHub Actions CI for integrity gate enforcement

## Architecture

```
claude-multi-agent-protocol/
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── protocol-overview.md         # Rationale: one-way data + bidirectional intent
│   ├── handover-spec.md             # HANDOVER.md format specification
│   ├── sync-spec.md                 # SYNC.md format specification
│   └── claim-evidence.md            # Gate 0: every claim evidenced
├── examples/
│   ├── upstream-repo/
│   │   └── HANDOVER.md              # Synthetic 3-entry queue example
│   └── commons/
│       └── SYNC.md                  # Synthetic 3-agent intent surface
├── scripts/
│   ├── validate.py                  # Conformance validator (Python stdlib only)
│   └── integrity-check.sh           # Gates 0, 4, 5 + validator smoke tests
└── .github/workflows/ci.yml         # Runs integrity check + hype-word audit
```

## Setup

No install step required.

```bash
git clone https://github.com/aman-bhandari/claude-multi-agent-protocol.git
cd claude-multi-agent-protocol
```

Python 3.10 or newer is required for the validator.

## Usage

### Validate a HANDOVER file

```bash
python3 scripts/validate.py handover path/to/HANDOVER.md
```

Checks required fields, status-enum values, ISO 8601 dates. Unknown extension fields are warnings, not errors.

### Validate a SYNC file

```bash
python3 scripts/validate.py sync path/to/SYNC.md
```

Checks top-level sections (Goal Status, Decision Log, Conflict Registry) and per-agent required fields (`current-focus`, `recent-shift`, `open-question`).

### Validate both at once

```bash
python3 scripts/validate.py both path/to/HANDOVER.md path/to/SYNC.md
```

### Read the examples

`examples/upstream-repo/HANDOVER.md` shows a three-agent pipeline (Producer → Processor → Publisher) with two queued entries and one processed entry.

`examples/commons/SYNC.md` shows the intent surface for the same pipeline with three agent sections, a four-entry decision log, and one resolved conflict.

## Adopt in your cluster

Steps are documented in `docs/protocol-overview.md` ("How to adopt") and recap here:

1. Create a commons repo. Put `SYNC.md` in it. Nothing else.
2. In each agent's own repo, add `HANDOVER.md` using the schema from `docs/handover-spec.md`.
3. In the commons repo's `SYNC.md`, add one section per agent following the schema from `docs/sync-spec.md`.
4. Each agent's operator prompt references both files: read both before working, update both after working.
5. Run `scripts/validate.py` in CI on every repo that owns one of the files.
6. When agents disagree, the human (Orchestrator) adds a Conflict Registry row and resolves it inline.

## Integrity check

```bash
bash scripts/integrity-check.sh
```

Runs:

- **Gate 0** — every claim in `docs/claim-evidence.md` marked verified (✅)
- **Gate 4** — zero private identifiers (internal project names, client domains, real individuals)
- **Gate 5** — no secrets (API keys, tokens, passwords)
- **Artifact-specific** — all three spec docs present; both example files present; HANDOVER example has ≥2 entries; SYNC example has ≥2 decision-log entries and ≥3 agent sections; `scripts/validate.py` is clean against the shipped examples AND correctly rejects a deliberately-broken HANDOVER fixture

CI runs the same gates on every push via `.github/workflows/ci.yml`.

## Honest extract statement

The protocol was originally designed for a four-repo research-lab cluster (one "human" position plus three agents: a builder, a documenter, and a publisher). The extract keeps:

- The two-surface architecture (HANDOVER for one-way data, SYNC for bidirectional intent)
- The single-writer invariants (per-repo HANDOVER, per-section SYNC)
- The seven operating rules (one-way data, single-writer sections, strict schema, append-only decision log, durable contracts win over transient intent, git-as-serializer, timestamps mandatory)
- The three-field per-agent schema (current-focus, recent-shift, open-question)
- The append-only decision log + conflict registry pattern

The extract drops everything lab-specific: the original role names (replaced with Producer / Processor / Publisher in the examples), the domain-specific wiki and chronicle references, and all real decision entries. The three agent sections in `examples/commons/SYNC.md` and the HANDOVER entries in `examples/upstream-repo/HANDOVER.md` are synthetic — a policy-document-processing pipeline that does not exist, with fake dates, fake batches, and fake schema-migration notes.

## Related artifacts

- `claude-code-mcp-qa-automation` — end-to-end QA automation built on Claude Code + MCP patterns
- `claude-code-agent-skills-framework` — research scaffold for AI-engineering coaching with Claude Code
- `llm-rag-knowledge-graph` — chronicle editorial format + wiki-as-RAG graph shape (uses this protocol for inter-repo coordination)
- `nextjs-16-mdx-research-publisher` — static publisher for research labs

## License

MIT © 2026 Aman Bhandari. See `LICENSE`.
