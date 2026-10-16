"""Consumer contract for the public naming CSVs, without an Explorer import.

Key and column rules: protocols/vaillant/ebus-vaillant-B524-register-map.md,
"OP=0x02 — Local Parameter Registers" / "Register name correspondence fixture".
Naming rows use (opcode, group, register), not concrete instance identity:
development/b524-provisional-name-evidence.md, "Evidence and missing-evidence key".
Neither an omitted instance nor an observed label qualifies native behavior.
architecture/naming.md, "Register and field names", keeps correspondence
annotations separate from canonical names.
"""

import csv
from pathlib import Path

import pytest


FIXTURES = Path(__file__).resolve().parents[1] / "protocols/vaillant/fixtures"
SELECTOR = ("opcode", "group", "register")
NAMES = ("name", "previous_name")
ANNOTATIONS = (
    "vaillant_friendly_name",
    "vaillant_name_vrc720",
    "vaillant_name_vrc700",
    "myvaillant_name_vrc720",
    "myvaillant_name_vrc700",
    "ebusd_name",
)
BRIDGE_COLUMNS = (*SELECTOR, *NAMES, *ANNOTATIONS)


def _rows(filename):
    with (FIXTURES / filename).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _key(row):
    return tuple(int(row[column], 16) for column in SELECTOR)


def _index(rows, source):
    indexed = {}
    for position, row in enumerate(rows, start=2):
        key = _key(row)
        if key in indexed:
            raise ValueError(f"{source}: duplicate/ambiguous selector {key} at row {position}")
        indexed[key] = row
    return indexed


def _bridge(canonical, correspondence):
    """Project names only; OP06 annotations need no invented OP02 catalog row."""
    catalog = _index(canonical, "canonical")
    annotations = _index(correspondence, "correspondence")
    missing = catalog.keys() - annotations.keys()
    if missing:
        raise ValueError(f"canonical selectors missing correspondence: {sorted(missing)}")
    result = {}
    for key, row in annotations.items():
        if key in catalog:
            for column in NAMES:
                if row[column] != catalog[key][column]:
                    raise ValueError(f"{key}: conflicting {column}")
        result[key] = {column: row[column] for column in BRIDGE_COLUMNS}
    return result


def _synthetic(opcode="0x02", **changes):
    return dict.fromkeys(ANNOTATIONS, "") | {
        "opcode": opcode, "group": "0x01", "register": "0x0001",
        "name": "synthetic_name", "previous_name": "synthetic_previous",
    } | changes


def test_real_bridge_matches_independently_keyed_source_maps():
    canonical = _rows("b524-op02-register-names.csv")
    correspondence = _rows("b524-register-name-correspondence.csv")
    bridge = _bridge(canonical, correspondence)
    # Independent oracle: no use of _key/_index, and no positional zip join.
    catalog_map = {
        (int(r["opcode"], 16), int(r["group"], 16), int(r["register"], 16)): r
        for r in canonical
    }
    observed_map = {
        (int(r["opcode"], 16), int(r["group"], 16), int(r["register"], 16)): r
        for r in correspondence
    }
    assert canonical and correspondence
    assert set(bridge) == set(observed_map)
    assert set(catalog_map) <= set(bridge)
    assert {key[0] for key in catalog_map} == {0x02}
    assert any(key[0] == 0x06 for key in bridge)
    assert bridge == _bridge(list(reversed(canonical)), list(reversed(correspondence)))
    for key, record in bridge.items():
        assert set(record) == set(BRIDGE_COLUMNS)
        for column in NAMES:
            assert record[column] == catalog_map.get(key, observed_map[key])[column]
        for column in ANNOTATIONS:
            assert record[column] == observed_map[key][column]


def test_equal_group_register_and_names_do_not_merge_opcodes():
    local = _synthetic()
    remote = _synthetic("0x06")
    bridge = _bridge([local], [remote, local])
    assert set(bridge) == {(0x02, 0x01, 0x0001), (0x06, 0x01, 0x0001)}
    assert bridge[(0x02, 0x01, 0x0001)]["opcode"] == "0x02"
    assert bridge[(0x06, 0x01, 0x0001)]["opcode"] == "0x06"


@pytest.mark.parametrize("source", ["canonical", "correspondence"])
@pytest.mark.parametrize("conflicting", [False, True])
def test_duplicate_or_ambiguous_selectors_fail_closed(source, conflicting):
    row = _synthetic()
    # Hex spelling differences still identify the same native selector.
    duplicate = row | {"group": "0x1"}
    if conflicting:
        duplicate["name"] = "conflicting_name"
    inputs = {"canonical": [row], "correspondence": [row]}
    inputs[source].append(duplicate)
    with pytest.raises(ValueError, match=f"{source}: duplicate/ambiguous selector"):
        _bridge(**inputs)


def test_missing_selector_cannot_be_rescued_by_equal_names():
    with pytest.raises(ValueError, match="missing correspondence"):
        _bridge([_synthetic()], [_synthetic("0x06")])


@pytest.mark.parametrize("column", NAMES)
def test_conflicting_migration_columns_fail_closed(column):
    row = _synthetic()
    with pytest.raises(ValueError, match=f"conflicting {column}"):
        _bridge([row], [row | {column: "different_name"}])


@pytest.mark.parametrize("column", (*NAMES, *ANNOTATIONS))
def test_label_changes_preserve_identity_and_cannot_manufacture_authority(column):
    canonical = _rows("b524-op02-register-names.csv")
    correspondence = _rows("b524-register-name-correspondence.csv")
    before = _bridge(canonical, correspondence)
    # Deliberately identical, authority-sounding labels across every selector.
    text = "qualified writable codec temperature range 0..100"
    changed_catalog = [r | {column: text} if column in NAMES else dict(r) for r in canonical]
    changed_annotations = [r | {column: text} for r in correspondence]
    after = _bridge(changed_catalog, changed_annotations)
    assert set(after) == set(before)
    for key, record in after.items():
        assert record == before[key] | {column: text}
        assert set(record) == set(BRIDGE_COLUMNS)
        assert tuple(record[field] for field in SELECTOR) == tuple(
            before[key][field] for field in SELECTOR
        )
    # Source schema is also names-only: no hidden qualification fields to copy.
    assert all(set(row) == set(BRIDGE_COLUMNS) for row in correspondence)
