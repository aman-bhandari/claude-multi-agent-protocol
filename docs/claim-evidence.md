# Claim-Evidence Mapping

Every claim this repo makes — in its GitHub description, its README, and any resume line pointing at it — must map to a file or command that evidences the claim.

**Rule:** every row must be verified (✅) before push. An unverified row (☐) fails the integrity check and blocks CI.

## Claims

| Claim | Evidence (file / command) | Verified |
|-------|---------------------------|----------|
| "HANDOVER + SYNC protocol" | `docs/protocol-overview.md` + `docs/handover-spec.md` + `docs/sync-spec.md` all present; integrity-check enforces presence | ✅ |
| "one-way data flow + bidirectional intent log" | `docs/protocol-overview.md` sections "The two surfaces", "Why not put everything in SYNC?", "Why not put everything in HANDOVER?" explain the distinction with concrete example | ✅ |
| "HANDOVER.md schema (6 required fields)" | `docs/handover-spec.md` specifies required fields: date, from, for, status, artifact-path, summary; `scripts/validate.py` enforces all 6; shipped example (`examples/upstream-repo/HANDOVER.md`) passes validation | ✅ |
| "SYNC.md schema (3 required top sections + 3 per-agent fields)" | `docs/sync-spec.md` specifies Goal Status / Decision Log / Conflict Registry + per-agent current-focus / recent-shift / open-question; `scripts/validate.py` enforces; shipped example passes validation | ✅ |
| "synthetic example HANDOVER with >=2 entries" | `examples/upstream-repo/HANDOVER.md` has 2 queued entries + 1 processed entry; integrity-check counts `### ` headers | ✅ |
| "synthetic example SYNC with >=3 agent sections" | `examples/commons/SYNC.md` has Producer / Processor / Publisher sections; integrity-check counts them | ✅ |
| "synthetic example SYNC with >=2 decision-log entries" | `examples/commons/SYNC.md` Decision Log has 4 entries; integrity-check counts them | ✅ |
| "conformance validator (zero dependencies)" | `scripts/validate.py` runs on Python 3.10+ stdlib only (argparse, re, sys, pathlib); modes: `handover`, `sync`, `both` | ✅ |
| "validator rejects schema violations" | `scripts/integrity-check.sh` smoke-tests validator against a broken HANDOVER fixture; validator must exit non-zero | ✅ |
| "adoptable — 6-step adoption procedure" | `docs/protocol-overview.md` section "How to adopt" lists 6 concrete steps | ✅ |
| "extension points for per-team fields" | `docs/handover-spec.md` "Extension points" and `docs/sync-spec.md` "Extension points" sections document how to add fields; validator treats unknown fields as warnings not errors | ✅ |

## How this file is enforced

`scripts/integrity-check.sh` (run locally) and `.github/workflows/ci.yml` (run on every push) both fail if any row in this file carries `☐` instead of `✅`. This applies Gate 0 of the bulletproof publishing contract.

## Adding a new claim

1. Add a row here with the claim text (verbatim) and the evidencing command or file path.
2. Mark as `☐` until verified.
3. Run `bash scripts/integrity-check.sh`. It fails while any row carries `☐`.
4. Verify the evidence, flip to `✅`, re-run.
5. Push only after all rows are `✅`.
