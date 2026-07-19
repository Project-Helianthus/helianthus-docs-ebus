#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

platform_toolchain_mode="${PLATFORM_TOOLCHAIN_MODE:-supported}"
platform_docs_ebus_repository="${PLATFORM_DOCS_EBUS_REPOSITORY:-Project-Helianthus/helianthus-docs-ebus}"
case "${platform_toolchain_mode}" in
  exact|supported) ;;
  *)
    echo "PLATFORM_TOOLCHAIN_MODE must be exact or supported." >&2
    exit 2
    ;;
esac

echo "==> verify pinned workflow/schema gate tools"
if ! command -v actionlint >/dev/null 2>&1; then
  echo "actionlint v1.7.7 is required: go install github.com/rhysd/actionlint/cmd/actionlint@v1.7.7" >&2
  exit 2
fi
if [ "$(actionlint -version | sed -n '1p')" != "v1.7.7" ]; then
  echo "actionlint must report v1.7.7." >&2
  exit 2
fi
if ! command -v jv >/dev/null 2>&1; then
  echo "jv v0.7.0 is required: go install github.com/santhosh-tekuri/jsonschema/cmd/jv@v0.7.0" >&2
  exit 2
fi
if [ "$(jv --version | sed -n '1p')" != "github.com/santhosh-tekuri/jsonschema/cmd/jv v0.7.0" ]; then
  echo "jv must report v0.7.0." >&2
  exit 2
fi
actionlint .github/workflows/*.yml
echo "Pinned workflow/schema gate tools passed."

echo "==> verify markdown files are present"
count="$(git ls-files '*.md' | wc -l | tr -d ' ')"
if [ "${count}" -eq 0 ]; then
  echo "No markdown files found."
  exit 1
fi
echo "Found ${count} markdown files."

echo "==> check markdown for tabs and trailing spaces"
failed=0
if git grep -nI $'\t' -- '*.md'; then
  echo "Tab characters are not allowed in markdown files."
  failed=1
fi
if git grep -nI -E ' +$' -- '*.md'; then
  echo "Trailing spaces are not allowed in markdown files."
  failed=1
fi
if [ "${failed}" -ne 0 ]; then
  exit 1
fi

echo "==> enforce initiator/target terminology"
python3 - <<'PY'
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

begin_marker = "<!-- legacy-role-mapping:begin -->"
end_marker = "<!-- legacy-role-mapping:end -->"

# Construct legacy terms without spelling them out literally in-repo.
terms = ["m" + "aster", "sl" + "ave"]
pattern = re.compile(r"\b(" + "|".join(map(re.escape, terms)) + r")\b", re.IGNORECASE)

md_files = subprocess.check_output(["git", "ls-files", "*.md"], text=True).splitlines()

def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1

def print_match(file_path: str, text: str, index: int, match_text: str) -> None:
    print(f"{file_path}:{line_number(text, index)}:{match_text}", file=sys.stderr)

failed = False

for file_path in md_files:
    path = pathlib.Path(file_path)
    text = path.read_text(encoding="utf-8")

    # Build allowed regions from legacy-role-mapping markers in this file.
    allowed_ranges: list[tuple[int, int]] = []
    search_start = 0
    while True:
        b = text.find(begin_marker, search_start)
        if b == -1:
            break
        e = text.find(end_marker, b)
        if e == -1:
            break
        allowed_ranges.append((b, e + len(end_marker)))
        search_start = e + len(end_marker)

    for match in pattern.finditer(text):
        in_allowed = any(s <= match.start() < e for s, e in allowed_ranges)
        if not in_allowed:
            if not failed:
                print(
                    "Legacy role terms found outside legacy-role-mapping regions.",
                    file=sys.stderr,
                )
            failed = True
            print_match(file_path, text, match.start(), match.group(0))

if failed:
    sys.exit(1)

print("Terminology gate passed.")
PY

echo "==> private network address gate (docs must use placeholders)"
python3 - <<'PY'
from __future__ import annotations

import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path("scripts").resolve()))
from validate_platform_contracts import _private_network_literals

md_files = subprocess.check_output(["git", "ls-files", "*.md"], text=True).splitlines()
failed = False

for file_path in md_files:
    text = pathlib.Path(file_path).read_text(encoding="utf-8")
    for _, offset in _private_network_literals(text):
        line = text.count("\n", 0, offset) + 1
        print(f"{file_path}:{line}: private network address found (redact and use a placeholder)", file=sys.stderr)
        failed = True

if failed:
    sys.exit(1)
print("Private network gate passed.")
PY

echo "==> check eBUS source-address table"
python3 scripts/check_source_address_table_against_official_specs.py --run-canary
python3 -m pytest -q tests/test_source_address_table_checker.py

echo "==> check cross-runtime platform contracts (MSP-DOCS-CLEAN)"
python3 -m pytest -q tests/test_platform_contracts.py -k trusted_prior_workflow
python3 -m pytest -q tests/test_platform_contracts.py -k 'not trusted_prior_workflow'
python3 -m pytest -q tests/test_synchronized_evidence_contract.py
set --
if [ -n "${PLATFORM_PRIOR_MANIFEST:-}" ]; then
  set -- --prior-manifest "${PLATFORM_PRIOR_MANIFEST}"
fi
python3 scripts/validate_platform_contracts.py \
  --mode repository \
  --docs-ebus-root . \
  --docs-ebus-repository "${platform_docs_ebus_repository}" \
  --enforce-through MSP-DOCS-CLEAN \
  --toolchain-mode "${platform_toolchain_mode}" \
  "$@"

combined_ref_values=(
  "${PLATFORM_DOCS_EEBUS_ROOT:-}"
  "${PLATFORM_EEBUSREG_ROOT:-}"
  "${PLATFORM_DOCS_EBUS_REF:-}"
  "${PLATFORM_DOCS_EEBUS_REF:-}"
  "${PLATFORM_EEBUSREG_REF:-}"
  "${PLATFORM_PRIOR_MANIFEST:-}"
)
combined_ref_requested=false
for value in \
  "${PLATFORM_DOCS_EEBUS_ROOT:-}" \
  "${PLATFORM_EEBUSREG_ROOT:-}" \
  "${PLATFORM_DOCS_EBUS_REF:-}" \
  "${PLATFORM_DOCS_EEBUS_REF:-}" \
  "${PLATFORM_EEBUSREG_REF:-}"; do
  if [ -n "${value}" ]; then
    combined_ref_requested=true
  fi
done
if [ "${combined_ref_requested}" = true ]; then
  for value in "${combined_ref_values[@]}"; do
    test -n "${value}"
  done
  python3 scripts/validate_platform_combined_ref.py \
    --docs-ebus-root . \
    --docs-eebus-root "${PLATFORM_DOCS_EEBUS_ROOT}" \
    --eebusreg-root "${PLATFORM_EEBUSREG_ROOT}" \
    --docs-ebus-ref "${PLATFORM_DOCS_EBUS_REF}" \
    --docs-eebus-ref "${PLATFORM_DOCS_EEBUS_REF}" \
    --eebusreg-ref "${PLATFORM_EEBUSREG_REF}" \
    --prior-manifest "${PLATFORM_PRIOR_MANIFEST}" \
    --enforce-through MSP-DOCS-CLEAN \
    --toolchain-mode "${platform_toolchain_mode}"
fi

echo "==> check eBUS address-table taxonomy + frame-type contract hash (Phase C M-C0)"
bash scripts/check_address_table_taxonomy_hash.sh

echo "==> check runtime_state.json schema (runtime-state-w19-26 M0_DOC_GATE)"
bash scripts/check_runtime_state_schema.sh

echo "==> check deployment source-address wording"
python3 - <<'PY'
from __future__ import annotations

import pathlib
import sys

path = pathlib.Path("deployment/full-stack.md")
text = path.read_text(encoding="utf-8")
lower = text.lower()

forbidden = [
    "gentle-join",
    "gentle join",
    "enables **gentle-join**",
    "asks the proxy to select a free initiator",
    "reuses the persisted source address",
    "promote source_addr.last",
]
required = [
    "gateway default source-selection policy",
    "selects and validates an admitted source",
    "rollback/migration input only",
    "must not be promoted into active source authority",
]

failed = False
for phrase in forbidden:
    if phrase in lower:
        print(f"{path}: legacy source-address wording remains: {phrase}", file=sys.stderr)
        failed = True

for phrase in required:
    if phrase not in lower:
        print(f"{path}: required source-address wording missing: {phrase}", file=sys.stderr)
        failed = True

if failed:
    sys.exit(1)
print("Deployment source-address wording gate passed.")
PY

echo "==> check NM 07FE/07FF service names"
python3 - <<'PY'
from __future__ import annotations

import pathlib
import sys

checks = {
    "architecture/nm-model.md": [
        "`07 FE` | Inquiry of Existence",
        "`07 FF` | Sign of Life",
        "`07 FE` is Inquiry of Existence. `07 FF` is Sign of Life.",
    ],
    "architecture/nm-discovery.md": [
        "### 07 FF (Sign of Life Broadcast) -- Not Discovery",
    ],
    "architecture/nm-participant-policy.md": [
        "### 07 FF (Sign of Life) -- Optional-Later",
        "`07 FF` (Sign of Life) broadcasts originated by Helianthus",
    ],
}

for file_path, required_fragments in checks.items():
    text = pathlib.Path(file_path).read_text(encoding="utf-8")
    for fragment in required_fragments:
        if fragment not in text:
            print(f"{file_path}: missing required fragment: {fragment}", file=sys.stderr)
            sys.exit(1)
    forbidden = [
        "07 FF (QueryExistence",
        "`07 FF` | QueryExistence",
        "`07 FF` QueryExistence",
        "`07 FF` (QueryExistence)",
    ]
    for fragment in forbidden:
        if fragment in text:
            print(f"{file_path}: stale 07FF QueryExistence text: {fragment}", file=sys.stderr)
            sys.exit(1)

print("NM 07FE/07FF service name gate passed.")
PY
