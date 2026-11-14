from __future__ import annotations

import json
import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("naming_surface", ROOT / "scripts/check_naming_surface_contract.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def documents():
    return [(ROOT / path).read_text() for path in (
        "api/graphql.md", "api/mcp.md", "deployment/prometheus-semantic-coverage.md")]


def test_adopted_contract():
    CHECKER.validate(*documents())


@pytest.mark.parametrize("old,new", [
    ("type zone_state", "type ZoneState"),
    ("zone_room_temperature: Float", "currentTempC: Float"),
    ("zone_room_humidity: Float", "currentHumidityPct: Float"),
])
def test_removed_graphql_spelling_rejected(old, new):
    docs = documents()
    assert old in docs[0]
    docs[0] = docs[0].replace(old, new)
    with pytest.raises(ValueError):
        CHECKER.validate(*docs)


# Independent pin of the accepted setter keys; the synthetic reference below
# is built from it, never from the page under test.
SETTER_KEYS = {
    "set_system_config": {
        "dhw_outdoor_bivalence_temperature_limit": False,
        "room_humidity_limit_maximum": False,
        "adaptive_heating_curve_enabled": False,
        "heating_outdoor_bivalence_temperature_limit": False,
        "heating_flow_temperature_setpoint_maximum_at_heat_pump_fault": False,
        "maintenance_date": False,
        "dhw_flow_temperature_setpoint_maximum": False,
        "installer_name": False,
        "installer_phone_number": False,
        "installer_access_code": False,
    },
    "set_zone_config": {
        "zone_room_temperature_setpoint_at_holiday": False,
        "heating_zone_operating_mode": False,
        "zone_room_temperature_setpoint_at_quick_veto": False,
        "heating_zone_room_manual_temperature_setpoint": False,
        "zone_quick_veto_time": False,
    },
    "set_boiler_config": {
        "maximum_heating_flow_temperature_setpoint": False,
        "maximum_dhw_flow_temperature_setpoint": False,
        "heating_partial_load_power": False,
        "dhw_partial_load_power": False,
        "installer_phone_number": False,
        "installerMenuCode": True,
    },
}
FAMILY_OF = {setter: family for family, (setter, _) in CHECKER.SETTER_KEY_FAMILIES.items()}
SETTER_KEY_CASES = [(FAMILY_OF[setter], key)
                    for setter, keys in SETTER_KEYS.items() for key in keys]
PREVIOUS_KEY_CASES = [(family, key)
                      for family, keys in CHECKER.PREVIOUS_SETTER_KEYS.items() for key in keys]


def setter_reference(keys=SETTER_KEYS):
    setters = {}
    for setter, entries in keys.items():
        rows = []
        for key, is_open in entries.items():
            row = {"key": key, "open": is_open}
            if is_open:
                row["open_question"] = "Synthetic open question."
            rows.append(row)
        setters[setter] = {"keys": rows}
    return {"format": CHECKER.SETTER_KEY_FORMAT, "setters": setters}


def write_setter_reference(root, document):
    path = root / CHECKER.SETTER_KEY_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document if isinstance(document, str) else json.JSONEncoder().encode(document))


def loaded_setter_keys(tmp_path, keys=SETTER_KEYS):
    write_setter_reference(tmp_path, setter_reference(keys))
    return CHECKER.load_setter_keys(tmp_path)


def family_section(page, family):
    heading = CHECKER.SETTER_KEY_FAMILIES[family][1]
    start = page.index(heading + "\n")
    following = page.find("\n#", start + len(heading))
    return start, (len(page) if following < 0 else following + 1)


def replace_in_family(page, family, old, new):
    start, end = family_section(page, family)
    section = page[start:end]
    assert section.count(old) == 1, (family, old)
    return page[:start] + section.replace(old, new) + page[end:]


def family_row(page, family, key):
    start, end = family_section(page, family)
    rows = [line for line in page[start:end].splitlines()
            if line.startswith("| `" + key + "` |")]
    assert len(rows) == 1, (family, key)
    return rows[0] + "\n"


@pytest.mark.parametrize("family", CHECKER.SETTER_FAMILIES)
def test_missing_setter_family_rejected(family):
    docs = documents()
    key = CHECKER.SETTER_FAMILIES[family][0]
    assert key in docs[1]
    docs[1] = docs[1].replace(key, "removed_setter")
    with pytest.raises(ValueError, match="setter family"):
        CHECKER.validate(*docs)


@pytest.mark.parametrize("family", CHECKER.SETTER_KEY_FAMILIES)
def test_missing_setter_key_table_rejected(family):
    # Catches a family heading or table dropped from the page.
    docs = documents()
    heading = CHECKER.SETTER_KEY_FAMILIES[family][1]
    assert docs[1].count(heading + "\n") == 1
    docs[1] = docs[1].replace(heading + "\n", "#### Removed setter table\n")
    with pytest.raises(ValueError, match="setter family"):
        CHECKER.validate(*docs)


def test_setter_keys_match_reference(tmp_path):
    keys = loaded_setter_keys(tmp_path)
    assert {family: set(entries) for family, entries in keys.items()} == {
        FAMILY_OF[setter]: set(entries) for setter, entries in SETTER_KEYS.items()}
    CHECKER.validate(*documents(), setter_keys=keys)


@pytest.mark.parametrize("family,key", SETTER_KEY_CASES)
def test_missing_setter_key_rejected(tmp_path, family, key):
    # Each case catches the page dropping one accepted key of one family.
    docs = documents()
    docs[1] = replace_in_family(docs[1], family, family_row(docs[1], family, key), "")
    with pytest.raises(ValueError, match="missing setter key: " + family):
        CHECKER.validate(*docs, setter_keys=loaded_setter_keys(tmp_path))


@pytest.mark.parametrize("family,key", SETTER_KEY_CASES)
def test_extra_setter_key_rejected(tmp_path, family, key):
    # Each case catches the page listing a key the gateway no longer accepts.
    setter = CHECKER.SETTER_KEY_FAMILIES[family][0]
    reduced = {name: dict(entries) for name, entries in SETTER_KEYS.items()}
    del reduced[setter][key]
    with pytest.raises(ValueError, match="extra setter key: " + family):
        CHECKER.validate(*documents(), setter_keys=loaded_setter_keys(tmp_path, reduced))


@pytest.mark.parametrize("family", CHECKER.SETTER_KEY_FAMILIES)
def test_synthetic_extra_row_rejected(tmp_path, family):
    docs = documents()
    first = docs[1][slice(*family_section(docs[1], family))].split("\n| `", 1)[1]
    row = "| `" + first.split("\n", 1)[0] + "\n"
    docs[1] = replace_in_family(docs[1], family, row, row + row.replace(
        row.split("`")[1], "synthetic_extra_setter_key", 1))
    with pytest.raises(ValueError, match="extra setter key: " + family):
        CHECKER.validate(*docs, setter_keys=loaded_setter_keys(tmp_path))


@pytest.mark.parametrize("family,key", PREVIOUS_KEY_CASES)
def test_previous_setter_key_listed_rejected(tmp_path, family, key):
    # Each case catches a previous spelling returning to its family table,
    # with or without the gateway reference.
    docs = documents()
    row = family_row(docs[1], family, next(iter(
        dict(CHECKER.documented_setter_rows(docs[1], CHECKER.SETTER_KEY_FAMILIES[family][1])))))
    docs[1] = replace_in_family(docs[1], family, row, row + row.replace(
        row.split("`")[1], key, 1))
    for setter_keys in (None, loaded_setter_keys(tmp_path)):
        with pytest.raises(ValueError, match="previous setter key"):
            CHECKER.validate(*docs, setter_keys=setter_keys)


@pytest.mark.parametrize("key", sorted(set().union(*CHECKER.PREVIOUS_SETTER_KEYS.values())
                                       - {"installerMenuCode"}))
@pytest.mark.parametrize("index", (0, 1))
def test_previous_setter_key_named_rejected(tmp_path, key, index):
    # Each case catches prose naming a previous spelling as a current key.
    docs = documents()
    docs[index] += "\nThe setter accepts `" + key + "`.\n"
    with pytest.raises(ValueError, match="previous setter key named: " + key):
        CHECKER.validate(*docs, setter_keys=loaded_setter_keys(tmp_path))


def test_open_setter_key_stays_provisional(tmp_path):
    docs = documents()
    row = family_row(docs[1], "boiler", "installerMenuCode")
    assert "Provisional" in row
    docs[1] = replace_in_family(docs[1], "boiler", row, row.replace("Provisional", "Settled"))
    with pytest.raises(ValueError, match="not provisional"):
        CHECKER.validate(*docs, setter_keys=loaded_setter_keys(tmp_path))


def _drop_format(document):
    del document["format"]


def _wrong_format(document):
    document["format"] = "synthetic.other.v1"


def _drop_family(document):
    del document["setters"]["set_zone_config"]


def _empty_family(document):
    document["setters"]["set_system_config"]["keys"] = []


def _duplicate_key(document):
    rows = document["setters"]["set_boiler_config"]["keys"]
    rows.append(dict(rows[0]))


def _open_without_question(document):
    for row in document["setters"]["set_boiler_config"]["keys"]:
        row.pop("open_question", None)


def _camel_case_key(document):
    document["setters"]["set_zone_config"]["keys"][0]["key"] = "holidaySetpoint"


def _missing_open_flag(document):
    del document["setters"]["set_system_config"]["keys"][0]["open"]


@pytest.mark.parametrize("mutate", [
    _drop_format, _wrong_format, _drop_family, _empty_family, _duplicate_key,
    _open_without_question, _camel_case_key, _missing_open_flag,
])
def test_malformed_setter_reference_fails_closed(tmp_path, mutate):
    document = setter_reference()
    mutate(document)
    write_setter_reference(tmp_path, document)
    with pytest.raises(ValueError, match="setter key reference"):
        CHECKER.load_setter_keys(tmp_path)


@pytest.mark.parametrize("content", [None, "{not json", "[]"])
def test_missing_or_unreadable_setter_reference_fails_closed(tmp_path, content):
    if content is not None:
        write_setter_reference(tmp_path, content)
    with pytest.raises(ValueError, match="setter key reference"):
        CHECKER.load_setter_keys(tmp_path)


def test_main_fails_closed_without_setter_reference(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["check", "--root", str(ROOT), "--gateway-root", str(tmp_path)])
    assert CHECKER.main() == 1
    assert "setter key reference missing" in capsys.readouterr().err


def test_main_unverified_without_reference(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["check", "--root", str(tmp_path)])
    assert CHECKER.main() == 2
    assert "UNVERIFIED" in capsys.readouterr().err


@pytest.mark.parametrize("name", ["ebus.invoke", "ebus.devices", "ebus_invoke", "ebus_devices"])
def test_removed_tool_not_reissued(name):
    docs = documents()
    docs[1] = docs[1].replace("| ebus_v1_registry_devices_list |", "| " + name + " |")
    with pytest.raises(ValueError):
        CHECKER.validate(*docs)


def test_undocumented_registration_rejected():
    docs = documents()
    _, rows = CHECKER.mcp.documented_rows(docs[1])
    extra = copy.deepcopy(rows[0])
    extra["name"] = "synthetic_undocumented_tool"
    with pytest.raises(ValueError, match="parity"):
        CHECKER.validate(*docs, registration={"schema_version": 1, "tools": rows + [extra]})


def test_changed_constant_unit_rejected():
    docs = documents()
    old = "| `helianthus_semantic_evidence_age` | `gauge` | `connector, dimension, domain, fact_id, pack, unit` | `seconds` |"
    assert old in docs[2]
    docs[2] = docs[2].replace(old, old.replace("`seconds`", "`milliseconds`"))
    with pytest.raises(ValueError):
        CHECKER.validate(*docs)


def test_m2m_unit_has_six_explicit_exclusions():
    assert len(CHECKER.EXCLUSIONS) == 6
    assert all(reason == "shape differs; docs-ebus#1166" for reason in CHECKER.EXCLUSIONS.values())


@pytest.mark.parametrize("field", CHECKER.mcp.FIELDS)
def test_registration_each_identity_and_attribute_rejected(field):
    # name catches tool replacement; surface and registration_profile catch
    # moves between scopes; availability_condition catches enablement changes;
    # implementation_source catches a changed owner binding.
    docs = documents()
    _, rows = CHECKER.mcp.documented_rows(docs[1])
    changed = copy.deepcopy(rows)
    changed[0][field] = "synthetic_changed_" + field
    with pytest.raises(ValueError):
        CHECKER.validate(*docs, registration={"schema_version": 1, "tools": changed})


@pytest.mark.parametrize("adopted,removed", [
    ("current_temp_c", "currentTempC"),
    ("target_temp_c", "targetTempC"),
    ("operating_mode", "operatingMode"),
    ("semantic_snapshot", "semanticSnapshot"),
    ("asset_ids", "assetIds"),
    ("asset_id", "assetId"),
    ("snapshot_id", "snapshotId"),
    ("pack_id", "packId"),
    ("pack_version", "packVersion"),
    ("fact_id", "factId"),
    ("candidate_id", "candidateId"),
    ("item_id", "itemId"),
    ("source_items", "sourceItems"),
    ("unavailable_reason", "unavailableReason"),
    ("zone_update", "zoneUpdate"),
])
def test_removed_member_rejected_in_additional_example(adopted, removed):
    # Each pair catches a production serializer or schema member reverting
    # that one spelling; value selection and native identity stay unchanged.
    docs = documents()
    example = "\n```graphql\ntype synthetic_example { " + adopted + ": String }\n```\n"
    CHECKER.validate(docs[0] + example, *docs[1:])
    with pytest.raises(ValueError, match="GraphQL"):
        CHECKER.validate(docs[0] + example.replace(adopted, removed), *docs[1:])


@pytest.mark.parametrize("old,adopted", CHECKER.OPERATION_NAMES.items())
@pytest.mark.parametrize("index", (0, 1))
def test_operation_each_member_and_type_rejects_removed_spelling(old, adopted, index):
    # Each row catches the corresponding schema member/type or serializer key
    # reverting independently in either the page or the example assertions.
    docs = [(ROOT / name).read_text() for name in (
        "api/semantic-operation-route.md", "tests/semantic_operation_route_contract.json")]
    CHECKER.validate_operation(*docs)
    assert adopted in docs[index]
    docs[index] = docs[index].replace(adopted, old)
    with pytest.raises(ValueError, match="operation"):
        CHECKER.validate_operation(*docs)


@pytest.mark.parametrize("mutation", [None, "tool", "metric"])
def test_offline_parity_branch(tmp_path, mutation):
    # Independent, fixed synthetic candidate inventory; provenance is not published.
    fixture = json.loads((ROOT / "tests/fixtures/naming_surface_inventory.json").read_text())
    if mutation == "tool":
        fixture["tools"][0]["name"] = "synthetic_changed_tool"
    if mutation == "metric":
        fixture["families"][0]["name"] = "synthetic_changed_metric"
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "mcp-tool-inventory.md").write_text(
        "```json\n" + json.dumps({"schema_version": 1, "tools": fixture["tools"]}) + "\n```\n")
    (docs / "metrics-inventory.json").write_text(json.dumps({"families": fixture["families"]}))
    write_setter_reference(tmp_path, setter_reference())
    if mutation is None:
        CHECKER.validate_root(ROOT, tmp_path)
    else:
        with pytest.raises(ValueError, match="parity"):
            CHECKER.validate_root(ROOT, tmp_path)


@pytest.mark.parametrize("adopted,removed", [
    ('heating_mode', 'heatingMode'),
    ('energy_category', 'EnergyCategory'),
    ('energy_bucket', 'EnergyBucket'),
    ('REGULATOR', 'regulator'),
    ('FUNCTION_MODULE', 'function_module'),
    ('zones_update', 'zonesUpdate'),
    ('energy_totals_update', 'energyTotalsUpdate'),
    ('system_update', 'systemUpdate'),
    ('circuits_update', 'circuitsUpdate'),
    ('INTERPRETED', 'interpreted'),
    ('GPIO_ONLY', 'gpio_only'),
    ('ABSENT', 'absent'),
    ('CONTROLLER_UNREACHABLE', 'controller_unreachable'),
    ('CONFIGURATION_UNAVAILABLE', 'configuration_unavailable'),
    ('CONFIGURATION_NOT_INTERPRETABLE', 'configuration_not_interpretable'),
    ('SOLAR_ACQUISITION_FAILED', 'solar_acquisition_failed'),
    ('CYLINDER_ACQUISITION_FAILED', 'cylinder_acquisition_failed'),
    ('EVIDENCE_STALE', 'evidence_stale'),
    ('INCOHERENT_ACQUISITION', 'incoherent_acquisition'),
])
def test_remaining_owned_graphql_names(adopted, removed):
    docs = documents()
    assert adopted in docs[0]
    with pytest.raises(ValueError, match="GraphQL"):
        CHECKER.validate(docs[0].replace(adopted, removed), *docs[1:])


def test_dynamic_builder_start_remains_exported():
    page = documents()[0]
    assert "`Start(ctx)` performs an initial build" in page
    assert "`start(ctx)`" not in page


@pytest.mark.parametrize("text", [
    "```graphql\n{ busSummary { status } }\n```",
    "Invoke `modbus.v1.raw.read`.",
    "```graphql\n{ busSummary_extra { status } }\n```",
    "```graphql\ntype Query { busSummaryExtra: String }\n```",
    "```graphql\ntype Query { busSummary2: String }\n```",
])
def test_remaining_page_injection_rejected(tmp_path, text):
    # Root field catches schema reversion; tool catches registration reversion.
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text("[]")
    (tmp_path / "api").mkdir()
    (tmp_path / "api/portal.md").write_text(text)
    with pytest.raises(ValueError, match="remaining API|partial stale"):
        CHECKER.validate_remaining_pages(tmp_path)


@pytest.mark.parametrize("name", ["current_temp_c_source", "current_temp_cSource"])
def test_adopted_graphql_name_extension_allowed(tmp_path, name):
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text("[]")
    (tmp_path / "api").mkdir()
    (tmp_path / "api/portal.md").write_text(
        "```graphql\ntype Query { " + name + ": String }\n```\n")
    CHECKER.validate_remaining_pages(tmp_path)


def test_remaining_exemptions_exist():
    CHECKER.validate_remaining_pages(ROOT)


@pytest.mark.parametrize("opening,closing", [
    ("```json", "```"),
    ("```json response-example", "```"),
    ("```yaml", "```"),
    ("```", "```"),
    ("```graphql", "```"),
    ("```graphql schema-example", "```"),
    ("~~~~graphql schema-example", "~~~~"),
    ("  ````graphql schema-example", "  `````"),
])
def test_documentary_exemption_cannot_move_into_graphql(tmp_path, opening, closing):
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text(json.dumps([{
        "file": "api/graphql.md", "token": "flowsetHcMaxC",
        "context": "flowsetHcMaxC", "count": 1,
        "reason": "Preserved documentary correspondence.",
    }]))
    (tmp_path / "api").mkdir()
    page = tmp_path / "api/graphql.md"
    page.write_text("Documentary correspondence: `flowsetHcMaxC`.\n")
    CHECKER.validate_remaining_pages(tmp_path)
    body = ('type Query { flowsetHcMaxC: Float }' if "graphql" in opening
            else '{"flowsetHcMaxC": 42}')
    page.write_text(opening + "\n" + body + "\n" + closing + "\n")
    with pytest.raises(ValueError, match="remaining API spelling or stale naming exemption"):
        CHECKER.validate_remaining_pages(tmp_path)


@pytest.mark.parametrize("value", [
    '"busSummaryExtra"',
    '"escaped \\" busSummaryExtra # still string"',
    '"""block busSummaryExtra\nmore data"""',
])
def test_stale_prefix_in_graphql_strings_allowed(tmp_path, value):
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text("[]")
    page = tmp_path / "example.md"
    page.write_text('```graphql schema-example\n{ search(value: ' + value + ') }\n```\n')
    CHECKER.validate_remaining_pages(tmp_path)
    page.write_text('```graphql schema-example\n{ busSummaryExtra(value: ' + value + ') }\n```\n')
    with pytest.raises(ValueError, match="partial stale"):
        CHECKER.validate_remaining_pages(tmp_path)


@pytest.mark.parametrize("body", [
    '{ search(value: "busSummary") }',
    '{ search(value: "escaped \\" busSummary") }',
    '"""busSummary\nblock description"""\ntype Query { search: String }',
    '{ search } # busSummary',
    '{ search(value: "busSummary") } # flowsetHcMaxC',
])
def test_exact_stale_graphql_data_ignored_but_names_checked(tmp_path, body):
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text("[]")
    page = tmp_path / "example.md"
    page.write_text("```graphql schema-example\n" + body + "\n```\n")
    CHECKER.validate_remaining_pages(tmp_path)
    page.write_text("```graphql schema-example\n" + body + "\n{ busSummary }\n```\n")
    with pytest.raises(ValueError, match="remaining API"):
        CHECKER.validate_remaining_pages(tmp_path)


@pytest.mark.parametrize("opening, name", [
    ("```graphql", "busSummaryextra"),
    ("```GraphQL", "busSummaryExtra"),
    ("```GRAPHQL schema-example", "busSummary2"),
])
def test_stale_prefix_rejected_for_any_continuation_and_fence_case(tmp_path, opening, name):
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text("[]")
    page = tmp_path / "example.md"
    page.write_text(opening + "\n{ " + name + " }\n```\n")
    with pytest.raises(ValueError, match="partial stale"):
        CHECKER.validate_remaining_pages(tmp_path)


def test_exact_stale_prose_still_checked_beside_graphql_data(tmp_path):
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text("[]")
    (tmp_path / "example.md").write_text(
        '```graphql\n{ search(value: "busSummary") }\n```\nbusSummary\n')
    with pytest.raises(ValueError, match="remaining API"):
        CHECKER.validate_remaining_pages(tmp_path)
