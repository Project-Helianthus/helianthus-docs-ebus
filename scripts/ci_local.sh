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

allowed_file = pathlib.Path("protocols/ebus-overview.md")
begin_marker = "<!-- legacy-role-mapping:begin -->"
end_marker = "<!-- legacy-role-mapping:end -->"

# Construct legacy terms without spelling them out literally in-repo.
terms = ["m" + "aster", "sl" + "ave"]
pattern = re.compile(r"\\b(" + "|".join(map(re.escape, terms)) + r")\\b", re.IGNORECASE)

md_files = subprocess.check_output(["git", "ls-files", "*.md"], text=True).splitlines()

def line_number(text: str, index: int) -> int:
    return text.count("\\n", 0, index) + 1

def print_match(file_path: str, text: str, index: int, match_text: str) -> None:
    print(f"{file_path}:{line_number(text, index)}:{match_text}", file=sys.stderr)

if not allowed_file.exists():
    print(f"Expected {allowed_file} to exist.", file=sys.stderr)
    sys.exit(1)

allowed_text = allowed_file.read_text(encoding="utf-8")
begin_index = allowed_text.find(begin_marker)
end_index = allowed_text.find(end_marker)
if begin_index == -1 or end_index == -1 or end_index <= begin_index:
    print(
        "Missing or malformed legacy-role-mapping markers in protocols/ebus-overview.md.",
        file=sys.stderr,
    )
    sys.exit(1)

allowed_region_start = begin_index
allowed_region_end = end_index

failed = False

for file_path in md_files:
    path = pathlib.Path(file_path)
    text = path.read_text(encoding="utf-8")
    for match in pattern.finditer(text):
        if path != allowed_file:
            if not failed:
                print(
                    "Legacy role terms must not appear outside protocols/ebus-overview.md.",
                    file=sys.stderr,
                )
            failed = True
            print_match(file_path, text, match.start(), match.group(0))

for match in pattern.finditer(allowed_text):
    if not (allowed_region_start <= match.start() < allowed_region_end):
        if not failed:
            print(
                "Legacy role terms must only appear inside the legacy-role-mapping note.",
                file=sys.stderr,
            )
        failed = True
        print_match(str(allowed_file), allowed_text, match.start(), match.group(0))

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

def is_private(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return addr.version == 4 and (addr.is_private or addr.is_link_local)

failed = False

for file_path in md_files:
    text = pathlib.Path(file_path).read_text(encoding="utf-8")
    for match in ipv4_re.finditer(text):
        ip = match.group(0)
        if not is_private(ip):
            continue
        line = text.count("\n", 0, match.start()) + 1
        print(f"{file_path}:{line}: private IPv4 address found (redact and use a placeholder)", file=sys.stderr)
        failed = True

if failed:
    sys.exit(1)
print("Private IPv4 gate passed.")
PY
