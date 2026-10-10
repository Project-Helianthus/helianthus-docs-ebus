"""Mechanical checks for the public B524 register name correspondence fixture.

The correspondence fixture layers observed naming annotations (Vaillant
friendly/family names, myVaillant names, ebusd names) onto the existing
canonical `b524-op02-register-names.csv` catalog. It must never silently
drift from that catalog's `name` column, and its own keys must stay unique.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "protocols" / "vaillant" / "fixtures"
CANONICAL = FIXTURES / "b524-op02-register-names.csv"
CORRESPONDENCE = FIXTURES / "b524-register-name-correspondence.csv"

EXPECTED_COLUMNS = [
    "opcode",
    "group",
    "register",
    "name",
    "vaillant_friendly_name",
    "vaillant_name_vrc720",
    "vaillant_name_vrc700",
    "myvaillant_name_vrc720",
    "myvaillant_name_vrc700",
    "ebusd_name",
]


def _rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8")))


def test_correspondence_fixture_has_expected_columns() -> None:
    with CORRESPONDENCE.open(encoding="utf-8") as handle:
        header = next(csv.reader(handle))
    assert header == EXPECTED_COLUMNS


def test_correspondence_keys_are_unique() -> None:
    rows = _rows(CORRESPONDENCE)
    keys = [(row["opcode"], row["group"], row["register"]) for row in rows]
    assert len(set(keys)) == len(keys)
    assert len(rows) > 0


def test_correspondence_name_column_matches_canonical_op02_catalog() -> None:
    canonical = {
        (row["opcode"], row["group"], row["register"]): row["name"]
        for row in _rows(CANONICAL)
    }
    correspondence = _rows(CORRESPONDENCE)
    op02_rows = [row for row in correspondence if row["opcode"] == "0x02"]

    # Every OP02 key in the canonical catalog must appear, unchanged, in the
    # correspondence fixture: the correspondence fixture must not widen,
    # narrow, or relabel the canonical presentation name.
    assert len(op02_rows) == len(canonical)
    for row in op02_rows:
        key = (row["opcode"], row["group"], row["register"])
        assert key in canonical, f"{key} is not in the canonical OP02 catalog"
        assert row["name"] == canonical[key], (
            f"{key}: correspondence name {row['name']!r} != "
            f"canonical name {canonical[key]!r}"
        )


def test_correspondence_fixture_is_data_only() -> None:
    # CC0 boundary: the fixture is plain observed-name data, not an
    # application instruction, command, or CLI argument.
    text = CORRESPONDENCE.read_text(encoding="utf-8")
    for banned in ("--", "`$", "subprocess", "os.system", "import "):
        assert banned not in text
