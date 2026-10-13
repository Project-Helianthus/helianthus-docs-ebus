"""Mechanical checks for the public B509 register name correspondence fixture.

The fixture maps every entry of the B509 boiler and heat pump register maps to
a canonical name and, where known, correspondence names. An entry is identified
by `(device_class, operation, selector)`; equal names never merge entries of
different identity. These tests keep the fixture and the two maps in step and
keep the fixture's own keys, names and multi-value cells well formed.
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAILLANT = ROOT / "protocols" / "vaillant"
CORRESPONDENCE = VAILLANT / "fixtures" / "b509-register-name-correspondence.csv"
BOILER_MAP = VAILLANT / "ebus-vaillant-B509-boiler-register-map.md"
HEAT_PUMP_MAP = VAILLANT / "ebus-vaillant-B509-heatpump-register-map.md"

EXPECTED_COLUMNS = [
    "device_class",
    "operation",
    "selector",
    "name",
    "unit",
    "vaillant_friendly_name",
    "vaillant_name",
    "ebusd_name",
    "legacy_api_path",
    "open_question",
]

DEVICE_CLASSES = ("boiler", "heat_pump", "heat_pump_interface_unit", "any")
OPERATIONS = ("0D", "0E", "54")

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
API_PREFIX_TOKENS = ("state_", "config_", "diagnostics_", "identity_", "energy_")

# The two operation rows carry no selector.
OPERATION_ROWS = {
    ("any", "0D", "read_symbolic_address"),
    ("any", "0E", "write_symbolic_address"),
}

# Columns whose cells may hold several values separated by " | ".
CORRESPONDENCE_COLUMNS = [
    "vaillant_friendly_name",
    "vaillant_name",
    "ebusd_name",
    "legacy_api_path",
]

NAME_CELL = re.compile(r"^`([a-z][a-z0-9]*(?:_[a-z0-9]+)*)`$")
REGISTER_ID_CELL = re.compile(r"^`(0x[0-9A-F]{4})`$")
SELECTOR_CELL = re.compile(r"^`(54 02 00 [0-9A-F]{2} [0-9A-F]{2})`$")


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _table_cells(path: Path) -> list[list[str]]:
    cells = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("|"):
            cells.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return cells


def _map_entries(path: Path, register_class: str) -> list[tuple[str, str, str]]:
    """Return `(device_class, selector, name)` for every register row of a map."""
    entries = []
    for cells in _table_cells(path):
        if len(cells) < 2:
            continue
        selector_match = SELECTOR_CELL.match(cells[0])
        name_match = NAME_CELL.match(cells[1])
        if selector_match and name_match:
            entries.append(
                ("heat_pump_interface_unit", selector_match.group(1), name_match.group(1))
            )
            continue
        name_match = NAME_CELL.match(cells[0])
        if not name_match:
            continue
        for cell in cells[1:]:
            register_match = REGISTER_ID_CELL.match(cell)
            if register_match:
                entries.append((register_class, register_match.group(1), name_match.group(1)))
                break
    return entries


def _cell_values(row: dict[str, str], column: str) -> tuple[str, ...]:
    return tuple(row[column].split(" | ")) if row[column] else ()


def test_correspondence_fixture_has_expected_columns() -> None:
    with CORRESPONDENCE.open(encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle))
    assert header == EXPECTED_COLUMNS


def test_correspondence_rows_have_ten_columns_and_unique_identity() -> None:
    with CORRESPONDENCE.open(encoding="utf-8", newline="") as handle:
        raw_rows = list(csv.reader(handle))
    assert len(raw_rows) > 1
    for index, raw in enumerate(raw_rows, start=1):
        assert len(raw) == len(EXPECTED_COLUMNS), f"line {index}: {len(raw)} columns"

    rows = _rows(CORRESPONDENCE)
    keys = [(row["device_class"], row["operation"], row["selector"]) for row in rows]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    assert duplicates == [], f"identity tuple used more than once: {duplicates}"


def test_correspondence_device_class_and_operation_are_known() -> None:
    for row in _rows(CORRESPONDENCE):
        where = f"{row['device_class']}/{row['operation']}/{row['selector']}"
        assert row["device_class"] in DEVICE_CLASSES, f"{where}: unknown device_class"
        assert row["operation"] in OPERATIONS, f"{where}: unknown operation"


def test_correspondence_names_are_snake_case_without_api_prefix() -> None:
    for row in _rows(CORRESPONDENCE):
        name = row["name"]
        where = f"{row['device_class']}/{row['operation']}/{row['selector']}"
        assert NAME_PATTERN.match(name), f"{where}: {name!r} is not snake_case"
        assert not name.startswith(API_PREFIX_TOKENS), f"{where}: {name!r} has an API prefix"


def test_empty_selector_rows_are_exactly_the_two_operation_rows() -> None:
    empty = {
        (row["device_class"], row["operation"], row["name"])
        for row in _rows(CORRESPONDENCE)
        if not row["selector"]
    }
    assert empty == OPERATION_ROWS


def test_register_map_entries_appear_in_the_fixture_with_the_same_name() -> None:
    # The heat pump map holds the two-byte registers of section 1 and the
    # five-byte selectors of section 2; `_map_entries` assigns each its class.
    map_entries = _map_entries(BOILER_MAP, "boiler") + _map_entries(HEAT_PUMP_MAP, "heat_pump")
    assert len(map_entries) > 0

    by_identity = {}
    for device_class, selector, name in map_entries:
        key = (device_class, selector)
        assert key not in by_identity, f"{key} is listed twice in the maps"
        by_identity[key] = name

    operation = {"boiler": "0D", "heat_pump": "0D", "heat_pump_interface_unit": "54"}
    fixture = {
        (row["device_class"], row["operation"], row["selector"]): row["name"]
        for row in _rows(CORRESPONDENCE)
        if row["selector"]
    }

    for (device_class, selector), name in by_identity.items():
        key = (device_class, operation[device_class], selector)
        assert key in fixture, f"{key} is in a register map but not in the fixture"
        assert fixture[key] == name, (
            f"{key}: fixture name {fixture[key]!r} != map name {name!r}"
        )

    expected_keys = {
        (device_class, operation[device_class], selector)
        for device_class, selector in by_identity
    }
    extra = sorted(set(fixture) - expected_keys)
    assert extra == [], f"fixture rows that are in neither register map: {extra}"


def test_correspondence_cells_use_only_the_canonical_separator() -> None:
    # Values are separated by exactly " | ". Any other use of the pipe
    # character would make a multi-valued cell look single-valued.
    for row in _rows(CORRESPONDENCE):
        where = f"{row['device_class']}/{row['operation']}/{row['selector']}"
        assert "|" not in row["name"], f"{where}: pipe in name"
        for column in CORRESPONDENCE_COLUMNS:
            for value in _cell_values(row, column):
                assert "|" not in value, f"{where} {column}: non-canonical separator in {row[column]!r}"
                assert value and value == value.strip(), (
                    f"{where} {column}: malformed value in {row[column]!r}"
                )
