#!/usr/bin/env python3
"""
validate.py — conformance validator for HANDOVER.md and SYNC.md.

Checks that files conform to the schemas in docs/handover-spec.md and
docs/sync-spec.md.

Usage:
    python3 scripts/validate.py handover path/to/HANDOVER.md
    python3 scripts/validate.py sync path/to/SYNC.md
    python3 scripts/validate.py both path/to/HANDOVER.md path/to/SYNC.md

Exit codes:
    0 — all required fields present; any unknown fields are warnings only
    1 — one or more required fields missing (hard failure)
    2 — usage error (bad arguments)

Zero external dependencies — Python 3.10+ stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HANDOVER_REQUIRED_FIELDS = ["date", "from", "for", "status", "artifact-path", "summary"]
HANDOVER_VALID_STATUS = {"queued", "processed", "abandoned"}

SYNC_REQUIRED_TOP_SECTIONS = ["Goal Status", "Decision Log", "Conflict Registry"]
SYNC_AGENT_REQUIRED_FIELDS = ["current-focus", "recent-shift", "open-question"]


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def warn(msg: str, warnings: list[str]) -> None:
    warnings.append(msg)


def validate_handover(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")

    if not re.search(r"^## Queue\b", text, flags=re.MULTILINE):
        fail(f"{path}: missing required section '## Queue'", errors)

    entry_pattern = re.compile(r"^### \[?([A-Za-z0-9_.\-]+)\]?:", flags=re.MULTILINE)
    entries = list(entry_pattern.finditer(text))
    if not entries:
        warn(f"{path}: no entries found under any ### heading", warnings)

    for i, m in enumerate(entries):
        start = m.end()
        end = entries[i + 1].start() if i + 1 < len(entries) else len(text)
        block = text[start:end]
        entry_id = m.group(1)

        found_fields = {}
        for fm in re.finditer(r"^\s*-\s+\*\*([a-z\-]+)\*\*:\s*(.*)$", block, flags=re.MULTILINE):
            found_fields[fm.group(1)] = fm.group(2).strip()

        for required in HANDOVER_REQUIRED_FIELDS:
            if required not in found_fields:
                fail(f"{path}: entry '{entry_id}' missing required field '{required}'", errors)

        status = found_fields.get("status")
        if status and status not in HANDOVER_VALID_STATUS:
            fail(
                f"{path}: entry '{entry_id}' has invalid status '{status}'. "
                f"Valid: {sorted(HANDOVER_VALID_STATUS)}",
                errors,
            )

        date = found_fields.get("date")
        if date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            fail(f"{path}: entry '{entry_id}' date '{date}' not ISO 8601 (YYYY-MM-DD)", errors)

        unknown = set(found_fields) - set(HANDOVER_REQUIRED_FIELDS)
        for field in sorted(unknown):
            warn(f"{path}: entry '{entry_id}' has unknown extension field '{field}' (allowed)", warnings)

    return errors, warnings


def validate_sync(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")

    for section in SYNC_REQUIRED_TOP_SECTIONS:
        if not re.search(rf"^##\s+{re.escape(section)}\b", text, flags=re.MULTILINE):
            fail(f"{path}: missing required top-level section '## {section}'", errors)

    agent_section_pattern = re.compile(
        r"^##\s+(?!Goal Status\b|Decision Log\b|Conflict Registry\b|Stale-section watchdog\b)(.+?)$",
        flags=re.MULTILINE,
    )
    agents = list(agent_section_pattern.finditer(text))
    if len(agents) < 2:
        warn(
            f"{path}: fewer than 2 agent sections found. The protocol assumes a "
            f"multi-agent cluster; single-agent setups should not use SYNC.",
            warnings,
        )

    for i, m in enumerate(agents):
        header = m.group(1).strip()
        start = m.end()
        end = agents[i + 1].start() if i + 1 < len(agents) else len(text)
        block = text[start:end]
        agent_name = re.split(r"\s*\(", header)[0].strip()

        found_fields = {}
        for fm in re.finditer(
            r"^\s*-\s+\*\*([a-z\-]+)\*\*\s*(?:\([^)]*\))?:\s*(.*)$",
            block,
            flags=re.MULTILINE,
        ):
            found_fields[fm.group(1)] = fm.group(2).strip()

        for required in SYNC_AGENT_REQUIRED_FIELDS:
            if required not in found_fields:
                fail(
                    f"{path}: agent section '{agent_name}' missing required field '{required}'",
                    errors,
                )

        unknown = set(found_fields) - set(SYNC_AGENT_REQUIRED_FIELDS)
        for field in sorted(unknown):
            warn(
                f"{path}: agent section '{agent_name}' has unknown extension field "
                f"'{field}' (allowed)",
                warnings,
            )

    return errors, warnings


def render(errors: list[str], warnings: list[str]) -> int:
    for w in warnings:
        print(f"[warn] {w}")
    for e in errors:
        print(f"[fail] {e}", file=sys.stderr)
    if errors:
        print(f"\n{len(errors)} validation error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(f"OK — {len(warnings)} warning(s), no errors")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["handover", "sync", "both"])
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    if args.mode == "handover":
        if len(args.paths) != 1:
            print("handover mode expects exactly one path", file=sys.stderr)
            return 2
        e, w = validate_handover(args.paths[0])
        errors.extend(e)
        warnings.extend(w)
    elif args.mode == "sync":
        if len(args.paths) != 1:
            print("sync mode expects exactly one path", file=sys.stderr)
            return 2
        e, w = validate_sync(args.paths[0])
        errors.extend(e)
        warnings.extend(w)
    else:
        if len(args.paths) != 2:
            print("both mode expects exactly two paths: <handover> <sync>", file=sys.stderr)
            return 2
        e, w = validate_handover(args.paths[0])
        errors.extend(e)
        warnings.extend(w)
        e, w = validate_sync(args.paths[1])
        errors.extend(e)
        warnings.extend(w)

    return render(errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
