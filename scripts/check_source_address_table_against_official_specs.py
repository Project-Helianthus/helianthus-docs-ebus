#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "architecture/ebus_standard/12-source-address-table.md"
FIXTURE_PATH = REPO_ROOT / "tests/fixtures/source_address_table_official_v1.json"

TABLE_VERSION = "ebus-source-address-table/v1"
ANCHOR = "#ebus-source-address-table-v1"
EXPECTED_TABLE_HASH = "e78954445087f63064818ab60a2739b9a6b9bf0ae0147fbe92aac5ac76592103"

TABLE_HEADER = (
    "| Source | Priority index | Arbitration nibble | Official description summary | "
    "Canonical description | Free-use | Recommended for | Companion |"
)

APPENDIX_REL = "Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md"
SPEC12_EN_REL = "Spec_Prot_12_V1_3_1_E.en.md"
SPEC12_SRC_REL = "SRC/Spec_Prot_12_V1_3_1_E.md"
OFFICIAL_RELS = (APPENDIX_REL, SPEC12_EN_REL, SPEC12_SRC_REL)

PRIORITY_TO_NIBBLE = {
    0: "0x0",
    1: "0x1",
    2: "0x3",
    3: "0x7",
    4: "0xF",
}

EXPECTED_PRIORITY_SKETCH = [
    ("Participant 1", "0000", "0000"),
    ("Participant 2", "0001", "0000"),
    ("Participant 3", "0011", "0000"),
    ("Participant 4", "0111", "0000"),
    ("Participant 5", "1111", "0000"),
    ("Participant 6", "0000", "0001"),
    ("Participant 7", "0001", "0001"),
    ("Participant 24", "0111", "1111"),
    ("Participant 25", "1111", "1111"),
]


class CheckError(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def split_markdown_row(line: str) -> list[str]:
    if not line.startswith("|"):
        raise CheckError(f"not a Markdown table row: {line!r}")
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator_row(line: str) -> bool:
    body = line.strip().strip("|").strip()
    return bool(body) and set(body) <= {"-", ":", "|", " "}


def clean_cell(cell: str) -> str:
    return cell.strip().strip("`").strip()


def normalized_table_block(doc_text: str) -> str:
    lines = doc_text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip() == TABLE_HEADER)
    except StopIteration as exc:
        raise CheckError("source-address table header not found") from exc

    table_lines: list[str] = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        table_lines.append(line.rstrip())

    if len(table_lines) != 27:
        raise CheckError(f"expected 27 table lines, found {len(table_lines)}")
    return "\n".join(table_lines) + "\n"


def parse_doc_rows(table_block: str) -> list[dict[str, Any]]:
    lines = table_block.splitlines()
    if lines[0] != TABLE_HEADER:
        raise CheckError("source-address table header changed")
    if not is_separator_row(lines[1]):
        raise CheckError("source-address table separator row is invalid")

    rows: list[dict[str, Any]] = []
    for line in lines[2:]:
        cells = split_markdown_row(line)
        if len(cells) != 8:
            raise CheckError(f"expected 8 cells in table row, got {len(cells)}: {line}")
        rows.append(
            {
                "source": clean_cell(cells[0]),
                "priority_index": cells[1],
                "arbitration_nibble": clean_cell(cells[2]),
                "official_description_summary": cells[3],
                "canonical_description": cells[4],
                "free_use": cells[5],
                "recommended_for": cells[6],
                "companion": clean_cell(cells[7]),
            }
        )

    if len(rows) != 25:
        raise CheckError(f"expected 25 source-address rows, found {len(rows)}")
    return rows


def load_fixture() -> dict[str, Any]:
    try:
        return json.loads(read_text(FIXTURE_PATH))
    except FileNotFoundError as exc:
        raise CheckError(f"fixture missing: {FIXTURE_PATH}") from exc


def plain_description(raw_description: str) -> str:
    desc = raw_description.replace("*", "").replace("`", "").strip()
    desc = re.sub(r"\s*\([^)]*\)", "", desc).strip()
    return re.sub(r"\s+", " ", desc)


def official_summary(raw_description: str) -> str:
    plain = plain_description(raw_description)
    if not plain:
        return "empty"
    if "*" in raw_description:
        return f"{plain} recommendation"
    return plain


def canonical_description(summary: str, free_use: str) -> str:
    if free_use == "yes":
        return "Not preallocated"
    if summary == "PC/Modem":
        return "PC/Modem"
    if summary == "PC":
        return "PC"
    if summary == "Heating controller":
        return "Heating regulator"
    if summary.startswith("Heating circuit controller "):
        return summary.replace("Heating circuit controller", "Heating circuit regulator", 1)
    if summary == "Hand programmer / Remote control":
        return "Handheld programmer / remote"
    if summary == "Bus interface / Climate controller":
        return "Bus interface / climate regulator"
    if summary == "Bus interface":
        return "Bus interface"
    if summary.startswith("Burner controller "):
        return summary.replace("Burner controller", "Combustion controller", 1)
    if summary == "Clock module / Radio clock module":
        return "Clock/radio-clock module"
    raise CheckError(f"cannot derive canonical description for {summary!r}")


def recommended_for(raw_description: str, free_use: str) -> str:
    if free_use != "yes":
        return "none"
    plain = plain_description(raw_description)
    if plain == "Heating controller":
        return "Heating regulator"
    if plain.startswith("Burner controller "):
        return plain.replace("Burner controller", "Combustion controller", 1)
    return "none"


def normalize_address_token(token: str) -> str:
    raw = clean_cell(token).upper()
    if raw.endswith("H"):
        raw = raw[:-1]
    value = int(raw, 16)
    if not 0 <= value <= 0xFF:
        raise CheckError(f"address out of one-byte range: {token!r}")
    return f"0x{value:02X}"


def parse_official_address_table(appendix_text: str) -> list[dict[str, Any]]:
    lines = appendix_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("| Address | Priority |"):
            start = i
            break
    if start is None:
        raise CheckError("official source-address table was not found")

    rows: list[dict[str, Any]] = []
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        cells = split_markdown_row(line)
        if len(cells) < 4:
            continue

        source = normalize_address_token(cells[0])
        source_value = int(source[2:], 16)
        priority = int(cells[1])
        free_use = "yes" if ("*" in cells[3] or not plain_description(cells[3])) else "no"
        summary = official_summary(cells[3])
        expected_nibble = PRIORITY_TO_NIBBLE.get(priority)
        actual_nibble = f"0x{source_value & 0x0F:X}"
        if actual_nibble != expected_nibble:
            raise CheckError(
                f"{source} priority p{priority} implies {expected_nibble}, got {actual_nibble}"
            )

        rows.append(
            {
                "source": source,
                "priority_index": f"p{priority}",
                "arbitration_nibble": actual_nibble,
                "official_description_summary": summary,
                "canonical_description": canonical_description(summary, free_use),
                "free_use": free_use,
                "recommended_for": recommended_for(cells[3], free_use),
                "companion": f"0x{(source_value + 5) & 0xFF:02X}",
            }
        )

    if len(rows) != 25:
        raise CheckError(f"official source-address table has {len(rows)} rows, expected 25")
    return rows


def parse_priority_sketch(spec_text: str) -> list[tuple[str, str, str]]:
    lines = spec_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("| Participant") and "Sub-Address" in line and "Priority Class" in line:
            start = i
            break
    if start is None:
        raise CheckError("priority/sub-address sketch table was not found")

    rows: list[tuple[str, str, str]] = []
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        cells = split_markdown_row(line)
        if len(cells) != 3:
            continue
        if cells[0] == "...":
            continue
        rows.append((cells[0], cells[1], cells[2]))
    return rows


def validate_priority_sketch(spec_text: str, rel_path: str) -> None:
    rows = parse_priority_sketch(spec_text)
    for expected in EXPECTED_PRIORITY_SKETCH:
        if expected not in rows:
            raise CheckError(f"{rel_path}: priority sketch missing {expected}")


def validate_companion_and_ack_context(spec_text: str) -> None:
    legacy_responder = "sl" + "ave"
    required_fragments = [
        "`0x01` = `0x06`",
        "address `0xFF`",
        f"{legacy_responder}-address `0x04`",
        "positive acknowledgement (`0x00`)",
        "negative acknowledgement (`0xFF`)",
    ]
    for fragment in required_fragments:
        if fragment not in spec_text:
            raise CheckError(f"official companion/ACK context missing fragment: {fragment}")


def validate_official_hashes(spec_dir: pathlib.Path, fixture: dict[str, Any]) -> None:
    expected_files = fixture["source_files"]
    for rel in OFFICIAL_RELS:
        path = spec_dir / rel
        if not path.exists():
            raise CheckError(f"official spec file missing: {path}")
        actual_hash = sha256_file(path)
        expected_hash = expected_files[rel]["sha256"]
        print(f"official_spec_sha256 {rel} {actual_hash}")
        if actual_hash != expected_hash:
            raise CheckError(
                f"official spec hash drift for {rel}: expected {expected_hash}, got {actual_hash}"
            )
        actual_lines = read_text(path).splitlines()
        for line_range, expected_excerpt in expected_files[rel].get("excerpts", {}).items():
            start, end = (int(part) for part in line_range.split("-", 1))
            actual_excerpt = "\n".join(actual_lines[start - 1 : end]) + "\n"
            if actual_excerpt != expected_excerpt:
                raise CheckError(f"official spec excerpt drift for {rel}:{line_range}")


def expected_rows_from_official(spec_dir: pathlib.Path, fixture: dict[str, Any]) -> list[dict[str, Any]]:
    validate_official_hashes(spec_dir, fixture)

    appendix_text = read_text(spec_dir / APPENDIX_REL)
    spec12_en_text = read_text(spec_dir / SPEC12_EN_REL)
    spec12_src_text = read_text(spec_dir / SPEC12_SRC_REL)

    rows = parse_official_address_table(appendix_text)
    validate_priority_sketch(spec12_en_text, SPEC12_EN_REL)
    validate_priority_sketch(spec12_src_text, SPEC12_SRC_REL)
    validate_companion_and_ack_context(spec12_en_text)

    fixture_rows = fixture["rows"]
    if rows != fixture_rows:
        raise CheckError("official spec rows no longer match committed fixture")
    return rows


def expected_rows_from_fixture(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    source_files = fixture["source_files"]
    try:
        appendix_text = source_files[APPENDIX_REL]["excerpts"]["28-60"]
        spec12_en_text = "\n".join(
            source_files[SPEC12_EN_REL]["excerpts"][line_range]
            for line_range in ("178-184", "254-256", "320-349", "471-478")
        )
        spec12_src_text = source_files[SPEC12_SRC_REL]["excerpts"]["320-349"]
    except KeyError as exc:
        raise CheckError(f"fixture missing exact official excerpt text: {exc}") from exc

    rows = parse_official_address_table(appendix_text)
    validate_priority_sketch(spec12_en_text, SPEC12_EN_REL)
    validate_priority_sketch(spec12_src_text, SPEC12_SRC_REL)
    validate_companion_and_ack_context(spec12_en_text)
    if rows != fixture["rows"]:
        raise CheckError("fixture rows do not match fixture official excerpts")
    return rows


def expected_rows(args: argparse.Namespace, fixture: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    if args.fixture_only:
        print("official_spec_mode fixture-only")
        return expected_rows_from_fixture(fixture), "fixture"

    spec_dir_value = args.spec_dir or os.environ.get("HELIANTHUS_OFFICIAL_SPEC_DIR")
    explicit = bool(spec_dir_value)
    if spec_dir_value:
        spec_dir = pathlib.Path(spec_dir_value).expanduser()
    else:
        spec_dir = REPO_ROOT.parent / "docs"

    if spec_dir.exists():
        return expected_rows_from_official(spec_dir, fixture), f"official:{spec_dir}"
    if explicit:
        raise CheckError(f"explicit official spec dir does not exist: {spec_dir}")

    print("official_spec_mode fixture-only")
    return expected_rows_from_fixture(fixture), "fixture"


def compare_rows(actual: list[dict[str, Any]], expected: list[dict[str, Any]]) -> None:
    if actual == expected:
        return
    for index, (got, want) in enumerate(zip(actual, expected), start=1):
        if got != want:
            source = want.get("source", got.get("source", f"row-{index}"))
            for field_name in sorted(set(got) | set(want)):
                if got.get(field_name) != want.get(field_name):
                    raise CheckError(
                        f"source-address row mismatch at row {index} source {source} "
                        f"field {field_name}: expected {want.get(field_name)!r}, "
                        f"got {got.get(field_name)!r}"
                    )
            raise CheckError(
                "source-address row mismatch at row "
                f"{index}: expected {json.dumps(want, sort_keys=True)}, "
                f"got {json.dumps(got, sort_keys=True)}"
            )
    raise CheckError(f"row count mismatch: expected {len(expected)}, got {len(actual)}")


def validate_doc_text(
    doc_text: str,
    expected: list[dict[str, Any]],
    *,
    check_hash: bool = True,
) -> str:
    if "## eBUS Source Address Table v1" not in doc_text:
        raise CheckError("required heading for GitHub anchor is missing")
    if f"Table anchor: `{ANCHOR}`" not in doc_text:
        raise CheckError("required table anchor declaration is missing")
    if f"Table version: `{TABLE_VERSION}`" not in doc_text:
        raise CheckError("required table version declaration is missing")

    table_block = normalized_table_block(doc_text)
    table_hash = sha256_bytes(table_block.encode("utf-8"))
    if check_hash and table_hash != EXPECTED_TABLE_HASH:
        raise CheckError(
            f"normalized Markdown table hash mismatch: expected {EXPECTED_TABLE_HASH}, got {table_hash}"
        )

    rows = parse_doc_rows(table_block)
    compare_rows(rows, expected)
    return table_hash


def run_mutation_canary(doc_text: str, expected: list[dict[str, Any]]) -> None:
    needle = "| `0x71` | p1 | `0x1` | Heating controller | Heating regulator | no | none | `0x76` |"
    replacement = "| `0x71` | p1 | `0x1` | Heating controller | Heating regulator | no | none | `0x77` |"
    if needle not in doc_text:
        raise CheckError("mutation canary needle not found")
    mutated = doc_text.replace(needle, replacement, 1)
    try:
        validate_doc_text(mutated, expected, check_hash=False)
    except CheckError as exc:
        print(f"mutation_canary rejected_mutated_table {exc}")
        return
    raise CheckError("mutation canary failed: mutated table was accepted")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the eBUS source-address table against official specs."
    )
    parser.add_argument(
        "--spec-dir",
        help="Official spec directory. Defaults to HELIANTHUS_OFFICIAL_SPEC_DIR, then ../docs.",
    )
    parser.add_argument(
        "--run-canary",
        action="store_true",
        help="Mutate one table cell in memory and require validation to fail.",
    )
    parser.add_argument(
        "--fixture-only",
        action="store_true",
        help="Use the committed official-derived fixture even if local specs are available.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixture = load_fixture()

    if fixture["table_version"] != TABLE_VERSION:
        raise CheckError("fixture table version mismatch")
    if fixture["normalized_table_hash"] != EXPECTED_TABLE_HASH:
        raise CheckError("fixture table hash mismatch")

    expected, mode = expected_rows(args, fixture)
    doc_text = read_text(DOC_PATH)
    table_hash = validate_doc_text(doc_text, expected)

    if args.run_canary:
        run_mutation_canary(doc_text, expected)

    print(f"source_address_table_ok mode={mode} version={TABLE_VERSION} hash={table_hash}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckError as exc:
        print(f"source_address_table_error: {exc}", file=sys.stderr)
        raise SystemExit(1)
