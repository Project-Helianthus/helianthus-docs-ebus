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
        ("flow_temperature_limit_at_flow_rate_maximum", "bound precedes its object"),
        ("room_temperature_setpoint_at_holiday_minimum", "bound precedes its object"),
        ("zone_name_year", "order of the parts"),
        ("holiday_start_date_hour", "order of the parts"),
        ("date_year_1", "order of the parts"),
        ("source_temperature_limit_at_flow_rate_maximum", "bound precedes its object"),
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
    """A canonical write-template row is found by its selector, not by its label syntax."""
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
