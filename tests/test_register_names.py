"""Decomposition test for canonical register names (architecture/naming.md).

Every canonical name on a covered surface decomposes into vocabulary words
whose roles follow the order of the parts; the vocabulary itself stays within
the closed predicate and abbreviation lists; renamed fixtures keep the earlier
name in `previous_name`.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_register_names as names  # noqa: E402

FIXTURES = ROOT / "protocols" / "vaillant" / "fixtures"


@pytest.fixture(scope="module")
def vocabulary() -> names.Vocabulary:
    return names.load_vocabulary()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_every_covered_name_decomposes(vocabulary: names.Vocabulary) -> None:
    covered = names.covered_names()
    assert len(covered) > 1000
    failures = []
    for where, name in covered:
        try:
            names.decompose(name, vocabulary)
        except names.NameError_ as error:
            failures.append(f"{where}: {error}")
    assert failures == []


def test_vocabulary_predicates_are_the_closed_list(vocabulary: names.Vocabulary) -> None:
    predicates = {
        token for token, roles in vocabulary.roles.items() if "predicate" in roles
    }
    assert predicates - set(names.PREDICATE_COMPOUNDS) == names.PREDICATES


def test_vocabulary_abbreviations_are_the_closed_list() -> None:
    abbreviations = {
        row["token"]
        for row in _rows(names.VOCABULARY)
        if row["definition"].startswith("Abbreviation:")
    }
    assert abbreviations == names.ABBREVIATIONS


def test_forbidden_synonyms_of_the_rules_are_listed(vocabulary: names.Vocabulary) -> None:
    for synonym, token in {
        "ch": "heating",
        "central_heating": "heating",
        "desired": "setpoint",
        "target": "setpoint",
        "set": "setpoint",
        "brine": "source",
        "deicing": "defrost",
        "three_way_valve": "diverter_valve",
        "gas": "fuel",
        "oil": "fuel",
        "buffer": "cylinder",
        "tank": "cylinder",
        "storage": "cylinder",
        "operation_mode": "operating_mode",
        "allowed": "enabled",
        "activation": "active",
        "max": "maximum",
        "min": "minimum",
        "duration": "time",
        "hours": "time",
        "interval": "time",
        "ext": "external",
    }.items():
        assert vocabulary.forbidden.get(synonym) == token, synonym


@pytest.mark.parametrize(
    "name",
    [
        "heating_flow_temperature_setpoint_maximum",
        "compressor_start_count_total",
        "compressor_on_time_minimum",
        "compressor_inlet_temperature",
        "outdoor_temperature_daily_average",
        "holiday_start_date",
        "heat_pump_flow_temperature_setpoint_maximum",
        "unknown_1",
        "heating_unknown_2",
        "compressor_start_count_total_reset_command",
        "holiday_end_clock_time_hour",
        "source_temperature_limit_at_maximum_flow_rate",
        "zone_name_prefix",
        "flow_temperature_limit_at_heat_pump_maximum_power",
        "pump_start_command",
        "pump_stop_command",
        "circuit_external_demand_input",
        "hydraulic_circuit_type",
        "time_program_day_period_count_maximum",
        "pump_active_at_maximum_outdoor_temperature",
        "pump_active_at_maximum_flow_temperature",
        "pump_start_count",
        "pump_operating_time",
        "pump_temperature_maximum",
        "flow_temperature_setpoint_maximum",
        "pump_start_count_total",
    ],
)
def test_examples_of_the_rules_decompose(vocabulary: names.Vocabulary, name: str) -> None:
    names.decompose(name, vocabulary)


@pytest.mark.parametrize(
    ("name", "reason"),
    [
        ("system_flow_temperature", "no vocabulary entry"),
        ("max_room_humidity", "forbidden synonym"),
        ("zone_quick_veto_duration", "forbidden synonym"),
        ("central_heating_flow_temperature", "forbidden synonym"),
        ("temperature_flow", "order of the parts"),
        ("flow_temperature_setpoint_maximum_minimum", "order of the parts"),
        ("heating_flow_temperature_setpoint_offset", "order of the parts"),
        ("heating_temperature_unknown_1", "precede 'unknown'"),
        ("unknown_1_temperature", "must close the name"),
        ("zone_holiday_close_command", "no vocabulary entry"),
        ("zone_holiday_mode_command", "not an action"),
        ("cooling_enabled_at", "empty condition"),
        ("Zone_Name", "snake_case"),
        ("pump_command", "only closes a name"),
        ("holiday_command", "only closes a name"),
        ("flow_temperature_limit_at_flow_rate_maximum", "is not followed by its object"),
        ("room_temperature_setpoint_at_holiday_minimum", "is not followed by its object"),
        ("zone_name_year", "order of the parts"),
        ("holiday_start_date_hour", "order of the parts"),
        ("date_year_1", "order of the parts"),
        ("source_temperature_limit_at_flow_rate_maximum", "is not followed by its object"),
        ("heating_cooling_temperature", "order of the parts"),
        ("compressor_inlet_outlet_temperature", "order of the parts"),
        ("external_ok", "order of the parts"),
        ("circuit_external_demand", "order of the parts"),
        ("holiday_start_date_month_2", "order of the parts"),
        ("pump_active_at_maximum_heat_pump", "not followed by its object"),
        ("pump_active_at_maximum", "not followed by its object"),
        ("temperature_count", "order of the parts"),
        ("heating_count", "order of the parts"),
        ("pump_time", "order of the parts"),
        ("pump_active_maximum", "order of the parts"),
        ("pump_mode_minimum", "order of the parts"),
        ("pump_fault_total", "order of the parts"),
    ],
)
def test_nonconforming_names_fail(vocabulary: names.Vocabulary, name: str, reason: str) -> None:
    with pytest.raises(names.NameError_, match=reason):
        names.decompose(name, vocabulary)


def test_renamed_fixtures_keep_the_previous_name() -> None:
    for fixture in (
        "b524-op02-register-names.csv",
        "b524-register-name-correspondence.csv",
        "b524-op02-requester-register-matrix.csv",
        "b524-op02-calendar-clock-selectors.csv",
        "b524-op00-system-information-ids.csv",
    ):
        rows = _rows(FIXTURES / fixture)
        for row in rows:
            assert "previous_name" in row, fixture
            assert bool(row["name"]) == bool(row["previous_name"]), (fixture, row)
    for row in _rows(FIXTURES / "b524-op02-write-templates.csv"):
        assert row["previous_name"], row


def test_provisional_names_carry_an_open_question() -> None:
    for fixture in ("b524-op02-register-names.csv", "b524-op00-system-information-ids.csv"):
        rows = _rows(FIXTURES / fixture)
        for row in rows:
            if "unknown" in row["name"].split("_"):
                assert row["open_question"], (fixture, row["name"])


def test_equal_names_in_one_selector_table_are_provisional() -> None:
    # The selector is part of identity: an equal name inside one opcode and
    # group is kept only for selectors on disjoint families, and both rows
    # then state the family split and the same-quantity question.
    for fixture, scope in (
        ("b524-op02-register-names.csv", ("opcode", "group")),
        ("b524-op00-system-information-ids.csv", ()),
    ):
        tables: dict[tuple[str, ...], dict[str, list[dict[str, str]]]] = {}
        for row in _rows(FIXTURES / fixture):
            if row["name"]:
                table = tables.setdefault(tuple(row[c] for c in scope), {})
                table.setdefault(row["name"], []).append(row)
        for table in tables.values():
            for name, entries in table.items():
                if len(entries) > 1:
                    assert all(entry["open_question"] for entry in entries), (fixture, name)


def _gate_with_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cell: str
) -> int:
    """Run the gate on a copy of the register map with one more row."""
    text = names.REGISTER_MAP.read_text(encoding="utf-8")
    marker = "## Constraint Catalog"
    assert marker in text
    row = f"| 0x0001 | {cell} | C | u16 | — | — | — | — | — | test row |\n\n"
    patched = tmp_path / "register-map.md"
    patched.write_text(text.replace(marker, row + marker, 1), encoding="utf-8")
    monkeypatch.setattr(names, "REGISTER_MAP", patched)
    # reported paths are relative to ROOT; the patched copy lies outside the repository
    monkeypatch.setattr(names, "ROOT", Path("/"))
    return names.main()


MALFORMED_CELLS = [
    "Flow_temperature",
    "`flow-temperature`",
    "flow temperature",
    "",
    "(flow_temperature)",
    "`(flow_temperature)`",
    "(Flow_temperature)",
    "flow`temperature",
    "flow_temperature`junk`",
    "(unknown_temperature)",
]


@pytest.mark.parametrize("cell", MALFORMED_CELLS)
def test_malformed_table_name_fails_the_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], cell: str
) -> None:
    """A register-map row whose name cell is malformed is reported, not skipped."""
    assert _gate_with_row(tmp_path, monkeypatch, cell) == 1
    assert capsys.readouterr().err


@pytest.mark.parametrize("cell", ["(unknown)", "(unknown, 8 regs)", "`flow_temperature`"])
def test_unnamed_note_and_code_span_name_pass_the_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cell: str
) -> None:
    """The explicit unnamed notes and a name in one code span are not failures."""
    assert _gate_with_row(tmp_path, monkeypatch, cell) == 0


@pytest.mark.parametrize("label", ["Dhw_temperature_setpoint", "dhw-temperature-setpoint", "dhw temperature setpoint"])
def test_malformed_write_template_label_fails_the_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], label: str
) -> None:
    """A canonical write-template row is found by its role, not by its label syntax."""
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    for source in names.FIXTURES.glob("*.csv"):
        text = source.read_text(encoding="utf-8")
        if source.name == "b524-op02-write-templates.csv":
            assert "\ndhw_temperature_setpoint," in text
            text = text.replace("\ndhw_temperature_setpoint,", f"\n{label},", 1)
        (fixtures / source.name).write_text(text, encoding="utf-8")
    monkeypatch.setattr(names, "FIXTURES", fixtures)
    monkeypatch.setattr(names, "ROOT", Path("/"))
    assert names.main() == 1
    assert capsys.readouterr().err


SEVEN_WORD_NAME = "heating_zone_room_comfort_temperature_setpoint_maximum"


def test_word_limit_is_the_only_failure_of_a_seven_word_name(
    vocabulary: names.Vocabulary, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The name is legal in every other respect: purpose, subject, place,
    attribute, object, predicate and bound in order; only the limit rejects it."""
    with monkeypatch.context() as relaxed:
        relaxed.setattr(names, "MAX_WORDS", 7)
        parts = names.decompose(SEVEN_WORD_NAME, vocabulary)
    assert [role for _, role in parts] == [
        "purpose", "subject", "place", "attribute", "object", "predicate", "bound",
    ]
    with pytest.raises(names.NameError_, match="7 words, more than 6"):
        names.decompose(SEVEN_WORD_NAME, vocabulary)


# ---------------------------------------------------------------------------
# Gate gaps: canonical write-template rows, `time` objects, end slots
# ---------------------------------------------------------------------------

CATALOG = [
    {"group": "0x03", "register": "0x0006", "name": "heating_zone_operating_mode",
     "previous_name": "zone_heating_operation_mode"},
    {"group": "0x01", "register": "0x0004", "name": "dhw_temperature_setpoint",
     "previous_name": "native_dhw_tapping_temperature_setpoint"},
]


def _template(label: str, previous: str, group: str, register: str,
              role: str = "canonical") -> dict[str, str]:
    return {"write": label, "previous_name": previous, "group": group,
            "register": register, "write_role": role}


@pytest.mark.parametrize("label,previous", [
    ("room control zone mode", "room-control zone mode"),
    ("heating_zone_operating_mode", "zone_heating_operation_mode"),
])
def test_prose_template_role_is_independent_of_catalog_strings(label: str, previous: str) -> None:
    rows = [_template(label, previous, "0x03", "0x0006", "prose")]
    assert names.canonical_template_labels(rows) == []


def test_canonical_template_label_is_validated(vocabulary: names.Vocabulary) -> None:
    rows = [
        _template("dhw_temperature_setpoint", "native_dhw_tapping_temperature_setpoint", "0x01", "0x0004"),
        # Both editable strings drift; the role still admits the raw label for validation.
        _template("dhw_temperature_set_point", "changed provenance", "0x01", "0x0004"),
        # Canonical labels cannot disappear through a selector change either.
        _template("dhw_temperature_set_point", "changed provenance", "0xFF", "0xFFFF"),
        _template("system configuration floats", "system configuration floats", "0x00", "0x0001 / 0x0023", "prose"),
    ]
    labels = names.canonical_template_labels(rows)
    assert labels == [(2, "dhw_temperature_setpoint"), (3, "dhw_temperature_set_point"),
                      (4, "dhw_temperature_set_point")]
    names.decompose(labels[0][1], vocabulary)
    for _, label in labels[1:]:
        with pytest.raises(names.NameError_):
            names.decompose(label, vocabulary)


@pytest.mark.parametrize("role", [None, "", "Canonical", "unknown", "canonical "])
def test_missing_or_invalid_template_role_fails(role: str | None) -> None:
    row = _template("dhw_temperature_setpoint", "changed provenance", "0x01", "0x0004")
    if role is None:
        del row["write_role"]
    else:
        row["write_role"] = role
    with pytest.raises(ValueError, match="write-templates.csv:2: write_role must be"):
        names.canonical_template_labels([row])


def test_fixture_write_templates_yield_only_catalog_labels() -> None:
    catalog_rows = _rows(FIXTURES / "b524-op02-register-names.csv")
    labels = names.canonical_template_labels(_rows(FIXTURES / "b524-op02-write-templates.csv"))
    assert len(labels) == 5
    assert {label for _, label in labels} <= {row["name"] for row in catalog_rows}


@pytest.mark.parametrize("mutation", ["drift", "missing", "invalid", "prose"])
def test_template_role_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], mutation: str,
) -> None:
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    for source in names.FIXTURES.glob("*.csv"):
        rows = _rows(source)
        fields = list(rows[0])
        if source.name == "b524-op02-write-templates.csv":
            row = next(row for row in rows if row["write"] == "dhw_temperature_setpoint")
            if mutation == "drift":
                row["write"] = "dhw_temperature_set_point"
                row["previous_name"] = "changed provenance"
            elif mutation == "missing":
                fields.remove("write_role")
                for item in rows:
                    del item["write_role"]
            elif mutation == "invalid":
                row["write_role"] = "unknown"
            else:
                row["write"] = "synthetic prose label"
                row["previous_name"] = "changed provenance"
                row["write_role"] = "prose"
        with (fixtures / source.name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    monkeypatch.setattr(names, "FIXTURES", fixtures)
    monkeypatch.setattr(names, "ROOT", Path("/"))
    assert names.main() == (0 if mutation == "prose" else 1)
    error = capsys.readouterr().err
    if mutation == "drift":
        assert "set_point" in error
    elif mutation in {"missing", "invalid"}:
        assert "write_role must be 'canonical' or 'prose'" in error
    else:
        assert not error


@pytest.mark.parametrize("name", ["temperature_time", "name_time", "date_time", "pump_time"])
def test_time_needs_an_activity_or_event_object(vocabulary: names.Vocabulary, name: str) -> None:
    with pytest.raises(names.NameError_):
        names.decompose(name, vocabulary)


@pytest.mark.parametrize(
    "name",
    ["dhw_loading_time_maximum", "backlight_on_time", "circuit_pump_operating_time_total",
     "drainback_start_time", "manual_cooling_time", "frost_protection_delay_time"],
)
def test_time_accepts_activity_and_event_objects(vocabulary: names.Vocabulary, name: str) -> None:
    names.decompose(name, vocabulary)


@pytest.mark.parametrize("name", ["pump_maximum", "pump_daily", "outdoor_temperature_average"])
def test_end_slots_need_their_prerequisites(vocabulary: names.Vocabulary, name: str) -> None:
    with pytest.raises(names.NameError_):
        names.decompose(name, vocabulary)


@pytest.mark.parametrize(
    "name",
    ["outdoor_temperature_daily_average", "boiler_flow_temperature_setpoint_maximum",
     "circuit_count_maximum", "cooling_electricity_consumption_current_month",
     "circuit_pump_operating_time_total"],
)
def test_end_slots_accept_legitimate_names(vocabulary: names.Vocabulary, name: str) -> None:
    names.decompose(name, vocabulary)


# ---------------------------------------------------------------------------
# Changed-name summary tables of the register map
# ---------------------------------------------------------------------------

REGISTER_MAP_TEXT = names.REGISTER_MAP.read_text(encoding="utf-8")


def _summary_cells(pattern) -> list[str]:
    cells = []
    for _, line in names._section(REGISTER_MAP_TEXT, "## OP=0x02", "## Constraint Catalog"):
        match = pattern.match(line)
        if match:
            cells.extend(names._cell_names(match[1]))
    return cells


@pytest.mark.parametrize(
    "pattern", [names.SUMMARY_REGISTER_ROW, names.SUMMARY_SELECTOR_ROW]
)
def test_current_summary_tables_are_covered_and_pass(
    vocabulary: names.Vocabulary, pattern
) -> None:
    cells = _summary_cells(pattern)
    assert cells
    covered = {name for _, name in names.covered_names()}
    for cell in cells:
        names.decompose(cell, vocabulary)
        assert cell in covered


@pytest.mark.parametrize(
    "line",
    [
        "| `0x001D` | `serial_numbr_prefix` | `vrc720_serial_part1` |",
        "| `GG=0x09/0x0A, RR=0x000F` | `room_temprature` | `current_room_temperature` |",
    ],
)
def test_misspelled_name_in_a_summary_table_is_rejected(
    vocabulary: names.Vocabulary, line: str
) -> None:
    match = next(
        m for p in (names.SUMMARY_REGISTER_ROW, names.SUMMARY_SELECTOR_ROW)
        if (m := p.match(line))
    )
    (cell,) = names._cell_names(match[1])
    with pytest.raises(names.NameError_):
        names.decompose(cell, vocabulary)


# ---------------------------------------------------------------------------
# `Candidate write encodings` table (after the constraint catalog)
# ---------------------------------------------------------------------------


def _write_encoding_cells() -> list[str]:
    cells = []
    for _, line in names._section(
        REGISTER_MAP_TEXT, "### Candidate write encodings", "## Open questions"
    ):
        match = names.WRITE_ENCODING_ROW.match(line)
        if match and match[1].strip() != names.NO_CATALOG_NAME:
            cells.extend(names._strip_code_span(part) for part in match[1].split(", "))
    return cells


def test_candidate_write_encoding_names_are_covered_and_pass(
    vocabulary: names.Vocabulary,
) -> None:
    cells = _write_encoding_cells()
    assert "dhw_outdoor_bivalence_temperature_limit" in cells
    assert "none in the catalog" not in " ".join(cells)
    covered = [name for _, name in names.covered_names()]
    for cell in cells:
        names.decompose(cell, vocabulary)
        assert cell in covered


def test_malformed_candidate_write_encoding_name_is_rejected(
    vocabulary: names.Vocabulary,
) -> None:
    line = "| `GG=0x00`, `RR=0x0001` | `Dhw-outdoor-bivalence-temperature-limit` | float32 |"
    match = names.WRITE_ENCODING_ROW.match(line)
    (cell,) = [names._strip_code_span(part) for part in match[1].split(", ")]
    with pytest.raises(names.NameError_):
        names.decompose(cell, vocabulary)


def test_unquoted_malformed_catalog_cell_is_rejected_and_prose_is_skipped(
    vocabulary: names.Vocabulary,
) -> None:
    line = "| `GG=0x03`, `RR=0x0011` | Zone-enabled | one byte 00 or 01 |"
    match = names.WRITE_ENCODING_ROW.match(line)
    assert match[1].strip() != names.NO_CATALOG_NAME
    with pytest.raises(names.NameError_):
        names.decompose(names._strip_code_span(match[1]), vocabulary)
    prose = names.WRITE_ENCODING_ROW.match(
        "| `GG=0x00`, `II=0xFF`, `RR=0x0103` | none in the catalog | bytes `01 00` |"
    )
    assert prose[1].strip() == names.NO_CATALOG_NAME
    assert "none in the catalog" not in [n for _, n in names.covered_names()]


def test_command_target_counts_as_one_word(vocabulary: names.Vocabulary) -> None:
    name = "heating_zone_room_comfort_temperature_setpoint_maximum_reset_command"
    assert names.decompose(name, vocabulary)[0][1] == "target"


def test_command_with_structurally_invalid_target_is_rejected(
    vocabulary: names.Vocabulary,
) -> None:
    for name in ("pump_maximum_reset_command", "Zone-enabled_reset_command",
                 "temperature_time_reset_command"):
        with pytest.raises(names.NameError_):
            names.decompose(name, vocabulary)


@pytest.mark.parametrize(
    ("cell", "valid"),
    [("`zone_enabled`", True), ("zone_enabled", True),
     ("`zone_enabled``", False), ("``zone_enabled``", False)],
)
def test_column_cells_strip_one_code_span_only(
    vocabulary: names.Vocabulary, cell: str, valid: bool
) -> None:
    line = f"| `GG=0x03`, `RR=0x0011` | {cell} | one byte 00 or 01 |"
    match = names.WRITE_ENCODING_ROW.match(line)
    (name,) = [names._strip_code_span(part) for part in match[1].split(", ")]
    if valid:
        names.decompose(name, vocabulary)
    else:
        with pytest.raises(names.NameError_):
            names.decompose(name, vocabulary)
    summary = names.SUMMARY_REGISTER_ROW.match(f"| `0x001D` | {cell} | `old` |")
    (summary_name,) = names._cell_names(summary[1])
    assert summary_name == name


def test_subject_only_count_takes_only_the_maximum_bound(vocabulary: names.Vocabulary) -> None:
    names.decompose("circuit_count_maximum", vocabulary)
    names.decompose("zone_count_maximum", vocabulary)
    names.decompose("boiler_count", vocabulary)
    for name in ("circuit_count_minimum", "circuit_count_total"):
        with pytest.raises(names.NameError_):
            names.decompose(name, vocabulary)
    # the event-object form keeps its rules
    names.decompose("time_program_day_period_count_maximum", vocabulary)
    names.decompose("circuit_pump_start_count_total", vocabulary)


def test_remaining_period_follows_time_only(vocabulary: names.Vocabulary) -> None:
    names.decompose("defrost_time_remaining", vocabulary)
    for name in ("temperature_remaining", "pump_start_count_remaining"):
        with pytest.raises(names.NameError_):
            names.decompose(name, vocabulary)


def test_condition_bound_needs_the_object_it_precedes(vocabulary: names.Vocabulary) -> None:
    names.decompose("pump_active_at_heating_maximum_flow_temperature", vocabulary)
    names.decompose("heating_flow_temperature_setpoint_maximum_at_heat_pump_fault", vocabulary)
    for name in (
        "pump_active_at_heating_maximum",
        "pump_active_at_flow_temperature_maximum",
    ):
        with pytest.raises(names.NameError_):
            names.decompose(name, vocabulary)


# ---------------------------------------------------------------------------
# Protocol-page tables whose rows do not begin with a register
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cell", ["0x0016", "`0x0016`", "0x00AF", "`0x00AF`"])
def test_header_register_selectors_are_not_names(cell: str) -> None:
    table = (
        "| Operation | Register |\n| --- | --- |\n"
        f"| Read | {cell} |\n"
        "| Read | `ventilation_operating_mode` |"
    )
    assert names.header_column_names(table.splitlines()) == [(4, "ventilation_operating_mode")]


@pytest.mark.parametrize("cell", ["0x0016", "`0x0016`", "0x00AF", "`0x00AF`"])
def test_catalog_named_register_selector_passes_main(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], cell: str
) -> None:
    text = names.PROTOCOL.read_text(encoding="utf-8")
    table = (
        "\n\n| Operation | Path | Register |\n| --- | --- | --- |\n"
        f"| Read | GG=0x00, RR={names._strip_code_span(cell)} | {cell} |\n"
    )
    original_read_text = Path.read_text

    def read_text(path: Path, *args, **kwargs) -> str:
        if path == names.PROTOCOL:
            return text + table
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    assert names.main() == 0
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("header", ["Name", "Write"])
def test_selector_mismatch_exemption_is_limited_to_register_columns(header: str) -> None:
    lines = (
        f"| Operation | Path | Register | {header} |\n| --- | --- | --- | --- |\n"
        "| Read | GG=0x00, RR=0x0016 | `0x0016` | `0x0016` |"
    ).splitlines()
    assert names.selector_name_mismatches(lines, _rows(FIXTURES / "b524-op02-register-names.csv")) == [
        (3, "0x0016", "ventilation_operating_mode")
    ]


@pytest.mark.parametrize("header", ["Name", "Write"])
@pytest.mark.parametrize("cell", ["0x0016", "`0x0016`", "0x00AF", "`0x00AF`"])
def test_header_selector_exemption_is_limited_to_register_columns(
    vocabulary: names.Vocabulary, header: str, cell: str
) -> None:
    table = f"| Path | {header} |\n| --- | --- |\n| Read | {cell} |"
    found = names.header_column_names(table.splitlines())
    assert found == [(3, names._strip_code_span(cell))]
    with pytest.raises(names.NameError_):
        names.decompose(found[0][1], vocabulary)


def test_header_selector_exemption_preserves_names_in_the_same_row() -> None:
    table = (
        "| Path | Register | Name | Write |\n| --- | --- | --- | --- |\n"
        "| Read | `0x0016` | `0x0016` | `0x0016` |"
    )
    assert names.header_column_names(table.splitlines()) == [(3, "0x0016"), (3, "0x0016")]


@pytest.mark.parametrize(
    "cell",
    [
        "InvalidName", "`InvalidName`", "``0x0016``", "`0x0016", "0x0016`",
        "0x00af", "0X0016", "0x016", "0x0016" + "0",  # valid selector plus an extra digit
    ],
)
def test_header_selector_exclusion_preserves_invalid_names(
    vocabulary: names.Vocabulary, cell: str
) -> None:
    table = "| Operation | Register |\n| --- | --- |\n" f"| Read | {cell} |"
    found = names.header_column_names(table.splitlines())
    assert found == [(3, names._strip_code_span(cell))]
    with pytest.raises(names.NameError_):
        names.decompose(found[0][1], vocabulary)


def test_protocol_header_column_names_are_covered_and_pass(
    vocabulary: names.Vocabulary,
) -> None:
    found = names.header_column_names(names.PROTOCOL.read_text(encoding="utf-8").splitlines())
    assert {name for _, name in found} >= {
        "ventilation_operating_mode",
        "special_function_mode",
        "external_energy_management_enabled",
    }
    covered = [name for _, name in names.covered_names()]
    for _, name in found:
        names.decompose(name, vocabulary)
        assert name in covered


@pytest.mark.parametrize(
    "table",
    [
        "| Operation | Path | Register |\n| --- | --- | --- |\n"
        "| Read | `OP=0x02` | `Ventilation-operating-mode` (enum) |",
        "| Write | Body | Value |\n| --- | --- | --- |\n"
        "| `External-energy-management-enabled` (`RR=0x00B6`) | `02 01` | one byte |",
        "| Write | Body | Value |\n| --- | --- | --- |\n"
        "| `external_energy_management_enabled`` (`RR=0x00B6`) | `02 01` | one byte |",
    ],
)
def test_malformed_name_in_a_non_register_leading_table_is_rejected(
    vocabulary: names.Vocabulary, table: str
) -> None:
    found = names.header_column_names(table.splitlines())
    assert len(found) == 1
    with pytest.raises(names.NameError_):
        names.decompose(found[0][1], vocabulary)


def test_prose_cells_and_register_leading_rows_are_not_read_twice() -> None:
    table = (
        "| Operation | Path | Register |\n| --- | --- | --- |\n"
        "| Write | `OP=0x02` | Write target for mode activation |\n"
        "| RR | Name |\n| --- | --- |\n| `0x0001` | `device_connected` |"
    )
    assert names.header_column_names(table.splitlines()) == []


@pytest.mark.parametrize(
    "table",
    [
        "| Operation | Path | Register |\n| --- | --- | --- |\n"
        "| Read | `OP=0x02` | Ventilation-operating-mode (enum, see register map) |",
        "| Write | Body | Value |\n| --- | --- | --- |\n"
        "| External-energy-management-enabled (`RR=0x00B6`) | `02 01` | one byte |",
    ],
)
def test_unquoted_malformed_token_in_a_name_column_is_rejected(
    vocabulary: names.Vocabulary, table: str
) -> None:
    found = names.header_column_names(table.splitlines())
    assert len(found) == 1
    with pytest.raises(names.NameError_):
        names.decompose(found[0][1], vocabulary)


def test_unquoted_canonical_name_is_accepted_and_prose_is_skipped(
    vocabulary: names.Vocabulary,
) -> None:
    table = (
        "| Operation | Path | Register |\n| --- | --- | --- |\n"
        "| Read | `OP=0x02` | ventilation_operating_mode (enum, see register map) |\n"
        "| Write | `OP=0x02` | Write target for mode activation |\n"
        "| Write | `OP=0x02` | `special_function_mode` (dormant) |"
    )
    found = names.header_column_names(table.splitlines())
    assert [name for _, name in found] == ["ventilation_operating_mode", "special_function_mode"]
    for _, name in found:
        names.decompose(name, vocabulary)


def test_name_cells_equal_the_catalog_name_of_their_row_selector() -> None:
    lines = names.PROTOCOL.read_text(encoding="utf-8").splitlines()
    catalog = _rows(FIXTURES / "b524-op02-register-names.csv")
    assert names.selector_name_mismatches(lines, catalog) == []
    with_selector = {n: s for n, _, s in names.name_column_cells(lines) if s}
    assert len(with_selector) == 3


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("`ventilation_operating_mode` (enum, see register map)",
         "Ventilation-operating-mode (enum, see register map)"),
        ("`external_energy_management_enabled` (`RR=0x00B6`)",
         "External-energy-management-enabled (`RR=0x00B6`)"),
        ("`ventilation_operating_mode` (enum, see register map)",
         "`Ventilation operating mode` (enum, see register map)"),
        ("`external_energy_management_enabled` (`RR=0x00B6`)",
         "`External energy management enabled` (`RR=0x00B6`)"),
        # a valid name of another register is not the catalog name of the selector
        ("`special_function_mode` (dormant when no mode active)",
         "`ventilation_operating_mode` (dormant when no mode active)"),
    ],
)
def test_mutated_name_cell_of_the_real_page_is_rejected(
    vocabulary: names.Vocabulary, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], old: str, new: str
) -> None:
    text = names.PROTOCOL.read_text(encoding="utf-8")
    assert old in text
    lines = text.replace(old, new, 1).splitlines()
    catalog = _rows(FIXTURES / "b524-op02-register-names.csv")
    mismatches = names.selector_name_mismatches(lines, catalog)
    assert len(mismatches) == 1
    token = mismatches[0][1]
    try:
        names.decompose(token, vocabulary)
    except names.NameError_:
        pass
    else:
        assert token != mismatches[0][2]

    original_read_text = Path.read_text

    def read_text(path: Path, *args, **kwargs) -> str:
        if path == names.PROTOCOL:
            return "\n".join(lines)
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    assert names.main() == 1
    error = capsys.readouterr().err
    number, found, expected = mismatches[0]
    selector = names._row_selector([cell.strip() for cell in lines[number - 1].split("|")])
    assert f"{names.PROTOCOL.relative_to(names.ROOT)}:{number}: selector" in error
    assert f"GG={selector[0]}, RR={selector[1]}" in error
    assert f"expected {expected!r}, found {found!r}" in error


@pytest.mark.parametrize("selector", ["no selector", "GG=0xFE, RR=0xFFFF"])
def test_backticked_whitespace_is_validated_without_a_catalog_name(
    vocabulary: names.Vocabulary, selector: str
) -> None:
    table = (
        "| Path | Name |\n| --- | --- |\n"
        f"| {selector} | `flow temperature` (note) |\n"
        f"| {selector} | flow temperature (note) |"
    )
    found = names.header_column_names(table.splitlines())
    assert found == [(3, "flow temperature")]
    with pytest.raises(names.NameError_, match="snake_case"):
        names.decompose(found[0][1], vocabulary)


def test_real_page_prose_cells_are_skipped_even_with_catalog_selectors() -> None:
    lines = names.PROTOCOL.read_text(encoding="utf-8").splitlines()
    prose_lines = {160, 161, 162, 1198, 1199, 1200, 1202}
    catalog = {
        (row["group"], row["register"]) for row in
        _rows(FIXTURES / "b524-op02-register-names.csv") if row["name"]
    }
    for number in prose_lines:
        cells = [cell.strip() for cell in lines[number - 1].split("|")]
        assert names._row_selector(cells) in catalog
    assert prose_lines.isdisjoint(number for number, _, _ in names.name_column_cells(lines))
    assert names.mangled_canonical_names(
        lines, _rows(FIXTURES / "b524-op02-register-names.csv")
    ) == []


@pytest.mark.parametrize(
    ("number", "cell", "expected", "selector"),
    [
        (158, "Ventilation operating mode (enum, see register map)",
         "ventilation_operating_mode", ("0x00", "0x0016")),
        (1201, "External energy management enabled (`RR=0x00B6`)",
         "external_energy_management_enabled", ("0x00", "0x00B6")),
        (158, "Ventilation-operating mode (enum, see register map)",
         "ventilation_operating_mode", ("0x00", "0x0016")),
        (158, "!Ventilation  operating--mode! (enum, see register map)",
         "ventilation_operating_mode", ("0x00", "0x0016")),
    ],
)
def test_unquoted_mangled_canonical_name_fails_the_gate(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    number: int, cell: str, expected: str, selector: tuple[str, str]
) -> None:
    lines = names.PROTOCOL.read_text(encoding="utf-8").splitlines()
    column = 3 if number == 158 else 1
    cells = lines[number - 1].split("|")
    cells[column] = f" {cell} "
    lines[number - 1] = "|".join(cells)
    catalog = _rows(FIXTURES / "b524-op02-register-names.csv")
    token = names._strip_code_span(names.TRAILING_NOTE.sub("", cell))
    # The original classification and selector checks still skip this prose.
    assert number not in {n for n, _, _ in names.name_column_cells(lines)}
    assert names.selector_name_mismatches(lines, catalog) == []
    assert names.mangled_canonical_names(lines, catalog) == [(number, token, expected)]

    original_read_text = Path.read_text

    def read_text(path: Path, *args, **kwargs) -> str:
        if path == names.PROTOCOL:
            return "\n".join(lines)
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    assert names.main() == 1
    error = capsys.readouterr().err
    assert error == (
        f"{names.PROTOCOL.relative_to(names.ROOT)}:{number}: "
        f"selector GG={selector[0]}, RR={selector[1]}: "
        f"mangled canonical name: expected {expected!r}, found {token!r}\n"
    )


@pytest.mark.parametrize("selector", ["no selector", "GG=0xFE, RR=0xFFFF"])
def test_normalized_prose_needs_a_catalog_named_selector(selector: str) -> None:
    table = (
        "| Path | Name |\n| --- | --- |\n"
        f"| {selector} | Heating zone operating mode (note) |"
    )
    assert names.mangled_canonical_names(table.splitlines(), CATALOG) == []


def test_already_canonical_cells_are_left_to_existing_selector_checks() -> None:
    lines = names.PROTOCOL.read_text(encoding="utf-8").replace(
        "`ventilation_operating_mode` (enum, see register map)",
        "Ventilation-operating-mode (enum, see register map)", 1,
    ).splitlines()
    catalog = _rows(FIXTURES / "b524-op02-register-names.csv")
    assert names.mangled_canonical_names(lines, catalog) == []
    assert names.selector_name_mismatches(lines, catalog) == [
        (158, "Ventilation-operating-mode", "ventilation_operating_mode")
    ]
