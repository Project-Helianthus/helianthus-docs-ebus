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


def test_correspondence_ebusd_names_are_not_duplicated_within_an_opcode() -> None:
    # A literal ebusd name is a claim that this project mapped that public
    # ebusd configuration name onto a specific (group, register) selector.
    # The same literal name must not be mapped onto more than one selector
    # within the same opcode -- that pattern is exactly the false-positive
    # shape found and removed from GG00 RR0015 (`HwcParallelLoading`,
    # belongs only to RR000A) and GG02 RR0001 (`Hc{hc}CircuitType`, belongs
    # only to RR0002).
    rows = _rows(CORRESPONDENCE)
    by_opcode: dict[str, dict[str, set[tuple[str, str]]]] = {}
    for row in rows:
        ebusd_name = row["ebusd_name"].strip()
        if not ebusd_name:
            continue
        opcode_map = by_opcode.setdefault(row["opcode"], {})
        for token in (part.strip() for part in ebusd_name.split("|")):
            if not token:
                continue
            opcode_map.setdefault(token, set()).add((row["group"], row["register"]))

    duplicates = [
        (opcode, token, sorted(keys))
        for opcode, names in by_opcode.items()
        for token, keys in names.items()
        if len(keys) > 1
    ]
    assert duplicates == [], (
        "ebusd name(s) mapped onto more than one (group, register) within "
        f"the same opcode: {duplicates}"
    )


ANNOTATION_COLUMNS = EXPECTED_COLUMNS[4:]

# A cell lists more than one value only when each value is an observed name
# of that same register for that column. Every such cell is pinned here, so
# a regenerated fixture cannot quietly attach the name of a derived value,
# an aggregate or a composite field to a register again.
MULTI_VALUED_CELLS = {
    ("0x02", "0x00", "0x008B", "vaillant_friendly_name"): (
        "Max Flow Set Point Heat Pump",
        "Max Flow Set Point Heat Pump CH",
    ),
    ("0x02", "0x01", "0x0008", "vaillant_friendly_name"): (
        "Current target flow temperature",
        "Current target flow temperature heating",
    ),
    ("0x02", "0x02", "0x0002", "vaillant_name_vrc720"): (
        "circuit_type",
        "circuit_type_of_mixed_circuit_external",
    ),
    ("0x02", "0x02", "0x0002", "vaillant_name_vrc700"): (
        "circuit_type",
        "circuit_type_of_mixed_circuit_external",
    ),
}


def _cell_values(row: dict[str, str], column: str) -> tuple[str, ...]:
    return tuple(row[column].split(" | ")) if row[column] else ()


def test_correspondence_cells_use_only_the_canonical_separator() -> None:
    # Values are separated by exactly " | ". Any other use of the pipe
    # character would make a multi-valued cell look single-valued and slip
    # past the checks below, so it is rejected outright.
    for row in _rows(CORRESPONDENCE):
        for column in ANNOTATION_COLUMNS:
            for value in _cell_values(row, column):
                where = f"{row['opcode']}/{row['group']}/{row['register']} {column}"
                assert "|" not in value, f"{where}: non-canonical separator in {row[column]!r}"
                assert value and value == value.strip(), f"{where}: malformed value in {row[column]!r}"


def test_correspondence_multi_valued_cells_are_exactly_the_pinned_set() -> None:
    found = {}
    for row in _rows(CORRESPONDENCE):
        for column in ANNOTATION_COLUMNS:
            values = _cell_values(row, column)
            if len(values) > 1:
                key = (row["opcode"], row["group"], row["register"], column)
                found[key] = values
    assert found == MULTI_VALUED_CELLS


def test_correspondence_values_are_not_repeated_within_a_cell() -> None:
    # The fixture records each name once, in one spelling: values that differ
    # only in letter case, spacing or punctuation are the same name (see the
    # "Register name correspondence fixture" section of the register map).
    for row in _rows(CORRESPONDENCE):
        for column in ANNOTATION_COLUMNS:
            values = list(_cell_values(row, column))
            folded = ["".join(ch for ch in value.lower() if ch.isalnum()) for value in values]
            assert len(set(folded)) == len(folded), (
                f"{row['opcode']}/{row['group']}/{row['register']} {column}: "
                f"spelling variants of one name listed as separate values: {values}"
            )


def test_correspondence_vaillant_names_are_attached_to_one_register_per_family() -> None:
    for column in ("vaillant_name_vrc720", "vaillant_name_vrc700"):
        # Partitioned by opcode: OP=0x02 and OP=0x06 are independent
        # namespaces, so the same name may be recorded once in each.
        seen: dict[tuple[str, str], tuple[str, str]] = {}
        for row in _rows(CORRESPONDENCE):
            here = (row["group"], row["register"])
            for value in _cell_values(row, column):
                key = (row["opcode"], value)
                assert seen.setdefault(key, here) == here, (
                    f"{column}: {value!r} (opcode {row['opcode']}) is attached to both "
                    f"{seen[key]} and {here}"
                )


def test_correspondence_fixture_is_data_only() -> None:
    # CC0 boundary: the fixture is plain observed-name data, not an
    # application instruction, command, or CLI argument.
    text = CORRESPONDENCE.read_text(encoding="utf-8")
    for banned in ("--", "`$", "subprocess", "os.system", "import "):
        assert banned not in text
