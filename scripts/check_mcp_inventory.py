#!/usr/bin/env python3
"""Compare scoped gateway discovery output with the documentation inventory."""

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("name", "surface", "registration_profile", "availability_condition",
          "implementation_source")
SURFACES = {"ordinary", "operator", "operator_source"}


def marked_rows(text, marker, header):
    start, end = f"\n{marker}:start\n", f"\n{marker}:end\n"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"missing or duplicate {marker} table")
    body = text.split(start)[1].split(end)[0].strip().splitlines()
    if body[:2] != header:
        raise ValueError(f"invalid {marker} header")
    rows = []
    for line in body[2:]:
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if not line.startswith("| ") or not line.endswith(" |") or not all(cells):
            raise ValueError(f"invalid {marker} row")
        rows.append(cells)
    if not rows:
        raise ValueError(f"empty {marker} table")
    return rows


def classification(profile):
    return "target" if profile.startswith("target_") else "implemented"


def documented_rows(text):
    profiles = {}
    for profile, surface, status in marked_rows(text, "mcp-profiles", [
            "| Profile | Surface | Classification |", "|---|---|---|"]):
        if profile in profiles or surface not in SURFACES or status != classification(profile):
            raise ValueError("invalid profile or stale target classification")
        profiles[profile] = surface
    rows = []
    for name, surface, names, condition, source, status in marked_rows(
            text, "mcp-inventory", [
                "| Tool | Surface | Profiles | Availability condition | Implementation source | Classification |",
                "|---|---|---|---|---|---|"]):
        for profile in names.split(", "):
            if profiles.get(profile) != surface or status != classification(profile):
                raise ValueError("unknown profile, moved surface or stale target classification")
            rows.append(dict(zip(FIELDS, (name, surface, profile, condition, source))))
    return profiles, rows


def unique_rows(rows, profiles):
    result = {}
    if not isinstance(rows, list) or not rows:
        raise ValueError("tools must be a nonempty array")
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(FIELDS):
            raise ValueError("invalid tool schema")
        if any(not isinstance(value, str) or not value.strip() for value in row.values()):
            raise ValueError("tool fields must be nonempty strings")
        if profiles.get(row["registration_profile"]) != row["surface"]:
            raise ValueError("unknown profile or surface")
        key = tuple(row[field] for field in FIELDS[:3])
        if key in result:
            raise ValueError("duplicate tool key")
        result[key] = tuple(row[field] for field in FIELDS)
    return result


def validate(inventory, text):
    if (not isinstance(inventory, dict) or set(inventory) != {"schema_version", "tools"}
            or type(inventory["schema_version"]) is not int or inventory["schema_version"] != 1):
        raise ValueError("invalid inventory schema version")
    profiles, docs = documented_rows(text)
    actual = unique_rows(inventory["tools"], profiles)
    expected = unique_rows(docs, profiles)
    if actual != expected:
        raise ValueError("inventory parity failed: added, removed or changed scoped tool")
    section = text.split("## G5 runtime lifecycle MCP contract (D4)", 1)[1].split("## ", 1)[0]
    if re.search(r"pending\s+(?:\*\*)?implementation|not part of the implemented", section, re.I):
        raise ValueError("runtime tools restored to pending status")
    if "**implemented**" not in section:
        raise ValueError("runtime implementation status missing")
    return len(actual)


def no_duplicate_members(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--docs", type=Path, default=ROOT / "api/mcp.md")
    args = parser.parse_args()
    try:
        inventory = json.loads(args.inventory.read_text(), object_pairs_hook=no_duplicate_members)
        count = validate(inventory, args.docs.read_text())
    except (OSError, ValueError, KeyError, IndexError) as error:
        print(f"MCP inventory: {error}", file=sys.stderr)
        return 1
    print(f"MCP inventory parity passed: {count} scoped entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
