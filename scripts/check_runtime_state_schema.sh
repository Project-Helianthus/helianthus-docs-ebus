#!/usr/bin/env bash
# Validate runtime_state.schema.json against fixtures using
# santhosh-tekuri/jsonschema/cmd/jv. Plan: runtime-state-w19-26.locked AD05/AD22.
#
# Two-stage check per file:
#   1. JSON Schema (jv) — types, ranges, regex, required, enum, format-assert.
#   2. Python post-check — invariants that JSON Schema cannot express cleanly:
#      - AD18 uniqueness: ebus.known_bus_members[].addr must be unique
#        (one cache entry per eBUS address).
#
# CI installs jv via setup-go (see .github/workflows/docs-ci.yml).
# Local invocation: requires `go install github.com/santhosh-tekuri/jsonschema/cmd/jv@v0.7.0`
# (or any tagged release providing the cmd/jv binary).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

schema="runtime-state/runtime_state.schema.json"
positive="runtime-state/examples/positive.json"
negatives=(
  "runtime-state/examples/negative-out-of-range-addr.json"
  "runtime-state/examples/negative-invalid-uuid.json"
  "runtime-state/examples/negative-missing-instance-guid.json"
  "runtime-state/examples/negative-unsupported-schema-version.json"
  "runtime-state/examples/negative-invalid-timestamp.json"
  "runtime-state/examples/negative-duplicate-addr.json"
)

if ! command -v jv >/dev/null 2>&1; then
  echo "==> jv not found on PATH; install with: go install github.com/santhosh-tekuri/jsonschema/cmd/jv@v0.7.0" >&2
  exit 2
fi

echo "==> jv version"
jv --version || true

# Returns 0 if the file passes BOTH jv schema validation AND the AD18 uniqueness
# post-check; non-zero on any failure. Uses python3 for the AD18 check.
validate_one() {
  local file="$1"
  if ! jv -d 2020 -f "${schema}" "${file}" 2>/dev/null; then
    return 1
  fi
  # AD18 uniqueness post-check (JSON Schema 2020-12 cannot express unique-by-key).
  python3 - "${file}" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as fp:
    data = json.load(fp)

members = data.get("ebus", {}).get("known_bus_members") or []
seen = {}
for idx, member in enumerate(members):
    addr = member.get("addr")
    if addr is None:
        continue
    if addr in seen:
        print(
            f"AD18 uniqueness violation in {path}: addr={addr} appears at "
            f"index {seen[addr]} and {idx}; ebus.known_bus_members[].addr "
            "must be unique (one entry per eBUS address).",
            file=sys.stderr,
        )
        sys.exit(1)
    seen[addr] = idx
PY
}

echo "==> validating positive fixture: ${positive}"
if ! validate_one "${positive}"; then
  echo "FAIL: positive fixture rejected" >&2
  exit 1
fi
echo "  OK"

echo "==> validating negative fixtures (must be rejected)"
failed=0
for fixture in "${negatives[@]}"; do
  echo "  ${fixture}"
  if validate_one "${fixture}"; then
    echo "    FAIL: negative fixture was accepted" >&2
    failed=1
  else
    echo "    OK (rejected as expected)"
  fi
done

if [ "${failed}" -ne 0 ]; then
  echo "Runtime-state schema gate FAILED." >&2
  exit 1
fi

echo "==> Runtime-state schema gate passed."
