from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "architecture/fixtures/vaillant-semreg-thermal-map-v1.json"
STRUCTURAL = ROOT / "architecture/fixtures/structural-relation-candidates-v1.json"
QUALIFICATION = ROOT / "architecture/fixtures/vaillant-controller-qualification-v1.json"
SPEC = importlib.util.spec_from_file_location(
    "vaillant_semreg_thermal_map", ROOT / "scripts/validate_vaillant_semreg_thermal_map.py"
)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)

SYSTEM_GROUP = "OP=0x02 GG=0x00 II=0x00"
OUTDOOR = "PB=0xB5 SB=0x24 OP=0x02 GG=0x00 II=0x00 RR=0x0073"
FLOW = "PB=0xB5 SB=0x24 OP=0x02 GG=0x00 II=0x00 RR=0x004B"
AVERAGE = "PB=0xB5 SB=0x24 OP=0x02 GG=0x00 II=0x00 RR=0x0095"


def index() -> dict[str, object]:
    return json.loads(INDEX.read_text(encoding="utf-8"))


def structural() -> dict[str, object]:
    return json.loads(STRUCTURAL.read_text(encoding="utf-8"))


def qualification() -> dict[str, object]:
    return json.loads(QUALIFICATION.read_text(encoding="utf-8"))


def rows_by_key(value: dict[str, object]) -> dict[str, dict[str, object]]:
    return {row["native_key"]: row for row in value["mappings"]}  # type: ignore[index]


def rejects(value: dict[str, object], **kwargs: object) -> None:
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(value, **kwargs)


def test_accepts_current_typed_index() -> None:
    CHECKER.validate_index(index())
    CHECKER.validate_index(index(), structural=structural(), qualification=qualification())


def test_rows_are_keyed_by_the_native_identity_of_the_value() -> None:
    rows = index()["mappings"]  # type: ignore[index]
    assert [row["native_key"] for row in rows] == [OUTDOOR, FLOW, AVERAGE]  # type: ignore[index]
    for row in rows:  # type: ignore[union-attr]
        selector = row["native_selector"]  # type: ignore[index]
        assert row["native_key"] == (  # type: ignore[index]
            f"PB={selector['pb']} SB={selector['sb']} OP={selector['operation']} "
            f"GG={selector['group']} II={selector['instance']} RR={selector['register']}"
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("PB", "0xB6"), ("SB", "0x23"), ("OP", "0x06"),
        ("GG", "0x01"), ("II", "0x01"), ("RR", "0x0074"),
    ),
)
def test_rejects_a_native_key_that_differs_from_the_selector(field: str, value: str) -> None:
    mutated = deepcopy(index())
    row = mutated["mappings"][0]  # type: ignore[index]
    parts = dict(part.split("=") for part in row["native_key"].split())  # type: ignore[index]
    parts[field] = value
    row["native_key"] = " ".join(f"{name}={parts[name]}" for name in ("PB", "SB", "OP", "GG", "II", "RR"))  # type: ignore[index]
    rejects(mutated)


def test_rejects_a_gateway_field_or_a_repeated_key_as_the_row_key() -> None:
    mutated = deepcopy(index())
    row = mutated["mappings"][0]  # type: ignore[index]
    row["native_key"] = row["legacy_system_field"]  # type: ignore[index]
    rejects(mutated)

    mutated = deepcopy(index())
    mutated["mappings"][1]["native_key"] = mutated["mappings"][0]["native_key"]  # type: ignore[index]
    rejects(mutated)

    mutated = deepcopy(index())
    del mutated["mappings"][0]["native_key"]  # type: ignore[index]
    rejects(mutated)


def test_every_row_names_its_native_resource_in_native_terms() -> None:
    value = index()
    assert value["native_resources"] == [  # type: ignore[index]
        {"selector": SYSTEM_GROUP, "kind": "b524_semantic_root"},
    ]
    for row in value["mappings"]:  # type: ignore[union-attr]
        assert row["native_resource"] == SYSTEM_GROUP  # type: ignore[index]


def test_rejects_a_row_attached_by_ordinal() -> None:
    # False join: a position in a list is no native identity.
    mutated = deepcopy(index())
    mutated["mappings"][0]["native_resource"] = 0  # type: ignore[index]
    rejects(mutated)

    mutated = deepcopy(index())
    mutated["mappings"][0]["native_resource"] = "0"  # type: ignore[index]
    rejects(mutated)

    sidecar = qualification()
    sidecar["thermal_rows"] = [0, 1, 2]
    rejects(index(), qualification=sidecar)


@pytest.mark.parametrize(
    ("selector", "kind"),
    (
        ("OP=0x06 GG=0x00 II=0x00", "b524_semantic_root"),
        ("OP=0x02 GG=0x01 II=0x00", "b524_semantic_root"),
        ("OP=0x02 GG=0x00 II=0x01", "b524_semantic_root"),
        (SYSTEM_GROUP, "zone_instance"),
    ),
)
def test_rejects_a_false_join_to_another_native_resource(selector: str, kind: str) -> None:
    # Each field of the native resource is varied: operation, group, instance, kind.
    mutated = deepcopy(index())
    mutated["native_resources"] = [{"selector": selector, "kind": kind}]  # type: ignore[index]
    for row in mutated["mappings"]:  # type: ignore[union-attr]
        row["native_resource"] = selector  # type: ignore[index]
    rejects(mutated)


@pytest.mark.parametrize(
    "selector", ("OP=0x06 GG=0x00 II=0x00", "OP=0x02 GG=0x01 II=0x00", "OP=0x02 GG=0x00 II=0x01"),
)
def test_false_join_rule_holds_without_the_closed_row_table(selector: str) -> None:
    # The row's key is held by the system group; a resource with another
    # operation, group or instance is a false join even when it is expected.
    row = {"native_resource": selector, "relation_candidates": {"refs": [], "absence": "none"}}
    resources = {selector: "b524_semantic_root"}
    with pytest.raises(CHECKER.CheckError, match="false join"):
        CHECKER.check_attachment(row, OUTDOOR, resources, (selector, "b524_semantic_root"), {}, "probe")
    CHECKER.check_attachment(
        {**row, "native_resource": SYSTEM_GROUP}, OUTDOOR, {SYSTEM_GROUP: "b524_semantic_root"},
        (SYSTEM_GROUP, "b524_semantic_root"), {}, "probe",
    )


def test_rejects_a_listed_native_resource_that_nothing_uses() -> None:
    mutated = deepcopy(index())
    mutated["native_resources"].append(  # type: ignore[union-attr]
        {"selector": "OP=0x02 GG=0x03 II=zone", "kind": "zone_instance"}
    )
    rejects(mutated)


def test_rejects_a_native_resource_the_index_does_not_list() -> None:
    mutated = deepcopy(index())
    mutated["mappings"][0]["native_resource"] = "OP=0x02 GG=0x03 II=0x00"  # type: ignore[index]
    rejects(mutated)

    mutated = deepcopy(index())
    mutated["native_resources"].append(deepcopy(mutated["native_resources"][0]))  # type: ignore[union-attr]
    rejects(mutated)


def test_relation_candidates_are_an_explicit_absence_for_every_row() -> None:
    for row in index()["mappings"]:  # type: ignore[union-attr]
        candidates = row["relation_candidates"]  # type: ignore[index]
        assert candidates["refs"] == []
        assert isinstance(candidates["absence"], str) and candidates["absence"]


def with_zone_candidate(value: dict[str, object], *, list_zone: bool) -> dict[str, object]:
    mutated = deepcopy(value)
    if list_zone:
        mutated["native_resources"].append(  # type: ignore[union-attr]
            {"selector": "OP=0x02 GG=0x03 II=zone", "kind": "zone_instance"}
        )
    mutated["mappings"][0]["relation_candidates"] = {  # type: ignore[index]
        "refs": ["SRC-SD15-controller-zone"], "absence": None,
    }
    return mutated


def test_accepts_a_reference_whose_endpoints_the_index_lists() -> None:
    CHECKER.validate_index(with_zone_candidate(index(), list_zone=True))


def test_rejects_a_dangling_endpoint() -> None:
    # The candidate names zone_instance, which no listed native resource is.
    rejects(with_zone_candidate(index(), list_zone=False))


def test_rejects_a_dangling_endpoint_with_the_right_kind_but_another_selector() -> None:
    # The listed zone_instance is not the candidate's native position.
    mutated = with_zone_candidate(index(), list_zone=True)
    mutated["native_resources"][-1]["selector"] = "OP=0x02 GG=0x04 II=wrong"  # type: ignore[index]
    rejects(mutated)


def test_rejects_unknown_ordinal_or_unrelated_candidate_references() -> None:
    mutated = with_zone_candidate(index(), list_zone=True)
    mutated["mappings"][0]["relation_candidates"]["refs"] = ["SRC-not-listed"]  # type: ignore[index]
    rejects(mutated)

    mutated = with_zone_candidate(index(), list_zone=True)
    mutated["mappings"][0]["relation_candidates"]["refs"] = [6]  # type: ignore[index]
    rejects(mutated)

    # Both endpoints listed, but neither is the row's own native resource.
    mutated = with_zone_candidate(index(), list_zone=True)
    mutated["native_resources"].append(  # type: ignore[union-attr]
        {"selector": "OP=0x02 GG=0x02 II=circuit", "kind": "circuit_instance"}
    )
    mutated["mappings"][0]["relation_candidates"]["refs"] = ["SRC-SD06-zone-to-circuit"]  # type: ignore[index]
    rejects(mutated)


def test_rejects_both_or_neither_of_references_and_absence() -> None:
    mutated = with_zone_candidate(index(), list_zone=True)
    mutated["mappings"][0]["relation_candidates"]["absence"] = "also absent"  # type: ignore[index]
    rejects(mutated)

    mutated = deepcopy(index())
    mutated["mappings"][0]["relation_candidates"]["absence"] = ""  # type: ignore[index]
    rejects(mutated)

    mutated = deepcopy(index())
    del mutated["mappings"][0]["relation_candidates"]  # type: ignore[index]
    rejects(mutated)


def test_targets_copy_the_element_inventory_disposition() -> None:
    rows = rows_by_key(index())
    for key, fact in ((OUTDOOR, "thermal.measurement.air_temperature"), (FLOW, "thermal.measurement.water_temperature")):
        assert rows[key]["target"] == {
            "definition": {
                "pack": {"id": "helianthus.pack.thermal", "version": "1.0.0"},
                "id": fact, "version": "1.0.0",
            },
            "element_kind": "fact",
            "disposition": "unknown",
            "planes": [],
            "reason": "catalog.reason.subject_unresolved",
        }
        assert rows[key]["semreg_fact"] == fact
    assert rows[AVERAGE]["target"] is None
    assert rows[AVERAGE]["semreg_fact"] is None


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("definition", "pack", "id"), "helianthus.pack.storage"),
        (("definition", "pack", "version"), "1.1.0"),
        (("definition", "id"), "thermal.measurement.outdoor_air_temperature"),
        (("definition", "version"), "1.0.1"),
        (("element_kind",), "dimension"),
        (("disposition",), "member"),
        (("planes",), ["control"]),
        (("reason",), "catalog.reason.no_fact_or_relation"),
    ),
)
def test_rejects_target_drift_in_every_member(path: tuple[str, ...], value: object) -> None:
    mutated = deepcopy(index())
    target = mutated["mappings"][1]["target"]  # type: ignore[index]
    for part in path[:-1]:
        target = target[part]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]
    rejects(mutated)


def test_an_unknown_target_stays_unknown_and_places_no_quantity() -> None:
    mutated = deepcopy(index())
    target = mutated["mappings"][0]["target"]  # type: ignore[index]
    target.update({"disposition": "member", "planes": ["control"], "reason": None})  # type: ignore[union-attr]
    rejects(mutated)

    mutated = deepcopy(index())
    mutated["mappings"][2]["target"] = deepcopy(mutated["mappings"][0]["target"])  # type: ignore[index]
    rejects(mutated)


@pytest.mark.parametrize(
    ("member", "value"),
    (
        ("dimensions", {"thermal.dimension.temperature": "temperature:system_flow"}),
        ("dimensions", {"thermal.dimension.system": "temperature:outdoor_air"}),
        ("semreg_value", {"kind": "quantity", "unit": "unit.kelvin"}),
    ),
)
def test_rejects_role_grammar_or_a_semantic_value_on_a_row(member: str, value: object) -> None:
    mutated = deepcopy(index())
    mutated["mappings"][0][member] = value  # type: ignore[index]
    rejects(mutated)


def test_qualification_sidecar_binds_to_the_rows_by_native_key() -> None:
    assert qualification()["thermal_rows"] == [OUTDOOR, FLOW, AVERAGE]

    sidecar = qualification()
    sidecar["thermal_rows"] = [OUTDOOR, FLOW]
    rejects(index(), qualification=sidecar)

    sidecar = qualification()
    sidecar["thermal_rows"] = [OUTDOOR, FLOW, AVERAGE.replace("RR=0x0095", "RR=0x0096")]
    rejects(index(), qualification=sidecar)

    sidecar = qualification()
    sidecar["thermal_rows"] = ["state.outdoor_temperature", "state.flow_temperature", "state.outdoor_temperature_avg24h"]
    rejects(index(), qualification=sidecar)


MAPPED_TEMPERATURE = {
    "wire_type": "f32_le",
    "unit": "degC",
    "si_unit": "kelvin",
    "conversion": "degrees Celsius plus 273.15",
}


def test_native_rows_keep_native_units_and_delayed_evaluation_separate() -> None:
    rows = rows_by_key(index())
    for key in (OUTDOOR, FLOW):
        assert rows[key]["native_value"] == MAPPED_TEMPERATURE
    assert rows[AVERAGE]["native_value"] == {"wire_type": "f32_le", "unit": "degC"}

    lifecycle = index()["lifecycle"]  # type: ignore[index]
    observation = lifecycle["retained_native_observation"]  # type: ignore[index]
    evaluation = lifecycle["caller_evaluation_context"]  # type: ignore[index]
    assert observation["received_at"] != evaluation["evaluated_at"]  # type: ignore[index]
    assert observation["receipt_monotonic"] != evaluation["evaluate_monotonic"]  # type: ignore[index]
    assert lifecycle["evaluation_cannot_overwrite_receipt"] is True  # type: ignore[index]
    assert lifecycle["freshness_axis"] == "elapsed_monotonic"  # type: ignore[index]


def test_flow_temperature_row_uses_the_canonical_system_field() -> None:
    rows = index()["mappings"]  # type: ignore[index]
    fields = [row["legacy_system_field"] for row in rows]  # type: ignore[index]
    assert "state.flow_temperature" in fields
    assert "state.system_flow_temperature" not in fields


def test_rejects_the_previous_flow_temperature_field() -> None:
    mutated = deepcopy(index())
    row = mutated["mappings"][1]  # type: ignore[index]
    assert row["legacy_system_field"] == "state.flow_temperature"  # type: ignore[index]
    row["legacy_system_field"] = "state.system_flow_temperature"  # type: ignore[index]
    rejects(mutated)


def test_rejects_operation_or_service_family_substitution() -> None:
    mutated = deepcopy(index())
    row = mutated["mappings"][1]  # type: ignore[index]
    row["native_selector"]["operation"] = "0x06"  # type: ignore[index]
    rejects(mutated)

    mutated = deepcopy(index())
    mutated["native_distinctions"]["b509_substitutable_for_b524_rows"] = True  # type: ignore[index]
    rejects(mutated)


def test_rejects_type_unit_or_register_drift() -> None:
    mutated = deepcopy(index())
    row = mutated["mappings"][0]  # type: ignore[index]
    row["native_value"]["wire_type"] = "u16"  # type: ignore[index]
    rejects(mutated)

    mutated = deepcopy(index())
    row = mutated["mappings"][0]  # type: ignore[index]
    row["native_value"]["unit"] = "unit.celsius"  # type: ignore[index]
    rejects(mutated)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("destination", "0x08"),
        ("controller_family", "HMU"),
        ("request_direction", "target_to_initiator"),
        ("value_direction", "initiator_to_target"),
    ),
)
def test_rejects_destination_family_or_direction_drift(field: str, value: str) -> None:
    mutated = deepcopy(index())
    row = mutated["mappings"][0]  # type: ignore[index]
    row["native_selector"][field] = value  # type: ignore[index]
    rejects(mutated)

    mutated = deepcopy(index())
    row = mutated["mappings"][2]  # type: ignore[index]
    row["native_selector"]["register"] = "0x0073"  # type: ignore[index]
    rejects(mutated)


def test_rejects_withheld_and_nonclaim_drift() -> None:
    mutated = deepcopy(index())
    row = mutated["mappings"][2]  # type: ignore[index]
    row["disposition"] = "exact"  # type: ignore[index]
    rejects(mutated)

    mutated = deepcopy(index())
    mutated["nonclaims"]["write_route_established"] = True  # type: ignore[index]
    rejects(mutated)


@pytest.mark.parametrize("key", (OUTDOOR, FLOW))
@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("wire_type", "u16"),
        ("unit", "unit.celsius"),
        ("unit", "kelvin"),
        ("si_unit", None),
        ("si_unit", "unit.celsius"),
        ("conversion", None),
        ("conversion", "degrees Celsius"),
    ),
)
def test_mapped_temperature_rejects_each_field(key: str, field: str, value: object) -> None:
    # wire_type: u16 replaces f32_le.
    # unit: unit.celsius or kelvin replaces the native unit degC.
    # si_unit: absent, or unit.celsius stated as the SI unit.
    # conversion: absent, or degrees Celsius without plus 273.15.
    mutated = deepcopy(index())
    native = rows_by_key(mutated)[key]["native_value"]
    if value is None:
        del native[field]  # type: ignore[index]
    else:
        native[field] = value  # type: ignore[index]
    rejects(mutated)


def test_unmapped_average_keeps_the_native_unit_only() -> None:
    mutated = deepcopy(index())
    native = rows_by_key(mutated)[AVERAGE]["native_value"]
    native["si_unit"] = "kelvin"  # type: ignore[index]
    native["conversion"] = "degrees Celsius plus 273.15"  # type: ignore[index]
    rejects(mutated)


def docs_root() -> Path:
    raw = os.environ.get("PLATFORM_DOCS_ROOT")
    if raw:
        return Path(raw)
    for candidate in (ROOT / "checkouts" / "docs", ROOT / ".pytest_cache" / "platform-docs"):
        if candidate.is_dir():
            return candidate
    raise OSError("PLATFORM_DOCS_ROOT is required")


def handoff_pages() -> dict[str, str]:
    docs = docs_root()
    def load(path: str) -> str:
        base = docs if path == "api/semantic-snapshot-read.md" else ROOT
        return (base / path).read_text(encoding="utf-8")
    return {path: load(path) for path, *_rest in CHECKER.PAGE_RULES}


def test_handoff_pages_state_the_native_unit_and_both_si_statements() -> None:
    CHECKER.check_handoff_pages(handoff_pages())


def _without_row_token(text: str, marker: str, token: str) -> str:
    """Drop one statement from the marked row and keep it somewhere else on the page."""
    lines = text.splitlines()
    found = False
    for index, line in enumerate(lines):
        if marker not in line:
            continue
        if token not in line:
            raise AssertionError(f"row {marker!r} has no {token!r}")
        lines[index] = line.replace(token, "omitted")
        found = True
        break
    if not found:
        raise AssertionError(marker)
    body = "\n".join(lines)
    if token not in body:
        body += f"\n\nunrelated mention of {token}\n"
    return body


FIELDS = ("native", "semantic", "si_unit", "conversion")
STATEMENT_CASES = [
    pytest.param(path, marker, field, token, id=f"{path}:{marker}:{field}")
    for path, marker, *tokens in CHECKER.PAGE_RULES
    for field, token in zip(FIELDS, tokens)
    if token is not None
]


@pytest.mark.parametrize(("path", "marker", "field", "token"), STATEMENT_CASES)
def test_handoff_page_rejects_a_missing_statement(path: str, marker: str, field: str, token: str) -> None:
    # native: the native-unit spelling is removed from this mapped row only.
    # semantic: the SemReg unit identifier is removed from this mapped row only.
    # si_unit: the SI-unit statement is removed from this mapped row only.
    # conversion: the conversion statement is removed from this mapped row only.
    # Another occurrence remains on the page, so a whole-page search would pass.
    pages = handoff_pages()
    pages[path] = _without_row_token(pages[path], marker, token)
    assert token in pages[path]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.check_handoff_pages(pages)


def test_every_mapped_row_with_native_evidence_names_its_native_unit() -> None:
    # The native-unit field is the native spelling, never a SemReg identifier.
    natives = [native for _path, _marker, native, *_rest in CHECKER.PAGE_RULES if native is not None]
    assert natives
    assert all("unit." not in native for native in natives)
    assert sum(native == "°C" for native in natives) == 8


def test_heating_manual_row_without_native_celsius_fails() -> None:
    # unit.celsius alone is the SemReg identifier. Dropping the native °C from
    # the row fails even though the SemReg identifier stays.
    pages = handoff_pages()
    path = "architecture/zone-setpoint-semreg-cutover.md"
    row = CHECKER.mapped_row(path, pages[path], "| Heating manual |")
    stripped = row.replace("°C catalog label, ", "catalog label, ")
    assert "°C" not in stripped and "unit.celsius" in stripped
    pages[path] = pages[path].replace(row, stripped)
    with pytest.raises(CHECKER.CheckError, match="native unit"):
        CHECKER.check_handoff_pages(pages)


def test_a_semreg_identifier_is_refused_as_the_native_unit() -> None:
    page = "| Heating manual | 0x0022, f32, `unit.celsius` (SI unit kelvin, degrees Celsius plus 273.15) |\n"
    with pytest.raises(CHECKER.CheckError, match="SemReg identifier"):
        CHECKER.check_handoff_page(
            "page.md", page, "| Heating manual |", "unit.celsius", None, *CHECKER.TEMPERATURE_SI,
        )


def _table_spans(text: str) -> list[tuple[int, int]]:
    """Start and end line index of each run of pipe-prefixed lines."""
    lines = text.splitlines()
    spans: list[tuple[int, int]] = []
    start = None
    for index, line in enumerate(lines + [""]):
        is_row = line.strip().startswith("|")
        if is_row and start is None:
            start = index
        elif not is_row and start is not None:
            spans.append((start, index))
            start = None
    return spans


def _handoff_spans(path: str, text: str) -> list[tuple[int, int]]:
    lines = text.splitlines()
    markers = tuple(marker for rule_path, marker, *_rest in CHECKER.PAGE_RULES if rule_path == path)
    headers = tuple(header for rule_path, header in CHECKER.WITHHELD_TABLE_HEADERS if rule_path == path)
    return [
        (start, end) for start, end in _table_spans(text)
        if any(marker in lines[index] for index in range(start, end) for marker in markers)
        or any(lines[start].strip().startswith(header) for header in headers)
    ]


def _expected_unmapped_rows(path: str, text: str) -> list[str]:
    lines = text.splitlines()
    markers = tuple(marker for rule_path, marker, *_rest in CHECKER.PAGE_RULES if rule_path == path)
    rows: list[str] = []
    for start, end in _handoff_spans(path, text):
        assert CHECKER.is_table_separator(lines[start + 1]), (path, lines[start])
        for line in lines[start + 2:end]:
            if not any(marker in line for marker in markers):
                rows.append(line)
    return rows


def _rows_outside_handoff_tables(path: str, text: str) -> list[str]:
    lines = text.splitlines()
    inside = {index for start, end in _handoff_spans(path, text) for index in range(start, end)}
    return [
        line for start, end in _table_spans(text) for index, line in enumerate(lines[start:end], start)
        if index not in inside and not CHECKER.is_table_separator(line)
    ]


def _suffix_line(text: str, row: str, suffix: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line == row:
            lines[index] = line + suffix
            return "\n".join(lines)
    raise AssertionError(row)


def test_unmapped_rows_are_every_non_mapped_body_row_of_a_handoff_table() -> None:
    pages = handoff_pages()
    for path, text in pages.items():
        assert CHECKER.unmapped_handoff_rows(path, text) == _expected_unmapped_rows(path, text)


def test_every_page_has_a_handoff_table() -> None:
    pages = handoff_pages()
    for path, text in pages.items():
        assert CHECKER.handoff_tables(path, text), path


def test_rows_outside_the_handoff_tables_are_not_unmapped_rows() -> None:
    # Unrelated tables on a hand-off page are outside this contract. A row there may
    # name an SI unit or 273.15 without being read as a withheld hand-off row.
    pages = handoff_pages()
    outside = _rows_outside_handoff_tables(
        "api/semantic-snapshot-read.md", pages["api/semantic-snapshot-read.md"],
    )
    assert len(outside) > 20
    seen = 0
    for path, text in pages.items():
        for row in _rows_outside_handoff_tables(path, text):
            seen += 1
            assert row not in CHECKER.unmapped_handoff_rows(path, text)
            mutated = dict(pages)
            mutated[path] = _suffix_line(text, row, " SI unit kelvin, degrees Celsius plus 273.15")
            CHECKER.check_handoff_pages(mutated)
    assert seen > len(outside)


def test_handoff_table_header_may_name_the_si_unit() -> None:
    pages = handoff_pages()
    for path, text in pages.items():
        for start, _end in _handoff_spans(path, text):
            header = text.splitlines()[start]
            mutated = dict(pages)
            mutated[path] = _suffix_line(text, header, " SI unit and conversion |")
            CHECKER.check_handoff_pages(mutated)


@pytest.mark.parametrize(("path", "header"), CHECKER.WITHHELD_TABLE_HEADERS)
def test_a_missing_withheld_row_table_fails(path: str, header: str) -> None:
    pages = handoff_pages()
    assert header in pages[path]
    pages[path] = pages[path].replace(header, "| Renamed |")
    with pytest.raises(CHECKER.CheckError):
        CHECKER.check_handoff_pages(pages)


@pytest.mark.parametrize(
    ("path", "marker"),
    (
        ("architecture/zone-setpoint-semreg-cutover.md", "| Cooling manual |"),
        ("architecture/zone-setpoint-semreg-cutover.md", "| Cooling computed effective |"),
        ("architecture/zone-setpoint-semreg-cutover.md", "| Quick-veto override |"),
        ("architecture/dhw-measured-temperature-cutover.md", "| `(0x02, 0x01, 0x00, 0x0004)` |"),
        ("architecture/dhw-measured-temperature-cutover.md", "| `(0x02, 0x01, 0x00, 0x0008)` |"),
        ("architecture/dhw-setpoint-semreg-cutover.md", "| DHW flow ceiling |"),
        ("architecture/dhw-setpoint-semreg-cutover.md", "| Boiler-direct desired temperature candidate |"),
        ("architecture/solar-loop-temperature-cutover.md", "| Collector candidate |"),
        ("architecture/humidity-semreg-cutover.md", "| Configuration threshold |"),
        ("architecture/b524-semantic-mapping.md", "`PB=0xB5 SB=0x24 OP=0x02 GG=0x00 II=0x00 RR=0x0095`"),
        ("architecture/outdoor-temperature-semreg-cutover.md", "state.outdoor_temperature_avg24h"),
        ("architecture/circuit-temperature-cutover.md", "| `0x0007` |"),
        ("architecture/circuit-temperature-cutover.md", "| `0x0020` |"),
        ("architecture/boiler-temperature-semreg-mapping.md", "| Return: `ReturnTemperatureC`"),
        ("architecture/cylinder-temperature-cutover.md", "| `0x0001` |"),
    ),
)
def test_unmapped_page_row_rejects_a_conversion(path: str, marker: str) -> None:
    # A withheld row is not on a fixed list. Deriving every non-mapped table row
    # rejects a conversion added to that row, including one the list never named.
    pages = handoff_pages()
    rows = [row for row in CHECKER.unmapped_handoff_rows(path, pages[path]) if marker in row]
    assert len(rows) == 1
    pages[path] = _suffix_line(pages[path], rows[0], " degrees Celsius plus 273.15")
    with pytest.raises(CHECKER.CheckError):
        CHECKER.check_handoff_pages(pages)


def test_unmapped_humidity_row_rejects_the_ratio_conversion() -> None:
    pages = handoff_pages()
    path = "architecture/humidity-semreg-cutover.md"
    rows = [row for row in CHECKER.unmapped_handoff_rows(path, pages[path]) if "| Configuration threshold |" in row]
    assert len(rows) == 1
    pages[path] = _suffix_line(pages[path], rows[0], " percent divided by 100")
    with pytest.raises(CHECKER.CheckError):
        CHECKER.check_handoff_pages(pages)


def test_every_derived_unmapped_row_rejects_a_conversion() -> None:
    pages = handoff_pages()
    seen = 0
    for path, text in pages.items():
        for row in CHECKER.unmapped_handoff_rows(path, text):
            seen += 1
            mutated = dict(pages)
            mutated[path] = _suffix_line(text, row, " degrees Celsius plus 273.15")
            with pytest.raises(CHECKER.CheckError):
                CHECKER.check_handoff_pages(mutated)
    assert seen > len(CHECKER.PAGE_RULES)


@pytest.mark.parametrize(
    "wording",
    (
        "; converted to kelvin",
        " `unit.kelvin`",
        " Kelvin",
        "; converts to a ratio",
        " as a fraction",
        " plus 273",
        " value divided by 100",
        " SI quantity",
        "; conversion applies",
        " `unit.one`",
        " `unit.celsius`",
        " `unit.percent`",
        " `unit.watt`",
        " `unit.dimensionless`",
    ),
)
def test_unmapped_row_rejects_alternate_si_wording(wording: str) -> None:
    # Not only the canonical phrases: any SI unit, SemReg unit id or conversion
    # wording on a row with no mapped quantity fails, on every derived unmapped row.
    pages = handoff_pages()
    for path, text in pages.items():
        for row in CHECKER.unmapped_handoff_rows(path, text):
            mutated = dict(pages)
            mutated[path] = _suffix_line(text, row, wording)
            with pytest.raises(CHECKER.CheckError):
                CHECKER.check_handoff_pages(mutated)


def test_unmapped_cooling_row_rejects_a_semantic_unit_id() -> None:
    # Cooling manual keeps the native °C. unit.celsius and unit.percent are
    # SemReg unit ids, so either one on that withheld row fails.
    pages = handoff_pages()
    path = "architecture/zone-setpoint-semreg-cutover.md"
    rows = [row for row in CHECKER.unmapped_handoff_rows(path, pages[path]) if "| Cooling manual |" in row]
    assert len(rows) == 1
    assert "unit." not in rows[0]
    for suffix in (" `unit.celsius`", " `unit.percent`"):
        mutated = dict(pages)
        mutated[path] = _suffix_line(pages[path], rows[0], suffix)
        with pytest.raises(CHECKER.CheckError):
            CHECKER.check_handoff_pages(mutated)


def test_snapshot_example_keeps_its_pack_unit_and_rejects_another() -> None:
    # The storage example already names unit.percent as that pack's unit. That
    # one id stays. Adding unit.celsius, or a second unit.percent, still fails.
    pages = handoff_pages()
    path = "api/semantic-snapshot-read.md"
    rows = [row for row in CHECKER.unmapped_handoff_rows(path, pages[path]) if "helianthus.pack.storage" in row]
    assert len(rows) == 1
    assert rows[0].count("unit.percent") == 1
    CHECKER.check_handoff_pages(pages)
    for suffix in (" `unit.celsius`", " `unit.percent`"):
        mutated = dict(pages)
        mutated[path] = _suffix_line(pages[path], rows[0], suffix)
        with pytest.raises(CHECKER.CheckError):
            CHECKER.check_handoff_pages(mutated)


def test_unmapped_cooling_row_rejects_converted_to_kelvin() -> None:
    pages = handoff_pages()
    path = "architecture/zone-setpoint-semreg-cutover.md"
    rows = [row for row in CHECKER.unmapped_handoff_rows(path, pages[path]) if "| Cooling manual |" in row]
    assert len(rows) == 1
    pages[path] = pages[path].replace(rows[0], rows[0].replace("°C", "°C; converted to kelvin", 1))
    assert pages[path] != handoff_pages()[path]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.check_handoff_pages(pages)


def test_unmapped_row_keeps_a_native_candidate_kelvin_difference() -> None:
    # A bare K is the native candidate unit of a temperature difference, not a conversion.
    pages = handoff_pages()
    path = "architecture/cylinder-temperature-cutover.md"
    assert any("candidate K" in row for row in CHECKER.unmapped_handoff_rows(path, pages[path]))
    CHECKER.check_handoff_pages(pages)


def test_humidity_native_unit_is_percent_not_the_semantic_target() -> None:
    # unit.percent alone is the SemReg quantity id. It does not satisfy the wire unit.
    pages = handoff_pages()
    path = "architecture/humidity-semreg-cutover.md"
    pages[path] = pages[path].replace(
        "Native unit percent (`%`). Semantic target `unit.percent`.",
        "Native unit `unit.percent`.",
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.check_handoff_pages(pages)


def test_humidity_semantic_target_precedes_the_conversion() -> None:
    pages = handoff_pages()
    path = "architecture/humidity-semreg-cutover.md"
    pages[path] = pages[path].replace(
        "Semantic target `unit.percent`. SI unit a ratio, percent divided by 100.",
        "SI unit a ratio, percent divided by 100. Semantic target `unit.percent`.",
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.check_handoff_pages(pages)


def test_humidity_page_keeps_the_wire_unit_apart_from_the_semantic_target() -> None:
    text = (ROOT / "architecture/humidity-semreg-cutover.md").read_text(encoding="utf-8")
    assert text.count("Native unit percent (`%`). Semantic target `unit.percent`.") == 3
    assert "The native unit stays percent (`%`). The semantic target is `unit.percent`." in text
    assert "The native unit stays `unit.percent`" not in text
    assert "Native unit `unit.percent`" not in text


def test_rejects_receipt_evaluation_boundary_or_freshness_drift() -> None:
    mutated = deepcopy(index())
    lifecycle = mutated["lifecycle"]  # type: ignore[index]
    lifecycle["caller_evaluation_context"]["evaluated_at"] = lifecycle["retained_native_observation"]["received_at"]  # type: ignore[index]
    rejects(mutated)

    mutated = deepcopy(index())
    lifecycle = mutated["lifecycle"]  # type: ignore[index]
    lifecycle["evaluation_cannot_overwrite_receipt"] = False  # type: ignore[index]
    rejects(mutated)

    mutated = deepcopy(index())
    lifecycle = mutated["lifecycle"]  # type: ignore[index]
    lifecycle["freshness_axis"] = "wall_clock"  # type: ignore[index]
    rejects(mutated)
