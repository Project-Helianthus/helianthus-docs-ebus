"""Mechanical checks for the public B509 register name correspondence fixture.

The fixture maps every entry of the B509 boiler and heat pump register maps to
a canonical name and, where known, correspondence names. An entry is identified
by `(device_class, operation, selector)`; equal names never merge entries of
different identity. These tests keep the fixture and the two maps in step,
including the codec and scale of every register, keep the fixture's own keys,
names and multi-value cells well formed, and keep the refrigerant and
compressor rows of the heat pump map consistent with the fixture, and keep the
read-only poll page of the architecture tree consistent with the map.
"""

import csv
import re
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAILLANT = ROOT / "protocols" / "vaillant"
CORRESPONDENCE = VAILLANT / "fixtures" / "b509-register-name-correspondence.csv"
BOILER_MAP = VAILLANT / "ebus-vaillant-b509-boiler-register-map.md"
HEAT_PUMP_MAP = VAILLANT / "ebus-vaillant-b509-heatpump-register-map.md"

EXPECTED_COLUMNS = [
    "device_class",
    "operation",
    "selector",
    "name",
    "unit",
    "codec",
    "scale",
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

# A `Codec / scale` cell starts with a code span holding the codec, optionally
# followed by ` / N` (scale 1/N) and a parenthesised remark. Text after the
# span may state a factor as `(N... units)`; `(unknown)` states no codec.
CODEC_SPAN = re.compile(r"^`([^`]+)`(.*)$")
CODEC_BODY = re.compile(r"^(?P<codec>.+?)(?:\s+/\s+(?P<divisor>[0-9]+))?(?:\s*\(.*\))?$")
UNITS_FACTOR = re.compile(r"\((?P<factor>[0-9]+)\s*[A-Za-z]*\s+units\)")
CODEC_HEADER = "Codec / scale"
SELECTOR_HEADER = "Full selector (hex)"

HEAT_PUMP_CLASSES = ("heat_pump", "heat_pump_interface_unit")
POLL_HEADING = "## Refrigerant and compressor numeric rows"
POLL_PAGE = ROOT / "architecture" / "b509-heatpump-refrigerant-poll.md"
POLL_SUBJECTS = ("refrigerant_", "compressor_")
POLL_HEADER = ["Selector", "Operation", "Class", "Name", "Unit", "Unresolved evidence"]


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


def split_codec_cell(cell: str) -> tuple[str, str]:
    """Return `(codec, scale)` stated by one `Codec / scale` cell of a map."""
    span = CODEC_SPAN.match(cell)
    if not span:
        return "", ""
    rest = span.group(2).strip()
    if rest == "(unknown)":
        return "", ""
    body = CODEC_BODY.match(span.group(1))
    assert body, f"unreadable codec cell {cell!r}"
    scale = ""
    if body.group("divisor"):
        scale = str(Decimal(1) / Decimal(body.group("divisor")))
    factor = UNITS_FACTOR.search(rest)
    if factor:
        scale = str(Decimal(factor.group("factor")))
    return body.group("codec").strip(), scale


def _map_codecs(path: Path, register_class: str) -> dict[tuple[str, str], tuple[str, str]]:
    """Return `{(device_class, selector): (codec, scale)}` for every register row.

    Two-byte registers take the `Codec / scale` column of their table; the
    five-byte selectors take the `Type` column and state no scale.
    """
    result = {}
    codec_index = type_index = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            codec_index = type_index = None
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if CODEC_HEADER in cells:
            codec_index = cells.index(CODEC_HEADER)
            continue
        if SELECTOR_HEADER in cells and "Type" in cells:
            type_index = cells.index("Type")
            continue
        selector_match = SELECTOR_CELL.match(cells[0])
        if selector_match and type_index is not None and NAME_CELL.match(cells[1]):
            key = ("heat_pump_interface_unit", selector_match.group(1))
            assert key not in result, f"{key} is listed twice in the maps"
            result[key] = (cells[type_index], "")
            continue
        if codec_index is None or not NAME_CELL.match(cells[0]):
            continue
        for cell in cells[1:]:
            register_match = REGISTER_ID_CELL.match(cell)
            if register_match:
                key = (register_class, register_match.group(1))
                assert key not in result, f"{key} is listed twice in the maps"
                result[key] = split_codec_cell(cells[codec_index])
                break
    return result


def _poll_rows() -> list[dict[str, str]]:
    """Return the rows of the table in the read-only refrigerant poll section."""
    lines = HEAT_PUMP_MAP.read_text(encoding="utf-8").splitlines()
    assert POLL_HEADING in lines, "the heat pump map has no refrigerant and compressor numeric rows section"
    section = []
    for line in lines[lines.index(POLL_HEADING) + 1 :]:
        if line.startswith("## "):
            break
        section.append(line)
    tables = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in section
        if line.startswith("|")
    ]
    assert tables and tables[0] == POLL_HEADER, "unexpected poll table header"
    rows = []
    for cells in tables[2:]:
        assert len(cells) == len(POLL_HEADER), f"malformed poll row {cells}"
        rows.append(dict(zip(POLL_HEADER, (cell.strip("`") for cell in cells))))
    return rows


def _section_text(heading: str) -> str:
    lines = HEAT_PUMP_MAP.read_text(encoding="utf-8").splitlines()
    body = []
    for line in lines[lines.index(heading) + 1 :]:
        if line.startswith("## "):
            break
        body.append(line)
    return " ".join(" ".join(body).split())


def _cell_values(row: dict[str, str], column: str) -> tuple[str, ...]:
    return tuple(row[column].split(" | ")) if row[column] else ()


def test_correspondence_fixture_has_expected_columns() -> None:
    with CORRESPONDENCE.open(encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle))
    assert header == EXPECTED_COLUMNS


def test_correspondence_rows_have_all_columns_and_unique_identity() -> None:
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


def test_codec_cell_rule_reads_codec_and_scale() -> None:
    # Each case varies one part of the cell: the codec span, a ` / N` divisor,
    # a remark inside the span, a factor after the span, and a stated unknown.
    cases = {
        "`DATA2c`": ("DATA2c", ""),
        "`SIN / 10`": ("SIN", "0.1"),
        "`UIN / 100`": ("UIN", "0.01"),
        "`UCH (0x0F=on, 0xF0=off)`": ("UCH", ""),
        "`on/off`": ("on/off", ""),
        "`HEX:8` (8 bytes)": ("HEX:8", ""),
        "`phase flags` (bitmask)": ("phase flags", ""),
        "`UCH` (100W units)": ("UCH", "100"),
        "`value` (unknown)": ("", ""),
        "`*r` stub (raw)": ("*r", ""),
        "no code span": ("", ""),
    }
    for cell, expected in cases.items():
        assert split_codec_cell(cell) == expected, cell


def test_codec_and_scale_columns_equal_the_map_pages() -> None:
    codecs = _map_codecs(BOILER_MAP, "boiler") | _map_codecs(HEAT_PUMP_MAP, "heat_pump")
    entries = _map_entries(BOILER_MAP, "boiler") + _map_entries(HEAT_PUMP_MAP, "heat_pump")
    assert {(device_class, selector) for device_class, selector, _ in entries} == set(codecs)

    rows = {(row["device_class"], row["selector"]): row for row in _rows(CORRESPONDENCE)}
    for key, (codec, scale) in codecs.items():
        assert key in rows, f"{key} is in a register map but not in the fixture"
        assert (rows[key]["codec"], rows[key]["scale"]) == (codec, scale), (
            f"{key}: fixture codec/scale "
            f"{(rows[key]['codec'], rows[key]['scale'])!r} != map {(codec, scale)!r}"
        )


def test_codec_and_scale_of_selected_rows() -> None:
    # Pinned rows guard the reading rule: a divisor, a factor after the span, a
    # stated unknown, a candidate factor that is only an open question, a
    # sentinel remark inside the span and a five-byte type column.
    expected = {
        ("boiler", "0x2E00"): ("SIN", "0.1"),
        ("boiler", "0x5500"): ("UIN", "0.01"),
        ("boiler", "0x2900"): ("UIN", ""),
        ("boiler", "0x0500"): ("UCH", ""),
        ("heat_pump", "0xE201"): ("UCH", "100"),
        ("heat_pump", "0x8000"): ("", ""),
        ("heat_pump", "0x1400"): ("sensor", ""),
        ("heat_pump_interface_unit", "54 02 00 0D 0A"): ("EXP", ""),
        ("heat_pump_interface_unit", "54 02 00 C3 0B"): ("word", ""),
    }
    rows = {(row["device_class"], row["selector"]): row for row in _rows(CORRESPONDENCE)}
    for key, value in expected.items():
        assert (rows[key]["codec"], rows[key]["scale"]) == value, key


def test_operation_rows_have_no_codec_or_scale() -> None:
    # The two operation rows are operations, not registers: the map's markers
    # for them are not a value codec.
    for row in _rows(CORRESPONDENCE):
        if not row["selector"]:
            assert (row["codec"], row["scale"]) == ("", ""), row["name"]


def test_scale_is_a_plain_decimal_beside_a_codec() -> None:
    for row in _rows(CORRESPONDENCE):
        where = f"{row['device_class']}/{row['operation']}/{row['selector']}"
        assert row["codec"] == row["codec"].strip(), f"{where}: padded codec"
        if row["scale"]:
            assert row["codec"], f"{where}: scale without codec"
            assert re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", row["scale"]), f"{where}: scale"
            assert Decimal(row["scale"]) > 0, f"{where}: scale must be positive"


def test_poll_rows_match_the_fixture() -> None:
    fixture = {
        (row["device_class"], row["operation"], row["selector"]): row
        for row in _rows(CORRESPONDENCE)
    }
    seen = set()
    for poll in _poll_rows():
        key = (poll["Class"], poll["Operation"], poll["Selector"])
        assert key not in seen, f"{key} is listed twice in the poll"
        seen.add(key)
        assert key in fixture, f"{key} is in the poll but not in the fixture"
        row = fixture[key]
        assert poll["Class"] in HEAT_PUMP_CLASSES, f"{key}: not a heat pump class"
        assert poll["Name"] == row["name"], f"{key}: name differs from the fixture"
        assert poll["Unit"] == (row["unit"] or "unresolved"), f"{key}: unit differs"
        assert row["codec"], f"{key}: the poll lists a row without a codec"


def test_poll_covers_the_final_numeric_refrigerant_and_compressor_rows() -> None:
    # A row qualifies when it belongs to a heat pump class, its subject is the
    # refrigerant or the compressor, it is not a configuration value, it has a
    # unit and no open question. The one exception is the compressor speed,
    # whose only open item is the unit the poll section asks for.
    expected = set()
    for row in _rows(CORRESPONDENCE):
        if row["device_class"] not in HEAT_PUMP_CLASSES:
            continue
        if not row["name"].startswith(POLL_SUBJECTS):
            continue
        if row["legacy_api_path"].startswith("config."):
            continue
        key = (row["device_class"], row["operation"], row["selector"])
        if row["unit"] and not row["open_question"]:
            expected.add(key)
        elif row["name"] == "compressor_speed" and "unit is unresolved" in row["open_question"]:
            expected.add(key)
    listed = {(poll["Class"], poll["Operation"], poll["Selector"]) for poll in _poll_rows()}
    assert listed == expected


def test_poll_withholds_pressures_and_compressor_speed_until_their_evidence() -> None:
    for poll in _poll_rows():
        evidence = poll["Unresolved evidence"]
        if poll["Unit"] == "bar":
            assert "pressure reference" in evidence and "absolute or gauge" in evidence, poll
        elif poll["Name"] == "compressor_speed":
            assert "unit" in evidence, poll
        else:
            assert evidence == "--", poll


def test_protocol_page_carries_no_poll_behaviour() -> None:
    text = HEAT_PUMP_MAP.read_text(encoding="utf-8")
    assert "Read-only refrigerant poll" not in text
    assert "refrigerant-poll" not in text, "the protocol page must not link to the poll page"
    section = _section_text(POLL_HEADING)
    for forbidden in (
        "at least 60 seconds",
        "off by default",
        "scrape",
        "cycle",
        "Owner approval",
        "withheld",
        "fills it",
        "usable as a point",
        "use as a point",
        "exported",
    ):
        assert forbidden not in section, f"the protocol page states gateway behaviour: {forbidden}"


def test_poll_page_states_its_bounds_and_the_owner_decision() -> None:
    text = " ".join(POLL_PAGE.read_text(encoding="utf-8").split())
    assert "(../protocols/vaillant/ebus-vaillant-b509-heatpump-register-map.md)" in text
    for statement in (
        "at most one read of each listed selector",
        "at least 60 seconds",
        "off by default",
        "never starts, schedules or hastens a poll read",
        "stays withheld",
        "no other selector fills it, even one with the same name",
        "Enabling the poll on an installation is the owner's decision at live testing.",
        "Nothing in this page authorizes a read on any installation or field bus.",
    ):
        assert statement in text, f"the poll page does not state: {statement}"


def test_poll_page_is_listed_in_the_architecture_index() -> None:
    index = (ROOT / "architecture" / "index.md").read_text(encoding="utf-8")
    assert "(b509-heatpump-refrigerant-poll.md)" in index


PROTOCOL_PAGE = VAILLANT / "ebus-vaillant-b509.md"
FIXTURE_HEADING = "## Register name correspondence fixture"


def _fixture_schema_rows() -> list[tuple[str, str]]:
    lines = PROTOCOL_PAGE.read_text(encoding="utf-8").splitlines()
    rows: list[tuple[str, str]] = []
    for line in lines[lines.index(FIXTURE_HEADING) + 1 :]:
        if line.startswith("## "):
            break
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append((cells[0].strip("`"), " ".join(" | ".join(cells[1:]).split())))
    return rows


def test_protocol_page_schema_table_lists_every_fixture_column_in_order() -> None:
    assert [column for column, _ in _fixture_schema_rows()] == EXPECTED_COLUMNS


def test_protocol_page_schema_defines_codec_and_scale() -> None:
    meaning = dict(_fixture_schema_rows())
    codec, scale = meaning["codec"], meaning["scale"]
    assert "Empty when the map states no codec" in codec, codec
    assert "multiplies the decoded value" in scale, scale
    assert "states no factor" in scale and "unresolved" in scale, scale
    for text in (codec, scale):
        assert "boiler" in text and "heat pump" in text, text
