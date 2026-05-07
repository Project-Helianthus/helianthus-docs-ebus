#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

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

echo "==> private IPv4 address gate (docs must use placeholders)"
python3 - <<'PY'
from __future__ import annotations

import ipaddress
import pathlib
import re
import subprocess
import sys

md_files = subprocess.check_output(["git", "ls-files", "*.md"], text=True).splitlines()
ipv4_re = re.compile(r"\\b(?:(?:\\d{1,3})\\.){3}(?:\\d{1,3})\\b")

PRIVATE_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),  # CGNAT
    ipaddress.ip_network("169.254.0.0/16"),  # link-local
]

def is_private_ipv4(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    if addr.version != 4:
        return False
    return any(addr in net for net in PRIVATE_NETS)

failed = False

for file_path in md_files:
    text = pathlib.Path(file_path).read_text(encoding="utf-8")
    for match in ipv4_re.finditer(text):
        ip = match.group(0)
        if not is_private_ipv4(ip):
            continue
        line = text.count("\n", 0, match.start()) + 1
        print(f"{file_path}:{line}: private IPv4 address found (redact and use a placeholder)", file=sys.stderr)
        failed = True

if failed:
    sys.exit(1)
print("Private IPv4 gate passed.")
PY

echo "==> check eBUS source-address table"
python3 scripts/check_source_address_table_against_official_specs.py --run-canary
python3 -m pytest -q tests/test_source_address_table_checker.py

echo "==> check eBUS address-table taxonomy + frame-type contract hash (Phase C M-C0)"
bash scripts/check_address_table_taxonomy_hash.sh

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
