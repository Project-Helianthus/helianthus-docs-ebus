#!/usr/bin/env bash
# Validate runtime_state.schema.json against fixtures using
# santhosh-tekuri/jsonschema/cmd/jv. Plan: runtime-state-w19-26.locked AD05/AD22.
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
)

if ! command -v jv >/dev/null 2>&1; then
  echo "==> jv not found on PATH; install with: go install github.com/santhosh-tekuri/jsonschema/cmd/jv@v0.7.0" >&2
  exit 2
fi

echo "==> jv version"
jv --version || true

echo "==> validating positive fixture: ${positive}"
if ! jv -d 2020 "${schema}" "${positive}"; then
  echo "FAIL: positive fixture rejected by schema" >&2
  exit 1
fi
echo "  OK"

echo "==> validating negative fixtures (must be rejected)"
failed=0
for fixture in "${negatives[@]}"; do
  echo "  ${fixture}"
  if jv -d 2020 "${schema}" "${fixture}" 2>/dev/null; then
    echo "    FAIL: negative fixture was accepted by schema" >&2
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
