#!/usr/bin/env bash
# Integrity check for claude-multi-agent-protocol.
# Runs Gates 0, 4, 5 from the bulletproof publishing contract.

set -euo pipefail

cd "$(dirname "$0")/.."

fail=0
green() { printf '\033[32m%s\033[0m\n' "$1"; }
red()   { printf '\033[31m%s\033[0m\n' "$1"; }

echo "[Gate 0] claim-evidence mapping..."
if grep -Eq '^\| .* \| .* \| ☐ \|$' docs/claim-evidence.md; then
  red "FAIL: unverified claims in docs/claim-evidence.md (look for | ☐ | rows)"
  fail=1
else
  green "OK: all claim-table rows marked verified"
fi

echo "[Gate 4] identifier grep (private names / clients / domains)..."
if grep -riE \
  'sirrista|saacash|aman0101|ATATT3|xoxe|xoxp|Olga|Arun|Thinh|Hudson|Anida|Vladimir|Sirish|Om Prakash|dev\.querylah|bhandari\.aman0101|taksha|daxa|querylah' \
  --exclude-dir=.git \
  --exclude=integrity-check.sh \
  --exclude=claim-evidence.md \
  . ; then
  red "FAIL: identifier leak"
  fail=1
else
  green "OK: no private identifiers"
fi

echo "[Gate 5] secret grep..."
hits=$(grep -riE \
  '(sk-[a-zA-Z0-9]{20,}|sk-ant-[a-zA-Z0-9_-]{20,}|ghp_[a-zA-Z0-9]{20,}|xoxb-[0-9a-zA-Z-]{20,}|xoxp-[0-9a-zA-Z-]{20,}|ATATT3[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16}|[A-Z_]+_(KEY|TOKEN|SECRET|PASSWORD)=[^\s]+)' \
  --exclude-dir=.git \
  --exclude-dir=node_modules \
  --exclude='*.env.example' \
  --exclude=integrity-check.sh \
  . || true)
if [[ -n "$hits" ]]; then
  red "FAIL: possible secret(s) detected — review manually:"
  echo "$hits"
  fail=1
else
  green "OK: no secret patterns"
fi

echo "[Artifact-specific] spec docs present..."
for f in docs/protocol-overview.md docs/handover-spec.md docs/sync-spec.md; do
  if [[ ! -f "$f" ]]; then
    red "FAIL: missing $f"
    fail=1
  fi
done
if [[ "$fail" -eq 0 ]]; then
  green "OK: protocol-overview.md + handover-spec.md + sync-spec.md all present"
fi

echo "[Artifact-specific] example files present..."
for f in examples/upstream-repo/HANDOVER.md examples/commons/SYNC.md; do
  if [[ ! -f "$f" ]]; then
    red "FAIL: missing $f"
    fail=1
  fi
done
if [[ -f examples/upstream-repo/HANDOVER.md && -f examples/commons/SYNC.md ]]; then
  green "OK: example HANDOVER.md + SYNC.md present"
fi

echo "[Artifact-specific] HANDOVER example has >=2 entries..."
entry_count=$(grep -cE '^### ' examples/upstream-repo/HANDOVER.md || true)
if [[ "$entry_count" -lt 2 ]]; then
  red "FAIL: HANDOVER example has $entry_count entries, expected >=2"
  fail=1
else
  green "OK: HANDOVER example has $entry_count entries"
fi

echo "[Artifact-specific] SYNC example has >=2 decision-log entries..."
# Count bullet rows under the Decision Log section only.
dec_count=$(awk '
  /^## Decision Log/ { in_sec=1; next }
  /^## / && in_sec { in_sec=0 }
  in_sec && /^- [0-9]{4}-[0-9]{2}-[0-9]{2}/ { count++ }
  END { print count+0 }
' examples/commons/SYNC.md)
if [[ "$dec_count" -lt 2 ]]; then
  red "FAIL: SYNC example has $dec_count decision-log entries, expected >=2"
  fail=1
else
  green "OK: SYNC example has $dec_count decision-log entries"
fi

echo "[Artifact-specific] SYNC example has >=3 agent sections..."
agent_count=$(awk '
  /^## / {
    name=$0
    sub(/^## */, "", name)
    sub(/ .*$/, "", name)
    if (name != "Goal" && name != "Decision" && name != "Conflict" && name != "Stale-section") count++
  }
  END { print count+0 }
' examples/commons/SYNC.md)
if [[ "$agent_count" -lt 3 ]]; then
  red "FAIL: SYNC example has $agent_count agent sections, expected >=3"
  fail=1
else
  green "OK: SYNC example has $agent_count agent sections"
fi

echo "[Artifact-specific] validator passes on examples..."
if ! python3 scripts/validate.py both examples/upstream-repo/HANDOVER.md examples/commons/SYNC.md > /dev/null; then
  red "FAIL: scripts/validate.py reports errors on shipped examples"
  fail=1
else
  green "OK: scripts/validate.py clean against examples"
fi

echo "[Artifact-specific] validator rejects broken HANDOVER (smoke test)..."
tmp=$(mktemp)
cat > "$tmp" <<'EOF'
# Broken HANDOVER

## Queue

### bad-entry-1: Missing status and date

- **from**: SomeAgent
- **for**: any
EOF
if python3 scripts/validate.py handover "$tmp" > /dev/null 2>&1; then
  red "FAIL: validator should have rejected broken HANDOVER but accepted it"
  fail=1
else
  green "OK: validator correctly rejects broken HANDOVER"
fi
rm -f "$tmp"

echo
if [[ "$fail" -ne 0 ]]; then
  red "INTEGRITY CHECK FAILED"
  exit 1
fi
green "ALL GATES GREEN"
