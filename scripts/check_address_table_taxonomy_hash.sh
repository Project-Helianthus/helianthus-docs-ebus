#!/usr/bin/env bash
# check_address_table_taxonomy_hash.sh — Phase C M-C0 hash gate.
#
# Recomputes the SHA-256 over the 256-byte taxonomy + frame-type contract
# + validator contract blocks of architecture/ebus_standard/12-address-table.md
# and compares it to the pinned canonical value.
#
# Hard-fails (exit 1) on mismatch — any edit to those blocks requires
# recompute + pin update in the same PR.
#
# Decision references: AD25, AD26, AD27 of locked plan
# address-table-registry-w19-26 / Phase C / M-C0_DOC_SPEC.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOC_PATH="${REPO_ROOT}/architecture/ebus_standard/12-address-table.md"
EXPECTED_HASH="c19124aca8b42c1dcae659c37e7b21b20a4538dc7bc2bd785b5643b3f70503cc"

if [[ ! -f "${DOC_PATH}" ]]; then
  echo "ERROR: address-table doc not found at ${DOC_PATH}" >&2
  exit 1
fi

# Extract block: from `## 256-Byte Address Taxonomy` (inclusive) to
# `## Hash Contract (taxonomy + frame-type contract)` (exclusive).
# Trailing whitespace stripped per line, exactly one terminal LF.
ACTUAL_HASH="$(
  awk '
    /^## Hash Contract \(taxonomy \+ frame-type contract\)[[:space:]]*$/ {
      inblock = 0
    }
    inblock { print }
    /^## 256-Byte Address Taxonomy[[:space:]]*$/ { inblock = 1; print }
  ' "${DOC_PATH}" \
    | sed -E 's/[[:space:]]+$//' \
    | shasum -a 256 \
    | cut -d' ' -f1
)"

if [[ "${ACTUAL_HASH}" == "${EXPECTED_HASH}" ]]; then
  echo "address-table taxonomy hash OK: ${ACTUAL_HASH}"
  exit 0
fi

cat >&2 <<EOF
ERROR: address-table taxonomy hash mismatch.
  expected: ${EXPECTED_HASH}
  actual:   ${ACTUAL_HASH}

The 256-byte taxonomy / frame-type contract / validator contract blocks
in 12-address-table.md were edited but the pinned hash was not updated.

Resolution: recompute via the awk+sed+shasum snippet at the bottom of
the doc's "Hash Contract (taxonomy + frame-type contract)" section,
then update the "Normalized hash:" line in 12-address-table.md to the
new value. Both must land in the same PR.
EOF
exit 1
